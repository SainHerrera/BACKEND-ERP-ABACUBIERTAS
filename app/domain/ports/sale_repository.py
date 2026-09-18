from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.entities.sale import Sale


class SaleRepository(ABC):
    @abstractmethod
    def list(
        self,
        id_cliente: UUID | None = None,
        estado: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Sale], int]:
        """Lista pedidos de venta con filtros opcionales y paginación. Retorna (items, total)."""

    @abstractmethod
    def get_by_id(self, id_orden_venta: UUID) -> Sale | None:
        """Obtiene un pedido de venta con sus detalles."""

    @abstractmethod
    def count(self) -> int:
        """Cantidad total de pedidos de venta (para numeración consecutiva)."""

    @abstractmethod
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
        """Persiste el pedido con sus detalles sin commit; el commit lo controla el llamador."""

    @abstractmethod
    def update(
        self,
        id_orden_venta: UUID,
        *,
        estado: str | None = None,
        observaciones: str | None = None,
    ) -> Sale | None:
        """Actualiza estado y/o observaciones; los valores None se conservan."""

    @abstractmethod
    def update_estado(self, id_orden_venta: UUID, estado: str) -> Sale | None:
        """Solo cambia el estado del pedido."""