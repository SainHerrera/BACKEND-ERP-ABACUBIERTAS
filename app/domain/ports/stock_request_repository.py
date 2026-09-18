from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.entities.stock_request import StockRequest


class StockRequestRepository(ABC):
    @abstractmethod
    def list(
        self,
        estado: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[StockRequest], int]:
        """Lista solicitudes de stock con filtro opcional de estado y paginación."""

    @abstractmethod
    def get_by_id(self, id_solicitud: UUID) -> StockRequest | None:
        """Obtiene una solicitud de stock por su ID."""

    @abstractmethod
    def count(self) -> int:
        """Cantidad total de solicitudes (para numeración consecutiva)."""

    @abstractmethod
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
        """Persiste la solicitud sin commit; el commit lo controla el llamador."""

    @abstractmethod
    def update_estado(self, id_solicitud: UUID, estado: str) -> StockRequest | None:
        """Solo cambia el estado de la solicitud."""