from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.application.services.events import EventService
from mei.domain.review.models import ReviewItem
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.actors import ActorRepository
from mei.infrastructure.repositories.claims import ClaimRepository
from mei.infrastructure.repositories.review import ReviewRepository
from mei.shared.enums import ReviewStatus, ReviewType
from mei.shared.errors import ConflictError, NotFoundError
from mei.shared.time import utcnow

_CLAIM_ROLES = frozenset({"claimant", "subject"})


class ReviewService:
    """Analyst resolution of queued `ReviewItem`s (design doc sections 12.3, 15.2).

    Backfills the real link the originating pipeline step declined to make
    automatically, keyed off `ReviewItem.subject_json` (see
    `EntityResolutionService` for the fields it writes).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._review = ReviewRepository(session)
        self._actors = ActorRepository(session)
        self._claims = ClaimRepository(session)
        self._events = EventService(session)

    async def list_pending(
        self,
        *,
        review_type: ReviewType | None = None,
        status: ReviewStatus | None = ReviewStatus.PENDING,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReviewItem]:
        return await self._review.list_all(
            review_type=review_type, status=status, limit=limit, offset=offset
        )

    async def get(self, item_id: UUID) -> ReviewItem:
        item = await self._review.get(item_id)
        if item is None:
            raise NotFoundError(f"Review item {item_id} not found")
        return item

    async def resolve_entity_resolution(
        self, item_id: UUID, *, resolved_actor_id: UUID, principal: Principal
    ) -> ReviewItem:
        item = await self._require_pending(item_id)
        if item.review_type != ReviewType.ENTITY_RESOLUTION:
            raise ConflictError(f"Review item {item_id} is not an entity-resolution item")

        actor = await self._actors.get(resolved_actor_id)
        if actor is None:
            raise NotFoundError(f"Actor {resolved_actor_id} not found")

        subject = item.subject_json
        link_kind = subject["link_kind"]
        target_type = subject["target_type"]
        target_id = UUID(str(subject["target_id"]))

        if target_type == "event" and link_kind == "event_actor":
            await self._events.add_actor(
                event_id=target_id,
                actor_id=actor.id,
                role=str(subject.get("event_role") or "participant"),
            )
        elif target_type == "claim" and link_kind in _CLAIM_ROLES:
            claim = await self._claims.get(target_id)
            if claim is None:
                raise NotFoundError(f"Claim {target_id} not found")
            await self._claims.set_actor(claim, role=str(link_kind), actor_id=actor.id)
        else:
            raise ConflictError(
                f"Unsupported review subject: target_type={target_type!r} link_kind={link_kind!r}"
            )

        await self._review.resolve(
            item,
            status=ReviewStatus.APPROVED,
            resolution={"resolved_actor_id": str(actor.id)},
            resolved_by=str(principal.user_id),
            resolved_at=utcnow(),
        )
        return item

    async def reject(self, item_id: UUID, *, principal: Principal) -> ReviewItem:
        item = await self._require_pending(item_id)
        await self._review.resolve(
            item,
            status=ReviewStatus.REJECTED,
            resolution={},
            resolved_by=str(principal.user_id),
            resolved_at=utcnow(),
        )
        return item

    async def _require_pending(self, item_id: UUID) -> ReviewItem:
        item = await self.get(item_id)
        if item.status != ReviewStatus.PENDING:
            raise ConflictError(f"Review item {item_id} is already {item.status}")
        return item


__all__ = ["ReviewService"]
