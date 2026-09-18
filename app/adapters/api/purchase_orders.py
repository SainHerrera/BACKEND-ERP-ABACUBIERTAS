from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.adapters.api.audit import auditar
from app.adapters.deps import get_current_user, require_roles
from app.adapters.repositories.movement_repository import SQLAlchemyMovementRepository
from app.adapters.repositories.product_repository import SQLAlchemyProductRepository
from app.adapters.repositories.provider_repository import SQLAlchemyProviderRepository
from app.adapters.repositories.purchase_order_repository import (
    SQLAlchemyPurchaseOrderRepository,
)
from app.adapters.repositories.system_settings_repository import (
    SQLAlchemySystemSettingsRepository,
)
from app.adapters.schemas import (
    ApprovePoUpdate,
    Page,
    PurchaseOrderCreate,
    PurchaseOrderDetailRead,
    PurchaseOrderRead,
    ReceivePoCreate,
)
from app.application.services.purchase_order_service import PurchaseOrderService
from app.domain.entities.purchase_order import PurchaseOrder
from app.domain.entities.user import User
from app.domain.exceptions import (
    InvalidPurchaseOrderStatus,
    InvalidPurchaseOrderTransition,
    InvalidQuantity,
    ProductNotFound,
    ProductNotInOrder,
    ProviderNotFound,
    PurchaseOrderNotFound,
    ReceiptExceedsOrdered,
)
from app.infrastructure.db import get_db

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])

CREATE_ROLES = ("admin", "compras")
RECEIVE_ROLES = ("admin", "bodega")
APPROVE_ROLES = ("admin", "gerencia")


def _build_service(db: Session) -> PurchaseOrderService:
    return PurchaseOrderService(
        SQLAlchemyPurchaseOrderRepository(db),
        SQLAlchemyProviderRepository(db),
        SQLAlchemyProductRepository(db),
        SQLAlchemySystemSettingsRepository(db),
        SQLAlchemyMovementRepository(db),
        db,
    )


def _to_read(o: PurchaseOrder) -> PurchaseOrderRead:
    detalles = [
        PurchaseOrderDetailRead(
            id_detalle=idx,
            id_producto=d.id_producto,
            descripcion=d.descripcion,
            cantidad_ordenada=d.cantidad_ordenada,
            cantidad_recibida=d.cantidad_recibida,
            precio_unitario=d.precio_unitario,
            tiempo_entrega_dias=d.tiempo_entrega_dias,
        )
        for idx, d in enumerate(o.detalles, start=1)
    ]
    return PurchaseOrderRead(
        id_orden_compra=o.id_orden_compra,
        numero_oc=o.numero_oc,
        id_proveedor=o.id_proveedor,
        nombre_proveedor=o.nombre_proveedor,
        fecha_emision=o.fecha_emision,
        estado=o.estado,
        observaciones=o.observaciones,
        id_solicitud=o.id_solicitud,
        numero_solicitud=o.numero_solicitud,
        id_cotizacion=o.id_cotizacion,
        total=Decimal(o.total),
        detalles=detalles,
        created_at=o.created_at,
        updated_at=o.updated_at,
    )


@router.get("", response_model=Page[PurchaseOrderRead])
def list_purchase_orders(
    estado: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[PurchaseOrderRead]:
    try:
        items, total = _build_service(db).list(estado=estado, skip=skip, limit=limit)
    except InvalidPurchaseOrderStatus as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return Page(
        items=[_to_read(o) for o in items], total=total, skip=skip, limit=limit
    )


# Ojo: debe declararse antes de /{order_id} para no ser capturada como path param.
@router.get("/pending-approval", response_model=list[PurchaseOrderRead])
def list_pending_approval(
    _current_user: User = Depends(require_roles(*APPROVE_ROLES)),
    db: Session = Depends(get_db),
) -> list[PurchaseOrderRead]:
    return [_to_read(o) for o in _build_service(db).pending_approval()]


@router.get("/{order_id}", response_model=PurchaseOrderRead)
def get_purchase_order(
    order_id: UUID,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PurchaseOrderRead:
    try:
        return _to_read(_build_service(db).get(order_id))
    except PurchaseOrderNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Orden de compra no encontrada"
        )


@router.post("", response_model=PurchaseOrderRead, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    data: PurchaseOrderCreate,
    current_user: User = Depends(require_roles(*CREATE_ROLES)),
    db: Session = Depends(get_db),
) -> PurchaseOrderRead:
    service = _build_service(db)
    try:
        order = service.create(
            id_proveedor=data.id_proveedor,
            fecha_emision=data.fecha_emision,
            observaciones=data.observaciones,
            id_solicitud=data.id_solicitud,
            numero_solicitud=data.numero_solicitud,
            id_cotizacion=data.id_cotizacion,
            detalles=[d.model_dump() for d in data.detalles],
        )
        auditar(
            db,
            current_user,
            "purchase_order_created",
            f"Orden de compra {order.numero_oc} creada (estado {order.estado})",
        )
        if order.estado == "pendiente_aprobacion":
            auditar(
                db,
                current_user,
                "purchase_order_pending_approval",
                f"Orden de compra {order.numero_oc} supera el umbral de aprobación y queda pendiente",
            )
        return _to_read(order)
    except ProviderNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proveedor no encontrado")
    except ProductNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidQuantity as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{order_id}/mark-transit", response_model=PurchaseOrderRead)
def mark_order_transit(
    order_id: UUID,
    current_user: User = Depends(require_roles(*CREATE_ROLES)),
    db: Session = Depends(get_db),
) -> PurchaseOrderRead:
    try:
        order = _to_read(_build_service(db).mark_transit(order_id))
        auditar(db, current_user, "purchase_order_in_transit", f"Orden {order.numero_oc} en tránsito")
        return order
    except PurchaseOrderNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Orden de compra no encontrada"
        )
    except InvalidPurchaseOrderTransition as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{order_id}/receive", response_model=PurchaseOrderRead)
def receive_purchase_order(
    order_id: UUID,
    data: ReceivePoCreate,
    current_user: User = Depends(require_roles(*RECEIVE_ROLES)),
    db: Session = Depends(get_db),
) -> PurchaseOrderRead:
    service = _build_service(db)
    try:
        order = _to_read(
            service.receive(
                order_id,
                id_producto=data.product_id,
                cantidad=data.quantity,
                fecha=data.fecha,
                nota=data.note,
                id_usuario=current_user.id,
            )
        )
        auditar(db, current_user, "purchase_order_received", f"Recepción registrada en {order.numero_oc}")
        return order
    except PurchaseOrderNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Orden de compra no encontrada"
        )
    except ProductNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    except (InvalidPurchaseOrderTransition, InvalidQuantity, ProductNotInOrder) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ReceiptExceedsOrdered as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{order_id}/approve", response_model=PurchaseOrderRead)
def approve_purchase_order(
    order_id: UUID,
    data: ApprovePoUpdate,
    current_user: User = Depends(require_roles(*APPROVE_ROLES)),
    db: Session = Depends(get_db),
) -> PurchaseOrderRead:
    try:
        order = _to_read(_build_service(db).approve(order_id, aprobar=data.aprobar))
        accion = "purchase_order_approved" if data.aprobar else "purchase_order_rejected"
        estado_txt = "aprobada" if data.aprobar else "rechazada"
        auditar(db, current_user, accion, f"Orden de compra {order.numero_oc} {estado_txt}")
        return order
    except PurchaseOrderNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Orden de compra no encontrada"
        )
    except InvalidPurchaseOrderTransition as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))