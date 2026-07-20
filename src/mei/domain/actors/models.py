from datetime import date
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mei.infrastructure.database.base import Base, TimestampMixin
from mei.shared.enums import ActorStatus, ActorType
from mei.shared.ids import uuid7


class Actor(TimestampMixin, Base):
    __tablename__ = "actors"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    canonical_name: Mapped[str] = mapped_column(String(300), index=True)
    native_name: Mapped[str | None] = mapped_column(String(300), default=None)
    actor_type: Mapped[ActorType] = mapped_column(String(40), index=True)
    parent_actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("actors.id", ondelete="SET NULL"), default=None
    )
    country_actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("actors.id", ondelete="SET NULL"), default=None
    )
    status: Mapped[ActorStatus] = mapped_column(String(20), default=ActorStatus.ACTIVE)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    valid_from: Mapped[date | None] = mapped_column(default=None)
    valid_to: Mapped[date | None] = mapped_column(default=None)
    attributes_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)

    aliases: Mapped[list["ActorAlias"]] = relationship(
        back_populates="actor",
        cascade="all, delete-orphan",
        foreign_keys="ActorAlias.actor_id",
    )


class ActorAlias(Base):
    __tablename__ = "actor_aliases"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("actors.id", ondelete="CASCADE"), index=True)
    alias: Mapped[str] = mapped_column(String(300), index=True)
    language: Mapped[str | None] = mapped_column(String(10), default=None)
    alias_type: Mapped[str | None] = mapped_column(String(50), default=None)
    valid_from: Mapped[date | None] = mapped_column(default=None)
    valid_to: Mapped[date | None] = mapped_column(default=None)

    actor: Mapped[Actor] = relationship(back_populates="aliases", foreign_keys=[actor_id])


class ActorLeadership(Base):
    __tablename__ = "actor_leadership"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("actors.id", ondelete="CASCADE"), index=True)
    person_actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("actors.id", ondelete="CASCADE"), index=True
    )
    role_name: Mapped[str] = mapped_column(String(200))
    valid_from: Mapped[date | None] = mapped_column(default=None)
    valid_to: Mapped[date | None] = mapped_column(default=None)
    evidence_bundle_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("evidence_bundles.id", ondelete="SET NULL"), default=None
    )


__all__ = ["Actor", "ActorAlias", "ActorLeadership"]
