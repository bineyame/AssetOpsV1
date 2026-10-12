"""S3-01 owner walkthrough: Performance > Dispatch over a private copy of the dispatch-case database.

    .venv/Scripts/python.exe tools/s3_dispatch_walkthrough.py prepare   # copy DB, run comparison, stage states
    .venv/Scripts/python.exe tools/s3_dispatch_walkthrough.py serve     # API on 8820 until Ctrl+C
    .venv/Scripts/python.exe tools/s3_dispatch_walkthrough.py recover   # optional: real worker clears staged days

Isolation (like the S2 demo):
- Database `assetops_s3walk` is dropped and recreated as a copy of `assetops_s3cases`
  (the reviewed `s3-dispatch-cases-v1` producer output). The producer database and
  the developer database are only read.
- Code is `git archive HEAD` into `%LOCALAPPDATA%/AssetOps/s3-dispatch-walkthrough/tree`
  with its own `var/`; nothing is written to this repository's `var/`.
- Ports: API 8820, frontend 5320 (start it from `frontend/` as printed).

Staged states (walkthrough database only, labelled as such in the owner notes):
- 2026-10-05: a PENDING recompute job, as when a new accepted record waits for the worker
  (the selected result stays visible but STALE, `RECOMPUTE_OUTSTANDING`).
- 2026-10-07: a recompute that fails on every attempt (a deliberately broken model run by
  this script) so the read shows FAILED with the prior selection still open.
Their 6-hour read bracket also touches the neighbouring days (10-04, 10-06, 10-08). The
reviewer days 10-01, 10-02, 10-03 and 10-09 are untouched.
"""

from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = REPO / ".venv" / "Scripts" / "python.exe"
if not PY.exists():  # POSIX venv layout
    PY = REPO / ".venv" / "bin" / "python"
WORK = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AssetOps" / "s3-dispatch-walkthrough"
SOURCE_DB, DB = "assetops_s3cases", "assetops_s3walk"
PRODUCER_MANIFEST = WORK.parent / "s3-dispatch-cases" / "s3-dispatch-cases-v1.json"
# The producer's own manifest names the evidence IDs of the database copied here (the committed
# `.agent/S3-01-dispatch-cases-v1.manifest.json` is from an earlier producer run and matches no ID).
MANIFEST = WORK / "s3-dispatch-cases-v1.json"
PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
DB_URL = f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{DB}"
STALE_DAY, FAILED_DAY = "2026-10-05", "2026-10-07"

STAGE = r'''
import sys
from datetime import datetime, timedelta, timezone
from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
from assetops_backend.analytics.assessment_inputs import Window
from assetops_backend.analytics.assessment_worker import DispatchAssessmentWorker
from assetops_backend.evidence.composition import build_evidence_ledger

url, stale_day, failed_day = sys.argv[1:4]
tenant, site = build_evidence_ledger(url).site_scope("demo", "KOBO-001")
store = PostgresAssessmentStore(url)
now = datetime.now(timezone.utc)

def day(text):
    start = datetime.fromisoformat(text + "T00:00:00+00:00")
    return Window(start, start + timedelta(days=1))

class StagedFailure:
    """Walkthrough-only: a model run that always fails, to show the FAILED read with the prior selection."""
    ANALYTIC_ID, MODEL_VERSION = "dispatch", "dispatch-3.1"

    @staticmethod
    def assess(_inputs):
        raise RuntimeError("walkthrough staged failure: the assessment could not be computed")

if len(sys.argv) > 4 and sys.argv[4] == "recover":
    for d in (failed_day, stale_day):
        store.enqueue(tenant, site, "dispatch", day(d), now)
    done = DispatchAssessmentWorker(store).run_pending(reconcile=False)
    print("recovered: the real worker ran", len(done), "jobs")
    raise SystemExit(0)

store.enqueue(tenant, site, "dispatch", day(failed_day), now)
for attempt in range(3):
    DispatchAssessmentWorker(store, model=StagedFailure, clock=lambda: now + timedelta(seconds=attempt),
                             backoff=timedelta(0)).run_pending(reconcile=False)
store.enqueue(tenant, site, "dispatch", day(stale_day), now + timedelta(minutes=1))
print("staged: FAILED", failed_day, "and PENDING", stale_day)
'''


def say(text: str = "") -> None:
    print(text, flush=True)


