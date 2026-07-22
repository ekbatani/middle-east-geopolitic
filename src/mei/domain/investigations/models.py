from datetime import datetime
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mei.infrastructure.database.base import Base, TimestampMixin
from mei.shared.ids import uuid7


class Investigation(TimestampMixin, Base):
    __tablename__ = "investigations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    title: Mapped[str] = mapped_column(String(300))
    question: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)  # pending, running, completed, failed
    priority: Mapped[str] = mapped_column(String(20), default="medium", index=True)  # low, medium, high
    requested_by: Mapped[str] = mapped_column(String(200))
    assigned_to: Mapped[str | None] = mapped_column(String(200), default=None)
    started_at: Mapped[datetime | None] = mapped_column(default=None)
    completed_at: Mapped[datetime | None] = mapped_column(default=None)
    result_summary: Mapped[str | None] = mapped_column(Text, default=None)
    confidence: Mapped[float | None] = mapped_column(Float, default=None)
    report_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("reports.id", ondelete="SET NULL"), default=None
    )

    steps: Mapped[list["InvestigationStep"]] = relationship(
        back_populates="investigation", cascade="all, delete-orphan"
    )


class InvestigationStep(Base):
    __tablename__ = "investigation_steps"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    investigation_id: Mapped[UUID] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), index=True
    )
    step_type: Mapped[str] = mapped_column(String(50))
    sequence: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending, running, completed, failed
    input_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    output_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(default=None)
    completed_at: Mapped[datetime | None] = mapped_column(default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)

    investigation: Mapped[Investigation] = relationship(back_populates="steps")


__all__ = ["Investigation", "InvestigationStep"]
