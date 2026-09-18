from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.provider import Provider


class ProviderRepository(ABC):
    @abstractmethod
    def get_by_id(self, provider_id: UUID) -> Provider | None:
        """Retorna el proveedor por id o None."""

    @abstractmethod
    def get_by_nit(self, nit: str) -> Provider | None:
        """Retorna el proveedor por nit o None."""

    @abstractmethod
    def list(
        self, search: str | None = None, skip: int = 0, limit: int = 50
    ) -> tuple[list[Provider], int]:
        """Lista proveedores con búsqueda opcional y paginación. Retorna (items, total)."""

    @abstractmethod
    def create(
        self,
        nombre_empresa: str,
        nit: str,
        *,
        contacto: str | None = None,
        telefono: str | None = None,
        email: str | None = None,
        direccion: str | None = None,
        ciudad: str | None = None,
        categoria_material: str = "general",
        condiciones_pago: str | None = None,
        observaciones: str | None = None,
        estado: str = "activo",
    ) -> Provider:
        """Persiste un proveedor y lo retorna."""

    @abstractmethod
    def update(
        self,
        provider_id: UUID,
        *,
        nombre_empresa: str | None = None,
        nit: str | None = None,
        contacto: str | None = None,
        telefono: str | None = None,
        email: str | None = None,
        direccion: str | None = None,
        ciudad: str | None = None,
        categoria_material: str | None = None,
        condiciones_pago: str | None = None,
        observaciones: str | None = None,
        estado: str | None = None,
    ) -> Provider | None:
        """Actualiza solo los campos provistos. Retorna el proveedor o None si no existe."""