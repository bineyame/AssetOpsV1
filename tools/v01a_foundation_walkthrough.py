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
PRODUCER = WORK.parent / "s4-finding-cases"
PRODUCER_MANIFEST = PRODUCER / "s4-finding-cases-manifest.json"
MANIFEST = WORK / "s4-finding-cases-manifest.json"
PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
API_PORT, WEB_PORT, EMPTY_API_PORT, EMPTY_WEB_PORT = 8860, 5360, 8861, 5361

# Selected Foundation periods in the copied database (valid_from of each stored period).
PERIODS = (
    ("Imported period (29 Sep 2026)", "2026-09-30T00:00:00Z"),
    ("Demo configuration period (1 Oct 2026)", "2026-10-01T12:00:00Z"),
    ("Capability channels added (2 Oct 2026)", "2026-10-02T12:00:00Z"),
    ("Current period (21 Oct 2026 onward)", "2026-10-22T00:00:00Z"),
    ("Before any stored version (missing state)", "2026-09-01T00:00:00Z"),
)


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
    for label, at in PERIODS:
        say(f"- {label}:")
        for view, path in (("Site model", "foundation"), ("Single line diagram", "foundation/sld"),
                           ("Readiness", "foundation/readiness")):
            say(f"    {view}: {site}/{path}?at={at}")


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
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    for name in ("links", "serve"):
        s = sub.add_parser(name)
        s.add_argument("--port", type=int, default=API_PORT)
        s.add_argument("--web-port", type=int, default=WEB_PORT)
        s.add_argument("--empty-port", type=int, default=EMPTY_API_PORT)
        s.add_argument("--empty-web-port", type=int, default=EMPTY_WEB_PORT)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "links":
        links(args.web_port, args.empty_web_port)
    else:
        serve(args.port, args.web_port, args.empty_port, args.empty_web_port)


if __name__ == "__main__":
    main()
