from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.investigations import InvestigationService
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.investigations import InvestigationRepository
from mei.shared.enums import Scope
from mei.shared.errors import NotFoundError

router = APIRouter(prefix="/investigations", tags=["investigations"])

CreatePrincipal = Annotated[Principal, Depends(require_scopes(Scope.INVESTIGATIONS_CREATE))]
ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INVESTIGATIONS_READ))]


class StepOut(BaseModel):
    id: UUID
    step_type: str
    sequence: int
    status: str
    input_json: dict[str, object]
    output_json: dict[str, object]
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None


class InvestigationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    question: str
    status: str
    priority: str
    requested_by: str
    assigned_to: str | None
    started_at: datetime | None
    completed_at: datetime | None
    result_summary: str | None
    confidence: float | None
    report_id: UUID | None
    created_at: datetime
    updated_at: datetime


class InvestigationDetailOut(InvestigationOut):
    steps: list[StepOut]


class CreateInvestigationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    question: str = Field(min_length=1)
    priority: str = Field(default="medium")
    assigned_to: str | None = None


@router.post("", response_model=InvestigationOut, status_code=201)
async def create_investigation(
    payload: CreateInvestigationRequest,
    session: SessionDep,
    principal: CreatePrincipal,
) -> InvestigationOut:
    service = InvestigationService(session)
    investigation = await service.launch_investigation(
        title=payload.title,
        question=payload.question,
        requested_by=str(principal.user_id),
        priority=payload.priority,
        assigned_to=payload.assigned_to,
    )
    await audit(
        session,
        principal,
        "investigation.launched",
        resource_type="investigation",
        resource_id=str(investigation.id),
    )
    return InvestigationOut.model_validate(investigation)


@router.get("/{investigation_id}", response_model=InvestigationDetailOut)
async def get_investigation(
    investigation_id: UUID,
    session: SessionDep,
    _principal: ReadPrincipal,
) -> InvestigationDetailOut:
    repo = InvestigationRepository(session)
    investigation = await repo.get(investigation_id)
    if not investigation:
        raise NotFoundError(f"Investigation {investigation_id} not found")
    steps = await repo.get_steps(investigation_id)
    return InvestigationDetailOut(
        id=investigation.id,
        title=investigation.title,
        question=investigation.question,
        status=investigation.status,
        priority=investigation.priority,
        requested_by=investigation.requested_by,
        assigned_to=investigation.assigned_to,
        started_at=investigation.started_at,
        completed_at=investigation.completed_at,
        result_summary=investigation.result_summary,
        confidence=investigation.confidence,
        report_id=investigation.report_id,
        created_at=investigation.created_at,
        updated_at=investigation.updated_at,
        steps=[
            StepOut(
                id=s.id,
                step_type=s.step_type,
                sequence=s.sequence,
                status=s.status,
                input_json=s.input_json,
                output_json=s.output_json,
                started_at=s.started_at,
                completed_at=s.completed_at,
                error_message=s.error_message,
            )
            for s in steps
        ],
    )


@router.get("", response_model=list[InvestigationOut])
async def list_investigations(
    session: SessionDep,
    _principal: ReadPrincipal,
    status: str | None = None,
    priority: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[InvestigationOut]:
    repo = InvestigationRepository(session)
    investigations = await repo.list_all(
        status=status,
        priority=priority,
        limit=limit,
        offset=offset,
    )
    return [InvestigationOut.model_validate(i) for i in investigations]


__all__ = ["router"]
