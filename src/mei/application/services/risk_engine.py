"""Deterministic risk calculation with bounded LLM adjustment (design doc section 18).

`RiskEngine.calculate` is the whole of ADR-006 in one place: a reproducible
base score computed purely from stored `indicator_observations` and
`risk_indicator_weights`, plus an optional, range-clamped LLM adjustment
that can never move the score by more than 10 points in either direction.
Calling it twice against the same indicator history (nothing new recorded
in between) always produces the same `base_score` — that reproducibility is
the Phase 3 acceptance criterion in design doc section 35.
"""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict, cast
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.risks.models import RiskAssessment
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.infrastructure.repositories.indicators import IndicatorRepository
from mei.infrastructure.repositories.risks import RiskRepository
from mei.shared.config import get_settings
from mei.shared.enums import IndicatorDirection, RiskApprovalStatus, ScopeType, Trend
from mei.shared.errors import LLMConfigurationError, LLMOutputError, NotFoundError, ValidationError
from mei.shared.logging import get_logger
from mei.shared.time import utcnow

logger = get_logger(__name__)

PROMPT_TASK_NAME = "risk_adjustment"
PROMPT_VERSION = "risk_adjustment_v1"

_TREND_EPSILON = 2  # score points; smaller moves read as "stable" rather than noise.


class RiskAdjustmentRecommendation(BaseModel):
    """Design doc section 18.4, verbatim (minus `base_score`, which the engine computes)."""

    recommended_adjustment: int = Field(ge=-10, le=10)
    rationale: list[str] = Field(default_factory=list)
    counter_indicators: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class ContributionRecord(TypedDict):
    indicator_code: str
    indicator_name: str
    weight: float
    direction: str
    raw_value: float | None
    normalized_value: float | None
    contribution: float | None
    confidence: float | None
    observed_at: str | None
    included: bool
    stale: bool


def _is_stale(observed_at: datetime, *, as_of: datetime, staleness_hours: int | None) -> bool:
    if staleness_hours is None:
        return False
    age_hours = (as_of - observed_at).total_seconds() / 3600
    return age_hours > staleness_hours


def aggregate_contributions(
    contributions: list[ContributionRecord], total_weight: float
) -> tuple[int, float, float]:
    """Pure scoring formula (design doc section 18.1-18.3), independent of the
    database so it can be property-tested directly: given the per-indicator
    breakdown, returns `(base_score, confidence, available_weight)`.

    Missing/stale indicators (`included=False`) are left out of the weighted
    average entirely rather than counted as zero risk, and the resulting gap
    between `available_weight` and `total_weight` scales confidence down
    (section 18.3: "low-confidence observations should reduce assessment
    confidence, not necessarily reduce the risk score itself").
    """
    included = [c for c in contributions if c["included"]]
    available_weight = sum(c["weight"] for c in included)
    if available_weight <= 0:
        return 0, 0.0, 0.0

    weighted_score_sum = 0.0
    weighted_confidence_sum = 0.0
    for record in included:
        contribution = record["contribution"]
        if contribution is not None:
            weighted_score_sum += record["weight"] * contribution
        record_confidence = record["confidence"]
        if record_confidence is not None:
            weighted_confidence_sum += record["weight"] * record_confidence

    base_score = max(0, min(100, round(100 * weighted_score_sum / available_weight)))
    raw_confidence = weighted_confidence_sum / available_weight
    coverage_ratio = available_weight / total_weight if total_weight > 0 else 0.0
    confidence = max(0.0, min(1.0, raw_confidence * coverage_ratio))
    return base_score, confidence, available_weight


