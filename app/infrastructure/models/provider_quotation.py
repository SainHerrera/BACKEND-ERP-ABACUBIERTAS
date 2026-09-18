import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base


class ProviderQuotationModel(Base):
    __tablename__ = "provider_quotations"

    id_cotizacion: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    numero_cotizacion: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    id_solicitud: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("stock_requests.id_solicitud", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    id_producto: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id_producto", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    id_proveedor: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("providers.id_proveedor", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nombre_proveedor: Mapped[str | None] = mapped_column(String(150), nullable=True)
    precio_unitario: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0"), default=Decimal("0")
    )
    tiempo_entrega_dias: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    condiciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    seleccionada: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"), default=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )