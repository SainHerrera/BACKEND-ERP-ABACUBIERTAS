from decimal import Decimal

from app.domain.entities.system_settings import SystemSettings
from app.domain.ports.system_settings_repository import SystemSettingsRepository
from app.infrastructure.models.system_settings import SystemSettingsModel

DEFAULT_MONTO_APROBACION = Decimal("5000000")


class SQLAlchemySystemSettingsRepository(SystemSettingsRepository):
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _to_domain(model: SystemSettingsModel) -> SystemSettings:
        return SystemSettings(
            stock_minimo_default=model.stock_minimo_default,
            margen_utilidad_default=model.margen_utilidad_default,
            catalogo_inicial_cargado=model.catalogo_inicial_cargado,
            aprobacion_oc_habilitada=model.aprobacion_oc_habilitada,
            aprobacion_oc_monto_minimo=model.aprobacion_oc_monto_minimo,
            updated_at=model.updated_at,
        )

    def _get_or_create_row(self) -> SystemSettingsModel:
        row = self.db.query(SystemSettingsModel).filter(SystemSettingsModel.id == 1).first()
        if row is None:
            row = SystemSettingsModel(id=1)
            self.db.add(row)
            self.db.flush()
        return row

    def get(self) -> SystemSettings:
        return self._to_domain(self._get_or_create_row())

    def update(self, **kwargs) -> SystemSettings:
        row = self._get_or_create_row()
        allowed = {
            "stock_minimo_default",
            "margen_utilidad_default",
            "catalogo_inicial_cargado",
            "aprobacion_oc_habilitada",
            "aprobacion_oc_monto_minimo",
        }
        for key, value in kwargs.items():
            if key in allowed and value is not None:
                setattr(row, key, value)
        self.db.commit()
        return self._to_domain(row)

    def reset(self) -> SystemSettings:
        row = self._get_or_create_row()
        row.stock_minimo_default = 15
        row.margen_utilidad_default = 30
        row.catalogo_inicial_cargado = True
        row.aprobacion_oc_habilitada = False
        row.aprobacion_oc_monto_minimo = DEFAULT_MONTO_APROBACION
        self.db.commit()
        return self._to_domain(row)