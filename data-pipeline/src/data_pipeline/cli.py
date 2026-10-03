"""
Usage:
    python -m data_pipeline ingest --all
    python -m data_pipeline ingest --indicator I1589 --indicator I2790
    python -m data_pipeline ingest --all --trigger cron

`--all` resolves indicators *dynamically* from the shared registry
(app/api/registry/route.ts, which re-exports the existing TS
HCP_INDICATORS array) -- there is no second, hand-maintained list of ids
anywhere in this package. Whatever the registry currently contains is what
gets ingested, whether that's 9, 28, or any other number.

Exit code is non-zero if any indicator's overall_status is ERROR, so this
is safe to wire into cron/CI alerting.
"""
from __future__ import annotations

import argparse
import sys
from typing import List

from data_pipeline.ingestion.run import RunSummary, run_ingestion
from data_pipeline.registry.client import RegistryUnavailableError, fetch_registry
from data_pipeline.registry.models import IndicatorDefinition
from data_pipeline.storage.db import create_all, make_engine, make_session_factory


def resolve_indicators(
    registry: List[IndicatorDefinition],
    indicator_ids: List[str],
    use_all: bool,
) -> List[IndicatorDefinition]:
    """Pure resolution logic, independent of argparse, so it can be tested
    directly: --all must return every indicator currently in the registry,
    and only the registry decides what that set is."""
    if use_all:
        return list(registry)
    resolved = []
    for indicator_id in indicator_ids:
        match = next((i for i in registry if i.id == indicator_id), None)
        if match is None:
            raise ValueError(f"'{indicator_id}' is not in the registry.")
        resolved.append(match)
    return resolved


def _truncate(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


def _print_report(reports) -> None:
    cols = ["ID", "TITLE", "HTTP", "PARSED", "VALIDATION", "CANONICAL", "STATUS"]
    widths = [14, 46, 6, 8, 18, 11, 9]
    header = "".join(c.ljust(w) for c, w in zip(cols, widths))
    print(header)
    print("-" * len(header))
    for r in reports:
        counts = r.validation_counts
        validation_str = f"{counts.get('PASS', 0)}P/{counts.get('WARNING', 0)}W/{counts.get('ERROR', 0)}E"
        row = [
            r.indicator_id,
            _truncate(r.title, widths[1] - 2),
            str(r.http_status),
            str(r.records_parsed),
            validation_str,
            str(r.canonical_inserted),
            r.overall_status,
        ]
        print("".join(str(v).ljust(w) for v, w in zip(row, widths)))


def _print_summary(summary: RunSummary) -> None:
    print()
    print(f"Total requested:             {summary.total_requested}")
    print(f"Successful:                  {summary.successful}")
    print(f"Warnings:                    {summary.warnings}")
    print(f"Errors:                      {summary.errors}")
    print(f"Raw objects written:         {summary.raw_objects_written}")
    print(f"Canonical observations written: {summary.canonical_observations_written}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="data_pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest_parser = sub.add_parser("ingest")
    ingest_parser.add_argument("--indicator", action="append", default=[], help="Indicator id, repeatable")
    ingest_parser.add_argument("--all", action="store_true", help="Ingest every indicator currently in the registry")
    ingest_parser.add_argument("--trigger", default="manual", choices=["manual", "cron", "test"])
    ingest_parser.add_argument(
        "--allow-registry-cache", action="store_true",
        help="Read the registry from the local test cache instead of the network. "
             "Never use this for a production run.",
    )
    ingest_parser.add_argument(
        "--create-tables", action="store_true",
        help="Create tables if they don't exist (for local/dev DBs only; production uses Alembic).",
    )

    args = parser.parse_args(argv)

    try:
        registry = fetch_registry(allow_cache=args.allow_registry_cache)
    except RegistryUnavailableError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 2

    if not args.all and not args.indicator:
        print("FATAL: pass --all or one or more --indicator.", file=sys.stderr)
        return 2

    try:
        indicators = resolve_indicators(registry, args.indicator, args.all)
    except ValueError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 2

    engine = make_engine()
    if args.create_tables:
        create_all(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        reports = run_ingestion(session, indicators, trigger=args.trigger)

    summary = RunSummary.from_reports(reports)
    print(f"\nRun summary — {summary.total_requested} indicator(s) requested, all individually reported below\n")
    _print_report(reports)
    _print_summary(summary)

    return 1 if summary.errors > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
