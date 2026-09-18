from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.infrastructure.models.base import Base  # noqa: F401
from app.infrastructure.models.audit_log import AuditLogModel  # noqa: F401
from app.infrastructure.models.provider import ProviderModel  # noqa: F401
from app.infrastructure.models.product import ProductModel  # noqa: F401
from app.infrastructure.models.client import ClientModel  # noqa: F401
from app.infrastructure.models.movement import MovementModel  # noqa: F401
from app.infrastructure.models.purchase_order import (  # noqa: F401
    PurchaseOrderDetailModel,
    PurchaseOrderModel,
)
from app.infrastructure.models.provider_quotation import ProviderQuotationModel  # noqa: F401
from app.infrastructure.models.quotation import QuotationDetailModel, QuotationModel  # noqa: F401
from app.infrastructure.models.revoked_token import RevokedTokenModel  # noqa: F401
from app.infrastructure.models.sale import SaleDetailModel, SaleModel  # noqa: F401
from app.infrastructure.models.stock_request import StockRequestModel  # noqa: F401
from app.infrastructure.models.system_settings import SystemSettingsModel  # noqa: F401
from app.infrastructure.models.user import UserModel  # noqa: F401
from app.infrastructure.seed import seed_admin, seed_settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    seed_admin()
    seed_settings()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()