def env() -> dict[str, str]:
    tree = WORK / "tree"
    out = dict(os.environ)
    out["PYTHONPATH"] = os.pathsep.join(str(tree / p) for p in ("backend", "gateway", "simulator", "contracts", "host"))
    out["DATABASE_URL"] = DB_URL
    out["ASSETOPS_DEMO_FIXTURE_MANIFEST"] = str(MANIFEST)
    out["PYTHONUNBUFFERED"] = "1"
    out.pop("ASSETOPS_TEST_DATABASE_URL", None)
    return out


def py(*argv: str, check: bool = True) -> subprocess.CompletedProcess:
    done = subprocess.run([str(PY), *argv], cwd=str(WORK / "tree"), env=env(), capture_output=True, text=True,
                          timeout=900)
    if check and done.returncode != 0:
        raise SystemExit(f"FAILED: python {' '.join(argv[:3])}\n{done.stdout}\n{done.stderr}")
    return done


def prepare() -> None:
    import psycopg

    for needed, hint in (
        (PRODUCER_MANIFEST, "run the dispatch-case producer first (tools/s3_dispatch_cases.py)"),
        (REPO / "var" / "sites" / "kobo-001.yaml", "the Kobo site configuration is missing"),
    ):
        if not needed.exists():
            raise SystemExit(f"Missing prerequisite {needed}: {hint}")
    say("=== 1. Private work tree (git HEAD) with its own var/ ===")
    tree = WORK / "tree"
    if tree.exists():
        shutil.rmtree(tree)
    tree.mkdir(parents=True)
    archive = subprocess.run(["git", "archive", "--format=tar", "HEAD", "backend", "gateway", "host", "simulator",
                              "contracts", "config", "contract-fixtures"], cwd=REPO, capture_output=True,
                             check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(tree, filter="data")
    (tree / "var" / "sites").mkdir(parents=True)
    shutil.copy2(REPO / "var" / "sites" / "kobo-001.yaml", tree / "var" / "sites" / "kobo-001.yaml")
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout
    say(f"  {tree} (code from {head.strip()})")
    probe = py("-c", "import assetops_backend;print(assetops_backend.__file__)").stdout.strip()
    if str(tree).lower() not in probe.lower():
        raise SystemExit(f"Isolation failed: assetops_backend resolves to {probe}")

    shutil.copy2(PRODUCER_MANIFEST, MANIFEST)
    say(f"  demo manifest: {MANIFEST} (copied from the producer work directory)")

    say(f"=== 2. Database {DB} as a copy of {SOURCE_DB} ===")
    with psycopg.connect(f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {DB} WITH (FORCE)")
        c.execute(f"CREATE DATABASE {DB} TEMPLATE {SOURCE_DB}")
    say("  copied")

    say("=== 3. File-backed comparison (writes the report into the private tree only) ===")
    done = py("-m", "assetops_backend.performance_migration", "run", "--tenant", "demo", "--site", "KOBO-001",
              check=False)
    say("  " + done.stdout.strip().replace("\n", "\n  "))
    if done.returncode != 0:
        raise SystemExit(
            f"FAILED: the file-backed comparison did not pass (exit {done.returncode}); the dispatch read stays "
            f"closed, so nothing is ready to show.\n{done.stderr.strip()}"
        )

    say(f"=== 4. Staged states: FAILED {FAILED_DAY}, PENDING {STALE_DAY} (walkthrough database only) ===")
    say("  " + py("-c", STAGE, DB_URL, STALE_DAY, FAILED_DAY).stdout.strip())
    say("Prepared. Next: serve.")


def serve(port: int) -> None:
    logs = WORK / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    log = (logs / "api.log").open("a", encoding="utf-8")
    proc = subprocess.Popen([str(PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(port)],
                            cwd=str(WORK / "tree" / "host"), env=env(), stdout=log, stderr=subprocess.STDOUT)
    say(f"API on http://127.0.0.1:{port} (log {logs / 'api.log'}), pid {proc.pid}")
    say(f'Frontend, from frontend/:  $env:ASSETOPS_API_PORT="{port}"; npm.cmd run dev -- --port 5320 --strictPort')
    say("Then open http://localhost:5320/sites/KOBO-001/performance/dispatch?day=2026-10-09 . Ctrl+C stops the API.")
    try:
        while proc.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=20)
    sys.exit(proc.returncode or 0)


def main() -> None:
    parser = argparse.ArgumentParser(prog="tools/s3_dispatch_walkthrough.py")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    sub.add_parser("recover", help="run the real worker over the staged days (FAILED and STALE become CURRENT)")
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=8820)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "recover":
        say(py("-c", STAGE, DB_URL, STALE_DAY, FAILED_DAY, "recover").stdout.strip())
    else:
        serve(args.port)


if __name__ == "__main__":
    main()
