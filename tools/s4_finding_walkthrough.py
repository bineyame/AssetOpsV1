"""S4-01 owner walkthrough: the Site Finding detail over a private copy of the Finding-case database.

    .venv/Scripts/python.exe tools/s4_finding_cases.py run          # first: the reviewed fixture producer
    .venv/Scripts/python.exe tools/s4_finding_walkthrough.py prepare  # copy DB, run comparison, stage one day
    .venv/Scripts/python.exe tools/s4_finding_walkthrough.py links    # print the walkthrough addresses
    .venv/Scripts/python.exe tools/s4_finding_walkthrough.py serve    # API on 8840 until Ctrl+C
    .venv/Scripts/python.exe tools/s4_finding_walkthrough.py recover  # optional: real worker clears the staged day

A second, private walkthrough (for example an evidence-capture run) names its own database and work folder,
before the subcommand or through the environment (ASSETOPS_S4_WALK_DB / ASSETOPS_S4_WALK_WORK); the defaults
below are unchanged when neither is given:
    python tools/s4_finding_walkthrough.py --db assetops_s403p2_walk --work <private folder> prepare
    python tools/s4_finding_walkthrough.py --db ... --work ... close-gate  # move the private tree's comparison
                                                                          # reports aside: the cutover reads closed
    python tools/s4_finding_walkthrough.py --db ... --work ... open-gate   # undo close-gate
    python tools/s4_finding_walkthrough.py --db ... --work ... drop        # DROP DATABASE ... WITH (FORCE), then
                                                                          # remove the work folder if not the default
Protected databases (developer, producer, other slices' walkthrough and test databases) are refused as --db,
and a private work folder must name its own database (never the default assetops_s4walk).

Isolation (like the S3 walkthrough):
- Database `assetops_s4walk` is dropped and recreated as a copy of `assetops_s4cases` (the
  `s4-finding-cases-v1` producer output). The producer database and the developer database are only read.
- Code is `git archive HEAD` into `%LOCALAPPDATA%/AssetOps/s4-finding-walkthrough/tree` with its own `var/`;
  nothing is written to this repository's `var/`.
- Ports: API 8840, frontend 5340 (start it from `frontend/` as printed). No other port is used.

Staged state (walkthrough database only, labelled as such in the owner notes):
- 2026-10-09: a PENDING recompute job, as when a new accepted record waits for the worker. The F02
  cross-midnight Finding (10-08 23:20 onward) then reads "Out of date" while its recorded version stays visible.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
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
APPDATA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AssetOps"
DEFAULT_WORK = APPDATA / "s4-finding-walkthrough"
SOURCE_DB, DEFAULT_DB = "assetops_s4cases", "assetops_s4walk"
# Never a walkthrough target: the developer, producer, other slices' walkthrough and the shared test databases.
PROTECTED_DBS = {"assetops", "assetops_test", SOURCE_DB, "assetops_s3cases", "assetops_s3walk", "assetops_s2demo"}
PROTECTED_DB_MARKERS = ("v01a", "v01b", "g01")
PRODUCER = APPDATA / "s4-finding-cases"
PRODUCER_MANIFEST = PRODUCER / "s4-finding-cases-manifest.json"
PRODUCER_RUN = PRODUCER / "s4-finding-cases-run.json"
PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
GATE_DIR = Path("var") / "evidence" / "migration-performance"
# Set by configure(); module-level so every subcommand reads one place.
WORK = DEFAULT_WORK
WORK_MARKER = ".s4-walkthrough-work"  # written by `prepare`; `drop` deletes only a folder that has it
DB = DEFAULT_DB
MANIFEST = WORK / "s4-finding-cases-manifest.json"
RUN = WORK / "s4-finding-cases-run.json"
DB_URL = f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{DB}"


def configure(db: str | None, work: str | None) -> None:
    """Pick the walkthrough database and work folder: flag, then environment, then the defaults."""
    global WORK, DB, MANIFEST, RUN, DB_URL
    db = db or os.environ.get("ASSETOPS_S4_WALK_DB") or DEFAULT_DB
    work_path = Path(work or os.environ.get("ASSETOPS_S4_WALK_WORK") or DEFAULT_WORK).resolve()
    default_work = work_path == DEFAULT_WORK.resolve()
    if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", db):
        raise SystemExit(f"Refused: database name {db!r} is not a plain lower-case identifier")
    if db in PROTECTED_DBS or any(m in db for m in PROTECTED_DB_MARKERS):
        raise SystemExit(f"Refused: {db} is a protected database and is never a walkthrough copy")
    if db == DEFAULT_DB and not default_work:
        raise SystemExit(f"Refused: a private work folder must name its own database, not {DEFAULT_DB}")
    if not default_work and work_path in (PRODUCER.resolve(), APPDATA.resolve(), REPO.resolve()):
        raise SystemExit(f"Refused: {work_path} is not a private work folder")
    WORK, DB = work_path, db
    MANIFEST = WORK / "s4-finding-cases-manifest.json"
    RUN = WORK / "s4-finding-cases-run.json"
    DB_URL = f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{DB}"
STALE_DAY = "2026-10-09"
API_PORT, WEB_PORT = 8840, 5340

STAGE = r'''
import sys
from datetime import datetime, timedelta, timezone
from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
from assetops_backend.analytics.assessment_inputs import Window
from assetops_backend.analytics.assessment_worker import DispatchAssessmentWorker
from assetops_backend.evidence.composition import build_evidence_ledger

url, stale_day = sys.argv[1:3]
tenant, site = build_evidence_ledger(url).site_scope("demo", "KOBO-001")
store = PostgresAssessmentStore(url)
now = datetime.now(timezone.utc)
start = datetime.fromisoformat(stale_day + "T00:00:00+00:00")
store.enqueue(tenant, site, "dispatch", Window(start, start + timedelta(days=1)), now)
if len(sys.argv) > 3 and sys.argv[3] == "recover":
    done = DispatchAssessmentWorker(store).run_pending(reconcile=False)
    print("recovered: the real worker ran", len(done), "jobs")
else:
    print("staged: PENDING", stale_day)
'''

# The walkthrough's named Findings, by fixture case and the anchor the producer records (exact IDs vary per run).
CASES = (
    ("F01 open (fault-fixture case, 2026-10-06)", "2026-10-06 08:00"),
    ("F01-gateway open (ordinary gateway path, 2026-10-02, template minimum on-time)", "2026-10-02 05:15"),
    ("F02 cross-midnight, same ID (staged out of date)", "2026-10-08 23:20"),
    ("F03 earlier episode", "2026-10-11 08:00"),
    ("F03 recurrence", "2026-10-11 09:30"),
    ("F04 late earlier record, same ID", "2026-10-13 08:30"),
    ("F05 not confirmed, then no longer supported", "2026-10-21 08:00"),
    ("F06 split original", "2026-10-15 08:00"),
    ("F06 split part", "2026-10-15 09:15"),
    ("F06 merged (canonical)", "2026-10-15 12:00"),
    ("F06 merged (joined into canonical)", "2026-10-15 13:00"),
)


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


def refuse_foreign_work() -> None:
    """Review N4: `prepare` marks only a folder it creates (or one it marked before). An existing non-empty
    `--work` folder without the marker is someone else's folder, so it is refused before anything is written."""
    if WORK == DEFAULT_WORK.resolve() or not WORK.exists() or (WORK / WORK_MARKER).is_file():
        return
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise SystemExit(f"Refusing --work {WORK}: it already exists, is not empty and has no {WORK_MARKER} marker, "
                         "so this tool did not create it. Choose a new folder name.")


