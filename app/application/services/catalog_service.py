from uuid import UUID

from app.domain.entities.provider import Provider
from app.domain.ports.product_repository import ProductRepository
from app.domain.ports.provider_repository import ProviderRepository
from app.domain.ports.system_settings_repository import SystemSettingsRepository
from app.infrastructure.catalog_seed import SEED_PRODUCTS, SEED_PROVIDERS


class CatalogService:
    """Población del catálogo inicial (proveedores + productos).

    Espejo del comportamiento del StorageEngine.loadInitialCatalog del frontend:
    solo inserta cuando la tabla correspondiente está vacía (idempotente) y marca
    `catalogo_inicial_cargado = true` en system_settings.
    """

    def __init__(
        self,
        providers: ProviderRepository,
        products: ProductRepository,
        settings: SystemSettingsRepository,
    ) -> None:
        self.providers = providers
        self.products = products
        self.settings = settings

    def load(self) -> dict[str, int]:
        _, provider_total = self.providers.list(skip=0, limit=1)
        provider_ids = {p.nombre_empresa: p.id_proveedor for p in self._all_providers()}

        inserted_providers = 0
        if provider_total == 0:
            for data in SEED_PROVIDERS:
                provider = self.providers.create(**data)
                provider_ids[provider.nombre_empresa] = provider.id_proveedor
                inserted_providers += 1

        _, product_total = self.products.list(skip=0, limit=1)
        inserted_products = 0
        if product_total == 0:
            for data in SEED_PRODUCTS:
                payload = dict(data)
                nombre_proveedor = payload.pop("nombre_proveedor", None)
                self.products.create(
                    **payload,
                    id_proveedor=provider_ids.get(nombre_proveedor) if nombre_proveedor else None,
                )
                inserted_products += 1

        self.settings.update(catalogo_inicial_cargado=True)
        return {"products": inserted_products, "providers": inserted_providers}

    def _all_providers(self) -> list[Provider]:
        providers, _ = self.providers.list(skip=0, limit=500)
        return providers