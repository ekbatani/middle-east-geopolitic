from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from mei.infrastructure.database.base import Base
from mei.shared.enums import IndicatorNormalizationMethod, ScopeType
from mei.shared.ids import uuid7


class IndicatorDefinition(Base):
    """Catalog entry for one measurable signal (design doc section 8.7 / section 34).

    `lower_bound`/`upper_bound`/`staleness_hours` extend the logical schema
    in the design doc to make the normalization and staleness policy
    described narratively in section 18.2 actually enforceable rather than
    implicit in code.
    """

    __tablename__ = "indicator_definitions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(1000), default=None)
    category: Mapped[str] = mapped_column(String(50), index=True)
    value_type: Mapped[str] = mapped_column(String(30))
    normalization_method: Mapped[IndicatorNormalizationMethod] = mapped_column(
        String(20), default=IndicatorNormalizationMethod.MIN_MAX
    )
    lower_bound: Mapped[float | None] = mapped_column(Float, default=None)
    upper_bound: Mapped[float | None] = mapped_column(Float, default=None)
    staleness_hours: Mapped[int | None] = mapped_column(Integer, default=None)
    default_weight: Mapped[float | None] = mapped_column(Float, default=None)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    ruleset_version: Mapped[str] = mapped_column(String(50), default="v1")


class IndicatorObservation(Base):
    """One raw reading of an indicator for one scope, at one point in time.

    Append-only, like `RelationshipObservation`: the risk engine always
    reads the latest non-stale row as of the assessment time rather than an
    upserted "current value", so a base score stays reproducible from
    history (design doc section 39 acceptance criteria).
    """

    __tablename__ = "indicator_observations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    indicator_id: Mapped[UUID] = mapped_column(
        ForeignKey("indicator_definitions.id", ondelete="CASCADE"), index=True
    )
    scope_type: Mapped[ScopeType] = mapped_column(String(20), index=True)
    scope_id: Mapped[UUID] = mapped_column(index=True)
    observed_at: Mapped[datetime] = mapped_column(index=True)
    raw_value: Mapped[float] = mapped_column(Float)
    normalized_value: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    evidence_bundle_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("evidence_bundles.id", ondelete="SET NULL"), default=None
    )
    source_method: Mapped[str | None] = mapped_column(String(100), default=None)


__all__ = ["IndicatorDefinition", "IndicatorObservation"]
