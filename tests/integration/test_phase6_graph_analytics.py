"""DB-backed test of Phase 6 graph analytics: `GraphAnalyticsService.build_actor_graph`
loads actors/relationships from Postgres into a `networkx.Graph`, following the same
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
from mei.application.services.graph_analytics import GraphAnalyticsService
from mei.application.services.relationships import RelationshipService
from mei.shared.config import get_settings
from mei.shared.enums import ActorType, RelationshipDirectionality

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


async def test_build_actor_graph_includes_only_actors_with_active_relationships(
    session: AsyncSession,
) -> None:
    actors = ActorService(session)
    iran = await actors.create_actor(canonical_name="Graph Test Iran", actor_type=ActorType.COUNTRY)
    israel = await actors.create_actor(
        canonical_name="Graph Test Israel", actor_type=ActorType.COUNTRY
    )
    unconnected = await actors.create_actor(
        canonical_name="Graph Test Unconnected", actor_type=ActorType.COUNTRY
    )

    await RelationshipService(session).create_relationship(
        source_actor_id=iran.id,
        target_actor_id=israel.id,
        relationship_type="interstate",
        directionality=RelationshipDirectionality.SYMMETRIC,
    )
    await session.commit()

    graph = await GraphAnalyticsService(session).build_actor_graph()

    assert set(graph.nodes) == {iran.id, israel.id}
    assert unconnected.id not in graph.nodes
    assert graph.has_edge(iran.id, israel.id)
    assert graph.nodes[iran.id]["canonical_name"] == "Graph Test Iran"


async def test_build_actor_graph_edge_weight_uses_latest_escalation_score(
    session: AsyncSession,
) -> None:
    actors = ActorService(session)
    source = await actors.create_actor(
        canonical_name="Weighted Source", actor_type=ActorType.COUNTRY
    )
    target = await actors.create_actor(
        canonical_name="Weighted Target", actor_type=ActorType.COUNTRY
    )

    relationship = await RelationshipService(session).create_relationship(
        source_actor_id=source.id,
        target_actor_id=target.id,
        relationship_type="interstate",
        directionality=RelationshipDirectionality.SYMMETRIC,
    )
    await session.commit()

    from mei.infrastructure.repositories.relationships import RelationshipRepository
    from mei.shared.time import utcnow

    await RelationshipRepository(session).add_observation(
        relationship_id=relationship.id,
        observed_at=utcnow(),
        scores={"escalation_risk_score": 72},
        trend=None,
        confidence=0.8,
        explanation=None,
        evidence_bundle_id=None,
        ruleset_version="v1",
        model_version=None,
        approved_by=None,
        approved_at=None,
    )
    await session.commit()

    graph = await GraphAnalyticsService(session).build_actor_graph()
    assert graph.edges[source.id, target.id]["weight"] == 72.0
