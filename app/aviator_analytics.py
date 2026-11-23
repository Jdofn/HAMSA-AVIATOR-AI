"""Descriptive analytics for user-authorized Aviator round exports.

Reports historical distributions only. It does not predict future rounds,
generate betting signals, or connect to third-party services.
"""
import math
import statistics
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

router = APIRouter()
MAX_ROUNDS = 10_000


class RoundSourceMetrics(BaseModel):
    players: Optional[float] = Field(default=None, ge=0)
    bets: Optional[float] = Field(default=None, ge=0)
    prize: Optional[float] = Field(default=None, ge=0)

    @field_validator("players", "bets", "prize")
    @classmethod
    def finite_metric(cls, value):
        if value is not None and not math.isfinite(value):
            raise ValueError("source metrics must be finite")
        return value


class RoundSample(BaseModel):
    multiplier: float = Field(gt=0, le=1_000_000)
    round_reference: Optional[str] = Field(default=None, max_length=128)
    occurred_at: Optional[str] = Field(default=None, max_length=64)
    players: Optional[float] = Field(default=None, ge=0)
    bets: Optional[float] = Field(default=None, ge=0)
    prize: Optional[float] = Field(default=None, ge=0)
    source_metrics: Optional[RoundSourceMetrics] = None

    @field_validator("multiplier", "players", "bets", "prize")
    @classmethod
    def finite_numbers(cls, value):
        if value is not None and not math.isfinite(value):
            raise ValueError("numeric values must be finite")
        return value


class AviatorAnalyzeRequest(BaseModel):
    rounds: list[RoundSample] = Field(min_length=1, max_length=MAX_ROUNDS)
    source: str = Field(min_length=3, max_length=300)
    authorization_basis: str = Field(min_length=5, max_length=500)


def _streak(values: list[float], predicate) -> int:
    best = current = 0
    for value in values:
        if predicate(value):
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


@router.post("/analyze")
async def analyze_aviator_history(request: AviatorAnalyzeRequest):
    values = [round_.multiplier for round_ in request.rounds]
    ordered = sorted(values)
    count = len(values)

    def percentile(p: float) -> float:
        position = (count - 1) * p
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return round(ordered[lower], 4)
        weight = position - lower
        return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 4)

    metrics = {"players": [], "bets": [], "prize": []}
    for sample in request.rounds:
        for name in metrics:
            value = getattr(sample, name)
            if value is None and sample.source_metrics is not None:
                value = getattr(sample.source_metrics, name)
            if value is not None:
                metrics[name].append(value)

    optional_summary = {}
    for name, series in metrics.items():
        if series:
            optional_summary[name] = {
                "samples": len(series),
                "average": round(statistics.fmean(series), 4),
                "total": round(sum(series), 4),
            }

    distribution = {
        "below_1_20x": sum(v < 1.2 for v in values),
        "1_20x_to_1_99x": sum(1.2 <= v < 2 for v in values),
        "2x_to_4_99x": sum(2 <= v < 5 for v in values),
        "5x_to_9_99x": sum(5 <= v < 10 for v in values),
        "10x_and_above": sum(v >= 10 for v in values),
    }

    return {
        "status": "analyzed",
        "mode": "historical_descriptive_only",
        "round_count": count,
        "multipliers": {
            "minimum": round(min(values), 4),
            "maximum": round(max(values), 4),
            "mean": round(statistics.fmean(values), 4),
            "median": round(statistics.median(values), 4),
            "population_stddev": round(statistics.pstdev(values), 4),
            "percentiles": {
                "p25": percentile(0.25), "p50": percentile(0.50),
                "p75": percentile(0.75), "p90": percentile(0.90),
            },
        },
        "thresholds": {
            "at_least_2x": {"count": sum(v >= 2 for v in values), "rate": round(sum(v >= 2 for v in values) / count, 4)},
            "at_least_5x": {"count": sum(v >= 5 for v in values), "rate": round(sum(v >= 5 for v in values) / count, 4)},
            "at_least_10x": {"count": sum(v >= 10 for v in values), "rate": round(sum(v >= 10 for v in values) / count, 4)},
        },
        "distribution": distribution,
        "streaks": {
            "max_consecutive_below_2x": _streak(values, lambda v: v < 2),
            "max_consecutive_at_least_2x": _streak(values, lambda v: v >= 2),
        },
        "recent_10_mean": round(statistics.fmean(values[-10:]), 4),
        "source_metrics": optional_summary,
        "provenance": {
            "source": request.source,
            "authorization_basis": request.authorization_basis,
            "provided_by_requester": True,
            "independently_verified": False,
        },
        "limitations": [
            "Statistics describe only the supplied historical sample.",
            "Historical frequencies and streaks do not predict future Aviator rounds.",
            "No betting recommendation, next-round prediction, or guaranteed outcome is produced.",
            "Source and authorization claims are requester-supplied and not independently verified.",
        ],
    }
