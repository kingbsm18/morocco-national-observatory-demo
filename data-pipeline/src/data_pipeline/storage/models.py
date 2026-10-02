"""SQLAlchemy ORM models for the six Phase 1 tables.

Uses the generic `JSON` type (not postgresql.JSONB) so the same models work
against both Postgres in production and SQLite in tests, without a second
set of test-only models to keep in sync.

raw_objects and observations are never UPDATEd by this codebase — only
INSERTed. "Current" values are a query (see repository.get_latest_observations),
never a stored flag, so nothing is ever silently overwritten.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Indicator(Base):
    __tablename__ = "indicators"
    id: Mapped[str] = mapped_column(String, primary_key=True)  # e.g. 'I1589' — same id as the TS registry
    source_id: Mapped[str] = mapped_column(String, ForeignKey("sources.id"))
    arabic_title: Mapped[str] = mapped_column(Text)
    french_title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    domain: Mapped[str] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(Text)
    frequency: Mapped[str] = mapped_column(Text)
    api_url: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    trigger: Mapped[str] = mapped_column(String, nullable=False)  # 'manual' | 'cron' | 'test'
    status: Mapped[str] = mapped_column(String, nullable=False)  # 'running' | 'success' | 'partial' | 'failed'
    indicator_count: Mapped[int] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class RawObject(Base):
    __tablename__ = "raw_objects"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    ingestion_run_id: Mapped[str] = mapped_column(String, ForeignKey("ingestion_runs.id"))
    indicator_id: Mapped[str] = mapped_column(String, ForeignKey("indicators.id"))
    source_id: Mapped[str] = mapped_column(String, ForeignKey("sources.id"))
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    http_status: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String, nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=True)


# kind vocabulary (approved): Phase 1 only ever writes 'official'.
VALID_OBSERVATION_KINDS = (
    "official",
    "official_provisional",
    "international_estimate",
    "modelled",
    "imputed",
    "derived",
    "forecast",
)


class Observation(Base):
    __tablename__ = "observations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    indicator_id: Mapped[str] = mapped_column(String, ForeignKey("indicators.id"))
    raw_object_id: Mapped[str] = mapped_column(String, ForeignKey("raw_objects.id"))
    ingestion_run_id: Mapped[str] = mapped_column(String, ForeignKey("ingestion_runs.id"))
    period: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Numeric, nullable=True)  # nullable: missing != zero
    unit: Mapped[str] = mapped_column(Text, nullable=True)
    dimension_ids: Mapped[dict] = mapped_column(JSON, default=dict)
    dimension_labels: Mapped[dict] = mapped_column(JSON, default=dict)
    dimension_key: Mapped[str] = mapped_column(String, nullable=False)  # identity key, never an array index
    kind: Mapped[str] = mapped_column(String, nullable=False, default="official")
    vintage: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint(f"kind IN {VALID_OBSERVATION_KINDS!r}", name="ck_observations_kind"),
    )


class ValidationResultRow(Base):
    __tablename__ = "validation_results"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    ingestion_run_id: Mapped[str] = mapped_column(String, ForeignKey("ingestion_runs.id"))
    indicator_id: Mapped[str] = mapped_column(String, ForeignKey("indicators.id"))
    raw_object_id: Mapped[str] = mapped_column(String, ForeignKey("raw_objects.id"), nullable=True)
    rule_name: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)  # PASS | WARNING | ERROR
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("severity IN ('PASS','WARNING','ERROR')", name="ck_validation_results_severity"),
    )
