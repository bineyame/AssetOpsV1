"""V-01a owner walkthrough: Sites, Foundation, Readiness and SLD over private database copies.

    .venv/Scripts/python.exe tools/s4_finding_cases.py run               # first: the reviewed fixture producer
    .venv/Scripts/python.exe tools/v01a_foundation_walkthrough.py prepare # copy DB, create an empty DB
    .venv/Scripts/python.exe tools/v01a_foundation_walkthrough.py links   # print the walkthrough addresses
    .venv/Scripts/python.exe tools/v01a_foundation_walkthrough.py serve   # both APIs until Ctrl+C

Isolation (like the S3/S4 walkthroughs):
- Database `assetops_v01awalk` is dropped and recreated as a copy of `assetops_s4cases` (the KOBO-001
  Site with its stored Foundation periods and binding sets). The producer database is only read.
- Database `assetops_v01aempty` is dropped and recreated empty and migrated: no Site at all, for the
  honest "No sites configured" state.
- Code is `git archive HEAD` into `%LOCALAPPDATA%/AssetOps/v01a-foundation-walkthrough/tree` with its own
  `var/`; nothing is written to this repository's `var/`. The empty API uses a second tree `var/` with no
  Site file.
- Ports: populated API 8860 / web 5360, empty API 8861 / web 5361. No other port is used.

A second copy (for example an implementer's or reviewer's private run) must not reuse the owner's
databases, tree or ports. Global options, given before the command, override the defaults:

    tools/v01a_foundation_walkthrough.py --db assetops_v01ar3walk --empty-db assetops_v01ar3empty         --work-name v01a-round3-impl prepare
    tools/v01a_foundation_walkthrough.py --db ... --empty-db ... --work-name ... serve         --port 8880 --web-port 5380 --empty-port 8881 --empty-web-port 5381
    tools/v01a_foundation_walkthrough.py --db ... --empty-db ... drop   # drop that copy's databases

`drop` refuses the owner's default database names unless `--allow-default` is given.

Nothing is staged: every screen reads persisted rows as the producer left them.
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
WORK = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AssetOps" / "v01a-foundation-walkthrough"
SOURCE_DB, DB, EMPTY_DB = "assetops_s4cases", "assetops_v01awalk", "assetops_v01aempty"
DEFAULT_DB, DEFAULT_EMPTY_DB, DEFAULT_WORK_NAME = DB, EMPTY_DB, WORK.name
PRODUCER = WORK.parent / "s4-finding-cases"
PRODUCER_MANIFEST = PRODUCER / "s4-finding-cases-manifest.json"
MANIFEST = WORK / "s4-finding-cases-manifest.json"
PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
API_PORT, WEB_PORT, EMPTY_API_PORT, EMPTY_WEB_PORT = 8860, 5360, 8861, 5361

# Instants chosen INSIDE each stored period (none is a period's valid_from). Today the period in
# effect is v10; the "21 Oct 2026 onward" period (v13) is SCHEDULED until that date, so its instant
# shows a "Scheduled period ... not the configuration in effect now" strip. After 21 Oct 2026 it
# becomes the current period and these labels need revisiting. The first link (no ?at=) is the
# configuration actually in effect now.
PERIODS = (
    ("Imported period (29 Sep 2026)", "2026-09-30T00:00:00Z"),
    ("Demo configuration period (1 Oct 2026)", "2026-10-01T12:00:00Z"),
    ("Capability channels added (2 Oct 2026)", "2026-10-02T12:00:00Z"),
    ("Scheduled period v13 (starts 21 Oct 2026; not in effect yet)", "2026-10-22T00:00:00Z"),
    ("Before any stored version (missing state)", "2026-09-01T00:00:00Z"),
)


def configure(db: str, empty_db: str, work_name: str) -> None:
    """Point this run at its own databases and work tree; defaults are the owner's walkthrough."""
    global WORK, DB, EMPTY_DB, MANIFEST
    for name in (db, empty_db):
        if not name.isidentifier() or not name.startswith("assetops_") or name == SOURCE_DB:
            raise SystemExit(f"Refusing database name {name!r}: use assetops_<name>, not the producer database")
    if not work_name or any(ch in work_name for ch in "/\\:") or work_name in (".", ".."):
        raise SystemExit(f"Refusing work-tree name {work_name!r}")
    WORK = WORK.parent / work_name
    DB, EMPTY_DB = db, empty_db
    MANIFEST = WORK / "s4-finding-cases-manifest.json"


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


def say(text: str = "") -> None:
    print(text, flush=True)


def db_url(name: str) -> str:
    return f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{name}"


def env(database: str, tree: Path) -> dict[str, str]:
    out = dict(os.environ)
    out["PYTHONPATH"] = os.pathsep.join(str(tree / p) for p in ("backend", "gateway", "simulator", "contracts", "host"))
    out["DATABASE_URL"] = db_url(database)
    out["ASSETOPS_DEMO_FIXTURE_MANIFEST"] = str(MANIFEST)
    out["PYTHONUNBUFFERED"] = "1"
    out.pop("ASSETOPS_TEST_DATABASE_URL", None)
    return out


