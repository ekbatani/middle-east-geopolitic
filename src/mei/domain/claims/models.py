from datetime import datetime
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mei.infrastructure.database.base import Base, TimestampMixin
from mei.shared.enums import EvidenceStance, LifecycleStatus, VerificationStatus
from mei.shared.ids import uuid7


class Claim(TimestampMixin, Base):
    __tablename__ = "claims"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    claim_text: Mapped[str] = mapped_column(Text)
    normalized_claim: Mapped[str | None] = mapped_column(Text, default=None)
    claim_type: Mapped[str] = mapped_column(String(100), index=True)
    claimant_actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("actors.id", ondelete="SET NULL"), default=None
    )
    subject_actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("actors.id", ondelete="SET NULL"), default=None
    )
    event_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), default=None, index=True
    )
    first_observed_at: Mapped[datetime | None] = mapped_column(default=None)
    last_checked_at: Mapped[datetime | None] = mapped_column(default=None)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        String(30), default=VerificationStatus.UNREVIEWED
    )
    confidence: Mapped[float | None] = mapped_column(Float, default=None)
    lifecycle_status: Mapped[LifecycleStatus] = mapped_column(
        String(20), default=LifecycleStatus.OBSERVED
    )
    created_by_type: Mapped[str] = mapped_column(String(20))
    created_by_id: Mapped[str | None] = mapped_column(String(200), default=None)

    evidence: Mapped[list["ClaimEvidence"]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )


class ClaimEvidence(Base):
    __tablename__ = "claim_evidence"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    claim_id: Mapped[UUID] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="SET NULL"), default=None
    )
    stance: Mapped[EvidenceStance] = mapped_column(String(30))
    excerpt: Mapped[str] = mapped_column(Text)
    source_location: Mapped[str | None] = mapped_column(String(300), default=None)
    directness: Mapped[str | None] = mapped_column(String(30), default=None)
    independence_group: Mapped[str | None] = mapped_column(String(200), default=None)
    confidence: Mapped[float | None] = mapped_column(Float, default=None)
    analyst_note: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    claim: Mapped[Claim] = relationship(back_populates="evidence")


__all__ = ["Claim", "ClaimEvidence"]
