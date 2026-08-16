from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.calibration import CalibrationService
from mei.application.services.forecast_audit import ForecastAuditService
from mei.domain.forecasts.models import ForecastRecord
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.forecasts import ForecastRepository
from mei.shared.enums import ForecastOutcome, ForecastStatus, Scope
from mei.shared.errors import NotFoundError

router = APIRouter(prefix="/forecasts", tags=["forecasts"])

# Forecast issuance/resolution has no dedicated scope in design doc section
# 26.2; both are analytical-output actions like report generation/approval,
# so they reuse those scopes rather than inventing new ones.
ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
IssuePrincipal = Annotated[Principal, Depends(require_scopes(Scope.REPORTS_GENERATE))]
ResolvePrincipal = Annotated[Principal, Depends(require_scopes(Scope.REPORTS_APPROVE))]


class ForecastOut(BaseModel):
    id: UUID
    question: str
    issued_at: datetime
    resolution_date: date
    probability: float
    confidence: float
    assumptions: list[str]
    evidence_bundle_id: UUID | None
    status: ForecastStatus
    outcome: ForecastOutcome | None
    resolved_at: datetime | None
    brier_score: float | None
    evaluation_note: str | None

    @classmethod
    def from_domain(cls, forecast: ForecastRecord) -> "ForecastOut":
        return cls(
            id=forecast.id,
            question=forecast.question,
            issued_at=forecast.issued_at,
            resolution_date=forecast.resolution_date,
            probability=forecast.probability,
            confidence=forecast.confidence,
            assumptions=list(forecast.assumptions_json),
            evidence_bundle_id=forecast.evidence_bundle_id,
            status=forecast.status,
            outcome=forecast.outcome,
            resolved_at=forecast.resolved_at,
            brier_score=forecast.brier_score,
            evaluation_note=forecast.evaluation_note,
        )


class IssueForecastRequest(BaseModel):
    question: str = Field(min_length=1)
    resolution_date: date
    probability: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    assumptions: list[str] = Field(default_factory=list)
    evidence_bundle_id: UUID | None = None


class ResolveForecastRequest(BaseModel):
    outcome: ForecastOutcome
    evaluation_note: str | None = None


@router.get("", response_model=list[ForecastOut])
async def list_forecasts(
    session: SessionDep,
    _principal: ReadPrincipal,
    status: ForecastStatus | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[ForecastOut]:
    forecasts = await ForecastRepository(session).list_all(
        status=status, limit=limit, offset=offset
    )
    return [ForecastOut.from_domain(f) for f in forecasts]


class CalibrationBucketOut(BaseModel):
    lower: float
    upper: float
    forecast_count: int
    mean_predicted_probability: float | None
    observed_frequency: float | None
    mean_brier_score: float | None


class CalibrationReportOut(BaseModel):
    overall_brier_score: float | None
    resolved_count: int
    open_count: int
    buckets: list[CalibrationBucketOut]


@router.get("/calibration", response_model=CalibrationReportOut)
async def get_calibration(
    session: SessionDep,
    _principal: ReadPrincipal,
    since: datetime | None = None,
    until: datetime | None = None,
    bucket_count: int = Query(default=10, ge=1, le=100),
) -> CalibrationReportOut:
    report = await CalibrationService(session).compute_reliability(
        since=since, until=until, bucket_count=bucket_count
    )
    return CalibrationReportOut(
        overall_brier_score=report["overall_brier_score"],
        resolved_count=report["resolved_count"],
        open_count=report["open_count"],
        buckets=[CalibrationBucketOut(**bucket) for bucket in report["buckets"]],
    )


@router.get("/{forecast_id}", response_model=ForecastOut)
async def get_forecast(
    forecast_id: UUID, session: SessionDep, _principal: ReadPrincipal
) -> ForecastOut:
    forecast = await ForecastRepository(session).get(forecast_id)
    if forecast is None:
        raise NotFoundError(f"Forecast {forecast_id} not found")
    return ForecastOut.from_domain(forecast)


@router.post("", response_model=ForecastOut, status_code=201)
async def issue_forecast(
    payload: IssueForecastRequest, session: SessionDep, principal: IssuePrincipal
) -> ForecastOut:
    forecast = await ForecastAuditService(session).issue_forecast(**payload.model_dump())
    await audit(
        session,
        principal,
        "forecast.issued",
        resource_type="forecast_record",
        resource_id=str(forecast.id),
    )
    return ForecastOut.from_domain(forecast)


@router.post("/{forecast_id}/resolve", response_model=ForecastOut)
async def resolve_forecast(
    forecast_id: UUID,
    payload: ResolveForecastRequest,
    session: SessionDep,
    principal: ResolvePrincipal,
) -> ForecastOut:
    forecast = await ForecastAuditService(session).resolve_forecast(
        forecast_id, outcome=payload.outcome, evaluation_note=payload.evaluation_note
    )
    await audit(
        session,
        principal,
        "forecast.resolved",
        resource_type="forecast_record",
        resource_id=str(forecast_id),
        metadata={"outcome": str(payload.outcome)},
    )
    return ForecastOut.from_domain(forecast)


class UpdateForecastRequest(BaseModel):
    question: str | None = None
    probability: float | None = None
    confidence: float | None = None
    resolution_date: date | None = None
    status: ForecastStatus | None = None


@router.patch("/{forecast_id}", response_model=ForecastOut)
async def update_forecast(
    forecast_id: UUID,
    payload: UpdateForecastRequest,
    session: SessionDep,
    principal: IssuePrincipal,
) -> ForecastOut:
    repo = ForecastRepository(session)
    forecast = await repo.get(forecast_id)
    if forecast is None:
        raise NotFoundError(f"Forecast {forecast_id} not found")

    updated = await repo.update(
        forecast,
        question=payload.question,
        probability=payload.probability,
        confidence=payload.confidence,
        resolution_date=payload.resolution_date,
        status=payload.status,
    )
    await audit(
        session,
        principal,
        "forecast.updated",
        resource_type="forecast_record",
        resource_id=str(forecast_id),
        metadata=payload.model_dump(exclude_unset=True),
    )
    await session.commit()
    return ForecastOut.from_domain(updated)


@router.delete("/{forecast_id}", status_code=204)
async def delete_forecast(
    forecast_id: UUID,
    session: SessionDep,
    principal: IssuePrincipal,
) -> None:
    repo = ForecastRepository(session)
    forecast = await repo.get(forecast_id)
    if forecast is None:
        raise NotFoundError(f"Forecast {forecast_id} not found")

    await repo.delete(forecast)
    await audit(
        session,
        principal,
        "forecast.deleted",
        resource_type="forecast_record",
        resource_id=str(forecast_id),
    )
    await session.commit()

