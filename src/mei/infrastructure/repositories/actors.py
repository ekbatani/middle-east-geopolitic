from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mei.domain.actors.models import Actor, ActorAlias, ActorLeadership
from mei.shared.enums import ActorStatus, ActorType


class ActorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, actor_id: UUID) -> Actor | None:
        result = await self._session.execute(
            select(Actor).where(Actor.id == actor_id).options(selectinload(Actor.aliases))
        )
        return result.scalar_one_or_none()

    async def get_by_canonical_name(self, canonical_name: str) -> Actor | None:
        result = await self._session.execute(
            select(Actor).where(Actor.canonical_name == canonical_name)
        )
        return result.scalar_one_or_none()

    async def find_by_exact_alias(self, name: str) -> Actor | None:
        """Entity resolution step 1 (design doc section 12.2): exact normalized match."""
        result = await self._session.execute(
            select(Actor)
            .options(selectinload(Actor.aliases))
            .where(Actor.canonical_name.ilike(name))
        )
        actor = result.scalar_one_or_none()
        if actor is not None:
            return actor

        alias_match = select(ActorAlias.actor_id).where(ActorAlias.alias.ilike(name))
        result = await self._session.execute(
            select(Actor).options(selectinload(Actor.aliases)).where(Actor.id.in_(alias_match))
        )
        return result.scalars().first()

    async def list_candidates(self, *, actor_type: ActorType | None = None) -> list[Actor]:
        """All actors (with aliases loaded) for fuzzy-match ranking in entity resolution.

        Unbounded by design: resolution needs the full candidate pool, not a
        page of it. Fine at the actor-registry scale this platform targets;
        revisit with a search index if that stops being true.
        """
        stmt = select(Actor).options(selectinload(Actor.aliases))
        if actor_type is not None:
            stmt = stmt.where(Actor.actor_type == actor_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique())

    async def list_all(
        self,
        *,
        query: str | None = None,
        actor_type: ActorType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Actor]:
        stmt = select(Actor).options(selectinload(Actor.aliases)).order_by(Actor.canonical_name)

        if actor_type is not None:
            stmt = stmt.where(Actor.actor_type == actor_type)

        if query:
            pattern = f"%{query}%"
            alias_match = select(ActorAlias.actor_id).where(ActorAlias.alias.ilike(pattern))
            stmt = stmt.where(
                or_(
                    Actor.canonical_name.ilike(pattern),
                    Actor.native_name.ilike(pattern),
                    Actor.id.in_(alias_match),
                )
            )

        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique())

    async def create(
        self,
        *,
        canonical_name: str,
        actor_type: ActorType,
        native_name: str | None = None,
        parent_actor_id: UUID | None = None,
        country_actor_id: UUID | None = None,
        description: str | None = None,
        status: ActorStatus = ActorStatus.ACTIVE,
    ) -> Actor:
        actor = Actor(
            canonical_name=canonical_name,
            actor_type=actor_type,
            native_name=native_name,
            parent_actor_id=parent_actor_id,
            country_actor_id=country_actor_id,
            description=description,
            status=status,
        )
        self._session.add(actor)
        await self._session.flush()
        return actor

    async def add_alias(
        self,
        *,
        actor_id: UUID,
        alias: str,
        language: str | None = None,
        alias_type: str | None = None,
    ) -> ActorAlias:
        alias_row = ActorAlias(
            actor_id=actor_id, alias=alias, language=language, alias_type=alias_type
        )
        self._session.add(alias_row)
        await self._session.flush()
        return alias_row

    async def list_by_ids(self, actor_ids: list[UUID]) -> list[Actor]:
        """Batch fetch, e.g. resolving the actors referenced by a set of
        relationships without one query per actor."""
        if not actor_ids:
            return []
        result = await self._session.execute(select(Actor).where(Actor.id.in_(actor_ids)))
        return list(result.scalars())

    async def list_leadership(self, actor_id: UUID) -> list[ActorLeadership]:
        result = await self._session.execute(
            select(ActorLeadership)
            .where(ActorLeadership.actor_id == actor_id)
            .order_by(ActorLeadership.valid_from)
        )
        return list(result.scalars())


__all__ = ["ActorRepository"]
