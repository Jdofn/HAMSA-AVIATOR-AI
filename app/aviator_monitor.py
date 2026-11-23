"""Operational health and quality diagnostics for authorized Aviator feeds.

This module evaluates records already stored by HAMSA. It does not probe,
connect to, or collect data from third-party services.
"""
from datetime import datetime, timedelta, timezone
import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.aviator_access import require_dashboard_access
from app.config import settings
from app.db import get_db
from app.models import RoundResult

router = APIRouter()
PROVIDER = "authorized_live_feed"
QUALITY_SAMPLE_LIMIT = 1000


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@router.get("/monitor/quality")
def feed_quality_monitor(
    sample_limit: int = Query(default=500, ge=1, le=QUALITY_SAMPLE_LIMIT),
    db: Session = Depends(get_db),
    _: None = Depends(require_dashboard_access),
):
    """Return persisted-feed freshness, source coverage, and data-quality metrics."""
    now = datetime.now(timezone.utc)
    total = db.query(func.count(RoundResult.id)).filter(
        RoundResult.provider == PROVIDER
    ).scalar() or 0

    latest_ingest = db.query(func.max(RoundResult.created_at)).filter(
        RoundResult.provider == PROVIDER
    ).scalar()
    latest_event = db.query(func.max(RoundResult.occurred_at)).filter(
        RoundResult.provider == PROVIDER
    ).scalar()

    rows = (
        db.query(RoundResult)
        .filter(RoundResult.provider == PROVIDER)
        .order_by(RoundResult.id.desc())
        .limit(sample_limit)
        .all()
    )

    latest_ingest_utc = _utc(latest_ingest)
    latest_event_utc = _utc(latest_event)
    ingest_age = max(0, int((now - latest_ingest_utc).total_seconds())) if latest_ingest_utc else None
    event_age = int((now - latest_event_utc).total_seconds()) if latest_event_utc else None
    stale_after = max(30, int(settings.feed_stale_after_seconds))

    if not total:
        feed_status = "no_data"
    elif ingest_age is not None and ingest_age > stale_after:
        feed_status = "stale"
    else:
        feed_status = "receiving"

    if not total:
        event_freshness = "no_data"
    elif event_age is not None and event_age < -300:
        event_freshness = "clock_skew"
    elif event_age is not None and event_age > stale_after:
        event_freshness = "old_events"
    else:
        event_freshness = "recent"

    valid_multipliers = sum(
        1 for row in rows
        if isinstance(row.multiplier, (int, float))
        and math.isfinite(float(row.multiplier))
        and float(row.multiplier) > 0
    )
    missing_metrics = sum(
        1 for row in rows
        if row.players is None and row.bets is None and row.prize is None
    )
    future_timestamps = sum(
        1 for row in rows
        if (event_time := _utc(row.occurred_at)) is not None
        and event_time > now + timedelta(minutes=5)
    )
    missing_round_ids = sum(1 for row in rows if not row.round_id)
    sample_count = len(rows)
    quality_score = round(
        100 * (valid_multipliers / sample_count) if sample_count else 0,
        2,
    )

    source_rows = (
        db.query(RoundResult.source, func.count(RoundResult.id))
        .filter(RoundResult.provider == PROVIDER)
        .group_by(RoundResult.source)
        .all()
    )
    sources = [
        {"source": source or "unspecified", "record_count": count}
        for source, count in source_rows
    ]

    return {
        "provider": PROVIDER,
        "feed_status": feed_status,
        "event_freshness": event_freshness,
        "stale_after_seconds": stale_after,
        "total_records": total,
        "sample_size": sample_count,
        "latest_ingested_at": latest_ingest_utc.isoformat() if latest_ingest_utc else None,
        "latest_event_at": latest_event_utc.isoformat() if latest_event_utc else None,
        "ingest_age_seconds": ingest_age,
        "event_age_seconds": event_age,
        "quality": {
            "score": quality_score,
            "valid_multiplier_count": valid_multipliers,
            "invalid_multiplier_count": sample_count - valid_multipliers,
            "records_missing_all_aggregate_metrics": missing_metrics,
            "future_event_timestamps": future_timestamps,
            "missing_round_ids": missing_round_ids,
            "duplicate_prevention": "database_unique_constraint_and_batch_deduplication",
            "historical_duplicate_count": None,
            "historical_duplicate_count_note": "Duplicate submissions are skipped at ingestion and are not retained as audit events.",
        },
        "sources": sources,
        "limitations": [
            "Health is inferred from records already ingested; no upstream service is contacted or independently probed.",
            "A receiving feed status confirms recent ingestion, not that the upstream source is complete or authentic.",
            "Provenance and authorization are requester-supplied and not independently verified.",
            "Quality scores describe stored data and do not predict future game outcomes.",
        ],
    }
