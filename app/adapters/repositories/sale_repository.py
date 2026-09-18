from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.entities.sale import Sale, SaleDetail
from app.domain.ports.sale_repository import SaleRepository
from app.infrastructure.models.client import ClientModel
from app.infrastructure.models.sale import SaleDetailModel, SaleModel


class SQLAlchemySaleRepository(SaleRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_domain(model: SaleModel, nombre_cliente: str | None = None) -> Sale:
        detalles = [
            SaleDetail(
                id_detalle_venta=d.id_detalle_venta,
                id_orden_venta=d.id_orden_venta,
                id_producto=d.id_producto,
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario,
                descuento=d.descuento,
                subtotal=d.subtotal,
                descripcion=d.descripcion,
            )
            for d in model.detalles
        ]
        return Sale(
            id_orden_venta=model.id_orden_venta,
            numero_orden=model.numero_orden,
            id_cliente=model.id_cliente,
            estado=model.estado,
            fecha_venta=model.fecha_venta,
            subtotal=model.subtotal,
            impuestos=model.impuestos,
            total=model.total,
            observaciones=model.observaciones,
            id_cotizacion=model.id_cotizacion,
            id_usuario=model.id_usuario,
            detalles=detalles,
            nombre_cliente=nombre_cliente,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _detail_models(id_orden_venta: UUID, detalles: list[dict]) -> list[SaleDetailModel]:
        return [
            SaleDetailModel(
                id_orden_venta=id_orden_venta,
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
    ) -> tuple[list[Sale], int]:
        query = self.db.query(SaleModel)
        if id_cliente is not None:
            query = query.filter(SaleModel.id_cliente == id_cliente)
        if estado is not None:
            query = query.filter(SaleModel.estado == estado)
        total = query.count()
        models = (
            query.order_by(SaleModel.fecha_venta.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        names = self._client_names({m.id_cliente for m in models})
        return [self._to_domain(m, names.get(m.id_cliente)) for m in models], total

    def get_by_id(self, id_orden_venta: UUID) -> Sale | None:
        model = (
            self.db.query(SaleModel)
            .filter(SaleModel.id_orden_venta == id_orden_venta)
            .first()
        )
        if model is None:
            return None
        names = self._client_names({model.id_cliente})
        return self._to_domain(model, names.get(model.id_cliente))

    def count(self) -> int:
        return self.db.query(func.count(SaleModel.id_orden_venta)).scalar() or 0

    def create(
        self,
        *,
        id_cliente: UUID,
        id_usuario: UUID | None,
        id_cotizacion: UUID | None,
        numero_orden: str,
        fecha_venta: datetime,
        estado: str,
        subtotal,
        impuestos,
        total,
        observaciones: str | None,
        detalles: list[dict],
    ) -> Sale:
        model = SaleModel(
            id_cliente=id_cliente,
            id_usuario=id_usuario,
            id_cotizacion=id_cotizacion,
            numero_orden=numero_orden,
            fecha_venta=fecha_venta,
            estado=estado,
            subtotal=subtotal,
            impuestos=impuestos,
            total=total,
            observaciones=observaciones,
        )
        self.db.add(model)
        self.db.flush()
        model.detalles.extend(self._detail_models(model.id_orden_venta, detalles))
        self.db.flush()
        names = self._client_names({model.id_cliente})
        return self._to_domain(model, names.get(model.id_cliente))

    def update(
        self,
        id_orden_venta: UUID,
        *,
        estado: str | None = None,
        observaciones: str | None = None,
    ) -> Sale | None:
        model = (
            self.db.query(SaleModel)
            .filter(SaleModel.id_orden_venta == id_orden_venta)
            .first()
        )
        if model is None:
            return None
        if estado is not None:
            model.estado = estado
        if observaciones is not None:
            model.observaciones = observaciones
        self.db.flush()
        names = self._client_names({model.id_cliente})
        return self._to_domain(model, names.get(model.id_cliente))

    def update_estado(self, id_orden_venta: UUID, estado: str) -> Sale | None:
        model = (
            self.db.query(SaleModel)
            .filter(SaleModel.id_orden_venta == id_orden_venta)
            .first()
        )
        if model is None:
            return None
        model.estado = estado
        self.db.flush()
        names = self._client_names({model.id_cliente})
        return self._to_domain(model, names.get(model.id_cliente))