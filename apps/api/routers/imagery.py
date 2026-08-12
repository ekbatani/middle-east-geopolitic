"""Imagery evidence submission and retrieval (design doc section 35, Phase 6 "imagery evidence")."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, HttpUrl

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.imagery_ingestion import ImageryIngestionService
from mei.domain.imagery.models import ImageEvidence
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.object_storage_mock import ObjectStorage
from mei.infrastructure.repositories.evidence import EvidenceRepository
from mei.infrastructure.repositories.imagery import ImageryRepository
from mei.shared.enums import Scope, VerificationStatus
from mei.shared.errors import NotFoundError

router = APIRouter(prefix="/imagery", tags=["imagery"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
SubmitPrincipal = Annotated[Principal, Depends(require_scopes(Scope.IMAGERY_SUBMIT))]


class ImageEvidenceOut(BaseModel):
    id: UUID
    source_id: UUID | None
    document_id: UUID | None
    content_type: str
    content_hash: str
    captured_at: datetime | None
    retrieved_at: datetime
    latitude: float | None
    longitude: float | None
    location_precision: str | None
    caption: str | None
    verification_status: VerificationStatus
    confidence: float | None
    analysis: dict[str, object]

    @classmethod
    def from_domain(cls, image: ImageEvidence) -> "ImageEvidenceOut":
        return cls(
            id=image.id,
            source_id=image.source_id,
            document_id=image.document_id,
            content_type=image.content_type,
            content_hash=image.content_hash,
            captured_at=image.captured_at,
            retrieved_at=image.retrieved_at,
            latitude=image.latitude,
            longitude=image.longitude,
            location_precision=image.location_precision,
            caption=image.caption,
            verification_status=image.verification_status,
            confidence=image.confidence,
            analysis=image.analysis_json,
        )


class SubmitImageRequest(BaseModel):
    image_url: HttpUrl
    source_id: UUID | None = None
    document_id: UUID | None = None
    caption: str | None = None
    captured_at: datetime | None = None


class LinkImageToBundleRequest(BaseModel):
    bundle_id: UUID
    weight: float = 1.0


@router.post("/submit", response_model=ImageEvidenceOut, status_code=201)
async def submit_image(
    payload: SubmitImageRequest, session: SessionDep, principal: SubmitPrincipal
) -> ImageEvidenceOut:
    image = await ImageryIngestionService(session).submit_image(
        image_url=str(payload.image_url),
        source_id=payload.source_id,
        document_id=payload.document_id,
        caption=payload.caption,
        captured_at=payload.captured_at,
        submitted_by_type="user",
        submitted_by_id=str(principal.user_id),
    )
    await audit(
        session,
        principal,
        "imagery.submitted",
        resource_type="image_evidence",
        resource_id=str(image.id),
        metadata={"image_url": str(payload.image_url)},
    )
    return ImageEvidenceOut.from_domain(image)


@router.get("", response_model=list[ImageEvidenceOut])
async def list_images(
    session: SessionDep,
    _principal: ReadPrincipal,
    source_id: UUID | None = None,
    verification_status: VerificationStatus | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ImageEvidenceOut]:
    images = await ImageryRepository(session).list_images(
        source_id=source_id,
        verification_status=verification_status,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
    return [ImageEvidenceOut.from_domain(i) for i in images]


@router.get("/{image_id}", response_model=ImageEvidenceOut)
async def get_image(
    image_id: UUID, session: SessionDep, _principal: ReadPrincipal
) -> ImageEvidenceOut:
    image = await ImageryRepository(session).get(image_id)
    if image is None:
        raise NotFoundError(f"Image {image_id} not found")
    return ImageEvidenceOut.from_domain(image)


@router.get("/{image_id}/raw")
async def get_image_raw(image_id: UUID, session: SessionDep, _principal: ReadPrincipal) -> Response:
    image = await ImageryRepository(session).get(image_id)
    if image is None:
        raise NotFoundError(f"Image {image_id} not found")
    raw_bytes = await ObjectStorage().get_bytes(image.object_key)
    return Response(content=raw_bytes, media_type=image.content_type)


@router.post("/{image_id}/analyze", response_model=ImageEvidenceOut)
async def reanalyze_image(
    image_id: UUID, session: SessionDep, principal: SubmitPrincipal
) -> ImageEvidenceOut:
    image = await ImageryRepository(session).get(image_id)
    if image is None:
        raise NotFoundError(f"Image {image_id} not found")

    import asyncio

    from mei.application.services.imagery_analysis import ImageryAnalysisService

    async def _analyze() -> None:
        from mei.infrastructure.database.session import get_session_factory

        session_factory = get_session_factory()
        async with session_factory() as s:
            await ImageryAnalysisService(s).analyze_image(image.id)
            await s.commit()

    asyncio.create_task(_analyze())
    await audit(
        session,
        principal,
        "imagery.reanalysis_requested",
        resource_type="image_evidence",
        resource_id=str(image.id),
    )
    return ImageEvidenceOut.from_domain(image)


@router.post("/{image_id}/link-to-bundle", status_code=201)
async def link_image_to_bundle(
    image_id: UUID,
    payload: LinkImageToBundleRequest,
    session: SessionDep,
    principal: SubmitPrincipal,
) -> dict[str, str]:
    images = ImageryRepository(session)
    evidence = EvidenceRepository(session)

    image = await images.get(image_id)
    if image is None:
        raise NotFoundError(f"Image {image_id} not found")
    if await evidence.get_bundle(payload.bundle_id) is None:
        raise NotFoundError(f"Evidence bundle {payload.bundle_id} not found")

    item = await evidence.add_imagery_item(
        bundle_id=payload.bundle_id, image_evidence_id=image_id, weight=payload.weight
    )
    await audit(
        session,
        principal,
        "imagery.linked_to_bundle",
        resource_type="image_evidence",
        resource_id=str(image_id),
        metadata={"bundle_id": str(payload.bundle_id)},
    )
    return {"bundle_id": str(item.bundle_id), "image_evidence_id": str(item.image_evidence_id)}
