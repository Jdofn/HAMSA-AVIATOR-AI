"""Defensive security research endpoints. No third-party target scanning or access bypass."""
import base64
import binascii
import hashlib
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

class InspectRequest(BaseModel):
    data: str = Field(min_length=1, max_length=16384)
    format: str = Field(default="base64", pattern="^(base64|hex|utf8)$")

@router.get("/scope")
async def scope():
    return {
        "mode": "defensive_research",
        "allowed": [
            "offline analysis of user-provided data",
            "encoding and hash inspection",
            "security checks on HAMSA-owned components",
            "authorized lab testing",
        ],
        "blocked": [
            "unauthorized access to third-party systems",
            "credential or session theft",
            "circumventing authentication, rate limits, or access controls",
            "decrypting data without the required key and authorization",
        ],
        "third_party_1xbet_integration": "not_configured",
    }

@router.post("/crypto/inspect")
async def inspect_crypto_payload(request: InspectRequest):
    """Decode encodings (not encryption) and calculate a SHA-256 fingerprint."""
    try:
        if request.format == "base64":
            raw = base64.b64decode(request.data, validate=True)
        elif request.format == "hex":
            raw = bytes.fromhex(request.data)
        else:
            raw = request.data.encode("utf-8")
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid encoded input") from exc

    preview = raw[:256]
    try:
        text_preview = preview.decode("utf-8")
        text_valid = True
    except UnicodeDecodeError:
        text_preview = None
        text_valid = False

    return {
        "input_format": request.format,
        "decoded_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "utf8_valid": text_valid,
        "text_preview": text_preview,
        "hex_preview": preview.hex(),
        "truncated": len(raw) > len(preview),
        "note": "Base64 and hex are encodings, not encryption. No decryption or key recovery is performed.",
    }

@router.get("/headers/check")
async def check_security_headers():
    """Static baseline for HAMSA API response hardening; does not scan remote hosts."""
    recommended = {
        "content-security-policy": "Define a restrictive policy appropriate to the API/UI.",
        "x-content-type-options": "nosniff",
        "referrer-policy": "no-referrer",
        "cache-control": "no-store for sensitive responses",
    }
    return {
        "check_type": "static_recommendations",
        "target": "HAMSA deployment configuration",
        "recommendations": recommended,
        "remote_scanning_performed": False,
    }
