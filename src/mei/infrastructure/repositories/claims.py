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
        lifecycle_status: LifecycleStatus = LifecycleStatus.OBSERVED,
        extraction_metadata_json: dict[str, object] | None = None,
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
            lifecycle_status=lifecycle_status,
            extraction_metadata_json=extraction_metadata_json or {},
        )
        self._session.add(claim)
        await self._session.flush()
        return claim

    async def set_actor(self, claim: Claim, *, role: str, actor_id: UUID) -> None:
        """Backfill a claimant/subject link once entity resolution review resolves it."""
        if role == "claimant":
            claim.claimant_actor_id = actor_id
        elif role == "subject":
            claim.subject_actor_id = actor_id
        else:
            raise ValueError(f"Unknown claim actor role: {role}")
        await self._session.flush()

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

    async def update(
        self,
        claim: Claim,
        *,
        claim_text: str | None = None,
        claim_type: str | None = None,
        verification_status: VerificationStatus | None = None,
        lifecycle_status: LifecycleStatus | None = None,
        confidence: float | None = None,
    ) -> Claim:
        if claim_text is not None:
            claim.claim_text = claim_text
        if claim_type is not None:
            claim.claim_type = claim_type
        if verification_status is not None:
            claim.verification_status = verification_status
        if lifecycle_status is not None:
            claim.lifecycle_status = lifecycle_status
        if confidence is not None:
            claim.confidence = confidence
        await self._session.flush()
        return claim

    async def delete(self, claim: Claim) -> None:
        await self._session.delete(claim)
        await self._session.flush()

    async def delete_evidence(self, evidence_id: UUID) -> bool:
        ev = await self._session.get(ClaimEvidence, evidence_id)
        if ev is not None:
            await self._session.delete(ev)
            await self._session.flush()
            return True
        return False


__all__ = ["ClaimRepository"]

