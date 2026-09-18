from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.adapters.deps import get_current_user, require_roles
from app.adapters.repositories.client_repository import SQLAlchemyClientRepository
from app.adapters.repositories.product_repository import SQLAlchemyProductRepository
from app.adapters.repositories.quotation_repository import SQLAlchemyQuotationRepository
from app.adapters.repositories.system_settings_repository import (
    SQLAlchemySystemSettingsRepository,
)
from app.adapters.schemas import (
    Page,
    QuotationCreate,
    QuotationDetailRead,
    QuotationEstadoUpdate,
    QuotationRead,
    QuotationUpdate,
    VALID_ESTADOS_COTIZACION,
)
from app.application.services.quotation_service import QuotationService
from app.domain.entities.quotation import Quotation
from app.domain.entities.user import User
from app.domain.exceptions import (
    ClientNotFound,
    InvalidQuotationStatus,
    InvalidQuotationTransition,
    ProductNotFound,
    QuotationNotFound,
)
from app.infrastructure.db import get_db

router = APIRouter(prefix="/quotations", tags=["quotations"])
client_quotations_router = APIRouter(prefix="/clients", tags=["quotations"])

WRITE_ROLES = ("admin", "ventas")


def _build_service(db: Session) -> QuotationService:
    from decimal import Decimal

    settings = SQLAlchemySystemSettingsRepository(db).get()
    return QuotationService(
        SQLAlchemyQuotationRepository(db),
        SQLAlchemyProductRepository(db),
        SQLAlchemyClientRepository(db),
        db,
        margen_utilidad=Decimal(settings.margen_utilidad_default),
    )


def _to_read(q: Quotation) -> QuotationRead:
    detalles = [
        QuotationDetailRead(
            id_detalle=idx,
            id_producto=d.id_producto,
            descripcion=d.descripcion,
            cantidad=d.cantidad,
            precio_unitario=d.precio_unitario,
            descuento=d.descuento,
            subtotal=d.subtotal,
        )
        for idx, d in enumerate(q.detalles, start=1)
    ]
    return QuotationRead(
        id_cotizacion=q.id_cotizacion,
        numero_consecutivo=q.numero_consecutivo,
        id_cliente=q.id_cliente,
        nombre_cliente=q.nombre_cliente,
        id_usuario=q.id_usuario,
        fecha_emision=q.fecha_emision,
        fecha_vencimiento=q.fecha_vencimiento,
        estado=q.estado,
        subtotal=q.subtotal,
        impuestos=q.impuestos,
        descuento=q.descuento,
        total=q.total,
        observaciones=q.observaciones,
        detalles=detalles,
        created_at=q.created_at,
        updated_at=q.updated_at,
    )


@router.get("", response_model=Page[QuotationRead])
def list_quotations(
    id_cliente: UUID | None = Query(default=None),
    estado: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[QuotationRead]:
    try:
        items, total = _build_service(db).list(
            id_cliente=id_cliente, estado=estado, skip=skip, limit=limit
        )
    except InvalidQuotationStatus as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return Page(
        items=[_to_read(q) for q in items], total=total, skip=skip, limit=limit
    )


@client_quotations_router.get("/{client_id}/quotations", response_model=Page[QuotationRead])
def list_client_quotations(
    client_id: UUID,
    estado: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[QuotationRead]:
    service = _build_service(db)
    if SQLAlchemyClientRepository(db).get_by_id(client_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    items, total = service.list(id_cliente=client_id, estado=estado, skip=skip, limit=limit)
    return Page(
        items=[_to_read(q) for q in items], total=total, skip=skip, limit=limit
    )


@router.get("/{quotation_id}", response_model=QuotationRead)
def get_quotation(
    quotation_id: UUID,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuotationRead:
    try:
        return _to_read(_build_service(db).get(quotation_id))
    except QuotationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada"
        )


@router.post("", response_model=QuotationRead, status_code=status.HTTP_201_CREATED)
def create_quotation(
    data: QuotationCreate,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> QuotationRead:
    service = _build_service(db)
    try:
        quotation = service.create(
            id_cliente=data.id_cliente,
            id_usuario=current_user.id,
            fecha_vencimiento=data.fecha_vencimiento,
            descuento=data.descuento,
            observaciones=data.observaciones,
            detalles=[d.model_dump() for d in data.detalles],
        )
        return _to_read(quotation)
    except ClientNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    except ProductNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")


@router.patch("/{quotation_id}", response_model=QuotationRead)
def update_quotation(
    quotation_id: UUID,
    data: QuotationUpdate,
    _current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> QuotationRead:
    service = _build_service(db)
    payload = data.model_dump(exclude_unset=True)
    if "detalles" in payload:
        payload["detalles"] = [d.model_dump() for d in data.detalles]
    if "descuento" in payload and payload["descuento"] is None:
        del payload["descuento"]
    try:
        return _to_read(service.update(quotation_id, **payload))
    except QuotationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada"
        )
    except ClientNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    except ProductNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    except InvalidQuotationTransition as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/{quotation_id}/estado", response_model=QuotationRead)
def update_quotation_estado(
    quotation_id: UUID,
    data: QuotationEstadoUpdate,
    _current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> QuotationRead:
    service = _build_service(db)
    try:
        return _to_read(service.update_estado(quotation_id, data.estado))
    except QuotationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada"
        )
    except InvalidQuotationTransition as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{quotation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quotation(
    quotation_id: UUID,
    _current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> None:
    try:
        _build_service(db).delete(quotation_id)
    except QuotationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada"
        )
    except InvalidQuotationTransition as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))