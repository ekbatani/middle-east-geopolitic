"""phase1 intelligence foundation schema

Revision ID: b43ba5d65f49
Revises:
Create Date: 2026-07-20 16:03:11.564579

"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b43ba5d65f49"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name=op.f("fk_user_roles_role_id_roles"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_user_roles_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id", name=op.f("pk_user_roles")),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("key_hash", sa.String(length=255), nullable=False),
        sa.Column("scopes", postgresql.ARRAY(sa.String(length=64)), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_api_keys_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_keys")),
    )
    op.create_index(op.f("ix_api_keys_user_id"), "api_keys", ["user_id"], unique=False)
    op.create_index(op.f("ix_api_keys_key_hash"), "api_keys", ["key_hash"], unique=True)

    op.create_table(
        "actors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("canonical_name", sa.String(length=300), nullable=False),
        sa.Column("native_name", sa.String(length=300), nullable=True),
        sa.Column("actor_type", sa.String(length=40), nullable=False),
        sa.Column("parent_actor_id", sa.Uuid(), nullable=True),
        sa.Column("country_actor_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("attributes_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["country_actor_id"],
            ["actors.id"],
            name=op.f("fk_actors_country_actor_id_actors"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["parent_actor_id"],
            ["actors.id"],
            name=op.f("fk_actors_parent_actor_id_actors"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_actors")),
    )
    op.create_index(op.f("ix_actors_canonical_name"), "actors", ["canonical_name"], unique=False)
    op.create_index(op.f("ix_actors_actor_type"), "actors", ["actor_type"], unique=False)

    op.create_table(
        "actor_aliases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("alias", sa.String(length=300), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("alias_type", sa.String(length=50), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["actors.id"],
            name=op.f("fk_actor_aliases_actor_id_actors"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_actor_aliases")),
    )
    op.create_index(op.f("ix_actor_aliases_actor_id"), "actor_aliases", ["actor_id"], unique=False)
    op.create_index(op.f("ix_actor_aliases_alias"), "actor_aliases", ["alias"], unique=False)

    op.create_table(
        "evidence_bundles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_bundles")),
    )

    op.create_table(
        "actor_leadership",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("person_actor_id", sa.Uuid(), nullable=False),
        sa.Column("role_name", sa.String(length=200), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("evidence_bundle_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["actors.id"],
            name=op.f("fk_actor_leadership_actor_id_actors"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_bundle_id"],
            ["evidence_bundles.id"],
            name=op.f("fk_actor_leadership_evidence_bundle_id_evidence_bundles"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["person_actor_id"],
            ["actors.id"],
            name=op.f("fk_actor_leadership_person_actor_id_actors"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_actor_leadership")),
    )
    op.create_index(
        op.f("ix_actor_leadership_actor_id"), "actor_leadership", ["actor_id"], unique=False
    )
    op.create_index(
        op.f("ix_actor_leadership_person_actor_id"),
        "actor_leadership",
        ["person_actor_id"],
        unique=False,
    )

    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("base_url", sa.String(length=2048), nullable=True),
        sa.Column("jurisdiction", sa.String(length=100), nullable=True),
        sa.Column("default_language", sa.String(length=10), nullable=True),
        sa.Column("ownership", sa.Text(), nullable=True),
        sa.Column("known_affiliations", sa.Text(), nullable=True),
        sa.Column("historical_reliability", sa.String(length=50), nullable=True),
        sa.Column("collection_policy", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sources")),
    )
    op.create_index(op.f("ix_sources_name"), "sources", ["name"], unique=False)

    op.create_table(
        "source_endpoints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("endpoint_type", sa.String(length=20), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("schedule", sa.String(length=100), nullable=True),
        sa.Column("parser_name", sa.String(length=100), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name=op.f("fk_source_endpoints_source_id_sources"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_endpoints")),
    )
    op.create_index(
        op.f("ix_source_endpoints_source_id"), "source_endpoints", ["source_id"], unique=False
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("canonical_url", sa.String(length=2048), nullable=False),
        sa.Column("external_id", sa.String(length=300), nullable=True),
        sa.Column("title", sa.String(length=1000), nullable=True),
        sa.Column("original_language", sa.String(length=10), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("raw_object_key", sa.String(length=1000), nullable=True),
        sa.Column("normalized_object_key", sa.String(length=1000), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("translation_text", sa.Text(), nullable=True),
        sa.Column("parser_version", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name=op.f("fk_documents_source_id_sources"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
    )
    op.create_index(op.f("ix_documents_source_id"), "documents", ["source_id"], unique=False)
    op.create_index(
        op.f("ix_documents_canonical_url"), "documents", ["canonical_url"], unique=False
    )
    op.create_index(op.f("ix_documents_content_hash"), "documents", ["content_hash"], unique=False)

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(1536), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_document_chunks_document_id_documents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_chunks")),
    )
    op.create_index(
        op.f("ix_document_chunks_document_id"), "document_chunks", ["document_id"], unique=False
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_precision", sa.String(length=30), nullable=True),
        sa.Column("severity", sa.Integer(), nullable=True),
        sa.Column("strategic_significance", sa.String(length=50), nullable=True),
        sa.Column("verification_status", sa.String(length=30), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("lifecycle_status", sa.String(length=20), nullable=False),
        sa.Column("evidence_bundle_id", sa.Uuid(), nullable=True),
        sa.Column("supersedes_event_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["evidence_bundle_id"],
            ["evidence_bundles.id"],
            name=op.f("fk_events_evidence_bundle_id_evidence_bundles"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_event_id"],
            ["events.id"],
            name=op.f("fk_events_supersedes_event_id_events"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
    )
    op.create_index(op.f("ix_events_event_type"), "events", ["event_type"], unique=False)
    op.create_index(op.f("ix_events_started_at"), "events", ["started_at"], unique=False)
    op.create_index(
        op.f("ix_events_lifecycle_status"), "events", ["lifecycle_status"], unique=False
    )

    op.create_table(
        "event_actors",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("participation_status", sa.String(length=30), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["actors.id"],
            name=op.f("fk_event_actors_actor_id_actors"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_event_actors_event_id_events"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("event_id", "actor_id", "role", name=op.f("pk_event_actors")),
    )

    op.create_table(
        "event_locations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("country_actor_id", sa.Uuid(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("location_precision", sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(
            ["country_actor_id"],
            ["actors.id"],
            name=op.f("fk_event_locations_country_actor_id_actors"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_event_locations_event_id_events"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_locations")),
    )
    op.create_index(
        op.f("ix_event_locations_event_id"), "event_locations", ["event_id"], unique=False
    )

    op.create_table(
        "event_impacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("impact_type", sa.String(length=50), nullable=False),
        sa.Column("magnitude", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=30), nullable=True),
        sa.Column("estimate_low", sa.Float(), nullable=True),
        sa.Column("estimate_high", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("evidence_bundle_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_event_impacts_event_id_events"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_bundle_id"],
            ["evidence_bundles.id"],
            name=op.f("fk_event_impacts_evidence_bundle_id_evidence_bundles"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_impacts")),
    )
    op.create_index(op.f("ix_event_impacts_event_id"), "event_impacts", ["event_id"], unique=False)

    op.create_table(
        "claims",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("normalized_claim", sa.Text(), nullable=True),
        sa.Column("claim_type", sa.String(length=100), nullable=False),
        sa.Column("claimant_actor_id", sa.Uuid(), nullable=True),
        sa.Column("subject_actor_id", sa.Uuid(), nullable=True),
        sa.Column("event_id", sa.Uuid(), nullable=True),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_status", sa.String(length=30), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("lifecycle_status", sa.String(length=20), nullable=False),
        sa.Column("created_by_type", sa.String(length=20), nullable=False),
        sa.Column("created_by_id", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["claimant_actor_id"],
            ["actors.id"],
            name=op.f("fk_claims_claimant_actor_id_actors"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"], ["events.id"], name=op.f("fk_claims_event_id_events"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["subject_actor_id"],
            ["actors.id"],
            name=op.f("fk_claims_subject_actor_id_actors"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_claims")),
    )
    op.create_index(op.f("ix_claims_claim_type"), "claims", ["claim_type"], unique=False)
    op.create_index(op.f("ix_claims_event_id"), "claims", ["event_id"], unique=False)

    op.create_table(
        "claim_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), nullable=True),
        sa.Column("stance", sa.String(length=30), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("source_location", sa.String(length=300), nullable=True),
        sa.Column("directness", sa.String(length=30), nullable=True),
        sa.Column("independence_group", sa.String(length=200), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("analyst_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["document_chunks.id"],
            name=op.f("fk_claim_evidence_chunk_id_document_chunks"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["claim_id"],
            ["claims.id"],
            name=op.f("fk_claim_evidence_claim_id_claims"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_claim_evidence_document_id_documents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_claim_evidence")),
    )
    op.create_index(
        op.f("ix_claim_evidence_claim_id"), "claim_evidence", ["claim_id"], unique=False
    )
    op.create_index(
        op.f("ix_claim_evidence_document_id"), "claim_evidence", ["document_id"], unique=False
    )

    op.create_table(
        "evidence_bundle_items",
        sa.Column("bundle_id", sa.Uuid(), nullable=False),
        sa.Column("claim_evidence_id", sa.Uuid(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["bundle_id"],
            ["evidence_bundles.id"],
            name=op.f("fk_evidence_bundle_items_bundle_id_evidence_bundles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["claim_evidence_id"],
            ["claim_evidence.id"],
            name=op.f("fk_evidence_bundle_items_claim_evidence_id_claim_evidence"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "bundle_id", "claim_evidence_id", name=op.f("pk_evidence_bundle_items")
        ),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_type", sa.String(length=20), nullable=False),
        sa.Column("actor_id", sa.String(length=200), nullable=True),
        sa.Column("action", sa.String(length=200), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=True),
        sa.Column("resource_id", sa.String(length=200), nullable=True),
        sa.Column("correlation_id", sa.String(length=100), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("evidence_bundle_items")
    op.drop_table("claim_evidence")
    op.drop_table("claims")
    op.drop_table("event_impacts")
    op.drop_table("event_locations")
    op.drop_table("event_actors")
    op.drop_table("events")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("source_endpoints")
    op.drop_table("sources")
    op.drop_table("actor_leadership")
    op.drop_table("evidence_bundles")
    op.drop_table("actor_aliases")
    op.drop_table("actors")
    op.drop_table("api_keys")
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.drop_table("users")
