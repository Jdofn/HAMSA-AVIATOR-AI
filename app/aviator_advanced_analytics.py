"""Advanced descriptive distribution, volatility, and time-pattern analytics.

This module analyzes caller-supplied historical round samples only. It does not
connect to a bookmaker, estimate future outcomes, or generate betting signals.
"""
from datetime import datetime, timezone
import math
import statistics
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

router = APIRouter()
MAX_ROUNDS = 10_000


class AdvancedRoundSample(BaseModel):
    multiplier: float = Field(gt=0, le=1_000_000)
    occurred_at: Optional[datetime] = None

    @field_validator("multiplier")
    @classmethod
    def finite_multiplier(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("multiplier must be finite")
        return value

    @field_validator("occurred_at")
    @classmethod
    def require_timezone_when_present(cls, value):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("occurred_at must include a timezone offset")
        return value


class AdvancedAnalyzeRequest(BaseModel):
    rounds: list[AdvancedRoundSample] = Field(min_length=2, max_length=MAX_ROUNDS)
    source: str = Field(min_length=3, max_length=300)
    authorization_basis: str = Field(min_length=5, max_length=500)
    rolling_window: int = Field(default=20, ge=2, le=500)


def _percentile(sorted_values: list[float], p: float) -> float:
    n = len(sorted_values)
    position = (n - 1) * p
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return round(sorted_values[lower], 4)
    weight = position - lower
    return round(sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight, 4)


@router.post("/advanced-analyze")
async def advanced_analyze_aviator_history(request: AdvancedAnalyzeRequest):
    values = [sample.multiplier for sample in request.rounds]
    ordered = sorted(values)
    count = len(values)
    mean = statistics.fmean(values)
    stddev = statistics.pstdev(values)
    p25, median, p75 = (_percentile(ordered, p) for p in (0.25, 0.50, 0.75))
    iqr = p75 - p25

    rolling = []
    window = request.rolling_window
    if count >= window:
        for end in range(window, count + 1):
            chunk = values[end - window:end]
            rolling.append({
                "end_round_index": end,
                "mean": round(statistics.fmean(chunk), 4),
                "population_stddev": round(statistics.pstdev(chunk), 4),
                "coefficient_of_variation": round(
                    statistics.pstdev(chunk) / statistics.fmean(chunk), 4
                ) if statistics.fmean(chunk) else None,
            })

    hourly: dict[str, list[float]] = defaultdict(list)
    timestamped = 0
    for sample in request.rounds:
        if sample.occurred_at is not None:
            timestamp = sample.occurred_at.astimezone(timezone.utc)
            hourly[f"{timestamp.hour:02d}:00"].append(sample.multiplier)
            timestamped += 1

    time_of_day = [
        {
            "utc_hour": hour,
            "sample_count": len(series),
            "mean": round(statistics.fmean(series), 4),
            "median": round(statistics.median(series), 4),
            "population_stddev": round(statistics.pstdev(series), 4),
            "at_least_2x_rate": round(sum(v >= 2 for v in series) / len(series), 4),
            "at_least_10x_rate": round(sum(v >= 10 for v in series) / len(series), 4),
        }
        for hour, series in sorted(hourly.items())
    ]

    lower_fence, upper_fence = p25 - 1.5 * iqr, p75 + 1.5 * iqr
    outlier_count = sum(v < lower_fence or v > upper_fence for v in values)
    return {
        "status": "analyzed",
        "mode": "historical_distribution_volatility_only",
        "round_count": count,
        "distribution": {
            "minimum": round(min(values), 4),
            "maximum": round(max(values), 4),
            "mean": round(mean, 4),
            "median": round(median, 4),
            "population_stddev": round(stddev, 4),
            "coefficient_of_variation": round(stddev / mean, 4) if mean else None,
            "percentiles": {
                "p05": _percentile(ordered, 0.05),
                "p10": _percentile(ordered, 0.10),
                "p25": p25,
                "p50": median,
                "p75": p75,
                "p90": _percentile(ordered, 0.90),
                "p95": _percentile(ordered, 0.95),
                "p99": _percentile(ordered, 0.99),
            },
            "interquartile_range": round(iqr, 4),
            "iqr_outlier_count": outlier_count,
            "iqr_outlier_rate": round(outlier_count / count, 4),
        },
        "threshold_rates": {
            "at_least_1_5x": round(sum(v >= 1.5 for v in values) / count, 4),
            "at_least_2x": round(sum(v >= 2 for v in values) / count, 4),
            "at_least_5x": round(sum(v >= 5 for v in values) / count, 4),
            "at_least_10x": round(sum(v >= 10 for v in values) / count, 4),
            "at_least_50x": round(sum(v >= 50 for v in values) / count, 4),
        },
        "rolling_volatility": {
            "window_size": window,
            "window_count": len(rolling),
            "latest_window": rolling[-1] if rolling else None,
            "maximum_window_stddev": max((item["population_stddev"] for item in rolling), default=None),
            "minimum_window_stddev": min((item["population_stddev"] for item in rolling), default=None),
            "series": rolling,
        },
        "time_of_day_utc": {
            "timestamped_rounds": timestamped,
            "untimestamped_rounds": count - timestamped,
            "hourly_groups": time_of_day,
            "note": "UTC grouping is descriptive; sample size and source timestamp quality affect interpretation.",
        },
        "provenance": {
            "source": request.source,
            "authorization_basis": request.authorization_basis,
            "provided_by_requester": True,
            "independently_verified": False,
        },
        "limitations": [
            "All outputs describe only the supplied historical sample.",
            "Rolling dispersion and time-of-day differences are descriptive, not predictive.",
            "IQR outliers are statistical flags, not evidence of fraud or a future event.",
            "No next-round prediction, betting signal, or guaranteed outcome is produced.",
            "Source authenticity and authorization claims are not independently verified.",
        ],
    }
