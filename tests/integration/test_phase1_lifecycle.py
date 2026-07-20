"""End-to-end DB-backed test of the Phase 1 acceptance criteria:

  "an analyst can create and approve an event with linked evidence"

Runs against a real Postgres (via testcontainers), applying the actual
Alembic migration this phase adds rather than `Base.metadata.create_all`,
so the hand-written migration is exercised at least once.
"""

import shutil
import subprocess
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mei.application.services.actors import ActorService
from mei.application.services.claims import ClaimService
from mei.application.services.events import EventService
from mei.application.services.identity import IdentityService
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.documents import DocumentRepository
from mei.infrastructure.repositories.sources import SourceRepository
from mei.shared.config import get_settings
from mei.shared.enums import ActorType, EvidenceStance, LifecycleStatus, RoleName, Scope, SourceType
from mei.shared.errors import ConflictError

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
def _apply_migrations(postgres_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    # migrations/env.py builds its engine from get_settings().database_url,
    # which already expects the asyncpg driver used by the app itself.
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    get_settings.cache_clear()

    config = Config(str(REPO_ROOT / "alembic.ini"))
    command.upgrade(config, "head")


@pytest_asyncio.fixture
async def session(postgres_url: str) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(postgres_url)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session
    await engine.dispose()


async def test_event_requires_linked_evidence_before_approval(session: AsyncSession) -> None:
    settings = get_settings()

    user = await IdentityService(session, settings).register_user(
        email="analyst@mei.dev", display_name="Test Analyst", roles=[RoleName.ANALYST]
    )
    principal = Principal(
        user_id=user.id, scopes=frozenset({str(Scope.CLAIMS_CREATE), str(Scope.EVENTS_CREATE)})
    )

    actor = await ActorService(session).create_actor(
        canonical_name="Test Country", actor_type=ActorType.COUNTRY
    )

    source = await SourceRepository(session).create(
        name="Test Wire Service", source_type=SourceType.WIRE_SERVICE
    )
    document = await DocumentRepository(session).create(
        source_id=source.id, canonical_url="https://example.com/article-1"
    )

    event = await EventService(session).create_event(
        event_type="military_strike",
        title="Test strike event",
        started_at=datetime.now(tz=UTC),
    )

    with pytest.raises(ConflictError):
        await EventService(session).approve_event(event.id)

    claim = await ClaimService(session).create_claim(
        claim_text="Test claim describing the strike.",
        claim_type="attribution",
        principal=principal,
        subject_actor_id=actor.id,
        event_id=event.id,
    )
    await ClaimService(session).add_evidence(
        claim_id=claim.id,
        document_id=document.id,
        stance=EvidenceStance.SUPPORTS,
        excerpt="An excerpt describing the strike.",
    )

    approved = await EventService(session).approve_event(event.id)
    assert approved.lifecycle_status == LifecycleStatus.APPROVED

    await session.commit()
