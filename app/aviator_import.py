"""Offline importer for user-supplied Aviator CF Capture CSV/JSON exports.

This module does not launch browsers, connect to betting sites, inspect network
traffic, or persist imported records.
"""
import csv
import io
import json
import math
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()
MAX_CONTENT_CHARS = 1_000_000
MAX_RECORDS = 10_000


class AviatorImportRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=180)
    format: str = Field(pattern="^(json|csv)$")
    content: str = Field(min_length=1, max_length=MAX_CONTENT_CHARS)
    source: str = Field(min_length=3, max_length=300)
    authorization_basis: str = Field(min_length=5, max_length=500)


def _timestamp(value: Any) -> datetime:
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.strip().isdigit()):
        # The source project's JavaScript Date(ts) usage indicates epoch milliseconds.
        return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    raise ValueError("TS must be epoch milliseconds or an ISO-8601 timestamp")


def normalize_capture_records(content: str, file_format: str) -> list[dict[str, Any]]:
    try:
        if file_format == "json":
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                parsed = parsed.get("records", parsed.get("data", [parsed]))
            if not isinstance(parsed, list) or not all(isinstance(row, dict) for row in parsed):
                raise ValueError("JSON must contain an array of capture objects")
            rows = parsed
        else:
            # Legacy source writes headerless rows: Time, players, bets, F, prize, L.
            raw_rows = list(csv.reader(io.StringIO(content)))
            if not raw_rows:
                raise ValueError("CSV must contain at least one data row")
            known_headers = {"f", "ts", "time", "l"}
            first = {cell.strip().lower() for cell in raw_rows[0]}
            if first.intersection(known_headers):
                rows = list(csv.DictReader(io.StringIO(content)))
            else:
                rows = []
                for values in raw_rows:
                    if len(values) != 6:
                        raise ValueError("Headerless capture CSV rows must contain exactly 6 columns")
                    time_value, _players, _bets, multiplier_value, _prize, round_value = values
                    rows.append({"Time": time_value, "F": multiplier_value, "L": round_value})
            if not rows or not rows[0]:
                raise ValueError("CSV must contain at least one data row")
    except (json.JSONDecodeError, csv.Error) as exc:
        raise ValueError(f"Invalid {file_format.upper()} capture export") from exc

    if not rows or len(rows) > MAX_RECORDS:
        raise ValueError(f"Capture export must contain between 1 and {MAX_RECORDS} rows")

    normalized = []
    for index, row in enumerate(rows, start=1):
        fields = {str(key).strip().lower(): value for key, value in row.items() if key is not None}
        if "f" not in fields or not ({"ts", "time"} & fields.keys()):
            raise ValueError(f"Row {index} must contain F and either TS or Time")
        try:
            multiplier = float(fields["f"])
            if not math.isfinite(multiplier) or multiplier <= 0:
                raise ValueError
            if fields.get("ts") not in (None, ""):
                occurred_at = _timestamp(fields["ts"])
                time_of_day = None
            else:
                time_of_day = str(fields["time"]).strip()
                datetime.strptime(time_of_day, "%H:%M")
                occurred_at = None
        except (TypeError, ValueError, OverflowError, OSError) as exc:
            raise ValueError(f"Row {index} has invalid F or TS value") from exc
        round_reference = fields.get("l")
        normalized.append({
            "round_reference": str(round_reference)[:128] if round_reference not in (None, "") else None,
            "multiplier": multiplier,
            "occurred_at": occurred_at.isoformat() if occurred_at else None,
            "time_of_day": time_of_day,
            "verification_status": "unverified",
        })
    return normalized


@router.post("/aviator/import")
async def import_aviator_capture(request: AviatorImportRequest):
    """Normalize a local export for analysis; never fetch or persist third-party data."""
    try:
        rounds = normalize_capture_records(request.content, request.format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "status": "imported_for_analysis",
        "persisted": False,
        "record_count": len(rounds),
        "rounds": rounds,
        "provenance": {
            "file_name": request.file_name,
            "source": request.source,
            "authorization_basis": request.authorization_basis,
            "provided_by_requester": True,
            "independently_verified": False,
        },
        "limitations": [
            "Only L, F, and TS fields are normalized; player, bet, and prize metrics are ignored.",
            "TS numeric values are interpreted as Unix epoch milliseconds; the source CSV HH:mm-only Time field is preserved without inventing a calendar date.",
            "All records remain unverified; import does not establish Provably Fair validity.",
            "No browser automation, network capture, account access, or database persistence occurs.",
        ],
    }
