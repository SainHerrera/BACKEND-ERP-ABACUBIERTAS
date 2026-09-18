from __future__ import annotations

from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.quotation import Quotation
from app.domain.exceptions import (
    ClientNotFound,
    InvalidQuotationStatus,
    InvalidQuotationTransition,
    ProductNotFound,
    QuotationNotFound,
)
from app.domain.ports.client_repository import ClientRepository
from app.domain.ports.product_repository import ProductRepository
from app.domain.ports.quotation_repository import QuotationRepository

# Fallback si no se inyecta un margen desde system_settings.
DEFAULT_MARGEN_UTILIDAD = 30
TAX_RATE = Decimal("0.19")
VALID_ESTADOS = {"borrador", "enviada", "aprobada", "rechazada", "vencida"}
ALLOWED_TRANSITIONS = {
    "borrador": {"enviada"},
    "enviada": {"aprobada", "rechazada", "vencida"},
}
PLAZO_VENCIMIENTO_DIAS = 30


class QuotationService:
    def __init__(
        self,
        quotations: QuotationRepository,
        products: ProductRepository,
        clients: ClientRepository,
        db: Session,
        margen_utilidad: Decimal | None = None,
    ):
        self.quotations = quotations
        self.products = products
        self.clients = clients
        self.db = db
        self.margen_utilidad = Decimal(
            margen_utilidad if margen_utilidad is not None else DEFAULT_MARGEN_UTILIDAD
        )

    def _apply_margin(self, detalles: list[dict], product_price_lookup) -> list[dict]:
        margin = self.margen_utilidad / Decimal(100)
        result = []
        for d in detalles:
            cantidad = Decimal(d["cantidad"])
            deprec_descuento = Decimal(d.get("descuento") or 0)
            precio = Decimal(d.get("precio_unitario") or 0)
            if precio > 0:
                precio_unitario = precio
            else:
                producto = product_price_lookup(d["id_producto"])
                if producto is None:
                    raise ProductNotFound("Producto no encontrado")
                base_price = Decimal(str(producto.precio_unitario))
                precio_unitario = (base_price * (1 + margin)).quantize(
                    Decimal("1"), rounding=ROUND_HALF_UP
                )
            subtotal = precio_unitario * cantidad - deprec_descuento
            result.append(
                {
                    "id_producto": d["id_producto"],
                    "descripcion": d.get("descripcion"),
                    "cantidad": int(cantidad),
                    "precio_unitario": precio_unitario,
                    "descuento": deprec_descuento,
                    "subtotal": subtotal,
                }
            )
        return result

    @staticmethod
    def _detailed_to_dicts(quotation: Quotation) -> list[dict]:
        return [
            {
                "id_producto": d.id_producto,
                "descripcion": d.descripcion,
                "cantidad": d.cantidad,
                "precio_unitario": d.precio_unitario,
                "descuento": d.descuento,
                "subtotal": d.subtotal,
            }
            for d in quotation.detalles
        ]

    @staticmethod
    def _compute_totals(detalles: list[dict], descuento: Decimal) -> tuple[Decimal, Decimal, Decimal]:
        subtotal = sum(
            (Decimal(d["subtotal"]) for d in detalles),
            Decimal("0"),
        )
        base = Decimal(max(0, subtotal - descuento))
        impuestos = (base * TAX_RATE).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        total = base + impuestos
        return subtotal, impuestos, total

    def _product_price(self, id_producto: UUID):
        return self.products.get_by_id(id_producto)

    def list(
        self,
        id_cliente: UUID | None = None,
        estado: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Quotation], int]:
        if estado is not None and estado not in VALID_ESTADOS:
            raise InvalidQuotationStatus(
                f"Estado inválido. Permitidos: {', '.join(sorted(VALID_ESTADOS))}"
            )
        return self.quotations.list(
            id_cliente=id_cliente, estado=estado, skip=skip, limit=limit
        )

    def get(self, id_cotizacion: UUID) -> Quotation:
        quotation = self.quotations.get_by_id(id_cotizacion)
        if quotation is None:
            raise QuotationNotFound("Cotización no encontrada")
        return quotation

    def create(
        self,
        *,
        id_cliente: UUID,
        id_usuario: UUID | None,
        detalles: list[dict],
        fecha_vencimiento: datetime | None = None,
        descuento: Decimal = Decimal("0"),
        observaciones: str | None = None,
    ) -> Quotation:
        if self.clients.get_by_id(id_cliente) is None:
            raise ClientNotFound("Cliente no encontrado")
        if not detalles:
            raise InvalidQuotationTransition("La cotización debe tener al menos un detalle")

        detalles_margin = self._apply_margin(detalles, self._product_price)
        subtotal, impuestos, total = self._compute_totals(
            detalles_margin, Decimal(descuento)
        )
        numero = f"COT-{self.quotations.count() + 1:04d}"
        fecha_emision = datetime.now()
        if fecha_vencimiento is None:
            fecha_vencimiento = fecha_emision + timedelta(
                days=PLAZO_VENCIMIENTO_DIAS
            )

        try:
            quotation = self.quotations.create(
                id_cliente=id_cliente,
                id_usuario=id_usuario,
                numero_consecutivo=numero,
                fecha_emision=fecha_emision,
                fecha_vencimiento=fecha_vencimiento,
                estado="borrador",
                subtotal=subtotal,
                impuestos=impuestos,
                descuento=Decimal(descuento),
                total=total,
                observaciones=observaciones,
                detalles=detalles_margin,
            )
            self.db.commit()
            return quotation
        except Exception:
            self.db.rollback()
            raise

    def update(
        self,
        id_cotizacion: UUID,
        *,
        id_cliente: UUID | None = None,
        fecha_vencimiento: datetime | None = None,
        descuento: Decimal | None = None,
        observaciones: str | None = None,
        detalles: list[dict] | None = None,
    ) -> Quotation:
        current = self.get(id_cotizacion)
        if current.estado != "borrador":
            raise InvalidQuotationTransition(
                "Solo se puede editar una cotización en estado borrador"
            )
        if id_cliente is not None and self.clients.get_by_id(id_cliente) is None:
            raise ClientNotFound("Cliente no encontrado")

        if detalles is not None:
            detail_dicts = self._apply_margin(detalles, self._product_price)
        else:
            detail_dicts = self._detailed_to_dicts(current)

        descuento_final = (
            Decimal(descuento) if descuento is not None else current.descuento
        )
        subtotal, impuestos, total = self._compute_totals(detail_dicts, descuento_final)

        try:
            quotation = self.quotations.update(
                id_cotizacion,
                id_cliente=id_cliente or current.id_cliente,
                fecha_vencimiento=(
                    fecha_vencimiento if fecha_vencimiento is not None
                    else current.fecha_vencimiento
                ),
                estado=current.estado,
                subtotal=subtotal,
                impuestos=impuestos,
                descuento=descuento_final,
                total=total,
                observaciones=(
                    observaciones if observaciones is not None else current.observaciones
                ),
                detalles=detail_dicts if detalles is not None else None,
            )
            self.db.commit()
            return quotation
        except Exception:
            self.db.rollback()
            raise

    def update_estado(self, id_cotizacion: UUID, estado: str) -> Quotation:
        if estado not in VALID_ESTADOS:
            raise InvalidQuotationStatus(
                f"Estado inválido. Permitidos: {', '.join(sorted(VALID_ESTADOS))}"
            )
        current = self.get(id_cotizacion)
        if current.estado == estado:
            return current
        if estado not in ALLOWED_TRANSITIONS.get(current.estado, set()):
            raise InvalidQuotationTransition(
                f"No se puede cambiar el estado de '{current.estado}' a '{estado}'"
            )
        try:
            quotation = self.quotations.update_estado(id_cotizacion, estado)
            self.db.commit()
            return quotation
        except Exception:
            self.db.rollback()
            raise

    def delete(self, id_cotizacion: UUID) -> None:
        current = self.get(id_cotizacion)
        if current.estado != "borrador":
            raise InvalidQuotationTransition(
                "Solo se pueden eliminar cotizaciones en estado borrador"
            )
        try:
            self.quotations.delete(id_cotizacion)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise