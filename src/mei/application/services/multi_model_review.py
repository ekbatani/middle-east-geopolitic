"""Multi-model review of high-impact risk assessments (design doc section 35, Phase 6).

Scoped deliberately to `RiskAssessment` score deltas: a `RiskAssessment`
already has a single well-defined numeric output (`final_score`), so a
"second opinion" is a shadow rerun of `RiskEngine.calculate` with a second
configured model (`persist=False`, so it never writes a competing
assessment row or perturbs trend/previous-score history) and a comparison
of the two final scores. High-impact *events* are routed into the
existing Phase 2 review queue instead (see `ReviewType.HIGH_IMPACT_EVENT`
in `mei.application.services.review`) rather than duplicating this
mechanism for extraction, which has no single scalar output to diff.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.application.services.risk_engine import RiskEngine
from mei.domain.model_reviews.models import ModelReviewResult
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.infrastructure.repositories.model_reviews import ModelReviewRepository
from mei.infrastructure.repositories.risks import RiskRepository
from mei.shared.enums import ModelReviewSubjectType
from mei.shared.errors import NotFoundError

_SCORE_DELTA_REASON = "score_delta"


def should_trigger_for_risk(
    final_score: int, previous_score: int | None, threshold: int
) -> str | None:
    """The trigger reason if this risk assessment warrants a second-model
    shadow review, else `None`. A first-ever assessment (no `previous_score`)
    has nothing to diff against, so it never triggers on its own — only a
    move of at least `threshold` points from the prior assessment does.
    Pure and DB-free so it's directly unit-testable.
    """
    if previous_score is None:
        return None
    if abs(final_score - previous_score) >= threshold:
        return _SCORE_DELTA_REASON
    return None


def classify_agreement(primary_score: int, secondary_score: int, tolerance: int) -> bool:
    """Whether the primary and secondary models' final scores agree within
    `tolerance` points. Pure and DB-free."""
    return abs(primary_score - secondary_score) <= tolerance


class MultiModelReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self._risks = RiskRepository(session)
        self._reviews = ModelReviewRepository(session)
        self._risk_engine = RiskEngine(session)

    async def review_risk_assessment(
        self,
        assessment_id: UUID,
        *,
        secondary_llm: StructuredLLM,
        agreement_tolerance: int,
    ) -> ModelReviewResult:
        primary = await self._risks.get_assessment(assessment_id)
        if primary is None:
            raise NotFoundError(f"Risk assessment {assessment_id} not found")

        secondary = await self._risk_engine.calculate(
            risk_definition_id=primary.risk_definition_id,
            scope_type=primary.scope_type,
            scope_id=primary.scope_id,
            as_of=primary.assessed_at,
            llm=secondary_llm,
            triggered_by="multi_model_review",
            persist=False,
        )

        agreement = classify_agreement(
            primary.final_score, secondary.final_score, agreement_tolerance
        )
        agreement_delta = abs(primary.final_score - secondary.final_score)

        return await self._reviews.create(
            subject_type=ModelReviewSubjectType.RISK_ASSESSMENT,
            subject_id=primary.id,
            trigger_reason=_SCORE_DELTA_REASON,
            primary_model=primary.model_version or "deterministic",
            secondary_model=secondary.model_version or "deterministic",
            primary_final_score=primary.final_score,
            secondary_final_score=secondary.final_score,
            agreement=agreement,
            agreement_delta=agreement_delta,
            secondary_output_json={
                "explanation": secondary.explanation,
                "contributions": secondary.contributions_json,
                "counter_indicators": secondary.counter_indicators_json,
            },
        )


__all__ = ["MultiModelReviewService", "classify_agreement", "should_trigger_for_risk"]
