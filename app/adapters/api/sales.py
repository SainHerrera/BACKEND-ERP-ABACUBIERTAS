from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.adapters.deps import get_current_user, require_roles
from app.adapters.repositories.client_repository import SQLAlchemyClientRepository
from app.adapters.repositories.movement_repository import SQLAlchemyMovementRepository
from app.adapters.repositories.product_repository import SQLAlchemyProductRepository
from app.adapters.repositories.quotation_repository import SQLAlchemyQuotationRepository
from app.adapters.repositories.sale_repository import SQLAlchemySaleRepository
from app.adapters.schemas import (
    Page,
    SaleCreate,
    SaleDetailRead,
    SaleRead,
    SaleUpdate,
)
from app.application.services.sale_service import SaleService
from app.domain.entities.sale import Sale
from app.domain.entities.user import User
from app.domain.exceptions import (
    ClientNotFound,
    InsufficientStock,
    InvalidSaleStatus,
    InvalidSaleTransition,
    ProductNotFound,
    QuotationNotFound,
    SaleNotFound,
)
from app.infrastructure.db import get_db

router = APIRouter(prefix="/sales", tags=["sales"])
quotation_conversion_router = APIRouter(prefix="/quotations", tags=["sales"])

WRITE_ROLES = ("admin", "ventas")
DISPATCH_ROLES = ("admin", "bodega")


def _build_service(db: Session) -> SaleService:
    return SaleService(
        SQLAlchemySaleRepository(db),
        SQLAlchemyProductRepository(db),
        SQLAlchemyClientRepository(db),
        SQLAlchemyQuotationRepository(db),
        SQLAlchemyMovementRepository(db),
        db,
    )


def _to_read(s: Sale) -> SaleRead:
    detalles = [
        SaleDetailRead(
            id_detalle=idx,
            id_producto=d.id_producto,
            descripcion=d.descripcion,
            cantidad=d.cantidad,
            precio_unitario=d.precio_unitario,
            descuento=d.descuento,
            subtotal=d.subtotal,
        )
        for idx, d in enumerate(s.detalles, start=1)
    ]
    return SaleRead(
        id_orden_venta=s.id_orden_venta,
        numero_orden=s.numero_orden,
        id_cliente=s.id_cliente,
        nombre_cliente=s.nombre_cliente,
        id_cotizacion=s.id_cotizacion,
        id_usuario=s.id_usuario,
        fecha_venta=s.fecha_venta,
        estado=s.estado,
        subtotal=s.subtotal,
        impuestos=s.impuestos,
        total=s.total,
        observaciones=s.observaciones,
        detalles=detalles,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


@router.get("", response_model=Page[SaleRead])
def list_sales(
    id_cliente: UUID | None = Query(default=None),
    estado: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[SaleRead]:
    try:
        items, total = _build_service(db).list(
            id_cliente=id_cliente, estado=estado, skip=skip, limit=limit
        )
    except InvalidSaleStatus as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return Page(items=[_to_read(s) for s in items], total=total, skip=skip, limit=limit)


@router.get("/{sale_id}", response_model=SaleRead)
def get_sale(
    sale_id: UUID,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SaleRead:
    try:
        return _to_read(_build_service(db).get(sale_id))
    except SaleNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido de venta no encontrado"
        )


@router.post("", response_model=SaleRead, status_code=status.HTTP_201_CREATED)
def create_sale(
    data: SaleCreate,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> SaleRead:
    service = _build_service(db)
    try:
        sale = service.create(
            id_cliente=data.id_cliente,
            id_usuario=current_user.id,
            id_cotizacion=data.id_cotizacion,
            observaciones=data.observaciones,
            detalles=[d.model_dump() for d in data.detalles],
        )
        return _to_read(sale)
    except ClientNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    except ProductNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")


@router.patch("/{sale_id}", response_model=SaleRead)
def update_sale(
    sale_id: UUID,
    data: SaleUpdate,
    _current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> SaleRead:
    service = _build_service(db)
    payload = data.model_dump(exclude_unset=True)
    try:
        return _to_read(service.update(sale_id, **payload))
    except SaleNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido de venta no encontrado"
        )
    except InvalidSaleStatus as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except InvalidSaleTransition as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{sale_id}/confirm-dispatch", response_model=SaleRead)
def confirm_dispatch(
    sale_id: UUID,
    observaciones: str | None = None,
    current_user: User = Depends(require_roles(*DISPATCH_ROLES)),
    db: Session = Depends(get_db),
) -> SaleRead:
    service = _build_service(db)
    try:
        return _to_read(
            service.confirm_dispatch(sale_id, observaciones=observaciones, id_usuario=current_user.id)
        )
    except SaleNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido de venta no encontrado"
        )
    except ProductNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    except InsufficientStock as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except InvalidSaleTransition as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{sale_id}/cancel", response_model=SaleRead)
def cancel_sale(
    sale_id: UUID,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> SaleRead:
    service = _build_service(db)
    try:
        return _to_read(service.cancel(sale_id, id_usuario=current_user.id))
    except SaleNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido de venta no encontrado"
        )
    except ProductNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")


@quotation_conversion_router.post("/{quotation_id}/convert-to-sale", response_model=SaleRead)
def convert_to_sale(
    quotation_id: UUID,
    observaciones: str | None = None,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> SaleRead:
    service = _build_service(db)
    try:
        sale = service.convert_from_quotation(
            quotation_id, id_usuario=current_user.id, observaciones=observaciones
        )
        return _to_read(sale)
    except QuotationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada")
    except ClientNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    except ProductNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    except InvalidSaleTransition as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))