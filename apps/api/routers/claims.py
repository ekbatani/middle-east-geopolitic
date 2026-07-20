from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.claims import ClaimService
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.claims import ClaimRepository
from mei.shared.enums import EvidenceStance, LifecycleStatus, Scope, VerificationStatus
from mei.shared.errors import NotFoundError

router = APIRouter(prefix="/claims", tags=["claims"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
CreatePrincipal = Annotated[Principal, Depends(require_scopes(Scope.CLAIMS_CREATE))]


class ClaimEvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    chunk_id: UUID | None
    stance: EvidenceStance
    excerpt: str
    source_location: str | None
    confidence: float | None
    analyst_note: str | None
    created_at: datetime


class ClaimOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_text: str
    claim_type: str
    claimant_actor_id: UUID | None
    subject_actor_id: UUID | None
    event_id: UUID | None
    verification_status: VerificationStatus
    lifecycle_status: LifecycleStatus
    confidence: float | None


class CreateClaimRequest(BaseModel):
    claim_text: str = Field(min_length=1)
    claim_type: str = Field(min_length=1, max_length=100)
    claimant_actor_id: UUID | None = None
    subject_actor_id: UUID | None = None
    event_id: UUID | None = None


class AddClaimEvidenceRequest(BaseModel):
    document_id: UUID
    stance: EvidenceStance
    excerpt: str = Field(min_length=1)
    chunk_id: UUID | None = None
    source_location: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    analyst_note: str | None = None


@router.get("/{claim_id}", response_model=ClaimOut)
async def get_claim(claim_id: UUID, session: SessionDep, _principal: ReadPrincipal) -> ClaimOut:
    claim = await ClaimRepository(session).get(claim_id)
    if claim is None:
        raise NotFoundError(f"Claim {claim_id} not found")
    return ClaimOut.model_validate(claim)


@router.get("/{claim_id}/evidence", response_model=list[ClaimEvidenceOut])
async def get_claim_evidence(
    claim_id: UUID, session: SessionDep, _principal: ReadPrincipal
) -> list[ClaimEvidenceOut]:
    repo = ClaimRepository(session)
    if await repo.get(claim_id) is None:
        raise NotFoundError(f"Claim {claim_id} not found")
    evidence = await repo.list_evidence(claim_id)
    return [ClaimEvidenceOut.model_validate(item) for item in evidence]


@router.get("", response_model=list[ClaimOut])
async def list_claims(
    session: SessionDep,
    _principal: ReadPrincipal,
    event_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ClaimOut]:
    claims = await ClaimRepository(session).list_all(event_id=event_id, limit=limit, offset=offset)
    return [ClaimOut.model_validate(claim) for claim in claims]


@router.post("", response_model=ClaimOut, status_code=201)
async def create_claim(
    payload: CreateClaimRequest, session: SessionDep, principal: CreatePrincipal
) -> ClaimOut:
    claim = await ClaimService(session).create_claim(principal=principal, **payload.model_dump())
    await audit(
        session, principal, "claim.created", resource_type="claim", resource_id=str(claim.id)
    )
    return ClaimOut.model_validate(claim)


@router.post("/{claim_id}/evidence", response_model=ClaimEvidenceOut, status_code=201)
async def add_claim_evidence(
    claim_id: UUID,
    payload: AddClaimEvidenceRequest,
    session: SessionDep,
    principal: CreatePrincipal,
) -> ClaimEvidenceOut:
    evidence = await ClaimService(session).add_evidence(claim_id=claim_id, **payload.model_dump())
    await audit(
        session,
        principal,
        "claim.evidence_added",
        resource_type="claim",
        resource_id=str(claim_id),
        metadata={"claim_evidence_id": str(evidence.id)},
    )
    return ClaimEvidenceOut.model_validate(evidence)
