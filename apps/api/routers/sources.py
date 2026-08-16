from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.source_ingestion import SourceIngestionService
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.sources import SourceRepository
from mei.shared.enums import DocumentStatus, EndpointType, Scope, SourceType
from mei.shared.errors import NotFoundError

router = APIRouter(tags=["sources"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
SubmitPrincipal = Annotated[Principal, Depends(require_scopes(Scope.SOURCES_SUBMIT))]


class SourceEndpointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    endpoint_type: EndpointType
    url: str
    schedule: str | None
    parser_name: str | None
    priority: int
    last_success_at: datetime | None
    last_failure_at: datetime | None
    failure_count: int


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source_type: SourceType
    base_url: str | None
    jurisdiction: str | None
    default_language: str | None
    enabled: bool
    endpoints: list[SourceEndpointOut] = Field(default_factory=list)


class CreateSourceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    source_type: SourceType
    base_url: str | None = None
    default_language: str | None = None
    jurisdiction: str | None = None


class UpdateSourceRequest(BaseModel):
    name: str | None = None
    source_type: SourceType | None = None
    base_url: str | None = None
    default_language: str | None = None
    enabled: bool | None = None


class CreateSourceEndpointRequest(BaseModel):
    endpoint_type: EndpointType
    url: str = Field(min_length=1, max_length=2048)
    schedule: str | None = None
    priority: int = 100


class UpdateSourceEndpointRequest(BaseModel):
    endpoint_type: EndpointType | None = None
    url: str | None = None
    schedule: str | None = None
    priority: int | None = None


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


@router.post("/sources", response_model=SourceOut, status_code=201)
async def create_source(
    payload: CreateSourceRequest,
    session: SessionDep,
    principal: SubmitPrincipal,
) -> SourceOut:
    repo = SourceRepository(session)
    source = await repo.create(
        name=payload.name,
        source_type=payload.source_type,
        base_url=payload.base_url,
        default_language=payload.default_language,
    )
    await audit(
        session,
        principal,
        "source.created",
        resource_type="source",
        resource_id=str(source.id),
        metadata={"name": payload.name, "source_type": payload.source_type},
    )
    await session.commit()
    created = await repo.get(source.id)
    return SourceOut.model_validate(created)


@router.get("/sources/{source_id}", response_model=SourceOut)
async def get_source(source_id: UUID, session: SessionDep, _principal: ReadPrincipal) -> SourceOut:
    source = await SourceRepository(session).get(source_id)
    if source is None:
        raise NotFoundError(f"Source {source_id} not found")
    return SourceOut.model_validate(source)


@router.patch("/sources/{source_id}", response_model=SourceOut)
async def update_source(
    source_id: UUID,
    payload: UpdateSourceRequest,
    session: SessionDep,
    principal: SubmitPrincipal,
) -> SourceOut:
    repo = SourceRepository(session)
    source = await repo.get(source_id)
    if source is None:
        raise NotFoundError(f"Source {source_id} not found")

    updated = await repo.update(
        source,
        name=payload.name,
        source_type=payload.source_type,
        base_url=payload.base_url,
        default_language=payload.default_language,
        enabled=payload.enabled,
    )
    await audit(
        session,
        principal,
        "source.updated",
        resource_type="source",
        resource_id=str(source_id),
        metadata=payload.model_dump(exclude_unset=True),
    )
    await session.commit()
    refreshed = await repo.get(source_id)
    return SourceOut.model_validate(refreshed)


@router.delete("/sources/{source_id}", status_code=204)
async def delete_source(
    source_id: UUID,
    session: SessionDep,
    principal: SubmitPrincipal,
) -> None:
    repo = SourceRepository(session)
    source = await repo.get(source_id)
    if source is None:
        raise NotFoundError(f"Source {source_id} not found")

    await repo.delete(source)
    await audit(
        session,
        principal,
        "source.deleted",
        resource_type="source",
        resource_id=str(source_id),
    )
    await session.commit()


@router.post("/sources/{source_id}/endpoints", response_model=SourceEndpointOut, status_code=201)
async def add_source_endpoint(
    source_id: UUID,
    payload: CreateSourceEndpointRequest,
    session: SessionDep,
    principal: SubmitPrincipal,
) -> SourceEndpointOut:
    repo = SourceRepository(session)
    source = await repo.get(source_id)
    if source is None:
        raise NotFoundError(f"Source {source_id} not found")

    endpoint = await repo.create_endpoint(
        source_id=source_id,
        endpoint_type=payload.endpoint_type,
        url=payload.url,
        schedule=payload.schedule,
        priority=payload.priority,
    )
    await audit(
        session,
        principal,
        "source.endpoint_created",
        resource_type="source_endpoint",
        resource_id=str(endpoint.id),
        metadata={"source_id": str(source_id), "url": payload.url},
    )
    await session.commit()
    return SourceEndpointOut.model_validate(endpoint)


@router.patch("/sources/endpoints/{endpoint_id}", response_model=SourceEndpointOut)
async def update_source_endpoint(
    endpoint_id: UUID,
    payload: UpdateSourceEndpointRequest,
    session: SessionDep,
    principal: SubmitPrincipal,
) -> SourceEndpointOut:
    repo = SourceRepository(session)
    endpoint = await repo.get_endpoint(endpoint_id)
    if endpoint is None:
        raise NotFoundError(f"Endpoint {endpoint_id} not found")

    updated = await repo.update_endpoint(
        endpoint,
        endpoint_type=payload.endpoint_type,
        url=payload.url,
        schedule=payload.schedule,
        priority=payload.priority,
    )
    await audit(
        session,
        principal,
        "source.endpoint_updated",
        resource_type="source_endpoint",
        resource_id=str(endpoint_id),
    )
    await session.commit()
    return SourceEndpointOut.model_validate(updated)


@router.delete("/sources/endpoints/{endpoint_id}", status_code=204)
async def delete_source_endpoint(
    endpoint_id: UUID,
    session: SessionDep,
    principal: SubmitPrincipal,
) -> None:
    repo = SourceRepository(session)
    endpoint = await repo.get_endpoint(endpoint_id)
    if endpoint is None:
        raise NotFoundError(f"Endpoint {endpoint_id} not found")

    await repo.delete_endpoint(endpoint)
    await audit(
        session,
        principal,
        "source.endpoint_deleted",
        resource_type="source_endpoint",
        resource_id=str(endpoint_id),
    )
    await session.commit()


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
