from datetime import datetime
from uuid import UUID

from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from mei.infrastructure.database.base import Base
from mei.shared.enums import AuditActorType
from mei.shared.ids import uuid7


class AuditLog(Base):
    """Immutable record of authentication events, tool calls, and mutations.

    Append-only: nothing in this module ever updates or deletes a row,
    per section 27.5 of the implementation design.
    """

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    actor_type: Mapped[AuditActorType] = mapped_column(String(20))
    actor_id: Mapped[str | None] = mapped_column(String(200), default=None)
    action: Mapped[str] = mapped_column(String(200), index=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), default=None)
    resource_id: Mapped[str | None] = mapped_column(String(200), default=None)
    correlation_id: Mapped[str | None] = mapped_column(String(100), default=None)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False, index=True
    )


__all__ = ["AuditLog"]
