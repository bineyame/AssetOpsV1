"""S4-02b owner walkthrough: the bounded fuel cost of a Finding on Site > Financials, and its versions.

Builds on the S4-02b producer template `assetops_s402bcases` (`tools/s402b_power_cases.py run`: the S4 Finding
cases, the ordinary F01-gateway case and the authored P01-power demonstration case). This tool:
- stages a private code tree from git HEAD in `%LOCALAPPDATA%/AssetOps/<work-name>/tree` with its own `var/`;
- copies the template into the walkthrough database, upgrades it to the migration head and runs the normal
  file-backed Performance comparison, which opens the source gate when it passes (so money can read current);
- publishes the SYSTEM diesel price fixture steps v1-v3 and runs the fuel cost recompute: P01-power is priced,
  F01-gateway stays "not calculated" (its power readings cover too little of the time);
- makes a second database with the same Findings and no price, compared and NOT recomputed (the "not worked out
  yet" state; `recompute --empty` then gives "no price for the whole window").

    python tools/s402b_fuel_cost_walkthrough.py --db assetops_s402bwalk --empty-db assetops_s402bempty \
        --work-name s402b-owner prepare
    python tools/s402b_fuel_cost_walkthrough.py ... links [--web-port 5372 --empty-web-port 5373]
    python tools/s402b_fuel_cost_walkthrough.py ... serve [--port 8872 --empty-port 8873]   # until Ctrl+C
    python tools/s402b_fuel_cost_walkthrough.py ... publish-v4      # the backdated October price correction
    python tools/s402b_fuel_cost_walkthrough.py ... recompute [--empty]
    python tools/s402b_fuel_cost_walkthrough.py ... close-gate | open-gate
    python tools/s402b_fuel_cost_walkthrough.py ... drop

Only databases whose names start with `assetops_s402b` and do not end in `_test` are accepted, and never the
producer template itself, so the developer database and other slices' databases cannot be named.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = REPO / ".venv" / "Scripts" / "python.exe"
if not PY.exists():
    PY = REPO / ".venv" / "bin" / "python"
PG = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432"
TEMPLATE_DB = "assetops_s402bcases"
APPDATA = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share") / "AssetOps"
PRODUCER_WORK = APPDATA / "s402b-power-cases"
FIXTURE = Path("conversions") / "demo-diesel-price-publications.json"
GATE_DIR = Path("var") / "evidence" / "migration-performance"
MARKER = ".s402b-walkthrough-work"
SITE = "KOBO-001"


def say(text: str = "") -> None:
    print(text, flush=True)


def checked_db(name: str) -> str:
    if (not name.startswith("assetops_s402b") or not name.replace("_", "").isalnum() or name.endswith("_test")
            or name == TEMPLATE_DB):
        raise SystemExit(f"Refused database {name!r}: this tool only uses private assetops_s402b* walkthrough "
                         f"databases (not *_test, not the template {TEMPLATE_DB}).")
    return name


def work_dir(name: str) -> Path:
    if not name or "/" in name or "\\" in name or name in {"s402b-power-cases", "s4-finding-walkthrough"}:
        raise SystemExit(f"Refused --work-name {name!r}.")
    return APPDATA / name


def manifest() -> Path | None:
    for candidate in sorted(PRODUCER_WORK.glob("*manifest*.json")):
        return candidate
    return None


def tree_env(work: Path, db: str) -> dict[str, str]:
    tree = work / "tree"
    out = dict(os.environ)
    out["PYTHONPATH"] = os.pathsep.join(str(tree / p) for p in ("backend", "gateway", "simulator", "contracts", "host"))
    out["DATABASE_URL"] = f"{PG}/{db}"
    m = manifest()
    if m is not None:
        out["ASSETOPS_DEMO_FIXTURE_MANIFEST"] = str(m)
    out["PYTHONUNBUFFERED"] = "1"
    out.pop("ASSETOPS_TEST_DATABASE_URL", None)
    return out


def tree_py(work: Path, db: str, *argv: str, cwd: str = "backend", check: bool = True) -> subprocess.CompletedProcess:
    done = subprocess.run([str(PY), *argv], cwd=str(work / "tree" / cwd), env=tree_env(work, db),
                          capture_output=True, text=True, timeout=900)
    if check and done.returncode != 0:
        raise SystemExit(f"FAILED: python {' '.join(argv[:3])}\n{done.stdout}\n{done.stderr}")
    return done


def admin(sql: str) -> None:
    import psycopg

    with psycopg.connect(f"{PG.replace('+psycopg', '')}/assetops", autocommit=True) as c:
        c.execute(sql)


def query(db: str, sql: str, params: dict | None = None) -> list[dict]:
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(f"{PG.replace('+psycopg', '')}/{db}", row_factory=dict_row) as c:
        return list(c.execute(sql, params or {}).fetchall())


def stage_tree(work: Path) -> None:
    if work.exists() and any(work.iterdir()) and not (work / MARKER).is_file():
        raise SystemExit(f"Refusing {work}: it exists, is not empty and has no {MARKER} marker.")
    tree = work / "tree"
    if tree.exists():
        shutil.rmtree(tree)
    tree.mkdir(parents=True)
    (work / MARKER).write_text("created by tools/s402b_fuel_cost_walkthrough.py prepare\n", encoding="utf-8")
    archive = subprocess.run(["git", "archive", "--format=tar", "HEAD", "backend", "gateway", "host", "simulator",
                              "contracts", "config", "contract-fixtures"], cwd=REPO, capture_output=True,
                             check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(tree, filter="data")
    (tree / "var" / "sites").mkdir(parents=True)
    shutil.copy2(REPO / "var" / "sites" / "kobo-001.yaml", tree / "var" / "sites" / "kobo-001.yaml")
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout
    say(f"  {tree} (code from {head.strip()})")
    probe = tree_py(work, "assetops", "-c", "import assetops_backend;print(assetops_backend.__file__)").stdout
    if str(tree).lower() not in probe.lower():
        raise SystemExit(f"Isolation failed: assetops_backend resolves to {probe}")


def copy_db(work: Path, name: str) -> None:
    admin(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")
    admin(f"CREATE DATABASE {name} TEMPLATE {TEMPLATE_DB}")
    tree_py(work, name, "-m", "alembic", "upgrade", "head")
    done = tree_py(work, name, "-m", "assetops_backend.performance_migration", "run", "--tenant", "demo", "--site",
                   SITE, check=False)
    verdict = "passed: the source gate is open" if done.returncode == 0 else \
        f"did not pass (exit {done.returncode}): Findings read as audit records only"
    say(f"  {name}: copied from {TEMPLATE_DB}, upgraded, Performance comparison {verdict}")


def publish(work: Path, db: str, *steps: str) -> None:
    argv = ["-m", "assetops_backend.publish_assumption", "fixture", "--site", SITE, "--file", str(FIXTURE)]
    for s in steps:
        argv += ["--step", s]
    for line in tree_py(work, db, *argv).stdout.splitlines():
        step = json.loads(line)
        say(f"  {step['step']}: {step['change_kind']} version {step['revision_no']} {step['revision_id']}"
            f"{' (already published)' if step['replayed'] else ''}")


def recompute(work: Path, db: str) -> None:
    out = tree_py(work, db, "-m", "assetops_backend.recompute_consequences", "run", "--site", SITE).stdout
    say("  " + out.strip().replace("\n", "\n  "))


def prepare(db: str, empty: str, work: Path) -> None:
    exists = query("assetops", "SELECT 1 FROM pg_database WHERE datname = %(d)s", {"d": TEMPLATE_DB})
    if not exists:
        raise SystemExit(f"Missing template {TEMPLATE_DB}: run `.venv/Scripts/python.exe tools/s402b_power_cases.py "
                         "run` first (about 2.5 minutes).")
    say(f"=== 1. Private code tree in {work} ===")
    stage_tree(work)
    say(f"=== 2. Walkthrough database {db} ===")
    copy_db(work, db)
    say("=== 3. SYSTEM diesel prices v1-v3 and the fuel cost recompute ===")
    publish(work, db, "v1", "v2", "v3")
    recompute(work, db)
    say(f"=== 4. Empty-price database {empty}: the same Findings, no price, not recomputed ===")
    copy_db(work, empty)
    say("Prepared. Next: links, then serve.")


def links(db: str, empty: str, web: int, empty_web: int) -> None:
    base = f"http://localhost:{web}/sites/{SITE}"
    say(f"- Assumptions (prices, schedule, history): {base}/financials/assumptions")
    for r in query(db, "SELECT r.id, r.revision_no, r.change_kind FROM financial_assumption_revision r "
                       "ORDER BY r.revision_no"):
        say(f"    price version {r['revision_no']} ({r['change_kind']}): {base}/financials/assumptions?revision_id={r['id']}")
    latest = ("SELECT r.finding_id, r.id, r.revision_no, r.episode_start, r.episode_end FROM finding_revision r "
              "WHERE r.revision_no = (SELECT max(x.revision_no) FROM finding_revision x WHERE x.finding_id = r.finding_id) "
              "ORDER BY r.episode_start")
    rows = query(db, latest)
    picks = {
        "P01-power (demonstration data, priced)": [r for r in rows if r["episode_start"].date().isoformat() == "2026-10-23"],
        "F01-gateway (ordinary gateway readings, not calculated)": [
            r for r in rows if r["episode_start"].strftime("%Y-%m-%d %H:%M") == "2026-10-02 05:15"],
    }
    for label, found in picks.items():
        for r in found[:1]:
            say(f"- {label}: {base}/financials?finding_id={r['finding_id']}&revision_id={r['id']}")
            say(f"    the finding: {base}/findings/{r['finding_id']}?revision_id={r['id']}")
            say(f"    its evidence: {base}/findings/{r['finding_id']}/evidence?revision_id={r['id']}")
            for c in query(db, "SELECT id, revision_no, state FROM financial_consequence_revision "
                               "WHERE finding_revision_id = %(r)s ORDER BY revision_no", {"r": r["id"]}):
                say(f"    fuel cost version {c['revision_no']} ({c['state']}): {base}/financials?finding_id="
                    f"{r['finding_id']}&revision_id={r['id']}&consequence_revision_id={c['id']}")
        if not found:
            say(f"- {label}: not found in {db}")
    old = query(db, "SELECT r.finding_id, r.id, r.revision_no FROM finding_revision r WHERE r.revision_no < "
                    "(SELECT max(x.revision_no) FROM finding_revision x WHERE x.finding_id = r.finding_id) "
                    "ORDER BY r.episode_start LIMIT 1")
    for r in old:
        say(f"- An earlier finding version (kept for the record): {base}/financials?finding_id={r['finding_id']}"
            f"&revision_id={r['id']}")
    ebase = f"http://localhost:{empty_web}/sites/{SITE}"
    for r in [x for x in query(empty, latest) if x["episode_start"].date().isoformat() == "2026-10-23"][:1]:
        say(f"- Empty-price store, P01-power: {ebase}/financials?finding_id={r['finding_id']}&revision_id={r['id']}")
    say(f"- Empty-price store, Assumptions: {ebase}/financials/assumptions")


def serve(db: str, empty: str, work: Path, port: int, empty_port: int, web: int, empty_web: int) -> None:
    logs = work / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    procs = []
    for name, p in ((db, port), (empty, empty_port)):
        log = (logs / f"api-{p}.log").open("a", encoding="utf-8")
        procs.append(subprocess.Popen(
            [str(PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(p)],
            cwd=str(work / "tree" / "host"), env=tree_env(work, name), stdout=log, stderr=subprocess.STDOUT))
        say(f"API for {name} on http://127.0.0.1:{p} (log {logs / f'api-{p}.log'})")
    say(f'Frontends, from frontend/:  $env:ASSETOPS_API_PORT="{port}"; npm.cmd run dev -- --port {web} --strictPort')
    say(f'                       and  $env:ASSETOPS_API_PORT="{empty_port}"; npm.cmd run dev -- --port {empty_web} --strictPort')
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


def gate(work: Path, close: bool) -> None:
    """Close (move the comparison reports aside) or reopen the private tree's source gate, for both databases."""
    live = work / "tree" / GATE_DIR
    aside = live.with_name(live.name + ".closed")
    src, dst = (live, aside) if close else (aside, live)
    if not src.exists():
        raise SystemExit(f"Nothing to move: {src} does not exist")
    if dst.exists():
        raise SystemExit(f"Refused: {dst} already exists")
    src.rename(dst)
    say(f"{'Closed' if close else 'Reopened'}: moved {src} -> {dst}. Restart `serve` if it caches the gate.")


