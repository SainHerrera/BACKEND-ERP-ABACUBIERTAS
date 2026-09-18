from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AuditLogEntry:
    id: UUID
    fecha: datetime | None = None
    id_usuario: UUID | None = None
    nombre_usuario: str | None = None
    email_usuario: str | None = None
    rol_usuario: str | None = None
    accion: str | None = None
    detalle: str | None = None