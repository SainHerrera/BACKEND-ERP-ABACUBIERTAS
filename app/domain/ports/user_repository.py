from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        """Retorna el usuario por email o None."""

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User | None:
        """Retorna el usuario por id o None."""

    @abstractmethod
    def list_users(self, rol: str | None = None, status: bool | None = None) -> list[User]:
        """Lista usuarios aplicando filtros opcionales de rol y estado."""

    @abstractmethod
    def create(self, name: str, email: str, password: str, rol: str) -> User:
        """Persiste un nuevo usuario y lo retorna con sus valores de BD."""

    @abstractmethod
    def update(
        self,
        user_id: UUID,
        *,
        name: str | None = None,
        email: str | None = None,
        password: str | None = None,
        rol: str | None = None,
        status: bool | None = None,
    ) -> User | None:
        """Actualiza solo los campos provistos. Retorna el usuario o None si no existe."""