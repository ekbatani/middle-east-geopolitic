from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.events import EventService
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.events import EventRepository
from mei.shared.enums import LifecycleStatus, Scope, VerificationStatus
from mei.shared.errors import NotFoundError

router = APIRouter(prefix="/events", tags=["events"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
CreatePrincipal = Annotated[Principal, Depends(require_scopes(Scope.EVENTS_CREATE))]
ApprovePrincipal = Annotated[Principal, Depends(require_scopes(Scope.EVENTS_APPROVE))]


class EventActorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    actor_id: UUID
    role: str
    participation_status: str | None
    confidence: float | None


class EventLocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    country_actor_id: UUID | None
    latitude: float | None
    longitude: float | None
    location_precision: str | None


class EventImpactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    impact_type: str
    magnitude: float | None
    unit: str | None
    estimate_low: float | None
    estimate_high: float | None
    confidence: float | None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    title: str
    summary: str | None
    started_at: datetime
    ended_at: datetime | None
    severity: int | None
    strategic_significance: str | None
    verification_status: VerificationStatus
    lifecycle_status: LifecycleStatus
    confidence: float | None
    actors: list[EventActorOut] = Field(default_factory=list)
    locations: list[EventLocationOut] = Field(default_factory=list)
    impacts: list[EventImpactOut] = Field(default_factory=list)


class CreateEventRequest(BaseModel):
    event_type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=500)
    started_at: datetime
    summary: str | None = None
    ended_at: datetime | None = None
    time_precision: str | None = None
    severity: int | None = Field(default=None, ge=1, le=5)
    strategic_significance: str | None = None


class AddEventActorRequest(BaseModel):
    actor_id: UUID
    role: str = Field(min_length=1, max_length=50)
    participation_status: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class AddEventLocationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    country_actor_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_precision: str | None = None


class AddEventImpactRequest(BaseModel):
    impact_type: str = Field(min_length=1, max_length=50)
    magnitude: float | None = None
    unit: str | None = None
    estimate_low: float | None = None
    estimate_high: float | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


@router.get("", response_model=list[EventOut])
async def list_events(
    session: SessionDep,
    _principal: ReadPrincipal,
    lifecycle_status: LifecycleStatus | None = None,
    event_type: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[EventOut]:
    events = await EventRepository(session).list_all(
        lifecycle_status=lifecycle_status, event_type=event_type, limit=limit, offset=offset
    )
    return [EventOut.model_validate(event) for event in events]


@router.get("/{event_id}", response_model=EventOut)
async def get_event(event_id: UUID, session: SessionDep, _principal: ReadPrincipal) -> EventOut:
    event = await EventRepository(session).get(event_id)
    if event is None:
        raise NotFoundError(f"Event {event_id} not found")
    return EventOut.model_validate(event)


@router.post("", response_model=EventOut, status_code=201)
async def create_event(
    payload: CreateEventRequest, session: SessionDep, principal: CreatePrincipal
) -> EventOut:
    event = await EventService(session).create_event(**payload.model_dump())
    await audit(
        session, principal, "event.created", resource_type="event", resource_id=str(event.id)
    )
    return EventOut.model_validate(await EventRepository(session).get(event.id))


@router.post("/{event_id}/actors", response_model=EventActorOut, status_code=201)
async def add_event_actor(
    event_id: UUID,
    payload: AddEventActorRequest,
    session: SessionDep,
    principal: CreatePrincipal,
) -> EventActorOut:
    link = await EventService(session).add_actor(event_id=event_id, **payload.model_dump())
    await audit(
        session, principal, "event.actor_added", resource_type="event", resource_id=str(event_id)
    )
    return EventActorOut.model_validate(link)


@router.post("/{event_id}/locations", response_model=EventLocationOut, status_code=201)
async def add_event_location(
    event_id: UUID,
    payload: AddEventLocationRequest,
    session: SessionDep,
    principal: CreatePrincipal,
) -> EventLocationOut:
    location = await EventService(session).add_location(event_id=event_id, **payload.model_dump())
    await audit(
        session, principal, "event.location_added", resource_type="event", resource_id=str(event_id)
    )
    return EventLocationOut.model_validate(location)


@router.post("/{event_id}/impacts", response_model=EventImpactOut, status_code=201)
async def add_event_impact(
    event_id: UUID,
    payload: AddEventImpactRequest,
    session: SessionDep,
    principal: CreatePrincipal,
) -> EventImpactOut:
    impact = await EventService(session).add_impact(event_id=event_id, **payload.model_dump())
    await audit(
        session, principal, "event.impact_added", resource_type="event", resource_id=str(event_id)
    )
    return EventImpactOut.model_validate(impact)


@router.post("/{event_id}/approve", response_model=EventOut)
async def approve_event(
    event_id: UUID, session: SessionDep, principal: ApprovePrincipal
) -> EventOut:
    await EventService(session).approve_event(event_id)
    await audit(
        session, principal, "event.approved", resource_type="event", resource_id=str(event_id)
    )
    return EventOut.model_validate(await EventRepository(session).get(event_id))


@router.post("/{event_id}/reject", response_model=EventOut)
async def reject_event(
    event_id: UUID, session: SessionDep, principal: ApprovePrincipal
) -> EventOut:
    await EventService(session).reject_event(event_id)
    await audit(
        session, principal, "event.rejected", resource_type="event", resource_id=str(event_id)
    )
    return EventOut.model_validate(await EventRepository(session).get(event_id))
