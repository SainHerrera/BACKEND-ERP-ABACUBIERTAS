from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class RevokedToken:
    jti: str
    user_id: UUID | None
    expires_at: datetime
    revoked_at: datetime