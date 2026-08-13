import asyncio
from uuid import UUID

from mei.application.services.forecast_audit import ForecastAuditService
from mei.application.services.scenario_engine import ScenarioEngine
from mei.infrastructure.database.session import get_session_factory
from mei.infrastructure.llm.factory import get_structured_llm
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.shared.errors import LLMConfigurationError
from mei.shared.logging import get_logger

logger = get_logger(__name__)


def _try_get_llm() -> StructuredLLM | None:
    try:
        return get_structured_llm()
    except LLMConfigurationError:
        return None


def evaluate_due_forecasts() -> None:
    """Surface forecasts past their resolution date that are still open.

    Resolution itself stays a human action (design doc section 13.4:
    determining a real-world outcome isn't something to automate) — this
    job only logs which forecasts need an analyst's `POST
    /forecasts/{id}/resolve` call, matching design doc section 24.1's
    "Evaluate due forecasts" schedule entry.
    """
    asyncio.run(_evaluate_due_forecasts_async())


async def _evaluate_due_forecasts_async() -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        due = await ForecastAuditService(session).list_due()

    logger.info(
        "update_scenarios.forecasts_due_for_review",
        count=len(due),
        forecast_ids=[str(f.id) for f in due],
    )


def update_scenario(scenario_id: str) -> None:
    """Re-evaluate one scenario's trigger and invalidation conditions
    (design doc section 19.2), persisting a new `ScenarioAssessment`."""
    asyncio.run(_update_scenario_async(scenario_id))


async def _update_scenario_async(scenario_id: str) -> None:
    session_factory = get_session_factory()
    llm = _try_get_llm()

    async with session_factory() as session:
        assessment = await ScenarioEngine(session).update_scenario(
            UUID(scenario_id), llm=llm, triggered_by="scheduler"
        )
        await session.commit()

    logger.info(
        "update_scenarios.scenario_updated",
        scenario_id=scenario_id,
        assessment_id=str(assessment.id),
        probability_low=assessment.probability_low,
        probability_high=assessment.probability_high,
    )
