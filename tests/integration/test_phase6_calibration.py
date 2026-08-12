"""DB-backed test of Phase 6 calibration reporting: `CalibrationService.compute_reliability`
against real `ForecastRecord` rows, following the same testcontainers pattern as
`tests/integration/test_phase3_risk_lifecycle.py`.
"""

import os
import shutil
import subprocess
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mei.application.services.calibration import CalibrationService
from mei.application.services.forecast_audit import ForecastAuditService
from mei.shared.config import get_settings
from mei.shared.enums import ForecastOutcome

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


async def test_compute_reliability_scores_resolved_forecasts_and_counts_open_ones(
    session: AsyncSession,
) -> None:
    audit_service = ForecastAuditService(session)

    resolved_yes = await audit_service.issue_forecast(
        question="Will the ceasefire hold through Q3?",
        resolution_date=date(2026, 9, 1),
        probability=80.0,
        confidence=0.7,
    )
    await audit_service.resolve_forecast(resolved_yes.id, outcome=ForecastOutcome.YES)

    resolved_no = await audit_service.issue_forecast(
        question="Will the border crossing reopen this month?",
        resolution_date=date(2026, 9, 1),
        probability=20.0,
        confidence=0.6,
    )
    await audit_service.resolve_forecast(resolved_no.id, outcome=ForecastOutcome.NO)

    await audit_service.issue_forecast(
        question="Still-open forecast",
        resolution_date=date(2026, 12, 1),
        probability=50.0,
        confidence=0.5,
    )
    await session.commit()

    report = await CalibrationService(session).compute_reliability(bucket_count=10)

    assert report["resolved_count"] == 2
    assert report["open_count"] == 1
    assert report["overall_brier_score"] is not None
    assert sum(b["forecast_count"] for b in report["buckets"]) == 2

    high_confidence_bucket = report["buckets"][8]  # 80-90% bucket
    assert high_confidence_bucket["forecast_count"] == 1
    assert high_confidence_bucket["observed_frequency"] == 1.0


async def test_compute_reliability_since_filters_by_issued_at(session: AsyncSession) -> None:
    audit_service = ForecastAuditService(session)

    forecast = await audit_service.issue_forecast(
        question="Forecast issued now",
        resolution_date=date(2027, 2, 1),
        probability=60.0,
        confidence=0.5,
    )
    await audit_service.resolve_forecast(forecast.id, outcome=ForecastOutcome.YES)
    await session.commit()

    # `issue_forecast` always stamps `issued_at` with the current time, so a
    # `since` cutoff safely in the future is what proves the filter actually
    # excludes a forecast rather than the test racing real wall-clock time.
    future_cutoff = datetime(2030, 1, 1, tzinfo=UTC)
    report = await CalibrationService(session).compute_reliability(since=future_cutoff)

    assert report["resolved_count"] == 0