def prepare() -> None:
    import psycopg

    for needed, hint in (
        (PRODUCER_MANIFEST, "run the Finding-case producer first (tools/s4_finding_cases.py run)"),
        (PRODUCER_RUN, "run the Finding-case producer first (tools/s4_finding_cases.py run)"),
        (REPO / "var" / "sites" / "kobo-001.yaml", "the Kobo site configuration is missing"),
    ):
        if not needed.exists():
            raise SystemExit(f"Missing prerequisite {needed}: {hint}")
    refuse_foreign_work()
    say("=== 1. Private work tree (git HEAD) with its own var/ ===")
    tree = WORK / "tree"
    if tree.exists():
        shutil.rmtree(tree)
    tree.mkdir(parents=True)
    (WORK / WORK_MARKER).write_text("created by tools/s4_finding_walkthrough.py prepare\n", encoding="utf-8")
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
    shutil.copy2(PRODUCER_RUN, RUN)
    say(f"  demo manifest and run record copied from {PRODUCER}")

    say(f"=== 2. Database {DB} as a copy of {SOURCE_DB} ===")
    with psycopg.connect(f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {DB} WITH (FORCE)")
        c.execute(f"CREATE DATABASE {DB} TEMPLATE {SOURCE_DB}")
    say("  copied")

    say("=== 3. File-backed comparison (opens the Performance cutover gate if it passes) ===")
    done = py("-m", "assetops_backend.performance_migration", "run", "--tenant", "demo", "--site", "KOBO-001",
              check=False)
    say("  " + done.stdout.strip().replace("\n", "\n  "))
    if done.returncode != 0:
        say(f"  The comparison did not pass (exit {done.returncode}); the Finding detail will show its "
            f"'not released' state and only exact version links open, as audit records.")
        say("  " + done.stderr.strip().replace("\n", "\n  "))

    say(f"=== 4. Staged state: PENDING {STALE_DAY} (walkthrough database only) ===")
    say("  " + py("-c", STAGE, DB_URL, STALE_DAY).stdout.strip())
    say("Prepared. Next: links, then serve.")


def links(web: int) -> None:
    run = json.loads(RUN.read_text(encoding="utf-8"))
    by_anchor = {f["anchor_start"][:16]: f for f in run["findings"]}
    base = f"http://localhost:{web}/sites/KOBO-001/findings"
    say(f"Producer run from commit {run.get('produced_from_commit')} (status {run.get('status')}).")
    for label, anchor in CASES:
        f = by_anchor.get(anchor)
        if f is None:
            say(f"- {label}: not in this run (anchor {anchor})")
            continue
        say(f"- {label}: {base}/{f['finding_id']}")
        say(f"    Evidence (latest version at read time): {base}/{f['finding_id']}/evidence")
        revisions = f["revisions"]
        if len(revisions) > 1:
            for n, rev in enumerate(revisions, start=1):
                say(f"    version {n} ({rev['transition']}): {base}/{f['finding_id']}?revision_id={rev['revision_id']}")
        for n, rev in enumerate(revisions, start=1):
            say(f"    version {n} Evidence: {base}/{f['finding_id']}/evidence?revision_id={rev['revision_id']}")
        say(f"    History (latest version at read time): {base}/{f['finding_id']}/history")
        for n, rev in enumerate(revisions, start=1):
            say(f"    version {n} History: {base}/{f['finding_id']}/history?revision_id={rev['revision_id']}")
    dispatch = f"http://localhost:{web}/sites/KOBO-001/performance/dispatch"
    say(f"- Dispatch day with a Finding link: {dispatch}?day=2026-10-06")
    say(f"- Dispatch day that could not be decided (not a no-Finding result): {dispatch}?day=2026-10-19")
    say(f"- Dispatch day with no assessment, so a Finding is not known either way: {dispatch}?day=2026-10-07")
    say(f"- Another day with no assessment in this fixture: {dispatch}?day=2026-10-25")
    say("  (The fixture has no fully assessed day with no Finding; 2026-10-25 is NOT_ASSESSED, not 'no Finding'.)")


def serve(port: int, web: int) -> None:
    logs = WORK / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    log = (logs / "api.log").open("a", encoding="utf-8")
    proc = subprocess.Popen([str(PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(port)],
                            cwd=str(WORK / "tree" / "host"), env=env(), stdout=log, stderr=subprocess.STDOUT)
    say(f"API on http://127.0.0.1:{port} (log {logs / 'api.log'}), pid {proc.pid}")
    say(f'Frontend, from frontend/:  $env:ASSETOPS_API_PORT="{port}"; npm.cmd run dev -- --port {web} --strictPort')
    say("Then open the addresses printed by `links`. Ctrl+C stops the API; stop the frontend with Ctrl+C too.")
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


def gate(close: bool) -> None:
    """Close (move the comparison reports aside) or reopen the private tree's Performance cutover gate."""
    if WORK == DEFAULT_WORK.resolve():
        raise SystemExit("Refused: close-gate/open-gate act only on a private (non-default) work folder")
    live = WORK / "tree" / GATE_DIR
    aside = live.with_name(live.name + ".closed")
    src, dst = (live, aside) if close else (aside, live)
    if not src.exists():
        raise SystemExit(f"Nothing to move: {src} does not exist")
    if dst.exists():
        raise SystemExit(f"Refused: {dst} already exists")
    src.rename(dst)
    say(f"{'Closed' if close else 'Reopened'}: moved {src} -> {dst}")


def drop(include_default: bool) -> None:
    """Drop the walkthrough database WITH (FORCE); remove the work folder only when it is not the default."""
    import psycopg

    if DB == DEFAULT_DB and not include_default:
        raise SystemExit(f"Refused: dropping the default {DEFAULT_DB} needs --include-default")
    with psycopg.connect(f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {DB} WITH (FORCE)")
    say(f"Dropped database {DB}")
    if WORK != DEFAULT_WORK.resolve() and WORK.exists() and (WORK / WORK_MARKER).is_file():
        shutil.rmtree(WORK)
        say(f"Removed work folder {WORK}")
    elif WORK != DEFAULT_WORK.resolve() and WORK.exists():
        say(f"Kept work folder {WORK}: it has no {WORK_MARKER} marker, so `prepare` did not create it")
    else:
        say(f"Kept work folder {WORK}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="tools/s4_finding_walkthrough.py")
    parser.add_argument("--db", help=f"walkthrough database (env ASSETOPS_S4_WALK_DB; default {DEFAULT_DB})")
    parser.add_argument("--work", help=f"work folder (env ASSETOPS_S4_WALK_WORK; default {DEFAULT_WORK})")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    sub.add_parser("close-gate", help="private work folder only: the Performance cutover then reads closed")
    sub.add_parser("open-gate", help="private work folder only: undo close-gate")
    dr = sub.add_parser("drop", help="drop the walkthrough database, and the work folder unless it is the default")
    dr.add_argument("--include-default", action="store_true", help=f"allow dropping {DEFAULT_DB}")
    sub.add_parser("recover", help="run the real worker over the staged day (it becomes current again)")
    lk = sub.add_parser("links")
    lk.add_argument("--web-port", type=int, default=WEB_PORT)
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=API_PORT)
    s.add_argument("--web-port", type=int, default=WEB_PORT)
    args = parser.parse_args()
    configure(args.db, args.work)
    say(f"(walkthrough database {DB}, work folder {WORK})")
    if args.command == "prepare":
        prepare()
    elif args.command in ("close-gate", "open-gate"):
        gate(args.command == "close-gate")
    elif args.command == "drop":
        drop(args.include_default)
    elif args.command == "recover":
        say(py("-c", STAGE, DB_URL, STALE_DAY, "recover").stdout.strip())
    elif args.command == "links":
        links(args.web_port)
    else:
        serve(args.port, args.web_port)


if __name__ == "__main__":
    main()
