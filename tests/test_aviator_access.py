from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_production_import_and_history_require_dashboard_token(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "dashboard_access_token", "")

    payload = {
        "file_name": "rounds.json",
        "format": "json",
        "content": '[{"l":"secure-r1","f":2.2,"ts":1760000000000}]',
        "source": "synthetic security test",
        "authorization_basis": "Synthetic fixture",
    }
    blocked = client.post("/api/v1/data/aviator/import", json=payload)
    assert blocked.status_code == 503

    monkeypatch.setattr(settings, "dashboard_access_token", "test-only-secret")
    unauthorized = client.post("/api/v1/data/aviator/import", json=payload)
    assert unauthorized.status_code == 401

    authorized = client.post(
        "/api/v1/data/aviator/import",
        json=payload,
        headers={"X-Dashboard-Token": "test-only-secret"},
    )
    assert authorized.status_code == 200

    blocked_history = client.get("/api/v1/aviator/rounds")
    assert blocked_history.status_code == 401

    authorized_history = client.get(
        "/api/v1/aviator/rounds",
        headers={"X-Dashboard-Token": "test-only-secret"},
    )
    assert authorized_history.status_code == 200
    assert authorized_history.json()["total"] == 1
