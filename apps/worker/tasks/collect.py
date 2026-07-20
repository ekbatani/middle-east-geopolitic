from apps.worker.celery_app import celery_app
from mei.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="apps.worker.tasks.collect.collect_critical_feeds")
def collect_critical_feeds() -> None:
    """Poll high-priority source endpoints. Implemented in Phase 2."""
    logger.info("task.not_implemented", task="collect_critical_feeds")


@celery_app.task(name="apps.worker.tasks.collect.collect_normal_feeds")
def collect_normal_feeds() -> None:
    """Poll standard-priority source endpoints. Implemented in Phase 2."""
    logger.info("task.not_implemented", task="collect_normal_feeds")


@celery_app.task(name="apps.worker.tasks.collect.retry_failed_endpoints")
def retry_failed_endpoints() -> None:
    """Retry source endpoints above the configured failure threshold. Implemented in Phase 2."""
    logger.info("task.not_implemented", task="retry_failed_endpoints")


@celery_app.task(name="apps.worker.tasks.collect.audit_source_failures")
def audit_source_failures() -> None:
    """Summarize source-endpoint reliability. Implemented in Phase 2."""
    logger.info("task.not_implemented", task="audit_source_failures")


@celery_app.task(name="apps.worker.tasks.collect.archive_old_raw_data")
def archive_old_raw_data() -> None:
    """Tier or archive aged raw object-storage data. Implemented in Phase 2."""
    logger.info("task.not_implemented", task="archive_old_raw_data")


@celery_app.task(name="apps.worker.tasks.collect.fetch_and_archive_document")
def fetch_and_archive_document(source_endpoint_id: str, url: str) -> None:
    """Fetch a single URL under the SSRF-safe HTTP policy and archive raw bytes.

    Triggered on manual submission and by the polling tasks above.
    Implemented in Phase 1/2.
    """
    logger.info(
        "task.not_implemented",
        task="fetch_and_archive_document",
        source_endpoint_id=source_endpoint_id,
        url=url,
    )
