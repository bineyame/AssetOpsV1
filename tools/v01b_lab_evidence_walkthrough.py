"""V-01b owner walkthrough: Lab (Gateway & Ingestion) and Site Evidence over private copies.

    .venv/Scripts/python.exe tools/s4_finding_cases.py run                  # first: the reviewed fixture producer
    .venv/Scripts/python.exe tools/v01b_lab_evidence_walkthrough.py prepare # copy DB, Lab files and gateway ledger
    .venv/Scripts/python.exe tools/v01b_lab_evidence_walkthrough.py links   # print the walkthrough addresses
    .venv/Scripts/python.exe tools/v01b_lab_evidence_walkthrough.py serve   # gateway + both APIs until Ctrl+C

Isolation (like the V-01a walkthrough):
- Database `assetops_v01bwalk` is dropped and recreated as a copy of `assetops_s4cases`: the KOBO-001
  Site, its accepted Evidence, rejections, deliveries and the registered Lab run's central receipt.
  The producer database is only read.
- Database `assetops_v01bempty` is dropped and recreated empty and migrated (no Site), for the honest
  "No such site" Evidence state.
- Code is `git archive HEAD` into `%LOCALAPPDATA%/AssetOps/v01b-lab-evidence-walkthrough/tree`. The
  producer's Lab files (`var/runs`, `executions`, `publication-schedules`, `sites`) are copied into that
  tree's own `var/`; nothing is written to this repository's `var/` or to the producer's folder.
- The producer's gateway ledger (SQLite) is copied with the SQLite backup API into `<work>/gateway`,
  its local credential and upload credential are copied and restricted to the current user, and its
  config is rewritten to a private pipe name. Its upload target is an unused local port, so the copy
  never delivers anything: the ledger is shown exactly as the producer left it.
- Ports: populated API 8862 / web 5362, empty API 8863 / web 5363. No other port is used.

A second copy (an implementer's or reviewer's private run) must not reuse the owner's databases, tree
or ports. Global options, given before the command, override the defaults:

    tools/v01b_lab_evidence_walkthrough.py --db assetops_v01bimpl --empty-db assetops_v01bimplempty \
        --work-name v01b-impl prepare
    tools/v01b_lab_evidence_walkthrough.py --db ... --empty-db ... --work-name ... serve \
        --port 8884 --web-port 5384 --empty-port 8885 --empty-web-port 5385
    tools/v01b_lab_evidence_walkthrough.py --db ... --empty-db ... --work-name ... drop

`drop` refuses the owner's default database names unless `--allow-default` is given.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = REPO / ".venv" / "Scripts" / "python.exe"
if not PY.exists():  # POSIX venv layout
    PY = REPO / ".venv" / "bin" / "python"
WORK = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AssetOps" / "v01b-lab-evidence-walkthrough"
SOURCE_DB, DB, EMPTY_DB = "assetops_s4cases", "assetops_v01bwalk", "assetops_v01bempty"
DEFAULT_DB, DEFAULT_EMPTY_DB, DEFAULT_WORK_NAME = DB, EMPTY_DB, WORK.name
PRODUCER = WORK.parent / "s4-finding-cases"
PRODUCER_MANIFEST = PRODUCER / "s4-finding-cases-manifest.json"
PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
API_PORT, WEB_PORT, EMPTY_API_PORT, EMPTY_WEB_PORT = 8862, 5362, 8863, 5363
LAB_DIRS = ("runs", "executions", "publication-schedules", "sites")
#: An unused local port: the copied gateway may try to upload, and must never reach a real server.
DEAD_UPLOAD = "https://127.0.0.1:9"
# Evidence windows on the stored KOBO-001 data. The producer's accepted readings are on 2026-10-02;
# 2026-09-01 is before any reading (the honest "nothing received" state).
POPULATED_WINDOW = ("2026-10-02T00:00:00Z", "2026-10-03T00:00:00Z")
EMPTY_WINDOW = ("2026-09-01T00:00:00Z", "2026-09-02T00:00:00Z")


def configure(db: str, empty_db: str, work_name: str) -> None:
    """Point this run at its own databases and work tree; defaults are the owner's walkthrough."""
    global WORK, DB, EMPTY_DB
    for name in (db, empty_db):
        if not name.isidentifier() or not name.startswith("assetops_") or name == SOURCE_DB:
            raise SystemExit(f"Refusing database name {name!r}: use assetops_<name>, not the producer database")
    if not work_name or any(ch in work_name for ch in "/\\:") or work_name in (".", ".."):
        raise SystemExit(f"Refusing work-tree name {work_name!r}")
    WORK = WORK.parent / work_name
    DB, EMPTY_DB = db, empty_db


