from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.scenario_engine import ScenarioEngine, ScenarioUpdateRecommendation
from mei.domain.scenarios.models import ScenarioAssessment
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.llm.factory import get_structured_llm
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.infrastructure.repositories.scenarios import ScenarioRepository
from mei.shared.enums import ScenarioFamily, ScenarioStatus, Scope, ScopeType
from mei.shared.errors import LLMConfigurationError, NotFoundError

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
ManagePrincipal = Annotated[Principal, Depends(require_scopes(Scope.SCENARIOS_SIMULATE))]


def _try_get_llm() -> StructuredLLM | None:
    """Best-effort LLM drafting: canonical scenario updates must still work
    — carrying the previous assessment forward — when no provider is
    configured, matching the risk engine's convention."""
    try:
        return get_structured_llm()
    except LLMConfigurationError:
        return None


class ScenarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    scope_type: ScopeType
    scope_id: UUID | None
    scenario_family: ScenarioFamily
    time_horizon: str
    status: ScenarioStatus
    description: str | None


class ScenarioAssessmentOut(BaseModel):
    id: UUID
    scenario_id: UUID
    assessed_at: datetime
    probability_low: float
    probability_high: float
    confidence: float
    assumptions: list[str]
    trigger_events: list[str]
    leading_indicators: list[str]
    expected_actor_behavior: str | None
    military_consequences: str | None
    economic_consequences: str | None
    humanitarian_consequences: str | None
    invalidation_criteria: list[str]
    explanation_of_change: str | None
    evidence_bundle_id: UUID | None
    model_version: str | None
    approved_by: str | None
    approved_at: datetime | None

    @classmethod
    def from_domain(cls, assessment: ScenarioAssessment) -> "ScenarioAssessmentOut":
        return cls(
            id=assessment.id,
            scenario_id=assessment.scenario_id,
            assessed_at=assessment.assessed_at,
            probability_low=assessment.probability_low,
            probability_high=assessment.probability_high,
            confidence=assessment.confidence,
            assumptions=list(assessment.assumptions_json),
            trigger_events=list(assessment.trigger_events_json),
            leading_indicators=list(assessment.leading_indicators_json),
            expected_actor_behavior=assessment.expected_actor_behavior,
            military_consequences=assessment.military_consequences,
            economic_consequences=assessment.economic_consequences,
            humanitarian_consequences=assessment.humanitarian_consequences,
            invalidation_criteria=list(assessment.invalidation_criteria_json),
            explanation_of_change=assessment.explanation_of_change,
            evidence_bundle_id=assessment.evidence_bundle_id,
            model_version=assessment.model_version,
            approved_by=assessment.approved_by,
            approved_at=assessment.approved_at,
        )


