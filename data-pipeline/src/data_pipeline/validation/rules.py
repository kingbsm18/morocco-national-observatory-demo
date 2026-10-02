"""
Deterministic validation rules. Each rule is a pure function returning zero
or more (rule_name, severity, message, details) results. Severity is always
one of PASS / WARNING / ERROR — nothing is ever silently discarded.

Design note on severities (flagged for review, since this is new policy that
didn't exist as graded severity in the frontend before):
- `identity_chain` (registry id == requested id == response.code) is the
  strongest invariant and is an ERROR — it blocks canonical writes. This is
  the direct guard against the historical indicator-mixing bug.
- `registry_label_match` (HCP's response label vs. the registry's hand-typed
  French title) is a WARNING, not an ERROR. Today's frontend treats any
  wording drift here as a hard failure (see validateIndicatorIntegrity in
  lib/data/hcp.ts), which means a harmless rewording on HCP's side can take
  an indicator fully offline. Here it's recorded and surfaced, but does not
  block ingestion of otherwise-identity-correct data. If you'd rather keep
  this as ERROR to match current frontend behavior exactly, say so and it's
  a one-line change.
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from data_pipeline.registry.models import IndicatorDefinition
from data_pipeline.sources.hcp.parser import NormalizedIndicator, normalize_identity, clean

PASS = "PASS"
WARNING = "WARNING"
ERROR = "ERROR"


@dataclass
class ValidationResult:
    rule_name: str
    severity: str
    message: str
    details: Optional[Dict[str, Any]] = None


def dimension_key(dimension_ids: Dict[str, str]) -> str:
    """Stable identity key for an observation's dimension combination.
    Never an array index — built from the real HCP dimension/modality ids."""
    canonical = json.dumps(dimension_ids, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def rule_identity_chain(
    indicator: IndicatorDefinition, requested_id: str, raw_payload: Any
) -> ValidationResult:
    response_code = clean(raw_payload.get("code")) if isinstance(raw_payload, dict) else ""
    if indicator.id != requested_id:
        return ValidationResult(
            "identity_chain", ERROR,
            f"Registry indicator id ({indicator.id}) does not match requested id ({requested_id}).",
            {"registry_id": indicator.id, "requested_id": requested_id},
        )
    if response_code != requested_id:
        return ValidationResult(
            "identity_chain", ERROR,
            f"HCP response code ({response_code or 'missing'}) does not match requested indicator id ({requested_id}).",
            {"requested_id": requested_id, "response_code": response_code},
        )
    return ValidationResult(
        "identity_chain", PASS,
        f"registry.id == requested_id == response.code == {requested_id}",
    )


def rule_required_metadata_exists(
    indicator: IndicatorDefinition, raw_payload: Any, normalized: Optional[NormalizedIndicator]
) -> ValidationResult:
    if normalized is None:
        return ValidationResult("required_metadata_exists", ERROR, "Response could not be parsed at all.")
    if not normalized.label:
        return ValidationResult("required_metadata_exists", ERROR, "HCP response label is missing.")
    if not normalized.metadata.unit:
        return ValidationResult(
            "required_metadata_exists", WARNING,
            "HCP response did not include a unit; falling back to the registry's unit field when displaying this indicator.",
        )
    return ValidationResult("required_metadata_exists", PASS, "Label and unit metadata present.")


def rule_registry_label_match(
    indicator: IndicatorDefinition, normalized: Optional[NormalizedIndicator]
) -> ValidationResult:
    if normalized is None or not normalized.label:
        return ValidationResult("registry_label_match", WARNING, "Cannot compare labels: no parsed label.")
    matches = normalize_identity(normalized.label) == normalize_identity(indicator.frenchTitle)
    if matches:
        return ValidationResult("registry_label_match", PASS, "Response label matches registry title.")
    return ValidationResult(
        "registry_label_match", WARNING,
        f"Response label ({normalized.label!r}) does not match registry frenchTitle ({indicator.frenchTitle!r}).",
        {"response_label": normalized.label, "registry_title": indicator.frenchTitle},
    )


def rule_dimension_ids_exist(normalized: Optional[NormalizedIndicator]) -> ValidationResult:
    if normalized is None:
        return ValidationResult("dimension_ids_exist", PASS, "Nothing to check: no parsed data.")
    declared = {d.id for d in normalized.dimensions}
    offending = []
    for obs in normalized.observations:
        for dim_id in obs.dimension_ids:
            if dim_id not in declared:
                offending.append({"period": obs.period, "dimension_id": dim_id})
    if offending:
        return ValidationResult(
            "dimension_ids_exist", ERROR,
            f"{len(offending)} observation(s) reference a dimension id not declared in this response's dimensions array.",
            {"offending": offending[:20]},
        )
    return ValidationResult("dimension_ids_exist", PASS, "All referenced dimension ids are declared.")


def rule_numeric_values_parse(raw_payload: Any, normalized: Optional[NormalizedIndicator]) -> ValidationResult:
    if normalized is None or not isinstance(raw_payload, dict):
        return ValidationResult("numeric_values_parse", PASS, "Nothing to check: no parsed data.")
    data = raw_payload.get("data") if isinstance(raw_payload.get("data"), dict) else {}
    unparseable = []
    for key, raw in data.items():
        raw_value = raw.get("value") if isinstance(raw, dict) else None
        if raw_value is None or raw_value == "":
            continue  # legitimately missing, not a parse failure
        try:
            float(str(raw_value).replace(",", "."))
        except ValueError:
            unparseable.append(key)
    if unparseable:
        return ValidationResult(
            "numeric_values_parse", ERROR,
            f"{len(unparseable)} observation value(s) could not be parsed as numbers.",
            {"keys": unparseable[:20]},
        )
    return ValidationResult("numeric_values_parse", PASS, "All present values parse as numbers.")


def rule_duplicate_observations(normalized: Optional[NormalizedIndicator]) -> ValidationResult:
    if normalized is None:
        return ValidationResult("duplicate_observation_detection", PASS, "Nothing to check: no parsed data.")
    seen: Dict[Any, int] = {}
    for obs in normalized.observations:
        key = (obs.period, dimension_key(obs.dimension_ids))
        seen[key] = seen.get(key, 0) + 1
    duplicates = {k: v for k, v in seen.items() if v > 1}
    if duplicates:
        return ValidationResult(
            "duplicate_observation_detection", WARNING,
            f"{len(duplicates)} (period, dimension) combination(s) appear more than once in this response. "
            "All rows are kept (none are silently discarded) but this should be reviewed.",
            {"count": len(duplicates)},
        )
    return ValidationResult("duplicate_observation_detection", PASS, "No duplicate (period, dimension) combinations.")


def rule_period_validity(normalized: Optional[NormalizedIndicator]) -> ValidationResult:
    if normalized is None:
        return ValidationResult("period_validity", PASS, "Nothing to check: no parsed data.")
    malformed = [o.period for o in normalized.observations if o.period and not o.period.replace("-", "").isdigit()]
    if malformed:
        return ValidationResult(
            "period_validity", WARNING,
            f"{len(malformed)} observation(s) have a non-numeric period value.",
            {"periods": sorted(set(malformed))[:20]},
        )
    return ValidationResult("period_validity", PASS, "All periods are numeric.")


def rule_unit_consistency(
    indicator: IndicatorDefinition, normalized: Optional[NormalizedIndicator]
) -> ValidationResult:
    if normalized is None or not normalized.metadata.unit:
        return ValidationResult("unit_consistency", PASS, "Nothing to compare: no parsed unit.")
    if normalize_identity(normalized.metadata.unit) == normalize_identity(indicator.unit):
        return ValidationResult("unit_consistency", PASS, "Registry unit matches response unit.")
    return ValidationResult(
        "unit_consistency", WARNING,
        f"Registry unit ({indicator.unit!r}) differs from response unit ({normalized.metadata.unit!r}).",
        {"registry_unit": indicator.unit, "response_unit": normalized.metadata.unit},
    )
