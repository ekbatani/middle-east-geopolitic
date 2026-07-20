from apps.worker.celery_app import celery_app
from mei.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="apps.worker.tasks.generate_reports.generate_daily_brief")
def generate_daily_brief() -> None:
    """Generate the daily brief report. Implemented in Phase 4."""
    logger.info("task.not_implemented", task="generate_daily_brief")


@celery_app.task(name="apps.worker.tasks.generate_reports.generate_weekly_outlook")
def generate_weekly_outlook() -> None:
    """Generate the weekly outlook report. Implemented in Phase 4."""
    logger.info("task.not_implemented", task="generate_weekly_outlook")


@celery_app.task(name="apps.worker.tasks.generate_reports.generate_report")
def generate_report(report_type: str, scope_type: str, scope_id: str | None) -> None:
    """Generate a single report of the given type and scope."""
    logger.info(
        "task.not_implemented",
        task="generate_report",
        report_type=report_type,
        scope_type=scope_type,
        scope_id=scope_id,
    )
