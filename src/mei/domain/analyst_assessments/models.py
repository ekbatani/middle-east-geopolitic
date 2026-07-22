from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from mei.infrastructure.database.base import Base, TimestampMixin
from mei.shared.enums import DisagreementSubjectType
from mei.shared.ids import uuid7


class AnalystAssessment(TimestampMixin, Base):
    """One analyst's independent position on a claim/event/risk assessment/
    relationship observation (design doc section 35, Phase 6).

    Distinct from `ReviewItem`: a review item is a pipeline-generated
    ambiguous decision awaiting a single resolution; this is a durable,
    per-analyst record that a different analyst's row never overwrites, so
    disagreement stays visible instead of collapsing into one "current"
    answer. The unique constraint lets one analyst revise their own
    position (upsert) without touching anyone else's.
    """

    __tablename__ = "analyst_assessments"
    __table_args__ = (
        UniqueConstraint(
            "subject_type",
            "subject_id",
            "analyst_user_id",
            name="uq_analyst_assessments_subject_analyst",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    subject_type: Mapped[DisagreementSubjectType] = mapped_column(String(30), index=True)
    subject_id: Mapped[UUID] = mapped_column(index=True)
    analyst_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    stance: Mapped[str | None] = mapped_column(String(30), default=None)
    score: Mapped[float | None] = mapped_column(Float, default=None)
    confidence: Mapped[float | None] = mapped_column(Float, default=None)
    rationale: Mapped[str | None] = mapped_column(Text, default=None)
    evidence_bundle_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("evidence_bundles.id", ondelete="SET NULL"), default=None
    )


__all__ = ["AnalystAssessment"]
