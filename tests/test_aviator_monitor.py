from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def _feed(records):
    return client.post("/api/v1/aviator/feed/batch", json={
        "source": "phase05 synthetic monitor fixture",
        "authorization_basis": "Synthetic records created for local automated tests",
        "records": records,
    })


def test_quality_monitor_reports_no_data():
    response = client.get("/api/v1/aviator/monitor/quality")
    assert response.status_code == 200
    body = response.json()
    assert body["feed_status"] == "no_data"
    assert body["event_freshness"] == "no_data"
    assert body["total_records"] == 0
    assert body["quality"]["score"] == 0


def test_quality_monitor_reports_recent_feed_and_source_breakdown():
    response = _feed([
        {"round_id": "monitor-1", "multiplier": 1.5, "occurred_at": datetime.now(timezone.utc).isoformat()},
        {"round_id": "monitor-2", "multiplier": 4.0, "occurred_at": datetime.now(timezone.utc).isoformat(), "players": 5},
    ])
    assert response.status_code == 200

    monitor = client.get("/api/v1/aviator/monitor/quality")
    assert monitor.status_code == 200
    body = monitor.json()
    assert body["feed_status"] == "receiving"
    assert body["event_freshness"] == "recent"
    assert body["total_records"] == 2
    assert body["quality"]["score"] == 100
    assert body["quality"]["valid_multiplier_count"] == 2
    assert body["quality"]["records_missing_all_aggregate_metrics"] == 1
    assert body["sources"][0]["source"] == "phase05 synthetic monitor fixture"


def test_quality_monitor_flags_old_events_and_future_timestamps():
    old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    response = _feed([
        {"round_id": "monitor-old", "multiplier": 2.0, "occurred_at": old},
        {"round_id": "monitor-future", "multiplier": 3.0, "occurred_at": future},
    ])
    assert response.status_code == 200
    body = client.get("/api/v1/aviator/monitor/quality").json()
    assert body["feed_status"] == "receiving"
    assert body["event_freshness"] == "clock_skew"
    assert body["quality"]["future_event_timestamps"] == 1


def test_quality_monitor_requires_dashboard_token_in_production(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "dashboard_access_token", "phase05-secret")
    denied = client.get("/api/v1/aviator/monitor/quality")
    assert denied.status_code == 401
    accepted = client.get(
        "/api/v1/aviator/monitor/quality",
        headers={"X-Dashboard-Token": "phase05-secret"},
    )
    assert accepted.status_code == 200


def test_quality_monitor_bounds_sample_size():
    assert client.get("/api/v1/aviator/monitor/quality?sample_limit=0").status_code == 422
    assert client.get("/api/v1/aviator/monitor/quality?sample_limit=1001").status_code == 422
