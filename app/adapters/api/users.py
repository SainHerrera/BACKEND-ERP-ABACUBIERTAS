from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.adapters.api.audit import auditar
from app.adapters.deps import get_current_user, require_admin
from app.adapters.repositories.user_repository import SQLAlchemyUserRepository
from app.adapters.schemas import UserResponse, UserUpdateRequest
from app.application.services.user_service import UserService
from app.domain.entities.user import User
from app.domain.exceptions import EmailAlreadyRegistered, UserNotFound
from app.infrastructure.db import get_db

router = APIRouter(prefix="/users", tags=["users"])

VALID_ROLES_LIST = {"admin", "ventas", "compras", "bodega", "gerencia"}


def _build_service(db: Session) -> UserService:
    return UserService(SQLAlchemyUserRepository(db))


@router.get("", response_model=list[UserResponse])
def list_users(
    rol: str | None = Query(default=None, description="Filtrar por rol"),
    status_filter: str | None = Query(default=None, alias="status", description="activo / inactivo"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[User]:
    if rol is not None and rol not in VALID_ROLES_LIST:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Rol inválido. Permitidos: {', '.join(sorted(VALID_ROLES_LIST))}",
        )
    status_bool: bool | None = None
    if status_filter is not None:
        if status_filter == "activo":
            status_bool = True
        elif status_filter == "inactivo":
            status_bool = False
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El parámetro status debe ser 'activo' o 'inactivo'",
            )
    users = _build_service(db).list(rol=rol, status=status_bool)
    return users[skip : skip + limit]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    try:
        return _build_service(db).get(user_id)
    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    data: UserUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    service = _build_service(db)
    payload = data.model_dump(exclude_unset=True)
    try:
        user = service.update(
            user_id,
            name=data.name,
            email=data.email,
            password=data.password,
            rol=data.rol,
            status=data.status,
        )
        if "status" in payload:
            accion = "user_deactivated" if data.status is False else "user_activated"
            detalle = f"Usuario {user.name} {'desactivado' if data.status is False else 'activado'}"
        elif "rol" in payload:
            accion = "role_changed"
            detalle = f"Rol de {user.name} cambiado a {user.rol}"
        else:
            accion = "user_updated"
            detalle = f"Usuario {user.name} actualizado"
        auditar(db, admin, accion, detalle)
        return user
    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    except EmailAlreadyRegistered:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El email ya está registrado")


@router.delete("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivarte a ti mismo",
        )
    service = _build_service(db)
    try:
        user = service.deactivate(user_id)
        auditar(db, current_user, "user_deactivated", f"Usuario {user.name} desactivado")
        return user
    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")