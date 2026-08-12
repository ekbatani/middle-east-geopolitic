from mei.shared.logging import get_logger

logger = get_logger(__name__)


def reevaluate_unresolved_claims() -> None:
    """Re-run verification for claims not yet corroborated or contradicted. Implemented in Phase 2."""
    logger.info("task.not_implemented", task="reevaluate_unresolved_claims")


def verify_claim(claim_id: str) -> None:
    """Assess corroboration, contradiction, and source independence for one claim."""
    logger.info("task.not_implemented", task="verify_claim", claim_id=claim_id)
