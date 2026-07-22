from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import BaseModel

from mei.infrastructure.llm.fake_adapter import FakeStructuredLLM
from mei.infrastructure.object_storage.client import build_imagery_object_key


def test_build_imagery_object_key_includes_source_id() -> None:
    source_id = uuid4()
    image_id = uuid4()
    retrieved_at = datetime(2026, 7, 22, tzinfo=UTC)

    key = build_imagery_object_key(
        source_id=source_id,
        image_id=image_id,
        content_hash="abc123",
        extension="jpg",
        retrieved_at=retrieved_at,
    )

    assert key == f"imagery/2026/07/22/{source_id}/{image_id}-abc123.jpg"


def test_build_imagery_object_key_without_source_id_uses_unattributed() -> None:
    image_id = uuid4()
    retrieved_at = datetime(2026, 7, 22, tzinfo=UTC)

    key = build_imagery_object_key(
        source_id=None,
        image_id=image_id,
        content_hash="abc123",
        extension="png",
        retrieved_at=retrieved_at,
    )

    assert key == f"imagery/2026/07/22/unattributed/{image_id}-abc123.png"


def test_build_imagery_object_key_never_collides_with_raw_prefix() -> None:
    key = build_imagery_object_key(
        source_id=uuid4(),
        image_id=uuid4(),
        content_hash="abc123",
        extension="jpg",
        retrieved_at=datetime(2026, 7, 22, tzinfo=UTC),
    )
    assert key.startswith("imagery/")
    assert not key.startswith("raw/")


class _FakeOutput(BaseModel):
    description: str


async def test_fake_structured_llm_generate_structured_from_image_matches_protocol() -> None:
    llm = FakeStructuredLLM(responses={"imagery_analysis": _FakeOutput(description="a photo")})

    result = await llm.generate_structured_from_image(
        task_name="imagery_analysis",
        prompt_version="imagery_analyze_v1",
        image_bytes=b"fake-bytes",
        content_type="image/jpeg",
        output_model=_FakeOutput,
        metadata={},
    )

    assert result.description == "a photo"


async def test_fake_structured_llm_unregistered_task_raises() -> None:
    llm = FakeStructuredLLM(responses={})
    with pytest.raises(KeyError):
        await llm.generate_structured_from_image(
            task_name="unregistered",
            prompt_version="v1",
            image_bytes=b"x",
            content_type="image/png",
            output_model=_FakeOutput,
            metadata={},
        )
