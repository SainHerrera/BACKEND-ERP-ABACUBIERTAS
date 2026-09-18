from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base


class SystemSettingsModel(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    stock_minimo_default: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("15"), default=15
    )
    margen_utilidad_default: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("30"), default=30
    )
    catalogo_inicial_cargado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"), default=True
    )
    aprobacion_oc_habilitada: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"), default=False
    )
    aprobacion_oc_monto_minimo: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        server_default=text("5000000"),
        default=Decimal("5000000"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )