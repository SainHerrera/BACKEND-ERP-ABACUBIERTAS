from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.adapters.api.audit import auditar
from app.adapters.deps import get_current_user, require_roles
from app.adapters.repositories.product_repository import SQLAlchemyProductRepository
from app.adapters.repositories.stock_request_repository import (
    SQLAlchemyStockRequestRepository,
)
from app.adapters.schemas import (
    Page,
    StockRequestCreate,
    StockRequestRead,
    StockRequestStatusUpdate,
)
from app.application.services.stock_request_service import StockRequestService
from app.domain.entities.stock_request import StockRequest
from app.domain.entities.user import User
from app.domain.exceptions import (
    InvalidQuantity,
    InvalidStockRequestStatus,
    InvalidStockRequestTransition,
    ProductNotFound,
    StockRequestNotFound,
)
from app.infrastructure.db import get_db

router = APIRouter(prefix="/stock-requests", tags=["stock-requests"])

CREATE_ROLES = ("admin", "compras", "bodega")
WRITE_ROLES = ("admin", "compras")


def _build_service(db: Session) -> StockRequestService:
    return StockRequestService(
        SQLAlchemyStockRequestRepository(db),
        SQLAlchemyProductRepository(db),
        db,
    )


def _to_read(r: StockRequest) -> StockRequestRead:
    return StockRequestRead(
        id_solicitud=r.id_solicitud,
        numero_solicitud=r.numero_solicitud,
        id_producto=r.id_producto,
        descripcion=r.descripcion,
        cantidad_sugerida=r.cantidad_sugerida,
        stock_actual=r.stock_actual,
        stock_minimo=r.stock_minimo,
        estado=r.estado,
        fecha=r.fecha,
        id_usuario=r.id_usuario,
        nombre_usuario=r.nombre_usuario,
        observaciones=r.observaciones,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.get("", response_model=Page[StockRequestRead])
def list_stock_requests(
    estado: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[StockRequestRead]:
    try:
        items, total = _build_service(db).list(estado=estado, skip=skip, limit=limit)
    except InvalidStockRequestStatus as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return Page(items=[_to_read(r) for r in items], total=total, skip=skip, limit=limit)


@router.get("/{request_id}", response_model=StockRequestRead)
def get_stock_request(
    request_id: UUID,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StockRequestRead:
    try:
        return _to_read(_build_service(db).get(request_id))
    except StockRequestNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud de stock no encontrada"
        )


@router.post("", response_model=StockRequestRead, status_code=status.HTTP_201_CREATED)
def create_stock_request(
    data: StockRequestCreate,
    current_user: User = Depends(require_roles(*CREATE_ROLES)),
    db: Session = Depends(get_db),
) -> StockRequestRead:
    try:
        solicitud = _to_read(
            _build_service(db).create(
                id_producto=data.id_producto,
                cantidad_sugerida=data.cantidad_sugerida,
                observaciones=data.observaciones,
                id_usuario=current_user.id,
                nombre_usuario=current_user.name,
            )
        )
        auditar(
            db,
            current_user,
            "stock_request_created",
            f"Solicitud de stock {solicitud.numero_solicitud} creada",
        )
        return solicitud
    except ProductNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    except InvalidQuantity as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/{request_id}/status", response_model=StockRequestRead)
def update_stock_request_status(
    request_id: UUID,
    data: StockRequestStatusUpdate,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> StockRequestRead:
    try:
        solicitud = _to_read(
            _build_service(db).update_estado(
                request_id,
                estado=data.estado,
                id_usuario=current_user.id,
                nombre_usuario=current_user.name,
            )
        )
        auditar(
            db,
            current_user,
            "stock_request_updated",
            f"Solicitud {solicitud.numero_solicitud} → {solicitud.estado}",
        )
        return solicitud
    except StockRequestNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud de stock no encontrada"
        )
    except (InvalidStockRequestStatus, InvalidStockRequestTransition) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))