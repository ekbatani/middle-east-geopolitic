from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.risk_engine import RiskEngine
from mei.domain.risks.models import RiskAssessment
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.llm.factory import get_structured_llm
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.infrastructure.repositories.risks import RiskRepository
from mei.shared.enums import RiskApprovalStatus, Scope, ScopeType, Trend
from mei.shared.errors import LLMConfigurationError, NotFoundError

router = APIRouter(prefix="/risks", tags=["risks"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
RecalculatePrincipal = Annotated[Principal, Depends(require_scopes(Scope.RISKS_RECALCULATE))]


def _try_get_llm() -> StructuredLLM | None:
    """Best-effort LLM adjustment: recalculation must still work — with the
    deterministic base score alone — when no provider key is configured."""
    try:
        return get_structured_llm()
    except LLMConfigurationError:
        return None


class RiskDefinitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str | None
    scope_types: list[str]
    ruleset_version: str


class RiskAssessmentOut(BaseModel):
    id: UUID
    risk_definition_id: UUID
    scope_type: ScopeType
    scope_id: UUID | None
    assessed_at: datetime
    base_score: int
    llm_adjustment: int
    final_score: int
    previous_score: int | None
    trend: Trend | None
    confidence: float
    explanation: str | None
    counter_indicators: list[str]
    evidence_bundle_id: UUID | None
    ruleset_version: str
    model_version: str | None
    approval_status: RiskApprovalStatus
    approved_by: str | None
    approved_at: datetime | None

    @classmethod
    def from_domain(cls, assessment: RiskAssessment) -> "RiskAssessmentOut":
        return cls(
            id=assessment.id,
            risk_definition_id=assessment.risk_definition_id,
            scope_type=assessment.scope_type,
            scope_id=assessment.scope_id,
            assessed_at=assessment.assessed_at,
            base_score=assessment.base_score,
            llm_adjustment=assessment.llm_adjustment,
            final_score=assessment.final_score,
            previous_score=assessment.previous_score,
            trend=assessment.trend,
            confidence=assessment.confidence,
            explanation=assessment.explanation,
            counter_indicators=list(assessment.counter_indicators_json),
            evidence_bundle_id=assessment.evidence_bundle_id,
            ruleset_version=assessment.ruleset_version,
            model_version=assessment.model_version,
            approval_status=assessment.approval_status,
            approved_by=assessment.approved_by,
            approved_at=assessment.approved_at,
        )


class RiskCatalogItemOut(BaseModel):
    definition: RiskDefinitionOut
    latest_assessment: RiskAssessmentOut | None = None


class RecalculateRiskRequest(BaseModel):
    risk_definition_id: UUID
    scope_type: ScopeType
    scope_id: UUID | None = None


@router.get("", response_model=list[RiskCatalogItemOut])
async def list_risks(
    session: SessionDep,
    _principal: ReadPrincipal,
    scope_type: ScopeType | None = None,
    scope_id: UUID | None = None,
) -> list[RiskCatalogItemOut]:
    repo = RiskRepository(session)
    definitions = await repo.list_definitions()

    items: list[RiskCatalogItemOut] = []
    for definition in definitions:
        if scope_type is not None and scope_type.value not in definition.scope_types:
            continue
        latest = None
        if scope_type is not None:
            assessment = await repo.get_latest_assessment(
                risk_definition_id=definition.id, scope_type=scope_type, scope_id=scope_id
            )
            latest = RiskAssessmentOut.from_domain(assessment) if assessment else None
        items.append(
            RiskCatalogItemOut(
                definition=RiskDefinitionOut.model_validate(definition), latest_assessment=latest
            )
        )
    return items


@router.get("/{risk_definition_id}/history", response_model=list[RiskAssessmentOut])
async def get_risk_history(
    risk_definition_id: UUID,
    session: SessionDep,
    _principal: ReadPrincipal,
    scope_type: ScopeType,
    scope_id: UUID | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[RiskAssessmentOut]:
    repo = RiskRepository(session)
    if await repo.get_definition(risk_definition_id) is None:
        raise NotFoundError(f"Risk definition {risk_definition_id} not found")

    history = await repo.list_history(
        risk_definition_id=risk_definition_id,
        scope_type=scope_type,
        scope_id=scope_id,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
    return [RiskAssessmentOut.from_domain(a) for a in history]


@router.post("/recalculate", response_model=RiskAssessmentOut, status_code=201)
async def recalculate_risk(
    payload: RecalculateRiskRequest, session: SessionDep, principal: RecalculatePrincipal
) -> RiskAssessmentOut:
    assessment = await RiskEngine(session).calculate(
        risk_definition_id=payload.risk_definition_id,
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        llm=_try_get_llm(),
        triggered_by=str(principal.user_id),
    )
    await audit(
        session,
        principal,
        "risk.recalculated",
        resource_type="risk_assessment",
        resource_id=str(assessment.id),
        metadata={
            "risk_definition_id": str(payload.risk_definition_id),
            "scope_type": str(payload.scope_type),
            "scope_id": str(payload.scope_id) if payload.scope_id else None,
        },
    )
    return RiskAssessmentOut.from_domain(assessment)
