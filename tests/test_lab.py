import hashlib
import hmac

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_protocol_inspect_filters_sensitive_and_unapproved_headers():
    response = client.post("/api/v1/lab/protocol/inspect", json={
        "source": "owned local integration fixture",
        "authorization_basis": "Synthetic data created for this test",
        "events": [{
            "protocol": "http",
            "event_type": "http_request",
            "direction": "outbound",
            "method": "GET",
            "route_template": "/api/v1/rounds/{round_id}",
            "payload_bytes": 0,
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer do-not-return",
                "Cookie": "session=do-not-return",
                "X-User-Email": "private@example.test",
            },
        }],
    })
    assert response.status_code == 200
    body = response.json()
    assert body["persisted"] is False
    assert body["provenance_claims_verified"] is False
    assert body["events"][0]["headers"] == {"content-type": "application/json"}
    assert "do-not-return" not in response.text
    assert "private@example.test" not in response.text


def test_protocol_inspect_validates_http_response_shape():
    response = client.post("/api/v1/lab/protocol/inspect", json={
        "source": "local fixture",
        "authorization_basis": "Owned synthetic data",
        "events": [{
            "protocol": "http",
            "event_type": "http_response",
            "direction": "inbound",
            "status_code": 204,
        }],
    })
    assert response.status_code == 200
    assert response.json()["counts"]["http_response"] == 1


def test_protocol_inspect_rejects_mismatched_protocol_event():
    response = client.post("/api/v1/lab/protocol/inspect", json={
        "source": "local fixture",
        "authorization_basis": "Owned synthetic data",
        "events": [{
            "protocol": "http",
            "event_type": "websocket_message",
            "direction": "inbound",
            "message_type": "text",
        }],
    })
    assert response.status_code == 422


def test_protocol_inspect_requires_provenance():
    response = client.post("/api/v1/lab/protocol/inspect", json={
        "events": [{
            "protocol": "websocket",
            "event_type": "websocket_message",
            "direction": "inbound",
            "message_type": "text",
        }],
    })
    assert response.status_code == 422


def test_hmac_sha256_valid_and_key_not_returned():
    message = "owned test message"
    key = "local-test-key"
    digest = hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()
    response = client.post("/api/v1/lab/crypto/hmac/verify", json={
        "message": message,
        "secret_key": key,
        "expected_digest": digest,
    })
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["key_persisted"] is False
    assert key not in response.text
    assert digest not in response.text


def test_hmac_sha256_rejects_wrong_digest():
    response = client.post("/api/v1/lab/crypto/hmac/verify", json={
        "message": "message",
        "secret_key": "key",
        "expected_digest": "0" * 64,
    })
    assert response.status_code == 200
    assert response.json()["valid"] is False


def test_hmac_rejects_wrong_digest_length():
    response = client.post("/api/v1/lab/crypto/hmac/verify", json={
        "message": "message",
        "secret_key": "key",
        "expected_digest": "abcd",
    })
    assert response.status_code == 422
