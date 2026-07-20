from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.claims.models import Claim, ClaimEvidence
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.actors import ActorRepository
from mei.infrastructure.repositories.claims import ClaimRepository
from mei.infrastructure.repositories.documents import DocumentRepository
from mei.infrastructure.repositories.events import EventRepository
from mei.shared.enums import EvidenceStance
from mei.shared.errors import NotFoundError


class ClaimService:
    def __init__(self, session: AsyncSession) -> None:
        self._claims = ClaimRepository(session)
        self._actors = ActorRepository(session)
        self._events = EventRepository(session)
        self._documents = DocumentRepository(session)

    async def create_claim(
        self,
        *,
        claim_text: str,
        claim_type: str,
        principal: Principal,
        claimant_actor_id: UUID | None = None,
        subject_actor_id: UUID | None = None,
        event_id: UUID | None = None,
    ) -> Claim:
        for actor_id, label in (
            (claimant_actor_id, "claimant_actor_id"),
            (subject_actor_id, "subject_actor_id"),
        ):
            if actor_id is not None and await self._actors.get(actor_id) is None:
                raise NotFoundError(f"Actor referenced by {label} ({actor_id}) not found")

        if event_id is not None and await self._events.get(event_id) is None:
            raise NotFoundError(f"Event {event_id} not found")

        return await self._claims.create(
            claim_text=claim_text,
            claim_type=claim_type,
            created_by_type="user",
            created_by_id=str(principal.user_id),
            claimant_actor_id=claimant_actor_id,
            subject_actor_id=subject_actor_id,
            event_id=event_id,
        )

    async def add_evidence(
        self,
        *,
        claim_id: UUID,
        document_id: UUID,
        stance: EvidenceStance,
        excerpt: str,
        chunk_id: UUID | None = None,
        source_location: str | None = None,
        confidence: float | None = None,
        analyst_note: str | None = None,
    ) -> ClaimEvidence:
        if await self._claims.get(claim_id) is None:
            raise NotFoundError(f"Claim {claim_id} not found")
        if await self._documents.get(document_id) is None:
            raise NotFoundError(f"Document {document_id} not found")

        return await self._claims.add_evidence(
            claim_id=claim_id,
            document_id=document_id,
            chunk_id=chunk_id,
            stance=stance,
            excerpt=excerpt,
            source_location=source_location,
            confidence=confidence,
            analyst_note=analyst_note,
        )


__all__ = ["ClaimService"]
