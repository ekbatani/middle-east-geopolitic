"""Forecast issuance and post-hoc scoring (design doc section 8.9).

Resolution is deliberately a human action (`resolve_forecast`), never
something the scheduler infers on its own: determining whether "the
ceasefire held" or "the leader was incapacitated" actually happened is
exactly the kind of judgment call design doc section 13.4 reserves for a
person, not a model. `evaluate_due_forecasts` (the Celery job) only
surfaces which forecasts are past their resolution date and still open.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.forecasts.models import ForecastRecord
from mei.infrastructure.repositories.forecasts import ForecastRepository
from mei.shared.enums import ForecastOutcome
from mei.shared.errors import NotFoundError
from mei.shared.time import utcnow


def calculate_brier_score(probability: float, outcome: ForecastOutcome) -> float | None:
    """Standard Brier score `(probability - actual)^2`, with `probability`
    on a 0-1 scale. `AMBIGUOUS` outcomes aren't binary, so they close out
    the forecast's status without producing a misleading number, rather
    than forcing a score onto a question that was never cleanly resolved.
    """
    if outcome == ForecastOutcome.AMBIGUOUS:
        return None
    actual = 1.0 if outcome == ForecastOutcome.YES else 0.0
    return (probability - actual) ** 2


class ForecastAuditService:
    def __init__(self, session: AsyncSession) -> None:
        self._forecasts = ForecastRepository(session)

    async def issue_forecast(
        self,
        *,
        question: str,
        resolution_date: date,
        probability: float,
        confidence: float,
        assumptions: list[str] | None = None,
        evidence_bundle_id: UUID | None = None,
    ) -> ForecastRecord:
        return await self._forecasts.create(
            question=question,
            issued_at=utcnow(),
            resolution_date=resolution_date,
            probability=probability,
            confidence=confidence,
            assumptions=assumptions or [],
            evidence_bundle_id=evidence_bundle_id,
        )

    async def list_due(self, *, as_of: date | None = None) -> list[ForecastRecord]:
        return await self._forecasts.list_due(as_of=as_of or utcnow().date())

    async def resolve_forecast(
        self,
        forecast_id: UUID,
        *,
        outcome: ForecastOutcome,
        evaluation_note: str | None = None,
    ) -> ForecastRecord:
        forecast = await self._forecasts.get(forecast_id)
        if forecast is None:
            raise NotFoundError(f"Forecast {forecast_id} not found")

        # `probability` is stored 0-100 (matching every other scored field
        # on this platform); Brier scoring is conventionally 0-1.
        brier_score = calculate_brier_score(forecast.probability / 100, outcome)

        resolved = await self._forecasts.resolve(
            forecast_id,
            outcome=outcome,
            resolved_at=utcnow(),
            brier_score=brier_score,
            evaluation_note=evaluation_note,
        )
        if resolved is None:
            raise NotFoundError(f"Forecast {forecast_id} not found")
        return resolved


__all__ = ["ForecastAuditService", "calculate_brier_score"]
