from apps.worker.celery_app import celery_app
from mei.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="apps.worker.tasks.calculate_risks.recalculate_active_conflict_risks")
def recalculate_active_conflict_risks() -> None:
    """Recompute deterministic risk scores for scopes with recent activity. Implemented in Phase 3."""
    logger.info("task.not_implemented", task="recalculate_active_conflict_risks")


@celery_app.task(name="apps.worker.tasks.calculate_risks.refresh_country_indicators")
def refresh_country_indicators() -> None:
    """Refresh slow-moving country-level indicators. Implemented in Phase 3."""
    logger.info("task.not_implemented", task="refresh_country_indicators")


@celery_app.task(name="apps.worker.tasks.calculate_risks.calculate_risk_assessment")
def calculate_risk_assessment(risk_definition_id: str, scope_type: str, scope_id: str) -> None:
    """Compute one risk assessment: deterministic base plus bounded LLM adjustment."""
    logger.info(
        "task.not_implemented",
        task="calculate_risk_assessment",
        risk_definition_id=risk_definition_id,
        scope_type=scope_type,
        scope_id=scope_id,
    )
