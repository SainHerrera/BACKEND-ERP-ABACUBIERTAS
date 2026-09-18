import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base


class ProductModel(Base):
    __tablename__ = "products"

    id_producto: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    unidad_medida: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'unidad'"), default="unidad"
    )
    precio_unitario: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0"), default=Decimal("0")
    )
    stock_actual: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    stock_minimo: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("15"), default=15
    )
    id_proveedor: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("providers.id_proveedor", ondelete="SET NULL"),
        nullable=True,
    )
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"), default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )