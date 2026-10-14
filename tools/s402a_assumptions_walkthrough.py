"""S4-02a owner walkthrough: Site diesel price (Financials > Assumptions) and the Finding bridge.

Builds on the S4-01/S4-03 Finding walkthrough (`tools/s4_finding_walkthrough.py`), which copies the reviewed
Finding-case database and stages a private code tree from git HEAD. This tool then:
- upgrades the copied database to the current migration head and publishes the demonstration diesel prices
  with the server-side SYSTEM publisher (fixture steps v1 INITIAL, v2 SUCCESSION, v3 CORRECTION);
- makes a second, empty-price database (the same Findings, no price published) for the missing state.

    python tools/s402a_assumptions_walkthrough.py --db assetops_s402awalk --empty-db assetops_s402aempty \
        --work-name s402a-owner prepare
    python tools/s402a_assumptions_walkthrough.py ... links [--web-port 5370]
    python tools/s402a_assumptions_walkthrough.py ... serve --port 8870 --empty-port 8871   # until Ctrl+C
    python tools/s402a_assumptions_walkthrough.py ... drop                                  # cleanup

Only databases whose names start with `assetops_s402a` are accepted, so the developer database and other
slices' walkthrough or test databases cannot be named. The work folder is
`%LOCALAPPDATA%/AssetOps/<work-name>`; nothing is written to this repository's `var/`.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = REPO / ".venv" / "Scripts" / "python.exe"
if not PY.exists():
    PY = REPO / ".venv" / "bin" / "python"
FINDING_TOOL = REPO / "tools" / "s4_finding_walkthrough.py"
PG = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432"
SOURCE_DB = "assetops_s4cases"
FIXTURE = Path("conversions") / "demo-diesel-price-publications.json"


def say(text: str = "") -> None:
    print(text, flush=True)


def checked_db(name: str) -> str:
    if not name.startswith("assetops_s402a") or not name.replace("_", "").isalnum() or name.endswith("_test"):
        raise SystemExit(f"Refused database {name!r}: this tool only uses private assetops_s402a* databases.")
    return name


def work_dir(name: str) -> Path:
    if not name or "/" in name or "\\" in name or name in {"s4-finding-walkthrough"}:
        raise SystemExit(f"Refused --work-name {name!r}.")
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share") / "AssetOps"
    return base / name


def tree_env(work: Path, db: str) -> dict[str, str]:
    tree = work / "tree"
    out = dict(os.environ)
    out["PYTHONPATH"] = os.pathsep.join(str(tree / p) for p in ("backend", "gateway", "simulator", "contracts", "host"))
    out["DATABASE_URL"] = f"{PG}/{db}"
    out["ASSETOPS_DEMO_FIXTURE_MANIFEST"] = str(work / "s4-finding-cases-manifest.json")
    out["PYTHONUNBUFFERED"] = "1"
    out.pop("ASSETOPS_TEST_DATABASE_URL", None)
    return out


def tree_py(work: Path, db: str, *argv: str, cwd: str = "backend") -> str:
    done = subprocess.run([str(PY), *argv], cwd=str(work / "tree" / cwd), env=tree_env(work, db),
                          capture_output=True, text=True, timeout=900)
    if done.returncode != 0:
        raise SystemExit(f"FAILED: python {' '.join(argv[:3])}\n{done.stdout}\n{done.stderr}")
    return done.stdout


def psql(sql: str) -> None:
    import psycopg

    with psycopg.connect(f"{PG.replace('+psycopg', '')}/assetops", autocommit=True) as c:
        c.execute(sql)


def prepare(db: str, empty: str, work: Path) -> None:
    say(f"=== 1. Finding walkthrough copy {db} and private code tree {work / 'tree'} ===")
    subprocess.run([str(PY), str(FINDING_TOOL), "--db", db, "--work", str(work), "prepare"], check=True)
    say(f"=== 2. Upgrade {db} to the current migration head and publish the demonstration prices ===")
    tree_py(work, db, "-m", "alembic", "upgrade", "head")
    out = tree_py(work, db, "-m", "assetops_backend.publish_assumption", "fixture", "--site", "KOBO-001",
                  "--file", str(FIXTURE), "--step", "v1", "--step", "v2", "--step", "v3")  # S4-02a steps only (v4 is S4-02b)
    for line in out.splitlines():
        step = json.loads(line)
        say(f"  {step['step']}: {step['change_kind']} version {step['revision_no']} {step['revision_id']}"
            f"{' (already published)' if step['replayed'] else ''}")
    say(f"=== 3. Empty-price database {empty}: the same Findings, no price published ===")
    psql(f"DROP DATABASE IF EXISTS {empty} WITH (FORCE)")
    psql(f"CREATE DATABASE {empty} TEMPLATE {SOURCE_DB}")
    tree_py(work, empty, "-m", "alembic", "upgrade", "head")
    say("Prepared. Next: links, then serve.")


def links(db: str, work: Path, web: int, empty_web: int) -> None:
    run = json.loads((work / "s4-finding-cases-run.json").read_text(encoding="utf-8")) if (work / "s4-finding-cases-run.json").exists() \
        else None
    base = f"http://localhost:{web}/sites/KOBO-001"
    say(f"- Financials overview: {base}/financials")
    say(f"- Assumptions (current price, schedule, history, disabled edit): {base}/financials/assumptions")
    out = tree_py(work, db, "-c", (
        "import json,sys\n"
        "from assetops_backend.financials.composition import build_assumption_store\n"
        "from assetops_backend.config import database_url\n"
        "s=build_assumption_store(database_url()); t=s.site_scope('demo','KOBO-001')\n"
        "print(json.dumps([{k:str(r[k]) for k in ('id','revision_no','recorded_at','change_kind')} "
        "for r in s.revisions(t[1],t[2],'diesel_price_per_litre')]))"))
    for r in json.loads(out):
        say(f"- Version {r['revision_no']} ({r['change_kind']}): {base}/financials/assumptions?revision_id={r['id']}")
        say(f"    Prices as recorded then: {base}/financials/assumptions?recorded_at="
            f"{r['recorded_at'].replace('+', '%2B').replace(' ', 'T')}")
    findings = (run or {}).get("findings") or []
    for f in findings[:3]:
        say(f"- Finding {f['finding_id']} (from {f['anchor_start'][:16]}): {base}/findings/{f['finding_id']}")
        say(f"    Its money view: {base}/financials?finding_id={f['finding_id']}")
    say(f"- Empty-price store: http://localhost:{empty_web}/sites/KOBO-001/financials/assumptions")


def serve(db: str, empty: str, work: Path, port: int, empty_port: int) -> None:
    logs = work / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    procs = []
    for name, p in ((db, port), (empty, empty_port)):
        log = (logs / f"api-{p}.log").open("a", encoding="utf-8")
        procs.append(subprocess.Popen(
            [str(PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(p)],
            cwd=str(work / "tree" / "host"), env=tree_env(work, name), stdout=log, stderr=subprocess.STDOUT))
        say(f"API for {name} on http://127.0.0.1:{p} (log {logs / f'api-{p}.log'})")
    say("Ctrl+C stops both APIs.")
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


def drop(db: str, empty: str, work: Path) -> None:
    for name in (db, empty):
        psql(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")
        say(f"dropped {name}")
    if work.exists():
        shutil.rmtree(work)
        say(f"removed {work}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="s402a_assumptions_walkthrough")
    parser.add_argument("--db", required=True)
    parser.add_argument("--empty-db", required=True)
    parser.add_argument("--work-name", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    lk = sub.add_parser("links")
    lk.add_argument("--web-port", type=int, default=5370)
    lk.add_argument("--empty-web-port", type=int, default=5371)
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=8870)
    s.add_argument("--empty-port", type=int, default=8871)
    sub.add_parser("drop")
    args = parser.parse_args()
    db, empty, work = checked_db(args.db), checked_db(args.empty_db), work_dir(args.work_name)
    if db == empty:
        raise SystemExit("--db and --empty-db must differ.")
    if args.command == "prepare":
        prepare(db, empty, work)
    elif args.command == "links":
        links(db, work, args.web_port, args.empty_web_port)
    elif args.command == "serve":
        serve(db, empty, work, args.port, args.empty_port)
    else:
        drop(db, empty, work)


if __name__ == "__main__":
    sys.exit(main())
