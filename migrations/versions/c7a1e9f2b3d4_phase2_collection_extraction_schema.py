"""phase2 collection and extraction schema

Revision ID: c7a1e9f2b3d4
Revises: b43ba5d65f49
Create Date: 2026-07-21 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c7a1e9f2b3d4"
down_revision: str | None = "b43ba5d65f49"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Deduplication (design doc section 11): stage-3/4 checks add a content
    # fingerprint and a self-referential "this document is a duplicate of"
    # pointer.
    op.add_column(
        "documents", sa.Column("content_fingerprint", sa.String(length=16), nullable=True)
    )
    op.add_column("documents", sa.Column("duplicate_of_document_id", sa.Uuid(), nullable=True))
    op.create_index(
        op.f("ix_documents_content_fingerprint"), "documents", ["content_fingerprint"], unique=False
    )
    op.create_index(
        op.f("ix_documents_duplicate_of_document_id"),
        "documents",
        ["duplicate_of_document_id"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_documents_duplicate_of_document_id_documents"),
        "documents",
        "documents",
        ["duplicate_of_document_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # LLM extraction provenance (design doc section 13.3).
    op.add_column(
        "claims",
        sa.Column(
            "extraction_metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "events",
        sa.Column(
            "extraction_metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    # Generic analyst review queue (entity resolution, event-duplicate merges).
    op.create_table(
        "review_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("review_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("subject_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("candidates_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("resolution_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_review_items")),
    )
    op.create_index(
        op.f("ix_review_items_review_type"), "review_items", ["review_type"], unique=False
    )
    op.create_index(op.f("ix_review_items_status"), "review_items", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("review_items")
    op.drop_column("events", "extraction_metadata_json")
    op.drop_column("claims", "extraction_metadata_json")
    op.drop_constraint(
        op.f("fk_documents_duplicate_of_document_id_documents"), "documents", type_="foreignkey"
    )
    op.drop_index(op.f("ix_documents_duplicate_of_document_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_content_fingerprint"), table_name="documents")
    op.drop_column("documents", "duplicate_of_document_id")
    op.drop_column("documents", "content_fingerprint")
