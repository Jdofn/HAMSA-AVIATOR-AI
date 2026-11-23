"""Signed webhook adapter for operator-authorized upstream providers.

Signature format: HMAC-SHA256(secret, timestamp + "." + raw_request_body), hex encoded.
This endpoint does not fetch or scrape any third-party service.
"""
import hashlib
import hmac
import time

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.aviator_live_feed import LiveFeedBatch, ingest_authorized_feed
from app.config import settings
from app.db import get_db

router = APIRouter()
MAX_BODY_BYTES = 256_000
MAX_CLOCK_SKEW_SECONDS = 300


@router.post("/feed/webhook")
async def receive_signed_webhook(
    request: Request,
    x_hamsa_timestamp: str | None = Header(default=None),
    x_hamsa_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """Accept a signed normalized batch from a provider the operator may use."""
    secret = settings.live_feed_webhook_secret
    if not secret:
        raise HTTPException(status_code=503, detail="Signed webhook is not configured")
    if not x_hamsa_timestamp or not x_hamsa_signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature headers")
    try:
        timestamp = int(x_hamsa_timestamp)
        timestamp_bytes = x_hamsa_timestamp.encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError):
        raise HTTPException(status_code=401, detail="Invalid webhook timestamp")
    if abs(int(time.time()) - timestamp) > MAX_CLOCK_SKEW_SECONDS:
        raise HTTPException(status_code=401, detail="Webhook timestamp outside allowed window")

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_BODY_BYTES:
                raise HTTPException(status_code=413, detail="Webhook body exceeds 256 KB limit")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid Content-Length header")
    raw_body = await request.body()
    if len(raw_body) > MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Webhook body exceeds 256 KB limit")
    signed_payload = timestamp_bytes + b"." + raw_body
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    supplied = x_hamsa_signature.removeprefix("sha256=").strip().lower()
    if not hmac.compare_digest(expected, supplied):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = LiveFeedBatch.model_validate_json(raw_body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail="Invalid normalized live-feed payload") from exc

    return ingest_authorized_feed(payload=payload, db=db, _=None)
