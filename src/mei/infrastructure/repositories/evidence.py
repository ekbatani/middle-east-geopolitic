from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.evidence.models import EvidenceBundle, EvidenceBundleItem


class EvidenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_bundle(self, bundle_id: UUID) -> EvidenceBundle | None:
        return await self._session.get(EvidenceBundle, bundle_id)

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


__all__ = ["EvidenceRepository"]
