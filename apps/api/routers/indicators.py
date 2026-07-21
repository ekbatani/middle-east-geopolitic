from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.indicators import IndicatorService
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.indicators import IndicatorRepository
from mei.shared.enums import IndicatorNormalizationMethod, Scope, ScopeType
from mei.shared.errors import NotFoundError

router = APIRouter(prefix="/indicators", tags=["indicators"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
RecordPrincipal = Annotated[Principal, Depends(require_scopes(Scope.ADMIN_CONFIGURATION))]


class IndicatorDefinitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str | None
    category: str
    value_type: str
    normalization_method: IndicatorNormalizationMethod
    lower_bound: float | None
    upper_bound: float | None
    staleness_hours: int | None
    active: bool


class IndicatorObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    indicator_id: UUID
    scope_type: ScopeType
    scope_id: UUID
    observed_at: datetime
    raw_value: float
    normalized_value: float
    confidence: float
    source_method: str | None


class RecordObservationRequest(BaseModel):
    scope_type: ScopeType
    scope_id: UUID
    raw_value: float
    confidence: float = Field(default=1.0, ge=0, le=1)
    observed_at: datetime | None = None
    source_method: str | None = None


@router.get("", response_model=list[IndicatorDefinitionOut])
async def list_indicators(
    session: SessionDep, _principal: ReadPrincipal, active_only: bool = True
) -> list[IndicatorDefinitionOut]:
    definitions = await IndicatorRepository(session).list_definitions(active_only=active_only)
    return [IndicatorDefinitionOut.model_validate(d) for d in definitions]


@router.get("/{indicator_code}/observations", response_model=list[IndicatorObservationOut])
async def list_indicator_observations(
    indicator_code: str,
    session: SessionDep,
    _principal: ReadPrincipal,
    scope_type: ScopeType,
    scope_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[IndicatorObservationOut]:
    repo = IndicatorRepository(session)
    definition = await repo.get_definition_by_code(indicator_code)
    if definition is None:
        raise NotFoundError(f"Indicator '{indicator_code}' not found")
    observations = await repo.list_observations(
        indicator_id=definition.id, scope_type=scope_type, scope_id=scope_id, limit=limit
    )
    return [IndicatorObservationOut.model_validate(o) for o in observations]


@router.post(
    "/{indicator_code}/observations", response_model=IndicatorObservationOut, status_code=201
)
async def record_indicator_observation(
    indicator_code: str,
    payload: RecordObservationRequest,
    session: SessionDep,
    principal: RecordPrincipal,
) -> IndicatorObservationOut:
    observation = await IndicatorService(session).record_observation(
        indicator_code=indicator_code, **payload.model_dump()
    )
    await audit(
        session,
        principal,
        "indicator.observation_recorded",
        resource_type="indicator",
        resource_id=indicator_code,
    )
    return IndicatorObservationOut.model_validate(observation)
