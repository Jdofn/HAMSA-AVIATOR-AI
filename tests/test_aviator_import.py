from fastapi.testclient import TestClient
from app.main import app
from app.aviator_import import normalize_capture_records

client = TestClient(app)

BASE = {
    "source": "local exported capture file",
    "authorization_basis": "User-provided local export for authorized research",
}


def _import(content, file_name="capture.csv", fmt="csv"):
    return client.post("/api/v1/data/aviator/import", json={
        **BASE, "file_name": file_name, "format": fmt, "content": content,
    })


def test_import_persists_rounds_and_aggregate_metrics():
    response = _import("Time,Players,Bets,F,Prize,L\n12:30,20,25,2.5,100,round-7\n")
    assert response.status_code == 200
    body = response.json()
    assert body["persisted"] is True
    assert body["inserted_count"] == 1
    assert body["duplicate_count"] == 0

    saved = client.get("/api/v1/aviator/rounds")
    assert saved.status_code == 200
    item = saved.json()["items"][0]
    assert item["multiplier"] == 2.5
    assert item["round_reference"] == "round-7"
    assert item["time_of_day"] == "12:30"
    assert item["players"] == 20
    assert item["bets"] == 25
    assert item["prize"] == 100
    assert item["verification_status"] == "unverified"


def test_reimport_skips_duplicate_round_reference():
    csv_content = "Time,Players,Bets,F,Prize,L\n12:30,20,25,2.5,100,round-7\n"
    first = _import(csv_content)
    second = _import(csv_content)
    assert first.json()["inserted_count"] == 1
    assert second.json()["inserted_count"] == 0
    assert second.json()["duplicate_count"] == 1
    assert client.get("/api/v1/aviator/rounds").json()["total"] == 1


def test_imports_json_with_epoch_milliseconds():
    response = _import('[{"l":"r1","f":1.75,"ts":1760000000000}]', "capture.json", "json")
    assert response.status_code == 200
    assert response.json()["inserted_count"] == 1
    saved = client.get("/api/v1/aviator/rounds").json()["items"][0]
    assert saved["occurred_at"] is not None


def test_rejects_missing_f_or_ts():
    response = _import('[{"l":"r1","f":2.0}]', "bad.json", "json")
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
    response = _import("12:30,20,25,2.5,100,round-8\n", "data.csv")
    assert response.status_code == 200
    assert response.json()["inserted_count"] == 1
    saved = client.get("/api/v1/aviator/rounds").json()["items"][0]
    assert saved["time_of_day"] == "12:30"
    assert saved["round_reference"] == "round-8"
    assert saved["source_file"] == "data.csv"


def test_rejects_invalid_aggregate_metrics():
    try:
        normalize_capture_records("12:30,-1,25,2.5,100,round-9", "csv")
    except ValueError:
        pass
    else:
        raise AssertionError("Negative source metrics must be rejected")


def test_summary_reports_persisted_history():
    _import("Time,Players,Bets,F,Prize,L\n12:30,20,25,2.5,100,round-a\n12:31,30,35,5.5,150,round-b\n")
    summary = client.get("/api/v1/aviator/summary").json()
    assert summary["round_count"] == 2
    assert summary["mean"] == 4.0
    assert summary["minimum"] == 2.5
    assert summary["maximum"] == 5.5
    assert summary["at_least_2x"] == 2
    assert summary["at_least_5x"] == 1


def test_dashboard_page_is_available():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "HAMSA AVIATOR AI" in response.text
    assert "Import & save rounds" in response.text
