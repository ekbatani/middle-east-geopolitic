import asyncio
import operator as operator_module
from collections.abc import Callable
from uuid import UUID

from apps.worker.celery_app import celery_app
from mei.infrastructure.database.session import get_session_factory
from mei.infrastructure.messaging.telegram import TelegramClient
from mei.infrastructure.repositories.monitors import MonitorRepository
from mei.infrastructure.repositories.relationships import RelationshipRepository
from mei.infrastructure.repositories.risks import RiskRepository
from mei.shared.config import get_settings
from mei.shared.enums import ScopeType
from mei.shared.logging import get_logger
from mei.shared.time import utcnow

logger = get_logger(__name__)

_OPERATORS: dict[str, Callable[[float, float], bool]] = {
    ">": operator_module.gt,
    ">=": operator_module.ge,
    "<": operator_module.lt,
    "<=": operator_module.le,
    "==": operator_module.eq,
}


def evaluate_threshold(value: object, operator: str, threshold: object) -> bool:
    """Evaluate a monitor's `condition_json` comparison against an observed value.

    Kept as a standalone pure function (no DB/session access) so the
    comparison rules can be unit tested directly.
    """
    try:
        observed = float(value)  # type: ignore[arg-type]
        target = float(threshold)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return False

    comparator = _OPERATORS.get(operator)
    return comparator(observed, target) if comparator else False


@celery_app.task(name="apps.worker.tasks.dispatch_notifications.evaluate_monitors")
def evaluate_monitors() -> None:
    """Evaluate enabled monitors and enqueue notifications for triggered ones."""
    asyncio.run(_evaluate_monitors_async())


async def _evaluate_monitors_async() -> None:
    session_factory = get_session_factory()
    now = utcnow()

    async with session_factory() as session:
        monitor_repo = MonitorRepository(session)
        relationships_repo = RelationshipRepository(session)
        risks_repo = RiskRepository(session)

        monitors = await monitor_repo.list_all(enabled=True)
        for monitor in monitors:
            cond = monitor.condition_json
            triggered = False
            trigger_time = None
            title = ""
            body = ""

            try:
                if monitor.monitor_type == "relationship_threshold":
                    rel_id = cond.get("relationship_id")
                    field = cond.get("field", "escalation_risk_score")
                    op = cond.get("operator", ">=")
                    val = cond.get("value")

                    if rel_id and val is not None:
                        obs = await relationships_repo.get_latest_observation(UUID(str(rel_id)), as_of=now)
                        obs_val = getattr(obs, str(field), None) if obs else None
                        if (
                            obs is not None
                            and obs_val is not None
                            and evaluate_threshold(obs_val, str(op), val)
                            and (not monitor.last_triggered_at or obs.observed_at > monitor.last_triggered_at)
                        ):
                            triggered = True
                            trigger_time = obs.observed_at
                            title = f"Alert: Monitor '{monitor.name}' Triggered"
                            body = f"Relationship {rel_id} field '{field}' is {obs_val}, which violates the condition '{op} {val}'."

                elif monitor.monitor_type == "country_risk":
                    country_id = cond.get("country_actor_id")
                    risk_def_id = cond.get("risk_definition_id")
                    op = cond.get("operator", ">=")
                    val = cond.get("value")

                    if country_id and risk_def_id and val is not None:
                        assessment = await risks_repo.get_latest_assessment(
                            risk_definition_id=UUID(str(risk_def_id)),
                            scope_type=ScopeType.COUNTRY,
                            scope_id=UUID(str(country_id)),
                            as_of=now,
                        )
                        if assessment and evaluate_threshold(assessment.final_score, str(op), val) and (
                            not monitor.last_triggered_at
                            or assessment.assessed_at > monitor.last_triggered_at
                        ):
                            triggered = True
                            trigger_time = assessment.assessed_at
                            title = f"Alert: Monitor '{monitor.name}' Triggered"
                            body = f"Country {country_id} risk {risk_def_id} score is {assessment.final_score}, which violates the condition '{op} {val}'."

                if triggered:
                    notif = await monitor_repo.create_notification(
                        monitor_id=monitor.id,
                        report_id=None,
                        severity="warning",
                        title=title,
                        body=body,
                        delivery_channel=monitor.delivery_channel,
                    )
                    monitor.last_triggered_at = trigger_time or now
                    send_notification.delay(str(notif.id))

                monitor.last_evaluated_at = now

            except Exception as exc:
                logger.exception(
                    "dispatch_notifications.monitor_evaluation_failed",
                    monitor_id=str(monitor.id),
                    error=str(exc),
                )

        await session.commit()


@celery_app.task(name="apps.worker.tasks.dispatch_notifications.send_notification")
def send_notification(notification_id: str) -> None:
    """Deliver a single notification on its configured channel."""
    asyncio.run(_send_notification_async(notification_id))


async def _send_notification_async(notification_id: str) -> None:
    session_factory = get_session_factory()
    settings = get_settings()

    async with session_factory() as session:
        monitor_repo = MonitorRepository(session)
        notif = await monitor_repo.get_notification(UUID(notification_id))
        if not notif:
            logger.error("dispatch_notifications.not_found", notification_id=notification_id)
            return

        client = TelegramClient(
            bot_token=settings.telegram_bot_token,
            default_chat_id=settings.telegram_chat_id,
        )

        try:
            await client.send_message(f"[{notif.severity.upper()}] {notif.title}\n\n{notif.body}")
            notif.status = "sent"
            notif.sent_at = utcnow()
        except Exception as exc:
            notif.status = "failed"
            notif.error_message = str(exc)

        await session.commit()
