"""
Confirms that `ingest --all` resolves its indicator set purely from whatever
the registry fixture hands it -- there is no second, hand-maintained list of
ids inside cli.py or ingestion/run.py. The only place this test suite itself
hardcodes 28 ids is tests/conftest.py, which exists specifically to mirror
lib/data/hcp-indicators.ts for offline testing (see its module docstring);
production code never does this -- it always calls registry.client.fetch_registry()
to get the live set.
"""
from __future__ import annotations

import pytest

from data_pipeline.cli import resolve_indicators
from tests.conftest import _REGISTRY_SUBSET


def test_all_resolves_every_indicator_in_the_registry(registry):
    resolved = resolve_indicators(registry, indicator_ids=[], use_all=True)
    assert len(resolved) == 28
    assert {i.id for i in resolved} == set(_REGISTRY_SUBSET.keys())


def test_all_resolves_whatever_size_the_registry_happens_to_be(registry_test_subset):
    """Resolution logic itself must not assume any particular count -- it
    reflects whatever the registry (real or fixture) contains, 9 or 28 or
    any other number."""
    resolved = resolve_indicators(registry_test_subset, indicator_ids=[], use_all=True)
    assert len(resolved) == len(registry_test_subset)


def test_explicit_indicator_ids_resolve_only_those(registry):
    resolved = resolve_indicators(registry, indicator_ids=["I1589", "I3210"], use_all=False)
    assert [i.id for i in resolved] == ["I1589", "I3210"]


def test_unknown_explicit_id_raises(registry):
    with pytest.raises(ValueError):
        resolve_indicators(registry, indicator_ids=["I_NOT_REAL"], use_all=False)
