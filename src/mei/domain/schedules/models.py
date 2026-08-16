from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mei.infrastructure.database.base import Base, TimestampMixin
from mei.shared.ids import uuid7
from mei.shared.time import utcnow


class JobSchedule(TimestampMixin, Base):
    __tablename__ = "job_schedules"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(200), index=True)
    job_type: Mapped[str] = mapped_column(String(100), index=True)
    cron_expression: Mapped[str | None] = mapped_column(String(100), default=None)
    interval_seconds: Mapped[int | None] = mapped_column(Integer, default=None)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    last_status: Mapped[str | None] = mapped_column(String(50), default="idle")

    executions: Mapped[list["JobExecution"]] = relationship(
        back_populates="schedule", cascade="all, delete-orphan", order_by="desc(JobExecution.started_at)"
    )


class JobExecution(Base):
    __tablename__ = "job_executions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    schedule_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("job_schedules.id", ondelete="SET NULL"), nullable=True, index=True
    )
    job_type: Mapped[str] = mapped_column(String(100), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    status: Mapped[str] = mapped_column(String(50), default="running", index=True)  # running, success, failed
    items_processed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    log_output: Mapped[str | None] = mapped_column(Text, default=None)

    schedule: Mapped[JobSchedule | None] = relationship(back_populates="executions")


__all__ = ["JobExecution", "JobSchedule"]
