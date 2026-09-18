import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base


class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    id_usuario: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    nombre_usuario: Mapped[str | None] = mapped_column(String(26), nullable=True)
    email_usuario: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rol_usuario: Mapped[str | None] = mapped_column(String(20), nullable=True)
    accion: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)