from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.adapters.api.audit import auditar
from app.adapters.deps import get_current_user, require_roles
from app.adapters.repositories.product_repository import SQLAlchemyProductRepository
from app.adapters.repositories.provider_quotation_repository import (
    SQLAlchemyProviderQuotationRepository,
)
from app.adapters.repositories.provider_repository import SQLAlchemyProviderRepository
from app.adapters.repositories.stock_request_repository import (
    SQLAlchemyStockRequestRepository,
)
from app.adapters.schemas import (
    Page,
    ProviderQuotationCreate,
    ProviderQuotationRead,
    ProviderQuotationSelectUpdate,
)
from app.application.services.provider_quotation_service import ProviderQuotationService
from app.domain.entities.provider_quotation import ProviderQuotation
from app.domain.entities.user import User
from app.domain.exceptions import (
    InsufficientProviderQuotations,
    InvalidQuantity,
    ProductDoesNotMatchRequest,
    ProductNotFound,
    ProviderNotFound,
    ProviderQuotationNotFound,
    StockRequestNotFound,
)
from app.infrastructure.db import get_db

router = APIRouter(prefix="/provider-quotations", tags=["provider-quotations"])

WRITE_ROLES = ("admin", "compras")


def _build_service(db: Session) -> ProviderQuotationService:
    return ProviderQuotationService(
        SQLAlchemyProviderQuotationRepository(db),
        SQLAlchemyStockRequestRepository(db),
        SQLAlchemyProductRepository(db),
        SQLAlchemyProviderRepository(db),
        db,
    )


def _to_read(q: ProviderQuotation) -> ProviderQuotationRead:
    return ProviderQuotationRead(
        id_cotizacion=q.id_cotizacion,
        numero_cotizacion=q.numero_cotizacion,
        id_solicitud=q.id_solicitud,
        id_producto=q.id_producto,
        id_proveedor=q.id_proveedor,
        nombre_proveedor=q.nombre_proveedor,
        precio_unitario=q.precio_unitario,
        tiempo_entrega_dias=q.tiempo_entrega_dias,
        condiciones=q.condiciones,
        fecha=q.fecha,
        seleccionada=q.seleccionada,
        created_at=q.created_at,
        updated_at=q.updated_at,
    )


@router.get("", response_model=Page[ProviderQuotationRead])
def list_provider_quotations(
    id_solicitud: UUID | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[ProviderQuotationRead]:
    items, total = _build_service(db).list(
        id_solicitud=id_solicitud, skip=skip, limit=limit
    )
    return Page(items=[_to_read(q) for q in items], total=total, skip=skip, limit=limit)


@router.get("/{quotation_id}", response_model=ProviderQuotationRead)
def get_provider_quotation(
    quotation_id: UUID,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProviderQuotationRead:
    try:
        return _to_read(_build_service(db).get(quotation_id))
    except ProviderQuotationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización de proveedor no encontrada",
        )


@router.post("", response_model=ProviderQuotationRead, status_code=status.HTTP_201_CREATED)
def create_provider_quotation(
    data: ProviderQuotationCreate,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ProviderQuotationRead:
    try:
        quotation = _to_read(
            _build_service(db).create(
                id_solicitud=data.id_solicitud,
                id_producto=data.id_producto,
                id_proveedor=data.id_proveedor,
                precio_unitario=data.precio_unitario,
                tiempo_entrega_dias=data.tiempo_entrega_dias,
                condiciones=data.condiciones,
            )
        )
        auditar(
            db,
            current_user,
            "provider_quotation_created",
            f"Cotización de proveedor {quotation.numero_cotizacion} creada",
        )
        return quotation
    except StockRequestNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud de stock no encontrada"
        )
    except ProductNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    except ProviderNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proveedor no encontrado")
    except (InvalidQuantity, ProductDoesNotMatchRequest) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/{quotation_id}/seleccionar", response_model=ProviderQuotationRead)
def select_provider_quotation(
    quotation_id: UUID,
    data: ProviderQuotationSelectUpdate,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ProviderQuotationRead:
    try:
        quotation = _to_read(
            _build_service(db).select(quotation_id, seleccionada=data.seleccionada)
        )
        estado_txt = "seleccionada" if quotation.seleccionada else "deseleccionada"
        auditar(
            db,
            current_user,
            "provider_quotation_selected",
            f"Cotización {quotation.numero_cotizacion} {estado_txt}",
        )
        return quotation
    except ProviderQuotationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización de proveedor no encontrada",
        )
    except InsufficientProviderQuotations as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))