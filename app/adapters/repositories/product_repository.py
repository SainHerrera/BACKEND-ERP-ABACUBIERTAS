from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domain.entities.product import Product
from app.domain.ports.product_repository import ProductRepository
from app.infrastructure.models.product import ProductModel
from app.infrastructure.models.provider import ProviderModel


class SQLAlchemyProductRepository(ProductRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_domain(model: ProductModel, nombre_proveedor: str | None = None) -> Product:
        return Product(
            id_producto=model.id_producto,
            nombre=model.nombre,
            descripcion=model.descripcion,
            unidad_medida=model.unidad_medida,
            precio_unitario=float(model.precio_unitario),
            stock_actual=model.stock_actual,
            stock_minimo=model.stock_minimo,
            id_proveedor=model.id_proveedor,
            nombre_proveedor=nombre_proveedor,
            activo=model.activo,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _query_with_provider(self):
        return (
            self.db.query(ProductModel, ProviderModel.nombre_empresa)
            .outerjoin(ProviderModel, ProductModel.id_proveedor == ProviderModel.id_proveedor)
        )

    def _row_to_domain(self, row) -> Product:
        model, nombre_proveedor = row
        return self._to_domain(model, nombre_proveedor)

    def get_by_id(self, product_id: UUID) -> Product | None:
        row = (
            self._query_with_provider()
            .filter(ProductModel.id_producto == product_id)
            .first()
        )
        return self._row_to_domain(row) if row else None

    def get_by_nombre(self, nombre: str) -> Product | None:
        model = self.db.query(ProductModel).filter(ProductModel.nombre == nombre).first()
        return self._to_domain(model) if model else None

    def list(
        self, search: str | None = None, skip: int = 0, limit: int = 50
    ) -> tuple[list[Product], int]:
        query = self._query_with_provider()
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(ProductModel.nombre.ilike(pattern), ProductModel.descripcion.ilike(pattern))
            )
        total = query.count()
        rows = query.order_by(ProductModel.created_at.desc()).offset(skip).limit(limit).all()
        return [self._row_to_domain(row) for row in rows], total

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
        model = ProductModel(
            nombre=nombre,
            descripcion=descripcion,
            unidad_medida=unidad_medida,
            precio_unitario=precio_unitario,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            id_proveedor=id_proveedor,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self.get_by_id(model.id_producto)

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
        row = (
            self._query_with_provider()
            .filter(ProductModel.id_producto == product_id)
            .first()
        )
        if row is None:
            return None
        model, _ = row
        if nombre is not None:
            model.nombre = nombre
        if descripcion is not None:
            model.descripcion = descripcion
        if unidad_medida is not None:
            model.unidad_medida = unidad_medida
        if precio_unitario is not None:
            model.precio_unitario = precio_unitario
        if stock_minimo is not None:
            model.stock_minimo = stock_minimo
        if id_proveedor is not None:
            model.id_proveedor = id_proveedor
        self.db.commit()
        self.db.refresh(model)
        return self.get_by_id(product_id)

    def set_activo(self, product_id: UUID, activo: bool) -> Product | None:
        model = self.db.query(ProductModel).filter(ProductModel.id_producto == product_id).first()
        if model is None:
            return None
        model.activo = activo
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def update_stock(self, product_id: UUID, stock_actual: int) -> None:
        model = self.db.query(ProductModel).filter(ProductModel.id_producto == product_id).first()
        if model is not None:
            model.stock_actual = stock_actual
            self.db.flush()