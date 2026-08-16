from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mei.domain.schedules.models import JobExecution, JobSchedule
from mei.shared.time import utcnow


class ScheduleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, schedule_id: UUID) -> JobSchedule | None:
        result = await self._session.execute(
            select(JobSchedule)
            .where(JobSchedule.id == schedule_id)
            .options(selectinload(JobSchedule.executions))
        )
        return result.scalar_one_or_none()

    async def get_by_job_type(self, job_type: str) -> JobSchedule | None:
        result = await self._session.execute(
            select(JobSchedule)
            .where(JobSchedule.job_type == job_type)
            .options(selectinload(JobSchedule.executions))
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, enabled_only: bool = False) -> list[JobSchedule]:
        stmt = select(JobSchedule).options(selectinload(JobSchedule.executions)).order_by(JobSchedule.name)
        if enabled_only:
            stmt = stmt.where(JobSchedule.enabled.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().unique())

    async def create(
        self,
        *,
        name: str,
        job_type: str,
        cron_expression: str | None = None,
        interval_seconds: int | None = None,
        parameters: dict[str, Any] | None = None,
        enabled: bool = True,
    ) -> JobSchedule:
        schedule = JobSchedule(
            name=name,
            job_type=job_type,
            cron_expression=cron_expression,
            interval_seconds=interval_seconds,
            parameters=parameters or {},
            enabled=enabled,
        )
        self._session.add(schedule)
        await self._session.flush()
        return schedule

    async def update(
        self,
        schedule: JobSchedule,
        *,
        name: str | None = None,
        cron_expression: str | None = None,
        interval_seconds: int | None = None,
        parameters: dict[str, Any] | None = None,
        enabled: bool | None = None,
        last_run_at: datetime | None = None,
        next_run_at: datetime | None = None,
        last_status: str | None = None,
    ) -> JobSchedule:
        if name is not None:
            schedule.name = name
        if cron_expression is not None:
            schedule.cron_expression = cron_expression
        if interval_seconds is not None:
            schedule.interval_seconds = interval_seconds
        if parameters is not None:
            schedule.parameters = parameters
        if enabled is not None:
            schedule.enabled = enabled
        if last_run_at is not None:
            schedule.last_run_at = last_run_at
        if next_run_at is not None:
            schedule.next_run_at = next_run_at
        if last_status is not None:
            schedule.last_status = last_status
        await self._session.flush()
        return schedule

    async def delete(self, schedule: JobSchedule) -> None:
        await self._session.delete(schedule)
        await self._session.flush()

    async def create_execution(
        self,
        *,
        schedule_id: UUID | None,
        job_type: str,
        started_at: datetime | None = None,
        status: str = "running",
    ) -> JobExecution:
        execution = JobExecution(
            schedule_id=schedule_id,
            job_type=job_type,
            started_at=started_at or utcnow(),
            status=status,
        )
        self._session.add(execution)
        await self._session.flush()
        return execution

    async def update_execution(
        self,
        execution: JobExecution,
        *,
        completed_at: datetime | None = None,
        status: str | None = None,
        items_processed: int | None = None,
        error_message: str | None = None,
        log_output: str | None = None,
    ) -> JobExecution:
        if completed_at is not None:
            execution.completed_at = completed_at
        if status is not None:
            execution.status = status
        if items_processed is not None:
            execution.items_processed = items_processed
        if error_message is not None:
            execution.error_message = error_message
        if log_output is not None:
            execution.log_output = log_output
        await self._session.flush()
        return execution

    async def list_executions(
        self,
        *,
        job_type: str | None = None,
        schedule_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JobExecution]:
        stmt = select(JobExecution).order_by(desc(JobExecution.started_at)).limit(limit).offset(offset)
        if job_type:
            stmt = stmt.where(JobExecution.job_type == job_type)
        if schedule_id:
            stmt = stmt.where(JobExecution.schedule_id == schedule_id)
        result = await self._session.execute(stmt)
        return list(result.scalars())


__all__ = ["ScheduleRepository"]
