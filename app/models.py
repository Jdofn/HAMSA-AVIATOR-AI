from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class RoundResult(Base):
    __tablename__ = "round_results"
    __table_args__ = (UniqueConstraint("provider", "round_id", name="uq_provider_round"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    round_id: Mapped[str] = mapped_column(String(128))
    multiplier: Mapped[float] = mapped_column(Float)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    verification_status: Mapped[str] = mapped_column(String(32), default="unverified")
    time_of_day: Mapped[str | None] = mapped_column(String(5), nullable=True)
    players: Mapped[float | None] = mapped_column(Float, nullable=True)
    bets: Mapped[float | None] = mapped_column(Float, nullable=True)
    prize: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str | None] = mapped_column(String(300), nullable=True)
    source_file: Mapped[str | None] = mapped_column(String(180), nullable=True)
    import_batch_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )



class SportsbookEvent(Base):
    """Normalized sportsbook fixture with the latest supplied 1X2 odds snapshot."""
    __tablename__ = "sportsbook_events"
    __table_args__ = (
        UniqueConstraint("provider", "event_id", name="uq_sportsbook_provider_event"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    event_id: Mapped[str] = mapped_column(String(128), index=True)
    sport: Mapped[str] = mapped_column(String(120), index=True)
    league: Mapped[str | None] = mapped_column(String(180), nullable=True)
    home_team: Mapped[str] = mapped_column(String(180))
    away_team: Mapped[str] = mapped_column(String(180))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    event_status: Mapped[str] = mapped_column(String(24), default="scheduled")
    odds_home: Mapped[float | None] = mapped_column(Float, nullable=True)
    odds_draw: Mapped[float | None] = mapped_column(Float, nullable=True)
    odds_away: Mapped[float | None] = mapped_column(Float, nullable=True)
    odds_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(300))
    authorization_basis: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
