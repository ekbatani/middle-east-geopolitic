from datetime import datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mei.infrastructure.database.base import Base
from mei.shared.enums import DocumentStatus
from mei.shared.ids import uuid7

EMBEDDING_DIMENSIONS = 1536


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True
    )
    canonical_url: Mapped[str] = mapped_column(String(2048), index=True)
    external_id: Mapped[str | None] = mapped_column(String(300), default=None)
    title: Mapped[str | None] = mapped_column(String(1000), default=None)
    original_language: Mapped[str | None] = mapped_column(String(10), default=None)
    published_at: Mapped[datetime | None] = mapped_column(default=None)
    retrieved_at: Mapped[datetime | None] = mapped_column(default=None)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True, default=None)
    raw_object_key: Mapped[str | None] = mapped_column(String(1000), default=None)
    normalized_object_key: Mapped[str | None] = mapped_column(String(1000), default=None)
    extracted_text: Mapped[str | None] = mapped_column(Text, default=None)
    translation_text: Mapped[str | None] = mapped_column(Text, default=None)
    parser_version: Mapped[str | None] = mapped_column(String(50), default=None)
    status: Mapped[DocumentStatus] = mapped_column(String(20), default=DocumentStatus.PENDING)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    sequence: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer, default=None)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS), default=None
    )
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)

    document: Mapped[Document] = relationship(back_populates="chunks")


__all__ = ["Document", "DocumentChunk"]
