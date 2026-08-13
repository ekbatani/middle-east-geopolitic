from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mei.infrastructure.database.base import Base
from mei.shared.ids import uuid7


class Monitor(Base):
    __tablename__ = "monitors"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(300))
    user_id: Mapped[UUID] = mapped_column(index=True)
    monitor_type: Mapped[str] = mapped_column(String(50))
    condition_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    schedule: Mapped[str | None] = mapped_column(String(100), default=None)
    delivery_channel: Mapped[str] = mapped_column(String(50), default="telegram")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_evaluated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="monitor", cascade="all, delete-orphan"
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    monitor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("monitors.id", ondelete="CASCADE"), index=True, default=None
    )
    report_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("reports.id", ondelete="SET NULL"), index=True, default=None
    )
    severity: Mapped[str] = mapped_column(String(20), default="info")  # info, warning, critical
    title: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    delivery_channel: Mapped[str] = mapped_column(String(50), default="telegram")
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )  # pending, sent, failed
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)

    monitor: Mapped[Monitor | None] = relationship(back_populates="notifications")


__all__ = ["Monitor", "Notification"]