class CreateScenarioRequest(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    scope_type: ScopeType
    scope_id: UUID | None = None
    scenario_family: ScenarioFamily
    time_horizon: str = Field(min_length=1, max_length=50)
    description: str | None = None


class ScenarioSimulationRequest(BaseModel):
    scope_type: ScopeType
    scope_id: UUID | None = None
    scenario_family: ScenarioFamily
    time_horizon: str = Field(min_length=1, max_length=50)
    hypothetical_context: str = Field(min_length=1)


@router.get("", response_model=list[ScenarioOut])
async def list_scenarios(
    session: SessionDep,
    _principal: ReadPrincipal,
    scope_type: ScopeType | None = None,
    scope_id: UUID | None = None,
    status: ScenarioStatus | None = None,
) -> list[ScenarioOut]:
    repo = ScenarioRepository(session)
    if scope_type is not None:
        scenarios = await repo.list_by_scope(
            scope_type=scope_type, scope_id=scope_id, status=status
        )
    else:
        scenarios = await repo.list_all(status=status)
    return [ScenarioOut.model_validate(s) for s in scenarios]


@router.get("/{scenario_id}", response_model=ScenarioOut)
async def get_scenario(
    scenario_id: UUID, session: SessionDep, _principal: ReadPrincipal
) -> ScenarioOut:
    scenario = await ScenarioRepository(session).get(scenario_id)
    if scenario is None:
        raise NotFoundError(f"Scenario {scenario_id} not found")
    return ScenarioOut.model_validate(scenario)


class UpdateScenarioRequest(BaseModel):
    name: str | None = None
    scenario_family: ScenarioFamily | None = None
    time_horizon: str | None = None
    description: str | None = None
    status: ScenarioStatus | None = None


@router.patch("/{scenario_id}", response_model=ScenarioOut)
async def update_scenario_details(
    scenario_id: UUID,
    payload: UpdateScenarioRequest,
    session: SessionDep,
    principal: ManagePrincipal,
) -> ScenarioOut:
    repo = ScenarioRepository(session)
    scenario = await repo.get(scenario_id)
    if scenario is None:
        raise NotFoundError(f"Scenario {scenario_id} not found")

    updated = await repo.update(
        scenario,
        name=payload.name,
        scenario_family=payload.scenario_family,
        time_horizon=payload.time_horizon,
        description=payload.description,
        status=payload.status,
    )
    await audit(
        session,
        principal,
        "scenario.details_updated",
        resource_type="scenario",
        resource_id=str(scenario_id),
        metadata=payload.model_dump(exclude_unset=True),
    )
    await session.commit()
    return ScenarioOut.model_validate(updated)


@router.delete("/{scenario_id}", status_code=204)
async def delete_scenario(
    scenario_id: UUID,
    session: SessionDep,
    principal: ManagePrincipal,
) -> None:
    repo = ScenarioRepository(session)
    scenario = await repo.get(scenario_id)
    if scenario is None:
        raise NotFoundError(f"Scenario {scenario_id} not found")

    await repo.delete(scenario)
    await audit(
        session,
        principal,
        "scenario.deleted",
        resource_type="scenario",
        resource_id=str(scenario_id),
    )
    await session.commit()



@router.get("/{scenario_id}/history", response_model=list[ScenarioAssessmentOut])
async def get_scenario_history(
    scenario_id: UUID,
    session: SessionDep,
    _principal: ReadPrincipal,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[ScenarioAssessmentOut]:
    repo = ScenarioRepository(session)
    if await repo.get(scenario_id) is None:
        raise NotFoundError(f"Scenario {scenario_id} not found")
    assessments = await repo.list_assessments(
        scenario_id, since=since, until=until, limit=limit, offset=offset
    )
    return [ScenarioAssessmentOut.from_domain(a) for a in assessments]


@router.post("", response_model=ScenarioOut, status_code=201)
async def create_scenario(
    payload: CreateScenarioRequest, session: SessionDep, principal: ManagePrincipal
) -> ScenarioOut:
    scenario = await ScenarioEngine(session).create_scenario(**payload.model_dump())
    await audit(
        session,
        principal,
        "scenario.created",
        resource_type="scenario",
        resource_id=str(scenario.id),
    )
    return ScenarioOut.model_validate(scenario)


@router.post("/{scenario_id}/update", response_model=ScenarioAssessmentOut, status_code=201)
async def update_scenario(
    scenario_id: UUID, session: SessionDep, principal: ManagePrincipal
) -> ScenarioAssessmentOut:
    assessment = await ScenarioEngine(session).update_scenario(
        scenario_id, llm=_try_get_llm(), triggered_by=str(principal.user_id)
    )
    await audit(
        session,
        principal,
        "scenario.updated",
        resource_type="scenario",
        resource_id=str(scenario_id),
        metadata={"assessment_id": str(assessment.id)},
    )
    return ScenarioAssessmentOut.from_domain(assessment)


@router.post("/simulate", response_model=ScenarioUpdateRecommendation)
async def simulate_scenario(
    payload: ScenarioSimulationRequest, session: SessionDep, principal: ManagePrincipal
) -> ScenarioUpdateRecommendation:
    llm = _try_get_llm()
    if llm is None:
        raise LLMConfigurationError("Scenario simulation requires a configured LLM provider")

    result = await ScenarioEngine(session).simulate(
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        scenario_family=payload.scenario_family,
        time_horizon=payload.time_horizon,
        hypothetical_context=payload.hypothetical_context,
        llm=llm,
    )
    await audit(
        session,
        principal,
        "scenario.simulated",
        resource_type="scenario_family",
        resource_id=str(payload.scenario_family),
        metadata={"scope_type": str(payload.scope_type)},
    )
    return result
