from datetime import date, datetime
from uuid import UUID

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from mei.infrastructure.database.base import Base
from mei.shared.enums import ReportStatus, ReportType, ScopeType
from mei.shared.ids import uuid7


class Report(Base):
    """A generated intelligence report artifact (design doc section 8.10 / 25).

    `content_markdown` keeps the rendered body queryable/citable in place;
    `content_object_key` (when set) points at the same content archived in
    object storage, mirroring how `documents.raw_object_key` pairs with
    `documents.extracted_text` elsewhere in the platform.
    """

    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    report_type: Mapped[ReportType] = mapped_column(String(30), index=True)
    title: Mapped[str] = mapped_column(String(300))
    scope_type: Mapped[ScopeType | None] = mapped_column(String(20), default=None)
    scope_id: Mapped[UUID | None] = mapped_column(default=None)
    period_start: Mapped[date | None] = mapped_column(default=None)
    period_end: Mapped[date | None] = mapped_column(default=None)
    content_markdown: Mapped[str] = mapped_column(Text)
    content_object_key: Mapped[str | None] = mapped_column(String(500), default=None)
    status: Mapped[ReportStatus] = mapped_column(
        String(20), default=ReportStatus.GENERATED, index=True
    )
    generated_by_model: Mapped[str | None] = mapped_column(String(100), default=None)
    prompt_version: Mapped[str | None] = mapped_column(String(50), default=None)
    approved_by: Mapped[str | None] = mapped_column(String(200), default=None)
    approved_at: Mapped[datetime | None] = mapped_column(default=None)
    published_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


__all__ = ["Report"]
