import asyncio
from uuid import UUID

from apps.worker.celery_app import celery_app
from mei.application.services.risk_engine import RiskEngine
from mei.infrastructure.database.session import get_session_factory
from mei.infrastructure.llm.factory import get_structured_llm
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.infrastructure.repositories.relationships import RelationshipRepository
from mei.infrastructure.repositories.risks import RiskRepository
from mei.shared.enums import RelationshipStatus, ScopeType
from mei.shared.errors import LLMConfigurationError
from mei.shared.logging import get_logger

logger = get_logger(__name__)


def _try_get_llm() -> StructuredLLM | None:
    try:
        return get_structured_llm()
    except LLMConfigurationError:
        return None


@celery_app.task(name="apps.worker.tasks.calculate_risks.recalculate_active_conflict_risks")
def recalculate_active_conflict_risks() -> None:
    """Recompute relationship-scoped risk scores for every active relationship."""
    asyncio.run(_recalculate_active_conflict_risks_async())


async def _recalculate_active_conflict_risks_async() -> None:
    session_factory = get_session_factory()
    llm = _try_get_llm()
    computed = 0

    async with session_factory() as session:
        risks = RiskRepository(session)
        relationships = RelationshipRepository(session)

        definitions = [
            d
            for d in await risks.list_definitions()
            if ScopeType.RELATIONSHIP.value in d.scope_types
        ]
        if not definitions:
            return

        active_relationships = await relationships.list_all(
            status=RelationshipStatus.ACTIVE, limit=1000
        )
        engine = RiskEngine(session)
        for relationship in active_relationships:
            for definition in definitions:
                await engine.calculate(
                    risk_definition_id=definition.id,
                    scope_type=ScopeType.RELATIONSHIP,
                    scope_id=relationship.id,
                    llm=llm,
                    triggered_by="scheduler",
                )
                computed += 1
        await session.commit()

    logger.info("calculate_risks.active_conflict_risks_recalculated", assessment_count=computed)


@celery_app.task(name="apps.worker.tasks.calculate_risks.refresh_country_indicators")
def refresh_country_indicators() -> None:
    """Pull slow-moving country-level indicator readings from external sources.

    No indicator-source collector exists yet (that's the Phase 6 "commercial
    maritime data" / external feed work) — country indicators are populated
    via `POST /indicators/{code}/observations` in Phase 3 instead. This job
    is a placeholder for when an automated feed lands.
    """
    logger.info("task.not_implemented", task="refresh_country_indicators")


@celery_app.task(name="apps.worker.tasks.calculate_risks.calculate_risk_assessment")
def calculate_risk_assessment(
    risk_definition_id: str, scope_type: str, scope_id: str | None
) -> None:
    """Compute one risk assessment: deterministic base plus bounded LLM adjustment."""
    asyncio.run(
        _calculate_risk_assessment_async(
            risk_definition_id=risk_definition_id, scope_type=scope_type, scope_id=scope_id
        )
    )


async def _calculate_risk_assessment_async(
    *, risk_definition_id: str, scope_type: str, scope_id: str | None
) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        assessment = await RiskEngine(session).calculate(
            risk_definition_id=UUID(risk_definition_id),
            scope_type=ScopeType(scope_type),
            scope_id=UUID(scope_id) if scope_id else None,
            llm=_try_get_llm(),
            triggered_by="scheduler",
        )
        await session.commit()

    logger.info(
        "calculate_risks.assessment_completed",
        risk_definition_id=risk_definition_id,
        scope_type=scope_type,
        scope_id=scope_id,
        final_score=assessment.final_score,
    )
