from app.domain.entities.system_settings import SystemSettings
from app.domain.ports.system_settings_repository import SystemSettingsRepository

VALID_FIELDS = {
    "stock_minimo_default",
    "margen_utilidad_default",
    "catalogo_inicial_cargado",
    "aprobacion_oc_habilitada",
    "aprobacion_oc_monto_minimo",
}


class SystemSettingsService:
    def __init__(self, settings: SystemSettingsRepository):
        self.settings = settings

    def get(self) -> SystemSettings:
        return self.settings.get()

    def update(self, **payload) -> SystemSettings:
        allowed = {k: v for k, v in payload.items() if k in VALID_FIELDS}
        return self.settings.update(**allowed)

    def reset(self) -> SystemSettings:
        return self.settings.reset()

    def margen_utilidad(self) -> int:
        return self.settings.get().margen_utilidad_default