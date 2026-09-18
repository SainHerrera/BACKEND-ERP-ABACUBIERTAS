from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.entities.audit_log_entry import AuditLogEntry


class AuditLogRepository(ABC):
    @abstractmethod
    def create(
        self,
        *,
        fecha: datetime | None,
        id_usuario: UUID | None,
        nombre_usuario: str | None,
        email_usuario: str | None,
        rol_usuario: str | None,
        accion: str,
        detalle: str,
    ) -> AuditLogEntry:
        """Persiste la entrada sin commit; el commit lo controla el llamador."""

    @abstractmethod
    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        usuario: str | None = None,
        accion: str | None = None,
    ) -> tuple[list[AuditLogEntry], int]:
        """Lista entradas con paginación y filtros opcionales de usuario/acción."""

    @abstractmethod
    def clear(self) -> None:
        """Elimina todas las entradas del log."""