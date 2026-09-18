from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class PurchaseOrderDetail:
    id_detalle_oc: UUID
    id_orden_compra: UUID
    id_producto: UUID
    cantidad_ordenada: int
    precio_unitario: Decimal
    cantidad_recibida: int = 0
    tiempo_entrega_dias: int | None = None
    descripcion: str | None = None


@dataclass(frozen=True)
class PurchaseOrder:
    id_orden_compra: UUID
    numero_oc: str
    id_proveedor: UUID
    estado: str = "pendiente_aprobacion"
    fecha_emision: datetime | None = None
    observaciones: str | None = None
    id_solicitud: UUID | None = None
    numero_solicitud: str | None = None
    id_cotizacion: UUID | None = None
    nombre_proveedor: str | None = None
    detalles: list[PurchaseOrderDetail] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def total(self) -> Decimal:
        return sum(
            (Decimal(d.cantidad_ordenada) * Decimal(d.precio_unitario) for d in self.detalles),
            Decimal("0"),
        )