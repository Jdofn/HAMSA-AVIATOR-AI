from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _payload(rounds):
    return {
        "rounds": rounds,
        "source": "synthetic test fixture",
        "authorization_basis": "Synthetic data created for unit tests",
    }


def test_historical_analytics_returns_descriptive_statistics_only():
    response = client.post("/api/v1/aviator/analyze", json=_payload([
        {"multiplier": 1.0},
        {"multiplier": 2.0},
        {"multiplier": 5.0},
        {"multiplier": 10.0},
    ]))
    assert response.status_code == 200
    body = response.json()
    assert body["round_count"] == 4
    assert body["multipliers"]["minimum"] == 1.0
    assert body["multipliers"]["maximum"] == 10.0
    assert body["multipliers"]["median"] == 3.5
    assert body["thresholds"]["at_least_2x"]["count"] == 3
    assert body["thresholds"]["at_least_5x"]["count"] == 2
    assert body["distribution"]["below_1_20x"] == 1
    assert body["streaks"]["max_consecutive_below_2x"] == 1
    assert body["mode"] == "historical_descriptive_only"
    assert "prediction" not in body


def test_optional_source_metrics_are_aggregated_not_exposed_per_round():
    response = client.post("/api/v1/aviator/analyze", json=_payload([
        {"multiplier": 1.5, "players": 10, "bets": 20, "prize": 30},
        {"multiplier": 2.5, "players": 20, "bets": 40, "prize": 60},
    ]))
    assert response.status_code == 200
    metrics = response.json()["source_metrics"]
    assert metrics["players"] == {"samples": 2, "average": 15.0, "total": 30}
    assert metrics["bets"]["total"] == 60
    assert metrics["prize"]["total"] == 90
    assert "players" not in response.json()["multipliers"]


def test_analytics_accepts_importer_nested_source_metrics():
    response = client.post("/api/v1/aviator/analyze", json=_payload([
        {"multiplier": 1.5, "source_metrics": {"players": 10, "bets": 20, "prize": 30}},
        {"multiplier": 2.5, "source_metrics": {"players": 20, "bets": 40, "prize": 60}},
    ]))
    assert response.status_code == 200
    metrics = response.json()["source_metrics"]
    assert metrics["players"]["average"] == 15.0
    assert metrics["bets"]["total"] == 60
    assert metrics["prize"]["total"] == 90


def test_rejects_empty_rounds_and_nonpositive_multipliers():
    empty = client.post("/api/v1/aviator/analyze", json=_payload([]))
    invalid = client.post("/api/v1/aviator/analyze", json=_payload([{"multiplier": 0}]))
    assert empty.status_code == 422
    assert invalid.status_code == 422


def test_recent_mean_uses_last_ten_samples():
    rounds = [{"multiplier": float(value)} for value in range(1, 13)]
    response = client.post("/api/v1/aviator/analyze", json=_payload(rounds))
    assert response.status_code == 200
    assert response.json()["recent_10_mean"] == 7.5


def test_analysis_requires_provenance():
    response = client.post("/api/v1/aviator/analyze", json={"rounds": [{"multiplier": 2.0}]})
    assert response.status_code == 422
