"""
Registry access.

Decision (approved): the TypeScript array in lib/data/hcp-indicators.ts stays
the one hand-maintained copy. Everything else — including this pipeline —
reads it over HTTP via app/api/registry/route.ts, which does nothing but
re-export that same array as JSON. This makes two-manually-maintained-copies
structurally impossible: there is only ever one place a human edits the
indicator list.

Production ingestion must fail loudly if the registry cannot be retrieved,
rather than silently falling back to a stale cached copy — a stale registry
is exactly the kind of drift this mechanism exists to prevent. The cache is
for offline test runs only.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

import requests

from data_pipeline.config.settings import settings
from data_pipeline.registry.models import IndicatorDefinition

logger = logging.getLogger(__name__)


class RegistryUnavailableError(RuntimeError):
    """Raised when the registry cannot be retrieved. Callers must not catch
    this and substitute stale data — ingestion for the run should stop."""


def fetch_registry(allow_cache: bool = False) -> List[IndicatorDefinition]:
    if allow_cache:
        return _load_cache()
    try:
        response = requests.get(settings.registry_url, timeout=10)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:  # noqa: BLE001 - deliberately broad: any failure must be loud
        raise RegistryUnavailableError(
            f"Could not retrieve indicator registry from {settings.registry_url}: {exc}"
        ) from exc
    indicators = [IndicatorDefinition(**item) for item in payload]
    _write_cache(indicators)
    return indicators


def get_indicator(
    indicators: List[IndicatorDefinition], indicator_id: str
) -> Optional[IndicatorDefinition]:
    return next((i for i in indicators if i.id == indicator_id), None)


def _cache_path() -> Path:
    return Path(settings.registry_cache_path)


def _write_cache(indicators: List[IndicatorDefinition]) -> None:
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([i.model_dump() for i in indicators], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _load_cache() -> List[IndicatorDefinition]:
    path = _cache_path()
    if not path.exists():
        raise RegistryUnavailableError(
            f"No cached registry at {path} and allow_cache=True was requested. "
            "Run with network access once to populate the cache, or commit a "
            "fixture registry for tests."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [IndicatorDefinition(**item) for item in payload]