def say(text: str = "") -> None:
    print(text, flush=True)


def db_url(name: str) -> str:
    return f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{name}"


def gateway_address() -> str:
    if sys.platform == "win32":
        return rf"\\.\pipe\assetops-{WORK.name}-gateway"
    return str(WORK / "gateway" / "gw.sock")


def env(database: str, tree: Path, with_gateway: bool) -> dict[str, str]:
    out = dict(os.environ)
    out["PYTHONPATH"] = os.pathsep.join(str(tree / p) for p in ("backend", "gateway", "simulator", "contracts", "host"))
    out["DATABASE_URL"] = db_url(database)
    out["ASSETOPS_DEMO_FIXTURE_MANIFEST"] = str(WORK / "s4-finding-cases-manifest.json")
    out["PYTHONUNBUFFERED"] = "1"
    out.pop("ASSETOPS_TEST_DATABASE_URL", None)
    for key in ("ASSETOPS_GATEWAY_ADDRESS", "ASSETOPS_GATEWAY_CREDENTIAL"):
        out.pop(key, None)
    if with_gateway:
        out["ASSETOPS_GATEWAY_ADDRESS"] = gateway_address()
        out["ASSETOPS_GATEWAY_CREDENTIAL"] = str(WORK / "gateway" / "gateway.credential")
    return out


