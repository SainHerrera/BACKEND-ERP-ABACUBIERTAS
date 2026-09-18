from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.entities.purchase_order import PurchaseOrder


class PurchaseOrderRepository(ABC):
    @abstractmethod
    def list(
        self,
        estado: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[PurchaseOrder], int]:
        """Lista órdenes de compra con filtro opcional de estado y paginación."""

    @abstractmethod
    def list_pending_approval(self) -> list[PurchaseOrder]:
        """Lista sin paginación las órdenes pendientes de aprobación."""

    @abstractmethod
    def get_by_id(self, id_orden_compra: UUID) -> PurchaseOrder | None:
        """Obtiene una orden de compra con sus detalles."""

    @abstractmethod
    def count(self) -> int:
        """Cantidad total de órdenes de compra (para numeración consecutiva)."""

    @abstractmethod
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
        """Persiste la orden con sus detalles sin commit; el commit lo controla el llamador."""

    @abstractmethod
    def update_estado(self, id_orden_compra: UUID, estado: str) -> PurchaseOrder | None:
        """Solo cambia el estado de la orden."""

    @abstractmethod
    def apply_reception(
        self,
        id_orden_compra: UUID,
        *,
        id_producto: UUID,
        cantidad_recibida: int,
    ) -> PurchaseOrder | None:
        """Acumula la cantidad recibida en el detalle del producto y hace flush."""