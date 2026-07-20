from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from apps.api.dependencies import SessionDep, require_scopes
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.documents import DocumentRepository
from mei.shared.enums import DocumentStatus, Scope
from mei.shared.errors import NotFoundError

router = APIRouter(prefix="/documents", tags=["documents"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]


class DocumentChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sequence: int
    text: str
    token_count: int | None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    canonical_url: str
    title: str | None
    status: DocumentStatus
    content_hash: str | None
    retrieved_at: datetime | None
    extracted_text: str | None
    chunks: list[DocumentChunkOut] = []


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    session: SessionDep,
    _principal: ReadPrincipal,
    source_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[DocumentOut]:
    documents = await DocumentRepository(session).list_all(
        source_id=source_id, limit=limit, offset=offset
    )
    return [DocumentOut.model_validate(document) for document in documents]


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: UUID, session: SessionDep, _principal: ReadPrincipal
) -> DocumentOut:
    document = await DocumentRepository(session).get(document_id)
    if document is None:
        raise NotFoundError(f"Document {document_id} not found")
    return DocumentOut.model_validate(document)
