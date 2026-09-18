from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.client import Client


class ClientRepository(ABC):
    @abstractmethod
    def get_by_id(self, client_id: UUID) -> Client | None:
        """Retorna el cliente por id o None."""

    @abstractmethod
    def get_by_nit_cc(self, nit_cc: str) -> Client | None:
        """Retorna el cliente por NIT/CC o None."""

    @abstractmethod
    def list(
        self,
        search: str | None = None,
        estado: str | None = None,
        tipo: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Client], int]:
        """Lista clientes con filtros opcionales y paginación. Retorna (items, total)."""

    @abstractmethod
    def create(
        self,
        tipo_cliente: str,
        nombre_razon_social: str,
        nit_cc: str,
        *,
        nombre_contacto: str | None = None,
        telefono: str | None = None,
        email: str | None = None,
        direccion: str | None = None,
        ciudad: str | None = None,
        observaciones: str | None = None,
        estado: str = "activo",
    ) -> Client:
        """Persiste un cliente y lo retorna."""

    @abstractmethod
    def update(
        self,
        client_id: UUID,
        *,
        tipo_cliente: str | None = None,
        nombre_razon_social: str | None = None,
        nit_cc: str | None = None,
        nombre_contacto: str | None = None,
        telefono: str | None = None,
        email: str | None = None,
        direccion: str | None = None,
        ciudad: str | None = None,
        observaciones: str | None = None,
        estado: str | None = None,
    ) -> Client | None:
        """Actualiza solo los campos provistos. Retorna el cliente o None si no existe."""