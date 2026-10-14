"""S4-02d phase 2 non-vacuity probes: each mutation must make its named test fail; every file is restored with
`git checkout --` (run only on a clean, committed tree; needs ASSETOPS_TEST_DATABASE_URL for the Postgres tests).

    python .agent/S4-02d-phase-2-probes.py [name]
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = "backend/assetops_backend"
TICK, STAGES = f"{B}/scheduling/tick.py", f"{B}/scheduling/stages.py"
HEALTH, UP = f"{B}/scheduling/health.py", f"{B}/scheduling/upstream.py"
STORE = f"{B}/scheduling/adapters/postgres_schedule_store.py"
CLI = f"{B}/recompute_consequences.py"
PG = "backend/tests/test_s4_schedule_health_postgres.py"
UNIT = "backend/tests/test_s4_schedule_upstream_unit.py"

PROBES = [
    ("F2 Site back-off ignored", TICK,
     'if head and head["retry_due_at"] is not None and head["retry_due_at"] > self.store.db_now():', "if False:",
     PG, "test_f2"),
    ("F3 lost claim ignored", TICK, "if self.store.set_stage(t, s, token, name):",
     "if self.store.set_stage(t, s, token, name) or True:", PG, "test_f3"),
    ("seam reads heartbeat only (Q1)", UP, '        for o in observation:\n            blockers.append(("SCHEDULE", o["code"]))\n',
     "", PG, "test_repeated_claim_skips"),
    ("seam ignores a stopped environment", UP, 'blockers.append(("SCHEDULE", "SCHEDULE_STOPPED"))', "pass", PG,
     "test_pending_current_stale"),
    ("seam ignores unmatched selection", UP, 'blockers.append(("S4", "MATCH_PENDING"))', "pass", PG,
     "test_fence_moved_streak"),
    ("seam ignores selection moved during read", UP, 'blockers.append(("S4", "SELECTION_MOVED_DURING_READ"))',
     "pass", UNIT, "selection_committed"),
    ("seam ignores outstanding consequence work", UP, 'blockers.append(("CONSEQUENCE", "WORK_OUTSTANDING"))',
     "pass", PG, "test_skewed"),
    ("seam ignores consequence state", UP, "            if state != \"CURRENT\":\n", "            if False:\n", PG,
     "test_a_pre_0012"),
    ("heartbeat threshold ignored", HEALTH, "elif (now - beat).total_seconds() > th.stop_after_seconds:",
     "elif False:", PG, "test_pending_current_stale"),
    ("claim-skip alarm ignored", HEALTH, 'if int(head.get("claim_skips") or 0) >= th.claim_skip_alarm:',
     "if False:", PG, "test_repeated_claim_skips"),
    ("stale claim ignored", HEALTH,
     'if head.get("claim_token") is not None and head.get("lease_until") is not None and head["lease_until"] < now:',
     "if False:", PG, "test_repeated_claim_skips"),
    ("S4 backlog outside active set dropped", HEALTH, "if s4_backlog and not active:", "if False:", PG,
     "test_fence_moved_streak"),
    ("terminal S3 failure not alarmed", HEALTH, 'failed_jobs = [j for j in live if j["status"] == "FAILED"]',
     "failed_jobs = []", PG, "test_fence_moved_streak"),
    ("attempt growth not alarmed", HEALTH, "        if grown:\n", "        if False:\n", PG, "test_skewed"),
    ("streak not cleared on unchanged fence", STORE,
     "fence_moved_streak = 0 WHERE tenant_id = :t AND site_id = :s \"  # noqa: E501\n"
     "                   \"AND claim_token = :k RETURNING site_id\")\n        else:",
     "fence_moved_streak = fence_moved_streak WHERE tenant_id = :t AND site_id = :s \"  # noqa: E501\n"
     "                   \"AND claim_token = :k RETURNING site_id\")\n        else:", PG, "test_fence_moved_streak"),
    ("I3 S3 stage on the app clock", STAGES,
     "build_dispatch_assessment_worker(url, clock=db_clock(url)).run_site(",
     "build_dispatch_assessment_worker(url).run_site(", PG, "test_skewed"),
    ("I3 matcher on the app clock", STAGES, "    matcher.now = db_clock(url)", "    pass", PG, "test_skewed"),
    ("I3 scheduled drain on the app clock", STAGES, 'now=datetime.fromisoformat(args["now"]))', "now=None)", PG,
     "test_skewed"),
    ("I3 discover reconcile on the app clock", STAGES,
     "build_dispatch_assessment_worker(url, clock=db_clock(url)).reconcile_all()",
     "build_dispatch_assessment_worker(url).reconcile_all()", PG, "test_skewed"),
    ("I4 seam ignores S3 (race reads falsely CURRENT)", UP,
     ['                blockers.append(("S3", f"S3_{status}"))', '            blockers.append(("S3", "LIVE_JOB"))'],
     ["                pass", "            pass"], PG, "Overlapping"),
    ("I3 one-off drain on the app clock", CLI, "elif db_clock is not None or worker is None:", "elif False:", PG,
     "test_skewed"),
]


def restore(path: str) -> None:
    subprocess.run(["git", "checkout", "--", path], cwd=ROOT, check=True)


def main(only: str | None = None) -> int:
    failed = 0
    for name, path, old, new, tests, expr in PROBES:
        if only and only != name:
            continue
        file = ROOT / path
        text = file.read_text(encoding="utf-8")
        for o, n in (zip(old, new) if isinstance(old, list) else [(old, new)]):
            assert o in text, f"probe anchor not found in {path}: {o!r}"
            text = text.replace(o, n, 1)
        file.write_text(text, encoding="utf-8")
        try:
            out = subprocess.run([sys.executable, "-m", "pytest", tests, "-x", "-q", "-p", "no:cacheprovider",
                                  "-k", expr], cwd=ROOT, capture_output=True, text=True)
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
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
