from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from mei.infrastructure.database.base import Base, TimestampMixin
from mei.shared.enums import RelationshipDirectionality, RelationshipStatus, Trend
from mei.shared.ids import uuid7


class Relationship(TimestampMixin, Base):
    __tablename__ = "relationships"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    source_actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("actors.id", ondelete="CASCADE"), index=True
    )
    target_actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("actors.id", ondelete="CASCADE"), index=True
    )
    relationship_type: Mapped[str] = mapped_column(String(50), index=True)
    directionality: Mapped[RelationshipDirectionality] = mapped_column(
        String(20), default=RelationshipDirectionality.SYMMETRIC
    )
    valid_from: Mapped[date | None] = mapped_column(default=None)
    valid_to: Mapped[date | None] = mapped_column(default=None)
    status: Mapped[RelationshipStatus] = mapped_column(
        String(20), default=RelationshipStatus.ACTIVE
    )


class RelationshipObservation(Base):
    """One point-in-time scoring of a relationship across its dimensions.

    Append-only: history is the full set of rows for a `relationship_id`,
    never an update to a prior one, so `GET .../history` can answer
    "what did we believe as of date X" (design doc section 21.4 `as_of`).
    """

    __tablename__ = "relationship_observations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    relationship_id: Mapped[UUID] = mapped_column(
        ForeignKey("relationships.id", ondelete="CASCADE"), index=True
    )
    observed_at: Mapped[datetime] = mapped_column(index=True)
    diplomatic_score: Mapped[int | None] = mapped_column(Integer, default=None)
    military_cooperation_score: Mapped[int | None] = mapped_column(Integer, default=None)
    military_tension_score: Mapped[int | None] = mapped_column(Integer, default=None)
    intelligence_cooperation_score: Mapped[int | None] = mapped_column(Integer, default=None)
    economic_dependency_score: Mapped[int | None] = mapped_column(Integer, default=None)
    energy_dependency_score: Mapped[int | None] = mapped_column(Integer, default=None)
    strategic_trust_score: Mapped[int | None] = mapped_column(Integer, default=None)
    ideological_compatibility_score: Mapped[int | None] = mapped_column(Integer, default=None)
    proxy_competition_score: Mapped[int | None] = mapped_column(Integer, default=None)
    public_hostility_score: Mapped[int | None] = mapped_column(Integer, default=None)
    escalation_risk_score: Mapped[int | None] = mapped_column(Integer, default=None)
    trend: Mapped[Trend | None] = mapped_column(String(10), default=None)
    confidence: Mapped[float | None] = mapped_column(Float, default=None)
    explanation: Mapped[str | None] = mapped_column(Text, default=None)
    evidence_bundle_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("evidence_bundles.id", ondelete="SET NULL"), default=None
    )
    ruleset_version: Mapped[str | None] = mapped_column(String(50), default=None)
    model_version: Mapped[str | None] = mapped_column(String(100), default=None)
    approved_at: Mapped[datetime | None] = mapped_column(default=None)
    approved_by: Mapped[str | None] = mapped_column(String(200), default=None)


DIMENSION_SCORE_FIELDS: tuple[str, ...] = (
    "diplomatic_score",
    "military_cooperation_score",
    "military_tension_score",
    "intelligence_cooperation_score",
    "economic_dependency_score",
    "energy_dependency_score",
    "strategic_trust_score",
    "ideological_compatibility_score",
    "proxy_competition_score",
    "public_hostility_score",
    "escalation_risk_score",
)


__all__ = ["DIMENSION_SCORE_FIELDS", "Relationship", "RelationshipObservation"]
