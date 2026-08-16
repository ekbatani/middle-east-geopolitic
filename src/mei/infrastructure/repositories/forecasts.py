from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.forecasts.models import ForecastRecord
from mei.shared.enums import ForecastOutcome, ForecastStatus


class ForecastRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, forecast_id: UUID) -> ForecastRecord | None:
        return await self._session.get(ForecastRecord, forecast_id)

    async def list_all(
        self,
        *,
        status: ForecastStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ForecastRecord]:
        stmt = select(ForecastRecord).order_by(ForecastRecord.issued_at.desc())
        if status is not None:
            stmt = stmt.where(ForecastRecord.status == status)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def list_due(self, *, as_of: date) -> list[ForecastRecord]:
        stmt = (
            select(ForecastRecord)
            .where(
                ForecastRecord.status == ForecastStatus.OPEN,
                ForecastRecord.resolution_date <= as_of,
            )
            .order_by(ForecastRecord.resolution_date)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def create(
        self,
        *,
        question: str,
        issued_at: datetime,
        resolution_date: date,
        probability: float,
        confidence: float,
        assumptions: list[str],
        evidence_bundle_id: UUID | None,
    ) -> ForecastRecord:
        forecast = ForecastRecord(
            question=question,
            issued_at=issued_at,
            resolution_date=resolution_date,
            probability=probability,
            confidence=confidence,
            assumptions_json=list(assumptions),
            evidence_bundle_id=evidence_bundle_id,
        )
        self._session.add(forecast)
        await self._session.flush()
        return forecast

    async def resolve(
        self,
        forecast_id: UUID,
        *,
        outcome: ForecastOutcome,
        resolved_at: datetime,
        brier_score: float | None,
        evaluation_note: str | None,
    ) -> ForecastRecord | None:
        forecast = await self.get(forecast_id)
        if forecast is None:
            return None
        forecast.status = ForecastStatus.RESOLVED
        forecast.outcome = outcome
        forecast.resolved_at = resolved_at
        forecast.brier_score = brier_score
        forecast.evaluation_note = evaluation_note
        await self._session.flush()
        return forecast

    async def update(
        self,
        forecast: ForecastRecord,
        *,
        question: str | None = None,
        probability: float | None = None,
        confidence: float | None = None,
        resolution_date: date | None = None,
        status: ForecastStatus | None = None,
    ) -> ForecastRecord:
        if question is not None:
            forecast.question = question
        if probability is not None:
            forecast.probability = probability
        if confidence is not None:
            forecast.confidence = confidence
        if resolution_date is not None:
            forecast.resolution_date = resolution_date
        if status is not None:
            forecast.status = status
        await self._session.flush()
        return forecast

    async def delete(self, forecast: ForecastRecord) -> None:
        await self._session.delete(forecast)
        await self._session.flush()


__all__ = ["ForecastRepository"]

