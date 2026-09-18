import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base


class StockRequestModel(Base):
    __tablename__ = "stock_requests"

    id_solicitud: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    numero_solicitud: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    id_producto: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id_producto", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    descripcion: Mapped[str] = mapped_column(String(150), nullable=False)
    cantidad_sugerida: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_actual: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_minimo: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'pendiente'"), default="pendiente", index=True
    )
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    id_usuario: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    nombre_usuario: Mapped[str | None] = mapped_column(String(26), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )