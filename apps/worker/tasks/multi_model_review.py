import asyncio
from uuid import UUID

from apps.worker.celery_app import celery_app
from mei.application.services.multi_model_review import MultiModelReviewService
from mei.infrastructure.database.session import get_session_factory
from mei.infrastructure.llm.factory import get_secondary_structured_llm
from mei.shared.config import get_settings
from mei.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="apps.worker.tasks.multi_model_review.review_risk_assessment")
def review_risk_assessment(risk_assessment_id: str) -> None:
    """Shadow-rerun a high-impact risk assessment with a second configured
    model and record whether it agrees with the primary result."""
    asyncio.run(_review_risk_assessment_async(risk_assessment_id))


async def _review_risk_assessment_async(risk_assessment_id: str) -> None:
    secondary_llm = get_secondary_structured_llm()
    if secondary_llm is None:
        logger.info("multi_model_review.skipped_no_secondary_model", risk_assessment_id=risk_assessment_id)
        return

    settings = get_settings()
    session_factory = get_session_factory()
    async with session_factory() as session:
        review = await MultiModelReviewService(session).review_risk_assessment(
            UUID(risk_assessment_id),
            secondary_llm=secondary_llm,
            agreement_tolerance=settings.multi_model_review_agreement_tolerance,
        )
        await session.commit()

    logger.info(
        "multi_model_review.completed",
        risk_assessment_id=risk_assessment_id,
        agreement=review.agreement,
        agreement_delta=review.agreement_delta,
    )
