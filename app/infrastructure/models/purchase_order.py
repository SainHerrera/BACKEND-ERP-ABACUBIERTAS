import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base


class PurchaseOrderModel(Base):
    __tablename__ = "purchase_orders"

    id_orden_compra: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    numero_oc: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    id_proveedor: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("providers.id_proveedor", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nombre_proveedor: Mapped[str | None] = mapped_column(String(150), nullable=True)
    fecha_emision: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'pendiente_aprobacion'"), default="pendiente_aprobacion", index=True
    )
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Módulos stock-requests/provider-quotations existen desde FASE 3: con FK.
    id_solicitud: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("stock_requests.id_solicitud", ondelete="SET NULL"),
        nullable=True,
    )
    numero_solicitud: Mapped[str | None] = mapped_column(String(20), nullable=True)
    id_cotizacion: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("provider_quotations.id_cotizacion", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    detalles: Mapped[list["PurchaseOrderDetailModel"]] = relationship(
        "PurchaseOrderDetailModel",
        cascade="all, delete-orphan",
        back_populates="orden",
        order_by="PurchaseOrderDetailModel.id_detalle_oc",
    )


class PurchaseOrderDetailModel(Base):
    __tablename__ = "purchase_order_details"

    id_detalle_oc: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    id_orden_compra: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_orders.id_orden_compra", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_producto: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id_producto", ondelete="RESTRICT"),
        nullable=False,
    )
    descripcion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cantidad_ordenada: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_recibida: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    precio_unitario: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0"), default=Decimal("0")
    )
    tiempo_entrega_dias: Mapped[int | None] = mapped_column(Integer, nullable=True)

    orden: Mapped[PurchaseOrderModel] = relationship(
        "PurchaseOrderModel", back_populates="detalles"
    )