class RiskEngine:
    def __init__(self, session: AsyncSession) -> None:
        self._risks = RiskRepository(session)
        self._indicators = IndicatorRepository(session)

    async def calculate(
        self,
        *,
        risk_definition_id: UUID,
        scope_type: ScopeType,
        scope_id: UUID | None,
        as_of: datetime | None = None,
        llm: StructuredLLM | None = None,
        triggered_by: str | None = None,
        persist: bool = True,
    ) -> RiskAssessment:
        definition = await self._risks.get_definition(risk_definition_id)
        if definition is None:
            raise NotFoundError(f"Risk definition {risk_definition_id} not found")
        if scope_type.value not in definition.scope_types:
            raise ValidationError(
                f"Risk '{definition.code}' does not apply to scope type '{scope_type}'"
            )

        weights = await self._risks.list_weights(risk_definition_id)
        if not weights:
            raise ValidationError(f"Risk '{definition.code}' has no indicator weights configured")

        assessed_at = as_of or utcnow()
        contributions: list[ContributionRecord] = []
        total_weight = 0.0

        for weight_row in weights:
            indicator = await self._indicators.get_definition(weight_row.indicator_definition_id)
            if indicator is None:
                continue  # orphaned weight row; skip rather than fail the whole assessment
            total_weight += weight_row.weight

            observation = (
                None
                if scope_id is None
                else await self._indicators.get_latest_observation(
                    indicator_id=indicator.id,
                    scope_type=scope_type,
                    scope_id=scope_id,
                    as_of=assessed_at,
                )
            )

            stale = observation is not None and _is_stale(
                observation.observed_at,
                as_of=assessed_at,
                staleness_hours=indicator.staleness_hours,
            )
            included = observation is not None and not stale

            contribution_fraction: float | None = None
            if included and observation is not None:
                contribution_fraction = (
                    observation.normalized_value
                    if weight_row.direction == IndicatorDirection.POSITIVE
                    else 1.0 - observation.normalized_value
                )

            contributions.append(
                ContributionRecord(
                    indicator_code=indicator.code,
                    indicator_name=indicator.name,
                    weight=weight_row.weight,
                    direction=str(weight_row.direction),
                    raw_value=observation.raw_value if observation else None,
                    normalized_value=observation.normalized_value if observation else None,
                    contribution=contribution_fraction,
                    confidence=observation.confidence if observation else None,
                    observed_at=observation.observed_at.isoformat() if observation else None,
                    included=included,
                    stale=stale,
                )
            )

        base_score, confidence, available_weight = aggregate_contributions(
            contributions, total_weight
        )

        previous = await self._risks.get_latest_assessment(
            risk_definition_id=risk_definition_id, scope_type=scope_type, scope_id=scope_id
        )
        previous_score = previous.final_score if previous is not None else None

        adjustment = 0
        rationale: list[str] = []
        counter_indicators: list[str] = []
        model_version: str | None = None
        if llm is not None:
            (
                adjustment,
                rationale,
                counter_indicators,
                model_version,
            ) = await self._get_llm_adjustment(
                llm,
                definition_code=definition.code,
                scope_type=scope_type,
                scope_id=scope_id,
                base_score=base_score,
                contributions=contributions,
                previous_score=previous_score,
            )

        final_score = max(0, min(100, base_score + adjustment))

        trend: Trend | None = None
        if previous_score is not None:
            delta = final_score - previous_score
            if delta > _TREND_EPSILON:
                trend = Trend.RISING
            elif delta < -_TREND_EPSILON:
                trend = Trend.FALLING
            else:
                trend = Trend.STABLE

        explanation = self._build_explanation(
            base_score=base_score,
            adjustment=adjustment,
            final_score=final_score,
            available_weight=available_weight,
            total_weight=total_weight,
            rationale=rationale,
        )

        now = utcnow()
        # `contributions` is precisely-typed in-process (`ContributionRecord`);
        # the repository's JSONB column is the untyped persistence boundary
        # (`Mapped[list[object]]`), so the cast just marks that crossing
        # rather than changing anything at runtime.
        contributions_json = cast("list[object]", list(contributions))

        if not persist:
            # Multi-model review's shadow mode (design doc section 35,
            # Phase 6): a secondary model reruns the same calculation
            # without writing a competing `RiskAssessment` row or feeding
            # into `previous_score`/trend history. Built directly rather
            # than through `RiskRepository.create_assessment` so nothing
            # touches the session.
            return RiskAssessment(
                risk_definition_id=risk_definition_id,
                scope_type=scope_type,
                scope_id=scope_id,
                assessed_at=assessed_at,
                base_score=base_score,
                llm_adjustment=adjustment,
                final_score=final_score,
                previous_score=previous_score,
                trend=trend,
                confidence=confidence,
                explanation=explanation,
                counter_indicators_json=counter_indicators,
                contributions_json=contributions_json,
                evidence_bundle_id=None,
                ruleset_version=definition.ruleset_version,
                model_version=model_version,
                approval_status=RiskApprovalStatus.APPROVED,
                approved_by=triggered_by or "system",
                approved_at=now,
            )

        assessment = await self._risks.create_assessment(
            risk_definition_id=risk_definition_id,
            scope_type=scope_type,
            scope_id=scope_id,
            assessed_at=assessed_at,
            base_score=base_score,
            llm_adjustment=adjustment,
            final_score=final_score,
            previous_score=previous_score,
            trend=trend,
            confidence=confidence,
            explanation=explanation,
            counter_indicators=counter_indicators,
            contributions=contributions_json,
            evidence_bundle_id=None,
            ruleset_version=definition.ruleset_version,
            model_version=model_version,
            approval_status=RiskApprovalStatus.APPROVED,
            approved_by=triggered_by or "system",
            approved_at=now,
        )
        self._maybe_trigger_multi_model_review(assessment)
        return assessment

    @staticmethod
    def _maybe_trigger_multi_model_review(assessment: RiskAssessment) -> None:
        """Enqueue a second-model shadow review for a large enough score
        move (design doc section 35, Phase 6 "multi-model review").

        Local imports to avoid a circular import: `multi_model_review`
        imports `RiskEngine` for its own shadow rerun, and the Celery task
        module lives downstream of the application layer — the same
        pattern `InvestigationService.create` uses to enqueue
        `run_investigation` without a module-level worker dependency.
        """
        from mei.application.services.multi_model_review import should_trigger_for_risk

        settings = get_settings()
        if not settings.llm_secondary_model:
            return
        trigger_reason = should_trigger_for_risk(
            assessment.final_score,
            assessment.previous_score,
            settings.multi_model_review_score_delta_threshold,
        )
        if trigger_reason is None:
            return

        from apps.worker.tasks.multi_model_review import review_risk_assessment

        review_risk_assessment.delay(str(assessment.id))

    async def _get_llm_adjustment(
        self,
        llm: StructuredLLM,
        *,
        definition_code: str,
        scope_type: ScopeType,
        scope_id: UUID | None,
        base_score: int,
        contributions: list[ContributionRecord],
        previous_score: int | None,
    ) -> tuple[int, list[str], list[str], str | None]:
        settings = get_settings()
        input_text = self._build_llm_input(
            definition_code=definition_code,
            base_score=base_score,
            contributions=contributions,
            previous_score=previous_score,
        )
        try:
            recommendation = await llm.generate_structured(
                task_name=PROMPT_TASK_NAME,
                prompt_version=PROMPT_VERSION,
                input_text=input_text,
                output_model=RiskAdjustmentRecommendation,
                metadata={
                    "risk_definition_code": definition_code,
                    "scope_type": str(scope_type),
                    "scope_id": str(scope_id) if scope_id else "",
                },
            )
        except (LLMConfigurationError, LLMOutputError) as exc:
            logger.warning(
                "risk_engine.llm_adjustment_skipped",
                risk_definition_code=definition_code,
                error=str(exc),
            )
            return 0, [], [], None

        # Defensive clamp per section 18.4 ("the deterministic engine
        # validates the range") even though the Pydantic field already
        # rejects out-of-range values during parsing.
        adjustment = max(-10, min(10, recommendation.recommended_adjustment))
        model_version = f"{settings.llm_provider}:{settings.llm_model}:{PROMPT_VERSION}"
        return (
            adjustment,
            recommendation.rationale,
            recommendation.counter_indicators,
            model_version,
        )

    @staticmethod
    def _build_llm_input(
        *,
        definition_code: str,
        base_score: int,
        contributions: list[ContributionRecord],
        previous_score: int | None,
    ) -> str:
        lines = [
            f"Risk definition: {definition_code}",
            f"Deterministic base score: {base_score}/100",
            f"Previous final score: {previous_score if previous_score is not None else 'none recorded'}",
            "Indicator contributions:",
        ]
        for record in contributions:
            if not record["included"]:
                status = "stale" if record["stale"] else "no observation"
                lines.append(f"- {record['indicator_code']} ({record['indicator_name']}): {status}")
                continue
            lines.append(
                f"- {record['indicator_code']} ({record['indicator_name']}): "
                f"normalized={record['normalized_value']:.2f}, weight={record['weight']:.2f}, "
                f"direction={record['direction']}, confidence={record['confidence']:.2f}"
            )
        return "\n".join(lines)

    @staticmethod
    def _build_explanation(
        *,
        base_score: int,
        adjustment: int,
        final_score: int,
        available_weight: float,
        total_weight: float,
        rationale: list[str],
    ) -> str:
        coverage_pct = round(100 * available_weight / total_weight) if total_weight > 0 else 0
        parts = [
            f"Deterministic base score {base_score}/100 from {coverage_pct}% of configured "
            "indicator weight."
        ]
        if adjustment:
            parts.append(
                f"LLM-recommended adjustment of {adjustment:+d} applied, final {final_score}/100."
            )
        if rationale:
            parts.append(" ".join(rationale))
        return " ".join(parts)


