from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
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

    async def find_by_external_id(self, source_id: UUID, external_id: str) -> Document | None:
        """Dedup stage 1 (design doc section 11): exact external ID match."""
        result = await self._session.execute(
            select(Document).where(
                Document.source_id == source_id, Document.external_id == external_id
            )
        )
        return result.scalar_one_or_none()

    async def find_by_content_hash(
        self, content_hash: str, *, exclude_document_id: UUID | None = None
    ) -> Document | None:
        """Dedup stage 3: raw content hash match, across sources."""
        stmt = select(Document).where(Document.content_hash == content_hash)
        if exclude_document_id is not None:
            stmt = stmt.where(Document.id != exclude_document_id)
        result = await self._session.execute(stmt.order_by(Document.id).limit(1))
        return result.scalar_one_or_none()

    async def find_by_fingerprint(
        self, content_fingerprint: str, *, exclude_document_id: UUID | None = None
    ) -> Document | None:
        """Dedup stage 4: normalized text fingerprint match, across sources."""
        stmt = select(Document).where(Document.content_fingerprint == content_fingerprint)
        if exclude_document_id is not None:
            stmt = stmt.where(Document.id != exclude_document_id)
        result = await self._session.execute(stmt.order_by(Document.id).limit(1))
        return result.scalar_one_or_none()

    async def mark_duplicate(self, document: Document, *, duplicate_of_id: UUID) -> None:
        document.duplicate_of_document_id = duplicate_of_id
        await self._session.flush()

    async def create(
        self,
        *,
        source_id: UUID,
        canonical_url: str,
        title: str | None = None,
        external_id: str | None = None,
        published_at: datetime | None = None,
    ) -> Document:
        document = Document(
            source_id=source_id,
            canonical_url=canonical_url,
            title=title,
            external_id=external_id,
            published_at=published_at,
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
        self,
        document: Document,
        *,
        extracted_text: str,
        parser_version: str,
        content_fingerprint: str | None = None,
    ) -> None:
        document.extracted_text = extracted_text
        document.parser_version = parser_version
        document.status = DocumentStatus.PARSED
        if content_fingerprint is not None:
            document.content_fingerprint = content_fingerprint
        await self._session.flush()

    async def mark_failed(self, document: Document) -> None:
        document.status = DocumentStatus.FAILED
        await self._session.flush()

    async def set_language(self, document: Document, *, language: str) -> None:
        document.original_language = language
        await self._session.flush()

    async def set_translation(
        self, document: Document, *, translation_text: str, metadata: dict[str, object]
    ) -> None:
        document.translation_text = translation_text
        document.metadata_json = {**document.metadata_json, "translation": metadata}
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

    async def count_retrieved_before(self, cutoff: datetime) -> int:
        result = await self._session.execute(
            select(func.count(Document.id)).where(Document.retrieved_at < cutoff)
        )
        return int(result.scalar_one())

    async def clear_chunks(self, document_id: UUID) -> None:
        result = await self._session.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        for chunk in result.scalars():
            await self._session.delete(chunk)
        await self._session.flush()


__all__ = ["DocumentRepository"]
