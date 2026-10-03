"""
Orchestrates the pipeline exactly as specified:

    FETCH -> STORE RAW -> PARSE -> VALIDATE -> STORE CANONICAL

Raw objects and validation results are always retained, for every indicator,
regardless of outcome. If validation contains an ERROR, canonical
observations are not written for that payload; WARNINGs do not block.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from data_pipeline.registry.models import IndicatorDefinition
from data_pipeline.sources.hcp.client import fetch_raw
from data_pipeline.sources.hcp.parser import normalize_hcp_indicator
from data_pipeline.storage import repository
from data_pipeline.storage.models import IngestionRun
from data_pipeline.validation.engine import count_by_severity, run_validation
from data_pipeline.validation.rules import ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class IndicatorRunReport:
    indicator_id: str
    title: str
    http_status: int
    checksum: str
    records_parsed: int
    validation_counts: Dict[str, int]
    canonical_inserted: int
    status: str  # 'success' | 'skipped_unchanged' | 'blocked_error' | 'fetch_failed'
    overall_status: str = ""  # 'SUCCESS' | 'WARNING' | 'ERROR' -- set by _finalize()

    def __post_init__(self) -> None:
        if not self.overall_status:
            self.overall_status = _overall_status(self.status, self.validation_counts)


def _overall_status(status: str, validation_counts: Dict[str, int]) -> str:
    """Single tri-state verdict per indicator, on top of the more granular
    `status` string: ERROR if the run was blocked or the fetch failed;
    WARNING if it succeeded but validation raised a WARNING; SUCCESS
    otherwise (including a clean 'unchanged payload, nothing to do')."""
    if status in ("blocked_error", "fetch_failed"):
        return "ERROR"
    if validation_counts.get("WARNING", 0) > 0:
        return "WARNING"
    return "SUCCESS"


def ingest_indicator(
    session: Session, run: IngestionRun, indicator: IndicatorDefinition
) -> IndicatorRunReport:
    # 1. FETCH
    fetch_result = fetch_raw(indicator.apiUrl)
    if fetch_result.error or fetch_result.http_status == 0:
        repository.record_fetch_failure(session, run, indicator, fetch_result)
        return IndicatorRunReport(
            indicator_id=indicator.id,
            title=indicator.frenchTitle,
            http_status=fetch_result.http_status,
            checksum="",
            records_parsed=0,
            validation_counts={"ERROR": 1},
            canonical_inserted=0,
            status="fetch_failed",
        )

    # 2. STORE RAW (always, before anything else happens)
    raw_object_id, is_unchanged = repository.store_raw_object(session, run, indicator, fetch_result)

    if is_unchanged:
        repository.store_validation_results(
            session, run, indicator.id, raw_object_id,
            [ValidationResult(
                "unchanged_payload", "PASS",
                "Checksum matches the most recently retrieved payload for this indicator; "
                "no new canonical observations were written for this run.",
            )],
        )
        return IndicatorRunReport(
            indicator_id=indicator.id,
            title=indicator.frenchTitle,
            http_status=fetch_result.http_status,
            checksum=fetch_result.checksum,
            records_parsed=0,
            validation_counts={"PASS": 1},
            canonical_inserted=0,
            status="skipped_unchanged",
        )

    # 3. PARSE
    normalized = normalize_hcp_indicator(fetch_result.raw_payload)
    records_parsed = len(normalized.observations) if normalized else 0

    # 4. VALIDATE (results always stored, regardless of outcome)
    results = run_validation(
        indicator=indicator,
        requested_id=indicator.id,
        raw_payload=fetch_result.raw_payload,
        normalized=normalized,
    )
    repository.store_validation_results(session, run, indicator.id, raw_object_id, results)
    counts = count_by_severity(results)

    if counts.get("ERROR", 0) > 0:
        return IndicatorRunReport(
            indicator_id=indicator.id,
            title=indicator.frenchTitle,
            http_status=fetch_result.http_status,
            checksum=fetch_result.checksum,
            records_parsed=records_parsed,
            validation_counts=counts,
            canonical_inserted=0,
            status="blocked_error",
        )

    # 5. STORE CANONICAL
    assert normalized is not None  # no ERROR means parsing succeeded
    inserted = repository.store_observations(
        session, run, indicator, raw_object_id, normalized, vintage=fetch_result.retrieved_at
    )
    return IndicatorRunReport(
        indicator_id=indicator.id,
        title=indicator.frenchTitle,
        http_status=fetch_result.http_status,
        checksum=fetch_result.checksum,
        records_parsed=records_parsed,
        validation_counts=counts,
        canonical_inserted=inserted,
        status="success",
    )


@dataclass
class RunSummary:
    total_requested: int
    successful: int   # overall_status == SUCCESS
    warnings: int      # overall_status == WARNING
    errors: int        # overall_status == ERROR
    raw_objects_written: int       # one per indicator attempted, always -- nothing is ever skipped silently
    canonical_observations_written: int

    @classmethod
    def from_reports(cls, reports: List["IndicatorRunReport"]) -> "RunSummary":
        return cls(
            total_requested=len(reports),
            successful=sum(1 for r in reports if r.overall_status == "SUCCESS"),
            warnings=sum(1 for r in reports if r.overall_status == "WARNING"),
            errors=sum(1 for r in reports if r.overall_status == "ERROR"),
            raw_objects_written=len(reports),
            canonical_observations_written=sum(r.canonical_inserted for r in reports),
        )


def run_ingestion(
    session: Session,
    indicators: List[IndicatorDefinition],
    trigger: str = "manual",
) -> List[IndicatorRunReport]:
    """Ingests every indicator passed in, one at a time. Every single one gets
    a report appended -- there is no code path in this loop that moves to the
    next indicator without first producing a report for the current one, so
    nothing is ever silently skipped."""
    run = repository.start_ingestion_run(session, trigger=trigger, indicator_count=len(indicators))
    reports: List[IndicatorRunReport] = []
    for indicator in indicators:
        repository.ensure_indicator_row(session, indicator)
        report = ingest_indicator(session, run, indicator)
        reports.append(report)
    any_error = any(r.overall_status == "ERROR" for r in reports)
    repository.finish_ingestion_run(session, run, status="partial" if any_error else "success")
    assert len(reports) == len(indicators), "every requested indicator must produce exactly one report"
    return reports
