from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.evidence.models import EvidenceBundle, EvidenceBundleItem
from mei.domain.imagery.models import EvidenceBundleImageryItem


class EvidenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_bundle(self, bundle_id: UUID) -> EvidenceBundle | None:
        return await self._session.get(EvidenceBundle, bundle_id)

    async def list_item_claim_evidence_ids(self, bundle_id: UUID) -> list[UUID]:
        result = await self._session.execute(
            select(EvidenceBundleItem.claim_evidence_id).where(
                EvidenceBundleItem.bundle_id == bundle_id
            )
        )
        return list(result.scalars())

    async def create_bundle(
        self, *, title: str, summary: str | None = None, confidence: float | None = None
    ) -> EvidenceBundle:
        bundle = EvidenceBundle(title=title, summary=summary, confidence=confidence)
        self._session.add(bundle)
        await self._session.flush()
        return bundle

    async def add_item(
        self, *, bundle_id: UUID, claim_evidence_id: UUID, weight: float = 1.0
    ) -> EvidenceBundleItem:
        item = EvidenceBundleItem(
            bundle_id=bundle_id, claim_evidence_id=claim_evidence_id, weight=weight
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def list_bundle_imagery_ids(self, bundle_id: UUID) -> list[UUID]:
        result = await self._session.execute(
            select(EvidenceBundleImageryItem.image_evidence_id).where(
                EvidenceBundleImageryItem.bundle_id == bundle_id
            )
        )
        return list(result.scalars())

    async def add_imagery_item(
        self, *, bundle_id: UUID, image_evidence_id: UUID, weight: float = 1.0
    ) -> EvidenceBundleImageryItem:
        item = EvidenceBundleImageryItem(
            bundle_id=bundle_id, image_evidence_id=image_evidence_id, weight=weight
        )
        self._session.add(item)
        await self._session.flush()
        return item


__all__ = ["EvidenceRepository"]
