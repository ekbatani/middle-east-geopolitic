from apps.worker.celery_app import celery_app
from mei.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="apps.worker.tasks.resolve_entities.resolve_candidate_actor")
def resolve_candidate_actor(candidate_name: str, context_json: str) -> None:
    """Resolve an extracted actor mention to a canonical actor. Implemented in Phase 2."""
    logger.info(
        "task.not_implemented", task="resolve_candidate_actor", candidate_name=candidate_name
    )
