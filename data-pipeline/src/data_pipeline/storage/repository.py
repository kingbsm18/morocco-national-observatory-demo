"""
Insert-only data access. Nothing in this module ever UPDATEs raw_objects or
observations — a changed value is a new row, never an overwrite.

"Latest" is always computed from ingestion_runs.started_at, never from a
row's UUID primary key (UUIDs are not chronological — see repository.
get_latest_observations).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from data_pipeline.registry.models import IndicatorDefinition
from data_pipeline.sources.hcp.client import RawFetchResult
from data_pipeline.sources.hcp.parser import NormalizedIndicator
from data_pipeline.storage.models import (
    IngestionRun,
    Observation,
    RawObject,
    ValidationResultRow,
)
from data_pipeline.validation.rules import ValidationResult, dimension_key as compute_dimension_key


def start_ingestion_run(session: Session, trigger: str, indicator_count: int) -> IngestionRun:
    run = IngestionRun(
        started_at=datetime.now(timezone.utc),
        trigger=trigger,
        status="running",
        indicator_count=indicator_count,
    )
    session.add(run)
    session.commit()
    return run


def finish_ingestion_run(session: Session, run: IngestionRun, status: str) -> None:
    run.finished_at = datetime.now(timezone.utc)
    run.status = status
    session.add(run)
    session.commit()


def ensure_indicator_row(session: Session, indicator: IndicatorDefinition, source_id: str = "hcp") -> None:
    """Upsert-by-natural-key for the *indicator definition* only (title, unit,
    etc.) — this is reference data, not an immutable fact, so it is the one
    place in this module that does update existing rows. Observations and
    raw_objects are never touched by this function."""
    from data_pipeline.storage.models import Indicator, Source

    if session.get(Source, source_id) is None:
        session.add(Source(id=source_id, name="Haut-Commissariat au Plan (HCP BDS)", base_url="https://bds.hcp.ma/api/v1/indicators"))

    existing = session.get(Indicator, indicator.id)
    if existing is None:
        session.add(
            Indicator(
                id=indicator.id,
                source_id=source_id,
                arabic_title=indicator.arabicTitle,
                french_title=indicator.frenchTitle,
                description=indicator.description,
                domain=indicator.domain,
                unit=indicator.unit,
                frequency=indicator.frequency,
                api_url=indicator.apiUrl,
            )
        )
    else:
        existing.arabic_title = indicator.arabicTitle
        existing.french_title = indicator.frenchTitle
        existing.description = indicator.description
        existing.domain = indicator.domain
        existing.unit = indicator.unit
        existing.frequency = indicator.frequency
        existing.api_url = indicator.apiUrl
        existing.updated_at = datetime.now(timezone.utc)
    session.commit()


def _most_recent_checksum(session: Session, indicator_id: str) -> Optional[str]:
    stmt = (
        select(RawObject.checksum)
        .where(RawObject.indicator_id == indicator_id)
        .order_by(RawObject.retrieved_at.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def store_raw_object(
    session: Session,
    run: IngestionRun,
    indicator: IndicatorDefinition,
    fetch_result: RawFetchResult,
    source_id: str = "hcp",
) -> Tuple[str, bool]:
    """Always inserts a raw_objects row (raw data is always retained).
    Returns (raw_object_id, is_unchanged) where is_unchanged is True when
    this payload's checksum matches the indicator's most recently retrieved
    payload — the signal used to skip a redundant canonical write."""
    previous_checksum = _most_recent_checksum(session, indicator.id)
    is_unchanged = previous_checksum is not None and previous_checksum == fetch_result.checksum

    raw = RawObject(
        ingestion_run_id=run.id,
        indicator_id=indicator.id,
        source_id=source_id,
        source_url=fetch_result.url,
        retrieved_at=fetch_result.retrieved_at,
        http_status=fetch_result.http_status,
        checksum=fetch_result.checksum,
        raw_payload=fetch_result.raw_payload,
    )
    session.add(raw)
    session.commit()
    return raw.id, is_unchanged


def store_validation_results(
    session: Session,
    run: IngestionRun,
    indicator_id: str,
    raw_object_id: Optional[str],
    results: List[ValidationResult],
) -> None:
    for r in results:
        session.add(
            ValidationResultRow(
                ingestion_run_id=run.id,
                indicator_id=indicator_id,
                raw_object_id=raw_object_id,
                rule_name=r.rule_name,
                severity=r.severity,
                message=r.message,
                details=r.details,
            )
        )
    session.commit()


def store_observations(
    session: Session,
    run: IngestionRun,
    indicator: IndicatorDefinition,
    raw_object_id: str,
    normalized: NormalizedIndicator,
    vintage: datetime,
) -> int:
    """Inserts one new, immutable row per observation. Never collapses
    observations that differ by dimension, never uses an array index as
    identity — dimension_key is derived from the real HCP dimension/modality
    ids. Nothing here ever updates an existing row."""
    inserted = 0
    for obs in normalized.observations:
        session.add(
            Observation(
                indicator_id=indicator.id,
                raw_object_id=raw_object_id,
                ingestion_run_id=run.id,
                period=obs.period,
                value=obs.value,
                unit=normalized.metadata.unit or indicator.unit,
                dimension_ids=obs.dimension_ids,
                dimension_labels=obs.dimensions,
                dimension_key=compute_dimension_key(obs.dimension_ids),
                kind="official",
                vintage=vintage,
            )
        )
        inserted += 1
    session.commit()
    return inserted


def record_fetch_failure(
    session: Session,
    run: IngestionRun,
    indicator: IndicatorDefinition,
    fetch_result: RawFetchResult,
    source_id: str = "hcp",
) -> None:
    """A fetch that never got a response (network error, timeout) still gets
    a raw_objects row — http_status=0, raw_payload=None — so the ingestion
    run's history shows the attempt even though there is nothing to parse."""
    raw = RawObject(
        ingestion_run_id=run.id,
        indicator_id=indicator.id,
        source_id=source_id,
        source_url=fetch_result.url,
        retrieved_at=fetch_result.retrieved_at,
        http_status=fetch_result.http_status,
        checksum=fetch_result.checksum or "",
        raw_payload=None,
    )
    session.add(raw)
    session.commit()
    session.add(
        ValidationResultRow(
            ingestion_run_id=run.id,
            indicator_id=indicator.id,
            raw_object_id=raw.id,
            rule_name="fetch_succeeded",
            severity="ERROR",
            message=f"Fetch failed: {fetch_result.error or 'unknown error'}",
            details={"url": fetch_result.url},
        )
    )
    session.commit()


def get_latest_observations(session: Session, indicator_id: str) -> List[Observation]:
    """Returns the current value for each (period, dimension_key) of this
    indicator — "current" meaning the row from the ingestion run with the
    latest ingestion_runs.started_at, NEVER the row with the lexicographically
    largest UUID. Implemented as a window function so the database, not
    Python, owns the correctness of "latest"."""
    ranked = (
        select(
            Observation,
            func.row_number()
            .over(
                partition_by=(Observation.period, Observation.dimension_key),
                order_by=IngestionRun.started_at.desc(),
            )
            .label("rank"),
        )
        .join(IngestionRun, Observation.ingestion_run_id == IngestionRun.id)
        .where(Observation.indicator_id == indicator_id)
        .subquery()
    )
    stmt = select(ranked).where(ranked.c.rank == 1)
    rows = session.execute(stmt).all()
    return [session.get(Observation, row.id) for row in rows]
