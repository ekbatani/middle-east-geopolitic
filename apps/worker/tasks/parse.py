from apps.worker.celery_app import celery_app
from mei.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="apps.worker.tasks.parse.parse_document")
def parse_document(document_id: str) -> None:
    """Extract normalized text from a document's archived raw bytes. Implemented in Phase 1."""
    logger.info("task.not_implemented", task="parse_document", document_id=document_id)
