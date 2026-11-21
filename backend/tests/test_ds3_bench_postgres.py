"""DS3 (spec `specs/DS3-bulk-loader/spec.md` §5; D-DS3.16): the measurement DS4 re-runs. Opt-in and slow.

    ASSETOPS_DS3_BENCH=1 tools/heavy-slot.sh --db -- pwsh -NoProfile -File tools/run-host-tests.ps1 -- \\
        backend/tests/test_ds3_bench_postgres.py -s

Fourteen Kobo days (6 to 19 October, spec §3's rows) loaded once by central ingestion and once by the bulk load, each
into its own clone of one seed (`ds3bseed`, `ds3breal`, `ds3bbulk`, dropped in `finally`). Prints one JSON line: wall
time, rows written per table, `pg_total_relation_size` before and after, and statements per target table. It asserts
nothing about time; no figure here is a gate.
"""

from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from datetime import timedelta

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"),
    pytest.mark.skipif(os.environ.get("ASSETOPS_DS3_BENCH") != "1", reason="opt-in: set ASSETOPS_DS3_BENCH=1"),
]

if URL:
    from sqlalchemy import create_engine, event, text
    from test_ds3_bulk_load_postgres import DAY6, census, kobo_days, seed_database

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.bulk_load import BulkEvidenceLoad
    from assetops_backend.evidence.ledger_service import BatchIngestionService

DAYS = 14
SIZED = ("ingestion_batch", "accepted_evidence", "ingestion_disposition", "recompute_job", "chain_input_change")
_TARGET = re.compile(r"(?is)^\s*(?:INSERT\s+INTO|UPDATE)\s+([a-z_]+)")


def _sizes(url: str) -> dict[str, int]:
    eng = create_engine(url)
    try:
        with eng.connect() as c:
            return {t: c.execute(text("SELECT pg_total_relation_size(CAST(:t AS regclass))"), {"t": t}).scalar_one()
                    for t in SIZED}
    finally:
        eng.dispose()


def _rows(url: str) -> dict[str, int]:
    eng = create_engine(url)
    try:
        with eng.connect() as c:
            return census(c)
    finally:
        eng.dispose()


def _measure(url: str, ledger, run) -> dict:
    statements: Counter = Counter()
    engine = ledger._connect_engine()

    @event.listens_for(engine, "before_cursor_execute")
    def count(conn, cursor, statement, parameters, context, executemany):  # noqa: ARG001
        match = _TARGET.match(statement)
        if match:
            statements[match.group(1).lower()] += 1

    rows_before, sizes_before = _rows(url), _sizes(url)
    start = time.perf_counter()
    run()
    wall = time.perf_counter() - start
    pg_harness.dispose(ledger)
    rows_after, sizes_after = _rows(url), _sizes(url)
    return {
        "wall_seconds": round(wall, 3),
        "rows": {t: rows_after[t] - rows_before[t] for t in sorted(rows_after) if rows_after[t] != rows_before[t]},
        "bytes_before": sizes_before, "bytes_after": sizes_after,
        "statements": dict(sorted(statements.items())),
    }


def test_measure_fourteen_kobo_days_by_both_paths() -> None:
    seed, kit, _ = seed_database("ds3bseed")
    urls = [seed]
    try:
        real = pg_harness.clone_database("ds3breal", seed)
        urls.append(real)
        bulk = pg_harness.clone_database("ds3bbulk", seed)
        urls.append(bulk)
        batches = kobo_days(kit, [DAY6 + timedelta(days=d) for d in range(DAYS)])

        real_ledger = PostgresEvidenceLedger(real)
        service = BatchIngestionService(real_ledger)

        def submit_all() -> None:
            for body in batches:
                assert service.submit(kit.principal, body).status == 200

        bulk_ledger = PostgresEvidenceLedger(bulk)
        result = {
            "days": DAYS, "batches": len(batches),
            "real": _measure(real, real_ledger, submit_all),
            "bulk": _measure(bulk, bulk_ledger, lambda: BulkEvidenceLoad(bulk_ledger).load(batches)),
            "statement_counter": "sqlalchemy before_cursor_execute (INSERT/UPDATE targets)",
        }
        print("\nDS3_BENCH " + json.dumps(result, sort_keys=True))
    finally:
        for url in urls:
            pg_harness.drop_database(url)
