from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.movement import Movement
from app.domain.exceptions import (
    InsufficientStock,
    InvalidMovementType,
    InvalidQuantity,
    ProductNotFound,
)
from app.domain.ports.movement_repository import MovementRepository
from app.domain.ports.product_repository import ProductRepository


class MovementService:
    def __init__(
        self,
        products: ProductRepository,
        movements: MovementRepository,
        db: Session,
    ):
        self.products = products
        self.movements = movements
        self.db = db

    def registrar(
        self,
        *,
        id_producto: UUID,
        tipo: str,
        cantidad: int,
        referencia: str | None = None,
        id_usuario: UUID | None = None,
        nota: str | None = None,
        fecha: datetime | None = None,
    ) -> Movement:
        product = self.products.get_by_id(id_producto)
        if product is None:
            raise ProductNotFound("Producto no encontrado")
        if cantidad <= 0:
            raise InvalidQuantity("La cantidad a ingresar debe ser mayor a 0")

        if tipo == "entrada":
            nuevo_stock = product.stock_actual + cantidad
        elif tipo == "salida":
            if cantidad > product.stock_actual:
                raise InsufficientStock(
                    f'Stock insuficiente para "{product.nombre}". '
                    f"Stock disponible: {product.stock_actual}, solicitado: {cantidad}"
                )
            nuevo_stock = product.stock_actual - cantidad
        elif tipo == "ajuste":
            nuevo_stock = cantidad
        else:
            raise InvalidMovementType("Tipo de movimiento inválido")

        try:
            self.products.update_stock(id_producto, nuevo_stock)
            movement = self.movements.create(
                id_producto=id_producto,
                tipo=tipo,
                cantidad=cantidad,
                referencia=referencia,
                id_usuario=id_usuario,
                nota=nota,
                fecha=fecha,
            )
            self.db.commit()
            return movement
        except Exception:
            self.db.rollback()
            raise