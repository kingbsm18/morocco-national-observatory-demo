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
    http_status: int
    checksum: str
    records_parsed: int
    validation_counts: Dict[str, int]
    canonical_inserted: int
    status: str  # 'success' | 'skipped_unchanged' | 'blocked_error' | 'fetch_failed'


def ingest_indicator(
    session: Session, run: IngestionRun, indicator: IndicatorDefinition
) -> IndicatorRunReport:
    # 1. FETCH
    fetch_result = fetch_raw(indicator.apiUrl)
    if fetch_result.error or fetch_result.http_status == 0:
        repository.record_fetch_failure(session, run, indicator, fetch_result)
        return IndicatorRunReport(
            indicator_id=indicator.id,
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
        http_status=fetch_result.http_status,
        checksum=fetch_result.checksum,
        records_parsed=records_parsed,
        validation_counts=counts,
        canonical_inserted=inserted,
        status="success",
    )


def run_ingestion(
    session: Session,
    indicators: List[IndicatorDefinition],
    trigger: str = "manual",
) -> List[IndicatorRunReport]:
    run = repository.start_ingestion_run(session, trigger=trigger, indicator_count=len(indicators))
    reports: List[IndicatorRunReport] = []
    any_error = False
    for indicator in indicators:
        repository.ensure_indicator_row(session, indicator)
        report = ingest_indicator(session, run, indicator)
        reports.append(report)
        if report.status in ("blocked_error", "fetch_failed"):
            any_error = True
    repository.finish_ingestion_run(session, run, status="partial" if any_error else "success")
    return reports
