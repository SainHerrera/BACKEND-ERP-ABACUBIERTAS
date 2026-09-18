from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.adapters.deps import require_roles
from app.adapters.schemas import (
    ReportInventoryProduct,
    ReportInventoryValuation,
    ReportKpis,
    ReportProviderDeliveryItem,
    ReportProviderExpenseItem,
    ReportSalesBySellerItem,
    ReportSalesMonthlyItem,
)
from app.application.services.report_service import ReportService
from app.domain.entities.user import User
from app.infrastructure.db import get_db

router = APIRouter(prefix="/reports", tags=["reports"])

REPORT_ROLES = ("admin", "gerencia")
# El reporte por proveedor vive en el menú de Compras (ProviderReportPage).
PROVIDER_REPORT_ROLES = ("admin", "gerencia", "compras")


def _build_service(db: Session) -> ReportService:
    return ReportService(db)


@router.get("/kpis", response_model=ReportKpis)
def get_report_kpis(
    _current_user: User = Depends(require_roles(*REPORT_ROLES)),
    db: Session = Depends(get_db),
) -> ReportKpis:
    return ReportKpis(**ReportService(db).kpis())


@router.get("/sales-by-seller", response_model=list[ReportSalesBySellerItem])
def get_report_sales_by_seller(
    _current_user: User = Depends(require_roles(*REPORT_ROLES)),
    db: Session = Depends(get_db),
) -> list[ReportSalesBySellerItem]:
    return [
        ReportSalesBySellerItem(**x) for x in ReportService(db).sales_by_seller()
    ]


@router.get("/sales-monthly-trend", response_model=list[ReportSalesMonthlyItem])
def get_report_sales_monthly_trend(
    _current_user: User = Depends(require_roles(*REPORT_ROLES)),
    db: Session = Depends(get_db),
) -> list[ReportSalesMonthlyItem]:
    return [
        ReportSalesMonthlyItem(**x) for x in ReportService(db).sales_monthly_trend()
    ]


@router.get("/inventory-valuation", response_model=ReportInventoryValuation)
def get_report_inventory_valuation(
    _current_user: User = Depends(require_roles(*REPORT_ROLES)),
    db: Session = Depends(get_db),
) -> ReportInventoryValuation:
    data = ReportService(db).inventory_valuation()
    return ReportInventoryValuation(
        valorTotal=data["valorTotal"],
        porProducto=[ReportInventoryProduct(**x) for x in data["porProducto"]],
    )


@router.get("/provider-expense", response_model=list[ReportProviderExpenseItem])
def get_report_provider_expense(
    _current_user: User = Depends(require_roles(*PROVIDER_REPORT_ROLES)),
    db: Session = Depends(get_db),
) -> list[ReportProviderExpenseItem]:
    return [
        ReportProviderExpenseItem(**x) for x in ReportService(db).provider_expense()
    ]


@router.get("/provider-delivery", response_model=list[ReportProviderDeliveryItem])
def get_report_provider_delivery(
    _current_user: User = Depends(require_roles(*PROVIDER_REPORT_ROLES)),
    db: Session = Depends(get_db),
) -> list[ReportProviderDeliveryItem]:
    return [
        ReportProviderDeliveryItem(**x) for x in ReportService(db).provider_delivery()
    ]