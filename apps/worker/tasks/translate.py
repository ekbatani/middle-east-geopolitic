from apps.worker.celery_app import celery_app
from mei.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="apps.worker.tasks.translate.translate_document")
def translate_document(document_id: str) -> None:
    """Translate a document's normalized text when required. Implemented in Phase 2."""
    logger.info("task.not_implemented", task="translate_document", document_id=document_id)
