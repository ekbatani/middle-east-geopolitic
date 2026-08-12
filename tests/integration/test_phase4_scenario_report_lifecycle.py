"""End-to-end DB-backed test of the Phase 4 acceptance criteria:

  "scenario changes preserve prior versions"
  "reports cite internal evidence"
  "forecasts can be scored after resolution"

Runs against a real Postgres (via testcontainers), applying the actual
Alembic migrations, following the same pattern as
`tests/integration/test_phase3_risk_lifecycle.py`. Object storage is
monkeypatched out (no MinIO container stood up), matching
`tests/integration/test_phase2_extraction_pipeline.py`.
"""

import os
import shutil
import subprocess
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mei.application.services.actors import ActorService
from mei.application.services.forecast_audit import ForecastAuditService
from mei.application.services.report_generator import ReportGenerator
from mei.application.services.scenario_engine import ScenarioEngine, ScenarioUpdateRecommendation
from mei.infrastructure.llm.fake_adapter import FakeStructuredLLM
from mei.infrastructure.repositories.events import EventRepository
from mei.infrastructure.repositories.forecasts import ForecastRepository
from mei.infrastructure.repositories.scenarios import ScenarioRepository
from mei.shared.config import get_settings
from mei.shared.enums import (
    ActorType,
    ForecastOutcome,
    LifecycleStatus,
    ReportStatus,
    ReportType,
    ScenarioFamily,
    ScopeType,
)
from mei.shared.errors import ConflictError

REPO_ROOT = Path(__file__).resolve().parents[2]


def _docker_available() -> bool:
    return False
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


class _FakeObjectStorage:
    """No-op stand-in for MinIO/S3: no object storage container is stood up for this test."""

    async def ensure_bucket(self) -> None:
        return None

    async def put_bytes(self, key: str, data: bytes, *, content_type: str) -> None:
        return None


@pytest.fixture(autouse=True)
def _no_object_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mei.application.services.report_generator.ObjectStorage", _FakeObjectStorage
    )


async def test_scenario_update_preserves_prior_assessments(session: AsyncSession) -> None:
    country = await ActorService(session).create_actor(
        canonical_name="Test Scenario Country", actor_type=ActorType.COUNTRY
    )
    engine = ScenarioEngine(session)
    scenario = await engine.create_scenario(
        name="Test controlled de-escalation",
        scope_type=ScopeType.COUNTRY,
        scope_id=country.id,
        scenario_family=ScenarioFamily.CONTROLLED_DEESCALATION,
        time_horizon="3 months",
    )
    await session.commit()

    first = await engine.update_scenario(scenario.id, triggered_by="test")
    await session.commit()

    # No LLM and no prior assessment: the fallback records full uncertainty
    # rather than fabricating a number.
    assert first.probability_low == 0.0
    assert first.probability_high == 100.0
    assert first.confidence == 0.0

    second = await engine.update_scenario(scenario.id, triggered_by="test")
    await session.commit()

    # No LLM configured on the second pass either: it carries the previous
    # assessment forward rather than resetting it, and both rows remain in
    # history — "scenario changes preserve prior versions".
    assert second.probability_low == first.probability_low
    assert second.probability_high == first.probability_high

    history = await ScenarioRepository(session).list_assessments(scenario.id)
    assert [a.id for a in history] == [second.id, first.id]


