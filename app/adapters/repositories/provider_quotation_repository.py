from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, update
from sqlalchemy.orm import Session

from app.domain.entities.provider_quotation import ProviderQuotation
from app.domain.ports.provider_quotation_repository import ProviderQuotationRepository
from app.infrastructure.models.provider_quotation import ProviderQuotationModel


class SQLAlchemyProviderQuotationRepository(ProviderQuotationRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_domain(model: ProviderQuotationModel) -> ProviderQuotation:
        return ProviderQuotation(
            id_cotizacion=model.id_cotizacion,
            numero_cotizacion=model.numero_cotizacion,
            id_solicitud=model.id_solicitud,
            id_producto=model.id_producto,
            id_proveedor=model.id_proveedor,
            nombre_proveedor=model.nombre_proveedor,
            precio_unitario=model.precio_unitario,
            tiempo_entrega_dias=model.tiempo_entrega_dias,
            condiciones=model.condiciones,
            fecha=model.fecha,
            seleccionada=model.seleccionada,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def list(
        self,
        id_solicitud: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ProviderQuotation], int]:
        query = self.db.query(ProviderQuotationModel)
        if id_solicitud is not None:
            query = query.filter(ProviderQuotationModel.id_solicitud == id_solicitud)
        total = query.count()
        models = (
            query.order_by(ProviderQuotationModel.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models], total

    def get_by_id(self, id_cotizacion: UUID) -> ProviderQuotation | None:
        model = (
            self.db.query(ProviderQuotationModel)
            .filter(ProviderQuotationModel.id_cotizacion == id_cotizacion)
            .first()
        )
        if model is None:
            return None
        return self._to_domain(model)

    def count(self) -> int:
        return self.db.query(func.count(ProviderQuotationModel.id_cotizacion)).scalar() or 0

    def count_by_solicitud(self, id_solicitud: UUID) -> int:
        return (
            self.db.query(func.count(ProviderQuotationModel.id_cotizacion))
            .filter(ProviderQuotationModel.id_solicitud == id_solicitud)
            .scalar()
            or 0
        )

    def create(
        self,
        *,
        numero_cotizacion: str,
        id_solicitud: UUID,
        id_producto: UUID,
        id_proveedor: UUID,
        nombre_proveedor: str | None,
        precio_unitario: Decimal,
        tiempo_entrega_dias: int,
        condiciones: str | None,
        fecha: datetime | None,
        seleccionada: bool,
    ) -> ProviderQuotation:
        model = ProviderQuotationModel(
            numero_cotizacion=numero_cotizacion,
            id_solicitud=id_solicitud,
            id_producto=id_producto,
            id_proveedor=id_proveedor,
            nombre_proveedor=nombre_proveedor,
            precio_unitario=precio_unitario,
            tiempo_entrega_dias=tiempo_entrega_dias,
            condiciones=condiciones,
            fecha=fecha or datetime.now(),
            seleccionada=seleccionada,
        )
        self.db.add(model)
        self.db.flush()
        return self._to_domain(model)

    def set_seleccionada(self, id_cotizacion: UUID, seleccionada: bool) -> ProviderQuotation | None:
        model = (
            self.db.query(ProviderQuotationModel)
            .filter(ProviderQuotationModel.id_cotizacion == id_cotizacion)
            .first()
        )
        if model is None:
            return None
        if seleccionada:
            self.db.execute(
                update(ProviderQuotationModel)
                .where(ProviderQuotationModel.id_solicitud == model.id_solicitud)
                .values(seleccionada=False)
            )
            self.db.flush()
        model.seleccionada = seleccionada
        self.db.flush()
        return self._to_domain(model)