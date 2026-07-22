"""DB-backed test of Phase 6 multi-model review: a secondary-model shadow
rerun of a `RiskAssessment` via `MultiModelReviewService`, following the same
testcontainers pattern as `tests/integration/test_phase3_risk_lifecycle.py`.
"""

import os
import shutil
import subprocess
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mei.application.services.actors import ActorService
from mei.application.services.indicators import IndicatorService
from mei.application.services.multi_model_review import MultiModelReviewService
from mei.application.services.relationships import RelationshipService
from mei.application.services.risk_engine import RiskAdjustmentRecommendation, RiskEngine
from mei.domain.risks.models import RiskDefinition
from mei.infrastructure.llm.fake_adapter import FakeStructuredLLM
from mei.infrastructure.repositories.indicators import IndicatorRepository
from mei.infrastructure.repositories.risks import RiskRepository
from mei.shared.config import get_settings
from mei.shared.enums import (
    ActorType,
    IndicatorDirection,
    IndicatorNormalizationMethod,
    RelationshipDirectionality,
    ScopeType,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(["docker", "info"], capture_output=True, timeout=5, check=True)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _docker_available(), reason="Docker is not available")


@pytest.fixture(scope="module")
def postgres_url() -> Iterator[str]:
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("pgvector/pgvector:pg16", driver="asyncpg") as container:
        yield container.get_connection_url()


@pytest.fixture(scope="module", autouse=True)
def _apply_migrations(postgres_url: str) -> Iterator[None]:
    previous_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = postgres_url
    get_settings.cache_clear()

    config = Config(str(REPO_ROOT / "alembic.ini"))
    command.upgrade(config, "head")

    try:
        yield
    finally:
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url
        get_settings.cache_clear()


@pytest_asyncio.fixture
async def session(postgres_url: str) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(postgres_url)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session
    await engine.dispose()


async def _seed_relationship(session: AsyncSession) -> object:
    iran = await ActorService(session).create_actor(
        canonical_name="MMR Test Iran", actor_type=ActorType.COUNTRY
    )
    israel = await ActorService(session).create_actor(
        canonical_name="MMR Test Israel", actor_type=ActorType.COUNTRY
    )
    return await RelationshipService(session).create_relationship(
        source_actor_id=iran.id,
        target_actor_id=israel.id,
        relationship_type="interstate",
        directionality=RelationshipDirectionality.SYMMETRIC,
    )


async def _seed_risk_model(session: AsyncSession, *, code: str) -> RiskDefinition:
    indicators = IndicatorRepository(session)
    risks = RiskRepository(session)

    attacks = await indicators.create_definition(
        code=f"{code}_attacks",
        name="Test attacks",
        category="military",
        value_type="count",
        normalization_method=IndicatorNormalizationMethod.MIN_MAX,
        lower_bound=0,
        upper_bound=10,
        staleness_hours=72,
    )
    definition = await risks.create_definition(
        code=code, name="Test escalation risk", scope_types=["relationship"]
    )
    await risks.set_weight(
        risk_definition_id=definition.id,
        indicator_definition_id=attacks.id,
        weight=1.0,
        direction=IndicatorDirection.POSITIVE,
    )
    return definition


async def test_review_risk_assessment_records_disagreement_with_secondary_model(
    session: AsyncSession,
) -> None:
    relationship = await _seed_relationship(session)
    definition = await _seed_risk_model(session, code="mmr_disagreement")

    await IndicatorService(session).record_observation(
        indicator_code="mmr_disagreement_attacks",
        scope_type=ScopeType.RELATIONSHIP,
        scope_id=relationship.id,
        raw_value=5,  # (5-0)/(10-0) = 0.5 normalized -> base_score 50
    )
    await session.commit()

    primary = await RiskEngine(session).calculate(
        risk_definition_id=definition.id,
        scope_type=ScopeType.RELATIONSHIP,
        scope_id=relationship.id,
        triggered_by="test",
    )
    await session.commit()
    assert primary.base_score == 50
    assert primary.final_score == 50

    secondary_recommendation = RiskAdjustmentRecommendation(
        recommended_adjustment=10,
        rationale=["Secondary model sees an escalation signal the deterministic score misses."],
        counter_indicators=[],
        confidence=0.7,
    )
    secondary_llm = FakeStructuredLLM(responses={"risk_adjustment": secondary_recommendation})

    review = await MultiModelReviewService(session).review_risk_assessment(
        primary.id, secondary_llm=secondary_llm, agreement_tolerance=5
    )
    await session.commit()

    assert review.primary_final_score == 50
    assert review.secondary_final_score == 60
    assert review.agreement_delta == 10
    assert review.agreement is False  # 10 > tolerance of 5
    assert review.trigger_reason == "score_delta"

    # The shadow rerun must not have created a second persisted RiskAssessment.
    history = await RiskRepository(session).list_history(
        risk_definition_id=definition.id,
        scope_type=ScopeType.RELATIONSHIP,
        scope_id=relationship.id,
    )
    assert len(history) == 1


async def test_review_risk_assessment_records_agreement_within_tolerance(
    session: AsyncSession,
) -> None:
    relationship = await _seed_relationship(session)
    definition = await _seed_risk_model(session, code="mmr_agreement")

    await IndicatorService(session).record_observation(
        indicator_code="mmr_agreement_attacks",
        scope_type=ScopeType.RELATIONSHIP,
        scope_id=relationship.id,
        raw_value=5,
    )
    await session.commit()

    primary = await RiskEngine(session).calculate(
        risk_definition_id=definition.id,
        scope_type=ScopeType.RELATIONSHIP,
        scope_id=relationship.id,
        triggered_by="test",
    )
    await session.commit()

    secondary_recommendation = RiskAdjustmentRecommendation(
        recommended_adjustment=2,
        rationale=["Minor agreement-range adjustment."],
        counter_indicators=[],
        confidence=0.9,
    )
    secondary_llm = FakeStructuredLLM(responses={"risk_adjustment": secondary_recommendation})

    review = await MultiModelReviewService(session).review_risk_assessment(
        primary.id, secondary_llm=secondary_llm, agreement_tolerance=5
    )
    await session.commit()

    assert review.agreement_delta == 2
    assert review.agreement is True