def _as_float(value: object) -> float | None:
    return float(value) if isinstance(value, int | float) else None


def _field(record: object, key: str) -> object:
    """Read one field out of a `contributions_json` entry.

    Entries round-trip through JSONB as plain `dict`s (typed `object` by the
    ORM's `Mapped[list[object]]`, since JSONB content is opaque to
    SQLAlchemy), so this is a defensive `dict.get` rather than a typed
    `TypedDict` access.
    """
    return record.get(key) if isinstance(record, dict) else None


def diff_changed_indicators(
    previous: list[object] | None,
    current: list[object],
    *,
    epsilon: float = 0.05,
) -> list[str]:
    """Indicator codes whose normalized value moved by more than `epsilon`
    between two assessments' stored `contributions_json` (design doc section
    18.5, "changed indicators"). Read-time diff, not a stored column, so it
    always reflects the two specific assessments being compared."""
    if not previous:
        return [
            str(_field(record, "indicator_code")) for record in current if _field(record, "included")
        ]

    previous_by_code: dict[str, object] = {}
    for record in previous:
        code = _field(record, "indicator_code")
        if code is not None:
            previous_by_code[str(code)] = record

    changed: list[str] = []
    for record in current:
        code_obj = _field(record, "indicator_code")
        if code_obj is None:
            continue
        code = str(code_obj)
        prior_record = previous_by_code.get(code)
        current_value = _as_float(_field(record, "normalized_value"))
        prior_value = _as_float(_field(prior_record, "normalized_value")) if prior_record else None
        if current_value is None or prior_value is None:
            if current_value != prior_value:
                changed.append(code)
            continue
        if abs(current_value - prior_value) > epsilon:
            changed.append(code)
    return changed


__all__ = [
    "ContributionRecord",
    "RiskAdjustmentRecommendation",
    "RiskEngine",
    "aggregate_contributions",
    "diff_changed_indicators",
]
