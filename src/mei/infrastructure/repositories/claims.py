from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mei.domain.claims.models import Claim, ClaimEvidence
from mei.shared.enums import EvidenceStance, LifecycleStatus, VerificationStatus


class ClaimRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, claim_id: UUID) -> Claim | None:
        result = await self._session.execute(
            select(Claim).where(Claim.id == claim_id).options(selectinload(Claim.evidence))
        )
        return result.scalar_one_or_none()

    async def list_all(
        self, *, event_id: UUID | None = None, limit: int = 50, offset: int = 0
    ) -> list[Claim]:
        stmt = select(Claim).order_by(Claim.id.desc()).limit(limit).offset(offset)
        if event_id is not None:
            stmt = stmt.where(Claim.event_id == event_id)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def create(
        self,
        *,
        claim_text: str,
        claim_type: str,
        created_by_type: str,
        created_by_id: str | None,
        claimant_actor_id: UUID | None = None,
        subject_actor_id: UUID | None = None,
        event_id: UUID | None = None,
    ) -> Claim:
        claim = Claim(
            claim_text=claim_text,
            claim_type=claim_type,
            created_by_type=created_by_type,
            created_by_id=created_by_id,
            claimant_actor_id=claimant_actor_id,
            subject_actor_id=subject_actor_id,
            event_id=event_id,
            verification_status=VerificationStatus.UNREVIEWED,
            lifecycle_status=LifecycleStatus.OBSERVED,
        )
        self._session.add(claim)
        await self._session.flush()
        return claim

    async def add_evidence(
        self,
        *,
        claim_id: UUID,
        document_id: UUID,
        stance: EvidenceStance,
        excerpt: str,
        chunk_id: UUID | None = None,
        source_location: str | None = None,
        directness: str | None = None,
        independence_group: str | None = None,
        confidence: float | None = None,
        analyst_note: str | None = None,
    ) -> ClaimEvidence:
        evidence = ClaimEvidence(
            claim_id=claim_id,
            document_id=document_id,
            chunk_id=chunk_id,
            stance=stance,
            excerpt=excerpt,
            source_location=source_location,
            directness=directness,
            independence_group=independence_group,
            confidence=confidence,
            analyst_note=analyst_note,
        )
        self._session.add(evidence)
        await self._session.flush()
        return evidence

    async def list_evidence(self, claim_id: UUID) -> list[ClaimEvidence]:
        result = await self._session.execute(
            select(ClaimEvidence)
            .where(ClaimEvidence.claim_id == claim_id)
            .order_by(ClaimEvidence.created_at)
        )
        return list(result.scalars())


__all__ = ["ClaimRepository"]
