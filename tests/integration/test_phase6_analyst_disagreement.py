"""DB-backed test of Phase 6 analyst disagreement: two analysts recording
independent positions on the same subject, following the same testcontainers
pattern as `tests/integration/test_phase3_risk_lifecycle.py`.
"""

import os
import shutil
import subprocess
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mei.application.services.analyst_disagreement import AnalystDisagreementService
from mei.infrastructure.repositories.identity import IdentityRepository
from mei.shared.config import get_settings
from mei.shared.enums import DisagreementSubjectType

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


async def test_list_disagreements_surfaces_conflicting_positions_not_unanimous_ones(
    session: AsyncSession,
) -> None:
    identity = IdentityRepository(session)
    analyst_a = await identity.create_user(email="analyst-a@test.mei", display_name="Analyst A")
    analyst_b = await identity.create_user(email="analyst-b@test.mei", display_name="Analyst B")
    analyst_c = await identity.create_user(email="analyst-c@test.mei", display_name="Analyst C")
    await session.commit()

    service = AnalystDisagreementService(session)

    disputed_event_id = uuid4()
    await service.record_position(
        subject_type=DisagreementSubjectType.EVENT,
        subject_id=disputed_event_id,
        analyst_user_id=analyst_a.id,
        stance="agree",
        score=80.0,
        confidence=0.8,
        rationale="Corroborated by two independent sources.",
        evidence_bundle_id=None,
    )
    await service.record_position(
        subject_type=DisagreementSubjectType.EVENT,
        subject_id=disputed_event_id,
        analyst_user_id=analyst_b.id,
        stance="disagree",
        score=20.0,
        confidence=0.6,
        rationale="Sole source has a history of unreliable reporting.",
        evidence_bundle_id=None,
    )

    unanimous_claim_id = uuid4()
    await service.record_position(
        subject_type=DisagreementSubjectType.CLAIM,
        subject_id=unanimous_claim_id,
        analyst_user_id=analyst_a.id,
        stance="agree",
        score=75.0,
        confidence=0.9,
        rationale=None,
        evidence_bundle_id=None,
    )
    await service.record_position(
        subject_type=DisagreementSubjectType.CLAIM,
        subject_id=unanimous_claim_id,
        analyst_user_id=analyst_c.id,
        stance="agree",
        score=78.0,
        confidence=0.85,
        rationale=None,
        evidence_bundle_id=None,
    )
    await session.commit()

    disagreements = await service.list_disagreements()
    disagreement_subject_ids = {row[1] for row in disagreements}

    assert disputed_event_id in disagreement_subject_ids
    assert unanimous_claim_id not in disagreement_subject_ids


async def test_upsert_only_overwrites_the_same_analysts_own_position(session: AsyncSession) -> None:
    identity = IdentityRepository(session)
    analyst_a = await identity.create_user(email="upsert-a@test.mei", display_name="Upsert A")
    analyst_b = await identity.create_user(email="upsert-b@test.mei", display_name="Upsert B")
    await session.commit()

    service = AnalystDisagreementService(session)
    subject_id = uuid4()

    await service.record_position(
        subject_type=DisagreementSubjectType.RISK_ASSESSMENT,
        subject_id=subject_id,
        analyst_user_id=analyst_a.id,
        stance="agree",
        score=60.0,
        confidence=0.7,
        rationale="Initial read.",
        evidence_bundle_id=None,
    )
    await service.record_position(
        subject_type=DisagreementSubjectType.RISK_ASSESSMENT,
        subject_id=subject_id,
        analyst_user_id=analyst_b.id,
        stance="agree",
        score=65.0,
        confidence=0.7,
        rationale=None,
        evidence_bundle_id=None,
    )
    await session.commit()

    # Analyst A revises their own position; this must not touch analyst B's row.
    await service.record_position(
        subject_type=DisagreementSubjectType.RISK_ASSESSMENT,
        subject_id=subject_id,
        analyst_user_id=analyst_a.id,
        stance="disagree",
        score=25.0,
        confidence=0.8,
        rationale="Reassessed after new evidence.",
        evidence_bundle_id=None,
    )
    await session.commit()

    positions = await service.list_positions(
        subject_type=DisagreementSubjectType.RISK_ASSESSMENT, subject_id=subject_id
    )
    assert len(positions) == 2
    by_analyst = {p.analyst_user_id: p for p in positions}
    assert by_analyst[analyst_a.id].stance == "disagree"
    assert by_analyst[analyst_a.id].score == 25.0
    assert by_analyst[analyst_b.id].stance == "agree"
    assert by_analyst[analyst_b.id].score == 65.0
