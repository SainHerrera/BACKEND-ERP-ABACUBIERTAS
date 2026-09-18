from __future__ import annotations

import uuid

import pytest


def _unique(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


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


def _create_product(client, headers, tracker, *, provider_id: str, precio=10.0) -> str:
    resp = client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "nombre": _unique("TST Producto Audit"),
            "unidad_medida": "unidad",
            "precio_unitario": precio,
            "stock_actual": 20,
            "stock_minimo": 5,
            "id_proveedor": provider_id or None,
        },
    )
    assert resp.status_code == 201, resp.text
    pid = resp.json()["id_producto"]
    tracker.products.append(pid)
    return pid


def _create_stock_request(client, headers, tracker, *, product_id: str) -> str:
    resp = client.post(
        "/api/v1/stock-requests",
        headers=headers,
        json={"id_producto": product_id, "cantidad_sugerida": 10},
    )
    assert resp.status_code == 201, resp.text
    rid = resp.json()["id_solicitud"]
    tracker.stock_requests.append(rid)
    return rid


def _audit_items(client, headers, **params) -> dict:
    resp = client.get("/api/v1/audit-log", headers=headers, params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_audit_log_login_y_user_created(client, auth, admin_token):
    # auth registra (actor admin -> user_created) y luego inicia sesión (actor user -> login)
    user = auth("compras")
    tracker_emails = [user.email]
    admin_email = None
    me = client.get("/api/v1/auth/me", headers=_admin_headers(admin_token)).json()
    admin_email = me["email"]
    headers = _admin_headers(admin_token)

    logins = _audit_items(client, headers, accion="login", limit=50)
    assert any(
        e["email_usuario"] == user.email and e["rol_usuario"] == "compras"
        for e in logins["items"]
    ), "El login del usuario debe quedar registrado con actor correcto"

    created = _audit_items(client, headers, accion="user_created", limit=50)
    assert any(
        e["email_usuario"] == admin_email
        and user.email in (e["detalle"] or "")
        for e in created["items"]
    ), "La creación del usuario debe quedar registrada con el admin como actor"

    # Filtro por usuario (nombre/email) + paginación
    filtered = _audit_items(client, headers, usuario=user.email.split("@")[0], limit=10)
    assert all(user.email in (e["email_usuario"] or "") for e in filtered["items"])
    assert isinstance(filtered["total"], int)
    assert len(filtered["items"]) <= 10
    _ = tracker_emails


def test_audit_log_stock_request_wiring(client, admin_token, tracker):
    headers = _admin_headers(admin_token)
    provider_id = _create_provider(client, headers, tracker)
    product_id = _create_product(client, headers, tracker, provider_id=provider_id)
    _create_stock_request(client, headers, tracker, product_id=product_id)

    items = _audit_items(client, headers, accion="stock_request_created", limit=50)
    assert any(
        e["email_usuario"] == client.get("/api/v1/auth/me", headers=headers).json()["email"]
        and "SOL-" in (e["detalle"] or "")
        for e in items["items"]
    ), "Debe registrarse la creación de la solicitud de stock"


def test_audit_log_compras_wiring(client, admin_token, tracker):
    headers = _admin_headers(admin_token)
    admin_email = client.get("/api/v1/auth/me", headers=headers).json()["email"]

    provider_id = _create_provider(client, headers, tracker)
    product_id = _create_product(client, headers, tracker, provider_id=provider_id)
    solicitud_id = _create_stock_request(client, headers, tracker, product_id=product_id)

    # Dos cotizaciones de proveedor y selección de la primera
    cot_ids = []
    for _ in range(2):
        resp = client.post(
            "/api/v1/provider-quotations",
            headers=headers,
            json={
                "id_solicitud": solicitud_id,
                "id_producto": product_id,
                "id_proveedor": provider_id,
                "precio_unitario": 12.0,
                "tiempo_entrega_dias": 3,
                "condiciones": "TST pago",
            },
        )
        assert resp.status_code == 201, resp.text
        cot_ids.append(resp.json()["id_cotizacion"])
        tracker.provider_quotations.append(cot_ids[-1])

    resp = client.patch(
        f"/api/v1/provider-quotations/{cot_ids[0]}/seleccionar",
        headers=headers,
        json={"seleccionada": True},
    )
    assert resp.status_code == 200, resp.text

    quot_created = _audit_items(client, headers, accion="provider_quotation_created", limit=50)
    assert sum(1 for e in quot_created["items"] if e["email_usuario"] == admin_email) >= 2

    quot_selected = _audit_items(
        client, headers, accion="provider_quotation_selected", limit=50
    )
    assert any(
        e["email_usuario"] == admin_email and "seleccionada" in (e["detalle"] or "")
        for e in quot_selected["items"]
    )

    # Orden de compra -> purchase_order_created
    resp = client.post(
        "/api/v1/purchase-orders",
        headers=headers,
        json={
            "id_proveedor": provider_id,
            "detalles": [
                {
                    "id_producto": product_id,
                    "cantidad_ordenada": 5,
                    "precio_unitario": 12.0,
                }
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    tracker.orders.append(resp.json()["id_orden_compra"])

    pos = _audit_items(client, headers, accion="purchase_order_created", limit=50)
    assert any(
        e["email_usuario"] == admin_email and "OC-" in (e["detalle"] or "")
        for e in pos["items"]
    ), "Debe registrarse la creación de la orden de compra"


def test_audit_log_settings_y_rbac(client, admin_token, auth):
    admin_headers = _admin_headers(admin_token)
    admin_email = client.get("/api/v1/auth/me", headers=admin_headers).json()["email"]

    current = client.get("/api/v1/settings", headers=admin_headers).json()
    previous_minimo = current["stock_minimo_default"]
    nuevo_minimo = previous_minimo + 1 if previous_minimo != 99 else 98

    resp = client.patch(
        "/api/v1/settings",
        headers=admin_headers,
        json={"stock_minimo_default": nuevo_minimo},
    )
    assert resp.status_code == 200, resp.text
    try:
        updated = _audit_items(client, admin_headers, accion="settings_updated", limit=50)
        assert any(e["email_usuario"] == admin_email for e in updated["items"])
    finally:
        client.patch(
            "/api/v1/settings",
            headers=admin_headers,
            json={"stock_minimo_default": previous_minimo},
        )

    # Lectura: gerencia OK, ventas 403
    gerente = auth("gerencia")
    vendedor = auth("ventas")
    resp = client.get("/api/v1/audit-log", headers=gerente.headers)
    assert resp.status_code == 200, resp.text
    resp = client.get("/api/v1/audit-log", headers=vendedor.headers)
    assert resp.status_code == 403, resp.text

    # Borrado: solo admin; gerencia recibe 403 sin destruir datos
    resp = client.delete("/api/v1/audit-log", headers=gerente.headers)
    assert resp.status_code == 403, resp.text


def test_audit_log_clear_solo_admin(client, admin_token):
    headers = _admin_headers(admin_token)
    resp = client.delete("/api/v1/audit-log", headers=headers)
    assert resp.status_code == 204, resp.text
    data = _audit_items(client, headers)
    assert data["total"] == 0


def test_login_fallido_no_registra(client, admin_token):
    # Email del admin pero password incorrecto
    me = client.get("/api/v1/auth/me", headers=_admin_headers(admin_token)).json()
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": me["email"], "password": "contraseña_incorrecta_xxx"},
    )
    assert resp.status_code == 401, resp.text
    items = _audit_items(client, _admin_headers(admin_token), accion="login", limit=50)
    recent = [e for e in items["items"] if e["detalle"] and "Inicio de sesión" in e["detalle"]]
    assert not any(e["detalle"].startswith(f"Inicio de sesión de {me['name']}") for e in recent), (
        "Un login fallido no debe registrar entrada"
    )