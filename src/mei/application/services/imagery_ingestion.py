"""Imagery evidence submission (design doc section 35, Phase 6 "imagery evidence").

Follows the same shape as `SourceIngestionService.submit_url`: fetch under
the SSRF-safe policy, archive raw bytes, create the durable record — run
synchronously in the request so submission is immediately observable, with
`ImageryIngestionService` reused by a Celery task for any future batched
path. The vision-model analysis pass itself is always asynchronous
(`apps/worker/tasks/imagery.py::analyze_image`), dispatched here the same
way `InvestigationService.create` enqueues `run_investigation`.
"""

import hashlib
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.imagery.models import ImageEvidence
from mei.infrastructure.collection.http_fetcher import fetch_url, validate_url_security
from mei.infrastructure.object_storage.client import ObjectStorage, build_imagery_object_key
from mei.infrastructure.repositories.imagery import ImageryRepository
from mei.shared.ids import uuid7
from mei.shared.logging import get_logger
from mei.shared.time import utcnow

logger = get_logger(__name__)

IMAGE_CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/tiff": "tiff",
    "image/gif": "gif",
}


class ImageryIngestionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._images = ImageryRepository(session)
        self._storage = ObjectStorage()

    async def submit_image(
        self,
        *,
        image_url: str,
        source_id: UUID | None = None,
        document_id: UUID | None = None,
        caption: str | None = None,
        captured_at: datetime | None = None,
        submitted_by_type: str = "user",
        submitted_by_id: str | None = None,
    ) -> ImageEvidence:
        validate_url_security(image_url)
        result = await fetch_url(image_url)
        content_hash = hashlib.sha256(result.body).hexdigest()

        existing = await self._images.get_by_content_hash(content_hash)
        if existing is not None:
            return existing

        image_id = uuid7()
        extension = IMAGE_CONTENT_TYPE_EXTENSIONS.get(result.content_type, "bin")
        retrieved_at = utcnow()

        await self._storage.ensure_bucket()
        object_key = build_imagery_object_key(
            source_id=source_id,
            image_id=image_id,
            content_hash=content_hash,
            extension=extension,
            retrieved_at=retrieved_at,
        )
        await self._storage.put_bytes(object_key, result.body, content_type=result.content_type)

        image = await self._images.create(
            image_id=image_id,
            source_id=source_id,
            document_id=document_id,
            object_key=object_key,
            content_hash=content_hash,
            content_type=result.content_type,
            captured_at=captured_at,
            retrieved_at=retrieved_at,
            latitude=None,
            longitude=None,
            location_precision=None,
            caption=caption,
            submitted_by_type=submitted_by_type,
            submitted_by_id=submitted_by_id,
        )

        self._enqueue_analysis(image.id)
        return image

    @staticmethod
    def _enqueue_analysis(image_id: UUID) -> None:
        # Local import: the Celery task module lives downstream of the
        # application layer (same reasoning as
        # `InvestigationService.create` -> `run_investigation.delay`).
        from apps.worker.tasks.imagery import analyze_image

        analyze_image.delay(str(image_id))


__all__ = ["ImageryIngestionService"]
