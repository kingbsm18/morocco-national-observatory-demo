"""
Regression test for the historical bug: one indicator's data appearing under
another indicator's id. This must never again reach canonical storage.

The test simulates the bug shape directly: we ask the pipeline to ingest
indicator A, but the HTTP layer returns indicator B's payload (e.g. a caching
or routing mix-up upstream). The identity_chain validation rule must catch
this as an ERROR, and the pipeline must not write any canonical observation
rows for that run.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from sqlalchemy import select

from data_pipeline.ingestion.run import ingest_indicator
from data_pipeline.sources.hcp.client import RawFetchResult
from data_pipeline.storage import repository
from data_pipeline.storage.models import Observation, ValidationResultRow
from tests.conftest import load_mixed_fixture, make_indicator
from datetime import datetime, timezone


def _fake_fetch_returning(payload):
    def _fetch(api_url):
        return RawFetchResult(
            url=api_url,
            http_status=200,
            retrieved_at=datetime.now(timezone.utc),
            checksum=f"checksum-for-{payload.get('code')}-as-returned",
            raw_payload=payload,
        )
    return _fetch


@pytest.mark.parametrize(
    "requested_id, mixed_fixture_name",
    [
        ("I3210", "I3210_requested_returns_I1887_payload"),
        ("I1887", "I1887_requested_returns_I3210_payload"),
    ],
)
def test_cross_contaminated_payload_is_blocked(db_session, registry, requested_id, mixed_fixture_name):
    indicator = next(i for i in registry if i.id == requested_id)
    wrong_payload = load_mixed_fixture(mixed_fixture_name)
    assert wrong_payload["code"] != requested_id  # sanity check on the fixture itself

    run = repository.start_ingestion_run(db_session, trigger="test", indicator_count=1)
    repository.ensure_indicator_row(db_session, indicator)

    with patch("data_pipeline.ingestion.run.fetch_raw", new=_fake_fetch_returning(wrong_payload)):
        report = ingest_indicator(db_session, run, indicator)

    assert report.status == "blocked_error"
    assert report.canonical_inserted == 0

    # No observation row anywhere in the database should carry the requested
    # indicator's id with data that actually belongs to the other indicator.
    stored_observations = db_session.execute(
        select(Observation).where(Observation.indicator_id == requested_id)
    ).scalars().all()
    assert len(stored_observations) == 0

    # The ERROR must be on record, not silently swallowed.
    identity_errors = db_session.execute(
        select(ValidationResultRow).where(
            ValidationResultRow.indicator_id == requested_id,
            ValidationResultRow.rule_name == "identity_chain",
            ValidationResultRow.severity == "ERROR",
        )
    ).scalars().all()
    assert len(identity_errors) == 1


def test_clean_payload_for_same_two_indicators_is_not_blocked(db_session, registry):
    """Companion check: I3210 and I1887 ingest normally when each gets its own
    correct payload, so the block above is specifically about mismatched
    code/id, not about these two indicators generally."""
    from tests.conftest import load_fixture

    for indicator_id in ("I3210", "I1887"):
        indicator = next(i for i in registry if i.id == indicator_id)
        correct_payload = load_fixture(indicator_id)
        run = repository.start_ingestion_run(db_session, trigger="test", indicator_count=1)
        repository.ensure_indicator_row(db_session, indicator)
        with patch("data_pipeline.ingestion.run.fetch_raw", new=_fake_fetch_returning(correct_payload)):
            report = ingest_indicator(db_session, run, indicator)
        assert report.status == "success"
        assert report.canonical_inserted == 12  # 4 periods x 3 modalities
