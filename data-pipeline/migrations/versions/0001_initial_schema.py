"""initial schema: sources, indicators, ingestion_runs, raw_objects, observations, validation_results

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "indicators",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("source_id", sa.String(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("arabic_title", sa.Text()),
        sa.Column("french_title", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("domain", sa.Text()),
        sa.Column("unit", sa.Text()),
        sa.Column("frequency", sa.Text()),
        sa.Column("api_url", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_indicators_source_id", "indicators", ["source_id"])

    op.create_table(
        "ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("trigger", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("indicator_count", sa.Integer()),
        sa.Column("notes", sa.Text()),
    )
    op.create_index("ix_ingestion_runs_started_at", "ingestion_runs", ["started_at"])

    op.create_table(
        "raw_objects",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("ingestion_runs.id"), nullable=False),
        sa.Column("indicator_id", sa.String(), sa.ForeignKey("indicators.id"), nullable=False),
        sa.Column("source_id", sa.String(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB()),
    )
    op.create_index("ix_raw_objects_indicator_retrieved", "raw_objects", ["indicator_id", "retrieved_at"])
    op.create_index("ix_raw_objects_indicator_checksum", "raw_objects", ["indicator_id", "checksum"])

    op.create_table(
        "observations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("indicator_id", sa.String(), sa.ForeignKey("indicators.id"), nullable=False),
        sa.Column("raw_object_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("raw_objects.id"), nullable=False),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("ingestion_runs.id"), nullable=False),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("value", sa.Numeric(), nullable=True),
        sa.Column("unit", sa.Text()),
        sa.Column("dimension_ids", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("dimension_labels", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("dimension_key", sa.String(), nullable=False),
        sa.Column(
            "kind", sa.String(), nullable=False, server_default="official",
        ),
        sa.Column("vintage", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "kind IN ('official','official_provisional','international_estimate','modelled','imputed','derived','forecast')",
            name="ck_observations_kind",
        ),
    )
    op.create_index(
        "ix_observations_identity", "observations",
        ["indicator_id", "period", "dimension_key", "ingestion_run_id"],
    )

    op.create_table(
        "validation_results",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("ingestion_runs.id"), nullable=False),
        sa.Column("indicator_id", sa.String(), sa.ForeignKey("indicators.id"), nullable=False),
        sa.Column("raw_object_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("raw_objects.id"), nullable=True),
        sa.Column("rule_name", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("severity IN ('PASS','WARNING','ERROR')", name="ck_validation_results_severity"),
    )
    op.create_index("ix_validation_results_run_severity", "validation_results", ["ingestion_run_id", "severity"])


def downgrade() -> None:
    op.drop_table("validation_results")
    op.drop_table("observations")
    op.drop_table("raw_objects")
    op.drop_table("ingestion_runs")
    op.drop_table("indicators")
    op.drop_table("sources")
