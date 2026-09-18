from uuid import UUID

from app.domain.entities.product import Product
from app.domain.exceptions import (
    DuplicateProductName,
    ProductNotFound,
    ProviderNotFound,
)
from app.domain.ports.product_repository import ProductRepository
from app.domain.ports.provider_repository import ProviderRepository


class ProductService:
    def __init__(self, products: ProductRepository, providers: ProviderRepository):
        self.products = products
        self.providers = providers

    def _validar_proveedor(self, id_proveedor: UUID | None) -> None:
        if id_proveedor is not None and self.providers.get_by_id(id_proveedor) is None:
            raise ProviderNotFound("Proveedor no encontrado")

    def create(
        self,
        nombre: str,
        *,
        descripcion: str | None = None,
        unidad_medida: str = "unidad",
        precio_unitario: float = 0.0,
        stock_inicial: int | None = None,
        stock_minimo: int = 15,
        id_proveedor: UUID | None = None,
    ) -> Product:
        if self.products.get_by_nombre(nombre) is not None:
            raise DuplicateProductName("Ya existe un producto registrado con ese nombre")
        self._validar_proveedor(id_proveedor)
        stock_actual = stock_inicial if stock_inicial is not None else 0
        return self.products.create(
            nombre=nombre,
            descripcion=descripcion,
            unidad_medida=unidad_medida,
            precio_unitario=precio_unitario,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            id_proveedor=id_proveedor,
        )

    def list(self, search: str | None = None, skip: int = 0, limit: int = 50) -> tuple[list[Product], int]:
        return self.products.list(search=search, skip=skip, limit=limit)

    def get(self, product_id: UUID) -> Product:
        product = self.products.get_by_id(product_id)
        if product is None:
            raise ProductNotFound("Producto no encontrado")
        return product

    def update(self, product_id: UUID, **fields) -> Product:
        if "nombre" in fields and fields["nombre"] is not None:
            existing = self.products.get_by_nombre(fields["nombre"])
            if existing is not None and existing.id_producto != product_id:
                raise DuplicateProductName("Ya existe un producto registrado con ese nombre")
        if fields.get("id_proveedor") is not None:
            self._validar_proveedor(fields["id_proveedor"])
        product = self.products.update(product_id, **fields)
        if product is None:
            raise ProductNotFound("Producto no encontrado")
        return product

    def deactivate(self, product_id: UUID) -> Product:
        product = self.products.set_activo(product_id, activo=False)
        if product is None:
            raise ProductNotFound("Producto no encontrado")
        return product