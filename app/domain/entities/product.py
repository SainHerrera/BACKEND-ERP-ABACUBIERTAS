from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Product:
    id_producto: UUID
    nombre: str
    descripcion: str | None = None
    unidad_medida: str = "unidad"
    precio_unitario: float = 0.0
    stock_actual: int = 0
    stock_minimo: int = 15
    id_proveedor: UUID | None = None
    nombre_proveedor: str | None = None
    activo: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def low_stock(self) -> bool:
        return self.stock_actual <= self.stock_minimo

    @property
    def status(self) -> str:
        return "low" if self.low_stock else "normal"