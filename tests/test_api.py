from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_status():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "HAMSA AVIATOR AI"
    assert body["phase"] == "06"

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
