from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.relationships.models import (
    DIMENSION_SCORE_FIELDS,
    Relationship,
    RelationshipObservation,
)
from mei.infrastructure.repositories.actors import ActorRepository
from mei.infrastructure.repositories.relationships import RelationshipRepository
from mei.shared.enums import RelationshipDirectionality, Trend
from mei.shared.errors import NotFoundError
from mei.shared.time import utcnow


class RelationshipService:
    def __init__(self, session: AsyncSession) -> None:
        self._relationships = RelationshipRepository(session)
        self._actors = ActorRepository(session)

    async def create_relationship(
        self,
        *,
        source_actor_id: UUID,
        target_actor_id: UUID,
        relationship_type: str,
        directionality: RelationshipDirectionality = RelationshipDirectionality.SYMMETRIC,
    ) -> Relationship:
        if await self._actors.get(source_actor_id) is None:
            raise NotFoundError(f"Actor {source_actor_id} not found")
        if await self._actors.get(target_actor_id) is None:
            raise NotFoundError(f"Actor {target_actor_id} not found")

        existing = await self._relationships.get_between(
            source_actor_id=source_actor_id,
            target_actor_id=target_actor_id,
            relationship_type=relationship_type,
        )
        if existing is not None:
            return existing

        return await self._relationships.create(
            source_actor_id=source_actor_id,
            target_actor_id=target_actor_id,
            relationship_type=relationship_type,
            directionality=directionality,
        )

    async def record_observation(
        self,
        relationship_id: UUID,
        *,
        scores: dict[str, int | None],
        trend: Trend | None,
        confidence: float | None,
        explanation: str | None,
        evidence_bundle_id: UUID | None,
        ruleset_version: str,
        approved_by: str,
        model_version: str | None = None,
    ) -> RelationshipObservation:
        """Record an analyst-submitted dimension scoring (design doc section 8.6).

        The caller reaching this method already holds `relationships:assess`
        scope (enforced at the API layer), so their submission *is* the
        human confirmation required by section 13.4 for a relationship
        change recommendation — an LLM may have proposed the scores, but a
        person is the one asserting them here.
        """
        relationship = await self._relationships.get(relationship_id)
        if relationship is None:
            raise NotFoundError(f"Relationship {relationship_id} not found")

        unknown_fields = set(scores) - set(DIMENSION_SCORE_FIELDS)
        if unknown_fields:
            raise ValueError(f"Unknown relationship dimension(s): {sorted(unknown_fields)}")

        now = utcnow()
        return await self._relationships.add_observation(
            relationship_id=relationship_id,
            observed_at=now,
            scores=scores,
            trend=trend,
            confidence=confidence,
            explanation=explanation,
            evidence_bundle_id=evidence_bundle_id,
            ruleset_version=ruleset_version,
            model_version=model_version,
            approved_by=approved_by,
            approved_at=now,
        )

    async def get_history(
        self,
        relationship_id: UUID,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RelationshipObservation]:
        if await self._relationships.get(relationship_id) is None:
            raise NotFoundError(f"Relationship {relationship_id} not found")
        return await self._relationships.list_observations(
            relationship_id, since=since, until=until, limit=limit, offset=offset
        )


__all__ = ["RelationshipService"]
