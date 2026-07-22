from datetime import datetime
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from mei.infrastructure.database.base import Base
from mei.shared.enums import VerificationStatus
from mei.shared.ids import uuid7


class ImageEvidence(Base):
    """A submitted satellite/photo image and its vision-model analysis
    (design doc section 35, Phase 6 "imagery evidence").

    Imagery is frequently geolocated independently of any event, so
    `latitude`/`longitude` live directly on this table (mirroring
    `EventLocation`) rather than requiring an event link. `analysis_json`
    mirrors `Event.extraction_metadata_json`'s provenance convention
    (provider, model, prompt name/version, timestamp).
    """

    __tablename__ = "image_evidence"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    source_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sources.id", ondelete="SET NULL"), default=None
    )
    document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), default=None
    )
    object_key: Mapped[str] = mapped_column(String(500))
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    content_type: Mapped[str] = mapped_column(String(100))
    captured_at: Mapped[datetime | None] = mapped_column(default=None)
    retrieved_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, default=None)
    longitude: Mapped[float | None] = mapped_column(Float, default=None)
    location_precision: Mapped[str | None] = mapped_column(String(30), default=None)
    caption: Mapped[str | None] = mapped_column(Text, default=None)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        String(30), default=VerificationStatus.UNREVIEWED
    )
    confidence: Mapped[float | None] = mapped_column(Float, default=None)
    analysis_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    submitted_by_type: Mapped[str] = mapped_column(String(20))
    submitted_by_id: Mapped[str | None] = mapped_column(String(200), default=None)


class EvidenceBundleImageryItem(Base):
    """Imagery counterpart to `EvidenceBundleItem` (design doc section 8.4).

    `EvidenceBundleItem`'s primary key is the composite
    `(bundle_id, claim_evidence_id)`; a primary-key column can't be NULL in
    Postgres, so an image can't be added as an XOR-nullable sibling column
    on that already-shipped table without restructuring it. A parallel
    table with the same shape (composite PK, `weight`, `CASCADE` on both
    sides) is strictly additive instead.
    """

    __tablename__ = "evidence_bundle_imagery_items"

    bundle_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_bundles.id", ondelete="CASCADE"), primary_key=True
    )
    image_evidence_id: Mapped[UUID] = mapped_column(
        ForeignKey("image_evidence.id", ondelete="CASCADE"), primary_key=True
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0)


__all__ = ["EvidenceBundleImageryItem", "ImageEvidence"]
