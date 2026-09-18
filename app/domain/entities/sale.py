from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class SaleDetail:
    id_detalle_venta: UUID
    id_orden_venta: UUID
    id_producto: UUID
    cantidad: int
    precio_unitario: Decimal
    descuento: Decimal = Decimal("0")
    subtotal: Decimal = Decimal("0")
    descripcion: str | None = None


@dataclass(frozen=True)
class Sale:
    id_orden_venta: UUID
    numero_orden: str
    id_cliente: UUID
    estado: str = "pendiente"
    fecha_venta: datetime | None = None
    subtotal: Decimal = Decimal("0")
    impuestos: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    observaciones: str | None = None
    id_cotizacion: UUID | None = None
    id_usuario: UUID | None = None
    detalles: list[SaleDetail] = field(default_factory=list)
    nombre_cliente: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None