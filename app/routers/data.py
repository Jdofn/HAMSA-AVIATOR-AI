"""Offline JSON/CSV dataset inspection with provenance and secret redaction."""
import csv
import hashlib
import io
import json
import re
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter()
MAX_CONTENT_CHARS = 1_000_000
SENSITIVE_KEY = re.compile(
    r"(authorization|cookie|token|password|passwd|secret|api[_-]?key|private[_-]?key|session)",
    re.IGNORECASE,
)
REDACTED = "[REDACTED]"


class DatasetInspectRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=180)
    format: str = Field(pattern="^(json|csv)$")
    content: str = Field(min_length=1, max_length=MAX_CONTENT_CHARS)
    source: str = Field(min_length=3, max_length=300)
    authorization_basis: str = Field(min_length=5, max_length=500)

    @field_validator("file_name")
    @classmethod
    def safe_file_name(cls, value: str) -> str:
        if "/" in value or "\\" in value or value in {".", ".."}:
            raise ValueError("file_name must be a plain filename")
        return value


def redact(value: Any) -> tuple[Any, int]:
    """Return a sanitized copy and count of redacted values."""
    if isinstance(value, dict):
        clean = {}
        count = 0
        for key, item in value.items():
            if SENSITIVE_KEY.search(str(key)):
                clean[key] = REDACTED
                count += 1
            else:
                clean_item, item_count = redact(item)
                clean[key] = clean_item
                count += item_count
        return clean, count
    if isinstance(value, list):
        clean_items = []
        count = 0
        for item in value:
            clean_item, item_count = redact(item)
            clean_items.append(clean_item)
            count += item_count
        return clean_items, count
    return value, 0


def normalize_records(parsed: Any) -> list[dict[str, Any]]:
    if isinstance(parsed, list) and all(isinstance(row, dict) for row in parsed):
        return parsed
    if isinstance(parsed, dict):
        rows = parsed.get("records", parsed.get("data"))
        if isinstance(rows, list) and all(isinstance(row, dict) for row in rows):
            return rows
        return [parsed]
    raise ValueError("JSON must be an object, an array of objects, or contain a records/data array")


@router.post("/datasets/inspect")
async def inspect_dataset(request: DatasetInspectRequest):
    """Parse a user-provided JSON/CSV dataset in memory; nothing is persisted."""
    raw = request.content.encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    try:
        if request.format == "json":
            records = normalize_records(json.loads(request.content))
        else:
            reader = csv.DictReader(io.StringIO(request.content))
            if not reader.fieldnames:
                raise ValueError("CSV must include a header row")
            records = list(reader)
            if not records:
                raise ValueError("CSV must include at least one data row")
    except (json.JSONDecodeError, csv.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {request.format.upper()} dataset: {exc}") from exc

    sanitized, redaction_count = redact(records)
    columns = sorted({str(key) for row in records for key in row.keys()})
    return {
        "status": "inspected",
        "persisted": False,
        "file_name": request.file_name,
        "format": request.format,
        "record_count": len(records),
        "columns": columns,
        "sha256": digest,
        "redactions": redaction_count,
        "preview": sanitized[:5],
        "provenance": {
            "source": request.source,
            "authorization_basis": request.authorization_basis,
            "provided_by_requester": True,
        },
        "limitations": [
            "Input was processed in memory and was not stored.",
            "Source and authorization claims are supplied by the requester and are not independently verified.",
            "Only JSON and CSV are supported in this phase; packet captures are not parsed.",
        ],
    }
