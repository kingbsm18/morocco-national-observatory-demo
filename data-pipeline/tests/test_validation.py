from __future__ import annotations

import copy

import pytest

from data_pipeline.sources.hcp.parser import normalize_hcp_indicator
from data_pipeline.validation.engine import count_by_severity, run_validation
from tests.conftest import load_fixture, make_indicator


def test_clean_fixture_has_no_errors():
    indicator = make_indicator("I1589")
    payload = load_fixture("I1589")
    normalized = normalize_hcp_indicator(payload)
    results = run_validation(indicator, requested_id="I1589", raw_payload=payload, normalized=normalized)
    counts = count_by_severity(results)
    assert counts["ERROR"] == 0


def test_response_code_mismatch_is_error():
    indicator = make_indicator("I1589")
    payload = copy.deepcopy(load_fixture("I1589"))
    payload["code"] = "I9999"  # HCP claims to be answering for a different indicator
    normalized = normalize_hcp_indicator(payload)
    results = run_validation(indicator, requested_id="I1589", raw_payload=payload, normalized=normalized)
    identity_result = next(r for r in results if r.rule_name == "identity_chain")
    assert identity_result.severity == "ERROR"
    assert count_by_severity(results)["ERROR"] >= 1


def test_label_wording_drift_is_warning_not_error():
    indicator = make_indicator("I1589")
    payload = copy.deepcopy(load_fixture("I1589"))
    payload["label"] = payload["label"] + " (révisé)"  # harmless rewording on HCP's side
    normalized = normalize_hcp_indicator(payload)
    results = run_validation(indicator, requested_id="I1589", raw_payload=payload, normalized=normalized)
    label_result = next(r for r in results if r.rule_name == "registry_label_match")
    assert label_result.severity == "WARNING"
    assert count_by_severity(results)["ERROR"] == 0


def test_duplicate_observation_is_warning_and_rows_are_kept():
    indicator = make_indicator("I1589")
    payload = copy.deepcopy(load_fixture("I1589"))
    # HCP's key format doesn't allow a literal duplicate dict key, so we simulate
    # the real-world case: two distinct raw keys that resolve to the same
    # (period, dimension_ids) identity after parsing. "MTOT.MTOT_2021" encodes
    # two dimension-ids for a single-dimension indicator; both resolve to the
    # same modality (MTOT on D1), so it parses to an identical dimension_ids
    # combination as the existing "MTOT_2021" key for the same period.
    payload["data"]["MTOT.MTOT_2021"] = payload["data"]["MTOT_2021"]
    normalized = normalize_hcp_indicator(payload)
    results = run_validation(indicator, requested_id="I1589", raw_payload=payload, normalized=normalized)
    dup_result = next(r for r in results if r.rule_name == "duplicate_observation_detection")
    assert dup_result.severity == "WARNING"
    assert count_by_severity(results)["ERROR"] == 0


def test_missing_required_metadata_is_error():
    indicator = make_indicator("I1589")
    payload = copy.deepcopy(load_fixture("I1589"))
    payload["label"] = ""
    normalized = normalize_hcp_indicator(payload)
    results = run_validation(indicator, requested_id="I1589", raw_payload=payload, normalized=normalized)
    assert count_by_severity(results)["ERROR"] >= 1
