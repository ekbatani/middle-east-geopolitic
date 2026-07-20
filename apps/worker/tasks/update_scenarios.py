from apps.worker.celery_app import celery_app
from mei.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="apps.worker.tasks.update_scenarios.evaluate_due_forecasts")
def evaluate_due_forecasts() -> None:
    """Score forecasts that have reached their resolution date. Implemented in Phase 4."""
    logger.info("task.not_implemented", task="evaluate_due_forecasts")


@celery_app.task(name="apps.worker.tasks.update_scenarios.update_scenario")
def update_scenario(scenario_id: str) -> None:
    """Re-evaluate a scenario's trigger and invalidation conditions. Implemented in Phase 4."""
    logger.info("task.not_implemented", task="update_scenario", scenario_id=scenario_id)
