from apps.worker.celery_app import celery_app
from mei.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="apps.worker.tasks.parse.parse_document")
def parse_document(document_id: str) -> None:
    """Re-run extraction for an already-archived document.

    Phase 1's manual submission path (`SourceIngestionService.submit_url`)
    fetches, archives, and parses inline within the API request, so this
    task isn't on that path yet. It exists for Phase 2, when a re-parse
    (new parser version, previously failed extraction) needs to run
    against bytes already sitting in object storage without re-fetching.
    """
    logger.info("task.not_implemented", task="parse_document", document_id=document_id)
