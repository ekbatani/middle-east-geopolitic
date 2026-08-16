from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.scheduler import SchedulerService
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.collection.web_scraper import WebScraper
from mei.infrastructure.repositories.schedules import ScheduleRepository
from mei.shared.enums import Scope
from mei.shared.errors import NotFoundError

router = APIRouter(tags=["schedules"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
AdminPrincipal = Annotated[Principal, Depends(require_scopes(Scope.SOURCES_SUBMIT))]


class JobExecutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    schedule_id: UUID | None
    job_type: str
    started_at: datetime
    completed_at: datetime | None
    status: str
    items_processed: int
    error_message: str | None
    log_output: str | None


class JobScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    job_type: str
    cron_expression: str | None
    interval_seconds: int | None
    parameters: dict[str, Any]
    enabled: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    last_status: str | None
    executions: list[JobExecutionOut] = Field(default_factory=list)


class CreateJobScheduleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    job_type: str = Field(min_length=1, max_length=100)
    cron_expression: str | None = None
    interval_seconds: int | None = Field(default=86400, ge=30)
    parameters: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class UpdateJobScheduleRequest(BaseModel):
    name: str | None = None
    cron_expression: str | None = None
    interval_seconds: int | None = None
    parameters: dict[str, Any] | None = None
    enabled: bool | None = None


class TriggerJobResponse(BaseModel):
    success: bool
    job_type: str
    items_processed: int
    log_output: str


class TestScrapeRequest(BaseModel):
    url: HttpUrl


class TestScrapeResponse(BaseModel):
    url: str
    title: str | None
    extracted_text: str | None
    chunks_count: int
    detected_language: str | None
    status_code: int


@router.get("/schedules", response_model=list[JobScheduleOut])
async def list_schedules(
    session: SessionDep,
    _principal: ReadPrincipal,
    enabled_only: bool = Query(default=False),
) -> list[JobScheduleOut]:
    repo = ScheduleRepository(session)
    schedules = await repo.list_all(enabled_only=enabled_only)
    return [JobScheduleOut.model_validate(s) for s in schedules]


@router.post("/schedules", response_model=JobScheduleOut, status_code=201)
async def create_schedule(
    payload: CreateJobScheduleRequest,
    session: SessionDep,
    principal: AdminPrincipal,
) -> JobScheduleOut:
    repo = ScheduleRepository(session)
    schedule = await repo.create(
        name=payload.name,
        job_type=payload.job_type,
        cron_expression=payload.cron_expression,
        interval_seconds=payload.interval_seconds,
        parameters=payload.parameters,
        enabled=payload.enabled,
    )
    await audit(
        session,
        principal,
        "schedule.created",
        resource_type="schedule",
        resource_id=str(schedule.id),
        metadata={"name": payload.name, "job_type": payload.job_type},
    )
    await session.commit()
    # Refresh to load relationships
    created = await repo.get(schedule.id)
    return JobScheduleOut.model_validate(created)


@router.get("/schedules/executions", response_model=list[JobExecutionOut])
async def list_job_executions(
    session: SessionDep,
    _principal: ReadPrincipal,
    job_type: str | None = Query(default=None),
    schedule_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[JobExecutionOut]:
    repo = ScheduleRepository(session)
    executions = await repo.list_executions(
        job_type=job_type, schedule_id=schedule_id, limit=limit, offset=offset
    )
    return [JobExecutionOut.model_validate(e) for e in executions]


@router.get("/schedules/{schedule_id}", response_model=JobScheduleOut)
async def get_schedule(
    schedule_id: UUID,
    session: SessionDep,
    _principal: ReadPrincipal,
) -> JobScheduleOut:
    repo = ScheduleRepository(session)
    schedule = await repo.get(schedule_id)
    if schedule is None:
        raise NotFoundError(f"Schedule {schedule_id} not found")
    return JobScheduleOut.model_validate(schedule)


@router.patch("/schedules/{schedule_id}", response_model=JobScheduleOut)
async def update_schedule(
    schedule_id: UUID,
    payload: UpdateJobScheduleRequest,
    session: SessionDep,
    principal: AdminPrincipal,
) -> JobScheduleOut:
    repo = ScheduleRepository(session)
    schedule = await repo.get(schedule_id)
    if schedule is None:
        raise NotFoundError(f"Schedule {schedule_id} not found")

    updated = await repo.update(
        schedule,
        name=payload.name,
        cron_expression=payload.cron_expression,
        interval_seconds=payload.interval_seconds,
        parameters=payload.parameters,
        enabled=payload.enabled,
    )
    await audit(
        session,
        principal,
        "schedule.updated",
        resource_type="schedule",
        resource_id=str(schedule_id),
        metadata=payload.model_dump(exclude_unset=True),
    )
    await session.commit()
    refreshed = await repo.get(schedule.id)
    return JobScheduleOut.model_validate(refreshed)


@router.delete("/schedules/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: UUID,
    session: SessionDep,
    principal: AdminPrincipal,
) -> None:
    repo = ScheduleRepository(session)
    schedule = await repo.get(schedule_id)
    if schedule is None:
        raise NotFoundError(f"Schedule {schedule_id} not found")

    await repo.delete(schedule)
    await audit(
        session,
        principal,
        "schedule.deleted",
        resource_type="schedule",
        resource_id=str(schedule_id),
    )
    await session.commit()


@router.post("/schedules/{schedule_id}/run", response_model=TriggerJobResponse)
async def run_schedule_now(
    schedule_id: UUID,
    session: SessionDep,
    principal: AdminPrincipal,
) -> TriggerJobResponse:
    repo = ScheduleRepository(session)
    schedule = await repo.get(schedule_id)
    if schedule is None:
        raise NotFoundError(f"Schedule {schedule_id} not found")

    scheduler = SchedulerService.get_instance()
    success, items, logs = await scheduler.trigger_job_now(schedule_id)

    await audit(
        session,
        principal,
        "schedule.manual_run",
        resource_type="schedule",
        resource_id=str(schedule_id),
        metadata={"job_type": schedule.job_type, "items_processed": items},
    )

    return TriggerJobResponse(
        success=success,
        job_type=schedule.job_type,
        items_processed=items,
        log_output=logs,
    )


@router.post("/schedules/trigger-job/{job_type}", response_model=TriggerJobResponse)
async def trigger_job_by_type(
    job_type: str,
    session: SessionDep,
    principal: AdminPrincipal,
) -> TriggerJobResponse:
    scheduler = SchedulerService.get_instance()
    success, items, logs = await scheduler.trigger_by_type(job_type)

    await audit(
        session,
        principal,
        "schedule.job_triggered",
        resource_type="job",
        resource_id=job_type,
        metadata={"items_processed": items},
    )

    return TriggerJobResponse(
        success=success,
        job_type=job_type,
        items_processed=items,
        log_output=logs,
    )


@router.post("/schedules/test-scrape", response_model=TestScrapeResponse)
async def test_scrape_url(
    payload: TestScrapeRequest,
    _session: SessionDep,
    _principal: AdminPrincipal,
) -> TestScrapeResponse:
    scraper = WebScraper()
    result = await scraper.scrape_single_url(str(payload.url))
    return TestScrapeResponse(
        url=result.url,
        title=result.title,
        extracted_text=result.extracted_text[:2000] if result.extracted_text else None,
        chunks_count=len(result.chunks),
        detected_language=result.detected_language,
        status_code=result.status_code,
    )
