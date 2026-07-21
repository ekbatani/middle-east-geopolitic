from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from mei.infrastructure.database.base import Base
from mei.shared.enums import ForecastOutcome, ForecastStatus
from mei.shared.ids import uuid7


class ForecastRecord(Base):
    """A standing, scorable prediction (design doc section 8.8 / 8.9).

    `probability` and `confidence` are fixed at issuance; `status`,
    `outcome`, `resolved_at`, `brier_score`, and `evaluation_note` are the
    only fields a later resolution mutates, per the Phase 4 acceptance
    criterion "forecasts can be scored after resolution".
    """

    __tablename__ = "forecast_records"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    question: Mapped[str] = mapped_column(Text)
    issued_at: Mapped[datetime] = mapped_column(index=True)
    resolution_date: Mapped[date] = mapped_column(index=True)
    probability: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    assumptions_json: Mapped[list[object]] = mapped_column(JSONB, default=list)
    evidence_bundle_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("evidence_bundles.id", ondelete="SET NULL"), default=None
    )
    status: Mapped[ForecastStatus] = mapped_column(
        String(20), default=ForecastStatus.OPEN, index=True
    )
    outcome: Mapped[ForecastOutcome | None] = mapped_column(String(20), default=None)
    resolved_at: Mapped[datetime | None] = mapped_column(default=None)
    brier_score: Mapped[float | None] = mapped_column(Float, default=None)
    evaluation_note: Mapped[str | None] = mapped_column(Text, default=None)


__all__ = ["ForecastRecord"]
