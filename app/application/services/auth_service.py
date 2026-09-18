from datetime import datetime, timezone
from uuid import UUID

from app.core.config import settings
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain.entities.user import User
from app.domain.exceptions import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidToken,
    RegistrationDisabled,
    UserInactive,
)
from app.domain.ports.token_repository import TokenRevocationRepository
from app.domain.ports.user_repository import UserRepository


class AuthService:
    def __init__(self, users: UserRepository, tokens: TokenRevocationRepository):
        self.users = users
        self.tokens = tokens

    def register(self, name: str, email: str, password: str, rol: str) -> User:
        if not settings.allow_registration:
            raise RegistrationDisabled("El registro está deshabilitado")
        if self.users.get_by_email(email) is not None:
            raise EmailAlreadyRegistered("El email ya está registrado")
        return self.users.create(
            name=name,
            email=email,
            password=hash_password(password),
            rol=rol,
        )

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.password):
            raise InvalidCredentials("Credenciales incorrectas")
        if not user.status:
            raise UserInactive("Usuario desactivado")
        return user

    def issue_tokens(self, user_id: UUID) -> dict:
        return {
            "access_token": create_access_token(user_id),
            "refresh_token": create_refresh_token(user_id),
        }

    def refresh(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except TokenError as exc:
            raise InvalidToken("Token inválido o expirado") from exc

        self.tokens.purge_expired()

        if self.tokens.exists(payload["jti"]):
            raise InvalidToken("Token revocado")

        user = self.users.get_by_id(UUID(payload["sub"]))
        if user is None or not user.status:
            raise InvalidToken("Sesión inválida")
        return self.issue_tokens(user.id)

    def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except TokenError:
            return
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        user_id = UUID(payload["sub"]) if payload.get("sub") else None
        self.tokens.purge_expired()
        self.tokens.add(
            jti=payload["jti"],
            user_id=user_id,
            expires_at=expires_at,
        )

    def get_user(self, user_id: UUID) -> User | None:
        return self.users.get_by_id(user_id)