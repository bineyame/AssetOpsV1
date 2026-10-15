"""OPS-02 rule 8 writer-guard mutation corpus: the statement-level writer guard must refuse each negative probe for its
ownership reason and accept the controls. Every mutation appends module-level code to one backend module, runs the
guard, and restores the module with `git checkout --`, so run it only on a clean, committed tree.

    python tools/writer_guard_probes.py [--seam] [probe-name ...]

The default runner is `tools/check-architecture.ps1` (about 70 s a probe). `--seam` runs only the configuration-
persistence module that holds rule 8 (about 14 s a probe); use it while iterating and the default for evidence.
The guard's Python is this interpreter (passed as ASSETOPS_GUARD_PYTHON).

Sets:
- `F-B n`: the 11 forms `.agent/S4-02d-phase-2-review.md` F-B recorded as missed by the line-based guard.
- `split <writer>`: a two-line UPDATE of a table the writer does not own (S4-05a phase-1 review L1), one per writer.
- `reverse <table family>`: a two-line write by the Foundation store into another writer's table.
- `dynamic ...` / `core ...` / `fragment` / `cte` / `upsert` / `second writer`: unresolved or non-text forms.
- `controls`: allowed multiline SQL, case, aliases, reads, docstrings and comments in one run, which must pass.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = "backend/assetops_backend"
SCHEDULE = f"{B}/scheduling/adapters/postgres_schedule_store.py"
FOUNDATION = f"{B}/sites/adapters/postgres_foundation_store.py"
LEDGER = f"{B}/evidence/adapters/postgres_evidence_ledger.py"
ACCESS = f"{B}/evidence/adapters/postgres_gateway_access.py"
ASSESS = f"{B}/analytics/adapters/postgres_assessment_store.py"
FINDING = f"{B}/analytics/adapters/postgres_finding_store.py"
ASSUMPTION = f"{B}/financials/adapters/postgres_assumption_store.py"
CONSEQUENCE = f"{B}/financials/adapters/postgres_consequence_store.py"
TICK = f"{B}/scheduling/tick.py"

NEVER = "never deletes, truncates, upserts or runs DDL"
SCHED_TABLES = "The schedule store updates only"
MERGE_COPY = "No product writer runs MERGE or COPY"
LITERAL_TARGET = "names its target table literally"


def split(table: str, rest: str) -> str:
    """A two-line UPDATE: implicit concatenation across lines, the ordinary formatting of a long statement."""
    return f'_OPS02 = (\n    "UPDATE {table} "\n    "SET {rest}"\n)\n'


# (name, module, appended source, expected failure text)
NEGATIVE: list[tuple[str, str, str, str]] = [
    ("F-B 1 split other-table update", SCHEDULE, split("site", "lifecycle = :l WHERE tenant_id = :t"), SCHED_TABLES),
    ("F-B 2 split unlisted schedule column", SCHEDULE,
     split("schedule_site_head", "created_at = now() WHERE tenant_id = :t"),
     "may not update schedule_site_head.created_at"),
    ("F-B 3 split lowercase delete", SCHEDULE,
     '_OPS02 = (\n    "delete "\n    "from schedule_cursor where environment = :e"\n)\n', NEVER),
    ("F-B 4 triple-quoted update", SCHEDULE,
     '_OPS02 = """\nUPDATE site\nSET lifecycle = :l\nWHERE tenant_id = :t\n"""\n', SCHED_TABLES),
    ("F-B 5 escaped newline", SCHEDULE,
     '_OPS02 = "UPDATE site\\nSET lifecycle = :l WHERE tenant_id = :t"\n', SCHED_TABLES),
    ("F-B 6 comment-separated update", SCHEDULE,
     '_OPS02 = "UPDATE/**/site/**/SET lifecycle = :l WHERE tenant_id = :t"\n', SCHED_TABLES),
    ("F-B 7 comment-separated delete", SCHEDULE, '_OPS02 = "delete/**/from site where tenant_id = :t"\n', NEVER),
    ("F-B 8 merge", SCHEDULE,
     '_OPS02 = "MERGE INTO site s USING (SELECT 1) x ON true WHEN MATCHED THEN UPDATE SET lifecycle = \'x\'"\n',
     MERGE_COPY),
    ("F-B 9 core update", SCHEDULE,
     'from sqlalchemy import table, update\n_OPS02 = update(table("site")).values(lifecycle="x").where(True)\n',
     SCHED_TABLES),
    ("F-B 10 core delete", SCHEDULE,
     'from sqlalchemy import delete, table\n_OPS02 = delete(table("schedule_cursor"))\n', NEVER),
    ("F-B 11 lowercase copy", SCHEDULE, '_OPS02 = "copy site from stdin"\n', MERGE_COPY),
    # S4-05a phase-1 review L1: a two-line UPDATE is checked for every writer, not only the schedule store.
    ("split foundation", FOUNDATION, split("ingestion_batch", "processed_count = 0 WHERE id = :i"),
     "The Foundation store must not write ledger table 'ingestion_batch'"),
    ("split ledger", LEDGER, split("site", "lifecycle = :l WHERE id = :i"), "The evidence ledger writes only"),
    ("split access", ACCESS, split("gateway", "name = :n WHERE id = :g"), "The gateway access store inserts only"),
    ("split assessment", ASSESS, split("recompute_job", "site_id = :s WHERE id = :id"),
     "The assessment store inserts only"),
    ("split finding", FINDING, split("finding", "lifecycle = :l WHERE id = :i"), "The Finding store only inserts"),
    ("split assumption", ASSUMPTION, split("financial_assumption_revision", "value = :v WHERE id = :i"),
     "The assumption store only inserts"),
    ("split consequence", CONSEQUENCE, split("financial_consequence_revision", "amount = :a WHERE id = :i"),
     "The consequence store only inserts"),
    ("reverse finding", FOUNDATION, split("finding_revision", "lifecycle = :l WHERE id = :i"),
     "writes Finding table 'finding_revision'"),
    ("reverse assessment", FOUNDATION, split("assessment_revision", "scope = :s WHERE id = :i"),
     "writes assessment table 'assessment_revision'"),
    ("reverse access", FOUNDATION, split("gateway_credential", "revoked_at = now() WHERE id = :i"),
     "writes gateway access table 'gateway_credential'"),
    ("reverse assumption", FOUNDATION, split("financial_assumption_assignment", "recorded_to = now() WHERE id = :i"),
     "writes assumption table 'financial_assumption_assignment'"),
    ("reverse consequence", FOUNDATION, split("financial_consequence_revision", "amount = 0 WHERE id = :i"),
     "writes consequence table 'financial_consequence_revision'"),
    ("reverse schedule", FOUNDATION, split("schedule_cursor", "after_site_id = NULL WHERE environment = :e"),
     "writes schedule table 'schedule_cursor'"),
    ("reverse consequence work", CONSEQUENCE,
     '_OPS02 = (\n    "INSERT INTO financial_consequence_work "\n    "(id) VALUES (:i)"\n)\n',
     "Dirty consequence work is inserted only by the migration"),
    ("second writer split", TICK, split("schedule_tick_head", "heartbeat_at = now() WHERE environment = 'x'"),
     "A second product database writer"),
    ("dynamic f-string target", SCHEDULE,
     '_T = "site"\n_OPS02 = f"UPDATE {_T} SET stage = :s WHERE tenant_id = :t"\n', LITERAL_TARGET),
    ("dynamic percent target", FOUNDATION, '_T = "site"\n_OPS02 = "DELETE FROM %s WHERE id = :i" % _T\n',
     LITERAL_TARGET),
    ("dynamic format target", FOUNDATION, '_T = "site"\n_OPS02 = "INSERT INTO {} (id) VALUES (:i)".format(_T)\n',
     LITERAL_TARGET),
    ("dynamic set list", SCHEDULE,
     '_C = "created_at = now()"\n_OPS02 = "UPDATE schedule_site_head SET " + _C + " WHERE tenant_id = :t"\n',
     "names its SET columns literally"),
    ("fragment augmented assignment", FOUNDATION,
     '_OPS02 = "UPDATE site"\n_OPS02 += " SET lifecycle = :l WHERE id = :i"\n', "ends before its SET, VALUES or WHERE clause"),
    ("core aliased postgres insert", SCHEDULE,
     'from sqlalchemy import table\nfrom sqlalchemy.dialects.postgresql import insert as pg_insert\n'
     '_OPS02 = pg_insert(table("finding")).values(id=1)\n', "The schedule store only inserts into"),
    ("core dynamic table", FOUNDATION,
     'from sqlalchemy import update\n_T = None\n_OPS02 = update(_T).values(lifecycle="x")\n', LITERAL_TARGET),
    ("core table method", SCHEDULE, 'from sqlalchemy import table\n_OPS02 = table("schedule_cursor").delete()\n',
     NEVER),
    ("core module attribute", FINDING,
     'import sqlalchemy as sa\n_OPS02 = sa.update(sa.table("finding")).values(lifecycle="x")\n',
     "The Finding store only inserts"),
    ("core module postgresql insert", FINDING,
     'from sqlalchemy.dialects import postgresql\nfrom sqlalchemy import table\n'
     '_OPS02 = postgresql.insert(table("site")).values(id=1)\n', "The Finding store only inserts"),
    ("core module sql delete", FINDING,
     'from sqlalchemy import sql, table\n_OPS02 = sql.delete(table("finding"))\n', "The Finding store only inserts"),
    ("core fully dotted insert", FINDING,
     'import sqlalchemy\n_OPS02 = sqlalchemy.dialects.postgresql.insert(sqlalchemy.table("site")).values(id=1)\n',
     "The Finding store only inserts"),
    ("L1 keyword alias update", FINDING, '_OPS02 = "UPDATE site AS copy SET lifecycle = :l WHERE id = :i"\n',
     "The Finding store only inserts"),
    ("L2 quoted comment marker", FINDING,
     '_OPS02 = "SELECT \'--\' AS x; DELETE FROM site WHERE id = 1"\n', "The Finding store only inserts"),
    ("L2 bytes delete", FINDING, '_OPS02 = b"DELETE FROM site WHERE id = 1"\n', "The Finding store only inserts"),
    ("L3 lowercase fragment", FINDING, '_OPS02 = "update site"\n_OPS02 += " set lifecycle = :l"\n',
     "ends before its SET, VALUES or WHERE clause"),
    ("cte delete in finding", FINDING,
     '_OPS02 = "WITH x AS (DELETE FROM finding WHERE id = :i RETURNING id) SELECT 1"\n',
     "The Finding store only inserts"),
    ("split upsert", SCHEDULE,
     '_OPS02 = (\n    "INSERT INTO schedule_cursor (environment) VALUES (:e) "\n'
     '    "ON CONFLICT (environment) DO UPDATE SET after_site_id = NULL"\n)\n', NEVER),
    ("copy in foundation", FOUNDATION, '_OPS02 = "COPY site (id) FROM STDIN"\n', MERGE_COPY),
]

CONTROLS = (
    '_OPS02_A = """\nUPDATE schedule_site_head\nSET stage = :st,\n    stage_started_at = clock_timestamp()\n'
    'WHERE tenant_id = :t\n"""\n'
    '_OPS02_B = "update schedule_cursor set after_tenant_id = :t where environment = :e"\n'
    '_OPS02_C = (\n    "UPDATE schedule_enrolment "\n    "SET enrolled = :n, changed_at = clock_timestamp() "\n'
    '    "WHERE tenant_id = :t"\n)\n'
    '_OPS02_D = "UPDATE schedule_cursor AS c SET after_site_id = :s WHERE c.environment = :e"\n'
    '_OPS02_E = "Update Schedule_Cursor Set after_site_id = :s Where environment = :e"\n'
    '_OPS02_F = "SELECT h.stage FROM schedule_site_head h JOIN site s ON s.id = h.site_id WHERE h.tenant_id = :t '
    'FOR UPDATE OF h SKIP LOCKED"\n'
    '_OPS02_G = "SELECT updated_at FROM site WHERE lifecycle = \'update\'"\n'
    '_OPS02_H = "INSERT INTO schedule_cursor (environment, updated_at) VALUES (:e, now()) ON CONFLICT DO NOTHING"\n'
    '# DELETE FROM site WHERE id = 1 (a comment is not executed)\n'
    'def _ops02_doc():\n    """UPDATE site SET lifecycle = :l WHERE id = :i is documented here, never executed."""\n'
)


