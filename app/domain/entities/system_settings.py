from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class SystemSettings:
    stock_minimo_default: int = 15
    margen_utilidad_default: int = 30
    catalogo_inicial_cargado: bool = True
    aprobacion_oc_habilitada: bool = False
    aprobacion_oc_monto_minimo: Decimal = Decimal("5000000")
    updated_at: datetime | None = None