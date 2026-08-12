import asyncio
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.imagery.models import ImageEvidence
from mei.infrastructure.database.session import get_session_factory
from mei.infrastructure.llm.factory import get_structured_llm
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.infrastructure.object_storage.client import ObjectStorage
from mei.infrastructure.repositories.imagery import ImageryRepository
from mei.shared.enums import VerificationStatus
from mei.shared.errors import LLMConfigurationError, LLMOutputError
from mei.shared.logging import get_logger

logger = get_logger(__name__)

PROMPT_TASK_NAME = "imagery_analysis"
PROMPT_VERSION = "imagery_analyze_v1"


class ImageAnalysisResult(BaseModel):
    """Design doc section 35, Phase 6 "imagery evidence" vision-model output."""

    description: str
    notable_features: list[str] = Field(default_factory=list)
    possible_manipulation_indicators: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


def analyze_image(image_id: str) -> None:
    """Run the vision-model analysis pass over a submitted image."""
    asyncio.run(_analyze_image_async(image_id))


async def analyze_image_with_session(
    session: AsyncSession, image_id: str, *, llm: StructuredLLM
) -> ImageEvidence | None:
    """The actual analysis logic, taking an explicit session so it's
    directly callable from tests the same way application services are
    (see `mei.application.services.imagery_ingestion`). The Celery task
    wraps this with a session sourced from `get_session_factory()`; it
    isn't inlined into `_analyze_image_async` so a test can supply its own
    session/LLM instead of relying on the process-wide cached engine.
    Returns `None` (no-op) if the image no longer exists or the LLM
    produced no usable output.
    """
    images = ImageryRepository(session)
    image = await images.get(UUID(image_id))
    if image is None:
        logger.warning("imagery.analysis_target_not_found", image_id=image_id)
        return None

    raw_bytes = await ObjectStorage().get_bytes(image.object_key)

    try:
        result = await llm.generate_structured_from_image(
            task_name=PROMPT_TASK_NAME,
            prompt_version=PROMPT_VERSION,
            image_bytes=raw_bytes,
            content_type=image.content_type,
            output_model=ImageAnalysisResult,
            metadata={"image_id": image_id},
        )
    except LLMOutputError as exc:
        logger.warning("imagery.analysis_failed", image_id=image_id, error=str(exc))
        return None

    return await images.set_analysis(
        image,
        analysis_json=result.model_dump(),
        confidence=result.confidence,
        verification_status=VerificationStatus.SINGLE_SOURCE,
    )


async def _analyze_image_async(image_id: str) -> None:
    try:
        llm = get_structured_llm()
    except LLMConfigurationError:
        logger.info("imagery.analysis_skipped_no_llm", image_id=image_id)
        return

    session_factory = get_session_factory()
    async with session_factory() as session:
        updated = await analyze_image_with_session(session, image_id, llm=llm)
        if updated is not None:
            await session.commit()

    logger.info("imagery.analysis_completed", image_id=image_id)
