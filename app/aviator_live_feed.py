"""Authenticated ingestion adapter for explicitly authorized live data feeds.

This endpoint accepts normalized round events from a source the operator is
authorized to use. It does not connect to third-party sites, inspect browser
sessions, or intercept network traffic.
"""
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.aviator_access import require_dashboard_access
from app.db import get_db
from app.models import RoundResult

router = APIRouter()
MAX_BATCH_SIZE = 250
TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class LiveRound(BaseModel):
    round_id: str = Field(min_length=1, max_length=128)
    multiplier: float = Field(gt=0, allow_inf_nan=False)
    occurred_at: datetime | None = None
    time_of_day: str | None = Field(default=None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    players: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    bets: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    prize: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @field_validator("occurred_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("occurred_at must include a timezone")
        return value.astimezone(timezone.utc)


class LiveFeedBatch(BaseModel):
    source: str = Field(min_length=3, max_length=300)
    authorization_basis: str = Field(min_length=5, max_length=500)
    records: list[LiveRound] = Field(min_length=1, max_length=MAX_BATCH_SIZE)


@router.post("/feed/batch")
def ingest_authorized_feed(
    payload: LiveFeedBatch,
    db: Session = Depends(get_db),
    _: None = Depends(require_dashboard_access),
):
    """Persist a bounded batch from an authorized adapter; duplicate IDs are skipped."""
    inserted = 0
    duplicates = 0
    try:
        for record in payload.records:
            existing = db.query(RoundResult.id).filter(
                RoundResult.provider == "authorized_live_feed",
                RoundResult.round_id == record.round_id,
            ).first()
            if existing:
                duplicates += 1
                continue

            event_time = record.occurred_at or datetime.now(timezone.utc)
            db.add(RoundResult(
                provider="authorized_live_feed",
                round_id=record.round_id,
                multiplier=record.multiplier,
                occurred_at=event_time,
                verification_status="unverified",
                time_of_day=record.time_of_day,
                players=record.players,
                bets=record.bets,
                prize=record.prize,
                source=payload.source,
                source_file=None,
                import_batch_hash=None,
            ))
            inserted += 1
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Live-feed batch failed; transaction rolled back") from exc

    return {
        "status": "accepted",
        "provider": "authorized_live_feed",
        "inserted_count": inserted,
        "duplicate_count": duplicates,
        "record_count": len(payload.records),
        "provenance": {
            "source": payload.source,
            "authorization_basis": payload.authorization_basis,
            "provided_by_requester": True,
            "independently_verified": False,
        },
        "limitations": [
            "The adapter accepts normalized events only; it does not collect data from third-party services.",
            "Imported events remain unverified and historical values do not predict future rounds.",
        ],
    }
