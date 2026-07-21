import hashlib
from datetime import datetime
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.documents.models import Document
from mei.domain.sources.models import Source
from mei.infrastructure.collection.dedup import compute_fingerprint
from mei.infrastructure.collection.http_fetcher import fetch_url, validate_url_security
from mei.infrastructure.collection.parser import PARSER_VERSION, chunk_text, extract_text
from mei.infrastructure.object_storage.client import ObjectStorage, build_raw_object_key
from mei.infrastructure.repositories.documents import DocumentRepository
from mei.infrastructure.repositories.sources import SourceRepository
from mei.shared.enums import EndpointType, SourceType
from mei.shared.errors import NotFoundError
from mei.shared.logging import get_logger
from mei.shared.time import utcnow

logger = get_logger(__name__)

CONTENT_TYPE_EXTENSIONS = {
    "text/html": "html",
    "application/xhtml+xml": "html",
    "text/plain": "txt",
    "application/xml": "xml",
    "text/xml": "xml",
    "application/rss+xml": "xml",
    "application/atom+xml": "xml",
}


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed._replace(fragment="").geturl()


class SourceIngestionService:
    """Manual source submission: fetch, archive, and parse one URL.

    Runs synchronously within the request for Phase 1 so submission results
    (archived bytes, extracted text) are immediately observable. The
    fetch/archive/parse steps are factored so apps/worker/tasks/collect.py
    and parse.py can call the same logic once Phase 2 moves this behind
    Celery for automated collection.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._sources = SourceRepository(session)
        self._documents = DocumentRepository(session)
        self._storage = ObjectStorage()

    async def submit_url(
        self,
        *,
        url: str,
        title: str | None = None,
        source_id: UUID | None = None,
        external_id: str | None = None,
        published_at: datetime | None = None,
    ) -> Document:
        canonical_url = _normalize_url(url)
        validate_url_security(canonical_url)

        source = await self._resolve_source(source_id=source_id, url=canonical_url)

        existing = await self._documents.find_by_canonical_url(source.id, canonical_url)
        if existing is not None:
            return existing

        document = await self._documents.create(
            source_id=source.id,
            canonical_url=canonical_url,
            title=title,
            external_id=external_id,
            published_at=published_at,
        )

        try:
            await self._fetch_archive_parse(document, canonical_url, source_id=source.id)
        except Exception:
            await self._documents.mark_failed(document)
            raise

        return document

    async def _resolve_source(self, *, source_id: UUID | None, url: str) -> Source:
        if source_id is not None:
            source = await self._sources.get(source_id)
            if source is None:
                raise NotFoundError(f"Source {source_id} not found")
            return source

        hostname = urlparse(url).hostname or "unknown"
        source = await self._sources.create(
            name=hostname,
            source_type=SourceType.OTHER,
            base_url=f"{urlparse(url).scheme}://{hostname}",
        )
        await self._sources.create_endpoint(
            source_id=source.id, endpoint_type=EndpointType.MANUAL, url=url
        )
        return source

    async def _fetch_archive_parse(self, document: Document, url: str, *, source_id: UUID) -> None:
        result = await fetch_url(url)
        content_hash = hashlib.sha256(result.body).hexdigest()
        extension = CONTENT_TYPE_EXTENSIONS.get(result.content_type, "bin")
        retrieved_at = utcnow()

        await self._storage.ensure_bucket()
        object_key = build_raw_object_key(
            source_id=source_id,
            document_id=document.id,
            content_hash=content_hash,
            extension=extension,
            retrieved_at=retrieved_at,
        )
        await self._storage.put_bytes(object_key, result.body, content_type=result.content_type)

        await self._documents.mark_fetched(
            document,
            raw_object_key=object_key,
            content_hash=content_hash,
            retrieved_at=retrieved_at,
        )

        # Dedup stage 3 (design doc section 11): raw content hash match.
        # Checked after archiving (original bytes are always kept, per
        # section 10.4) but before spending an extraction/LLM pass on it.
        hash_duplicate = await self._documents.find_by_content_hash(
            content_hash, exclude_document_id=document.id
        )
        if hash_duplicate is not None:
            await self._documents.mark_duplicate(document, duplicate_of_id=hash_duplicate.id)
            logger.info(
                "document.duplicate_content_hash",
                document_id=str(document.id),
                duplicate_of_document_id=str(hash_duplicate.id),
            )
            return

        extracted = extract_text(result.body, url=url)
        if not extracted:
            logger.info("document.no_extractable_text", document_id=str(document.id))
            return

        # Dedup stage 4: normalized text fingerprint match (catches
        # word-for-word republication under a different URL/content-hash,
        # e.g. wire-service syndication).
        fingerprint = compute_fingerprint(extracted)
        fingerprint_duplicate = await self._documents.find_by_fingerprint(
            fingerprint, exclude_document_id=document.id
        )

        await self._documents.mark_parsed(
            document,
            extracted_text=extracted,
            parser_version=PARSER_VERSION,
            content_fingerprint=fingerprint,
        )

        if fingerprint_duplicate is not None:
            await self._documents.mark_duplicate(document, duplicate_of_id=fingerprint_duplicate.id)
            logger.info(
                "document.duplicate_fingerprint",
                document_id=str(document.id),
                duplicate_of_document_id=str(fingerprint_duplicate.id),
            )
            return

        for sequence, chunk in enumerate(chunk_text(extracted)):
            await self._documents.add_chunk(
                document_id=document.id,
                sequence=sequence,
                text=chunk,
                token_count=len(chunk.split()),
            )


__all__ = ["SourceIngestionService"]
