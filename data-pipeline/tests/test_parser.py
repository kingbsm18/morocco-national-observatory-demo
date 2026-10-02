from __future__ import annotations

import pytest

from data_pipeline.sources.hcp.parser import normalize_hcp_indicator, numeric, validate_indicator_integrity
from tests.conftest import _REGISTRY_SUBSET, load_fixture, make_indicator

ALL_IDS = list(_REGISTRY_SUBSET.keys())


@pytest.mark.parametrize("indicator_id", ALL_IDS)
def test_parses_code_and_label(indicator_id):
    payload = load_fixture(indicator_id)
    normalized = normalize_hcp_indicator(payload)
    assert normalized is not None
    assert normalized.indicator_id == indicator_id
    assert normalized.label == payload["label"]


@pytest.mark.parametrize("indicator_id", ALL_IDS)
def test_parses_dimensions_and_observations(indicator_id):
    payload = load_fixture(indicator_id)
    normalized = normalize_hcp_indicator(payload)
    assert len(normalized.dimensions) == 1
    assert normalized.dimensions[0].id == "D1"
    modality_ids = {m.id for m in normalized.dimensions[0].modalities}
    assert modality_ids == {"MTOT", "MURB", "MRUR"}
    # 4 periods x 3 modalities = 12 observations
    assert len(normalized.observations) == 12


@pytest.mark.parametrize("indicator_id", ALL_IDS)
def test_periods_sorted_and_deduped(indicator_id):
    payload = load_fixture(indicator_id)
    normalized = normalize_hcp_indicator(payload)
    assert normalized.periods == ["2021", "2022", "2023", "2024"]


@pytest.mark.parametrize("indicator_id", ALL_IDS)
def test_identity_validates_against_matching_registry_entry(indicator_id):
    payload = load_fixture(indicator_id)
    indicator = make_indicator(indicator_id)
    result = validate_indicator_integrity(indicator, payload)
    assert result.valid is True
    assert result.data_valid is True
    assert result.metadata_valid is True


def test_comma_decimal_value_parses():
    # Fixture generation intentionally writes one value as "X,XX" (comma decimal)
    # on the Total/first-period observation, to exercise the comma->dot path.
    payload = load_fixture("I1589")
    normalized = normalize_hcp_indicator(payload)
    first_period_total = next(
        o for o in normalized.observations if o.period == "2021" and o.dimension_ids.get("D1") == "MTOT"
    )
    assert isinstance(first_period_total.value, float)


def test_numeric_missing_is_none_not_zero():
    assert numeric(None) is None
    assert numeric("") is None
    assert numeric(0) == 0.0
    assert numeric("0") == 0.0


def test_normalize_returns_none_for_malformed_response():
    assert normalize_hcp_indicator({"not": "a valid payload"}) is None
    assert normalize_hcp_indicator(None) is None
    assert normalize_hcp_indicator([1, 2, 3]) is None
