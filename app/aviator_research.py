"""Phase 09 historical research diagnostics over persisted authorized imports.

Outputs are retrospective descriptive diagnostics only. No prediction,
betting recommendation, external connection, or causal inference is produced.
"""
from datetime import timezone
import math
import statistics

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.aviator_access import require_dashboard_access
from app.db import get_db
from app.models import RoundResult

router = APIRouter()
PROVIDER = "aviator_capture"
MAX_SAMPLE = 20_000


def _utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _correlation(left, right):
    if len(left) < 2:
        return None
    mean_left = statistics.fmean(left)
    mean_right = statistics.fmean(right)
    numerator = sum((a - mean_left) * (b - mean_right) for a, b in zip(left, right))
    denominator = math.sqrt(
        sum((a - mean_left) ** 2 for a in left)
        * sum((b - mean_right) ** 2 for b in right)
    )
    return round(numerator / denominator, 6) if denominator else None


def _rate(values, threshold):
    return round(sum(value >= threshold for value in values) / len(values), 6) if values else None


@router.get("/research/overview")
def historical_research_overview(
    limit: int = Query(default=5000, ge=2, le=MAX_SAMPLE),
    db: Session = Depends(get_db),
    _: None = Depends(require_dashboard_access),
):
    """Analyze the latest persisted CSV-imported rounds; never forecast outcomes."""
    rows = (
        db.query(RoundResult)
        .filter(RoundResult.provider == PROVIDER)
        .order_by(RoundResult.occurred_at.asc(), RoundResult.id.asc())
        .limit(limit)
        .all()
    )
    values = [
        float(row.multiplier) for row in rows
        if isinstance(row.multiplier, (int, float))
        and math.isfinite(float(row.multiplier))
        and float(row.multiplier) > 0
    ]
    count = len(values)
    if count < 2:
        return {
            "status": "insufficient_data",
            "mode": "retrospective_descriptive_research_only",
            "provider": PROVIDER,
            "round_count": count,
            "minimum_required": 2,
            "limitations": [
                "At least two valid persisted rounds are required.",
                "This endpoint does not predict future game outcomes.",
            ],
        }

    ordered = sorted(values)
    median = statistics.median(values)
    mean = statistics.fmean(values)
    split = count // 2
    first, second = values[:split], values[split:]
    lag_left, lag_right = values[:-1], values[1:]

    # Runs above/below the sample median: descriptive sequencing diagnostic.
    labels = [value >= median for value in values]
    runs = 1 + sum(labels[index] != labels[index - 1] for index in range(1, count))
    n_above = sum(labels)
    n_below = count - n_above
    runs_z = None
    if n_above and n_below and count > 3:
        expected = 1 + (2 * n_above * n_below / count)
        variance = (
            2 * n_above * n_below * (2 * n_above * n_below - count)
            / (count * count * (count - 1))
        )
        if variance > 0:
            runs_z = round((runs - expected) / math.sqrt(variance), 4)

    timestamps = [_utc(row.occurred_at) for row in rows]
    dated = [item for item in timestamps if item is not None]
    gaps = [
        (dated[index] - dated[index - 1]).total_seconds()
        for index in range(1, len(dated))
    ]
    duplicate_round_ids = count - len({row.round_id for row in rows})
    missing_round_ids = sum(not row.round_id for row in rows)
    missing_source = sum(not row.source for row in rows)
    unverified = sum(row.verification_status != "verified" for row in rows)

    hourly = {}
    for row in rows:
        timestamp = _utc(row.occurred_at)
        if timestamp is not None:
            hourly.setdefault(f"{timestamp.hour:02d}:00", []).append(float(row.multiplier))

    return {
        "status": "analyzed",
        "mode": "retrospective_descriptive_research_only",
        "provider": PROVIDER,
        "round_count": count,
        "sample": {
            "requested_limit": limit,
            "first_event_at": timestamps[0].isoformat() if timestamps and timestamps[0] else None,
            "last_event_at": timestamps[-1].isoformat() if timestamps and timestamps[-1] else None,
            "timestamp_coverage_rate": round(len(dated) / len(rows), 4) if rows else 0,
        },
        "distribution": {
            "minimum": round(min(values), 4),
            "maximum": round(max(values), 4),
            "mean": round(mean, 4),
            "median": round(median, 4),
            "population_stddev": round(statistics.pstdev(values), 4),
            "p05": round(ordered[math.floor((count - 1) * 0.05)], 4),
            "p25": round(statistics.quantiles(values, n=4, method="inclusive")[0], 4) if count >= 2 else None,
            "p75": round(statistics.quantiles(values, n=4, method="inclusive")[2], 4) if count >= 2 else None,
            "p95": round(ordered[math.ceil((count - 1) * 0.95)], 4),
            "rates": {
                "at_least_1_5x": _rate(values, 1.5),
                "at_least_2x": _rate(values, 2),
                "at_least_5x": _rate(values, 5),
                "at_least_10x": _rate(values, 10),
                "at_least_50x": _rate(values, 50),
            },
        },
        "sequence_diagnostics": {
            "lag_1_correlation": _correlation(lag_left, lag_right),
            "median_split_runs": runs,
            "runs_test_z_approx": runs_z,
            "interpretation": "Exploratory diagnostics only; dependence tests do not establish predictability or causal structure.",
        },
        "sample_comparison": {
            "method": "chronological_first_half_vs_second_half",
            "first_half_count": len(first),
            "second_half_count": len(second),
            "first_half_mean": round(statistics.fmean(first), 4) if first else None,
            "second_half_mean": round(statistics.fmean(second), 4) if second else None,
            "first_half_at_least_2x_rate": _rate(first, 2),
            "second_half_at_least_2x_rate": _rate(second, 2),
            "mean_difference_second_minus_first": round(statistics.fmean(second) - statistics.fmean(first), 4) if first and second else None,
        },
        "time_of_day_utc": [
            {
                "hour": hour,
                "sample_count": len(series),
                "median": round(statistics.median(series), 4),
                "at_least_2x_rate": _rate(series, 2),
            }
            for hour, series in sorted(hourly.items())
        ],
        "data_quality": {
            "rows_loaded": len(rows),
            "valid_multiplier_count": count,
            "invalid_or_nonpositive_multiplier_count": len(rows) - count,
            "duplicate_round_ids_in_sample": duplicate_round_ids,
            "missing_round_ids": missing_round_ids,
            "missing_source": missing_source,
            "unverified_rows": unverified,
            "timestamped_rows": len(dated),
            "median_inter_event_gap_seconds": round(statistics.median(gaps), 3) if gaps else None,
            "maximum_inter_event_gap_seconds": round(max(gaps), 3) if gaps else None,
        },
        "limitations": [
            "All metrics describe only persisted requester-supplied historical records.",
            "The sample is not guaranteed complete, random, independent, or representative.",
            "Observed correlations, streaks, time buckets, and half-sample differences are not forecasts.",
            "Small groups and multiple comparisons can produce unstable apparent patterns.",
            "Source authenticity and authorization are not independently verified.",
            "No next-round prediction, betting signal, or guaranteed outcome is generated.",
        ],
    }
