import asyncio
from uuid import UUID

from apps.worker.celery_app import celery_app
from mei.application.services.source_ingestion import SourceIngestionService
from mei.infrastructure.database.session import get_session_factory
from mei.infrastructure.repositories.sources import SourceRepository
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

    Wraps the same `SourceIngestionService` the manual `/sources/submit` API
    endpoint calls synchronously, so an automated Phase 2 poller can enqueue
    this task instead once endpoint discovery lands.
    """
    asyncio.run(_fetch_and_archive_document_async(source_endpoint_id, url))


async def _fetch_and_archive_document_async(source_endpoint_id: str, url: str) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        endpoint = await SourceRepository(session).get_endpoint(UUID(source_endpoint_id))
        if endpoint is None:
            logger.warning("collect.endpoint_not_found", source_endpoint_id=source_endpoint_id)
            return

        await SourceIngestionService(session).submit_url(url=url, source_id=endpoint.source_id)
        await session.commit()
