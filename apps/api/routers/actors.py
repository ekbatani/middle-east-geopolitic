from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.actors import ActorService
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.actors import ActorRepository
from mei.shared.enums import ActorStatus, ActorType, Scope
from mei.shared.errors import NotFoundError

router = APIRouter(prefix="/actors", tags=["actors"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
AdminPrincipal = Annotated[Principal, Depends(require_scopes(Scope.ADMIN_CONFIGURATION))]


class ActorAliasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    alias: str
    language: str | None
    alias_type: str | None
    valid_from: date | None
    valid_to: date | None


class ActorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    canonical_name: str
    native_name: str | None
    actor_type: ActorType
    status: ActorStatus
    parent_actor_id: UUID | None
    country_actor_id: UUID | None
    description: str | None
    aliases: list[ActorAliasOut] = Field(default_factory=list)


class ActorLeadershipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    person_actor_id: UUID
    role_name: str
    valid_from: date | None
    valid_to: date | None


class ActorTimelineResponse(BaseModel):
    actor_id: UUID
    leadership: list[ActorLeadershipOut]


class CreateActorRequest(BaseModel):
    canonical_name: str = Field(min_length=1, max_length=300)
    actor_type: ActorType
    native_name: str | None = None
    parent_actor_id: UUID | None = None
    country_actor_id: UUID | None = None
    description: str | None = None


class UpdateActorRequest(BaseModel):
    canonical_name: str | None = None
    actor_type: ActorType | None = None
    native_name: str | None = None
    description: str | None = None
    status: ActorStatus | None = None


class CreateActorAliasRequest(BaseModel):
    alias: str = Field(min_length=1, max_length=300)
    language: str | None = None
    alias_type: str | None = None


@router.get("", response_model=list[ActorOut])
async def list_actors(
    session: SessionDep,
    _principal: ReadPrincipal,
    q: str | None = Query(default=None, description="Case-insensitive name/alias search"),
    actor_type: ActorType | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ActorOut]:
    actors = await ActorRepository(session).list_all(
        query=q, actor_type=actor_type, limit=limit, offset=offset
    )
    return [ActorOut.model_validate(actor) for actor in actors]


@router.get("/{actor_id}", response_model=ActorOut)
async def get_actor(actor_id: UUID, session: SessionDep, _principal: ReadPrincipal) -> ActorOut:
    actor = await ActorRepository(session).get(actor_id)
    if actor is None:
        raise NotFoundError(f"Actor {actor_id} not found")
    return ActorOut.model_validate(actor)


@router.patch("/{actor_id}", response_model=ActorOut)
async def update_actor(
    actor_id: UUID,
    payload: UpdateActorRequest,
    session: SessionDep,
    principal: AdminPrincipal,
) -> ActorOut:
    repo = ActorRepository(session)
    actor = await repo.get(actor_id)
    if actor is None:
        raise NotFoundError(f"Actor {actor_id} not found")

    updated = await repo.update(
        actor,
        canonical_name=payload.canonical_name,
        actor_type=payload.actor_type,
        native_name=payload.native_name,
        description=payload.description,
        status=payload.status,
    )
    await audit(
        session,
        principal,
        "actor.updated",
        resource_type="actor",
        resource_id=str(actor_id),
        metadata=payload.model_dump(exclude_unset=True),
    )
    await session.commit()
    refreshed = await repo.get(actor_id)
    return ActorOut.model_validate(refreshed)


@router.delete("/{actor_id}", status_code=204)
async def delete_actor(
    actor_id: UUID,
    session: SessionDep,
    principal: AdminPrincipal,
) -> None:
    repo = ActorRepository(session)
    actor = await repo.get(actor_id)
    if actor is None:
        raise NotFoundError(f"Actor {actor_id} not found")

    await repo.delete(actor)
    await audit(
        session,
        principal,
        "actor.deleted",
        resource_type="actor",
        resource_id=str(actor_id),
    )
    await session.commit()


@router.get("/{actor_id}/timeline", response_model=ActorTimelineResponse)
async def get_actor_timeline(
    actor_id: UUID, session: SessionDep, _principal: ReadPrincipal
) -> ActorTimelineResponse:
    repo = ActorRepository(session)
    if await repo.get(actor_id) is None:
        raise NotFoundError(f"Actor {actor_id} not found")
    leadership = await repo.list_leadership(actor_id)
    return ActorTimelineResponse(
        actor_id=actor_id,
        leadership=[ActorLeadershipOut.model_validate(entry) for entry in leadership],
    )


@router.post("", response_model=ActorOut, status_code=201)
async def create_actor(
    payload: CreateActorRequest, session: SessionDep, principal: AdminPrincipal
) -> ActorOut:
    actor = await ActorService(session).create_actor(**payload.model_dump())
    await audit(
        session, principal, "actor.created", resource_type="actor", resource_id=str(actor.id)
    )
    await session.commit()
    return ActorOut.model_validate(actor)


@router.post("/{actor_id}/aliases", response_model=ActorAliasOut, status_code=201)
async def create_actor_alias(
    actor_id: UUID,
    payload: CreateActorAliasRequest,
    session: SessionDep,
    principal: AdminPrincipal,
) -> ActorAliasOut:
    repo = ActorRepository(session)
    if await repo.get(actor_id) is None:
        raise NotFoundError(f"Actor {actor_id} not found")

    alias = await repo.add_alias(actor_id=actor_id, **payload.model_dump())
    await audit(
        session, principal, "actor.alias_added", resource_type="actor", resource_id=str(actor_id)
    )
    await session.commit()
    return ActorAliasOut.model_validate(alias)


@router.delete("/{actor_id}/aliases/{alias_id}", status_code=204)
async def delete_actor_alias(
    actor_id: UUID,
    alias_id: UUID,
    session: SessionDep,
    principal: AdminPrincipal,
) -> None:
    repo = ActorRepository(session)
    if await repo.get(actor_id) is None:
        raise NotFoundError(f"Actor {actor_id} not found")

    deleted = await repo.delete_alias(alias_id)
    if not deleted:
        raise NotFoundError(f"Alias {alias_id} not found")

    await audit(
        session, principal, "actor.alias_deleted", resource_type="actor_alias", resource_id=str(alias_id)
    )
    await session.commit()
