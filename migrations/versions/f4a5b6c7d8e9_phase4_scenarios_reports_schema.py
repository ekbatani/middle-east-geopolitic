"""phase4 scenarios, forecasts, and reports schema

Revision ID: f4a5b6c7d8e9
Revises: e1b2c3d4f5a6
Create Date: 2026-07-21 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f4a5b6c7d8e9"
down_revision: str | None = "e1b2c3d4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Scenarios (design doc section 8.8 / 19) ---------------------------
    op.create_table(
        "scenarios",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("scope_type", sa.String(length=20), nullable=False),
        sa.Column("scope_id", sa.Uuid(), nullable=True),
        sa.Column("scenario_family", sa.String(length=30), nullable=False),
        sa.Column("time_horizon", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scenarios")),
    )
    op.create_index(op.f("ix_scenarios_scope_type"), "scenarios", ["scope_type"], unique=False)
    op.create_index(op.f("ix_scenarios_scope_id"), "scenarios", ["scope_id"], unique=False)
    op.create_index(
        op.f("ix_scenarios_scenario_family"), "scenarios", ["scenario_family"], unique=False
    )
    op.create_index(op.f("ix_scenarios_status"), "scenarios", ["status"], unique=False)

    op.create_table(
        "scenario_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scenario_id", sa.Uuid(), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("probability_low", sa.Float(), nullable=False),
        sa.Column("probability_high", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("assumptions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("trigger_events_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "leading_indicators_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("expected_actor_behavior", sa.Text(), nullable=True),
        sa.Column("military_consequences", sa.Text(), nullable=True),
        sa.Column("economic_consequences", sa.Text(), nullable=True),
        sa.Column("humanitarian_consequences", sa.Text(), nullable=True),
        sa.Column(
            "invalidation_criteria_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("explanation_of_change", sa.Text(), nullable=True),
        sa.Column("evidence_bundle_id", sa.Uuid(), nullable=True),
        sa.Column("model_version", sa.String(length=100), nullable=True),
        sa.Column("approved_by", sa.String(length=200), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["evidence_bundle_id"],
            ["evidence_bundles.id"],
            name=op.f("fk_scenario_assessments_evidence_bundle_id_evidence_bundles"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["scenario_id"],
            ["scenarios.id"],
            name=op.f("fk_scenario_assessments_scenario_id_scenarios"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scenario_assessments")),
    )
    op.create_index(
        op.f("ix_scenario_assessments_scenario_id"),
        "scenario_assessments",
        ["scenario_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scenario_assessments_assessed_at"),
        "scenario_assessments",
        ["assessed_at"],
        unique=False,
    )

    # --- Forecasts (design doc section 8.9) ---------------------------------
    op.create_table(
        "forecast_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolution_date", sa.Date(), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("assumptions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence_bundle_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("outcome", sa.String(length=20), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("brier_score", sa.Float(), nullable=True),
        sa.Column("evaluation_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["evidence_bundle_id"],
            ["evidence_bundles.id"],
            name=op.f("fk_forecast_records_evidence_bundle_id_evidence_bundles"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_forecast_records")),
    )
    op.create_index(
        op.f("ix_forecast_records_issued_at"), "forecast_records", ["issued_at"], unique=False
    )
    op.create_index(
        op.f("ix_forecast_records_resolution_date"),
        "forecast_records",
        ["resolution_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_forecast_records_status"), "forecast_records", ["status"], unique=False
    )

    # --- Reports (design doc section 8.10 / 25) -----------------------------
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_type", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("scope_type", sa.String(length=20), nullable=True),
        sa.Column("scope_id", sa.Uuid(), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("content_object_key", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("generated_by_model", sa.String(length=100), nullable=True),
        sa.Column("prompt_version", sa.String(length=50), nullable=True),
        sa.Column("approved_by", sa.String(length=200), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reports")),
    )
    op.create_index(op.f("ix_reports_report_type"), "reports", ["report_type"], unique=False)
    op.create_index(op.f("ix_reports_status"), "reports", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("forecast_records")
    op.drop_table("scenario_assessments")
    op.drop_table("scenarios")
