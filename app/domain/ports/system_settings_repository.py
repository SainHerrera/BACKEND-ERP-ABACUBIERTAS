from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.system_settings import SystemSettings


class SystemSettingsRepository(ABC):
    @abstractmethod
    def get(self) -> SystemSettings:
        """Obtiene la fila única de configuración, creándola con defaults si no existe."""

    @abstractmethod
    def update(self, **kwargs) -> SystemSettings:
        """Actualiza los campos no None de la configuración; los None se conservan."""

    @abstractmethod
    def reset(self) -> SystemSettings:
        """Restaura la configuración a los valores por defecto."""