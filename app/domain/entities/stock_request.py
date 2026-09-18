from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class StockRequest:
    id_solicitud: UUID
    numero_solicitud: str
    id_producto: UUID
    descripcion: str
    cantidad_sugerida: int
    stock_actual: int
    stock_minimo: int
    estado: str = "pendiente"
    fecha: datetime | None = None
    id_usuario: UUID | None = None
    nombre_usuario: str | None = None
    observaciones: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None