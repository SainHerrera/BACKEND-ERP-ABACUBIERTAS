from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.db import SessionLocal
from app.main import app


def _admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def admin_token(client) -> str:
    from app.core.config import settings

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


class Tracker:
    """Registra filas creadas en tests para borrarlas en orden seguro de FKs."""

    def __init__(self) -> None:
        self.movements = []  # id_movimiento
        self.provider_quotations = []  # id_cotizacion (proveedor)
        self.stock_requests = []  # id_solicitud
        self.orders = []  # id_orden_compra
        self.quotations = []  # id_cotizacion (cliente)
        self.sales = []  # id_orden_venta
        self.products = []  # id_producto
        self.clients = []  # id_cliente
        self.providers = []  # id_proveedor
        self.users = []  # id (users)
        self.audit_emails = []  # email_usuario de entradas de auditoría

    def clean(self) -> None:
        db = SessionLocal()
        try:
            for i in self.movements:
                db.execute(text("DELETE FROM movements WHERE id_movimiento = :i"), {"i": i})
            for i in self.provider_quotations:
                db.execute(
                    text("DELETE FROM provider_quotations WHERE id_cotizacion = :i"),
                    {"i": i},
                )
            for i in self.stock_requests:
                db.execute(
                    text("DELETE FROM stock_requests WHERE id_solicitud = :i"), {"i": i}
                )
            for i in self.orders:
                db.execute(
                    text("DELETE FROM purchase_orders WHERE id_orden_compra = :i"),
                    {"i": i},
                )
            for i in self.quotations:
                db.execute(
                    text("DELETE FROM quotations WHERE id_cotizacion = :i"), {"i": i}
                )
            for i in self.sales:
                db.execute(
                    text("DELETE FROM sales WHERE id_orden_venta = :i"), {"i": i}
                )
            for i in self.products:
                db.execute(
                    text("DELETE FROM products WHERE id_producto = :i"), {"i": i}
                )
            for i in self.clients:
                db.execute(text("DELETE FROM clients WHERE id_cliente = :i"), {"i": i})
            for i in self.providers:
                db.execute(
                    text("DELETE FROM providers WHERE id_proveedor = :i"), {"i": i}
                )
            for email in self.audit_emails:
                db.execute(
                    text("DELETE FROM audit_log WHERE email_usuario = :e"), {"e": email}
                )
            for i in self.users:
                db.execute(text("DELETE FROM users WHERE id = :i"), {"i": i})
            db.commit()
        finally:
            db.close()


@pytest.fixture
def tracker() -> Tracker:
    data = Tracker()
    yield data
    data.clean()


@pytest.fixture
def auth(client, admin_token):
    """Registra un usuario de prueba y devuelve sus headers de auth; lo limpia al final."""

    class TestUser:
        def __init__(self, name: str, email: str, rol: str, headers: dict, user_id: str):
            self.name = name
            self.email = email
            self.rol = rol
            self.headers = headers
            self.id = user_id

    created: list[TestUser] = []

    def _auth(rol: str, name: str | None = None) -> TestUser:
        suffix = uuid.uuid4().hex[:8]
        display_name = name or f"test_{rol}"
        email = f"test_{display_name}_{suffix}@test.com"
        admin_headers = _admin_headers(admin_token)
        resp = client.post(
            "/api/v1/auth/register",
            headers=admin_headers,
            json={"name": display_name[:26], "email": email, "password": "Test123!", "rol": rol},
        )
        assert resp.status_code == 201, resp.text
        user = resp.json()
        login = client.post(
            "/api/v1/auth/login", json={"email": email, "password": "Test123!"}
        )
        assert login.status_code == 200, login.text
        test_user = TestUser(
            name=user["name"],
            email=email,
            rol=rol,
            headers=_admin_headers(login.json()["access_token"]),
            user_id=str(user["id"]),
        )
        created.append(test_user)
        return test_user

    yield _auth

    if not created:
        return
    db = SessionLocal()
    try:
        for user in created:
            db.execute(
                text("DELETE FROM audit_log WHERE email_usuario = :e"), {"e": user.email}
            )
            db.execute(text("DELETE FROM users WHERE id = :i"), {"i": user.id})
        db.commit()
    finally:
        db.close()