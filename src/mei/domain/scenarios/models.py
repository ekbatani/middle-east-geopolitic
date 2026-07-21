from datetime import datetime
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from mei.infrastructure.database.base import Base, TimestampMixin
from mei.shared.enums import ScenarioFamily, ScenarioStatus, ScopeType
from mei.shared.ids import uuid7


class Scenario(TimestampMixin, Base):
    """A tracked scenario-family entry for one scope (design doc section 8.8).

    A scope typically carries up to four `Scenario` rows, one per
    `ScenarioFamily` (section 19.1), so the engine can run the "consistency
    checks across scenario probabilities" step (section 19.2 step 6) across
    siblings sharing the same `scope_type`/`scope_id`.
    """

    __tablename__ = "scenarios"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(300))
    scope_type: Mapped[ScopeType] = mapped_column(String(20), index=True)
    scope_id: Mapped[UUID | None] = mapped_column(index=True, default=None)
    scenario_family: Mapped[ScenarioFamily] = mapped_column(String(30), index=True)
    time_horizon: Mapped[str] = mapped_column(String(50))
    status: Mapped[ScenarioStatus] = mapped_column(
        String(20), default=ScenarioStatus.ACTIVE, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, default=None)


class ScenarioAssessment(Base):
    """One point-in-time probability assessment for a scenario (design doc section 8.8).

    Append-only, matching `RiskAssessment`/`RelationshipObservation`: history
    is the full set of rows for a `scenario_id`, never an update to a prior
    one, so the update process's "preserve previous assessment" step
    (section 19.2 step 8) is automatic rather than something the engine has
    to special-case.
    """

    __tablename__ = "scenario_assessments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    scenario_id: Mapped[UUID] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"), index=True
    )
    assessed_at: Mapped[datetime] = mapped_column(index=True)
    probability_low: Mapped[float] = mapped_column(Float)
    probability_high: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    assumptions_json: Mapped[list[object]] = mapped_column(JSONB, default=list)
    trigger_events_json: Mapped[list[object]] = mapped_column(JSONB, default=list)
    leading_indicators_json: Mapped[list[object]] = mapped_column(JSONB, default=list)
    expected_actor_behavior: Mapped[str | None] = mapped_column(Text, default=None)
    military_consequences: Mapped[str | None] = mapped_column(Text, default=None)
    economic_consequences: Mapped[str | None] = mapped_column(Text, default=None)
    humanitarian_consequences: Mapped[str | None] = mapped_column(Text, default=None)
    invalidation_criteria_json: Mapped[list[object]] = mapped_column(JSONB, default=list)
    explanation_of_change: Mapped[str | None] = mapped_column(Text, default=None)
    evidence_bundle_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("evidence_bundles.id", ondelete="SET NULL"), default=None
    )
    model_version: Mapped[str | None] = mapped_column(String(100), default=None)
    approved_by: Mapped[str | None] = mapped_column(String(200), default=None)
    approved_at: Mapped[datetime | None] = mapped_column(default=None)


__all__ = ["Scenario", "ScenarioAssessment"]
