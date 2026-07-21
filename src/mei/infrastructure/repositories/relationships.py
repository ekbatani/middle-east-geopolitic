from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.relationships.models import Relationship, RelationshipObservation
from mei.shared.enums import RelationshipDirectionality, RelationshipStatus, Trend


class RelationshipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, relationship_id: UUID) -> Relationship | None:
        return await self._session.get(Relationship, relationship_id)

    async def get_between(
        self, *, source_actor_id: UUID, target_actor_id: UUID, relationship_type: str
    ) -> Relationship | None:
        """Unordered lookup: a relationship row is one edge regardless of which
        actor was passed as source vs. target when it was created."""
        stmt = select(Relationship).where(
            Relationship.relationship_type == relationship_type,
            or_(
                and_(
                    Relationship.source_actor_id == source_actor_id,
                    Relationship.target_actor_id == target_actor_id,
                ),
                and_(
                    Relationship.source_actor_id == target_actor_id,
                    Relationship.target_actor_id == source_actor_id,
                ),
            ),
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_all(
        self,
        *,
        actor_id: UUID | None = None,
        relationship_type: str | None = None,
        status: RelationshipStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Relationship]:
        stmt = select(Relationship).order_by(Relationship.created_at.desc())
        if actor_id is not None:
            stmt = stmt.where(
                or_(
                    Relationship.source_actor_id == actor_id,
                    Relationship.target_actor_id == actor_id,
                )
            )
        if relationship_type is not None:
            stmt = stmt.where(Relationship.relationship_type == relationship_type)
        if status is not None:
            stmt = stmt.where(Relationship.status == status)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def create(
        self,
        *,
        source_actor_id: UUID,
        target_actor_id: UUID,
        relationship_type: str,
        directionality: RelationshipDirectionality = RelationshipDirectionality.SYMMETRIC,
    ) -> Relationship:
        relationship = Relationship(
            source_actor_id=source_actor_id,
            target_actor_id=target_actor_id,
            relationship_type=relationship_type,
            directionality=directionality,
            status=RelationshipStatus.ACTIVE,
        )
        self._session.add(relationship)
        await self._session.flush()
        return relationship

    async def add_observation(
        self,
        *,
        relationship_id: UUID,
        observed_at: datetime,
        scores: dict[str, int | None],
        trend: Trend | None,
        confidence: float | None,
        explanation: str | None,
        evidence_bundle_id: UUID | None,
        ruleset_version: str | None,
        model_version: str | None,
        approved_by: str | None,
        approved_at: datetime | None,
    ) -> RelationshipObservation:
        observation = RelationshipObservation(
            relationship_id=relationship_id,
            observed_at=observed_at,
            trend=trend,
            confidence=confidence,
            explanation=explanation,
            evidence_bundle_id=evidence_bundle_id,
            ruleset_version=ruleset_version,
            model_version=model_version,
            approved_by=approved_by,
            approved_at=approved_at,
            **scores,
        )
        self._session.add(observation)
        await self._session.flush()
        return observation

    async def get_latest_observation(
        self, relationship_id: UUID, *, as_of: datetime | None = None
    ) -> RelationshipObservation | None:
        stmt = select(RelationshipObservation).where(
            RelationshipObservation.relationship_id == relationship_id
        )
        if as_of is not None:
            stmt = stmt.where(RelationshipObservation.observed_at <= as_of)
        stmt = stmt.order_by(RelationshipObservation.observed_at.desc()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_previous_observation(
        self, relationship_id: UUID, *, before: datetime
    ) -> RelationshipObservation | None:
        stmt = (
            select(RelationshipObservation)
            .where(
                RelationshipObservation.relationship_id == relationship_id,
                RelationshipObservation.observed_at < before,
            )
            .order_by(RelationshipObservation.observed_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_recent_observations(
        self, *, since: datetime, limit: int = 200
    ) -> list[RelationshipObservation]:
        """Every observation recorded since `since`, across all relationships,
        for report generation's "relationship changes" section (design doc
        section 25.3)."""
        stmt = (
            select(RelationshipObservation)
            .where(RelationshipObservation.observed_at >= since)
            .order_by(RelationshipObservation.observed_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def list_observations(
        self,
        relationship_id: UUID,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RelationshipObservation]:
        stmt = select(RelationshipObservation).where(
            RelationshipObservation.relationship_id == relationship_id
        )
        if since is not None:
            stmt = stmt.where(RelationshipObservation.observed_at >= since)
        if until is not None:
            stmt = stmt.where(RelationshipObservation.observed_at <= until)
        stmt = stmt.order_by(RelationshipObservation.observed_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars())


__all__ = ["RelationshipRepository"]
