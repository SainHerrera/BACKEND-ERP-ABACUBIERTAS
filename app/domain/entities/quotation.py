from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class QuotationDetail:
    id_detalle_cotizacion: UUID
    id_cotizacion: UUID
    id_producto: UUID
    cantidad: int
    precio_unitario: Decimal
    descuento: Decimal = Decimal("0")
    subtotal: Decimal = Decimal("0")
    descripcion: str | None = None


@dataclass(frozen=True)
class Quotation:
    id_cotizacion: UUID
    numero_consecutivo: str
    id_cliente: UUID
    estado: str = "borrador"
    fecha_emision: datetime | None = None
    fecha_vencimiento: datetime | None = None
    subtotal: Decimal = Decimal("0")
    impuestos: Decimal = Decimal("0")
    descuento: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    observaciones: str | None = None
    id_usuario: UUID | None = None
    detalles: list[QuotationDetail] = field(default_factory=list)
    nombre_cliente: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None