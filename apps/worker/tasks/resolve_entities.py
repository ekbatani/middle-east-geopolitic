import asyncio
import json
from uuid import UUID

from apps.worker.celery_app import celery_app
from mei.application.services.entity_resolution import EntityResolutionService
from mei.infrastructure.database.session import get_session_factory
from mei.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="apps.worker.tasks.resolve_entities.resolve_candidate_actor")
def resolve_candidate_actor(candidate_name: str, context_json: str) -> None:
    """Standalone re-resolution of one actor mention against `EntityResolutionService`.

    `context_json` is a JSON object: `{"role", "target_type", "target_id",
    "document_id"?}`, matching the fields `ReviewItem.subject_json` uses
    (see `EntityResolutionService.resolve`).

    The extraction pipeline itself resolves actors inline, within the same
    transaction that creates the claim/event referencing them, rather than
    dispatching here — so the link and the record it belongs to commit
    atomically. This task is for standalone re-resolution against an
    already-existing target, e.g. after alias data changes.
    """
    asyncio.run(_resolve_candidate_actor_async(candidate_name, context_json))


async def _resolve_candidate_actor_async(candidate_name: str, context_json: str) -> None:
    context = json.loads(context_json)
    session_factory = get_session_factory()

    async with session_factory() as session:
        outcome = await EntityResolutionService(session).resolve(
            candidate_name,
            role=context["role"],
            target_type=context["target_type"],
            target_id=UUID(context["target_id"]),
            document_id=UUID(context["document_id"]) if context.get("document_id") else None,
        )
        await session.commit()

    logger.info(
        "resolve_entities.resolved",
        candidate_name=candidate_name,
        actor_id=str(outcome.actor_id) if outcome.actor_id else None,
        review_item_id=str(outcome.review_item_id) if outcome.review_item_id else None,
    )
