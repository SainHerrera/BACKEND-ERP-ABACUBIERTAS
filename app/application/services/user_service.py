from uuid import UUID

from app.core.security import hash_password
from app.domain.entities.user import User
from app.domain.exceptions import EmailAlreadyRegistered, UserNotFound
from app.domain.ports.user_repository import UserRepository


class UserService:
    def __init__(self, users: UserRepository):
        self.users = users

    def list(self, rol: str | None = None, status: bool | None = None) -> list[User]:
        return self.users.list_users(rol=rol, status=status)

    def get(self, user_id: UUID) -> User:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise UserNotFound(f"Usuario con id {user_id} no encontrado")
        return user

    def update(
        self,
        user_id: UUID,
        *,
        name: str | None = None,
        email: str | None = None,
        password: str | None = None,
        rol: str | None = None,
        status: bool | None = None,
    ) -> User:
        if email is not None:
            existing = self.users.get_by_email(email)
            if existing is not None and existing.id != user_id:
                raise EmailAlreadyRegistered("El email ya está registrado")

        user = self.users.update(
            user_id,
            name=name,
            email=email,
            password=hash_password(password) if password is not None else None,
            rol=rol,
            status=status,
        )
        if user is None:
            raise UserNotFound(f"Usuario con id {user_id} no encontrado")
        return user

    def deactivate(self, user_id: UUID) -> User:
        user = self.users.update(user_id, status=False)
        if user is None:
            raise UserNotFound(f"Usuario con id {user_id} no encontrado")
        return user