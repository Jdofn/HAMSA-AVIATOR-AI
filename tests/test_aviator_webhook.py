import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def signed_headers(body: bytes, secret: str, timestamp: int | None = None):
    ts = str(timestamp if timestamp is not None else int(time.time()))
    digest = hmac.new(secret.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
    return {"X-HAMSA-Timestamp": ts, "X-HAMSA-Signature": "sha256=" + digest}


def test_signed_webhook_requires_secret(monkeypatch):
    monkeypatch.setattr(settings, "live_feed_webhook_secret", "")
    response = client.post("/api/v1/aviator/feed/webhook", content=b"{}")
    assert response.status_code == 503


def test_signed_webhook_accepts_valid_signature_and_deduplicates(monkeypatch):
    secret = "test-webhook-secret"
    monkeypatch.setattr(settings, "live_feed_webhook_secret", secret)
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "dashboard_access_token", "")
    payload = {
        "source": "operator-authorized test provider",
        "authorization_basis": "Synthetic test fixture",
        "records": [{"round_id": "webhook-phase06-001", "multiplier": 2.75}],
    }
    body = json.dumps(payload, separators=(",", ":")).encode()
    response = client.post(
        "/api/v1/aviator/feed/webhook",
        content=body,
        headers={"Content-Type": "application/json", **signed_headers(body, secret)},
    )
    assert response.status_code == 200
    assert response.json()["inserted_count"] == 1
    again = client.post(
        "/api/v1/aviator/feed/webhook",
        content=body,
        headers={"Content-Type": "application/json", **signed_headers(body, secret)},
    )
    assert again.status_code == 200
    assert again.json()["inserted_count"] == 0


def test_signed_webhook_rejects_tampering_and_stale_timestamp(monkeypatch):
    secret = "test-webhook-secret"
    monkeypatch.setattr(settings, "live_feed_webhook_secret", secret)
    body = json.dumps({
        "source": "authorized test provider",
        "authorization_basis": "Synthetic test fixture",
        "records": [{"round_id": "webhook-phase06-002", "multiplier": 1.5}],
    }).encode()
    headers = signed_headers(body, secret)
    tampered = body.replace(b"1.5", b"9.5")
    assert client.post("/api/v1/aviator/feed/webhook", content=tampered, headers=headers).status_code == 401
    stale_headers = signed_headers(body, secret, int(time.time()) - 600)
    assert client.post("/api/v1/aviator/feed/webhook", content=body, headers=stale_headers).status_code == 401


def test_signed_webhook_rejects_non_sha256_signature_and_future_timestamp(monkeypatch):
    secret = "phase06-extra-test-secret"
    monkeypatch.setattr(settings, "live_feed_webhook_secret", secret)
    body = json.dumps({
        "source": "authorized test provider",
        "authorization_basis": "Synthetic test fixture",
        "records": [{"round_id": "webhook-phase06-003", "multiplier": 1.9}],
    }).encode()
    headers = signed_headers(body, secret)
    headers["X-HAMSA-Signature"] = headers["X-HAMSA-Signature"].removeprefix("sha256=")
    assert client.post("/api/v1/aviator/feed/webhook", content=body, headers=headers).status_code == 401

    future = signed_headers(body, secret, int(time.time()) + 600)
    assert client.post("/api/v1/aviator/feed/webhook", content=body, headers=future).status_code == 401


def test_signed_webhook_rejects_oversized_body(monkeypatch):
    secret = "phase06-large-body-secret"
    monkeypatch.setattr(settings, "live_feed_webhook_secret", secret)
    body = b" " * 256_001
    headers = signed_headers(body, secret)
    response = client.post("/api/v1/aviator/feed/webhook", content=body, headers=headers)
    assert response.status_code == 413
