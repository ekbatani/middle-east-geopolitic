"""DB-backed test of Phase 6 geospatial UI support: `EventRepository.list_for_map`
filters events down to the ones with a geolocated `EventLocation`, following the
same testcontainers pattern as `tests/integration/test_phase3_risk_lifecycle.py`.
"""

import os
import shutil
import subprocess
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mei.infrastructure.repositories.events import EventRepository
from mei.shared.config import get_settings

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


async def test_list_for_map_excludes_events_without_a_location(session: AsyncSession) -> None:
    repo = EventRepository(session)
    now = datetime(2026, 6, 1, tzinfo=UTC)

    geolocated = await repo.create(
        event_type="missile_strike", title="Geolocated event", started_at=now, severity=7
    )
    await repo.add_location(event_id=geolocated.id, name="Test City", latitude=33.5, longitude=36.3)

    await repo.create(
        event_type="missile_strike", title="No-location event", started_at=now, severity=7
    )
    await session.commit()

    results = await repo.list_for_map()
    result_ids = {event.id for event in results}
    assert geolocated.id in result_ids
    assert len(results) == 1


async def test_list_for_map_bbox_filters_out_locations_outside_the_box(
    session: AsyncSession,
) -> None:
    repo = EventRepository(session)
    now = datetime(2026, 6, 1, tzinfo=UTC)

    inside = await repo.create(
        event_type="protest", title="Inside bbox", started_at=now, severity=3
    )
    await repo.add_location(event_id=inside.id, name="Damascus", latitude=33.5, longitude=36.3)

    outside = await repo.create(
        event_type="protest", title="Outside bbox", started_at=now, severity=3
    )
    await repo.add_location(event_id=outside.id, name="Tokyo", latitude=35.7, longitude=139.7)
    await session.commit()

    results = await repo.list_for_map(bbox=(30.0, 25.0, 45.0, 40.0))
    result_ids = {event.id for event in results}
    assert inside.id in result_ids
    assert outside.id not in result_ids


async def test_list_for_map_filters_by_since_until_and_min_severity(session: AsyncSession) -> None:
    repo = EventRepository(session)
    t1 = datetime(2026, 1, 1, tzinfo=UTC)
    t2 = datetime(2026, 6, 1, tzinfo=UTC)

    old_low_severity = await repo.create(
        event_type="protest", title="Old, low severity", started_at=t1, severity=2
    )
    await repo.add_location(
        event_id=old_low_severity.id, name="City A", latitude=10.0, longitude=10.0
    )

    recent_high_severity = await repo.create(
        event_type="protest", title="Recent, high severity", started_at=t2, severity=9
    )
    await repo.add_location(
        event_id=recent_high_severity.id, name="City B", latitude=10.0, longitude=10.0
    )
    await session.commit()

    results = await repo.list_for_map(since=t2 - timedelta(days=1), min_severity=5)
    result_ids = {event.id for event in results}
    assert recent_high_severity.id in result_ids
    assert old_low_severity.id not in result_ids
