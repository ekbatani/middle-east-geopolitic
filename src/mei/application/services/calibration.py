"""Forecast calibration reporting (design doc section 35, Phase 6 "calibration dashboards").

Reliability/calibration for a set of resolved forecasts: how well the
issued `probability` matched the actual outcome frequency, bucketed the
way a standard reliability diagram is (see e.g. Brier's original 1950
paper) — forecasts issued around "70% likely" should resolve `YES` about
70% of the time if the platform's forecasting is well-calibrated.
"""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.forecasts.models import ForecastRecord
from mei.infrastructure.repositories.forecasts import ForecastRepository
from mei.shared.enums import ForecastOutcome, ForecastStatus

_SCORABLE_OUTCOMES = (ForecastOutcome.YES, ForecastOutcome.NO)


class ForecastSample(TypedDict):
    probability: float  # 0-100, matches `ForecastRecord.probability`
    outcome: ForecastOutcome | None
    brier_score: float | None


class CalibrationBucket(TypedDict):
    lower: float  # 0-1
    upper: float  # 0-1
    forecast_count: int
    mean_predicted_probability: float | None
    observed_frequency: float | None
    mean_brier_score: float | None


class CalibrationReport(TypedDict):
    overall_brier_score: float | None
    resolved_count: int
    open_count: int
    buckets: list[CalibrationBucket]


def bucket_forecasts(
    samples: list[ForecastSample], bucket_count: int = 10
) -> list[CalibrationBucket]:
    """Partition `[0, 1]` into `bucket_count` equal-width buckets and place
    each resolved, binary-outcome forecast into the one its predicted
    probability falls in.

    Pure and DB-free so it's directly unit-testable. Always returns
    exactly `bucket_count` buckets — an empty `samples` list still
    produces the full set of (empty) buckets rather than an empty list,
    so a caller can render a complete reliability diagram either way.
    """
    if bucket_count < 1:
        raise ValueError("bucket_count must be at least 1")

    width = 1.0 / bucket_count
    grouped: list[list[ForecastSample]] = [[] for _ in range(bucket_count)]
    for sample in samples:
        fraction = sample["probability"] / 100
        index = min(max(int(fraction * bucket_count), 0), bucket_count - 1)
        grouped[index].append(sample)

    buckets: list[CalibrationBucket] = []
    for index, group in enumerate(grouped):
        if not group:
            buckets.append(
                CalibrationBucket(
                    lower=index * width,
                    upper=(index + 1) * width,
                    forecast_count=0,
                    mean_predicted_probability=None,
                    observed_frequency=None,
                    mean_brier_score=None,
                )
            )
            continue

        probabilities = [s["probability"] / 100 for s in group]
        outcomes = [1.0 if s["outcome"] == ForecastOutcome.YES else 0.0 for s in group]
        brier_scores = [s["brier_score"] for s in group if s["brier_score"] is not None]
        buckets.append(
            CalibrationBucket(
                lower=index * width,
                upper=(index + 1) * width,
                forecast_count=len(group),
                mean_predicted_probability=sum(probabilities) / len(probabilities),
                observed_frequency=sum(outcomes) / len(outcomes),
                mean_brier_score=(sum(brier_scores) / len(brier_scores)) if brier_scores else None,
            )
        )
    return buckets


def _issued_between(
    forecast: ForecastRecord, since: datetime | None, until: datetime | None
) -> bool:
    if since is not None and forecast.issued_at < since:
        return False
    return not (until is not None and forecast.issued_at > until)


class CalibrationService:
    def __init__(self, session: AsyncSession) -> None:
        self._forecasts = ForecastRepository(session)

    async def compute_reliability(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        bucket_count: int = 10,
    ) -> CalibrationReport:
        resolved = await self._forecasts.list_all(status=ForecastStatus.RESOLVED, limit=100_000)
        open_forecasts = await self._forecasts.list_all(status=ForecastStatus.OPEN, limit=100_000)

        if since is not None or until is not None:
            resolved = [f for f in resolved if _issued_between(f, since, until)]
            open_forecasts = [f for f in open_forecasts if _issued_between(f, since, until)]

        scorable = [f for f in resolved if f.outcome in _SCORABLE_OUTCOMES]
        samples = [
            ForecastSample(probability=f.probability, outcome=f.outcome, brier_score=f.brier_score)
            for f in scorable
        ]
        buckets = bucket_forecasts(samples, bucket_count)

        brier_scores = [f.brier_score for f in scorable if f.brier_score is not None]
        overall_brier_score = sum(brier_scores) / len(brier_scores) if brier_scores else None

        return CalibrationReport(
            overall_brier_score=overall_brier_score,
            resolved_count=len(resolved),
            open_count=len(open_forecasts),
            buckets=buckets,
        )


__all__ = [
    "CalibrationBucket",
    "CalibrationReport",
    "CalibrationService",
    "ForecastSample",
    "bucket_forecasts",
]
