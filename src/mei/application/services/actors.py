from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.actors.models import Actor
from mei.infrastructure.repositories.actors import ActorRepository
from mei.shared.enums import ActorType
from mei.shared.errors import NotFoundError


class ActorService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ActorRepository(session)

    async def create_actor(
        self,
        *,
        canonical_name: str,
        actor_type: ActorType,
        native_name: str | None = None,
        parent_actor_id: UUID | None = None,
        country_actor_id: UUID | None = None,
        description: str | None = None,
    ) -> Actor:
        for related_id, label in (
            (parent_actor_id, "parent_actor_id"),
            (country_actor_id, "country_actor_id"),
        ):
            if related_id is not None and await self._repo.get(related_id) is None:
                raise NotFoundError(f"Actor referenced by {label} ({related_id}) not found")

        return await self._repo.create(
            canonical_name=canonical_name,
            actor_type=actor_type,
            native_name=native_name,
            parent_actor_id=parent_actor_id,
            country_actor_id=country_actor_id,
            description=description,
        )


__all__ = ["ActorService"]
