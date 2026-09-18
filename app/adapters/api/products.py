from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.adapters.deps import get_current_user, require_roles
from app.adapters.repositories.product_repository import SQLAlchemyProductRepository
from app.adapters.repositories.provider_repository import SQLAlchemyProviderRepository
from app.adapters.schemas import Page, ProductCreate, ProductRead, ProductUpdate
from app.application.services.product_service import ProductService
from app.domain.entities.user import User
from app.domain.exceptions import (
    DuplicateProductName,
    ProductNotFound,
    ProviderNotFound,
)
from app.infrastructure.db import get_db

router = APIRouter(prefix="/products", tags=["products"])

WRITE_ROLES = ("admin", "compras")


def _build_service(db: Session) -> ProductService:
    return ProductService(
        SQLAlchemyProductRepository(db),
        SQLAlchemyProviderRepository(db),
    )


@router.get("", response_model=Page[ProductRead])
def list_products(
    search: str | None = Query(default=None, max_length=150),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[ProductRead]:
    items, total = _build_service(db).list(search=search, skip=skip, limit=limit)
    return Page(items=items, total=total, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: UUID,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductRead:
    try:
        return _build_service(db).get(product_id)
    except ProductNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    _current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ProductRead:
    service = _build_service(db)
    try:
        return service.create(**data.model_dump(exclude_none=True))
    except DuplicateProductName:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un producto registrado con ese nombre",
        )
    except ProviderNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proveedor no encontrado")


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: UUID,
    data: ProductUpdate,
    _current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ProductRead:
    service = _build_service(db)
    try:
        return service.update(product_id, **data.model_dump(exclude_unset=True))
    except ProductNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    except DuplicateProductName:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un producto registrado con ese nombre",
        )
    except ProviderNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proveedor no encontrado")


@router.delete("/{product_id}", response_model=ProductRead)
def delete_product(
    product_id: UUID,
    _current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ProductRead:
    service = _build_service(db)
    try:
        return service.deactivate(product_id)
    except ProductNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")