from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.relationships import RelationshipService
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.relationships import RelationshipRepository
from mei.shared.enums import RelationshipDirectionality, RelationshipStatus, Scope, Trend
from mei.shared.errors import NotFoundError

router = APIRouter(prefix="/relationships", tags=["relationships"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
AssessPrincipal = Annotated[Principal, Depends(require_scopes(Scope.RELATIONSHIPS_ASSESS))]


class RelationshipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_actor_id: UUID
    target_actor_id: UUID
    relationship_type: str
    directionality: RelationshipDirectionality
    status: RelationshipStatus


class RelationshipObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    relationship_id: UUID
    observed_at: datetime
    diplomatic_score: int | None
    military_cooperation_score: int | None
    military_tension_score: int | None
    intelligence_cooperation_score: int | None
    economic_dependency_score: int | None
    energy_dependency_score: int | None
    strategic_trust_score: int | None
    ideological_compatibility_score: int | None
    proxy_competition_score: int | None
    public_hostility_score: int | None
    escalation_risk_score: int | None
    trend: Trend | None
    confidence: float | None
    explanation: str | None
    evidence_bundle_id: UUID | None
    ruleset_version: str | None
    model_version: str | None
    approved_by: str | None
    approved_at: datetime | None


class CreateRelationshipRequest(BaseModel):
    source_actor_id: UUID
    target_actor_id: UUID
    relationship_type: str = Field(min_length=1, max_length=50)
    directionality: RelationshipDirectionality = RelationshipDirectionality.SYMMETRIC


class AssessRelationshipRequest(BaseModel):
    diplomatic_score: int | None = Field(default=None, ge=0, le=100)
    military_cooperation_score: int | None = Field(default=None, ge=0, le=100)
    military_tension_score: int | None = Field(default=None, ge=0, le=100)
    intelligence_cooperation_score: int | None = Field(default=None, ge=0, le=100)
    economic_dependency_score: int | None = Field(default=None, ge=0, le=100)
    energy_dependency_score: int | None = Field(default=None, ge=0, le=100)
    strategic_trust_score: int | None = Field(default=None, ge=0, le=100)
    ideological_compatibility_score: int | None = Field(default=None, ge=0, le=100)
    proxy_competition_score: int | None = Field(default=None, ge=0, le=100)
    public_hostility_score: int | None = Field(default=None, ge=0, le=100)
    escalation_risk_score: int | None = Field(default=None, ge=0, le=100)
    trend: Trend | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    explanation: str | None = None
    evidence_bundle_id: UUID | None = None
    ruleset_version: str = "v1"

    def scores(self) -> dict[str, int | None]:
        return {
            "diplomatic_score": self.diplomatic_score,
            "military_cooperation_score": self.military_cooperation_score,
            "military_tension_score": self.military_tension_score,
            "intelligence_cooperation_score": self.intelligence_cooperation_score,
            "economic_dependency_score": self.economic_dependency_score,
            "energy_dependency_score": self.energy_dependency_score,
            "strategic_trust_score": self.strategic_trust_score,
            "ideological_compatibility_score": self.ideological_compatibility_score,
            "proxy_competition_score": self.proxy_competition_score,
            "public_hostility_score": self.public_hostility_score,
            "escalation_risk_score": self.escalation_risk_score,
        }


@router.get("", response_model=list[RelationshipOut])
async def list_relationships(
    session: SessionDep,
    _principal: ReadPrincipal,
    actor_id: UUID | None = None,
    relationship_type: str | None = None,
    status: RelationshipStatus | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[RelationshipOut]:
    relationships = await RelationshipRepository(session).list_all(
        actor_id=actor_id,
        relationship_type=relationship_type,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [RelationshipOut.model_validate(r) for r in relationships]


@router.get("/{relationship_id}", response_model=RelationshipOut)
async def get_relationship(
    relationship_id: UUID, session: SessionDep, _principal: ReadPrincipal
) -> RelationshipOut:
    relationship = await RelationshipRepository(session).get(relationship_id)
    if relationship is None:
        raise NotFoundError(f"Relationship {relationship_id} not found")
    return RelationshipOut.model_validate(relationship)


@router.get("/{relationship_id}/history", response_model=list[RelationshipObservationOut])
async def get_relationship_history(
    relationship_id: UUID,
    session: SessionDep,
    _principal: ReadPrincipal,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[RelationshipObservationOut]:
    observations = await RelationshipService(session).get_history(
        relationship_id, since=since, until=until, limit=limit, offset=offset
    )
    return [RelationshipObservationOut.model_validate(o) for o in observations]


@router.post("", response_model=RelationshipOut, status_code=201)
async def create_relationship(
    payload: CreateRelationshipRequest, session: SessionDep, principal: AssessPrincipal
) -> RelationshipOut:
    relationship = await RelationshipService(session).create_relationship(**payload.model_dump())
    await audit(
        session,
        principal,
        "relationship.created",
        resource_type="relationship",
        resource_id=str(relationship.id),
    )
    return RelationshipOut.model_validate(relationship)


@router.post(
    "/{relationship_id}/assess", response_model=RelationshipObservationOut, status_code=201
)
async def assess_relationship(
    relationship_id: UUID,
    payload: AssessRelationshipRequest,
    session: SessionDep,
    principal: AssessPrincipal,
) -> RelationshipObservationOut:
    observation = await RelationshipService(session).record_observation(
        relationship_id,
        scores=payload.scores(),
        trend=payload.trend,
        confidence=payload.confidence,
        explanation=payload.explanation,
        evidence_bundle_id=payload.evidence_bundle_id,
        ruleset_version=payload.ruleset_version,
        approved_by=str(principal.user_id),
    )
    await audit(
        session,
        principal,
        "relationship.assessed",
        resource_type="relationship",
        resource_id=str(relationship_id),
    )
    return RelationshipObservationOut.model_validate(observation)
