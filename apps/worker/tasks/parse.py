import asyncio
from uuid import UUID

from mei.infrastructure.collection.dedup import compute_fingerprint
from mei.infrastructure.collection.parser import PARSER_VERSION, chunk_text, extract_text
from mei.infrastructure.database.session import get_session_factory
from mei.infrastructure.object_storage.client import ObjectStorage
from mei.infrastructure.repositories.documents import DocumentRepository
from mei.shared.logging import get_logger

logger = get_logger(__name__)


def parse_document(document_id: str) -> None:
    """Re-run extraction for an already-archived document.

    Phase 1's manual submission path (`SourceIngestionService.submit_url`)
    fetches, archives, and parses inline within the API request, so this
    task isn't on that path. It exists for reprocessing bytes already
    sitting in object storage without re-fetching — e.g. a new parser
    version, or a previously failed extraction.
    """
    asyncio.run(_parse_document_async(document_id))


async def _parse_document_async(document_id: str) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        documents = DocumentRepository(session)
        document = await documents.get(UUID(document_id))
        if document is None:
            logger.warning("parse.document_not_found", document_id=document_id)
            return
        if document.raw_object_key is None:
            logger.warning("parse.no_raw_object", document_id=document_id)
            return

        body = await ObjectStorage().get_bytes(document.raw_object_key)
        extracted = extract_text(body, url=document.canonical_url)
        if not extracted:
            logger.info("parse.no_extractable_text", document_id=document_id)
            return

        fingerprint = compute_fingerprint(extracted)
        await documents.mark_parsed(
            document,
            extracted_text=extracted,
            parser_version=PARSER_VERSION,
            content_fingerprint=fingerprint,
        )

        await documents.clear_chunks(document.id)
        for sequence, chunk in enumerate(chunk_text(extracted)):
            await documents.add_chunk(
                document_id=document.id,
                sequence=sequence,
                text=chunk,
                token_count=len(chunk.split()),
            )

        await session.commit()
