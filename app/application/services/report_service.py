from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.infrastructure.models.provider_quotation import ProviderQuotationModel
from app.infrastructure.models.product import ProductModel
from app.infrastructure.models.purchase_order import PurchaseOrderModel
from app.infrastructure.models.quotation import QuotationModel
from app.infrastructure.models.sale import SaleModel
from app.infrastructure.models.user import UserModel


class ReportService:
    """Agregaciones de read-model que replican el StorageEngine del frontend."""

    def __init__(self, db: Session):
        self.db = db

    def kpis(self) -> dict:
        now = datetime.now()
        base_sales = self.db.query(
            func.coalesce(func.sum(SaleModel.total), 0)
        ).filter(SaleModel.estado != "cancelada")
        ventas_del_mes = (
            base_sales.filter(func.extract("year", SaleModel.fecha_venta) == now.year)
            .filter(func.extract("month", SaleModel.fecha_venta) == now.month)
            .scalar()
        )
        total_ventas = base_sales.scalar()

        cotizaciones_pendientes = (
            self.db.query(func.count(QuotationModel.id_cotizacion))
            .filter(QuotationModel.estado == "enviada")
            .scalar()
            or 0
        )
        stock_critico = (
            self.db.query(func.count(ProductModel.id_producto))
            .filter(ProductModel.stock_actual <= ProductModel.stock_minimo)
            .scalar()
            or 0
        )
        compras_pendientes = (
            self.db.query(func.count(PurchaseOrderModel.id_orden_compra))
            .filter(
                PurchaseOrderModel.estado.in_(
                    ("enviada", "en_transito", "pendiente_aprobacion")
                )
            )
            .scalar()
            or 0
        )
        aprobaciones_pendientes = (
            self.db.query(func.count(PurchaseOrderModel.id_orden_compra))
            .filter(PurchaseOrderModel.estado == "pendiente_aprobacion")
            .scalar()
            or 0
        )

        return {
            "ventasDelMes": float(ventas_del_mes or 0),
            "totalVentas": float(total_ventas or 0),
            "cotizacionesPendientes": cotizaciones_pendientes,
            "stockCritico": stock_critico,
            "comprasPendientes": compras_pendientes,
            "aprobacionesPendientes": aprobaciones_pendientes,
        }

    def sales_by_seller(self) -> list[dict]:
        rows = (
            self.db.query(SaleModel.id_usuario, SaleModel.total)
            .filter(SaleModel.estado != "cancelada")
            .all()
        )
        user_names = {u_id: name for u_id, name in self.db.query(UserModel.id, UserModel.name).all()}

        totals: dict[str, Decimal] = {}
        counts: dict[str, int] = {}
        for id_usuario, total in rows:
            key = str(id_usuario) if id_usuario is not None else "sin_usuario"
            totals[key] = totals.get(key, Decimal("0")) + Decimal(total)
            counts[key] = counts.get(key, 0) + 1

        items = [
            {
                "id_usuario": key,
                "vendedor": user_names.get(UUID(key), f"Usuario {key}"),
                "total": float(totals[key]),
                "ventas": counts[key],
            }
            for key in totals
        ]
        return sorted(items, key=lambda x: x["total"], reverse=True)

    def sales_monthly_trend(self) -> list[dict]:
        rows = (
            self.db.query(SaleModel.fecha_venta, SaleModel.total)
            .filter(SaleModel.estado != "cancelada")
            .all()
        )
        by_month: dict[str, Decimal] = {}
        for fecha, total in rows:
            key = fecha.strftime("%Y-%m")
            by_month[key] = by_month.get(key, Decimal("0")) + Decimal(total)
        return [
            {"mes": mes, "total": float(by_month[mes])} for mes in sorted(by_month)
        ]

    def inventory_valuation(self) -> dict:
        products = self.db.query(ProductModel).all()
        por_producto = [
            {
                "id_producto": p.id_producto,
                "nombre": p.nombre,
                "stock_actual": p.stock_actual,
                "precio_unitario": float(p.precio_unitario),
                "valor": float(p.stock_actual * Decimal(p.precio_unitario)),
            }
            for p in products
        ]
        por_producto.sort(key=lambda x: x["valor"], reverse=True)
        return {
            "valorTotal": float(sum(Decimal(str(x["valor"])) for x in por_producto)),
            "porProducto": por_producto,
        }

    def provider_expense(self) -> list[dict]:
        orders = self.db.query(PurchaseOrderModel).options(
            selectinload(PurchaseOrderModel.detalles)
        ).all()
        by_provider: dict[str, dict] = {}  # key -> {nombre, gasto_total, numero_oc}
        for order in orders:
            gasto = Decimal("0")
            for d in order.detalles:
                gasto += Decimal(d.cantidad_recibida) * Decimal(d.precio_unitario)
            key = str(order.id_proveedor)
            if key in by_provider:
                by_provider[key]["gasto_total"] += gasto
                by_provider[key]["numero_oc"] += 1
            else:
                by_provider[key] = {
                    "nombre_proveedor": order.nombre_proveedor
                    or f"Proveedor {order.id_proveedor}",
                    "gasto_total": gasto,
                    "numero_oc": 1 if gasto > 0 else 0,
                }
        items = [
            {
                "id_proveedor": key,
                "nombre_proveedor": value["nombre_proveedor"],
                "gasto_total": float(value["gasto_total"]),
                "numero_oc": value["numero_oc"],
            }
            for key, value in by_provider.items()
        ]
        return sorted(items, key=lambda x: x["gasto_total"], reverse=True)

    def provider_delivery(self) -> list[dict]:
        quotations = self.db.query(ProviderQuotationModel).all()
        orders = self.db.query(PurchaseOrderModel).options(
            selectinload(PurchaseOrderModel.detalles)
        ).all()
        by_provider: dict[str, dict] = {}  # key -> {nombre, total_dias, count}
        for q in quotations:
            key = str(q.id_proveedor)
            if key in by_provider:
                by_provider[key]["total_dias"] += Decimal(q.tiempo_entrega_dias)
                by_provider[key]["count"] += 1
            else:
                by_provider[key] = {
                    "nombre_proveedor": q.nombre_proveedor
                    or f"Proveedor {q.id_proveedor}",
                    "total_dias": Decimal(q.tiempo_entrega_dias),
                    "count": 1,
                }
        for order in orders:
            dias = sum((d.tiempo_entrega_dias or 0) for d in order.detalles)
            num_detalles = len(order.detalles) or 1
            if dias <= 0:
                continue
            promedio = Decimal(dias) / Decimal(num_detalles)
            key = str(order.id_proveedor)
            if key in by_provider:
                by_provider[key]["total_dias"] += promedio
                by_provider[key]["count"] += 1
            else:
                by_provider[key] = {
                    "nombre_proveedor": order.nombre_proveedor
                    or f"Proveedor {order.id_proveedor}",
                    "total_dias": promedio,
                    "count": 1,
                }
        items = [
            {
                "id_proveedor": key,
                "nombre_proveedor": value["nombre_proveedor"],
                "tiempo_promedio_dias": float(
                    value["total_dias"] / value["count"]
                )
                if value["count"]
                else 0.0,
                "cotizaciones": value["count"],
            }
            for key, value in by_provider.items()
        ]
        return sorted(items, key=lambda x: x["tiempo_promedio_dias"])