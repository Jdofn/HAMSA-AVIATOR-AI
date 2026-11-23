from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_security_scope_discloses_boundaries():
    response = client.get("/api/v1/security/scope")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "defensive_research"
    assert body["third_party_1xbet_integration"] == "not_configured"
    assert any("unauthorized" in item for item in body["blocked"])

def test_crypto_inspect_base64():
    response = client.post(
        "/api/v1/security/crypto/inspect",
        json={"data": "SGVsbG8=", "format": "base64"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["text_preview"] == "Hello"
    assert body["decoded_bytes"] == 5
    assert len(body["sha256"]) == 64

def test_crypto_inspect_rejects_invalid_base64():
    response = client.post(
        "/api/v1/security/crypto/inspect",
        json={"data": "%%%not-base64%%%", "format": "base64"},
    )
    assert response.status_code == 400

def test_crypto_inspect_rejects_oversized_input():
    response = client.post(
        "/api/v1/security/crypto/inspect",
        json={"data": "A" * 17000, "format": "base64"},
    )
    assert response.status_code == 422

def test_headers_check_is_static_only():
    response = client.get("/api/v1/security/headers/check")
    assert response.status_code == 200
    assert response.json()["remote_scanning_performed"] is False
