from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_live_feed_requires_configured_production_token(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "dashboard_access_token", "phase04-secret")
    payload = {
        "source": "authorized synthetic feed",
        "authorization_basis": "Operator-controlled test fixture",
        "records": [{"round_id": "live-001", "multiplier": 2.4, "time_of_day": "12:30"}],
    }
    denied = client.post("/api/v1/aviator/feed/batch", json=payload)
    assert denied.status_code == 401
    accepted = client.post(
        "/api/v1/aviator/feed/batch",
        json=payload,
        headers={"X-Dashboard-Token": "phase04-secret"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["inserted_count"] == 1


def test_live_feed_is_idempotent_and_visible_in_dashboard_history(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "dashboard_access_token", "")
    payload = {
        "source": "synthetic local adapter",
        "authorization_basis": "Synthetic test data",
        "records": [
            {"round_id": "live-002", "multiplier": 1.8, "occurred_at": "2026-11-23T10:00:00Z"},
            {"round_id": "live-003", "multiplier": 7.2, "players": 15, "bets": 20, "prize": 90},
            {"round_id": "live-003", "multiplier": 99.0},
        ],
    }
    first = client.post("/api/v1/aviator/feed/batch", json=payload)
    second = client.post("/api/v1/aviator/feed/batch", json=payload)
    assert first.status_code == 200
    assert first.json()["inserted_count"] == 2
    assert second.json()["inserted_count"] == 0
    assert second.json()["duplicate_count"] == 2

    history = client.get("/api/v1/aviator/rounds").json()
    assert history["total"] == 2
    assert {item["round_reference"] for item in history["items"]} == {"live-002", "live-003"}
    summary = client.get("/api/v1/aviator/summary").json()
    assert summary["round_count"] == 2
    assert summary["maximum"] == 7.2


def test_live_feed_rejects_invalid_values_and_oversized_batches():
    base = {
        "source": "authorized local feed",
        "authorization_basis": "Operator-owned source",
    }
    invalid = {**base, "records": [{"round_id": "bad", "multiplier": 0}]}
    assert client.post("/api/v1/aviator/feed/batch", json=invalid).status_code == 422
    oversized = {**base, "records": [{"round_id": str(i), "multiplier": 1.1} for i in range(251)]}
    assert client.post("/api/v1/aviator/feed/batch", json=oversized).status_code == 422
    naive_timestamp = {**base, "records": [{"round_id": "bad-time", "multiplier": 1.1, "occurred_at": "2026-11-23T10:00:00"}]}
    assert client.post("/api/v1/aviator/feed/batch", json=naive_timestamp).status_code == 422
