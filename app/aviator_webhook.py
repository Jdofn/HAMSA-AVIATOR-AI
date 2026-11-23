"""HMAC-authenticated webhook for explicitly authorized normalized live feeds."""
import hashlib
import hmac
import re
import time

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.aviator_live_feed import LiveFeedBatch, ingest_authorized_feed
from app.config import settings
from app.db import get_db

router = APIRouter()
MAX_BODY_BYTES = 256_000


@router.post("/feed/webhook")
async def receive_signed_webhook(
    request: Request,
    x_hamsa_timestamp: str | None = Header(default=None),
    x_hamsa_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """Verify HMAC over timestamp + exact raw body, then persist normalized events."""
    secret = settings.live_feed_webhook_secret
    if not secret:
        raise HTTPException(status_code=503, detail="Signed webhook is not configured")
    if not x_hamsa_timestamp or not x_hamsa_signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature headers")
    if not x_hamsa_timestamp.isascii() or not x_hamsa_timestamp.isdigit():
        raise HTTPException(status_code=401, detail="Invalid webhook timestamp")
    if not re.fullmatch(r"sha256=[0-9a-f]{64}", x_hamsa_signature):
        raise HTTPException(status_code=401, detail="Signature must be a lowercase SHA-256 hex digest")

    timestamp = int(x_hamsa_timestamp)
    tolerance = max(30, int(settings.live_feed_webhook_tolerance_seconds))
    if abs(int(time.time()) - timestamp) > tolerance:
        raise HTTPException(status_code=401, detail="Webhook timestamp outside allowed window")

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_BODY_BYTES:
                raise HTTPException(status_code=413, detail="Webhook body exceeds 256 KB limit")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid Content-Length header") from exc

    # Enforce the limit while streaming; do not buffer an unbounded chunked body.
    body_buffer = bytearray()
    async for chunk in request.stream():
        body_buffer.extend(chunk)
        if len(body_buffer) > MAX_BODY_BYTES:
            raise HTTPException(status_code=413, detail="Webhook body exceeds 256 KB limit")
    raw_body = bytes(body_buffer)

    signed_payload = x_hamsa_timestamp.encode("ascii") + b"." + raw_body
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), signed_payload, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, x_hamsa_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = LiveFeedBatch.model_validate_json(raw_body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail="Invalid normalized live-feed payload") from exc

    result = ingest_authorized_feed(payload=payload, db=db, _=None)
    result["authentication"] = "hmac_sha256_verified"
    result["limitations"].append(
        "HMAC confirms integrity and possession of the configured shared secret; it does not independently verify upstream authorization or game-result truth."
    )
    return result
