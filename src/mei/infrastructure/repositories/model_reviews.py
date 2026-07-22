from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.model_reviews.models import ModelReviewResult
from mei.shared.enums import ModelReviewSubjectType


class ModelReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, review_id: UUID) -> ModelReviewResult | None:
        return await self._session.get(ModelReviewResult, review_id)

    async def list_all(
        self,
        *,
        subject_type: ModelReviewSubjectType | None = None,
        agreement: bool | None = None,
        since: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ModelReviewResult]:
        stmt = select(ModelReviewResult).order_by(ModelReviewResult.reviewed_at.desc())
        if subject_type is not None:
            stmt = stmt.where(ModelReviewResult.subject_type == subject_type)
        if agreement is not None:
            stmt = stmt.where(ModelReviewResult.agreement == agreement)
        if since is not None:
            stmt = stmt.where(ModelReviewResult.reviewed_at >= since)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def create(
        self,
        *,
        subject_type: ModelReviewSubjectType,
        subject_id: UUID,
        trigger_reason: str,
        primary_model: str,
        secondary_model: str,
        primary_final_score: int,
        secondary_final_score: int,
        agreement: bool | None,
        agreement_delta: int | None,
        secondary_output_json: dict[str, object],
    ) -> ModelReviewResult:
        review = ModelReviewResult(
            subject_type=subject_type,
            subject_id=subject_id,
            trigger_reason=trigger_reason,
            primary_model=primary_model,
            secondary_model=secondary_model,
            primary_final_score=primary_final_score,
            secondary_final_score=secondary_final_score,
            agreement=agreement,
            agreement_delta=agreement_delta,
            secondary_output_json=secondary_output_json,
        )
        self._session.add(review)
        await self._session.flush()
        return review


__all__ = ["ModelReviewRepository"]
