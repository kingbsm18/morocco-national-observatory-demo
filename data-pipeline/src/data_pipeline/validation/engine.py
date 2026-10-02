"""Runs every rule for one indicator's ingestion attempt and returns the
full list of ValidationResult rows. Nothing here decides what to do with
an ERROR — that decision (block canonical write) lives in ingestion/run.py,
keeping "what's wrong" separate from "what we do about it"."""
from __future__ import annotations

from typing import Any, List, Optional

from data_pipeline.registry.models import IndicatorDefinition
from data_pipeline.sources.hcp.parser import NormalizedIndicator
from data_pipeline.validation import rules
from data_pipeline.validation.rules import ValidationResult


def run_validation(
    indicator: IndicatorDefinition,
    requested_id: str,
    raw_payload: Any,
    normalized: Optional[NormalizedIndicator],
) -> List[ValidationResult]:
    results = [
        rules.rule_identity_chain(indicator, requested_id, raw_payload),
        rules.rule_required_metadata_exists(indicator, raw_payload, normalized),
        rules.rule_registry_label_match(indicator, normalized),
        rules.rule_dimension_ids_exist(normalized),
        rules.rule_numeric_values_parse(raw_payload, normalized),
        rules.rule_duplicate_observations(normalized),
        rules.rule_period_validity(normalized),
        rules.rule_unit_consistency(indicator, normalized),
    ]
    return results


def count_by_severity(results: List[ValidationResult]) -> dict:
    counts = {"PASS": 0, "WARNING": 0, "ERROR": 0}
    for r in results:
        counts[r.severity] = counts.get(r.severity, 0) + 1
    return counts
