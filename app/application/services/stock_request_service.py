from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.stock_request import StockRequest
from app.domain.exceptions import (
    InvalidQuantity,
    InvalidStockRequestStatus,
    InvalidStockRequestTransition,
    ProductNotFound,
    StockRequestNotFound,
)
from app.domain.ports.product_repository import ProductRepository
from app.domain.ports.stock_request_repository import StockRequestRepository

VALID_ESTADOS = {"pendiente", "aprobada", "atendida", "rechazada"}
ALLOWED_TRANSITIONS = {
    "pendiente": {"aprobada", "rechazada"},
    "aprobada": {"atendida", "rechazada"},
}


class StockRequestService:
    def __init__(
        self,
        requests: StockRequestRepository,
        products: ProductRepository,
        db: Session,
    ):
        self.requests = requests
        self.products = products
        self.db = db

    def list(
        self,
        estado: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[StockRequest], int]:
        if estado is not None and estado not in VALID_ESTADOS:
            raise InvalidStockRequestStatus(
                f"Estado inválido. Permitidos: {', '.join(sorted(VALID_ESTADOS))}"
            )
        return self.requests.list(estado=estado, skip=skip, limit=limit)

    def get(self, id_solicitud: UUID) -> StockRequest:
        request = self.requests.get_by_id(id_solicitud)
        if request is None:
            raise StockRequestNotFound("Solicitud de stock no encontrada")
        return request

    def create(
        self,
        *,
        id_producto: UUID,
        cantidad_sugerida: int,
        observaciones: str | None = None,
        id_usuario: UUID | None = None,
        nombre_usuario: str | None = None,
    ) -> StockRequest:
        product = self.products.get_by_id(id_producto)
        if product is None or not product.activo:
            raise ProductNotFound("Producto no encontrado")
        if not cantidad_sugerida or cantidad_sugerida <= 0:
            raise InvalidQuantity("La cantidad sugerida debe ser mayor a 0")

        numero = f"SOL-{self.requests.count() + 1:04d}"
        try:
            request = self.requests.create(
                numero_solicitud=numero,
                id_producto=id_producto,
                descripcion=product.nombre,
                cantidad_sugerida=int(cantidad_sugerida),
                stock_actual=product.stock_actual,
                stock_minimo=product.stock_minimo,
                fecha=datetime.now(),
                id_usuario=id_usuario,
                nombre_usuario=nombre_usuario,
                observaciones=observaciones,
            )
            self.db.commit()
            return request
        except Exception:
            self.db.rollback()
            raise

    def update_estado(
        self,
        id_solicitud: UUID,
        estado: str,
        id_usuario: UUID | None = None,
        nombre_usuario: str | None = None,
    ) -> StockRequest:
        if estado not in VALID_ESTADOS:
            raise InvalidStockRequestStatus(
                f"Estado inválido. Permitidos: {', '.join(sorted(VALID_ESTADOS))}"
            )
        current = self.get(id_solicitud)
        if current.estado == estado:
            return current
        if estado not in ALLOWED_TRANSITIONS.get(current.estado, set()):
            raise InvalidStockRequestTransition(
                f"No se puede cambiar el estado de '{current.estado}' a '{estado}'"
            )
        try:
            request = self.requests.update_estado(id_solicitud, estado)
            self.db.commit()
            return request
        except Exception:
            self.db.rollback()
            raise