from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.adapters.deps import get_current_user, require_roles
from app.adapters.repositories.provider_repository import SQLAlchemyProviderRepository
from app.adapters.schemas import Page, ProviderCreate, ProviderRead, ProviderUpdate
from app.application.services.provider_service import ProviderService
from app.domain.entities.user import User
from app.domain.exceptions import DuplicateProviderNit, ProviderNotFound
from app.infrastructure.db import get_db

router = APIRouter(prefix="/providers", tags=["providers"])

WRITE_ROLES = ("admin", "compras")


def _build_service(db: Session) -> ProviderService:
    return ProviderService(SQLAlchemyProviderRepository(db))


@router.get("", response_model=Page[ProviderRead])
def list_providers(
    search: str | None = Query(default=None, max_length=120),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[ProviderRead]:
    items, total = _build_service(db).list(search=search, skip=skip, limit=limit)
    return Page(items=items, total=total, skip=skip, limit=limit)


@router.get("/{provider_id}", response_model=ProviderRead)
def get_provider(
    provider_id: UUID,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProviderRead:
    try:
        return _build_service(db).get(provider_id)
    except ProviderNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proveedor no encontrado")


@router.post("", response_model=ProviderRead, status_code=status.HTTP_201_CREATED)
def create_provider(
    data: ProviderCreate,
    _current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ProviderRead:
    try:
        return _build_service(db).create(**data.model_dump(exclude_none=True))
    except DuplicateProviderNit:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un proveedor registrado con el NIT",
        )


@router.patch("/{provider_id}", response_model=ProviderRead)
def update_provider(
    provider_id: UUID,
    data: ProviderUpdate,
    _current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ProviderRead:
    service = _build_service(db)
    try:
        return service.update(provider_id, **data.model_dump(exclude_unset=True))
    except ProviderNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proveedor no encontrado")
    except DuplicateProviderNit:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un proveedor registrado con el NIT",
        )


@router.delete("/{provider_id}", response_model=ProviderRead)
def delete_provider(
    provider_id: UUID,
    _current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ProviderRead:
    service = _build_service(db)
    try:
        return service.deactivate(provider_id)
    except ProviderNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proveedor no encontrado")