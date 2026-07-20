from apps.worker.celery_app import celery_app
from mei.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="apps.worker.tasks.dispatch_notifications.evaluate_monitors")
def evaluate_monitors() -> None:
    """Evaluate enabled monitors and enqueue notifications for triggered ones. Implemented in Phase 5."""
    logger.info("task.not_implemented", task="evaluate_monitors")


@celery_app.task(name="apps.worker.tasks.dispatch_notifications.send_notification")
def send_notification(notification_id: str) -> None:
    """Deliver a single notification on its configured channel."""
    logger.info("task.not_implemented", task="send_notification", notification_id=notification_id)
