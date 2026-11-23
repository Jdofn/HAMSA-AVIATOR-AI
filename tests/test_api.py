from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_status():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "HAMSA AVIATOR AI"
    assert body["phase"] == "07"

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_system_status_marks_data_source_unconfigured():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json()["official_data_source_configured"] is False
    assert response.json()["phase"] == 2


def test_sportsbook_source_catalog_is_separate_from_aviator():
    response = client.get("/api/v1/catalog/sportsbook/sources/1xbet-php")
    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "sportsbook"
    assert body["integration_status"] == "catalogued_not_connected"
    assert body["aviator_compatible"] is False
    assert "get_game" in body["reviewed_methods"]
    assert any("no Aviator/Crash" in item for item in body["limitations"])



def test_sportsbook_event_import_and_update():
    payload = {
        "source": "authorized synthetic sportsbook fixture",
        "authorization_basis": "Synthetic test data; no external provider used",
        "events": [{
            "event_id": "test-match-001",
            "sport": "Football",
            "league": "Test League",
            "home_team": "Home FC",
            "away_team": "Away FC",
            "starts_at": "2026-11-24T18:00:00Z",
            "event_status": "scheduled",
            "odds_home": 1.8,
            "odds_draw": 3.4,
            "odds_away": 4.2,
        }],
    }
    first = client.post("/api/v1/catalog/sportsbook/events/import", json=payload)
    assert first.status_code == 200
    assert first.json()["inserted_count"] == 1

    second = client.post("/api/v1/catalog/sportsbook/events/import", json=payload)
    assert second.status_code == 200
    assert second.json()["updated_count"] == 1

    listed = client.get("/api/v1/catalog/sportsbook/events")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["odds_1x2"]["home"] == 1.8

    summary = client.get("/api/v1/catalog/sportsbook/summary")
    assert summary.status_code == 200
    assert summary.json()["event_count"] == 1
    assert summary.json()["with_1x2_odds"] == 1


def test_sportsbook_event_import_rejects_invalid_odds():
    payload = {
        "source": "authorized synthetic sportsbook fixture",
        "authorization_basis": "Synthetic test data",
        "events": [{
            "event_id": "test-match-invalid",
            "sport": "Football",
            "home_team": "Home FC",
            "away_team": "Away FC",
            "odds_home": 0.5,
        }],
    }
    response = client.post("/api/v1/catalog/sportsbook/events/import", json=payload)
    assert response.status_code == 422


def test_crash_monitoring_reference_is_catalogued_not_connected():
    response = client.get("/api/v1/catalog/sportsbook/sources/crash-monitoring")
    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "aviator_research_reference"
    assert body["rest_api_available_in_repository"] is False
    assert body["integration_status"] == "audited_catalogued_not_connected"
    assert body["code_copied"] is False
    assert body["live_connection_enabled"] is False
    assert any("WebSocket scraping" in item for item in body["limitations"])
