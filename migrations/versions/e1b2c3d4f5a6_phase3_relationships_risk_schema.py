"""phase3 relationships and risk engine schema

Revision ID: e1b2c3d4f5a6
Revises: c7a1e9f2b3d4
Create Date: 2026-07-21 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e1b2c3d4f5a6"
down_revision: str | None = "c7a1e9f2b3d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Relationships (design doc section 8.6) ---------------------------
    op.create_table(
        "relationships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_actor_id", sa.Uuid(), nullable=False),
        sa.Column("target_actor_id", sa.Uuid(), nullable=False),
        sa.Column("relationship_type", sa.String(length=50), nullable=False),
        sa.Column("directionality", sa.String(length=20), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["source_actor_id"],
            ["actors.id"],
            name=op.f("fk_relationships_source_actor_id_actors"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_actor_id"],
            ["actors.id"],
            name=op.f("fk_relationships_target_actor_id_actors"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_relationships")),
    )
    op.create_index(
        op.f("ix_relationships_source_actor_id"), "relationships", ["source_actor_id"], unique=False
    )
    op.create_index(
        op.f("ix_relationships_target_actor_id"), "relationships", ["target_actor_id"], unique=False
    )
    op.create_index(
        op.f("ix_relationships_relationship_type"),
        "relationships",
        ["relationship_type"],
        unique=False,
    )

    op.create_table(
        "relationship_observations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("relationship_id", sa.Uuid(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("diplomatic_score", sa.Integer(), nullable=True),
        sa.Column("military_cooperation_score", sa.Integer(), nullable=True),
        sa.Column("military_tension_score", sa.Integer(), nullable=True),
        sa.Column("intelligence_cooperation_score", sa.Integer(), nullable=True),
        sa.Column("economic_dependency_score", sa.Integer(), nullable=True),
        sa.Column("energy_dependency_score", sa.Integer(), nullable=True),
        sa.Column("strategic_trust_score", sa.Integer(), nullable=True),
        sa.Column("ideological_compatibility_score", sa.Integer(), nullable=True),
        sa.Column("proxy_competition_score", sa.Integer(), nullable=True),
        sa.Column("public_hostility_score", sa.Integer(), nullable=True),
        sa.Column("escalation_risk_score", sa.Integer(), nullable=True),
        sa.Column("trend", sa.String(length=10), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("evidence_bundle_id", sa.Uuid(), nullable=True),
        sa.Column("ruleset_version", sa.String(length=50), nullable=True),
        sa.Column("model_version", sa.String(length=100), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(
            ["evidence_bundle_id"],
            ["evidence_bundles.id"],
            name=op.f("fk_relationship_observations_evidence_bundle_id_evidence_bundles"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["relationship_id"],
            ["relationships.id"],
            name=op.f("fk_relationship_observations_relationship_id_relationships"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_relationship_observations")),
    )
    op.create_index(
        op.f("ix_relationship_observations_relationship_id"),
        "relationship_observations",
        ["relationship_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_relationship_observations_observed_at"),
        "relationship_observations",
        ["observed_at"],
        unique=False,
    )

    # --- Indicators (design doc section 8.7) -------------------------------
    op.create_table(
        "indicator_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("value_type", sa.String(length=30), nullable=False),
        sa.Column("normalization_method", sa.String(length=20), nullable=False),
        sa.Column("lower_bound", sa.Float(), nullable=True),
        sa.Column("upper_bound", sa.Float(), nullable=True),
        sa.Column("staleness_hours", sa.Integer(), nullable=True),
        sa.Column("default_weight", sa.Float(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("ruleset_version", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_indicator_definitions")),
    )
    op.create_index(
        op.f("ix_indicator_definitions_code"), "indicator_definitions", ["code"], unique=True
    )
    op.create_index(
        op.f("ix_indicator_definitions_category"),
        "indicator_definitions",
        ["category"],
        unique=False,
    )

    op.create_table(
        "indicator_observations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("indicator_id", sa.Uuid(), nullable=False),
        sa.Column("scope_type", sa.String(length=20), nullable=False),
        sa.Column("scope_id", sa.Uuid(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_value", sa.Float(), nullable=False),
        sa.Column("normalized_value", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_bundle_id", sa.Uuid(), nullable=True),
        sa.Column("source_method", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(
            ["evidence_bundle_id"],
            ["evidence_bundles.id"],
            name=op.f("fk_indicator_observations_evidence_bundle_id_evidence_bundles"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["indicator_id"],
            ["indicator_definitions.id"],
            name=op.f("fk_indicator_observations_indicator_id_indicator_definitions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_indicator_observations")),
    )
    op.create_index(
        op.f("ix_indicator_observations_indicator_id"),
        "indicator_observations",
        ["indicator_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_indicator_observations_scope_type"),
        "indicator_observations",
        ["scope_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_indicator_observations_scope_id"),
        "indicator_observations",
        ["scope_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_indicator_observations_observed_at"),
        "indicator_observations",
        ["observed_at"],
        unique=False,
    )

    # --- Risks (design doc section 8.7 / 18) --------------------------------
    op.create_table(
        "risk_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("scope_types", postgresql.ARRAY(sa.String(length=20)), nullable=False),
        sa.Column("ruleset_version", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_risk_definitions")),
    )
    op.create_index(op.f("ix_risk_definitions_code"), "risk_definitions", ["code"], unique=True)

    op.create_table(
        "risk_indicator_weights",
        sa.Column("risk_definition_id", sa.Uuid(), nullable=False),
        sa.Column("indicator_definition_id", sa.Uuid(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("conditions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["indicator_definition_id"],
            ["indicator_definitions.id"],
            name=op.f("fk_risk_indicator_weights_indicator_definition_id_indicator_definitions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["risk_definition_id"],
            ["risk_definitions.id"],
            name=op.f("fk_risk_indicator_weights_risk_definition_id_risk_definitions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "risk_definition_id",
            "indicator_definition_id",
            name=op.f("pk_risk_indicator_weights"),
        ),
    )

    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("risk_definition_id", sa.Uuid(), nullable=False),
        sa.Column("scope_type", sa.String(length=20), nullable=False),
        sa.Column("scope_id", sa.Uuid(), nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("base_score", sa.Integer(), nullable=False),
        sa.Column("llm_adjustment", sa.Integer(), nullable=False),
        sa.Column("final_score", sa.Integer(), nullable=False),
        sa.Column("previous_score", sa.Integer(), nullable=True),
        sa.Column("trend", sa.String(length=10), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("explanation", sa.String(length=4000), nullable=True),
        sa.Column(
            "counter_indicators_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("contributions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence_bundle_id", sa.Uuid(), nullable=True),
        sa.Column("ruleset_version", sa.String(length=50), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=True),
        sa.Column("approval_status", sa.String(length=20), nullable=False),
        sa.Column("approved_by", sa.String(length=200), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["evidence_bundle_id"],
            ["evidence_bundles.id"],
            name=op.f("fk_risk_assessments_evidence_bundle_id_evidence_bundles"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["risk_definition_id"],
            ["risk_definitions.id"],
            name=op.f("fk_risk_assessments_risk_definition_id_risk_definitions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_risk_assessments")),
    )
    op.create_index(
        op.f("ix_risk_assessments_risk_definition_id"),
        "risk_assessments",
        ["risk_definition_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_risk_assessments_scope_type"), "risk_assessments", ["scope_type"], unique=False
    )
    op.create_index(
        op.f("ix_risk_assessments_scope_id"), "risk_assessments", ["scope_id"], unique=False
    )
    op.create_index(
        op.f("ix_risk_assessments_assessed_at"), "risk_assessments", ["assessed_at"], unique=False
    )


def downgrade() -> None:
    op.drop_table("risk_assessments")
    op.drop_table("risk_indicator_weights")
    op.drop_table("risk_definitions")
    op.drop_table("indicator_observations")
    op.drop_table("indicator_definitions")
    op.drop_table("relationship_observations")
    op.drop_table("relationships")
