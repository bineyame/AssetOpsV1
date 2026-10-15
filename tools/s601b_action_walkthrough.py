"""S6-01b owner walkthrough: the Recommendation, Action and Foundation change screens over a private database.

    python tools/s601b_action_walkthrough.py --db assetops_s601b_owner --work var/s601b_owner prepare
    python tools/s601b_action_walkthrough.py --db assetops_s601b_owner --work var/s601b_owner links
    python tools/s601b_action_walkthrough.py --db assetops_s601b_owner --work var/s601b_owner serve   # until Ctrl+C
    python tools/s601b_action_walkthrough.py --db assetops_s601b_owner --work var/s601b_owner drop

What `prepare` does (nothing outside the named database and work folder is written):
1. `git archive HEAD` of backend/gateway/host/simulator/contracts/config into `<work>/tree`, with its own `var/`
   holding only the Kobo Site file the stored import record names (the S1 test fixture, matching digest).
2. `CREATE DATABASE <db>`, migrated to head. An existing database of that name is dropped first only when the
   work folder's marker records that this tool made it; otherwise `prepare` refuses (review L1).
3. Runs S6-01a's `D-action-records` builder (`backend/tests/s6_action_records.py::build`, the same code that
   produced `backend/tests/fixtures/s6_action_api_contract.json`) against that database: S4 cases F01/F02 and an
   ineligible day through ingestion, assessment and matching; accept, observe, failed and successful applies and
   the F01 reassessment through the real Action API. Nothing is hand-inserted.
4. Writes `<work>/action-demo-grants.json`, the v2 grants document for THIS database's tenant/Site and the three
   fixture Findings only (`fixture_grants`), and `<work>/walkthrough.json` with every ID the walkthrough names.
5. Runs the Performance comparison in the private tree so the Finding reads are released.

`serve` starts the real API (`host/lab_app.py`) on 127.0.0.1:8961 with DATABASE_URL = the private database and
ASSETOPS_ACTION_DEMO_GRANTS = the grants document above, then prints the frontend command (port 5461). `drop`
removes the database and the work folder, and only those this tool made: the work folder's marker records the
database name, and `drop` checks the marker before it drops anything.

Guards: `--db` must start with `assetops_s601b`, be a plain identifier and never end in `_test` (test databases
belong to pytest); `--work` must be a `var/s601b*` folder directly under this repository's `var/`.

Recorded times: the builder's clock is the fixture's (2026-10-29 .. 2026-11-01). The served API uses the real
clock, so "now" reads (for example the application basis on a pending Action) read at today's date.
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
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = Path(sys.executable)
PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
PG_ADMIN = f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops"
API_PORT, WEB_PORT = 8961, 5461
MARKER = ".s601b-walkthrough-work"
SITE = "KOBO-001"

BUILD = r'''
import json, sys
from pathlib import Path
url, out = sys.argv[1], Path(sys.argv[2])
import pg_harness
from alembic import command
command.upgrade(pg_harness._alembic(url), "head")
from sqlalchemy import create_engine
from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
from test_s4_finding_store_postgres import CaseRunner
from test_s6_action_store_postgres import CASES
from test_s6_action_records_postgres import make_harness
from s6_action_records import RECORDS, build, fixture_grants

engine = create_engine(url)
runner = CaseRunner(PostgresFoundationStore(url), engine)
contract, rows = build(runner, CASES, make_harness(runner))
findings = {f["anchor_start"].date().isoformat(): f["id"] for f in runner.reload()["findings"]}
(out / "action-demo-grants.json").write_text(json.dumps(fixture_grants(runner.tenant, runner.site, findings), indent=2))
m = contract["manifest"]
rec, ov, ex, hi = m["recommendation:1#a"], m["action-overview:1#a"], m["action-execution:1#a"], m["action-history:1#a"]
change = ex["apply_applied"]["body"]["change"]
events = ex["apply_applied"]["body"]["event"]
latest = hi["events_latest"]["body"]["events"]
ids = {
    "site": "KOBO-001",
    "finding_f01": str(findings["2026-10-06"]),
    "finding_f01_origin_revision": rec["pre_accept_available"]["body"]["revision_id"],
    "finding_f01_latest_revision": ov["applied_pending_newer_revision"]["body"]["origin"].get("latest_revision_id")
        or rec["latest_revision_after_apply"]["body"]["revision_id"],
    "finding_f02": str(findings["2026-10-08"]),
    "finding_ineligible": str(findings["2026-10-12"]),
    "action": rec["accept_created"]["body"]["action"]["action_id"],
    "action_code": rec["accept_created"]["body"]["action"]["action_code"],
    "action_f02": ex["apply_no_change_failed"]["body"]["detail"]["event"]["action_id"],
    "change": change["change_id"],
    "events": [{"id": e["id"], "kind": e["kind"], "recorded_at": e["recorded_at"], "occurred_at": e["occurred_at"],
                "failure_code": e.get("failure_code")} for e in latest],
    "foundation": {"expected": change["expected_foundation_revision_id"],
                   "split": change["split_foundation_revision_id"], "new": change["new_foundation_revision_id"]},
    "binding_set_revisions": change["binding_set_revisions"],
}
(out / "walkthrough.json").write_text(json.dumps(ids, indent=2, default=str))
(out / "contract-run.json").write_text(json.dumps(contract, indent=2, default=str))
engine.dispose()
print("built: action", ids["action"], "change", ids["change"], "events", len(latest))
'''


def say(text: str = "") -> None:
    print(text, flush=True)


class Walk:
    def __init__(self, db: str, work: str) -> None:
        if not re.fullmatch(r"assetops_s601b[a-z0-9_]{0,40}", db) or db.endswith("_test"):
            raise SystemExit(f"Refused: --db {db!r} must start with assetops_s601b, be a plain lower-case "
                             "identifier and must not end in _test")
        path = (REPO / work).resolve() if not Path(work).is_absolute() else Path(work).resolve()
        if path.parent != (REPO / "var").resolve() or not path.name.startswith("s601b"):
            raise SystemExit(f"Refused: --work {path} must be a var/s601b* folder directly under {REPO / 'var'}")
        self.db, self.work, self.tree = db, path, path / "tree"
        self.url = f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{db}"

    def env(self, *, tests: bool = False) -> dict[str, str]:
        out = dict(os.environ)
        parts = ["backend", "gateway", "simulator", "contracts", "host"] + (["backend/tests"] if tests else [])
        out["PYTHONPATH"] = os.pathsep.join(str(self.tree / p) for p in parts)
        out["DATABASE_URL"] = self.url
        out["PYTHONUNBUFFERED"] = "1"
        out.pop("ASSETOPS_TEST_DATABASE_URL", None)
        if tests:
            # The builder's test modules read their database from this name at import; it is the private one.
            out["ASSETOPS_TEST_DATABASE_URL"] = self.url
        out["ASSETOPS_ACTION_DEMO_GRANTS"] = str(self.work / "action-demo-grants.json")
        return out

    def py(self, *argv: str, tests: bool = False, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
        done = subprocess.run([str(PY), *argv], cwd=str(cwd or self.tree), env=self.env(tests=tests),
                              capture_output=True, text=True, timeout=1800)
        if check and done.returncode != 0:
            raise SystemExit(f"FAILED: python {' '.join(argv[:2])}\n{done.stdout[-4000:]}\n{done.stderr[-4000:]}")
        return done

    def owned(self) -> bool:
        return (self.work / MARKER).is_file()

    def marker_db(self) -> str | None:
        """The database this tool recorded in the work folder's marker, or None."""
        if not self.owned():
            return None
        for line in (self.work / MARKER).read_text(encoding="utf-8").splitlines():
            if line.startswith("db="):
                return line[3:].strip()
        return None

    def db_exists(self, c) -> bool:
        return c.execute("SELECT 1 FROM pg_database WHERE datname = %s", (self.db,)).fetchone() is not None

    def prepare(self) -> None:
        import psycopg

        if self.work.exists() and any(self.work.iterdir()) and not self.owned():
            raise SystemExit(f"Refused: {self.work} exists, is not empty and was not made by this tool")
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            if self.db_exists(c) and self.marker_db() != self.db:
                raise SystemExit(f"Refused: database {self.db} exists and {self.work / MARKER} does not record that "
                                 "this tool made it; drop it yourself or choose another --db")
        say("=== 1. Private tree (git HEAD) with its own var/ ===")
        if self.tree.exists():
            shutil.rmtree(self.tree)
        self.tree.mkdir(parents=True)
        (self.work / MARKER).write_text(f"created by tools/s601b_action_walkthrough.py\ndb={self.db}\n", encoding="utf-8")
        archive = subprocess.run(["git", "archive", "--format=tar", "HEAD", "backend", "gateway", "host", "simulator",
                                  "contracts", "config", "contract-fixtures"], cwd=REPO, capture_output=True,
                                 check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(self.tree, filter="data")
        (self.tree / "var" / "sites").mkdir(parents=True)
        # The import record names var/sites/kobo-001.yaml with the S1 fixture's digest; anything else is a conflict.
        shutil.copy2(self.tree / "backend" / "tests" / "fixtures" / "s1" / "kobo-001.yaml",
                     self.tree / "var" / "sites" / "kobo-001.yaml")
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True)
        say(f"  {self.tree} (code from {head.stdout.strip()})")
        probe = self.py("-c", "import assetops_backend;print(assetops_backend.__file__)").stdout.strip()
        if str(self.tree).lower() not in probe.lower():
            raise SystemExit(f"Isolation failed: assetops_backend resolves to {probe}")

        say(f"=== 2. Database {self.db} ===")
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE)")
            c.execute(f"CREATE DATABASE {self.db}")
        say("  created")

        say("=== 3. D-action-records through the real stores and Action API ===")
        say("  " + self.py("-c", BUILD, self.url, str(self.work), tests=True,
                           cwd=self.tree / "backend" / "tests").stdout.strip().splitlines()[-1])

        say("=== 4. Performance comparison (releases the Finding reads) ===")
        done = self.py("-m", "assetops_backend.performance_migration", "run", "--tenant", "demo", "--site", SITE,
                       check=False)
        say("  " + (done.stdout.strip().splitlines() or ["(no output)"])[-1])
        if done.returncode != 0:
            say(f"  The comparison did not pass (exit {done.returncode}); Finding reads will say 'not released'.")
            say("  " + done.stderr.strip()[-2000:].replace("\n", "\n  "))
        say("Prepared. Next: links, then serve.")

    def ids(self) -> dict:
        path = self.work / "walkthrough.json"
        if not path.is_file():
            raise SystemExit("Run prepare first.")
        return json.loads(path.read_text(encoding="utf-8"))

    def links(self, web: int) -> None:
        i, base = self.ids(), f"http://localhost:{web}/sites/{SITE}"
        say(f"Action {i['action_code']} ({i['action']}) on Finding F01 {i['finding_f01']}")
        rows = [
            ("Finding F01, origin version", f"{base}/findings/{i['finding_f01']}?revision_id={i['finding_f01_origin_revision']}"),
            ("recommendation:1#a accepted snapshot + live status",
             f"{base}/findings/{i['finding_f01']}/recommendation?revision_id={i['finding_f01_origin_revision']}"),
            ("recommendation:1#a latest Finding version (earlier trial still open notice)",
             f"{base}/findings/{i['finding_f01']}/recommendation"),
            ("recommendation:1#a unavailable (SOC at headroom)", f"{base}/findings/{i['finding_ineligible']}/recommendation"),
            ("action-overview:1#a", f"{base}/actions/{i['action']}"),
            ("action-execution:1#a", f"{base}/actions/{i['action']}/execution"),
            ("action-history:1#a", f"{base}/actions/{i['action']}/history"),
            ("changes:1#a", f"{base}/foundation/changes/{i['change']}"),
            ("bare changes (unavailable)", f"{base}/foundation/changes"),
            ("second Action (F02, failed no-change, still pending)", f"{base}/actions/{i['action_f02']}/execution"),
        ]
        for event in i["events"]:
            rows.append((f"history at {event['kind']} {event['failure_code'] or ''}".strip(),
                         f"{base}/actions/{i['action']}/history?event_id={event['id']}"))
        observed = next(e for e in i["events"] if e["kind"] == "OBSERVED")
        rows.append(("history recorded through the observation", f"{base}/actions/{i['action']}/history?recorded_at={observed['recorded_at']}"))
        rows.append(("selector conflict (both)", f"{base}/actions/{i['action']}/history?event_id={observed['id']}&recorded_at={observed['recorded_at']}"))
        for label, url in rows:
            say(f"  {label}\n    {url}")
        say(f"  Foundation versions: expected {i['foundation']['expected']}, split {i['foundation']['split']}, "
            f"new {i['foundation']['new']}")

    def serve(self, port: int, web: int) -> None:
        self.ids()
        logs = self.work / "logs"
        logs.mkdir(exist_ok=True)
        log = open(logs / f"api-{port}.log", "w", encoding="utf-8")
        proc = subprocess.Popen([str(PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(port)],
                                cwd=str(self.tree / "host"), env=self.env(), stdout=log, stderr=subprocess.STDOUT)
        say(f"API on http://127.0.0.1:{port} (log {logs / f'api-{port}.log'}), pid {proc.pid}")
        say(f"Grants: {self.work / 'action-demo-grants.json'} (this database's tenant/Site, fixture Findings only)")
        say(f'Frontend, from frontend/:  $env:ASSETOPS_API_PORT="{port}"; npm.cmd run dev -- --port {web} --strictPort')
        self.links(web)
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()

    def drop(self) -> None:
        import psycopg

        recorded = self.marker_db()
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            if self.db_exists(c):
                if recorded != self.db:
                    raise SystemExit(f"Not dropping {self.db}: {self.work / MARKER} does not record that this tool "
                                     f"made it (recorded: {recorded or 'nothing'})")
                c.execute(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE)")
                say(f"dropped database {self.db}")
            else:
                say(f"database {self.db} does not exist")
        if self.work.exists():
            if not self.owned():
                raise SystemExit(f"Not removing {self.work}: it has no {MARKER} marker")
            shutil.rmtree(self.work)
            say(f"removed {self.work}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="tools/s601b_action_walkthrough.py")
    parser.add_argument("--db", required=True, help="private database, assetops_s601b*")
    parser.add_argument("--work", required=True, help="work folder var/s601b* under this repository")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare")
    lk = sub.add_parser("links")
    lk.add_argument("--web-port", type=int, default=WEB_PORT)
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=API_PORT)
    s.add_argument("--web-port", type=int, default=WEB_PORT)
    sub.add_parser("drop")
    args = parser.parse_args()
    walk = Walk(args.db, args.work)
    if args.cmd == "prepare":
        walk.prepare()
    elif args.cmd == "links":
        walk.links(args.web_port)
    elif args.cmd == "serve":
        walk.serve(args.port, args.web_port)
    else:
        walk.drop()


if __name__ == "__main__":
    main()
