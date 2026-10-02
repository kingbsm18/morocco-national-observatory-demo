"""
Ported, semantics-preserving translation of lib/data/hcp.ts
(normalizeHcpIndicator / validateIndicatorIntegrity / the numeric and
identity-normalization helpers) from the existing Next.js frontend.

This file intentionally mirrors the original control flow line-for-line
where possible, rather than "improving" it, per the instruction to preserve
existing HCP interpretation rather than inventing a new one. If the two
implementations ever need to diverge, that should be a deliberate, reviewed
change on both sides — not an accident of two people parsing the same API
differently.

Source of truth being ported: lib/data/hcp.ts in this same repository.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from data_pipeline.registry.models import IndicatorDefinition

CURLY_APOSTROPHE = "\u2019"


@dataclass
class Modality:
    id: str
    label: str
    total: bool


@dataclass
class Dimension:
    id: str
    label: str
    modalities: List[Modality] = field(default_factory=list)


@dataclass
class Observation:
    period: str
    value: Optional[float]
    dimensions: Dict[str, str]
    dimension_ids: Dict[str, str]
    foot_note: Any = None


@dataclass
class Metadata:
    unit: str = ""
    frequency: str = ""
    source: str = ""
    definition: str = ""
    footnotes: Any = None
    methodology: str = ""


@dataclass
class NormalizedIndicator:
    indicator_id: str
    label: str
    metadata: Metadata
    periods: List[str]
    dimensions: List[Dimension]
    observations: List[Observation]


@dataclass
class IntegrityResult:
    valid: bool
    reason: Optional[str] = None
    metadata_valid: Optional[bool] = None
    data_valid: Optional[bool] = None


def clean(value: Any) -> str:
    """Port of `String(value ?? '').trim()`."""
    if value is None:
        return ""
    return str(value).strip()


def normalize_identity(value: str) -> str:
    """Port of the identity-comparison helper used to fuzzy-match the
    HCP response label against the registry's hand-curated French title."""
    value = value.replace(CURLY_APOSTROPHE, "'")
    value = re.sub(r"\s+", " ", value)
    return value.strip().lower()


def numeric(value: Any) -> Optional[float]:
    """Port of the numeric parser: treats None/''  as missing (not zero),
    and accepts comma as a decimal separator."""
    if value is None or value == "":
        return None
    try:
        parsed = float(str(value).replace(",", "."))
    except ValueError:
        return None
    if parsed != parsed or parsed in (float("inf"), float("-inf")):  # NaN / inf guard
        return None
    return parsed


def validate_indicator_integrity(
    indicator: IndicatorDefinition, response: Any
) -> IntegrityResult:
    if not indicator.id:
        return IntegrityResult(valid=False, reason="missing-registry-id")
    if not indicator.apiUrl.endswith(f"/{quote(indicator.id, safe='')}"):
        return IntegrityResult(valid=False, reason="registry-endpoint-mismatch")
    if not isinstance(response, dict):
        return IntegrityResult(valid=False, reason="missing-response")
    payload = response
    response_code = clean(payload.get("code"))
    response_label = clean(payload.get("label"))
    if response_code != indicator.id:
        return IntegrityResult(
            valid=False,
            reason=f"response-code-mismatch:{response_code}",
            metadata_valid=False,
            data_valid=False,
        )
    if not response_label:
        return IntegrityResult(
            valid=False,
            reason="missing-response-label",
            metadata_valid=False,
            data_valid=False,
        )
    data = payload.get("data")
    if not isinstance(data, dict):
        return IntegrityResult(
            valid=False, reason="missing-response-data", metadata_valid=True, data_valid=False
        )
    metadata_valid = normalize_identity(response_label) == normalize_identity(
        indicator.frenchTitle
    )
    return IntegrityResult(
        valid=metadata_valid,
        reason=None if metadata_valid else f"response-label-mismatch:{response_label}",
        metadata_valid=metadata_valid,
        data_valid=True,
    )


def _period_sort_key(period: str) -> float:
    try:
        return float(period)
    except ValueError:
        return float("inf")


def normalize_hcp_indicator(response: Any) -> Optional[NormalizedIndicator]:
    if not isinstance(response, dict):
        return None
    payload = response
    data = payload.get("data")
    if not isinstance(data, dict):
        return None

    raw_dimensions = payload.get("dimensions") if isinstance(payload.get("dimensions"), list) else []
    dimensions: List[Dimension] = []
    for dimension in raw_dimensions:
        modalites = dimension.get("modalites")
        modalities: List[Modality] = []
        if isinstance(modalites, list):
            for modalite in modalites:
                modalities.append(
                    Modality(
                        id=clean(modalite.get("id")),
                        label=clean(modalite.get("label")),
                        total=modalite.get("total") is True,
                    )
                )
        dimensions.append(
            Dimension(id=clean(dimension.get("id")), label=clean(dimension.get("label")), modalities=modalities)
        )

    modality_lookup: Dict[str, Dict[str, Any]] = {}
    for dimension in dimensions:
        for modality in dimension.modalities:
            modality_lookup[modality.id] = {
                "dimension": dimension,
                "label": modality.label,
                "total": modality.total,
            }

    observations: List[Observation] = []
    for key, raw in data.items():
        parts = key.split("_")
        encoded_ids = parts[0] if len(parts) >= 1 else ""
        period = parts[1] if len(parts) >= 2 else ""
        ids = encoded_ids.split(".") if encoded_ids else []
        resolved: Dict[str, str] = {}
        dimension_ids: Dict[str, str] = {}
        for index, id_ in enumerate(ids):
            match = modality_lookup.get(id_)
            if match is None and index < len(dimensions):
                dim = dimensions[index]
                found = next((m for m in dim.modalities if m.id == id_), None)
                if found:
                    match = {"dimension": dim, "label": found.label, "total": found.total}
            if match:
                resolved[match["dimension"].label] = match["label"]
                dimension_ids[match["dimension"].id] = id_
        raw_value = raw.get("value") if isinstance(raw, dict) else None
        foot_note = raw.get("footNote") if isinstance(raw, dict) else None
        observations.append(
            Observation(
                period=clean(period),
                value=numeric(raw_value),
                dimensions=resolved,
                dimension_ids=dimension_ids,
                foot_note=foot_note,
            )
        )

    periods_source = (
        payload.get("periods")
        if isinstance(payload.get("periods"), list)
        else [o.period for o in observations]
    )
    periods_cleaned = [clean(p) for p in periods_source]
    periods_filtered = [p for p in periods_cleaned if p]
    periods_sorted = sorted(periods_filtered, key=_period_sort_key)
    periods_unique = list(dict.fromkeys(periods_sorted))

    metadata_raw = payload.get("metaData") if isinstance(payload.get("metaData"), dict) else {}
    metadata = Metadata(
        unit=clean(metadata_raw.get("unit")),
        frequency=clean(metadata_raw.get("frequency")),
        source=clean(metadata_raw.get("source")),
        definition=clean(metadata_raw.get("definitionFr")),
        footnotes=metadata_raw.get("footNotesFr"),
        methodology=clean(metadata_raw.get("methodOfCalculationFr")),
    )

    return NormalizedIndicator(
        indicator_id=clean(payload.get("code")),
        label=clean(payload.get("label")),
        metadata=metadata,
        periods=periods_unique,
        dimensions=dimensions,
        observations=observations,
    )
