from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from uuid import UUID

import dateparser
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from mei.application.services.entity_resolution import EntityResolutionService
from mei.domain.documents.models import Document
from mei.domain.events.models import Event
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.infrastructure.repositories.claims import ClaimRepository
from mei.infrastructure.repositories.events import EventRepository
from mei.infrastructure.repositories.review import ReviewRepository
from mei.shared.config import get_settings
from mei.shared.enums import EvidenceStance, LifecycleStatus, ReviewType
from mei.shared.logging import get_logger
from mei.shared.time import utcnow

logger = get_logger(__name__)

PROMPT_TASK_NAME = "claim_event_extraction"
PROMPT_VERSION = "claims_events_v1"


class ExtractedClaim(BaseModel):
    """Design doc section 14.1, verbatim."""

    text: str
    claimant_name: str | None = None
    subject_name: str | None = None
    claim_type: str
    event_reference: str | None = None
    source_excerpt: str
    temporal_reference: str | None = None
    location_reference: str | None = None
    extraction_confidence: float = Field(ge=0, le=1)


class ExtractedEventActor(BaseModel):
    name: str
    role: str


class ExtractedEvent(BaseModel):
    event_type: str
    title: str
    summary: str | None = None
    temporal_reference: str | None = None
    location_reference: str | None = None
    actors: list[ExtractedEventActor] = Field(default_factory=list)
    extraction_confidence: float = Field(ge=0, le=1)


class ExtractionResult(BaseModel):
    claims: list[ExtractedClaim] = Field(default_factory=list)
    events: list[ExtractedEvent] = Field(default_factory=list)


