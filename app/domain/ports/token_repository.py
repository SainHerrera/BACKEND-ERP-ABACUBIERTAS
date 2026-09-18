from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.entities.revoked_token import RevokedToken


class TokenRevocationRepository(ABC):
    @abstractmethod
    def add(self, jti: str, user_id: UUID | None, expires_at: datetime) -> RevokedToken:
        """Registra un token como revocado (idempotente)."""

    @abstractmethod
    def exists(self, jti: str) -> bool:
        """Retorna True si el jti está revocado."""

    @abstractmethod
    def purge_expired(self) -> None:
        """Elimina las revocaciones cuyas tokens ya expiraron."""