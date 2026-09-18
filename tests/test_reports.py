from __future__ import annotations

import uuid

import pytest

REPORT_PATHS = [
    "/api/v1/reports/kpis",
    "/api/v1/reports/sales-by-seller",
    "/api/v1/reports/sales-monthly-trend",
    "/api/v1/reports/inventory-valuation",
    "/api/v1/reports/provider-expense",
    "/api/v1/reports/provider-delivery",
]


@pytest.mark.parametrize("path", REPORT_PATHS)
def test_reports_rbac_gerencia_ok_ventas_403(client, auth, path):
    gerente = auth("gerencia")
    vendedor = auth("ventas")

    resp = client.get(path, headers=gerente.headers)
    assert resp.status_code == 200, resp.text

    resp = client.get(path, headers=vendedor.headers)
    assert resp.status_code == 403, resp.text


PROVIDER_REPORT_PATHS = [
    "/api/v1/reports/provider-expense",
    "/api/v1/reports/provider-delivery",
]


@pytest.mark.parametrize("path", PROVIDER_REPORT_PATHS)
def test_provider_reports_ok_para_compras(client, auth, path):
    # El reporte por proveedor vive en el menú de Compras (ProviderReportPage).
    compras = auth("compras")
    resp = client.get(path, headers=compras.headers)
    assert resp.status_code == 200, resp.text


def test_kpis_shape(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.get("/api/v1/reports/kpis", headers=headers)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert set(data) == {
        "ventasDelMes",
        "totalVentas",
        "cotizacionesPendientes",
        "stockCritico",
        "comprasPendientes",
        "aprobacionesPendientes",
    }
    assert isinstance(data["ventasDelMes"], float)
    assert isinstance(data["totalVentas"], float)
    assert isinstance(data["cotizacionesPendientes"], int)
    assert isinstance(data["stockCritico"], int)
    assert isinstance(data["comprasPendientes"], int)
    assert isinstance(data["aprobacionesPendientes"], int)


def _unique(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _create_provider(client, headers, tracker) -> str:
    resp = client.post(
        "/api/v1/providers",
        headers=headers,
        json={"nombre_empresa": _unique("TST Proveedor"), "nit": _unique("NIT")},
    )
    assert resp.status_code == 201, resp.text
    pid = resp.json()["id_proveedor"]
    tracker.providers.append(pid)
    return pid


def _create_product(client, headers, tracker, *, provider_id: str, precio=100, stock=7, stock_min=3) -> str:
    resp = client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "nombre": _unique("TST Lona"),
            "unidad_medida": "unidad",
            "precio_unitario": precio,
            "stock_inicial": stock,
            "stock_minimo": stock_min,
            "id_proveedor": provider_id or None,
        },
    )
    assert resp.status_code == 201, resp.text
    pid = resp.json()["id_producto"]
    tracker.products.append(pid)
    return pid


def _create_client(client, headers, tracker) -> str:
    resp = client.post(
        "/api/v1/clients",
        headers=headers,
        json={"tipo_cliente": "empresa", "nombre_razon_social": _unique("TST Cliente"), "nit_cc": _unique("CC")},
    )
    assert resp.status_code == 201, resp.text
    cid = resp.json()["id_cliente"]
    tracker.clients.append(cid)
    return cid


