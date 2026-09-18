from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.provider_quotation import ProviderQuotation
from app.domain.exceptions import (
    InsufficientProviderQuotations,
    InvalidQuantity,
    ProductDoesNotMatchRequest,
    ProductNotFound,
    ProviderNotFound,
    ProviderQuotationNotFound,
    StockRequestNotFound,
)
from app.domain.ports.product_repository import ProductRepository
from app.domain.ports.provider_quotation_repository import ProviderQuotationRepository
from app.domain.ports.provider_repository import ProviderRepository
from app.domain.ports.stock_request_repository import StockRequestRepository


class ProviderQuotationService:
    def __init__(
        self,
        quotations: ProviderQuotationRepository,
        requests: StockRequestRepository,
        products: ProductRepository,
        providers: ProviderRepository,
        db: Session,
    ):
        self.quotations = quotations
        self.requests = requests
        self.products = products
        self.providers = providers
        self.db = db

    def list(
        self,
        id_solicitud: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ProviderQuotation], int]:
        return self.quotations.list(
            id_solicitud=id_solicitud, skip=skip, limit=limit
        )

    def get(self, id_cotizacion: UUID) -> ProviderQuotation:
        quotation = self.quotations.get_by_id(id_cotizacion)
        if quotation is None:
            raise ProviderQuotationNotFound("Cotización de proveedor no encontrada")
        return quotation

    def create(
        self,
        *,
        id_solicitud: UUID,
        id_producto: UUID,
        id_proveedor: UUID,
        precio_unitario: Decimal,
        tiempo_entrega_dias: int,
        condiciones: str | None = None,
    ) -> ProviderQuotation:
        request = self.requests.get_by_id(id_solicitud)
        if request is None:
            raise StockRequestNotFound("Solicitud de stock no encontrada")

        product = self.products.get_by_id(id_producto)
        if product is None or not product.activo:
            raise ProductNotFound("Producto no encontrado")
        if product.id_producto != request.id_producto:
            raise ProductDoesNotMatchRequest(
                "El producto de la cotización no corresponde a la solicitud"
            )

        provider = self.providers.get_by_id(id_proveedor)
        if provider is None or not provider.activo:
            raise ProviderNotFound("Proveedor no encontrado")

        if not precio_unitario or precio_unitario <= 0:
            raise InvalidQuantity("El precio unitario debe ser mayor a 0")
        if not tiempo_entrega_dias or tiempo_entrega_dias <= 0:
            raise InvalidQuantity("El tiempo de entrega debe ser mayor a 0")

        numero = f"COT-{self.quotations.count() + 1:04d}"
        try:
            quotation = self.quotations.create(
                numero_cotizacion=numero,
                id_solicitud=id_solicitud,
                id_producto=request.id_producto,
                id_proveedor=id_proveedor,
                nombre_proveedor=provider.nombre_empresa,
                precio_unitario=Decimal(precio_unitario),
                tiempo_entrega_dias=tiempo_entrega_dias,
                condiciones=condiciones.strip() if condiciones and condiciones.strip() else None,
                fecha=datetime.now(),
                seleccionada=False,
            )
            self.db.commit()
            return quotation
        except Exception:
            self.db.rollback()
            raise

    def select(self, id_cotizacion: UUID, *, seleccionada: bool) -> ProviderQuotation:
        current = self.get(id_cotizacion)
        if current.seleccionada == seleccionada:
            return current
        if seleccionada and self.quotations.count_by_solicitud(current.id_solicitud) < 2:
            raise InsufficientProviderQuotations(
                "Se requieren al menos dos cotizaciones para elegir el mejor proveedor"
            )
        try:
            quotation = self.quotations.set_seleccionada(id_cotizacion, seleccionada)
            self.db.commit()
            return quotation
        except Exception:
            self.db.rollback()
            raise