from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _import_rounds():
    csv_content = (
        "TS,totalPlayers,totalBets,F,totalPrize,L\n"
        "1795478400000,10,100,1.2,80,r-001\n"
        "1795478460000,11,110,2.0,90,r-002\n"
        "1795478520000,12,120,1.5,95,r-003\n"
        "1795478580000,13,130,8.0,100,r-004\n"
        "1795478640000,14,140,2.5,110,r-005\n"
        "1795478700000,15,150,12.0,120,r-006\n"
    )
    return client.post("/api/v1/data/aviator/import", json={
        "file_name": "phase09-fixture.csv",
        "format": "csv",
        "content": csv_content,
        "source": "synthetic Phase 09 test fixture",
        "authorization_basis": "Generated locally for automated tests",
    })


def test_phase09_research_overview_uses_persisted_history():
    imported = _import_rounds()
    assert imported.status_code == 200
    assert imported.json()["inserted_count"] == 6

    response = client.get("/api/v1/aviator/research/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "retrospective_descriptive_research_only"
    assert body["round_count"] == 6
    assert body["distribution"]["rates"]["at_least_2x"] == 0.666667
    assert body["data_quality"]["unverified_rows"] == 6
    assert "not forecasts" in body["limitations"][2]


def test_phase09_duplicate_import_does_not_duplicate_rounds():
    first = _import_rounds()
    second = _import_rounds()
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["inserted_count"] == 0
    assert second.json()["duplicate_count"] == 6

    response = client.get("/api/v1/aviator/research/overview")
    assert response.status_code == 200
    assert response.json()["round_count"] == 6


def test_phase09_requires_minimum_history():
    response = client.get("/api/v1/aviator/research/overview?limit=1")
    assert response.status_code == 422
