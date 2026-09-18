from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.entities.purchase_order import PurchaseOrder, PurchaseOrderDetail
from app.domain.exceptions import ProductNotInOrder
from app.domain.ports.purchase_order_repository import PurchaseOrderRepository
from app.infrastructure.models.purchase_order import (
    PurchaseOrderDetailModel,
    PurchaseOrderModel,
)


class SQLAlchemyPurchaseOrderRepository(PurchaseOrderRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_domain(model: PurchaseOrderModel) -> PurchaseOrder:
        detalles = [
            PurchaseOrderDetail(
                id_detalle_oc=d.id_detalle_oc,
                id_orden_compra=d.id_orden_compra,
                id_producto=d.id_producto,
                descripcion=d.descripcion,
                cantidad_ordenada=d.cantidad_ordenada,
                cantidad_recibida=d.cantidad_recibida,
                precio_unitario=d.precio_unitario,
                tiempo_entrega_dias=d.tiempo_entrega_dias,
            )
            for d in model.detalles
        ]
        return PurchaseOrder(
            id_orden_compra=model.id_orden_compra,
            numero_oc=model.numero_oc,
            id_proveedor=model.id_proveedor,
            estado=model.estado,
            fecha_emision=model.fecha_emision,
            observaciones=model.observaciones,
            id_solicitud=model.id_solicitud,
            numero_solicitud=model.numero_solicitud,
            id_cotizacion=model.id_cotizacion,
            nombre_proveedor=model.nombre_proveedor,
            detalles=detalles,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _detail_models(id_orden_compra: UUID, detalles: list[dict]) -> list[PurchaseOrderDetailModel]:
        return [
            PurchaseOrderDetailModel(
                id_orden_compra=id_orden_compra,
                id_producto=d["id_producto"],
                descripcion=d.get("descripcion"),
                cantidad_ordenada=d["cantidad_ordenada"],
                cantidad_recibida=d.get("cantidad_recibida") or 0,
                precio_unitario=d["precio_unitario"],
                tiempo_entrega_dias=d.get("tiempo_entrega_dias"),
            )
            for d in detalles
        ]

    def list(
        self,
        estado: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[PurchaseOrder], int]:
        query = self.db.query(PurchaseOrderModel)
        if estado is not None:
            query = query.filter(PurchaseOrderModel.estado == estado)
        total = query.count()
        models = (
            query.order_by(PurchaseOrderModel.fecha_emision.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models], total

    def list_pending_approval(self) -> list[PurchaseOrder]:
        models = (
            self.db.query(PurchaseOrderModel)
            .filter(PurchaseOrderModel.estado == "pendiente_aprobacion")
            .order_by(PurchaseOrderModel.fecha_emision.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_by_id(self, id_orden_compra: UUID) -> PurchaseOrder | None:
        model = (
            self.db.query(PurchaseOrderModel)
            .filter(PurchaseOrderModel.id_orden_compra == id_orden_compra)
            .first()
        )
        if model is None:
            return None
        return self._to_domain(model)

    def count(self) -> int:
        return self.db.query(func.count(PurchaseOrderModel.id_orden_compra)).scalar() or 0

    def create(
        self,
        *,
        id_proveedor: UUID,
        nombre_proveedor: str | None,
        numero_oc: str,
        fecha_emision: datetime,
        estado: str,
        observaciones: str | None,
        id_solicitud: UUID | None,
        numero_solicitud: str | None,
        id_cotizacion: UUID | None,
        detalles: list[dict],
    ) -> PurchaseOrder:
        model = PurchaseOrderModel(
            id_proveedor=id_proveedor,
            nombre_proveedor=nombre_proveedor,
            numero_oc=numero_oc,
            fecha_emision=fecha_emision,
            estado=estado,
            observaciones=observaciones,
            id_solicitud=id_solicitud,
            numero_solicitud=numero_solicitud,
            id_cotizacion=id_cotizacion,
        )
        self.db.add(model)
        self.db.flush()
        model.detalles.extend(self._detail_models(model.id_orden_compra, detalles))
        self.db.flush()
        return self._to_domain(model)

    def update_estado(self, id_orden_compra: UUID, estado: str) -> PurchaseOrder | None:
        model = (
            self.db.query(PurchaseOrderModel)
            .filter(PurchaseOrderModel.id_orden_compra == id_orden_compra)
            .first()
        )
        if model is None:
            return None
        model.estado = estado
        self.db.flush()
        return self._to_domain(model)

    def apply_reception(
        self,
        id_orden_compra: UUID,
        *,
        id_producto: UUID,
        cantidad_recibida: int,
    ) -> PurchaseOrder | None:
        model = (
            self.db.query(PurchaseOrderModel)
            .filter(PurchaseOrderModel.id_orden_compra == id_orden_compra)
            .first()
        )
        if model is None:
            return None
        detail = next(
            (d for d in model.detalles if d.id_producto == id_producto), None
        )
        if detail is None:
            raise ProductNotInOrder(
                f"El producto con ID {id_producto} no pertenece a la orden {model.numero_oc}"
            )
        detail.cantidad_recibida = cantidad_recibida
        self.db.flush()
        return self._to_domain(model)