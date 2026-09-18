from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.entities.movement import Movement


class MovementRepository(ABC):
    @abstractmethod
    def list(
        self,
        product_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Movement], int]:
        """Lista movimientos con filtros opcionales y paginación. Retorna (items, total)."""

    @abstractmethod
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
        """Persiste un movimiento sin commit; el commit lo controla el llamador."""