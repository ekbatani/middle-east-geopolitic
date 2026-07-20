from apps.worker.celery_app import celery_app
from mei.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="apps.worker.tasks.extract.extract_claims_and_events")
def extract_claims_and_events(document_id: str) -> None:
    """Run structured LLM extraction of candidate claims and events. Implemented in Phase 2."""
    logger.info("task.not_implemented", task="extract_claims_and_events", document_id=document_id)
