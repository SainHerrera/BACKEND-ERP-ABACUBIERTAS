import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base


class SaleModel(Base):
    __tablename__ = "sales"

    id_orden_venta: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    numero_orden: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True
    )
    id_cliente: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("clients.id_cliente", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    id_cotizacion: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quotations.id_cotizacion", ondelete="SET NULL"),
        nullable=True,
    )
    id_usuario: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    fecha_venta: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    estado: Mapped[str] = mapped_column(
        String(12), nullable=False, server_default=text("'pendiente'"), default="pendiente", index=True
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0"), default=Decimal("0")
    )
    impuestos: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0"), default=Decimal("0")
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0"), default=Decimal("0")
    )
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    detalles: Mapped[list["SaleDetailModel"]] = relationship(
        "SaleDetailModel",
        cascade="all, delete-orphan",
        back_populates="venta",
        order_by="SaleDetailModel.id_detalle_venta",
    )


class SaleDetailModel(Base):
    __tablename__ = "sale_details"

    id_detalle_venta: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    id_orden_venta: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sales.id_orden_venta", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_producto: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id_producto", ondelete="RESTRICT"),
        nullable=False,
    )
    descripcion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0"), default=Decimal("0")
    )
    descuento: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0"), default=Decimal("0")
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0"), default=Decimal("0")
    )

    venta: Mapped[SaleModel] = relationship(
        "SaleModel", back_populates="detalles"
    )