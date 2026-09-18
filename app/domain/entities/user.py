from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class User:
    id: UUID
    name: str
    email: str
    password: str
    rol: str
    status: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None