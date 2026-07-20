from datetime import datetime
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mei.infrastructure.database.base import Base
from mei.shared.ids import uuid7


class EvidenceBundle(Base):
    """A curated, analyst-approved set of evidence backing one assessment.

    Distinct from `ClaimEvidence`: a claim's raw evidence links are the
    building blocks, a bundle is the reviewed subset actually cited by an
    approved event, relationship observation, or risk assessment.
    """

    __tablename__ = "evidence_bundles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str | None] = mapped_column(Text, default=None)
    confidence: Mapped[float | None] = mapped_column(Float, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(default=None)
    approved_by: Mapped[str | None] = mapped_column(String(200), default=None)

    items: Mapped[list["EvidenceBundleItem"]] = relationship(
        back_populates="bundle", cascade="all, delete-orphan"
    )


class EvidenceBundleItem(Base):
    __tablename__ = "evidence_bundle_items"

    bundle_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_bundles.id", ondelete="CASCADE"), primary_key=True
    )
    claim_evidence_id: Mapped[UUID] = mapped_column(
        ForeignKey("claim_evidence.id", ondelete="CASCADE"), primary_key=True
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    bundle: Mapped[EvidenceBundle] = relationship(back_populates="items")


__all__ = ["EvidenceBundle", "EvidenceBundleItem"]