def restore(path: str) -> None:
    subprocess.run(["git", "checkout", "--", path], cwd=ROOT, check=True)


def run_guard(seam: bool) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, ASSETOPS_GUARD_PYTHON=sys.executable)
    if seam:
        script = ('$ErrorActionPreference = "Stop"; . (Join-Path $PWD "tools/checks/_common.ps1"); '
                  '. (Join-Path $PWD "tools/checks/configuration-persistence.ps1"); '
                  '$f = @(Invoke-ConfigurationPersistenceCheck); '
                  'if ($f.Count -gt 0) { $f | ForEach-Object { Write-Output "- $_" }; exit 1 }; Write-Output "passed"')
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script]
    else:
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "tools/check-architecture.ps1"]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)


def probe(path: str, appended: str, seam: bool) -> subprocess.CompletedProcess[str]:
    file = ROOT / path
    original = file.read_text(encoding="utf-8")
    try:
        file.write_text(original.rstrip("\n") + "\n\n\n" + appended, encoding="utf-8")
        return run_guard(seam)
    finally:
        restore(path)


def main(argv: list[str]) -> int:
    seam = "--seam" in argv
    only = [a for a in argv if a != "--seam"]
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "backend"], cwd=ROOT, capture_output=True,
                           text=True).stdout.strip()
    if dirty:
        print(f"refusing to run on a dirty backend tree:\n{dirty}", file=sys.stderr)
        return 2
    failed = 0
    for name, path, appended, expect in NEGATIVE:
        if only and name not in only:
            continue
        out = probe(path, appended, seam)
        text = out.stdout + out.stderr
        ok = out.returncode != 0 and expect in text
        failed += not ok
        print(f"{'CAUGHT' if ok else 'MISSED'}  {name}", flush=True)
        if not ok:
            print("    expected: " + expect + "\n    " + "\n    ".join(text.strip().splitlines()[-6:]), flush=True)
    if not only or "controls" in only:
        out = probe(SCHEDULE, CONTROLS, seam)
        ok = out.returncode == 0
        failed += not ok
        print(f"{'ALLOWED' if ok else 'REFUSED'}  controls", flush=True)
        if not ok:
            print("    " + "\n    ".join((out.stdout + out.stderr).strip().splitlines()[-10:]), flush=True)
    clean = subprocess.run(["git", "status", "--porcelain", "--", "backend", "tools"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    print("tree restored" if not clean else f"tree NOT clean:\n{clean}")
    return 1 if failed or clean else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
