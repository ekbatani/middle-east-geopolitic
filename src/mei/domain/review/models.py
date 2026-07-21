from datetime import datetime
from uuid import UUID

from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from mei.infrastructure.database.base import Base
from mei.shared.enums import ReviewStatus, ReviewType
from mei.shared.ids import uuid7


class ReviewItem(Base):
    """A queued ambiguous decision an automated pipeline declined to make.

    Generic across review kinds (entity resolution, event-duplicate merges)
    rather than one table per kind: `subject_json` carries what needs a
    decision and where to apply it, `candidates_json` carries the ranked
    options the pipeline considered. See section 12.2 and 15.2 of the
    implementation design — never auto-merge below the confidence threshold,
    and treat similarity as advisory for high-impact merges.
    """

    __tablename__ = "review_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    review_type: Mapped[ReviewType] = mapped_column(String(30), index=True)
    status: Mapped[ReviewStatus] = mapped_column(
        String(20), default=ReviewStatus.PENDING, index=True
    )
    subject_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    candidates_json: Mapped[list[object]] = mapped_column(JSONB, default=list)
    resolution_json: Mapped[dict[str, object] | None] = mapped_column(JSONB, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(default=None)
    resolved_by: Mapped[str | None] = mapped_column(String(200), default=None)


__all__ = ["ReviewItem"]
