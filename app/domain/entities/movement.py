from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Movement:
    id_movimiento: UUID
    id_producto: UUID
    tipo: str
    cantidad: int
    referencia: str | None = None
    id_usuario: UUID | None = None
    fecha: datetime | None = None
    nota: str | None = None