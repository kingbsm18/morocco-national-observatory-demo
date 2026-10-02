"""
Usage:
    python -m data_pipeline ingest --all
    python -m data_pipeline ingest --indicator I1589 --indicator I2790
    python -m data_pipeline ingest --all --trigger cron

Exit code is non-zero if any indicator ended in 'blocked_error' or
'fetch_failed', so this is safe to wire into cron/CI alerting.
"""
from __future__ import annotations

import argparse
import sys

from data_pipeline.ingestion.run import run_ingestion
from data_pipeline.registry.client import RegistryUnavailableError, fetch_registry, get_indicator
from data_pipeline.storage.db import create_all, make_engine, make_session_factory


def _print_report(reports) -> None:
    header = f"{'INDICATOR':<14}{'HTTP':<6}{'CHECKSUM':<12}{'PARSED':<8}{'PASS':<6}{'WARN':<6}{'ERR':<6}{'INSERTED':<10}{'STATUS'}"
    print(header)
    print("-" * len(header))
    for r in reports:
        checksum_short = (r.checksum or "")[:10]
        counts = r.validation_counts
        print(
            f"{r.indicator_id:<14}{r.http_status:<6}{checksum_short:<12}{r.records_parsed:<8}"
            f"{counts.get('PASS', 0):<6}{counts.get('WARNING', 0):<6}{counts.get('ERROR', 0):<6}"
            f"{r.canonical_inserted:<10}{r.status}"
        )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="data_pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest_parser = sub.add_parser("ingest")
    ingest_parser.add_argument("--indicator", action="append", default=[], help="Indicator id, repeatable")
    ingest_parser.add_argument("--all", action="store_true", help="Ingest every active indicator in the registry")
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

    if args.all:
        indicators = registry
    elif args.indicator:
        indicators = []
        for indicator_id in args.indicator:
            found = get_indicator(registry, indicator_id)
            if found is None:
                print(f"FATAL: '{indicator_id}' is not in the registry.", file=sys.stderr)
                return 2
            indicators.append(found)
    else:
        print("FATAL: pass --all or one or more --indicator.", file=sys.stderr)
        return 2

    engine = make_engine()
    if args.create_tables:
        create_all(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        reports = run_ingestion(session, indicators, trigger=args.trigger)

    print(f"\nRun summary — {len(reports)} indicator(s)")
    _print_report(reports)

    any_error = any(r.status in ("blocked_error", "fetch_failed") for r in reports)
    return 1 if any_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