class ExtractionService:
    """LLM claim/event extraction and persistence (design doc sections 14, 15).

    `extract` only calls the LLM and validates its output; `persist` does
    the DB work (event clustering, entity resolution, claim/evidence
    creation) so a caller can inspect or log the raw result in between if
    useful, and so tests can exercise persistence against a canned result
    without a `StructuredLLM` in the loop at all.
    """

    def __init__(self, session: AsyncSession, llm: StructuredLLM) -> None:
        self._session = session
        self._llm = llm
        self._events = EventRepository(session)
        self._claims = ClaimRepository(session)
        self._review = ReviewRepository(session)
        self._resolver = EntityResolutionService(session)
        self._settings = get_settings()

    async def extract(self, document: Document) -> ExtractionResult:
        input_text = document.translation_text or document.extracted_text
        if not input_text:
            raise ValueError(f"Document {document.id} has no text to extract from")

        return await self._llm.generate_structured(
            task_name=PROMPT_TASK_NAME,
            prompt_version=PROMPT_VERSION,
            input_text=input_text,
            output_model=ExtractionResult,
            metadata={"document_id": str(document.id)},
        )

    async def persist(self, document: Document, result: ExtractionResult) -> None:
        provenance = self._build_provenance(document, result)
        event_by_title: dict[str, Event] = {}

        for extracted_event in result.events:
            event = await self._persist_event(document, extracted_event, provenance)
            event_by_title[extracted_event.title] = event

        for extracted_claim in result.claims:
            await self._persist_claim(document, extracted_claim, provenance, event_by_title)

    def _build_provenance(self, document: Document, result: ExtractionResult) -> dict[str, object]:
        input_text = document.translation_text or document.extracted_text or ""
        return {
            "provider": self._settings.llm_provider,
            "model": self._settings.llm_model,
            "prompt_name": PROMPT_TASK_NAME,
            "prompt_version": PROMPT_VERSION,
            "input_hash": hashlib.sha256(input_text.encode("utf-8")).hexdigest(),
            "output_hash": hashlib.sha256(result.model_dump_json().encode("utf-8")).hexdigest(),
            "generated_at": utcnow().isoformat(),
        }

    def _resolve_temporal(
        self, temporal_reference: str | None, document: Document
    ) -> tuple[datetime, str]:
        fallback = document.published_at or document.retrieved_at or utcnow()
        if not temporal_reference:
            return fallback, "approximate"

        parsed = dateparser.parse(
            temporal_reference,
            settings={
                "RELATIVE_BASE": fallback,
                "TIMEZONE": "UTC",
                "RETURN_AS_TIMEZONE_AWARE": True,
            },
        )
        if parsed is None:
            return fallback, "approximate"
        return parsed, "exact"

    async def _persist_event(
        self, document: Document, extracted: ExtractedEvent, provenance: dict[str, object]
    ) -> Event:
        started_at, time_precision = self._resolve_temporal(extracted.temporal_reference, document)

        # Confident-only actor ids feed the clustering lookup; ambiguous
        # mentions can't help find a matching event since we don't yet know
        # which actor they refer to.
        resolved_actor_ids: list[UUID] = []
        for actor in extracted.actors:
            confident_id = await self._resolver.resolve_confident(actor.name)
            if confident_id is not None:
                resolved_actor_ids.append(confident_id)

        window = timedelta(hours=self._settings.event_dedup_window_hours)
        candidates = await self._events.find_candidates(
            event_type=extracted.event_type,
            window_start=started_at - window,
            window_end=started_at + window,
            actor_ids=resolved_actor_ids,
        )

        if len(candidates) == 1:
            event = candidates[0]
            logger.info("event.deduplicated", event_id=str(event.id), document_id=str(document.id))
        else:
            event = await self._events.create(
                event_type=extracted.event_type,
                title=extracted.title,
                started_at=started_at,
                summary=extracted.summary,
                time_precision=time_precision,
                extraction_metadata_json=provenance,
            )
            if len(candidates) > 1:
                # More than one plausible existing event: don't guess which
                # one this is (design doc section 15.2, "advisory... high
                # impact merges require review").
                await self._review.create(
                    review_type=ReviewType.EVENT_DUPLICATE,
                    subject={
                        "new_event_id": str(event.id),
                        "document_id": str(document.id),
                        "event_type": extracted.event_type,
                    },
                    candidates=[
                        {
                            "event_id": str(candidate.id),
                            "title": candidate.title,
                            "started_at": candidate.started_at.isoformat(),
                        }
                        for candidate in candidates
                    ],
                )
                logger.info(
                    "event.duplicate_candidates_flagged",
                    event_id=str(event.id),
                    candidate_count=len(candidates),
                )

        existing_links = {(link.actor_id, link.role) for link in event.actors}
        for actor in extracted.actors:
            outcome = await self._resolver.resolve(
                actor.name,
                role="event_actor",
                target_type="event",
                target_id=event.id,
                document_id=document.id,
                extra_subject={"event_role": actor.role},
            )
            if (
                outcome.actor_id is not None
                and (outcome.actor_id, actor.role) not in existing_links
            ):
                await self._events.add_actor(
                    event_id=event.id, actor_id=outcome.actor_id, role=actor.role
                )
                existing_links.add((outcome.actor_id, actor.role))

        return event

    async def _persist_claim(
        self,
        document: Document,
        extracted: ExtractedClaim,
        provenance: dict[str, object],
        event_by_title: dict[str, Event],
    ) -> None:
        event = event_by_title.get(extracted.event_reference) if extracted.event_reference else None

        claim = await self._claims.create(
            claim_text=extracted.text,
            claim_type=extracted.claim_type,
            created_by_type="llm",
            created_by_id=f"{self._settings.llm_provider}:{self._settings.llm_model}:{PROMPT_VERSION}",
            event_id=event.id if event is not None else None,
            lifecycle_status=LifecycleStatus.EXTRACTED,
            extraction_metadata_json=provenance,
        )

        for role, name in (
            ("claimant", extracted.claimant_name),
            ("subject", extracted.subject_name),
        ):
            if not name:
                continue
            outcome = await self._resolver.resolve(
                name,
                role=role,
                target_type="claim",
                target_id=claim.id,
                document_id=document.id,
            )
            if outcome.actor_id is not None:
                await self._claims.set_actor(claim, role=role, actor_id=outcome.actor_id)

        await self._claims.add_evidence(
            claim_id=claim.id,
            document_id=document.id,
            stance=EvidenceStance.SUPPORTS,
            excerpt=extracted.source_excerpt,
            confidence=extracted.extraction_confidence,
        )


__all__ = [
    "PROMPT_TASK_NAME",
    "PROMPT_VERSION",
    "ExtractedClaim",
    "ExtractedEvent",
    "ExtractedEventActor",
    "ExtractionResult",
    "ExtractionService",
]
