from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Provider:
    id_proveedor: UUID
    nombre_empresa: str
    nit: str
    contacto: str | None = None
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None
    ciudad: str | None = None
    categoria_material: str = "general"
    condiciones_pago: str | None = None
    observaciones: str | None = None
    estado: str = "activo"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def activo(self) -> bool:
        return self.estado != "inactivo"