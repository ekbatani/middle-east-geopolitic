"""Analyst disagreement recording and surfacing (design doc section 35, Phase 6).

Distinct from the Phase 2 review queue (`mei.application.services.review`):
a review item is a pipeline-generated ambiguous decision waiting for one
resolution, this lets multiple analysts each record an independent,
durable position on the same claim/event/risk assessment/relationship
observation, and surfaces where those positions actually conflict rather
than silently collapsing them into one "current" answer.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.analyst_assessments.models import AnalystAssessment
from mei.infrastructure.repositories.analyst_assessments import AnalystAssessmentRepository
from mei.shared.enums import DisagreementSubjectType

DEFAULT_SCORE_SPREAD_THRESHOLD = 20.0


def classify_disagreement(
    stances: list[str | None],
    scores: list[float | None],
    *,
    score_threshold: float = DEFAULT_SCORE_SPREAD_THRESHOLD,
) -> bool:
    """Whether a set of analyst positions on one subject counts as
    disagreement: two or more distinct (non-`None`) stances, or a numeric
    `score` spread at or above `score_threshold`. Pure and DB-free so it's
    directly unit-testable.
    """
    distinct_stances = {s for s in stances if s is not None}
    if len(distinct_stances) >= 2:
        return True

    available_scores = [s for s in scores if s is not None]
    if len(available_scores) < 2:
        return False
    return (max(available_scores) - min(available_scores)) >= score_threshold


class AnalystDisagreementService:
    def __init__(self, session: AsyncSession) -> None:
        self._assessments = AnalystAssessmentRepository(session)

    async def record_position(
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
        return await self._assessments.upsert_position(
            subject_type=subject_type,
            subject_id=subject_id,
            analyst_user_id=analyst_user_id,
            stance=stance,
            score=score,
            confidence=confidence,
            rationale=rationale,
            evidence_bundle_id=evidence_bundle_id,
        )

    async def list_positions(
        self, *, subject_type: DisagreementSubjectType, subject_id: UUID
    ) -> list[AnalystAssessment]:
        return await self._assessments.list_positions(
            subject_type=subject_type, subject_id=subject_id
        )

    async def list_disagreements(
        self,
        *,
        subject_type: DisagreementSubjectType | None = None,
        score_spread_threshold: float = DEFAULT_SCORE_SPREAD_THRESHOLD,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[DisagreementSubjectType, UUID, int, int, float | None]]:
        return await self._assessments.list_disagreements(
            subject_type=subject_type,
            score_spread_threshold=score_spread_threshold,
            limit=limit,
            offset=offset,
        )


__all__ = ["AnalystDisagreementService", "classify_disagreement"]
