"""phase6 advanced analysis schema

Revision ID: b1c2d3e4f5a6
Revises: a5b6c7d8e9f0
Create Date: 2026-07-22 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "a5b6c7d8e9f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Analyst assessments (design doc section 35: analyst disagreement) --
    op.create_table(
        "analyst_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("subject_type", sa.String(length=30), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("analyst_user_id", sa.Uuid(), nullable=True),
        sa.Column("stance", sa.String(length=30), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("evidence_bundle_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["analyst_user_id"],
            ["users.id"],
            name=op.f("fk_analyst_assessments_analyst_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_bundle_id"],
            ["evidence_bundles.id"],
            name=op.f("fk_analyst_assessments_evidence_bundle_id_evidence_bundles"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_analyst_assessments")),
    )
    op.create_index(
        op.f("ix_analyst_assessments_subject_type"),
        "analyst_assessments",
        ["subject_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_analyst_assessments_subject_id"),
        "analyst_assessments",
        ["subject_id"],
        unique=False,
    )
    op.create_index(
        "uq_analyst_assessments_subject_analyst",
        "analyst_assessments",
        ["subject_type", "subject_id", "analyst_user_id"],
        unique=True,
    )

    # --- Model review results (design doc section 35: multi-model review) --
    op.create_table(
        "model_review_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("subject_type", sa.String(length=30), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("trigger_reason", sa.String(length=50), nullable=False),
        sa.Column("primary_model", sa.String(length=100), nullable=False),
        sa.Column("secondary_model", sa.String(length=100), nullable=False),
        sa.Column("primary_final_score", sa.Integer(), nullable=False),
        sa.Column("secondary_final_score", sa.Integer(), nullable=False),
        sa.Column("agreement", sa.Boolean(), nullable=True),
        sa.Column("agreement_delta", sa.Integer(), nullable=True),
        sa.Column("secondary_output_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_review_results")),
    )
    op.create_index(
        op.f("ix_model_review_results_subject_type"),
        "model_review_results",
        ["subject_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_review_results_subject_id"),
        "model_review_results",
        ["subject_id"],
        unique=False,
    )

    # --- Imagery evidence (design doc section 35: imagery evidence) --------
    op.create_table(
        "image_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=True),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("object_key", sa.String(length=500), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "retrieved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("location_precision", sa.String(length=30), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("verification_status", sa.String(length=30), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("analysis_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("submitted_by_type", sa.String(length=20), nullable=False),
        sa.Column("submitted_by_id", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name=op.f("fk_image_evidence_source_id_sources"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_image_evidence_document_id_documents"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_image_evidence")),
    )
    op.create_index(
        op.f("ix_image_evidence_content_hash"), "image_evidence", ["content_hash"], unique=False
    )

    op.create_table(
        "evidence_bundle_imagery_items",
        sa.Column("bundle_id", sa.Uuid(), nullable=False),
        sa.Column("image_evidence_id", sa.Uuid(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["bundle_id"],
            ["evidence_bundles.id"],
            name=op.f("fk_evidence_bundle_imagery_items_bundle_id_evidence_bundles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["image_evidence_id"],
            ["image_evidence.id"],
            name=op.f("fk_evidence_bundle_imagery_items_image_evidence_id_image_evidence"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "bundle_id", "image_evidence_id", name=op.f("pk_evidence_bundle_imagery_items")
        ),
    )


def downgrade() -> None:
    op.drop_table("evidence_bundle_imagery_items")
    op.drop_table("image_evidence")
    op.drop_table("model_review_results")
    op.drop_table("analyst_assessments")
