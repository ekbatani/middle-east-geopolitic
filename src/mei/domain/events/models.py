from datetime import datetime
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mei.infrastructure.database.base import Base, TimestampMixin
from mei.shared.enums import LifecycleStatus, VerificationStatus
from mei.shared.ids import uuid7


class Event(TimestampMixin, Base):
    __tablename__ = "events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(Text, default=None)
    started_at: Mapped[datetime] = mapped_column(index=True)
    ended_at: Mapped[datetime | None] = mapped_column(default=None)
    time_precision: Mapped[str | None] = mapped_column(String(30), default=None)
    severity: Mapped[int | None] = mapped_column(Integer, default=None)
    strategic_significance: Mapped[str | None] = mapped_column(String(50), default=None)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        String(30), default=VerificationStatus.UNREVIEWED
    )
    confidence: Mapped[float | None] = mapped_column(Float, default=None)
    lifecycle_status: Mapped[LifecycleStatus] = mapped_column(
        String(20), default=LifecycleStatus.EXTRACTED, index=True
    )
    evidence_bundle_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("evidence_bundles.id", ondelete="SET NULL"), default=None
    )
    supersedes_event_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), default=None
    )

    actors: Mapped[list["EventActor"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    locations: Mapped[list["EventLocation"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    impacts: Mapped[list["EventImpact"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class EventActor(Base):
    __tablename__ = "event_actors"

    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("actors.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(50), primary_key=True)
    participation_status: Mapped[str | None] = mapped_column(String(30), default=None)
    confidence: Mapped[float | None] = mapped_column(Float, default=None)

    event: Mapped[Event] = relationship(back_populates="actors")


class EventLocation(Base):
    __tablename__ = "event_locations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(300))
    country_actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("actors.id", ondelete="SET NULL"), default=None
    )
    latitude: Mapped[float | None] = mapped_column(Float, default=None)
    longitude: Mapped[float | None] = mapped_column(Float, default=None)
    location_precision: Mapped[str | None] = mapped_column(String(30), default=None)

    event: Mapped[Event] = relationship(back_populates="locations")


class EventImpact(Base):
    __tablename__ = "event_impacts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    impact_type: Mapped[str] = mapped_column(String(50))
    magnitude: Mapped[float | None] = mapped_column(Float, default=None)
    unit: Mapped[str | None] = mapped_column(String(30), default=None)
    estimate_low: Mapped[float | None] = mapped_column(Float, default=None)
    estimate_high: Mapped[float | None] = mapped_column(Float, default=None)
    confidence: Mapped[float | None] = mapped_column(Float, default=None)
    evidence_bundle_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("evidence_bundles.id", ondelete="SET NULL"), default=None
    )

    event: Mapped[Event] = relationship(back_populates="impacts")


__all__ = ["Event", "EventActor", "EventImpact", "EventLocation"]
