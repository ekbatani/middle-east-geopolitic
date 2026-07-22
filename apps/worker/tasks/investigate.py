import asyncio
from uuid import UUID

from apps.worker.celery_app import celery_app
from mei.application.services.investigations import InvestigationService
from mei.infrastructure.database.session import get_session_factory
from mei.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="apps.worker.tasks.investigate.run_investigation")
def run_investigation(investigation_id: str) -> None:
    """Run an investigation state machine steps."""
    asyncio.run(_run_investigation_async(investigation_id))


async def _run_investigation_async(investigation_id: str) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = InvestigationService(session)
        await service.execute_investigation(UUID(investigation_id))
        await session.commit()
