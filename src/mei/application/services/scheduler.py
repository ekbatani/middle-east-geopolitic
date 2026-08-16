from __future__ import annotations

import asyncio
import contextlib
from datetime import timedelta
from typing import Any
from uuid import UUID

from mei.application.services.pipeline_jobs import PipelineJobExecutor
from mei.domain.schedules.models import JobSchedule
from mei.infrastructure.database.session import get_session_factory
from mei.infrastructure.repositories.schedules import ScheduleRepository
from mei.shared.logging import get_logger
from mei.shared.time import utcnow

logger = get_logger(__name__)


class SchedulerService:
    """Asynchronous background scheduler for intelligence scraping, extraction, and analysis pipelines."""

    _instance: SchedulerService | None = None

    def __init__(self) -> None:
        self._running = False
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._background_tasks: set[asyncio.Task[Any]] = set()
        self._session_factory = get_session_factory()

    @classmethod
    def get_instance(cls) -> SchedulerService:
        if cls._instance is None:
            cls._instance = SchedulerService()
        return cls._instance

    async def start(self) -> None:
        """Start the background scheduler loop."""
        if self._running:
            return
        self._running = True
        self._tasks["main_loop"] = asyncio.create_task(self._main_scheduler_loop())
        logger.info("scheduler.started")

    async def stop(self) -> None:
        """Stop all scheduler background tasks."""
        self._running = False
        for _name, task in list(self._tasks.items()):
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._tasks.clear()
        logger.info("scheduler.stopped")

    async def trigger_job_now(self, schedule_id: UUID) -> tuple[bool, int, str]:
        """Trigger an immediate execution of a scheduled job."""
        async with self._session_factory() as session:
            repo = ScheduleRepository(session)
            schedule = await repo.get(schedule_id)
            if schedule is None:
                raise ValueError(f"Schedule {schedule_id} not found")

            return await self._execute_schedule(session, schedule)

    async def trigger_by_type(self, job_type: str) -> tuple[bool, int, str]:
        """Trigger an immediate execution of a job type."""
        async with self._session_factory() as session:
            repo = ScheduleRepository(session)
            schedule = await repo.get_by_job_type(job_type)
            if schedule is None:
                # Execute ad-hoc without schedule record
                executor = PipelineJobExecutor(session)
                items, logs = await executor.run_job(job_type)
                return True, items, logs

            return await self._execute_schedule(session, schedule)

    async def _execute_schedule(self, session: Any, schedule: JobSchedule) -> tuple[bool, int, str]:
        repo = ScheduleRepository(session)
        now = utcnow()
        execution = await repo.create_execution(
            schedule_id=schedule.id,
            job_type=schedule.job_type,
            started_at=now,
            status="running",
        )
        await repo.update(schedule, last_status="running", last_run_at=now)
        await session.commit()

        success = True
        error_msg: str | None = None
        items_processed = 0
        log_output = ""

        try:
            executor = PipelineJobExecutor(session)
            items_processed, log_output = await executor.run_job(
                schedule.job_type, parameters=schedule.parameters
            )
        except Exception as exc:
            success = False
            error_msg = str(exc)
            logger.error("scheduler.execution_failed", schedule_id=str(schedule.id), error=str(exc))

        completed_at = utcnow()
        interval = schedule.interval_seconds or 86400  # default 1 day
        next_run = completed_at + timedelta(seconds=interval)

        await repo.update_execution(
            execution,
            completed_at=completed_at,
            status="success" if success else "failed",
            items_processed=items_processed,
            error_message=error_msg,
            log_output=log_output,
        )
        await repo.update(
            schedule,
            last_status="success" if success else "failed",
            last_run_at=now,
            next_run_at=next_run,
        )
        await session.commit()

        return success, items_processed, log_output

    async def _main_scheduler_loop(self) -> None:
        """Periodic loop that checks for due schedules and executes them."""
        # Initial wait so application finishes startup
        await asyncio.sleep(5)

        while self._running:
            try:
                now = utcnow()
                async with self._session_factory() as session:
                    repo = ScheduleRepository(session)
                    schedules = await repo.list_all(enabled_only=True)

                    for schedule in schedules:
                        is_due = False
                        if schedule.next_run_at is None or schedule.next_run_at <= now:
                            is_due = True

                        if is_due and schedule.last_status != "running":
                            logger.info(
                                "scheduler.schedule_due",
                                schedule_id=str(schedule.id),
                                name=schedule.name,
                                job_type=schedule.job_type,
                            )
                            # Run in background task so loop doesn't block
                            bg_task = asyncio.create_task(self._run_due_schedule_safe(schedule.id))
                            self._background_tasks.add(bg_task)
                            bg_task.add_done_callback(self._background_tasks.discard)

            except Exception as loop_err:
                logger.error("scheduler.loop_error", error=str(loop_err))

            # Sleep 30 seconds between schedule checks
            await asyncio.sleep(30)

    async def _run_due_schedule_safe(self, schedule_id: UUID) -> None:
        try:
            async with self._session_factory() as session:
                repo = ScheduleRepository(session)
                schedule = await repo.get(schedule_id)
                if schedule and schedule.enabled:
                    await self._execute_schedule(session, schedule)
        except Exception as exc:
            logger.error("scheduler.async_run_error", schedule_id=str(schedule_id), error=str(exc))


__all__ = ["SchedulerService"]
