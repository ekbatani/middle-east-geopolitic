from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.analyst_assessments.models import AnalystAssessment
from mei.shared.enums import DisagreementSubjectType


class AnalystAssessmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, assessment_id: UUID) -> AnalystAssessment | None:
        return await self._session.get(AnalystAssessment, assessment_id)

    async def upsert_position(
        self,
        *,
        subject_type: DisagreementSubjectType,
        subject_id: UUID,
        analyst_user_id: UUID | None,
        stance: str | None,
        score: float | None,
        confidence: float | None,
        rationale: str | None,
        evidence_bundle_id: UUID | None,
    ) -> AnalystAssessment:
        """One analyst's position per subject: a second call from the same
        analyst on the same subject revises their existing row rather than
        adding a competing one, while a different analyst's row is
        untouched (the unique constraint is `(subject_type, subject_id,
        analyst_user_id)`)."""
        stmt = select(AnalystAssessment).where(
            AnalystAssessment.subject_type == subject_type,
            AnalystAssessment.subject_id == subject_id,
            AnalystAssessment.analyst_user_id == analyst_user_id,
        )
        result = await self._session.execute(stmt)
        existing = result.scalars().first()

        if existing is not None:
            existing.stance = stance
            existing.score = score
            existing.confidence = confidence
            existing.rationale = rationale
            existing.evidence_bundle_id = evidence_bundle_id
            await self._session.flush()
            return existing

        assessment = AnalystAssessment(
            subject_type=subject_type,
            subject_id=subject_id,
            analyst_user_id=analyst_user_id,
            stance=stance,
            score=score,
            confidence=confidence,
            rationale=rationale,
            evidence_bundle_id=evidence_bundle_id,
        )
        self._session.add(assessment)
        await self._session.flush()
        return assessment

    async def list_positions(
        self, *, subject_type: DisagreementSubjectType, subject_id: UUID
    ) -> list[AnalystAssessment]:
        stmt = (
            select(AnalystAssessment)
            .where(
                AnalystAssessment.subject_type == subject_type,
                AnalystAssessment.subject_id == subject_id,
            )
            .order_by(AnalystAssessment.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def list_disagreements(
        self,
        *,
        subject_type: DisagreementSubjectType | None = None,
        score_spread_threshold: float = 20.0,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[DisagreementSubjectType, UUID, int, int, float | None]]:
        """Subjects with more than one distinct `stance` among their
        recorded positions, or whose `score`s spread by at least
        `score_spread_threshold`. Returns
        `(subject_type, subject_id, position_count, distinct_stances, score_spread)`
        tuples rather than loaded `AnalystAssessment` rows — callers that
        need the individual positions call `list_positions` per subject.
        """
        score_spread = func.max(AnalystAssessment.score) - func.min(AnalystAssessment.score)
        stmt = (
            select(
                AnalystAssessment.subject_type,
                AnalystAssessment.subject_id,
                func.count(AnalystAssessment.id).label("position_count"),
                func.count(func.distinct(AnalystAssessment.stance)).label("distinct_stances"),
                score_spread.label("score_spread"),
            )
            .group_by(AnalystAssessment.subject_type, AnalystAssessment.subject_id)
            .having(
                (func.count(func.distinct(AnalystAssessment.stance)) >= 2)
                | (score_spread >= score_spread_threshold)
            )
            .order_by(score_spread.desc().nulls_last())
            .limit(limit)
            .offset(offset)
        )
        if subject_type is not None:
            stmt = stmt.where(AnalystAssessment.subject_type == subject_type)
        result = await self._session.execute(stmt)
        return [tuple(row) for row in result.all()]


__all__ = ["AnalystAssessmentRepository"]
