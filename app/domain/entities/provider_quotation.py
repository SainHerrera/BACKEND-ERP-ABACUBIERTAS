from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class ProviderQuotation:
    id_cotizacion: UUID
    numero_cotizacion: str
    id_solicitud: UUID
    id_producto: UUID
    id_proveedor: UUID
    nombre_proveedor: str | None = None
    precio_unitario: Decimal = Decimal("0")
    tiempo_entrega_dias: int = 0
    condiciones: str | None = None
    fecha: datetime | None = None
    seleccionada: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None