def test_inventory_valuation_includes_created_product(client, admin_token, tracker):
    headers = {"Authorization": f"Bearer {admin_token}"}
    provider_id = _create_provider(client, headers, tracker)
    product_id = _create_product(
        client, headers, tracker, provider_id=provider_id, precio=120.5, stock=4, stock_min=2
    )

    resp = client.get("/api/v1/reports/inventory-valuation", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    por_producto = data["porProducto"]

    item = next((p for p in por_producto if p["id_producto"] == product_id), None)
    assert item is not None, "El producto creado debe aparecer en la valoración"
    assert item["precio_unitario"] == pytest.approx(120.5)
    assert item["stock_actual"] == 4
    assert item["valor"] == pytest.approx(482.0)

    total = sum(p["valor"] for p in por_producto)
    assert data["valorTotal"] == pytest.approx(total)
    assert all(
        por_producto[i]["valor"] >= por_producto[i + 1]["valor"]
        for i in range(len(por_producto) - 1)
    )


def test_kpis_reaccionan_a_nuevos_datos(client, admin_token, tracker):
    headers = {"Authorization": f"Bearer {admin_token}"}
    before = client.get("/api/v1/reports/kpis", headers=headers).json()

    provider_id = _create_provider(client, headers, tracker)
    product_critico = _create_product(
        client, headers, tracker, provider_id=provider_id, precio=10, stock=1, stock_min=5
    )
    client_id = _create_client(client, headers, tracker)

    # Cotización enviada
    resp = client.post(
        "/api/v1/quotations",
        headers=headers,
        json={
            "id_cliente": client_id,
            "detalles": [
                {"id_producto": product_critico, "cantidad": 1, "precio_unitario": 10.0}
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    cot_id = resp.json()["id_cotizacion"]
    tracker.quotations.append(cot_id)
    resp = client.patch(f"/api/v1/quotations/{cot_id}/estado", headers=headers, json={"estado": "enviada"})
    assert resp.status_code == 200, resp.text

    # Orden de compra: aprobación deshabilitada -> estado 'enviada'
    resp = client.post(
        "/api/v1/purchase-orders",
        headers=headers,
        json={
            "id_proveedor": provider_id,
            "detalles": [
                {"id_producto": product_critico, "cantidad_ordenada": 2, "precio_unitario": 10.0}
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    po_id = resp.json()["id_orden_compra"]
    tracker.orders.append(po_id)

    after = client.get("/api/v1/reports/kpis", headers=headers).json()
    assert after["cotizacionesPendientes"] == before["cotizacionesPendientes"] + 1
    assert after["comprasPendientes"] == before["comprasPendientes"] + 1
    assert after["stockCritico"] >= before["stockCritico"] + 1


def test_ventas_reflejan_en_dashboard_reports(client, admin_token, tracker):
    headers = {"Authorization": f"Bearer {admin_token}"}
    me = client.get("/api/v1/auth/me", headers=headers).json()
    admin_id = str(me["id"])

    before_kpis = client.get("/api/v1/reports/kpis", headers=headers).json()
    before_seller = {
        i["id_usuario"]: i["total"]
        for i in client.get("/api/v1/reports/sales-by-seller", headers=headers).json()
    }
    before_trend = client.get("/api/v1/reports/sales-monthly-trend", headers=headers).json()

    provider_id = _create_provider(client, headers, tracker)
    product_id = _create_product(
        client, headers, tracker, provider_id=provider_id, precio=50, stock=100, stock_min=3
    )
    client_id = _create_client(client, headers, tracker)

    resp = client.post(
        "/api/v1/sales",
        headers=headers,
        json={
            "id_cliente": client_id,
            "detalles": [
                {"id_producto": product_id, "cantidad": 2, "precio_unitario": 50.0}
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    sale = resp.json()
    tracker.sales.append(sale["id_orden_venta"])
    expected_total = float(sale["total"])

    after_kpis = client.get("/api/v1/reports/kpis", headers=headers).json()
    assert after_kpis["totalVentas"] == pytest.approx(
        before_kpis["totalVentas"] + expected_total
    )
    assert after_kpis["ventasDelMes"] >= before_kpis["ventasDelMes"]

    after_seller = {
        i["id_usuario"]: i["total"]
        for i in client.get("/api/v1/reports/sales-by-seller", headers=headers).json()
    }
    assert after_seller.get(admin_id) == pytest.approx(
        before_seller.get(admin_id, 0.0) + expected_total
    )

    after_trend = client.get("/api/v1/reports/sales-monthly-trend", headers=headers).json()
    before_sum = sum(i["total"] for i in before_trend)
    after_sum = sum(i["total"] for i in after_trend)
    assert after_sum == pytest.approx(before_sum + expected_total)