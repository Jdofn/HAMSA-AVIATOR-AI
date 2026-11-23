from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _payload(rounds, rolling_window=2):
    return {
        "rounds": rounds,
        "source": "synthetic phase 08 fixture",
        "authorization_basis": "Synthetic records created for automated tests",
        "rolling_window": rolling_window,
    }


def test_advanced_distribution_percentiles_and_threshold_rates():
    response = client.post("/api/v1/aviator/advanced-analyze", json=_payload([
        {"multiplier": 1}, {"multiplier": 2}, {"multiplier": 5}, {"multiplier": 10},
    ]))
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "historical_distribution_volatility_only"
    assert body["round_count"] == 4
    assert body["distribution"]["p50"] == 3.5
    assert body["distribution"]["p95"] > body["distribution"]["p90"]
    assert body["threshold_rates"]["at_least_5x"] == 0.5
    assert body["rolling_volatility"]["window_count"] == 3
    assert "prediction" not in body


def test_time_of_day_uses_timezone_normalized_utc_hour_groups():
    response = client.post("/api/v1/aviator/advanced-analyze", json=_payload([
        {"multiplier": 2, "occurred_at": "2026-11-23T23:30:00-02:00"},
        {"multiplier": 4, "occurred_at": "2026-11-24T01:10:00Z"},
    ]))
    assert response.status_code == 200
    groups = response.json()["time_of_day_utc"]["hourly_groups"]
    assert groups[0]["utc_hour"] == "01:00"
    assert groups[0]["sample_count"] == 2


def test_advanced_analysis_rejects_naive_timestamp_and_small_sample():
    naive = client.post("/api/v1/aviator/advanced-analyze", json=_payload([
        {"multiplier": 2, "occurred_at": "2026-11-23T12:00:00"},
        {"multiplier": 3},
    ]))
    small = client.post("/api/v1/aviator/advanced-analyze", json=_payload([
        {"multiplier": 2},
    ]))
    assert naive.status_code == 422
    assert small.status_code == 422


def test_advanced_analysis_validates_rolling_window():
    response = client.post("/api/v1/aviator/advanced-analyze", json=_payload([
        {"multiplier": 2}, {"multiplier": 3},
    ], rolling_window=1))
    assert response.status_code == 422
