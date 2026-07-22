"""DB-backed test of Phase 6 imagery evidence: submission, dedupe, vision-model
analysis, and evidence-bundle linkage, following the same testcontainers pattern
as `tests/integration/test_phase3_risk_lifecycle.py`. Network/object-storage calls
are monkeypatched out (`tests/integration/test_phase2_extraction_pipeline.py`'s
`_no_network` pattern), and the vision LLM uses `FakeStructuredLLM`.
"""

import os
import shutil
import subprocess
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import ClassVar

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from apps.worker.tasks.imagery import ImageAnalysisResult, analyze_image_with_session
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mei.application.services.imagery_ingestion import ImageryIngestionService
from mei.infrastructure.collection.http_fetcher import FetchResult
from mei.infrastructure.llm.fake_adapter import FakeStructuredLLM
from mei.infrastructure.repositories.evidence import EvidenceRepository
from mei.infrastructure.repositories.imagery import ImageryRepository
from mei.shared.config import get_settings
from mei.shared.enums import VerificationStatus

REPO_ROOT = Path(__file__).resolve().parents[2]

_IMAGE_BYTES = b"\xff\xd8\xff\xe0fake-jpeg-bytes"


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


class _FakeObjectStorage:
    """No-op stand-in for MinIO/S3 that records what it was asked to store."""

    put_calls: ClassVar[list[tuple[str, bytes, str]]] = []
    stored: ClassVar[dict[str, bytes]] = {}

    async def ensure_bucket(self) -> None:
        return None

    async def put_bytes(self, key: str, data: bytes, *, content_type: str) -> None:
        _FakeObjectStorage.put_calls.append((key, data, content_type))
        _FakeObjectStorage.stored[key] = data

    async def get_bytes(self, key: str) -> bytes:
        return _FakeObjectStorage.stored[key]


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeObjectStorage.put_calls = []
    _FakeObjectStorage.stored = {}

    async def fake_fetch_url(url: str) -> FetchResult:
        return FetchResult(url=url, status_code=200, content_type="image/jpeg", body=_IMAGE_BYTES)

    monkeypatch.setattr(
        "mei.application.services.imagery_ingestion.validate_url_security", lambda url: None
    )
    monkeypatch.setattr("mei.application.services.imagery_ingestion.fetch_url", fake_fetch_url)
    monkeypatch.setattr(
        "mei.application.services.imagery_ingestion.ObjectStorage", _FakeObjectStorage
    )
    monkeypatch.setattr("apps.worker.tasks.imagery.ObjectStorage", _FakeObjectStorage)
    # `ImageryIngestionService.submit_image` enqueues analysis via Celery;
    # no worker/broker is running in this test, so make `.delay()` a no-op
    # rather than letting it try (and fail) to reach Redis.
    monkeypatch.setattr(
        "apps.worker.tasks.imagery.analyze_image.delay", lambda *args, **kwargs: None
    )


async def test_submit_image_dedupes_by_content_hash(session: AsyncSession) -> None:
    service = ImageryIngestionService(session)

    first = await service.submit_image(image_url="https://example.com/photo-a.jpg", caption="First")
    second = await service.submit_image(
        image_url="https://example.com/photo-b.jpg", caption="Second"
    )
    await session.commit()

    assert second.id == first.id  # same bytes -> same content hash -> dedup
    assert len(_FakeObjectStorage.put_calls) == 1  # only archived once


async def test_submit_image_archives_bytes_to_object_storage(session: AsyncSession) -> None:
    image = await ImageryIngestionService(session).submit_image(
        image_url="https://example.com/photo-unique-1.jpg"
    )
    await session.commit()

    assert len(_FakeObjectStorage.put_calls) == 1
    key, data, content_type = _FakeObjectStorage.put_calls[0]
    assert data == _IMAGE_BYTES
    assert content_type == "image/jpeg"
    assert key == image.object_key
    assert key.startswith("imagery/")


async def test_analyze_image_updates_analysis_and_verification_status(
    session: AsyncSession,
) -> None:
    image = await ImageryIngestionService(session).submit_image(
        image_url="https://example.com/photo-unique-2.jpg"
    )
    await session.commit()
    assert image.verification_status == VerificationStatus.UNREVIEWED

    canned = ImageAnalysisResult(
        description="A convoy of military vehicles on a highway.",
        notable_features=["military vehicle", "highway"],
        possible_manipulation_indicators=[],
        confidence=0.82,
    )
    llm = FakeStructuredLLM(responses={"imagery_analysis": canned})

    updated = await analyze_image_with_session(session, str(image.id), llm=llm)
    await session.commit()

    assert updated is not None
    assert updated.verification_status == VerificationStatus.SINGLE_SOURCE
    assert updated.confidence == 0.82
    assert updated.analysis_json["description"] == "A convoy of military vehicles on a highway."
    assert "military vehicle" in updated.analysis_json["notable_features"]


async def test_link_image_to_bundle_round_trips(session: AsyncSession) -> None:
    image = await ImageryIngestionService(session).submit_image(
        image_url="https://example.com/photo-unique-3.jpg"
    )
    evidence = EvidenceRepository(session)
    bundle = await evidence.create_bundle(title="Test imagery bundle")
    await session.commit()

    await evidence.add_imagery_item(bundle_id=bundle.id, image_evidence_id=image.id, weight=0.9)
    await session.commit()

    linked_ids = await evidence.list_bundle_imagery_ids(bundle.id)
    assert linked_ids == [image.id]


async def test_get_by_content_hash_returns_none_for_unknown_hash(session: AsyncSession) -> None:
    result = await ImageryRepository(session).get_by_content_hash("does-not-exist")
    assert result is None
