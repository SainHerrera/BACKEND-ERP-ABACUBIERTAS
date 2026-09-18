from __future__ import annotations


def _admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


def test_settings_margen_tope_100(client, admin_token):
    headers = _admin_headers(admin_token)
    current = client.get("/api/v1/settings", headers=headers).json()
    previous_margen = current["margen_utilidad_default"]

    resp = client.patch(
        "/api/v1/settings",
        headers=headers,
        json={"margen_utilidad_default": 150},
    )
    assert resp.status_code == 422, resp.text

    try:
        resp = client.patch(
            "/api/v1/settings",
            headers=headers,
            json={"margen_utilidad_default": 95},
        )
        assert resp.status_code == 200, resp.text
        saved = client.get("/api/v1/settings", headers=headers).json()
        assert saved["margen_utilidad_default"] == 95
    finally:
        client.patch(
            "/api/v1/settings",
            headers=headers,
            json={"margen_utilidad_default": previous_margen},
        )


def test_settings_margen_limite_inferior(client, admin_token):
    headers = _admin_headers(admin_token)
    resp = client.patch(
        "/api/v1/settings",
        headers=headers,
        json={"margen_utilidad_default": -5},
    )
    assert resp.status_code == 422, resp.text