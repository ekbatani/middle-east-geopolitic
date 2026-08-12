import asyncio
from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.application.services.source_ingestion import SourceIngestionService
from mei.domain.sources.models import SourceEndpoint
from mei.infrastructure.collection.http_fetcher import fetch_url, validate_url_security
from mei.infrastructure.collection.rss import parse_feed
from mei.infrastructure.database.session import get_session_factory
from mei.infrastructure.repositories.documents import DocumentRepository
from mei.infrastructure.repositories.sources import SourceRepository
from mei.shared.config import get_settings
from mei.shared.enums import DocumentStatus, EndpointType
from mei.shared.errors import FetchError, UnsupportedURLError
from mei.shared.logging import get_logger
from mei.shared.time import utcnow

logger = get_logger(__name__)

# Endpoints that keep failing past this many consecutive attempts stop being
# retried automatically; audit_source_failures still surfaces them so a
# human notices instead of the collector hammering a dead source forever.
_CIRCUIT_BREAKER_FAILURE_COUNT = 10
_AUDIT_FAILURE_THRESHOLD = 5


def collect_critical_feeds() -> None:
    """Poll high-priority source endpoints (design doc section 24.1: every 10 minutes)."""
    asyncio.run(_collect_feeds_async(schedule="critical"))


def collect_normal_feeds() -> None:
    """Poll standard-priority source endpoints (design doc section 24.1: hourly)."""
    asyncio.run(_collect_feeds_async(schedule="normal"))


def retry_failed_endpoints() -> None:
    asyncio.run(_retry_failed_endpoints_async())


def audit_source_failures() -> None:
    asyncio.run(_audit_source_failures_async())


def archive_old_raw_data() -> None:
    """Report documents past the retention window.

    Actual storage-class tiering/deletion is an S3/MinIO lifecycle-policy
    concern, not app logic; this reports what's eligible so that policy can
    be sized and verified.
    """
    asyncio.run(_archive_old_raw_data_async())


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


async def _collect_feeds_async(*, schedule: str) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        endpoints = await SourceRepository(session).list_endpoints_due(
            endpoint_type=EndpointType.RSS, schedule=schedule
        )
        new_document_ids: list[UUID] = []
        for endpoint in endpoints:
            new_document_ids.extend(await _collect_endpoint(session, endpoint))
        await session.commit()

    _chain_translation(new_document_ids)
    logger.info(
        "collect.feeds_collected",
        schedule=schedule,
        endpoint_count=len(endpoints),
        new_document_count=len(new_document_ids),
    )


async def _collect_endpoint(session: AsyncSession, endpoint: SourceEndpoint) -> list[UUID]:
    if endpoint.endpoint_type != EndpointType.RSS:
        # Only RSS polling is automated in Phase 2; HTML/API endpoints still
        # rely on manual submission via POST /sources/submit.
        return []

    sources_repo = SourceRepository(session)
    try:
        validate_url_security(endpoint.url)
        feed_result = await fetch_url(endpoint.url)
    except (FetchError, UnsupportedURLError) as exc:
        await sources_repo.mark_endpoint_failure(endpoint, at=utcnow())
        logger.warning(
            "collect.endpoint_fetch_failed", endpoint_id=str(endpoint.id), error=str(exc)
        )
        return []

    await sources_repo.mark_endpoint_success(endpoint, at=utcnow())
    items = parse_feed(feed_result.body)

    documents_repo = DocumentRepository(session)
    ingestion = SourceIngestionService(session)
    new_document_ids: list[UUID] = []

    for item in items:
        if item.external_id is not None:
            existing = await documents_repo.find_by_external_id(
                endpoint.source_id, item.external_id
            )
            if existing is not None:
                continue

        document = await ingestion.submit_url(
            url=item.link,
            title=item.title,
            source_id=endpoint.source_id,
            external_id=item.external_id,
            published_at=item.published_at,
        )
        if document.status == DocumentStatus.PARSED and document.duplicate_of_document_id is None:
            new_document_ids.append(document.id)

    return new_document_ids


async def _retry_failed_endpoints_async() -> None:
    session_factory = get_session_factory()
    new_document_ids: list[UUID] = []
    retried = 0

    async with session_factory() as session:
        failing = await SourceRepository(session).list_failing_endpoints(min_failure_count=1)
        for endpoint in failing:
            if endpoint.failure_count > _CIRCUIT_BREAKER_FAILURE_COUNT:
                continue
            new_document_ids.extend(await _collect_endpoint(session, endpoint))
            retried += 1
        await session.commit()

    _chain_translation(new_document_ids)
    logger.info("collect.retry_failed_endpoints_done", retried=retried)


async def _audit_source_failures_async() -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        failing = await SourceRepository(session).list_failing_endpoints(
            min_failure_count=_AUDIT_FAILURE_THRESHOLD
        )
        for endpoint in failing:
            logger.warning(
                "collect.endpoint_failing",
                endpoint_id=str(endpoint.id),
                source_id=str(endpoint.source_id),
                url=endpoint.url,
                failure_count=endpoint.failure_count,
                last_failure_at=(
                    endpoint.last_failure_at.isoformat() if endpoint.last_failure_at else None
                ),
            )
    logger.info("collect.audit_source_failures_done", failing_count=len(failing))


async def _archive_old_raw_data_async() -> None:
    settings = get_settings()
    cutoff = utcnow() - timedelta(days=settings.raw_data_retention_days)
    session_factory = get_session_factory()
    async with session_factory() as session:
        eligible_count = await DocumentRepository(session).count_retrieved_before(cutoff)
    logger.info(
        "collect.archive_old_raw_data_report",
        cutoff=cutoff.isoformat(),
        retention_days=settings.raw_data_retention_days,
        eligible_document_count=eligible_count,
    )


def _chain_translation(document_ids: list[UUID]) -> None:
    from apps.worker.tasks.translate import _translate_document_async

    for document_id in document_ids:
        asyncio.create_task(_translate_document_async(str(document_id)))