def drop(db: str, empty: str, work: Path) -> None:
    for name in (db, empty):
        admin(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")
        say(f"dropped {name}")
    if work.exists() and (work / MARKER).is_file():
        shutil.rmtree(work)
        say(f"removed {work}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="s402b_fuel_cost_walkthrough")
    parser.add_argument("--db", required=True)
    parser.add_argument("--empty-db", required=True)
    parser.add_argument("--work-name", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    lk = sub.add_parser("links")
    lk.add_argument("--web-port", type=int, default=5372)
    lk.add_argument("--empty-web-port", type=int, default=5373)
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=8872)
    s.add_argument("--empty-port", type=int, default=8873)
    s.add_argument("--web-port", type=int, default=5372)
    s.add_argument("--empty-web-port", type=int, default=5373)
    sub.add_parser("publish-v4")
    rc = sub.add_parser("recompute")
    rc.add_argument("--empty", action="store_true", help="recompute the empty-price database instead")
    sub.add_parser("close-gate")
    sub.add_parser("open-gate")
    sub.add_parser("drop")
    args = parser.parse_args()
    db, empty, work = checked_db(args.db), checked_db(args.empty_db), work_dir(args.work_name)
    if db == empty:
        raise SystemExit("--db and --empty-db must differ.")
    if args.command == "prepare":
        prepare(db, empty, work)
    elif args.command == "links":
        links(db, empty, args.web_port, args.empty_web_port)
    elif args.command == "serve":
        serve(db, empty, work, args.port, args.empty_port, args.web_port, args.empty_web_port)
    elif args.command == "publish-v4":
        publish(work, db, "v4")
    elif args.command == "recompute":
        recompute(work, empty if args.empty else db)
    elif args.command in ("close-gate", "open-gate"):
        gate(work, args.command == "close-gate")
    else:
        drop(db, empty, work)


if __name__ == "__main__":
    sys.exit(main())
