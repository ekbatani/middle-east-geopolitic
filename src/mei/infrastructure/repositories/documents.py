from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mei.domain.documents.models import Document, DocumentChunk
from mei.shared.enums import DocumentStatus


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, document_id: UUID) -> Document | None:
        result = await self._session.execute(
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.chunks))
        )
        return result.scalar_one_or_none()

    async def list_all(
        self, *, source_id: UUID | None = None, limit: int = 50, offset: int = 0
    ) -> list[Document]:
        stmt = select(Document).order_by(Document.id.desc()).limit(limit).offset(offset)
        if source_id is not None:
            stmt = stmt.where(Document.source_id == source_id)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def find_by_canonical_url(self, source_id: UUID, canonical_url: str) -> Document | None:
        result = await self._session.execute(
            select(Document).where(
                Document.source_id == source_id, Document.canonical_url == canonical_url
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self, *, source_id: UUID, canonical_url: str, title: str | None = None
    ) -> Document:
        document = Document(
            source_id=source_id,
            canonical_url=canonical_url,
            title=title,
            status=DocumentStatus.PENDING,
        )
        self._session.add(document)
        await self._session.flush()
        return document

    async def mark_fetched(
        self,
        document: Document,
        *,
        raw_object_key: str,
        content_hash: str,
        retrieved_at: datetime,
    ) -> None:
        document.raw_object_key = raw_object_key
        document.content_hash = content_hash
        document.retrieved_at = retrieved_at
        document.status = DocumentStatus.FETCHED
        await self._session.flush()

    async def mark_parsed(
        self, document: Document, *, extracted_text: str, parser_version: str
    ) -> None:
        document.extracted_text = extracted_text
        document.parser_version = parser_version
        document.status = DocumentStatus.PARSED
        await self._session.flush()

    async def mark_failed(self, document: Document) -> None:
        document.status = DocumentStatus.FAILED
        await self._session.flush()

    async def add_chunk(
        self, *, document_id: UUID, sequence: int, text: str, token_count: int
    ) -> DocumentChunk:
        chunk = DocumentChunk(
            document_id=document_id, sequence=sequence, text=text, token_count=token_count
        )
        self._session.add(chunk)
        await self._session.flush()
        return chunk


__all__ = ["DocumentRepository"]
