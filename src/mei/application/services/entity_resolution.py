from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from rapidfuzz import fuzz
from sqlalchemy.ext.asyncio import AsyncSession

from mei.infrastructure.repositories.actors import ActorRepository
from mei.infrastructure.repositories.review import ReviewRepository
from mei.shared.config import get_settings
from mei.shared.enums import ActorType, ReviewType

# Auto-resolving two close-scoring candidates as if only one existed would
# silently pick a coin flip; anything within this many RapidFuzz points of
# the top match is treated as ambiguous even if both clear the auto
# threshold, and sent to review instead (design doc section 12.2/12.3).
_AMBIGUITY_GAP = 5.0
_MAX_SURFACED_CANDIDATES = 5


@dataclass(frozen=True)
class ActorCandidate:
    actor_id: UUID
    canonical_name: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScoredCandidate:
    actor_id: UUID
    canonical_name: str
    score: float


def rank_candidates(name: str, candidates: list[ActorCandidate]) -> list[ScoredCandidate]:
    """Fuzzy-rank actor candidates against a mention (design doc section 12.2 step 3).

    Pure and DB-free by design so entity-resolution ranking behavior is unit
    testable without a database. Uses the best score across a candidate's
    canonical name and all aliases.
    """
    scored = []
    for candidate in candidates:
        names_to_check = (candidate.canonical_name, *candidate.aliases)
        best = max(fuzz.WRatio(name, other) for other in names_to_check)
        scored.append(
            ScoredCandidate(
                actor_id=candidate.actor_id, canonical_name=candidate.canonical_name, score=best
            )
        )
    scored.sort(key=lambda c: c.score, reverse=True)
    return scored


def is_auto_resolvable(ranked: list[ScoredCandidate], *, auto_threshold: float) -> bool:
    """Whether the top-ranked candidate is confident and unambiguous enough to auto-apply."""
    if not ranked:
        return False
    if ranked[0].score < auto_threshold:
        return False
    return not (len(ranked) > 1 and ranked[0].score - ranked[1].score < _AMBIGUITY_GAP)


@dataclass(frozen=True)
class ResolutionOutcome:
    """Exactly one of `actor_id` / `review_item_id` is set."""

    actor_id: UUID | None
    review_item_id: UUID | None


class EntityResolutionService:
    """Resolves an extracted actor mention to a canonical `Actor` (section 12).

    Never guesses below the configured confidence threshold: an unresolved
    or ambiguous mention is queued as a `ReviewItem` referencing exactly
    where the link needs to be applied once an analyst decides, rather than
    creating a partial/uncertain link on the claim or event.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._actors = ActorRepository(session)
        self._review = ReviewRepository(session)
        self._settings = get_settings()

    async def resolve_confident(
        self, candidate_name: str, *, actor_type_hint: ActorType | None = None
    ) -> UUID | None:
        """Side-effect-free resolution: an actor id if confident, else `None`.

        Used where a caller needs a best-effort id before it has a target to
        attach an ambiguous mention to (e.g. event-clustering needs resolved
        actor ids before the event row exists) — never queues a review item.
        """
        exact = await self._actors.find_by_exact_alias(candidate_name)
        if exact is not None:
            return exact.id

        ranked = await self._rank(candidate_name, actor_type_hint)
        if is_auto_resolvable(
            ranked, auto_threshold=self._settings.entity_resolution_auto_threshold
        ):
            return ranked[0].actor_id
        return None

    async def resolve(
        self,
        candidate_name: str,
        *,
        role: str,
        target_type: str,
        target_id: UUID,
        document_id: UUID | None = None,
        actor_type_hint: ActorType | None = None,
        extra_subject: dict[str, object] | None = None,
    ) -> ResolutionOutcome:
        exact = await self._actors.find_by_exact_alias(candidate_name)
        if exact is not None:
            return ResolutionOutcome(actor_id=exact.id, review_item_id=None)

        ranked = await self._rank(candidate_name, actor_type_hint)
        if is_auto_resolvable(
            ranked, auto_threshold=self._settings.entity_resolution_auto_threshold
        ):
            return ResolutionOutcome(actor_id=ranked[0].actor_id, review_item_id=None)

        review_threshold = self._settings.entity_resolution_review_threshold
        surfaced = [c for c in ranked if c.score >= review_threshold][:_MAX_SURFACED_CANDIDATES]
        item = await self._review.create(
            review_type=ReviewType.ENTITY_RESOLUTION,
            subject={
                "candidate_name": candidate_name,
                "link_kind": role,
                "target_type": target_type,
                "target_id": str(target_id),
                "document_id": str(document_id) if document_id else None,
                **(extra_subject or {}),
            },
            candidates=[
                {
                    "actor_id": str(candidate.actor_id),
                    "canonical_name": candidate.canonical_name,
                    "score": candidate.score,
                }
                for candidate in surfaced
            ],
        )
        return ResolutionOutcome(actor_id=None, review_item_id=item.id)

    async def _rank(
        self, candidate_name: str, actor_type_hint: ActorType | None
    ) -> list[ScoredCandidate]:
        candidates = await self._actors.list_candidates(actor_type=actor_type_hint)
        pool = [
            ActorCandidate(
                actor_id=actor.id,
                canonical_name=actor.canonical_name,
                aliases=tuple(alias.alias for alias in actor.aliases),
            )
            for actor in candidates
        ]
        return rank_candidates(candidate_name, pool)


__all__ = [
    "ActorCandidate",
    "EntityResolutionService",
    "ResolutionOutcome",
    "ScoredCandidate",
    "is_auto_resolvable",
    "rank_candidates",
]
