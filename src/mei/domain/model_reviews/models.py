from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from mei.infrastructure.database.base import Base
from mei.shared.enums import ModelReviewSubjectType
from mei.shared.ids import uuid7


class ModelReviewResult(Base):
    """A secondary-model shadow re-run of a high-impact assessment and
    whether it agrees with the primary model's persisted output (design
    doc section 35, Phase 6 "multi-model review").

    Scoped to `RiskAssessment` score deltas for now: the shadow run reruns
    `RiskEngine.calculate(..., persist=False)` with a second configured
    model rather than replaying raw extraction prompts, so this table only
    needs the two final scores and a diff, not a full second copy of the
    assessment.
    """

    __tablename__ = "model_review_results"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    subject_type: Mapped[ModelReviewSubjectType] = mapped_column(String(30), index=True)
    subject_id: Mapped[UUID] = mapped_column(index=True)
    trigger_reason: Mapped[str] = mapped_column(String(50))
    primary_model: Mapped[str] = mapped_column(String(100))
    secondary_model: Mapped[str] = mapped_column(String(100))
    primary_final_score: Mapped[int] = mapped_column(Integer)
    secondary_final_score: Mapped[int] = mapped_column(Integer)
    agreement: Mapped[bool | None] = mapped_column(Boolean, default=None)
    agreement_delta: Mapped[int | None] = mapped_column(Integer, default=None)
    secondary_output_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    reviewed_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


__all__ = ["ModelReviewResult"]
