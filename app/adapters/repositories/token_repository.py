from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.revoked_token import RevokedToken
from app.domain.ports.token_repository import TokenRevocationRepository
from app.infrastructure.models.revoked_token import RevokedTokenModel


class SQLAlchemyTokenRevocationRepository(TokenRevocationRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_domain(model: RevokedTokenModel) -> RevokedToken:
        return RevokedToken(
            jti=model.jti,
            user_id=model.user_id,
            expires_at=model.expires_at,
            revoked_at=model.revoked_at,
        )

    def add(self, jti: str, user_id: UUID | None, expires_at: datetime) -> RevokedToken:
        existing = self.db.query(RevokedTokenModel).filter(RevokedTokenModel.jti == jti).first()
        if existing is not None:
            return self._to_domain(existing)
        model = RevokedTokenModel(jti=jti, user_id=user_id, expires_at=expires_at)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def exists(self, jti: str) -> bool:
        return (
            self.db.query(RevokedTokenModel).filter(RevokedTokenModel.jti == jti).first()
            is not None
        )

    def purge_expired(self) -> None:
        now = datetime.now(timezone.utc)
        self.db.query(RevokedTokenModel).filter(RevokedTokenModel.expires_at < now).delete()
        self.db.commit()