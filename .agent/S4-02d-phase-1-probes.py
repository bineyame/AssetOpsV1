"""S4-02d phase 1 non-vacuity probes: each mutation must make its guard or test fail; every file is restored with
`git checkout --` (run only on a clean, committed tree).

    python .agent/S4-02d-phase-1-probes.py guard|tests

`guard` mutates the schedule writer and its neighbours and expects `tools/check-architecture.ps1` to fail with the
named message. `tests` mutates behaviour and expects the named Postgres test to fail (needs
ASSETOPS_TEST_DATABASE_URL).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = "backend/assetops_backend"
STORE = f"{B}/scheduling/adapters/postgres_schedule_store.py"
TICK = f"{B}/scheduling/tick.py"
STAGES = f"{B}/scheduling/stages.py"
TESTS = "backend/tests/test_s4_schedule_tick_postgres.py"

GUARD = [
    ("unlisted column", STORE, "SET s3_processed = :p, s3_deferred = :d WHERE",
     "SET s3_processed = :p, s3_deferred = :d, created_at = clock_timestamp() WHERE",
     "may not update schedule_site_head.created_at"),
    ("unlisted table insert", STORE, 'INSERT INTO schedule_cursor (environment, updated_at) "',
     'INSERT INTO recompute_job (environment, updated_at) "', "The schedule store only inserts into"),
    ("unlisted table update", STORE, "UPDATE schedule_cursor SET after_tenant_id",
     "UPDATE recompute_job SET after_tenant_id", "The schedule store updates only"),
    ("delete", STORE, "def db_now(self) -> datetime:",
     "def db_now(self) -> datetime:\n        _x = \"DELETE FROM schedule_cursor WHERE environment = :e\"",
     "never deletes, truncates, upserts or runs DDL"),
    ("upsert", STORE, "VALUES (:e, clock_timestamp()) ON CONFLICT DO NOTHING\"), p)\n            c.execute(text(\n",
     "VALUES (:e, clock_timestamp()) ON CONFLICT (environment) DO UPDATE SET after_site_id = NULL\"), p)\n"
     "            c.execute(text(\n", "never deletes, truncates, upserts or runs DDL"),
    ("split update", STORE, '"UPDATE schedule_site_head SET stage = :st, stage_started_at = clock_timestamp() WHERE',
     '"UPDATE schedule_site_head SET stage = :st, "\n            "stage_started_at = clock_timestamp() WHERE',
     "keeps its table, SET list and WHERE on one line"),
    ("non-literal set list", STORE, "SET s3_processed = :p, s3_deferred = :d WHERE",
     "SET {cols} WHERE", "names its SET columns literally"),
    ("second module writes schedule", TICK, "S4_OK = (",
     "_X = \"UPDATE schedule_tick_head SET heartbeat_at = now() WHERE environment = 'x'\"\nS4_OK = (",
     "A second product database writer"),
    ("other writer writes schedule", f"{B}/financials/adapters/postgres_consequence_store.py",
     "    def pending_work_sites(self)",
     "    _X = \"INSERT INTO schedule_cursor (environment, updated_at) VALUES ('x', now())\"\n\n"
     "    def pending_work_sites(self)", "writes schedule table 'schedule_cursor'"),
    ("driver outside writers", TICK, "import json\n", "import json\nimport sqlalchemy\n",
     "Database driver imported outside"),
    ("adapter import outside composition", TICK, "import json\n",
     "import json\nfrom assetops_backend.scheduling.adapters.postgres_schedule_store import PostgresScheduleStore\n",
     "adapters"),
    ("vacuous writer", STORE,
     "from sqlalchemy import create_engine, text\nfrom sqlalchemy.engine import Connection, Engine\n"
     "from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError\n", "",
     "found no SQL write or driver import"),
]

TESTS_PROBES = [
    ("S4 always runs", STAGES, 'if args.get("matched_version") == MATCHER_VERSION and',
     'if False and args.get("matched_version") == MATCHER_VERSION and', "TestConditionalMatchAndCurrentness"),
    ("completed fence omits own revisions", STAGES,
     "finding_revisions=out.fence.finding_revisions + len(out.revision_ids)",
     "finding_revisions=out.fence.finding_revisions", "TestConditionalMatchAndCurrentness"),
    ("global S3 lease", f"{B}/analytics/adapters/postgres_assessment_store.py",
     'scope = "" if site_id is None else " AND tenant_id = :t AND site_id = :s"\n        scoped',
     'scope = ""\n        scoped', "TestInventoryAndIsolation"),
    ("gateway-only Site selected", TICK, '(site["has_evidence"] or site["enrolled"])', "True",
     "TestInventoryAndIsolation"),
    ("Site claim ignores holder", STORE,
     '"AND (claim_token IS NULL OR lease_until < clock_timestamp()) RETURNING " + _SITE_HEAD',
     '"RETURNING " + _SITE_HEAD', "test_two_concurrent_ticks_and_a_held_site_claim"),
    ("no server timeouts in stage children", TICK, '        env["PGOPTIONS"] = (', '        env["UNUSED"] = (',
     "TestKillableStagesAndServerTimeouts"),
]


def restore(path: str) -> None:
    subprocess.run(["git", "checkout", "--", path], cwd=ROOT, check=True)


def mutate(path: str, old: str, new: str) -> None:
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    assert old in text, f"probe anchor not found in {path}: {old!r}"
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


def main(kind: str, only: str | None = None) -> int:
    failed = 0
    for name, path, old, new, expect in (GUARD if kind == "guard" else TESTS_PROBES):
        if only and only != name:
            continue
        mutate(path, old, new)
        try:
            if kind == "guard":
                out = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                                      "tools/check-architecture.ps1"], cwd=ROOT, capture_output=True, text=True)
                ok = out.returncode != 0 and expect in (out.stdout + out.stderr)
            else:
                out = subprocess.run([sys.executable, "-m", "pytest", TESTS, "-x", "-q", "-p", "no:cacheprovider",
                                      "-k", expect], cwd=ROOT, capture_output=True, text=True)
                ok = out.returncode == 1 and " failed" in out.stdout
        finally:
            restore(path)
        failed += not ok
        print(f"{'CAUGHT' if ok else 'MISSED'}  {name}", flush=True)
    clean = subprocess.run(["git", "status", "--porcelain", "--", "backend", "tools"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    print("tree restored" if not clean else f"tree NOT clean:\n{clean}")
    return 1 if failed or clean else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
