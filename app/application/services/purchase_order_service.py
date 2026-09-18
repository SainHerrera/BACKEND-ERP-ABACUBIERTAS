from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.purchase_order import PurchaseOrder
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
from app.domain.ports.movement_repository import MovementRepository
from app.domain.ports.product_repository import ProductRepository
from app.domain.ports.provider_repository import ProviderRepository
from app.domain.ports.purchase_order_repository import PurchaseOrderRepository
from app.domain.ports.system_settings_repository import SystemSettingsRepository

VALID_ESTADOS = {"pendiente_aprobacion", "enviada", "en_transito", "recibida", "rechazada"}


class PurchaseOrderService:
    def __init__(
        self,
        orders: PurchaseOrderRepository,
        providers: ProviderRepository,
        products: ProductRepository,
        settings: SystemSettingsRepository,
        movements: MovementRepository,
        db: Session,
    ):
        self.orders = orders
        self.providers = providers
        self.products = products
        self.settings = settings
        self.movements = movements
        self.db = db

    def list(
        self,
        estado: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[PurchaseOrder], int]:
        if estado is not None and estado not in VALID_ESTADOS:
            raise InvalidPurchaseOrderStatus(
                f"Estado inválido. Permitidos: {', '.join(sorted(VALID_ESTADOS))}"
            )
        return self.orders.list(estado=estado, skip=skip, limit=limit)

    def get(self, id_orden_compra: UUID) -> PurchaseOrder:
        order = self.orders.get_by_id(id_orden_compra)
        if order is None:
            raise PurchaseOrderNotFound("Orden de compra no encontrada")
        return order

    def pending_approval(self) -> list[PurchaseOrder]:
        return self.orders.list_pending_approval()

    def create(
        self,
        *,
        id_proveedor: UUID,
        detalles: list[dict],
        fecha_emision: datetime | None = None,
        observaciones: str | None = None,
        id_solicitud: UUID | None = None,
        numero_solicitud: str | None = None,
        id_cotizacion: UUID | None = None,
    ) -> PurchaseOrder:
        provider = self.providers.get_by_id(id_proveedor)
        if provider is None or not provider.activo:
            raise ProviderNotFound("Proveedor no encontrado")

        products = {d["id_producto"]: self.products.get_by_id(d["id_producto"]) for d in detalles}
        for d in detalles:
            prod = products[d["id_producto"]]
            if prod is None or not prod.activo:
                raise ProductNotFound(f"Producto con ID {d['id_producto']} no encontrado")
            desc = d.get("descripcion") or prod.nombre
            if not d.get("cantidad_ordenada") or d["cantidad_ordenada"] <= 0:
                raise InvalidQuantity(
                    f'La cantidad ordenada del producto "{desc}" debe ser mayor a 0'
                )
            if not d.get("precio_unitario") or Decimal(d["precio_unitario"]) <= 0:
                raise InvalidQuantity(
                    f'El precio unitario del producto "{desc}" debe ser mayor a 0'
                )

        total_oc = sum(
            (Decimal(d["cantidad_ordenada"]) * Decimal(d["precio_unitario"]) for d in detalles),
            Decimal("0"),
        )
        current_settings = self.settings.get()
        requiere_aprobacion = (
            current_settings.aprobacion_oc_habilitada
            and total_oc >= current_settings.aprobacion_oc_monto_minimo
        )
        numero = f"OC-{self.orders.count() + 1:04d}"
        estado = "pendiente_aprobacion" if requiere_aprobacion else "enviada"

        try:
            order = self.orders.create(
                id_proveedor=id_proveedor,
                nombre_proveedor=provider.nombre_empresa,
                numero_oc=numero,
                fecha_emision=fecha_emision or datetime.now(),
                estado=estado,
                observaciones=observaciones,
                id_solicitud=id_solicitud,
                numero_solicitud=numero_solicitud,
                id_cotizacion=id_cotizacion,
                detalles=detalles,
            )
            self.db.commit()
            return order
        except Exception:
            self.db.rollback()
            raise

    def mark_transit(self, id_orden_compra: UUID) -> PurchaseOrder:
        current = self.get(id_orden_compra)
        if current.estado != "enviada":
            raise InvalidPurchaseOrderTransition(
                f'La orden de compra {current.numero_oc} debe estar en estado "enviada" '
                f"para marcar en tránsito"
            )
        try:
            order = self.orders.update_estado(id_orden_compra, "en_transito")
            self.db.commit()
            return order
        except Exception:
            self.db.rollback()
            raise

    def approve(self, id_orden_compra: UUID, *, aprobar: bool) -> PurchaseOrder:
        current = self.get(id_orden_compra)
        if current.estado != "pendiente_aprobacion":
            raise InvalidPurchaseOrderTransition(
                f"La orden de compra {current.numero_oc} no está pendiente de aprobación"
            )
        try:
            order = self.orders.update_estado(
                id_orden_compra, "enviada" if aprobar else "rechazada"
            )
            self.db.commit()
            return order
        except Exception:
            self.db.rollback()
            raise

    def receive(
        self,
        id_orden_compra: UUID,
        *,
        id_producto: UUID,
        cantidad: int,
        fecha: datetime | None = None,
        nota: str | None = None,
        id_usuario: UUID | None = None,
    ) -> PurchaseOrder:
        current = self.get(id_orden_compra)
        if current.estado != "en_transito":
            raise InvalidPurchaseOrderTransition(
                f"La orden de compra {current.numero_oc} debe estar en tránsito "
                f"para registrar la entrada"
            )
        if cantidad <= 0:
            raise InvalidQuantity("La cantidad a recibir debe ser mayor a 0")

        detail = next((d for d in current.detalles if d.id_producto == id_producto), None)
        if detail is None:
            raise ProductNotInOrder(
                f"El producto con ID {id_producto} no pertenece a la orden {current.numero_oc}"
            )
        nuevo_recibido = detail.cantidad_recibida + cantidad
        if nuevo_recibido > detail.cantidad_ordenada:
            raise ReceiptExceedsOrdered(
                f'No se puede recibir más de lo ordenado para "{detail.descripcion}". '
                f"Ordenado: {detail.cantidad_ordenada}, recibido: {detail.cantidad_recibida}, "
                f"solicitado: {cantidad}"
            )

        try:
            product = self.products.get_by_id(id_producto)
            if product is None:
                raise ProductNotFound("Producto no encontrado")
            self.products.update_stock(id_producto, product.stock_actual + cantidad)
            self.movements.create(
                id_producto=id_producto,
                tipo="entrada",
                cantidad=cantidad,
                referencia=current.numero_oc,
                id_usuario=id_usuario,
                nota=(
                    nota.strip()
                    if nota and nota.strip()
                    else f"Recepción de mercancía de la orden {current.numero_oc}"
                ),
                fecha=fecha,
            )
            order = self.orders.apply_reception(
                id_orden_compra, id_producto=id_producto, cantidad_recibida=nuevo_recibido
            )
            if order is not None and all(
                d.cantidad_recibida >= d.cantidad_ordenada for d in order.detalles
            ):
                order = self.orders.update_estado(id_orden_compra, "recibida")
            self.db.commit()
            return order
        except Exception:
            self.db.rollback()
            raise