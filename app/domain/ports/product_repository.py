from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.product import Product


class ProductRepository(ABC):
    @abstractmethod
    def get_by_id(self, product_id: UUID) -> Product | None:
        """Retorna el producto (con nombre_proveedor) por id o None."""

    @abstractmethod
    def get_by_nombre(self, nombre: str) -> Product | None:
        """Retorna el producto por nombre o None."""

    @abstractmethod
    def list(
        self, search: str | None = None, skip: int = 0, limit: int = 50
    ) -> tuple[list[Product], int]:
        """Lista productos con búsqueda opcional y paginación. Retorna (items, total)."""

    @abstractmethod
    def create(
        self,
        nombre: str,
        *,
        descripcion: str | None = None,
        unidad_medida: str = "unidad",
        precio_unitario: float = 0.0,
        stock_actual: int = 0,
        stock_minimo: int = 15,
        id_proveedor: UUID | None = None,
    ) -> Product:
        """Persiste un producto y lo retorna."""

    @abstractmethod
    def update(
        self,
        product_id: UUID,
        *,
        nombre: str | None = None,
        descripcion: str | None = None,
        unidad_medida: str | None = None,
        precio_unitario: float | None = None,
        stock_minimo: int | None = None,
        id_proveedor: UUID | None = None,
    ) -> Product | None:
        """Actualiza solo los campos provistos. Retorna el producto o None si no existe."""

    @abstractmethod
    def set_activo(self, product_id: UUID, activo: bool) -> Product | None:
        """Activa/desactiva un producto (soft delete)."""

    @abstractmethod
    def update_stock(self, product_id: UUID, stock_actual: int) -> None:
        """Actualiza el stock sin commit; el commit lo controla el llamador."""