def extract_tree(tree: Path, with_kobo: bool) -> None:
    if tree.exists():
        shutil.rmtree(tree)
    tree.mkdir(parents=True)
    archive = subprocess.run(["git", "archive", "--format=tar", "HEAD", "backend", "gateway", "host", "simulator",
                              "contracts", "config", "contract-fixtures"], cwd=REPO, capture_output=True,
                             check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(tree, filter="data")
    (tree / "var" / "sites").mkdir(parents=True)
    if with_kobo:
        shutil.copy2(REPO / "var" / "sites" / "kobo-001.yaml", tree / "var" / "sites" / "kobo-001.yaml")


def prepare() -> None:
    import psycopg

    for needed, hint in (
        (PRODUCER_MANIFEST, "run the Finding-case producer first (tools/s4_finding_cases.py run)"),
        (REPO / "var" / "sites" / "kobo-001.yaml", "the Kobo site configuration is missing"),
    ):
        if not needed.exists():
            raise SystemExit(f"Missing prerequisite {needed}: {hint}")
    say("=== 1. Private work trees (git HEAD) with their own var/ ===")
    extract_tree(WORK / "tree", with_kobo=True)
    extract_tree(WORK / "tree-empty", with_kobo=False)
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout
    say(f"  {WORK / 'tree'} and {WORK / 'tree-empty'} (code from {head.strip()})")
    probe = subprocess.run([str(PY), "-c", "import assetops_backend;print(assetops_backend.__file__)"],
                           cwd=str(WORK / "tree"), env=env(DB, WORK / "tree"), capture_output=True,
                           text=True).stdout.strip()
    if str(WORK / "tree").lower() not in probe.lower():
        raise SystemExit(f"Isolation failed: assetops_backend resolves to {probe}")
    shutil.copy2(PRODUCER_MANIFEST, MANIFEST)

    say(f"=== 2. Database {DB} as a copy of {SOURCE_DB}; {EMPTY_DB} empty ===")
    with psycopg.connect(f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {DB} WITH (FORCE)")
        c.execute(f"CREATE DATABASE {DB} TEMPLATE {SOURCE_DB}")
        c.execute(f"DROP DATABASE IF EXISTS {EMPTY_DB} WITH (FORCE)")
        c.execute(f"CREATE DATABASE {EMPTY_DB}")
    done = subprocess.run([str(PY), "-m", "alembic", "upgrade", "head"], cwd=str(WORK / "tree-empty" / "backend"),
                          env=env(EMPTY_DB, WORK / "tree-empty"), capture_output=True, text=True, timeout=600)
    if done.returncode != 0:
        raise SystemExit(f"FAILED: alembic upgrade on {EMPTY_DB}\n{done.stdout}\n{done.stderr}")
    say("  copied; empty database migrated")
    say("Prepared. Next: links, then serve.")


def links(web: int, empty_web: int) -> None:
    site = f"http://localhost:{web}/sites/KOBO-001"
    say(f"- Sites (populated): http://localhost:{web}/sites")
    say(f"- Sites (no Site stored): http://localhost:{empty_web}/sites")
    say("- In effect now (no ?at=; this is the route a user lands on):")
    for view, path in (("Site model", "foundation"), ("Single line diagram", "foundation/sld"),
                       ("Readiness", "foundation/readiness")):
        say(f"    {view}: {site}/{path}")
    for label, at in PERIODS:
        say(f"- {label}:")
        for view, path in (("Site model", "foundation"), ("Single line diagram", "foundation/sld"),
                           ("Readiness", "foundation/readiness")):
            say(f"    {view}: {site}/{path}?at={at}")
    # V-01a round 2: a chosen part travels in the address beside `at`. Every stored KOBO-001 period
    # declares the same ten components, so no stored period change removes a part; the missing state
    # is shown with an address naming a part this period does not declare (as a link copied from
    # another Site would).
    scheduled = PERIODS[3][1]
    say("- A chosen part (battery) in the scheduled period, kept across views and reload:")
    for view, path in (("Single line diagram", "foundation/sld"), ("Readiness", "foundation/readiness"),
                       ("Site model", "foundation")):
        say(f"    {view}: {site}/{path}?at={scheduled}&component=battery")
    say(f"- A part this period does not declare (cleared, with a notice): {site}/foundation/sld?at={scheduled}"
        "&component=no-such-part")


def serve(port: int, web: int, empty_port: int, empty_web: int) -> None:
    logs = WORK / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    procs = []
    for name, database, tree, p in (("api", DB, WORK / "tree", port),
                                    ("api-empty", EMPTY_DB, WORK / "tree-empty", empty_port)):
        log = (logs / f"{name}.log").open("a", encoding="utf-8")
        procs.append(subprocess.Popen([str(PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port",
                                       str(p)], cwd=str(tree / "host"), env=env(database, tree), stdout=log,
                                      stderr=subprocess.STDOUT))
        say(f"{name} on http://127.0.0.1:{p} ({database}; log {logs / (name + '.log')}), pid {procs[-1].pid}")
    say("Frontends, each from frontend/ in its own terminal:")
    say(f'  $env:ASSETOPS_API_PORT="{port}"; npm.cmd run dev -- --port {web} --strictPort')
    say(f'  $env:ASSETOPS_API_PORT="{empty_port}"; npm.cmd run dev -- --port {empty_web} --strictPort')
    say("Then open the addresses printed by `links`. Ctrl+C stops both APIs.")
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


def main() -> None:
    parser = argparse.ArgumentParser(prog="tools/v01a_foundation_walkthrough.py")
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
