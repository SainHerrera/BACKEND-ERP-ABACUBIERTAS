from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.user import User
from app.domain.ports.user_repository import UserRepository
from app.infrastructure.models.user import UserModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            name=model.name,
            email=model.email,
            password=model.password,
            rol=model.rol,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_by_email(self, email: str) -> User | None:
        model = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_domain(model) if model else None

    def get_by_id(self, user_id: UUID) -> User | None:
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_domain(model) if model else None

    def list_users(self, rol: str | None = None, status: bool | None = None) -> list[User]:
        query = self.db.query(UserModel)
        if rol is not None:
            query = query.filter(UserModel.rol == rol)
        if status is not None:
            query = query.filter(UserModel.status == status)
        models = query.order_by(UserModel.created_at).all()
        return [self._to_domain(model) for model in models]

    def create(self, name: str, email: str, password: str, rol: str) -> User:
        model = UserModel(name=name, email=email, password=password, rol=rol)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def update(
        self,
        user_id: UUID,
        *,
        name: str | None = None,
        email: str | None = None,
        password: str | None = None,
        rol: str | None = None,
        status: bool | None = None,
    ) -> User | None:
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if model is None:
            return None
        if name is not None:
            model.name = name
        if email is not None:
            model.email = email
        if password is not None:
            model.password = password
        if rol is not None:
            model.rol = rol
        if status is not None:
            model.status = status
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)