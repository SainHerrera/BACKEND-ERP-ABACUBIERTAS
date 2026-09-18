from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.adapters.deps import get_current_user, require_roles
from app.adapters.repositories.client_repository import SQLAlchemyClientRepository
from app.adapters.schemas import ClientCreate, ClientRead, ClientUpdate, Page
from app.application.services.client_service import ClientService
from app.domain.entities.user import User
from app.domain.exceptions import ClientNotFound, DuplicateClientNitCc
from app.infrastructure.db import get_db

router = APIRouter(prefix="/clients", tags=["clients"])

WRITE_ROLES = ("admin", "ventas")

CLIENT_ESTADOS = {"activo", "inactivo", "prospecto", "frecuente", "corporativo"}
TIPO_CLIENTES = {"empresa", "persona_natural"}


def _build_service(db: Session) -> ClientService:
    return ClientService(SQLAlchemyClientRepository(db))


@router.get("", response_model=Page[ClientRead])
def list_clients(
    search: str | None = Query(default=None, max_length=150),
    estado: str | None = Query(default=None),
    tipo: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[ClientRead]:
    if estado is not None and estado not in CLIENT_ESTADOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Estado inválido. Permitidos: {', '.join(sorted(CLIENT_ESTADOS))}",
        )
    if tipo is not None and tipo not in TIPO_CLIENTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tipo inválido. Permitidos: {', '.join(sorted(TIPO_CLIENTES))}",
        )
    items, total = _build_service(db).list(search=search, estado=estado, tipo=tipo, skip=skip, limit=limit)
    return Page(items=items, total=total, skip=skip, limit=limit)


@router.get("/{client_id}", response_model=ClientRead)
def get_client(
    client_id: UUID,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClientRead:
    try:
        return _build_service(db).get(client_id)
    except ClientNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(
    data: ClientCreate,
    _current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ClientRead:
    try:
        return _build_service(db).create(**data.model_dump(exclude_none=True))
    except DuplicateClientNitCc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un cliente registrado con el NIT/CC",
        )


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(
    client_id: UUID,
    data: ClientUpdate,
    _current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ClientRead:
    service = _build_service(db)
    try:
        return service.update(client_id, **data.model_dump(exclude_unset=True))
    except ClientNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    except DuplicateClientNitCc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un cliente registrado con el NIT/CC",
        )


@router.delete("/{client_id}", response_model=ClientRead)
def delete_client(
    client_id: UUID,
    _current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ClientRead:
    service = _build_service(db)
    try:
        return service.deactivate(client_id)
    except ClientNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")