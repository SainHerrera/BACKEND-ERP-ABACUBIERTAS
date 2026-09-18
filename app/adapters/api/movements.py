from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.adapters.deps import get_current_user, require_roles
from app.adapters.repositories.movement_repository import SQLAlchemyMovementRepository
from app.adapters.repositories.product_repository import SQLAlchemyProductRepository
from app.adapters.schemas import (
    MovementAdjustmentCreate,
    MovementEntryCreate,
    MovementOutputCreate,
    MovementRead,
    Page,
)
from app.application.services.movement_service import MovementService
from app.domain.entities.user import User
from app.domain.exceptions import (
    InsufficientStock,
    InvalidMovementType,
    InvalidQuantity,
    ProductNotFound,
)
from app.infrastructure.db import get_db

router = APIRouter(prefix="/movements", tags=["movements"])

WRITE_ROLES = ("admin", "bodega")


def _build_service(db: Session) -> MovementService:
    return MovementService(
        SQLAlchemyProductRepository(db),
        SQLAlchemyMovementRepository(db),
        db,
    )


@router.get("", response_model=Page[MovementRead])
def list_movements(
    product_id: UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[MovementRead]:
    items, total = _build_service(db).movements.list(
        product_id=product_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
    return Page(items=items, total=total, skip=skip, limit=limit)


def _registrar(
    db: Session,
    tipo: str,
    data: MovementEntryCreate,
    current_user: User,
) -> MovementRead:
    service = _build_service(db)
    try:
        return service.registrar(
            id_producto=data.product_id,
            tipo=tipo,
            cantidad=data.quantity,
            referencia=data.reference,
            id_usuario=current_user.id,
            nota=data.note,
            fecha=data.fecha,
        )
    except ProductNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    except (InsufficientStock, InvalidQuantity, InvalidMovementType) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/entry", response_model=MovementRead, status_code=status.HTTP_201_CREATED)
def create_entry(
    data: MovementEntryCreate,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> MovementRead:
    return _registrar(db, "entrada", data, current_user)


@router.post("/output", response_model=MovementRead, status_code=status.HTTP_201_CREATED)
def create_output(
    data: MovementOutputCreate,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> MovementRead:
    return _registrar(db, "salida", data, current_user)


@router.post("/adjustment", response_model=MovementRead, status_code=status.HTTP_201_CREATED)
def create_adjustment(
    data: MovementAdjustmentCreate,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> MovementRead:
    return _registrar(db, "ajuste", data, current_user)