from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.movement import Movement
from app.domain.ports.movement_repository import MovementRepository
from app.infrastructure.models.movement import MovementModel


class SQLAlchemyMovementRepository(MovementRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_domain(model: MovementModel) -> Movement:
        return Movement(
            id_movimiento=model.id_movimiento,
            id_producto=model.id_producto,
            tipo=model.tipo,
            cantidad=model.cantidad,
            referencia=model.referencia,
            id_usuario=model.id_usuario,
            fecha=model.fecha,
            nota=model.nota,
        )

    def list(
        self,
        product_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Movement], int]:
        query = self.db.query(MovementModel)
        if product_id is not None:
            query = query.filter(MovementModel.id_producto == product_id)
        if date_from is not None:
            query = query.filter(MovementModel.fecha >= date_from)
        if date_to is not None:
            query = query.filter(MovementModel.fecha <= date_to)
        total = query.count()
        models = query.order_by(MovementModel.fecha.desc()).offset(skip).limit(limit).all()
        return [self._to_domain(model) for model in models], total

    def create(
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
        model = MovementModel(
            id_producto=id_producto,
            tipo=tipo,
            cantidad=cantidad,
            referencia=referencia,
            id_usuario=id_usuario,
            nota=nota,
            fecha=fecha,
        )
        self.db.add(model)
        self.db.flush()
        return self._to_domain(model)