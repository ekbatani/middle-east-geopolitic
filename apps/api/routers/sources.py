from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.source_ingestion import SourceIngestionService
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.sources import SourceRepository
from mei.shared.enums import DocumentStatus, Scope, SourceType
from mei.shared.errors import NotFoundError

router = APIRouter(tags=["sources"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
SubmitPrincipal = Annotated[Principal, Depends(require_scopes(Scope.SOURCES_SUBMIT))]


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source_type: SourceType
    base_url: str | None
    enabled: bool


class SubmitSourceRequest(BaseModel):
    url: HttpUrl
    title: str | None = Field(default=None, max_length=1000)
    source_id: UUID | None = None


class SubmitSourceResponse(BaseModel):
    document_id: UUID
    source_id: UUID
    status: DocumentStatus
    canonical_url: str
    title: str | None
    extracted_text_preview: str | None


@router.get("/sources", response_model=list[SourceOut])
async def list_sources(
    session: SessionDep,
    _principal: ReadPrincipal,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[SourceOut]:
    sources = await SourceRepository(session).list_all(limit=limit, offset=offset)
    return [SourceOut.model_validate(source) for source in sources]


@router.get("/sources/{source_id}", response_model=SourceOut)
async def get_source(source_id: UUID, session: SessionDep, _principal: ReadPrincipal) -> SourceOut:
    source = await SourceRepository(session).get(source_id)
    if source is None:
        raise NotFoundError(f"Source {source_id} not found")
    return SourceOut.model_validate(source)


@router.post("/sources/submit", response_model=SubmitSourceResponse, status_code=201)
async def submit_source(
    payload: SubmitSourceRequest, session: SessionDep, principal: SubmitPrincipal
) -> SubmitSourceResponse:
    """Manually submit a URL for fetch, archive, and text extraction (Phase 1)."""
    document = await SourceIngestionService(session).submit_url(
        url=str(payload.url), title=payload.title, source_id=payload.source_id
    )

    await audit(
        session,
        principal,
        "source.submitted",
        resource_type="document",
        resource_id=str(document.id),
        metadata={"url": str(payload.url)},
    )

    preview = document.extracted_text[:500] if document.extracted_text else None
    return SubmitSourceResponse(
        document_id=document.id,
        source_id=document.source_id,
        status=document.status,
        canonical_url=document.canonical_url,
        title=document.title,
        extracted_text_preview=preview,
    )
