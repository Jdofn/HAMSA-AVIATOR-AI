"""Offline protocol metadata inspection and HMAC verification for authorized labs."""
import hashlib
import hmac
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, model_validator

router = APIRouter()
ALLOWED_HEADERS = {
    "content-type", "content-length", "accept", "cache-control",
    "upgrade", "sec-websocket-protocol",
}


class ProtocolEvent(BaseModel):
    protocol: Literal["http", "websocket"]
    event_type: Literal["http_request", "http_response", "websocket_message"]
    direction: Literal["inbound", "outbound"]
    method: str | None = Field(default=None, max_length=16, pattern=r"^[A-Z]+$")
    status_code: int | None = Field(default=None, ge=100, le=599)
    route_template: str | None = Field(default=None, max_length=200, pattern=r"^/[A-Za-z0-9_/{}/.-]*$")
    message_type: Literal["text", "binary", "ping", "pong", "close"] | None = None
    payload_bytes: int = Field(default=0, ge=0, le=10_000_000)
    headers: dict[str, str] = Field(default_factory=dict, max_length=40)

    @model_validator(mode="after")
    def validate_protocol_shape(self):
        if self.protocol == "http":
            if self.event_type == "websocket_message":
                raise ValueError("HTTP events cannot be websocket_message")
            if self.event_type == "http_request" and not self.method:
                raise ValueError("HTTP requests require method")
            if self.event_type == "http_response" and self.status_code is None:
                raise ValueError("HTTP responses require status_code")
            if self.message_type is not None:
                raise ValueError("HTTP events cannot include message_type")
        else:
            if self.event_type != "websocket_message":
                raise ValueError("WebSocket events must use websocket_message")
            if self.message_type is None:
                raise ValueError("WebSocket messages require message_type")
            if self.method is not None or self.status_code is not None:
                raise ValueError("WebSocket messages cannot include HTTP fields")
        return self


class ProtocolInspectRequest(BaseModel):
    source: str = Field(min_length=3, max_length=300)
    authorization_basis: str = Field(min_length=5, max_length=500)
    events: list[ProtocolEvent] = Field(min_length=1, max_length=1000)


class HMACVerifyRequest(BaseModel):
    message: str = Field(max_length=65536)
    secret_key: str = Field(min_length=1, max_length=4096)
    expected_digest: str = Field(pattern=r"^[0-9a-fA-F]+$", min_length=64, max_length=128)
    algorithm: Literal["sha256", "sha512"] = "sha256"

    @model_validator(mode="after")
    def validate_digest_length(self):
        expected_length = 64 if self.algorithm == "sha256" else 128
        if len(self.expected_digest) != expected_length:
            raise ValueError(f"{self.algorithm} digest must be {expected_length} hexadecimal characters")
        return self


@router.post("/protocol/inspect")
async def inspect_protocol_export(request: ProtocolInspectRequest):
    """Summarize sanitized HTTP/WebSocket metadata; never accepts packet payloads."""
    counts = {"http_request": 0, "http_response": 0, "websocket_message": 0}
    header_counts: dict[str, int] = {}
    payload_total = 0
    summaries = []

    for event in request.events:
        counts[event.event_type] += 1
        payload_total += event.payload_bytes
        safe_headers = {}
        for name, value in event.headers.items():
            normalized = name.lower().strip()
            if normalized in ALLOWED_HEADERS:
                safe_headers[normalized] = value[:200]
                header_counts[normalized] = header_counts.get(normalized, 0) + 1
        summaries.append({
            "protocol": event.protocol,
            "event_type": event.event_type,
            "direction": event.direction,
            "method": event.method,
            "status_code": event.status_code,
            "route_template": event.route_template,
            "message_type": event.message_type,
            "payload_bytes": event.payload_bytes,
            "headers": safe_headers,
        })

    return {
        "status": "inspected",
        "persisted": False,
        "source": request.source,
        "authorization_basis": request.authorization_basis,
        "provenance_claims_verified": False,
        "event_count": len(request.events),
        "counts": counts,
        "allowed_header_counts": header_counts,
        "payload_bytes_total": payload_total,
        "events": summaries,
        "limitations": [
            "Only structured metadata is accepted; raw packet bodies and credentials are not parsed.",
            "Only allowlisted header names are returned; all other headers are dropped.",
            "Source and authorization claims are requester-supplied and are not independently verified.",
            "No network connection, remote scanning, or traffic interception is performed.",
        ],
    }


@router.post("/crypto/hmac/verify")
async def verify_hmac(request: HMACVerifyRequest):
    """Verify a supplied HMAC using a requester-provided key, in memory only."""
    key = request.secret_key.encode("utf-8")
    message = request.message.encode("utf-8")
    digest = hmac.new(key, message, getattr(hashlib, request.algorithm)).hexdigest()
    valid = hmac.compare_digest(digest, request.expected_digest.lower())
    return {
        "algorithm": request.algorithm,
        "valid": valid,
        "message_sha256": hashlib.sha256(message).hexdigest(),
        "key_persisted": False,
        "digest_returned": False,
        "note": "The supplied key is used only for this request and is not stored or returned.",
    }
