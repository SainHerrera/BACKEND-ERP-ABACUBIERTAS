from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.entities.quotation import Quotation, QuotationDetail
from app.domain.ports.quotation_repository import QuotationRepository
from app.infrastructure.models.client import ClientModel
from app.infrastructure.models.quotation import QuotationDetailModel, QuotationModel


class SQLAlchemyQuotationRepository(QuotationRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_domain(model: QuotationModel, nombre_cliente: str | None = None) -> Quotation:
        detalles = [
            QuotationDetail(
                id_detalle_cotizacion=d.id_detalle_cotizacion,
                id_cotizacion=d.id_cotizacion,
                id_producto=d.id_producto,
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario,
                descuento=d.descuento,
                subtotal=d.subtotal,
                descripcion=d.descripcion,
            )
            for d in model.detalles
        ]
        return Quotation(
            id_cotizacion=model.id_cotizacion,
            numero_consecutivo=model.numero_consecutivo,
            id_cliente=model.id_cliente,
            estado=model.estado,
            fecha_emision=model.fecha_emision,
            fecha_vencimiento=model.fecha_vencimiento,
            subtotal=model.subtotal,
            impuestos=model.impuestos,
            descuento=model.descuento,
            total=model.total,
            observaciones=model.observaciones,
            id_usuario=model.id_usuario,
            detalles=detalles,
            nombre_cliente=nombre_cliente,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _detail_models(id_cotizacion: UUID, detalles: list[dict]) -> list[QuotationDetailModel]:
        return [
            QuotationDetailModel(
                id_cotizacion=id_cotizacion,
                id_producto=d["id_producto"],
                descripcion=d.get("descripcion"),
                cantidad=d["cantidad"],
                precio_unitario=d["precio_unitario"],
                descuento=d.get("descuento") or Decimal("0"),
                subtotal=d["subtotal"],
            )
            for d in detalles
        ]

    def _client_names(self, client_ids: set[UUID]) -> dict[UUID, str]:
        if not client_ids:
            return {}
        rows = (
            self.db.query(ClientModel.id_cliente, ClientModel.nombre_razon_social)
            .filter(ClientModel.id_cliente.in_(client_ids))
            .all()
        )
        return {r[0]: r[1] for r in rows}

    def list(
        self,
        id_cliente: UUID | None = None,
        estado: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Quotation], int]:
        query = self.db.query(QuotationModel)
        if id_cliente is not None:
            query = query.filter(QuotationModel.id_cliente == id_cliente)
        if estado is not None:
            query = query.filter(QuotationModel.estado == estado)
        total = query.count()
        models = (
            query.order_by(QuotationModel.fecha_emision.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        names = self._client_names({m.id_cliente for m in models})
        return [self._to_domain(m, names.get(m.id_cliente)) for m in models], total

    def get_by_id(self, id_cotizacion: UUID) -> Quotation | None:
        model = (
            self.db.query(QuotationModel)
            .filter(QuotationModel.id_cotizacion == id_cotizacion)
            .first()
        )
        if model is None:
            return None
        names = self._client_names({model.id_cliente})
        return self._to_domain(model, names.get(model.id_cliente))

    def count(self) -> int:
        return self.db.query(func.count(QuotationModel.id_cotizacion)).scalar() or 0

    def create(
        self,
        *,
        id_cliente: UUID,
        id_usuario: UUID | None,
        numero_consecutivo: str,
        fecha_emision: datetime,
        fecha_vencimiento: datetime | None,
        estado: str,
        subtotal,
        impuestos,
        descuento,
        total,
        observaciones: str | None,
        detalles: list[dict],
    ) -> Quotation:
        model = QuotationModel(
            id_cliente=id_cliente,
            id_usuario=id_usuario,
            numero_consecutivo=numero_consecutivo,
            fecha_emision=fecha_emision,
            fecha_vencimiento=fecha_vencimiento,
            estado=estado,
            subtotal=subtotal,
            impuestos=impuestos,
            descuento=descuento,
            total=total,
            observaciones=observaciones,
        )
        self.db.add(model)
        self.db.flush()
        model.detalles.extend(self._detail_models(model.id_cotizacion, detalles))
        self.db.flush()
        names = self._client_names({model.id_cliente})
        return self._to_domain(model, names.get(model.id_cliente))

    def update(
        self,
        id_cotizacion: UUID,
        *,
        id_cliente: UUID,
        fecha_vencimiento: datetime | None,
        estado: str,
        subtotal,
        impuestos,
        descuento,
        total,
        observaciones: str | None,
        detalles: list[dict] | None = None,
    ) -> Quotation | None:
        model = (
            self.db.query(QuotationModel)
            .filter(QuotationModel.id_cotizacion == id_cotizacion)
            .first()
        )
        if model is None:
            return None
        model.id_cliente = id_cliente
        model.fecha_vencimiento = fecha_vencimiento
        model.estado = estado
        model.subtotal = subtotal
        model.impuestos = impuestos
        model.descuento = descuento
        model.total = total
        model.observaciones = observaciones
        if detalles is not None:
            self.db.query(QuotationDetailModel).filter(
                QuotationDetailModel.id_cotizacion == id_cotizacion
            ).delete()
            model.detalles.extend(self._detail_models(id_cotizacion, detalles))
        self.db.flush()
        names = self._client_names({model.id_cliente})
        return self._to_domain(model, names.get(model.id_cliente))

    def update_estado(self, id_cotizacion: UUID, estado: str) -> Quotation | None:
        model = (
            self.db.query(QuotationModel)
            .filter(QuotationModel.id_cotizacion == id_cotizacion)
            .first()
        )
        if model is None:
            return None
        model.estado = estado
        self.db.flush()
        names = self._client_names({model.id_cliente})
        return self._to_domain(model, names.get(model.id_cliente))

    def delete(self, id_cotizacion: UUID) -> None:
        self.db.query(QuotationDetailModel).filter(
            QuotationDetailModel.id_cotizacion == id_cotizacion
        ).delete()
        self.db.query(QuotationModel).filter(
            QuotationModel.id_cotizacion == id_cotizacion
        ).delete()
        self.db.flush()