def extract_tree(tree: Path, with_lab: bool) -> None:
    if tree.exists():
        shutil.rmtree(tree)
    tree.mkdir(parents=True)
    archive = subprocess.run(["git", "archive", "--format=tar", "HEAD", "backend", "gateway", "host", "simulator",
                              "contracts", "config", "contract-fixtures"], cwd=REPO, capture_output=True,
                             check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(tree, filter="data")
    (tree / "var").mkdir(parents=True)
    if with_lab:
        for name in LAB_DIRS:
            source = PRODUCER / "tree" / "var" / name
            if source.exists():
                shutil.copytree(source, tree / "var" / name)
    else:
        (tree / "var" / "sites").mkdir()


def protect(path: Path) -> None:
    subprocess.run([str(PY), "-c", "import sys;from pathlib import Path;"
                    "from assetops_gateway.credential_protection import restrict_to_current_user as r;"
                    "r(Path(sys.argv[1]))", str(path)], cwd=str(WORK / "tree"),
                   env=env(DB, WORK / "tree", False), check=True, capture_output=True)


def copy_gateway() -> None:
    """A private copy of the producer's gateway ledger that can be read but never delivers."""
    source, target = PRODUCER / "gateway", WORK / "gateway"
    if target.exists():
        shutil.rmtree(target)
    (target).mkdir(parents=True)
    with sqlite3.connect(f"file:{(source / 'gateway.sqlite3').as_posix()}?mode=ro", uri=True) as src, \
            sqlite3.connect(target / "gateway.sqlite3") as dst:
        src.backup(dst)
    config = json.loads((source / "gateway.json").read_text(encoding="utf-8"))
    shutil.copy2(source / "gateway.credential", target / "gateway.credential")
    protect(target / "gateway.credential")
    upload = config.get("upload", {})
    if upload.get("upload_credential_file"):
        cred = Path(upload["upload_credential_file"])
        (target / "credentials").mkdir()
        shutil.copy2(cred, target / "credentials" / cred.name)
        protect(target / "credentials" / cred.name)
        upload["upload_credential_file"] = str(target / "credentials" / cred.name)
    if upload.get("ca_file"):
        shutil.copy2(upload["ca_file"], target / "server.crt")
        upload["ca_file"] = str(target / "server.crt")
    upload["server_url"] = DEAD_UPLOAD
    config["address"] = gateway_address()
    (target / "gateway.json").write_text(json.dumps(config, indent=2), encoding="utf-8")


def prepare() -> None:
    import psycopg

    for needed, hint in (
        (PRODUCER_MANIFEST, "run the Finding-case producer first (tools/s4_finding_cases.py run)"),
        (PRODUCER / "tree" / "var" / "runs", "the producer's Lab run files are missing"),
        (PRODUCER / "gateway" / "gateway.sqlite3", "the producer's gateway ledger is missing"),
    ):
        if not needed.exists():
            raise SystemExit(f"Missing prerequisite {needed}: {hint}")
    say("=== 1. Private work trees (git HEAD) with their own var/ ===")
    extract_tree(WORK / "tree", with_lab=True)
    extract_tree(WORK / "tree-empty", with_lab=False)
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout
    say(f"  {WORK / 'tree'} (Lab files copied) and {WORK / 'tree-empty'} (code from {head.strip()})")
    probe = subprocess.run([str(PY), "-c", "import assetops_backend;print(assetops_backend.__file__)"],
                           cwd=str(WORK / "tree"), env=env(DB, WORK / "tree", False), capture_output=True,
                           text=True).stdout.strip()
    if str(WORK / "tree").lower() not in probe.lower():
        raise SystemExit(f"Isolation failed: assetops_backend resolves to {probe}")
    shutil.copy2(PRODUCER_MANIFEST, WORK / "s4-finding-cases-manifest.json")

    say("=== 2. Gateway ledger copy (private pipe, no delivery) ===")
    copy_gateway()
    say(f"  {WORK / 'gateway'} on {gateway_address()}; upload target {DEAD_UPLOAD} (never reached)")

    say(f"=== 3. Database {DB} as a copy of {SOURCE_DB}; {EMPTY_DB} empty ===")
    with psycopg.connect(f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {DB} WITH (FORCE)")
        c.execute(f"CREATE DATABASE {DB} TEMPLATE {SOURCE_DB}")
        c.execute(f"DROP DATABASE IF EXISTS {EMPTY_DB} WITH (FORCE)")
        c.execute(f"CREATE DATABASE {EMPTY_DB}")
    done = subprocess.run([str(PY), "-m", "alembic", "upgrade", "head"], cwd=str(WORK / "tree-empty" / "backend"),
                          env=env(EMPTY_DB, WORK / "tree-empty", False), capture_output=True, text=True, timeout=600)
    if done.returncode != 0:
        raise SystemExit(f"FAILED: alembic upgrade on {EMPTY_DB}\n{done.stdout}\n{done.stderr}")
    say("  copied; empty database migrated")

    say("=== 4. Evidence store comparison (opens the Site Evidence ledger read if it passes) ===")
    done = subprocess.run([str(PY), "-m", "assetops_backend.evidence_migration", "run", "--tenant", "demo", "--site",
                           "KOBO-001"], cwd=str(WORK / "tree"), env=env(DB, WORK / "tree", False),
                          capture_output=True, text=True, timeout=900)
    say("  " + (done.stdout.strip() or done.stderr.strip()).replace("\n", "\n  "))
    if done.returncode != 0:
        say(f"  The comparison did not pass (exit {done.returncode}); Site Evidence will show "
            "'Awaiting evidence migration', which is that honest state.")
    say("Prepared. Next: links, then serve.")


def run_ids() -> list[str]:
    runs = WORK / "tree" / "var" / "runs"
    return sorted(p.stem for p in runs.glob("run-*.yaml")) if runs.exists() else []


def links(web: int, empty_web: int) -> None:
    site = f"http://localhost:{web}/sites/KOBO-001/evidence"
    lab = f"http://localhost:{web}/simulator-lab"
    pf, pt = POPULATED_WINDOW
    ef, et = EMPTY_WINDOW
    say("Site Evidence (KOBO-001):")
    say(f"- Overview, populated day:        {site}?from={pf}&to={pt}")
    say(f"- Analysis, populated day:        {site}?view=analysis&from={pf}&to={pt}")
    say(f"- Overview, nothing received:     {site}?from={ef}&to={et}")
    say(f"- Analysis, nothing received:     {site}?view=analysis&from={ef}&to={et}")
    say(f"- Default window (no address):    {site}")
    say(f"- No such site (empty store):     http://localhost:{empty_web}/sites/KOBO-001/evidence")
    say("Simulator Lab:")
    say(f"- Runs:                           {lab}/runs")
    for run in run_ids():
        say(f"- Gateway & Ingestion ({run}): {lab}/runs/{run}")
    say(f"- Runs, empty store:              http://localhost:{empty_web}/simulator-lab/runs")


def wait_ready(url: str, timeout: float = 90) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(url, timeout=3):
                return True
        except Exception:  # noqa: BLE001 - polling until the server answers
            time.sleep(1)
    return False


def serve(port: int, web: int, empty_port: int, empty_web: int) -> None:
    logs = WORK / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    procs = []
    glog = (logs / "gateway.log").open("a", encoding="utf-8")
    procs.append(subprocess.Popen([str(PY), "-m", "assetops_gateway", "serve", "--config",
                                   str(WORK / "gateway" / "gateway.json")], cwd=str(WORK / "gateway"),
                                  env=env(DB, WORK / "tree", False), stdout=glog, stderr=subprocess.STDOUT))
    say(f"gateway on {gateway_address()} (log {logs / 'gateway.log'}), pid {procs[-1].pid}")
    time.sleep(3)
    for name, database, tree, p, gw in (("api", DB, WORK / "tree", port, True),
                                        ("api-empty", EMPTY_DB, WORK / "tree-empty", empty_port, False)):
        log = (logs / f"{name}.log").open("a", encoding="utf-8")
        procs.append(subprocess.Popen([str(PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port",
                                       str(p)], cwd=str(tree / "host"), env=env(database, tree, gw), stdout=log,
                                      stderr=subprocess.STDOUT))
        say(f"{name} on http://127.0.0.1:{p} ({database}; log {logs / (name + '.log')}), pid {procs[-1].pid}")
    for p in (port, empty_port):
        say(f"  :{p} {'ready' if wait_ready(f'http://127.0.0.1:{p}/api/sites') else 'NOT ready (see log)'}")
    say("Frontends, each from frontend/ in its own terminal:")
    say(f'  $env:ASSETOPS_API_PORT="{port}"; npm.cmd run dev -- --port {web} --strictPort')
    say(f'  $env:ASSETOPS_API_PORT="{empty_port}"; npm.cmd run dev -- --port {empty_web} --strictPort')
    say("Then open the addresses printed by `links`. Ctrl+C stops the gateway and both APIs.")
    try:
        while all(p.poll() is None for p in procs):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
                p.wait(timeout=20)
    sys.exit(max(p.returncode or 0 for p in procs))


def drop(allow_default: bool) -> None:
    import psycopg

    if not allow_default and (DB == DEFAULT_DB or EMPTY_DB == DEFAULT_EMPTY_DB):
        raise SystemExit("Refusing to drop the owner's walkthrough databases without --allow-default")
    with psycopg.connect(f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops", autocommit=True) as c:
        for name in (DB, EMPTY_DB):
            c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")
            say(f"dropped {name}")
    if WORK.exists() and WORK.name != DEFAULT_WORK_NAME:
        shutil.rmtree(WORK, ignore_errors=True)
        say(f"removed {WORK}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="tools/v01b_lab_evidence_walkthrough.py")
    parser.add_argument("--db", default=DB, help="populated copy of the producer database")
    parser.add_argument("--empty-db", default=EMPTY_DB, help="empty migrated database")
    parser.add_argument("--work-name", default=WORK.name, help="work-tree folder under %%LOCALAPPDATA%%/AssetOps")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    d = sub.add_parser("drop")
    d.add_argument("--allow-default", action="store_true")
    for name in ("links", "serve"):
        s = sub.add_parser(name)
        s.add_argument("--port", type=int, default=API_PORT)
        s.add_argument("--web-port", type=int, default=WEB_PORT)
        s.add_argument("--empty-port", type=int, default=EMPTY_API_PORT)
        s.add_argument("--empty-web-port", type=int, default=EMPTY_WEB_PORT)
    args = parser.parse_args()
    configure(args.db, args.empty_db, args.work_name)
    if args.command == "prepare":
        prepare()
    elif args.command == "drop":
        drop(args.allow_default)
    elif args.command == "links":
        links(args.web_port, args.empty_web_port)
    else:
        serve(args.port, args.web_port, args.empty_port, args.empty_web_port)


if __name__ == "__main__":
    main()
