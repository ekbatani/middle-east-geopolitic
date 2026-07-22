from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.events.models import Event, EventActor, EventImpact, EventLocation
from mei.infrastructure.repositories.actors import ActorRepository
from mei.infrastructure.repositories.claims import ClaimRepository
from mei.infrastructure.repositories.events import EventRepository
from mei.infrastructure.repositories.review import ReviewRepository
from mei.shared.enums import LifecycleStatus, ReviewType
from mei.shared.errors import ConflictError, NotFoundError

_TERMINAL_STATUSES = frozenset(
    {LifecycleStatus.APPROVED, LifecycleStatus.REJECTED, LifecycleStatus.SUPERSEDED}
)

# Event types design doc section 16.4 names as always requiring human review
# before the platform treats them as settled — attribution, casualty,
# leadership, nuclear, territorial, and war-status claims are too
# consequential for silent automated promotion. `event_type` is free text
# (no canonical enum), so this is the vocabulary extraction/analysts are
# expected to use for these categories.
HIGH_IMPACT_EVENT_TYPES = frozenset(
    {
        "war_declaration",
        "leader_death_or_incapacitation",
        "nuclear_incident",
        "major_attack_attribution",
        "mass_casualty_estimate",
        "territorial_control_change",
        "government_collapse",
        "ceasefire_or_treaty",
        "chokepoint_closure",
        "external_power_direct_entry",
    }
)

_CRITICAL_SIGNIFICANCE = "critical"


def is_high_impact_event(event_type: str, strategic_significance: str | None) -> bool:
    """Whether an event needs the design doc section 16.4 human-review
    path — either it's one of the always-review event types, or it's been
    marked critical strategic significance regardless of type. Pure and
    DB-free."""
    return event_type in HIGH_IMPACT_EVENT_TYPES or strategic_significance == _CRITICAL_SIGNIFICANCE


class EventService:
    def __init__(self, session: AsyncSession) -> None:
        self._events = EventRepository(session)
        self._claims = ClaimRepository(session)
        self._actors = ActorRepository(session)
        self._reviews = ReviewRepository(session)

    async def create_event(
        self,
        *,
        event_type: str,
        title: str,
        started_at: datetime,
        summary: str | None = None,
        ended_at: datetime | None = None,
        time_precision: str | None = None,
        severity: int | None = None,
        strategic_significance: str | None = None,
    ) -> Event:
        event = await self._events.create(
            event_type=event_type,
            title=title,
            started_at=started_at,
            summary=summary,
            ended_at=ended_at,
            time_precision=time_precision,
            severity=severity,
            strategic_significance=strategic_significance,
        )
        if is_high_impact_event(event_type, strategic_significance):
            await self._reviews.create(
                review_type=ReviewType.HIGH_IMPACT_EVENT,
                subject={
                    "event_id": str(event.id),
                    "event_type": event_type,
                    "strategic_significance": strategic_significance,
                },
                candidates=[],
            )
        return event

    async def add_actor(
        self,
        *,
        event_id: UUID,
        actor_id: UUID,
        role: str,
        participation_status: str | None = None,
        confidence: float | None = None,
    ) -> EventActor:
        await self._require_event(event_id)
        if await self._actors.get(actor_id) is None:
            raise NotFoundError(f"Actor {actor_id} not found")
        return await self._events.add_actor(
            event_id=event_id,
            actor_id=actor_id,
            role=role,
            participation_status=participation_status,
            confidence=confidence,
        )

    async def add_location(
        self,
        *,
        event_id: UUID,
        name: str,
        country_actor_id: UUID | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        location_precision: str | None = None,
    ) -> EventLocation:
        await self._require_event(event_id)
        if country_actor_id is not None and await self._actors.get(country_actor_id) is None:
            raise NotFoundError(f"Actor {country_actor_id} not found")
        return await self._events.add_location(
            event_id=event_id,
            name=name,
            country_actor_id=country_actor_id,
            latitude=latitude,
            longitude=longitude,
            location_precision=location_precision,
        )

    async def add_impact(
        self,
        *,
        event_id: UUID,
        impact_type: str,
        magnitude: float | None = None,
        unit: str | None = None,
        estimate_low: float | None = None,
        estimate_high: float | None = None,
        confidence: float | None = None,
    ) -> EventImpact:
        await self._require_event(event_id)
        return await self._events.add_impact(
            event_id=event_id,
            impact_type=impact_type,
            magnitude=magnitude,
            unit=unit,
            estimate_low=estimate_low,
            estimate_high=estimate_high,
            confidence=confidence,
        )

    async def approve_event(self, event_id: UUID) -> Event:
        event = await self._require_event(event_id)
        self._require_not_terminal(event)

        claims = await self._claims.list_all(event_id=event_id, limit=1000)
        has_evidence = False
        for claim in claims:
            if await self._claims.list_evidence(claim.id):
                has_evidence = True
                break

        if not has_evidence:
            raise ConflictError(
                "Cannot approve an event with no claim evidence linked to it. "
                "Create a claim referencing this event and attach evidence first."
            )

        await self._events.set_lifecycle_status(event, lifecycle_status=LifecycleStatus.APPROVED)
        return event

    async def reject_event(self, event_id: UUID) -> Event:
        event = await self._require_event(event_id)
        self._require_not_terminal(event)
        await self._events.set_lifecycle_status(event, lifecycle_status=LifecycleStatus.REJECTED)
        return event

    async def _require_event(self, event_id: UUID) -> Event:
        event = await self._events.get(event_id)
        if event is None:
            raise NotFoundError(f"Event {event_id} not found")
        return event

    @staticmethod
    def _require_not_terminal(event: Event) -> None:
        if event.lifecycle_status in _TERMINAL_STATUSES:
            raise ConflictError(f"Event is already {event.lifecycle_status}")


__all__ = ["HIGH_IMPACT_EVENT_TYPES", "EventService", "is_high_impact_event"]
