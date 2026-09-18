from uuid import UUID

from app.domain.entities.provider import Provider
from app.domain.exceptions import (
    DuplicateProviderNit,
    ProviderNotFound,
)
from app.domain.ports.provider_repository import ProviderRepository


class ProviderService:
    def __init__(self, providers: ProviderRepository):
        self.providers = providers

    def create(
        self,
        nombre_empresa: str,
        nit: str,
        **kwargs,
    ) -> Provider:
        if self.providers.get_by_nit(nit) is not None:
            raise DuplicateProviderNit("Ya existe un proveedor registrado con el NIT")
        return self.providers.create(nombre_empresa=nombre_empresa, nit=nit, **kwargs)

    def list(self, search: str | None = None, skip: int = 0, limit: int = 50) -> tuple[list[Provider], int]:
        return self.providers.list(search=search, skip=skip, limit=limit)

    def get(self, provider_id: UUID) -> Provider:
        provider = self.providers.get_by_id(provider_id)
        if provider is None:
            raise ProviderNotFound("Proveedor no encontrado")
        return provider

    def update(self, provider_id: UUID, **fields) -> Provider:
        if fields.get("nit") is not None:
            existing = self.providers.get_by_nit(fields["nit"])
            if existing is not None and existing.id_proveedor != provider_id:
                raise DuplicateProviderNit("Ya existe un proveedor registrado con el NIT")
        provider = self.providers.update(provider_id, **fields)
        if provider is None:
            raise ProviderNotFound("Proveedor no encontrado")
        return provider

    def deactivate(self, provider_id: UUID) -> Provider:
        return self.update(provider_id, estado="inactivo")