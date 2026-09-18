from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.entities.quotation import Quotation


class QuotationRepository(ABC):
    @abstractmethod
    def list(
        self,
        id_cliente: UUID | None = None,
        estado: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Quotation], int]:
        """Lista cotizaciones con filtros opcionales y paginación. Retorna (items, total)."""

    @abstractmethod
    def get_by_id(self, id_cotizacion: UUID) -> Quotation | None:
        """Obtiene una cotización con sus detalles."""

    @abstractmethod
    def count(self) -> int:
        """Cantidad total de cotizaciones (para numeración consecutiva)."""

    @abstractmethod
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
        """Persiste cotización con detalles sin commit; el commit lo controla el llamador."""

    @abstractmethod
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
        """Actualiza cabecera y, si detalles es distinto de None, reemplaza los detalles."""

    @abstractmethod
    def update_estado(self, id_cotizacion: UUID, estado: str) -> Quotation | None:
        """Solo cambia el estado de la cotización."""

    @abstractmethod
    def delete(self, id_cotizacion: UUID) -> None:
        """Elimina físicamente la cotización y sus detalles."""