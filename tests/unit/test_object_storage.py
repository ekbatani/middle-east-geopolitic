from datetime import UTC, datetime
from uuid import UUID

from mei.infrastructure.object_storage.client import build_raw_object_key

SOURCE_ID = UUID("00000000-0000-0000-0000-000000000001")
DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000002")


def test_build_raw_object_key_matches_documented_layout() -> None:
    retrieved_at = datetime(2026, 7, 20, 12, 0, 0, tzinfo=UTC)

    key = build_raw_object_key(
        source_id=SOURCE_ID,
        document_id=DOCUMENT_ID,
        content_hash="abc123",
        extension="html",
        retrieved_at=retrieved_at,
    )

    assert key == f"raw/2026/07/20/{SOURCE_ID}/{DOCUMENT_ID}-abc123.html"
