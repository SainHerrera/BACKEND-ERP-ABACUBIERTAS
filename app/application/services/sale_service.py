from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.sale import Sale
from app.domain.exceptions import (
    ClientNotFound,
    InsufficientStock,
    InvalidSaleStatus,
    InvalidSaleTransition,
    ProductNotFound,
    QuotationNotFound,
    SaleNotFound,
)
from app.domain.ports.client_repository import ClientRepository
from app.domain.ports.movement_repository import MovementRepository
from app.domain.ports.product_repository import ProductRepository
from app.domain.ports.quotation_repository import QuotationRepository
from app.domain.ports.sale_repository import SaleRepository

TAX_RATE = Decimal("0.19")
VALID_ESTADOS = {"pendiente", "en_proceso", "entregada", "cancelada"}
ALLOWED_TRANSITIONS = {
    "pendiente": {"en_proceso", "entregada"},
    "en_proceso": {"entregada"},
    "entregada": set(),
    "cancelada": set(),
}


class SaleService:
    def __init__(
        self,
        sales: SaleRepository,
        products: ProductRepository,
        clients: ClientRepository,
        quotations: QuotationRepository,
        movements: MovementRepository,
        db: Session,
    ):
        self.sales = sales
        self.products = products
        self.clients = clients
        self.quotations = quotations
        self.movements = movements
        self.db = db

    def list(
        self,
        id_cliente: UUID | None = None,
        estado: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Sale], int]:
        if estado is not None and estado not in VALID_ESTADOS:
            raise InvalidSaleStatus(
                f"Estado inválido. Permitidos: {', '.join(sorted(VALID_ESTADOS))}"
            )
        return self.sales.list(
            id_cliente=id_cliente, estado=estado, skip=skip, limit=limit
        )

    def get(self, id_orden_venta: UUID) -> Sale:
        sale = self.sales.get_by_id(id_orden_venta)
        if sale is None:
            raise SaleNotFound("Pedido de venta no encontrado")
        return sale

    @staticmethod
    def _apply_pricing(detalles: list[dict], product_price_lookup) -> list[dict]:
        result = []
        for d in detalles:
            cantidad = Decimal(d["cantidad"])
            desp_descuento = Decimal(d.get("descuento") or 0)
            precio = Decimal(d.get("precio_unitario") or 0)
            if precio <= 0:
                producto = product_price_lookup(d["id_producto"])
                if producto is None:
                    raise ProductNotFound("Producto no encontrado")
                precio = Decimal(str(producto.precio_unitario))
            subtotal = precio * cantidad - desp_descuento
            result.append(
                {
                    "id_producto": d["id_producto"],
                    "descripcion": d.get("descripcion"),
                    "cantidad": int(cantidad),
                    "precio_unitario": precio,
                    "descuento": desp_descuento,
                    "subtotal": subtotal,
                }
            )
        return result

    @staticmethod
    def _compute_totals(detalles: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
        subtotal = sum((Decimal(d["subtotal"]) for d in detalles), Decimal("0"))
        impuestos = (subtotal * TAX_RATE).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        total = subtotal + impuestos
        return subtotal, impuestos, total

    def create(
        self,
        *,
        id_cliente: UUID,
        id_usuario: UUID | None,
        detalles: list[dict],
        id_cotizacion: UUID | None = None,
        observaciones: str | None = None,
    ) -> Sale:
        if self.clients.get_by_id(id_cliente) is None:
            raise ClientNotFound("Cliente no encontrado")
        if not detalles:
            raise InvalidSaleTransition("El pedido debe tener al menos un detalle")

        detalles_out = self._apply_pricing(detalles, self.products.get_by_id)
        subtotal, impuestos, total = self._compute_totals(detalles_out)
        numero = f"PED-{self.sales.count() + 1:04d}"

        try:
            sale = self.sales.create(
                id_cliente=id_cliente,
                id_usuario=id_usuario,
                id_cotizacion=id_cotizacion,
                numero_orden=numero,
                fecha_venta=datetime.now(),
                estado="pendiente",
                subtotal=subtotal,
                impuestos=impuestos,
                total=total,
                observaciones=observaciones,
                detalles=detalles_out,
            )
            self.db.commit()
            return sale
        except Exception:
            self.db.rollback()
            raise

    def update(
        self,
        id_orden_venta: UUID,
        *,
        estado: str | None = None,
        observaciones: str | None = None,
    ) -> Sale:
        current = self.get(id_orden_venta)
        if estado is not None:
            if estado not in VALID_ESTADOS:
                raise InvalidSaleStatus(
                    f"Estado inválido. Permitidos: {', '.join(sorted(VALID_ESTADOS))}"
                )
            if current.estado != estado and estado not in ALLOWED_TRANSITIONS.get(
                current.estado, set()
            ):
                raise InvalidSaleTransition(
                    f"No se puede cambiar el estado de '{current.estado}' a '{estado}'"
                )
        try:
            sale = self.sales.update(
                id_orden_venta,
                estado=estado or current.estado,
                observaciones=observaciones,
            )
            self.db.commit()
            return sale
        except Exception:
            self.db.rollback()
            raise

    def confirm_dispatch(
        self,
        id_orden_venta: UUID,
        *,
        observaciones: str | None = None,
        id_usuario: UUID | None = None,
    ) -> Sale:
        current = self.get(id_orden_venta)
        if current.estado == "entregada":
            return current
        if current.estado == "cancelada":
            raise InvalidSaleTransition(
                "No se puede confirmar el despacho de un pedido cancelado"
            )

        actor_usuario = id_usuario or current.id_usuario
        products = {d.id_producto: self.products.get_by_id(d.id_producto) for d in current.detalles}
        for detail in current.detalles:
            product = products[detail.id_producto]
            if product is None or not product.activo:
                raise ProductNotFound("Producto no encontrado")
            if product.stock_actual < detail.cantidad:
                raise InsufficientStock(
                    f'Stock insuficiente para "{product.nombre}". '
                    f"Stock disponible: {product.stock_actual}, solicitado: {detail.cantidad}"
                )

        try:
            for detail in current.detalles:
                product = products[detail.id_producto]
                self.products.update_stock(
                    detail.id_producto, product.stock_actual - detail.cantidad
                )
                self.movements.create(
                    id_producto=detail.id_producto,
                    tipo="salida",
                    cantidad=detail.cantidad,
                    referencia=current.numero_orden,
                    id_usuario=actor_usuario,
                    nota=f"Despacho confirmado del pedido {current.numero_orden}",
                )
            observaciones_final = (
                observaciones if observaciones is not None else current.observaciones
            )
            sale = self.sales.update(
                id_orden_venta,
                estado="entregada",
                observaciones=observaciones_final,
            )
            self.db.commit()
            return sale
        except Exception:
            self.db.rollback()
            raise

    def cancel(self, id_orden_venta: UUID, *, id_usuario: UUID | None = None) -> Sale:
        current = self.get(id_orden_venta)
        if current.estado == "cancelada":
            return current

        was_dispatched = current.estado == "entregada"
        actor_usuario = id_usuario or current.id_usuario

        try:
            if was_dispatched:
                products = {
                    d.id_producto: self.products.get_by_id(d.id_producto)
                    for d in current.detalles
                }
                for detail in current.detalles:
                    product = products[detail.id_producto]
                    if product is None:
                        raise ProductNotFound("Producto no encontrado")
                    self.products.update_stock(
                        detail.id_producto, product.stock_actual + detail.cantidad
                    )
                    self.movements.create(
                        id_producto=detail.id_producto,
                        tipo="entrada",
                        cantidad=detail.cantidad,
                        referencia=f"REVERSIÓN {current.numero_orden}",
                        id_usuario=actor_usuario,
                        nota=(
                            f"Restauración de stock por cancelación "
                            f"del despacho {current.numero_orden}"
                        ),
                    )
            sale = self.sales.update_estado(id_orden_venta, "cancelada")
            self.db.commit()
            return sale
        except Exception:
            self.db.rollback()
            raise

    def convert_from_quotation(
        self,
        id_cotizacion: UUID,
        *,
        id_usuario: UUID | None,
        observaciones: str | None = None,
    ) -> Sale:
        quotation = self.quotations.get_by_id(id_cotizacion)
        if quotation is None:
            raise QuotationNotFound("Cotización no encontrada")
        if quotation.estado != "aprobada":
            raise InvalidSaleTransition(
                "Solo se puede convertir una cotización en estado aprobada"
            )
        detalles = [
            {
                "id_producto": d.id_producto,
                "descripcion": d.descripcion,
                "cantidad": d.cantidad,
                "precio_unitario": d.precio_unitario,
                "descuento": d.descuento,
            }
            for d in quotation.detalles
        ]
        observaciones_final = (
            observaciones
            if observaciones is not None
            else f"Convertido desde {quotation.numero_consecutivo}"
        )
        return self.create(
            id_cliente=quotation.id_cliente,
            id_usuario=id_usuario,
            id_cotizacion=id_cotizacion,
            detalles=detalles,
            observaciones=observaciones_final,
        )