from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.config import settings
from app.infrastructure.catalog_seed import SEED_PRODUCTS, SEED_PROVIDERS
from app.infrastructure.db import SessionLocal


def _admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


def _delete_rows(table: str, ids: set[str]) -> None:
    if not ids:
        return
    db = SessionLocal()
    try:
        for row_id in ids:
            db.execute(text(f"DELETE FROM {table} WHERE id = :i"), {"i": row_id})
        db.commit()
    finally:
        db.close()


def test_load_catalog_rbac(client, auth):
    """Solo admin puede cargar el catálogo inicial."""
    for rol in ("ventas", "compras", "bodega", "gerencia"):
        user = auth(rol)
        resp = client.post("/api/v1/settings/load-catalog", headers=user.headers)
        assert resp.status_code == 403, f"Rol {rol} no debe poder cargar el catálogo"


def test_load_catalog_admin_seeds_e_idempotente(client, admin_token):
    headers = _admin_headers(admin_token)

    def snapshot() -> tuple[set[str], set[str]]:
        products = client.get("/api/v1/products?skip=0&limit=500", headers=headers).json()
        providers = client.get("/api/v1/providers?skip=0&limit=500", headers=headers).json()
        return (
            {p["id_producto"] for p in products["items"]},
            {prov["id_proveedor"] for prov in providers["items"]},
        )

    before_products, before_providers = snapshot()

    try:
        resp = client.post("/api/v1/settings/load-catalog", headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert set(data) == {"products", "providers"}
        assert isinstance(data["products"], int)
        assert isinstance(data["providers"], int)

        if not before_providers:
            assert data["providers"] == len(SEED_PROVIDERS)
        else:
            assert data["providers"] == 0
        if not before_products:
            assert data["products"] == len(SEED_PRODUCTS)
        else:
            assert data["products"] == 0

        # Los productos seed quedan referenciando a los proveedores seed.
        products = client.get("/api/v1/products?skip=0&limit=100", headers=headers).json()["items"]
        cubierta = next((p for p in products if p["nombre"] == SEED_PRODUCTS[0]["nombre"]), None)
        if not before_products:
            assert cubierta is not None
            providers = client.get(
                "/api/v1/providers?skip=0&limit=100", headers=headers
            ).json()["items"]
            plastico = next(
                (p for p in providers if p["nombre_empresa"] == "Plásticos & Cubiertas Polímeros"),
                None,
            )
            assert plastico is not None
            assert cubierta["id_proveedor"] == plastico["id_proveedor"]

        # La bandera queda en true.
        current = client.get("/api/v1/settings", headers=headers).json()
        assert current["catalogo_inicial_cargado"] is True

        # La auditoría registra la acción.
        log = client.get(
            "/api/v1/audit-log?skip=0&limit=20&accion=catalog_loaded", headers=headers
        ).json()
        assert any(e["accion"] == "catalog_loaded" for e in log["items"])

        # Segunda llamada: no inserta nada (idempotente).
        resp2 = client.post("/api/v1/settings/load-catalog", headers=headers)
        assert resp2.status_code == 200, resp2.text
        assert resp2.json() == {"products": 0, "providers": 0}
    finally:
        # Limpia solo los registros creados por el test (no toca preexistentes).
        after_products, after_providers = snapshot()
        new_products = after_products - before_products
        new_providers = after_providers - before_providers
        db = SessionLocal()
        try:
            for pid in new_products:
                db.execute(
                    text("DELETE FROM products WHERE id_producto = :i"), {"i": pid}
                )
            for prid in new_providers:
                db.execute(
                    text("DELETE FROM providers WHERE id_proveedor = :i"), {"i": prid}
                )
            db.execute(
                text(
                    "DELETE FROM audit_log WHERE accion = 'catalog_loaded' "
                    "AND email_usuario = :e"
                ),
                {"e": settings.admin_email},
            )
            db.commit()
        finally:
            db.close()