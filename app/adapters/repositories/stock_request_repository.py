from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.entities.stock_request import StockRequest
from app.domain.ports.stock_request_repository import StockRequestRepository
from app.infrastructure.models.stock_request import StockRequestModel


class SQLAlchemyStockRequestRepository(StockRequestRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_domain(model: StockRequestModel) -> StockRequest:
        return StockRequest(
            id_solicitud=model.id_solicitud,
            numero_solicitud=model.numero_solicitud,
            id_producto=model.id_producto,
            descripcion=model.descripcion,
            cantidad_sugerida=model.cantidad_sugerida,
            stock_actual=model.stock_actual,
            stock_minimo=model.stock_minimo,
            estado=model.estado,
            fecha=model.fecha,
            id_usuario=model.id_usuario,
            nombre_usuario=model.nombre_usuario,
            observaciones=model.observaciones,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def list(
        self,
        estado: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[StockRequest], int]:
        query = self.db.query(StockRequestModel)
        if estado is not None:
            query = query.filter(StockRequestModel.estado == estado)
        total = query.count()
        models = (
            query.order_by(StockRequestModel.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models], total

    def get_by_id(self, id_solicitud: UUID) -> StockRequest | None:
        model = (
            self.db.query(StockRequestModel)
            .filter(StockRequestModel.id_solicitud == id_solicitud)
            .first()
        )
        if model is None:
            return None
        return self._to_domain(model)

    def count(self) -> int:
        return self.db.query(func.count(StockRequestModel.id_solicitud)).scalar() or 0

    def create(
        self,
        *,
        numero_solicitud: str,
        id_producto: UUID,
        descripcion: str,
        cantidad_sugerida: int,
        stock_actual: int,
        stock_minimo: int,
        fecha: datetime | None,
        id_usuario: UUID | None,
        nombre_usuario: str | None,
        observaciones: str | None,
    ) -> StockRequest:
        model = StockRequestModel(
            numero_solicitud=numero_solicitud,
            id_producto=id_producto,
            descripcion=descripcion,
            cantidad_sugerida=cantidad_sugerida,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            fecha=fecha or datetime.now(),
            id_usuario=id_usuario,
            nombre_usuario=nombre_usuario,
            observaciones=observaciones,
        )
        self.db.add(model)
        self.db.flush()
        return self._to_domain(model)

    def update_estado(self, id_solicitud: UUID, estado: str) -> StockRequest | None:
        model = (
            self.db.query(StockRequestModel)
            .filter(StockRequestModel.id_solicitud == id_solicitud)
            .first()
        )
        if model is None:
            return None
        model.estado = estado
        self.db.flush()
        return self._to_domain(model)