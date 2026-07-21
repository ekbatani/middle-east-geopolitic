from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mei.domain.events.models import Event, EventActor, EventImpact, EventLocation
from mei.shared.enums import LifecycleStatus, VerificationStatus

_ACTIVE_LIFECYCLE_STATUSES = (LifecycleStatus.EXTRACTED, LifecycleStatus.ASSESSED)


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _select_with_relations(self) -> Select[tuple[Event]]:
        return select(Event).options(
            selectinload(Event.actors),
            selectinload(Event.locations),
            selectinload(Event.impacts),
        )

    async def get(self, event_id: UUID) -> Event | None:
        stmt = self._select_with_relations().where(Event.id == event_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        lifecycle_status: LifecycleStatus | None = None,
        event_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Event]:
        stmt = self._select_with_relations().order_by(Event.started_at.desc())
        if lifecycle_status is not None:
            stmt = stmt.where(Event.lifecycle_status == lifecycle_status)
        if event_type is not None:
            stmt = stmt.where(Event.event_type == event_type)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique())

    async def create(
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
        extraction_metadata_json: dict[str, object] | None = None,
    ) -> Event:
        event = Event(
            event_type=event_type,
            title=title,
            summary=summary,
            started_at=started_at,
            ended_at=ended_at,
            time_precision=time_precision,
            severity=severity,
            strategic_significance=strategic_significance,
            verification_status=VerificationStatus.UNREVIEWED,
            lifecycle_status=LifecycleStatus.EXTRACTED,
            extraction_metadata_json=extraction_metadata_json or {},
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def find_candidates(
        self,
        *,
        event_type: str,
        window_start: datetime,
        window_end: datetime,
        actor_ids: list[UUID],
    ) -> list[Event]:
        """Event-clustering heuristic (design doc section 15.2): advisory only.

        Candidates share the event type, fall within the configured time
        window, and have at least one already-resolved actor in common.
        Callers decide what to do with >1 match (queue for review rather
        than auto-merge).
        """
        if not actor_ids:
            return []

        stmt = (
            self._select_with_relations()
            .join(EventActor, EventActor.event_id == Event.id)
            .where(
                Event.event_type == event_type,
                Event.lifecycle_status.in_(_ACTIVE_LIFECYCLE_STATUSES),
                Event.started_at >= window_start,
                Event.started_at <= window_end,
                EventActor.actor_id.in_(actor_ids),
            )
            .distinct()
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().unique())

    async def add_actor(
        self,
        *,
        event_id: UUID,
        actor_id: UUID,
        role: str,
        participation_status: str | None = None,
        confidence: float | None = None,
    ) -> EventActor:
        link = EventActor(
            event_id=event_id,
            actor_id=actor_id,
            role=role,
            participation_status=participation_status,
            confidence=confidence,
        )
        self._session.add(link)
        await self._session.flush()
        return link

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
        location = EventLocation(
            event_id=event_id,
            name=name,
            country_actor_id=country_actor_id,
            latitude=latitude,
            longitude=longitude,
            location_precision=location_precision,
        )
        self._session.add(location)
        await self._session.flush()
        return location

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
        impact = EventImpact(
            event_id=event_id,
            impact_type=impact_type,
            magnitude=magnitude,
            unit=unit,
            estimate_low=estimate_low,
            estimate_high=estimate_high,
            confidence=confidence,
        )
        self._session.add(impact)
        await self._session.flush()
        return impact

    async def set_lifecycle_status(
        self,
        event: Event,
        *,
        lifecycle_status: LifecycleStatus,
        evidence_bundle_id: UUID | None = None,
    ) -> None:
        event.lifecycle_status = lifecycle_status
        if evidence_bundle_id is not None:
            event.evidence_bundle_id = evidence_bundle_id
        await self._session.flush()


__all__ = ["EventRepository"]
