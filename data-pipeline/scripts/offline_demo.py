"""
DEV/OFFLINE USE ONLY -- never use this for a production ingestion run.

Runs `ingest --all` through the real CLI/pipeline code path, with only the
network fetch (sources.hcp.client.fetch_raw) swapped for the committed
synthetic fixtures in tests/fixtures/hcp_responses/. Registry resolution,
storage, validation, and CLI reporting are all the genuine production code --
nothing about the pipeline logic itself is mocked.

This exists because this repo's reference environment (the one this pipeline
was originally developed and tested in) had no network path to bds.hcp.ma.
Once you have real network access to HCP, just run the normal command
instead:

    python -m data_pipeline ingest --all

Usage:
    DATABASE_URL=sqlite:////tmp/demo.db python scripts/offline_demo.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))

os.environ.setdefault("REGISTRY_CACHE_PATH", "tests/fixtures/registry_cache.json")

import data_pipeline.ingestion.run as run_mod  # noqa: E402
from data_pipeline.sources.hcp.client import RawFetchResult  # noqa: E402
from conftest import load_fixture, _REGISTRY_SUBSET  # noqa: E402

FIXTURES = {iid: load_fixture(iid) for iid in _REGISTRY_SUBSET}


def fake_fetch_raw(api_url: str) -> RawFetchResult:
    indicator_id = api_url.rsplit("/", 1)[-1]
    payload = FIXTURES[indicator_id]
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return RawFetchResult(
        url=api_url,
        http_status=200,
        retrieved_at=datetime.now(timezone.utc),
        checksum=hashlib.sha256(body).hexdigest(),
        raw_payload=payload,
    )


def main() -> int:
    run_mod.fetch_raw = fake_fetch_raw  # the only thing swapped
    from data_pipeline.cli import main as cli_main

    return cli_main(["ingest", "--all", "--allow-registry-cache", "--create-tables", "--trigger", "test"])


if __name__ == "__main__":
    raise SystemExit(main())
