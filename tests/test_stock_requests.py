from __future__ import annotations

import uuid


def _unique(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


def _create_provider(client, headers, tracker) -> str:
    resp = client.post(
        "/api/v1/providers",
        headers=headers,
        json={"nombre_empresa": _unique("TST Proveedor SOL"), "nit": _unique("NIT")},
    )
    assert resp.status_code == 201, resp.text
    pid = resp.json()["id_proveedor"]
    tracker.providers.append(pid)
    return pid


def _create_product(client, headers, tracker, *, provider_id: str) -> str:
    resp = client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "nombre": _unique("TST Producto SOL"),
            "unidad_medida": "unidad",
            "precio_unitario": 10.0,
            "stock_actual": 50,
            "stock_minimo": 20,
            "id_proveedor": provider_id or None,
        },
    )
    assert resp.status_code == 201, resp.text
    pid = resp.json()["id_producto"]
    tracker.products.append(pid)
    return pid


def _create_stock_request(client, headers, *, product_id: str) -> dict:
    resp = client.post(
        "/api/v1/stock-requests",
        headers=headers,
        json={"id_producto": product_id, "cantidad_sugerida": 10},
    )
    return resp


def test_bodega_puede_crear_solicitud_de_abastecimiento(client, auth, admin_token, tracker):
    admin_headers = _admin_headers(admin_token)
    provider_id = _create_provider(client, admin_headers, tracker)
    product_id = _create_product(client, admin_headers, tracker, provider_id=provider_id)

    bodega = auth("bodega")
    resp = _create_stock_request(client, bodega.headers, product_id=product_id)
    assert resp.status_code == 201, resp.text
    assert resp.json()["estado"] == "pendiente"
    assert resp.json()["numero_solicitud"].startswith("SOL-")
    tracker.stock_requests.append(resp.json()["id_solicitud"])


def test_ventas_no_puede_crear_solicitud_de_abastecimiento(client, auth, admin_token, tracker):
    admin_headers = _admin_headers(admin_token)
    provider_id = _create_provider(client, admin_headers, tracker)
    product_id = _create_product(client, admin_headers, tracker, provider_id=provider_id)

    vendedor = auth("ventas")
    resp = _create_stock_request(client, vendedor.headers, product_id=product_id)
    assert resp.status_code == 403, resp.text


def test_bodega_no_puede_cambiar_estado_de_solicitud(client, auth, admin_token, tracker):
    admin_headers = _admin_headers(admin_token)
    provider_id = _create_provider(client, admin_headers, tracker)
    product_id = _create_product(client, admin_headers, tracker, provider_id=provider_id)

    resp = _create_stock_request(client, admin_headers, product_id=product_id)
    assert resp.status_code == 201, resp.text
    sol_id = resp.json()["id_solicitud"]
    tracker.stock_requests.append(sol_id)

    bodega = auth("bodega")
    patch = client.patch(
        f"/api/v1/stock-requests/{sol_id}/status",
        headers=bodega.headers,
        json={"estado": "aprobada"},
    )
    assert patch.status_code == 403, patch.text