from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.domain.entities.provider_quotation import ProviderQuotation


class ProviderQuotationRepository(ABC):
    @abstractmethod
    def list(
        self,
        id_solicitud: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ProviderQuotation], int]:
        """Lista cotizaciones de proveedor con filtro opcional por solicitud."""

    @abstractmethod
    def get_by_id(self, id_cotizacion: UUID) -> ProviderQuotation | None:
        """Obtiene una cotización por su ID."""

    @abstractmethod
    def count(self) -> int:
        """Cantidad total de cotizaciones (para numeración consecutiva)."""

    @abstractmethod
    def count_by_solicitud(self, id_solicitud: UUID) -> int:
        """Cantidad de cotizaciones registradas para una solicitud."""

    @abstractmethod
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
        """Persiste la cotización sin commit; el commit lo controla el llamador."""

    @abstractmethod
    def set_seleccionada(self, id_cotizacion: UUID, seleccionada: bool) -> ProviderQuotation | None:
        """Marca/desmarca una cotización como seleccionada."""