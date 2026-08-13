import asyncio
from uuid import UUID

from mei.infrastructure.database.session import get_session_factory
from mei.infrastructure.repositories.documents import DocumentRepository
from mei.infrastructure.translation.language_detection import detect_language
from mei.infrastructure.translation.translator import LLMTranslator
from mei.shared.config import get_settings
from mei.shared.errors import LLMConfigurationError
from mei.shared.logging import get_logger
from mei.shared.time import utcnow

logger = get_logger(__name__)


def translate_document(document_id: str) -> None:
    """Detect language and translate a document's text when required (section 10.6)."""
    asyncio.run(_translate_document_async(document_id))


async def _translate_document_async(document_id: str) -> None:
    settings = get_settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        documents = DocumentRepository(session)
        document = await documents.get(UUID(document_id))
        if document is None:
            logger.warning("translate.document_not_found", document_id=document_id)
            return
        if not document.extracted_text:
            logger.info("translate.no_text", document_id=document_id)
            return

        language = document.original_language
        if language is None:
            language = detect_language(document.extracted_text)
            if language is not None:
                await documents.set_language(document, language=language)

        target = settings.translation_target_language
        if language is not None and language != target:
            try:
                translator = LLMTranslator()
            except LLMConfigurationError:
                # No LLM configured: proceed with the original-language text
                # rather than failing the whole collection pipeline.
                logger.info("translate.skipped_no_llm_configured", document_id=document_id)
            else:
                translation = await translator.translate(
                    document.extracted_text, source_language=language, target_language=target
                )
                await documents.set_translation(
                    document,
                    translation_text=translation,
                    metadata={
                        "provider": settings.llm_provider,
                        "model": settings.llm_model,
                        "source_language": language,
                        "target_language": target,
                        "translated_at": utcnow().isoformat(),
                    },
                )

        await session.commit()

    _chain_extraction(document_id)


def _chain_extraction(document_id: str) -> None:
    from apps.worker.tasks.extract import _extract_claims_and_events_async

    asyncio.create_task(_extract_claims_and_events_async(document_id))
