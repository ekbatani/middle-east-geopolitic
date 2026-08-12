import asyncio
from uuid import UUID

from mei.application.services.report_generator import ReportGenerator
from mei.infrastructure.database.session import get_session_factory
from mei.infrastructure.llm.factory import get_structured_llm
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.shared.enums import ReportType, ScopeType
from mei.shared.errors import LLMConfigurationError
from mei.shared.logging import get_logger

logger = get_logger(__name__)


def _try_get_llm() -> StructuredLLM | None:
    try:
        return get_structured_llm()
    except LLMConfigurationError:
        return None


def generate_daily_brief() -> None:
    """Generate the daily brief report (design doc section 24.1/25.3)."""
    asyncio.run(_generate_async(ReportType.DAILY_BRIEF))


def generate_weekly_outlook() -> None:
    """Generate the weekly outlook report (design doc section 24.1)."""
    asyncio.run(_generate_async(ReportType.WEEKLY_OUTLOOK))


def generate_report(report_type: str, scope_type: str | None, scope_id: str | None) -> None:
    """Generate a single report of the given type and scope."""
    asyncio.run(
        _generate_async(
            ReportType(report_type),
            scope_type=ScopeType(scope_type) if scope_type else None,
            scope_id=UUID(scope_id) if scope_id else None,
        )
    )


async def _generate_async(
    report_type: ReportType,
    *,
    scope_type: ScopeType | None = None,
    scope_id: UUID | None = None,
) -> None:
    session_factory = get_session_factory()
    llm = _try_get_llm()

    async with session_factory() as session:
        report = await ReportGenerator(session).generate(
            report_type,
            scope_type=scope_type,
            scope_id=scope_id,
            llm=llm,
            triggered_by="scheduler",
        )
        await session.commit()

    logger.info(
        "generate_reports.report_generated",
        report_id=str(report.id),
        report_type=str(report_type),
    )
