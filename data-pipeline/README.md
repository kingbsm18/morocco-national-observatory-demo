# data-pipeline (Phase 1)

HCP ingestion pipeline: FETCH → STORE RAW → PARSE → VALIDATE → STORE CANONICAL.

Does not touch the existing Next.js frontend except for one new,
purely-additive file: `app/api/registry/route.ts`, which re-exports the
existing `HCP_INDICATORS` array from `lib/data/hcp-indicators.ts` as JSON so
this pipeline has one source of truth for the indicator registry, read over
HTTP instead of copy-pasted.

## Setup

```bash
cd data-pipeline
pip install -e ".[dev]"
cp .env.example .env   # set DATABASE_URL, REGISTRY_URL
```

Schema is managed by Alembic:

```bash
alembic upgrade head
```

## Running ingestion

```bash
# all indicators, reading the registry live from the running Next.js app
python -m data_pipeline ingest --all

# specific indicators
python -m data_pipeline ingest --indicator I1589 --indicator I2790
```

`REGISTRY_URL` defaults to `http://localhost:3000/api/registry`. In
production, point it at the deployed site. **Never pass
`--allow-registry-cache` in production** — it exists only so tests can run
without network access; a real ingestion run must fail loudly if it can't
reach the registry, not silently use a stale copy.

## Tests

```bash
pytest
```

### A note on the test fixtures

`tests/fixtures/hcp_responses/*.json` are **synthetic, schema-accurate
fixtures**, not live-recorded HCP responses — the sandbox this code was
written in has no network path to `bds.hcp.ma`, so they were built to match
the exact response shape the existing `normalizeHcpIndicator` /
`validateIndicatorIntegrity` logic expects (same `code`/`label`/`metaData`/
`dimensions`/`data` structure, same `modalityId_period` key format), using
the real titles/units/sources from the registry for the 9 agreed test
indicators.

They're enough to prove the parser, validation engine, and the
cross-contamination regression test behave correctly. They are **not** a
substitute for recording real HCP responses before trusting this pipeline
against production data. Before relying on this test suite as a true
regression guard against live HCP drift, replace these fixtures with actual
recorded responses (e.g. via a one-off `curl` per indicator, saved verbatim).

## What this phase deliberately does not do

No ML, no forecasting, no Airflow/Prefect/Kafka, no FastAPI migration, no
frontend cut-over. The frontend still talks to HCP directly today; this
pipeline runs independently and populates Postgres in parallel, ready for a
Phase 2 cut-over once verified against real HCP responses.
