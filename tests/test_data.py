from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_json_dataset_inspection_redacts_secrets_and_tracks_provenance():
    response = client.post("/api/v1/data/datasets/inspect", json={
        "file_name": "sample.json",
        "format": "json",
        "content": '[{"round_id":"r1","multiplier":2.4,"authorization":"Bearer private","nested":{"api_key":"secret"}}]',
        "source": "locally generated test fixture",
        "authorization_basis": "Owned synthetic test data",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["record_count"] == 1
    assert body["redactions"] == 2
    assert body["preview"][0]["authorization"] == "[REDACTED]"
    assert body["preview"][0]["nested"]["api_key"] == "[REDACTED]"
    assert body["persisted"] is False
    assert body["provenance"]["provided_by_requester"] is True
    assert len(body["sha256"]) == 64

def test_csv_dataset_inspection():
    response = client.post("/api/v1/data/datasets/inspect", json={
        "file_name": "rounds.csv",
        "format": "csv",
        "content": "round_id,multiplier\nr1,1.5\nr2,3.2",
        "source": "local sample",
        "authorization_basis": "Synthetic data created by project owner",
    })
    assert response.status_code == 200
    assert response.json()["record_count"] == 2
    assert response.json()["columns"] == ["multiplier", "round_id"]

def test_dataset_rejects_invalid_json():
    response = client.post("/api/v1/data/datasets/inspect", json={
        "file_name": "bad.json",
        "format": "json",
        "content": "{invalid",
        "source": "local test",
        "authorization_basis": "Owned test fixture",
    })
    assert response.status_code == 400

def test_dataset_rejects_path_like_filename():
    response = client.post("/api/v1/data/datasets/inspect", json={
        "file_name": "../secrets.json",
        "format": "json",
        "content": "[]",
        "source": "local test",
        "authorization_basis": "Owned test fixture",
    })
    assert response.status_code == 422

def test_dataset_requires_provenance():
    response = client.post("/api/v1/data/datasets/inspect", json={
        "file_name": "sample.json",
        "format": "json",
        "content": "[]",
        "source": "local test",
    })
    assert response.status_code == 422
