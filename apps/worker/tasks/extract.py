import asyncio
from uuid import UUID

from mei.application.services.extraction import ExtractionService
from mei.infrastructure.database.session import get_session_factory
from mei.infrastructure.llm.factory import get_structured_llm
from mei.infrastructure.repositories.documents import DocumentRepository
from mei.shared.logging import get_logger

logger = get_logger(__name__)


def extract_claims_and_events(document_id: str) -> None:
    """Run structured LLM extraction of candidate claims and events (sections 14, 15)."""
    asyncio.run(_extract_claims_and_events_async(document_id))


async def _extract_claims_and_events_async(document_id: str) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        document = await DocumentRepository(session).get(UUID(document_id))
        if document is None:
            logger.warning("extract.document_not_found", document_id=document_id)
            return
        if not (document.translation_text or document.extracted_text):
            logger.info("extract.no_text", document_id=document_id)
            return

        service = ExtractionService(session, get_structured_llm())
        result = await service.extract(document)
        await service.persist(document, result)
        await session.commit()

    logger.info(
        "extract.completed",
        document_id=document_id,
        claim_count=len(result.claims),
        event_count=len(result.events),
    )
