from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Client:
    id_cliente: UUID
    tipo_cliente: str = "empresa"
    nombre_razon_social: str = ""
    nit_cc: str = ""
    nombre_contacto: str | None = None
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None
    ciudad: str | None = None
    observaciones: str | None = None
    estado: str = "activo"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def activo(self) -> bool:
        return self.estado != "inactivo"