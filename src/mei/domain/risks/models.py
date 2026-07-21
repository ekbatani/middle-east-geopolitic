from datetime import datetime
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from mei.infrastructure.database.base import Base
from mei.shared.enums import IndicatorDirection, RiskApprovalStatus, ScopeType, Trend
from mei.shared.ids import uuid7


class RiskDefinition(Base):
    __tablename__ = "risk_definitions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(1000), default=None)
    scope_types: Mapped[list[str]] = mapped_column(ARRAY(String(20)), default=list)
    ruleset_version: Mapped[str] = mapped_column(String(50), default="v1")


class RiskIndicatorWeight(Base):
    """One indicator's contribution to one risk definition's deterministic base score.

    `direction` (design doc section 8.7) decides whether a higher normalized
    reading pushes the score up (`positive`, e.g. attack frequency) or down
    (`inverse`, e.g. diplomatic-channel openness). `conditions_json` is
    reserved for future conditional weighting (design doc's
    `conditions_json` column) but unused by the Phase 3 engine, which
    applies every active weight unconditionally.
    """

    __tablename__ = "risk_indicator_weights"

    risk_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("risk_definitions.id", ondelete="CASCADE"), primary_key=True
    )
    indicator_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("indicator_definitions.id", ondelete="CASCADE"), primary_key=True
    )
    weight: Mapped[float] = mapped_column(Float)
    direction: Mapped[IndicatorDirection] = mapped_column(
        String(10), default=IndicatorDirection.POSITIVE
    )
    conditions_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)


class RiskAssessment(Base):
    """One computed score for one risk definition at one scope (design doc section 18).

    `contributions_json` is a Phase-3 addition beyond the doc's literal
    column list: a snapshot of the per-indicator breakdown used to compute
    `base_score` (indicator code, raw/normalized value, weight, direction,
    confidence, observed_at), so the explanation API in section 18.5 can
    expose "changed indicators; evidence; counter-indicators" without
    recomputing against indicator history that may have moved on since.
    """

    __tablename__ = "risk_assessments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    risk_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("risk_definitions.id", ondelete="CASCADE"), index=True
    )
    scope_type: Mapped[ScopeType] = mapped_column(String(20), index=True)
    scope_id: Mapped[UUID | None] = mapped_column(index=True, default=None)
    assessed_at: Mapped[datetime] = mapped_column(index=True)
    base_score: Mapped[int] = mapped_column(Integer)
    llm_adjustment: Mapped[int] = mapped_column(Integer, default=0)
    final_score: Mapped[int] = mapped_column(Integer)
    previous_score: Mapped[int | None] = mapped_column(Integer, default=None)
    trend: Mapped[Trend | None] = mapped_column(String(10), default=None)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    explanation: Mapped[str | None] = mapped_column(String(4000), default=None)
    counter_indicators_json: Mapped[list[object]] = mapped_column(JSONB, default=list)
    contributions_json: Mapped[list[object]] = mapped_column(JSONB, default=list)
    evidence_bundle_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("evidence_bundles.id", ondelete="SET NULL"), default=None
    )
    ruleset_version: Mapped[str] = mapped_column(String(50), default="v1")
    model_version: Mapped[str | None] = mapped_column(String(100), default=None)
    approval_status: Mapped[RiskApprovalStatus] = mapped_column(
        String(20), default=RiskApprovalStatus.APPROVED
    )
    approved_by: Mapped[str | None] = mapped_column(String(200), default=None)
    approved_at: Mapped[datetime | None] = mapped_column(default=None)


__all__ = ["RiskAssessment", "RiskDefinition", "RiskIndicatorWeight"]
