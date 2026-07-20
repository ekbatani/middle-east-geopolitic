from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mei.infrastructure.database.base import Base, TimestampMixin
from mei.shared.enums import EndpointType, SourceType
from mei.shared.ids import uuid7


class Source(TimestampMixin, Base):
    __tablename__ = "sources"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(300), index=True)
    source_type: Mapped[SourceType] = mapped_column(String(40))
    base_url: Mapped[str | None] = mapped_column(String(2048), default=None)
    jurisdiction: Mapped[str | None] = mapped_column(String(100), default=None)
    default_language: Mapped[str | None] = mapped_column(String(10), default=None)
    ownership: Mapped[str | None] = mapped_column(Text, default=None)
    known_affiliations: Mapped[str | None] = mapped_column(Text, default=None)
    historical_reliability: Mapped[str | None] = mapped_column(String(50), default=None)
    collection_policy: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    endpoints: Mapped[list["SourceEndpoint"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class SourceEndpoint(Base):
    __tablename__ = "source_endpoints"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True
    )
    endpoint_type: Mapped[EndpointType] = mapped_column(String(20))
    url: Mapped[str] = mapped_column(String(2048))
    schedule: Mapped[str | None] = mapped_column(String(100), default=None)
    parser_name: Mapped[str | None] = mapped_column(String(100), default=None)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    last_success_at: Mapped[datetime | None] = mapped_column(default=None)
    last_failure_at: Mapped[datetime | None] = mapped_column(default=None)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)

    source: Mapped[Source] = relationship(back_populates="endpoints")


__all__ = ["Source", "SourceEndpoint"]
