from fastapi import APIRouter

from app.adapters.api.audit_log import router as audit_log_router
from app.adapters.api.auth import router as auth_router
from app.adapters.api.clients import router as clients_router
from app.adapters.api.movements import router as movements_router
from app.adapters.api.products import router as products_router
from app.adapters.api.provider_quotations import router as provider_quotations_router
from app.adapters.api.providers import router as providers_router
from app.adapters.api.purchase_orders import router as purchase_orders_router
from app.adapters.api.quotations import client_quotations_router, router as quotations_router
from app.adapters.api.reports import router as reports_router
from app.adapters.api.sales import quotation_conversion_router, router as sales_router
from app.adapters.api.settings import router as settings_router
from app.adapters.api.stock_requests import router as stock_requests_router
from app.adapters.api.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(audit_log_router)
api_router.include_router(users_router)
api_router.include_router(providers_router)
api_router.include_router(provider_quotations_router)
api_router.include_router(products_router)
api_router.include_router(clients_router)
api_router.include_router(movements_router)
api_router.include_router(quotations_router)
api_router.include_router(client_quotations_router)
api_router.include_router(sales_router)
api_router.include_router(quotation_conversion_router)
api_router.include_router(purchase_orders_router)
api_router.include_router(stock_requests_router)
api_router.include_router(reports_router)
api_router.include_router(settings_router)