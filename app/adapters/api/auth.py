from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.api.audit import auditar
from app.adapters.deps import get_current_user, require_admin
from app.adapters.repositories.token_repository import SQLAlchemyTokenRevocationRepository
from app.adapters.repositories.user_repository import SQLAlchemyUserRepository
from app.adapters.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.application.services.auth_service import AuthService
from app.core.security import decode_token
from app.domain.entities.user import User
from app.domain.exceptions import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidToken,
    RegistrationDisabled,
    UserInactive,
)
from app.infrastructure.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_service(db: Session) -> AuthService:
    return AuthService(
        SQLAlchemyUserRepository(db),
        SQLAlchemyTokenRevocationRepository(db),
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    service = _build_service(db)
    try:
        user = service.register(name=data.name, email=data.email, password=data.password, rol=data.rol)
        auditar(
            db,
            current_user,
            "user_created",
            f"Usuario {user.name} ({user.email}) creado con rol {user.rol}",
        )
        return user
    except RegistrationDisabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El registro está deshabilitado",
        )
    except EmailAlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    service = _build_service(db)
    try:
        user = service.authenticate(email=data.email, password=data.password)
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    except UserInactive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )
    auditar(db, user, "login", f"Inicio de sesión de {user.name}")
    return TokenResponse(**service.issue_tokens(user.id))


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    service = _build_service(db)
    try:
        tokens = service.refresh(data.refresh_token)
    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )
    return TokenResponse(**tokens)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshRequest, db: Session = Depends(get_db)) -> None:
    service = _build_service(db)
    service.logout(data.refresh_token)
    try:
        payload = decode_token(data.refresh_token, expected_type="refresh")
        user = SQLAlchemyUserRepository(db).get_by_id(UUID(payload["sub"]))
        auditar(db, user, "logout", f"Cierre de sesión de {user.name if user else 'usuario'}")
    except Exception:
        db.rollback()


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user