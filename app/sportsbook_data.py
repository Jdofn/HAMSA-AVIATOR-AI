"""Authorized normalized sportsbook event ingestion and read APIs.

This module does not call undocumented 1xBet endpoints. An authorized adapter
must submit normalized event and latest 1X2 odds data.
"""
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.aviator_access import require_dashboard_access
from app.db import get_db
from app.models import SportsbookEvent

router = APIRouter()
MAX_EVENTS_PER_BATCH = 250


class SportsbookEventInput(BaseModel):
    event_id: str = Field(min_length=1, max_length=128)
    sport: str = Field(min_length=2, max_length=120)
    league: str | None = Field(default=None, max_length=180)
    home_team: str = Field(min_length=1, max_length=180)
    away_team: str = Field(min_length=1, max_length=180)
    starts_at: datetime | None = None
    event_status: Literal["scheduled", "live", "finished", "cancelled"] = "scheduled"
    odds_home: float | None = Field(default=None, gt=1, allow_inf_nan=False)
    odds_draw: float | None = Field(default=None, gt=1, allow_inf_nan=False)
    odds_away: float | None = Field(default=None, gt=1, allow_inf_nan=False)

    @field_validator("starts_at")
    @classmethod
    def timezone_aware_start(cls, value: datetime | None):
        if value is not None:
            if value.tzinfo is None:
                raise ValueError("starts_at must include a timezone")
            return value.astimezone(timezone.utc)
        return value


class SportsbookBatch(BaseModel):
    source: str = Field(min_length=3, max_length=300)
    authorization_basis: str = Field(min_length=5, max_length=500)
    events: list[SportsbookEventInput] = Field(min_length=1, max_length=MAX_EVENTS_PER_BATCH)


@router.post("/events/import")
def import_sportsbook_events(
    payload: SportsbookBatch,
    db: Session = Depends(get_db),
    _: None = Depends(require_dashboard_access),
):
    """Upsert event metadata and the latest supplied 1X2 odds snapshot."""
    inserted = updated = duplicates = 0
    seen: set[str] = set()
    now = datetime.now(timezone.utc)
    try:
        for item in payload.events:
            if item.event_id in seen:
                duplicates += 1
                continue
            seen.add(item.event_id)
            event = db.query(SportsbookEvent).filter(
                SportsbookEvent.provider == "authorized_sportsbook_feed",
                SportsbookEvent.event_id == item.event_id,
            ).first()
            if event is None:
                event = SportsbookEvent(
                    provider="authorized_sportsbook_feed",
                    event_id=item.event_id,
                    sport=item.sport,
                    league=item.league,
                    home_team=item.home_team,
                    away_team=item.away_team,
                    starts_at=item.starts_at,
                    event_status=item.event_status,
                    odds_home=item.odds_home,
                    odds_draw=item.odds_draw,
                    odds_away=item.odds_away,
                    odds_updated_at=now if any(v is not None for v in (item.odds_home, item.odds_draw, item.odds_away)) else None,
                    source=payload.source,
                    authorization_basis=payload.authorization_basis,
                    created_at=now,
                    updated_at=now,
                )
                db.add(event)
                inserted += 1
            else:
                event.sport = item.sport
                event.league = item.league
                event.home_team = item.home_team
                event.away_team = item.away_team
                event.starts_at = item.starts_at
                event.event_status = item.event_status
                if any(v is not None for v in (item.odds_home, item.odds_draw, item.odds_away)):
                    event.odds_home = item.odds_home
                    event.odds_draw = item.odds_draw
                    event.odds_away = item.odds_away
                    event.odds_updated_at = now
                event.source = payload.source
                event.authorization_basis = payload.authorization_basis
                event.updated_at = now
                updated += 1
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Sportsbook import failed; transaction rolled back") from exc

    return {
        "status": "accepted",
        "provider": "authorized_sportsbook_feed",
        "inserted_count": inserted,
        "updated_count": updated,
        "duplicate_count": duplicates,
        "event_count": len(payload.events),
        "provenance": {
            "source": payload.source,
            "authorization_basis": payload.authorization_basis,
            "provided_by_requester": True,
            "independently_verified": False,
        },
        "limitations": [
            "Only normalized event metadata and the latest supplied 1X2 odds are stored; historical odds movement is not retained in this phase.",
            "Odds and event status remain source-supplied and unverified.",
            "This endpoint does not connect to 1xBet or execute the reviewed PHP wrapper.",
        ],
    }


@router.get("/events")
def list_sportsbook_events(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(require_dashboard_access),
):
    query = db.query(SportsbookEvent).filter(SportsbookEvent.provider == "authorized_sportsbook_feed")
    total = query.count()
    events = query.order_by(SportsbookEvent.starts_at.asc().nullslast(), SportsbookEvent.id.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [{
            "event_id": event.event_id,
            "sport": event.sport,
            "league": event.league,
            "home_team": event.home_team,
            "away_team": event.away_team,
            "starts_at": event.starts_at.isoformat() if event.starts_at else None,
            "event_status": event.event_status,
            "odds_1x2": {"home": event.odds_home, "draw": event.odds_draw, "away": event.odds_away},
            "odds_updated_at": event.odds_updated_at.isoformat() if event.odds_updated_at else None,
            "source": event.source,
            "updated_at": event.updated_at.isoformat() if event.updated_at else None,
        } for event in events],
    }


@router.get("/summary")
def sportsbook_summary(db: Session = Depends(get_db), _: None = Depends(require_dashboard_access)):
    query = db.query(SportsbookEvent).filter(SportsbookEvent.provider == "authorized_sportsbook_feed")
    events = query.all()
    return {
        "event_count": len(events),
        "by_status": {status: sum(event.event_status == status for event in events) for status in ("scheduled", "live", "finished", "cancelled")},
        "with_1x2_odds": sum(any(v is not None for v in (event.odds_home, event.odds_draw, event.odds_away)) for event in events),
        "sources": sorted({event.source for event in events}),
        "disclaimer": "Source-supplied sportsbook data is descriptive and unverified; this API does not provide betting advice.",
    }
