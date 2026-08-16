"""job schedules and executions schema

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-08-16 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c2d3e4f5a6b7"
down_revision: str | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_schedules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("cron_expression", sa.String(length=100), nullable=True),
        sa.Column("interval_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(length=50), server_default="idle", nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_schedules")),
    )
    op.create_index(op.f("ix_job_schedules_name"), "job_schedules", ["name"], unique=False)
    op.create_index(op.f("ix_job_schedules_job_type"), "job_schedules", ["job_type"], unique=False)

    op.create_table(
        "job_executions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("schedule_id", sa.Uuid(), nullable=True),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="running", nullable=False),
        sa.Column("items_processed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("log_output", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["schedule_id"],
            ["job_schedules.id"],
            name=op.f("fk_job_executions_schedule_id_job_schedules"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_executions")),
    )
    op.create_index(op.f("ix_job_executions_schedule_id"), "job_executions", ["schedule_id"], unique=False)
    op.create_index(op.f("ix_job_executions_job_type"), "job_executions", ["job_type"], unique=False)
    op.create_index(op.f("ix_job_executions_started_at"), "job_executions", ["started_at"], unique=False)
    op.create_index(op.f("ix_job_executions_status"), "job_executions", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("job_executions")
    op.drop_table("job_schedules")