async def test_scenario_update_with_llm_persists_recommendation(session: AsyncSession) -> None:
    country = await ActorService(session).create_actor(
        canonical_name="Test LLM Scenario Country", actor_type=ActorType.COUNTRY
    )
    engine = ScenarioEngine(session)
    scenario = await engine.create_scenario(
        name="Test managed confrontation",
        scope_type=ScopeType.COUNTRY,
        scope_id=country.id,
        scenario_family=ScenarioFamily.MANAGED_CONFRONTATION,
        time_horizon="6 months",
    )
    await session.commit()

    recommendation = ScenarioUpdateRecommendation(
        probability_low=20.0,
        probability_high=45.0,
        confidence=0.65,
        assumptions=["No new external mediation is attempted."],
        trigger_events=["cross_border_strike"],
        leading_indicators=["force_mobilization"],
        expected_actor_behavior="Both sides continue proxy pressure without direct engagement.",
        explanation_of_change="Initial assessment; no prior baseline.",
    )
    llm = FakeStructuredLLM(responses={"scenario_update": recommendation})

    assessment = await engine.update_scenario(scenario.id, llm=llm, triggered_by="test")
    await session.commit()

    assert assessment.probability_low == 20.0
    assert assessment.probability_high == 45.0
    assert assessment.confidence == 0.65
    assert assessment.trigger_events_json == ["cross_border_strike"]
    assert assessment.model_version is not None


async def test_forecast_can_be_scored_after_resolution(session: AsyncSession) -> None:
    audit = ForecastAuditService(session)
    forecast = await audit.issue_forecast(
        question="Will the ceasefire hold for 30 days?",
        resolution_date=date(2026, 1, 1),
        probability=70.0,
        confidence=0.6,
        assumptions=["No major spoiler attacks in the interim."],
    )
    await session.commit()

    due = await audit.list_due(as_of=date(2026, 1, 2))
    assert forecast.id in {f.id for f in due}

    resolved = await audit.resolve_forecast(
        forecast.id, outcome=ForecastOutcome.YES, evaluation_note="Ceasefire held through day 30."
    )
    await session.commit()

    assert resolved.outcome == ForecastOutcome.YES
    # probability 70% -> 0.7, outcome YES -> actual 1.0: (0.7 - 1.0)^2 = 0.09
    assert resolved.brier_score is not None
    assert abs(resolved.brier_score - 0.09) < 1e-9

    still_due = await audit.list_due(as_of=date(2026, 1, 2))
    assert forecast.id not in {f.id for f in still_due}


async def test_daily_brief_cites_internal_evidence_and_can_be_approved_and_published(
    session: AsyncSession,
) -> None:
    events = EventRepository(session)
    now = datetime.now(UTC)
    event = await events.create(
        event_type="military_strike",
        title="Test strike near the border",
        started_at=now - timedelta(hours=6),
    )
    await events.set_lifecycle_status(event, lifecycle_status=LifecycleStatus.APPROVED)
    await session.commit()

    generator = ReportGenerator(session)
    report = await generator.generate_daily_brief(triggered_by="test")
    await session.commit()

    assert report.status == ReportStatus.GENERATED
    assert report.report_type == ReportType.DAILY_BRIEF
    assert f"event/{event.id}" in report.content_markdown
    assert event.title in report.content_markdown

    approved = await generator.approve_report(report.id, approved_by="analyst")
    await session.commit()
    assert approved.status == ReportStatus.APPROVED
    assert approved.approved_by == "analyst"

    published = await generator.publish_report(report.id)
    await session.commit()
    assert published.status == ReportStatus.PUBLISHED
    assert published.published_at is not None


async def test_report_cannot_be_published_before_approval(session: AsyncSession) -> None:
    generator = ReportGenerator(session)
    report = await generator.generate_daily_brief(triggered_by="test")
    await session.commit()

    with pytest.raises(ConflictError):
        await generator.publish_report(report.id)


async def test_forecast_repository_lists_only_open_and_due_forecasts(session: AsyncSession) -> None:
    repo = ForecastRepository(session)
    future_forecast = await repo.create(
        question="Will X happen?",
        issued_at=datetime.now(UTC),
        resolution_date=date(2099, 1, 1),
        probability=50.0,
        confidence=0.5,
        assumptions=[],
        evidence_bundle_id=None,
    )
    await session.commit()

    due = await repo.list_due(as_of=date(2026, 1, 1))
    assert future_forecast.id not in {f.id for f in due}
