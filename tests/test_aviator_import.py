from fastapi.testclient import TestClient
from app.main import app
from app.aviator_import import normalize_capture_records

client = TestClient(app)


def test_imports_reference_csv_shape_and_preserves_aggregate_metrics():
    response = client.post("/api/v1/data/aviator/import", json={
        "file_name": "capture.csv",
        "format": "csv",
        "content": "Time,Players,Bets,F,Prize,L\n12:30,20,25,2.5,100,round-7\n",
        "source": "local exported capture file",
        "authorization_basis": "User-provided export from an authorized test session",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["persisted"] is False
    assert body["record_count"] == 1
    round_data = body["rounds"][0]
    assert round_data["multiplier"] == 2.5
    assert round_data["round_reference"] == "round-7"
    assert round_data["source_metrics"] == {"players": 20.0, "bets": 25.0, "prize": 100.0}
    assert round_data["verification_status"] == "unverified"


def test_imports_json_with_epoch_milliseconds():
    response = client.post("/api/v1/data/aviator/import", json={
        "file_name": "capture.json",
        "format": "json",
        "content": '[{"l":"r1","f":1.75,"ts":1760000000000}]',
        "source": "synthetic fixture",
        "authorization_basis": "Synthetic test data",
    })
    assert response.status_code == 200
    assert response.json()["record_count"] == 1
    assert response.json()["rounds"][0]["occurred_at"] is not None


def test_rejects_missing_f_or_ts():
    response = client.post("/api/v1/data/aviator/import", json={
        "file_name": "bad.csv",
        "format": "csv",
        "content": '[{"l":"r1","f":2.0}]',
        "source": "fixture",
        "authorization_basis": "Synthetic test data",
    })
    assert response.status_code == 400


def test_rejects_invalid_or_nonpositive_multiplier():
    for value in ["0", "-2", "NaN", "Infinity"]:
        try:
            normalize_capture_records(f'[{{"f":"{value}","ts":1760000000000}}]', "json")
        except ValueError:
            continue
        raise AssertionError(f"Expected invalid multiplier {value} to be rejected")


def test_rejects_oversized_record_count():
    rows = [{"f": 2.0, "ts": 1760000000000}] * 10001
    import json
    try:
        normalize_capture_records(json.dumps(rows), "json")
    except ValueError as exc:
        assert "10000" in str(exc)
    else:
        raise AssertionError("Expected record limit to be enforced")


def test_imports_original_headerless_six_column_csv():
    response = client.post("/api/v1/data/aviator/import", json={
        "file_name": "data.csv",
        "format": "csv",
        "content": "12:30,20,25,2.5,100,round-8\n",
        "source": "local export",
        "authorization_basis": "Authorized local test export",
    })
    assert response.status_code == 200
    round_data = response.json()["rounds"][0]
    assert round_data["time_of_day"] == "12:30"
    assert round_data["occurred_at"] is None
    assert round_data["round_reference"] == "round-8"
    assert round_data["source_metrics"] == {"players": 20.0, "bets": 25.0, "prize": 100.0}


def test_rejects_invalid_aggregate_metrics():
    try:
        normalize_capture_records("12:30,-1,25,2.5,100,round-9", "csv")
    except ValueError:
        pass
    else:
        raise AssertionError("Negative source metrics must be rejected")
