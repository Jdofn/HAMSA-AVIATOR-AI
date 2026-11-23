from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_status():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "HAMSA AVIATOR AI"
    assert body["phase"] == "05"

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_system_status_marks_data_source_unconfigured():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json()["official_data_source_configured"] is False
    assert response.json()["phase"] == 2
