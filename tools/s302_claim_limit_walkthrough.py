"""S3-02b owner walkthrough: the selected assessment's claim limit on Evidence Analysis, over a private database.

    python tools/s302_claim_limit_walkthrough.py --db assetops_s302_owner1 --work var/s302_owner1 prepare
    python tools/s302_claim_limit_walkthrough.py --db assetops_s302_owner1 --work var/s302_owner1 serve   # until Ctrl+C
    python tools/s302_claim_limit_walkthrough.py --db assetops_s302_owner1 --work var/s302_owner1 late
    python tools/s302_claim_limit_walkthrough.py --db assetops_s302_owner1 --work var/s302_owner1 attest
    python tools/s302_claim_limit_walkthrough.py --db assetops_s302_owner1 --work var/s302_owner1 drop

What `prepare` does (nothing outside the named database and work folder is written):
1. `git archive HEAD` of backend/gateway/host/simulator/contracts/config into `<work>/tree`, with its own `var/`
   holding only the Kobo Site file the stored import record names (the S1 test fixture, matching digest).
2. `CREATE DATABASE <db>`, migrated to head. An existing database of that name is dropped first only when the
   work folder's marker records that this tool made it; otherwise `prepare` refuses.
3. Runs S3-02a's fixture builder (`backend/tests/s3_claim_limit_records.py::build`): real Batch V2 ingestion under
   the Site's registered gateway and the real S3 assessment worker; nothing is hand-inserted. Its manifest of exact
   IDs is written to `<work>/manifest.json`; the ingestion sequence state to `<work>/runner-state.json` (for `late`).
4. Runs the S2 Evidence comparison and then the Performance comparison in the private tree and records both exits
   in `<work>/gates.json`. A comparison that does not pass stops `prepare` (the claim-limit read stays closed).
5. Starts the real API once on the API port and reads every case's exact selected revision through
   `/api/sites/KOBO-001/performance/dispatch/windows/{day}/claim-limit?revision=...`, checking it against the
   manifest's expectation; writes `<work>/verify.json`. Stops on any mismatch.

`serve` starts the API (`host/lab_app.py`) on 127.0.0.1:8932 against the private database and prints the frontend
command (port 5442) and the exact Evidence Analysis URLs (`?view=analysis&day=<YYYY-MM-DD>&revision=<id>`).

`late` delivers one late accepted battery-charge reading (08:12 on the full-coverage day, sealed and ingested like any
other) and leaves its recompute job outstanding (no worker pass), so the full-coverage revision the owner has open is
withdrawn from currentness: on reload it reads "Out of date · being redone" with no current conclusion, only what the
version said at the time. The other cases are untouched.

`attest` (API stopped) re-reads every case through the served route and fails unless both comparisons passed and
every read matches; after `late` the full-coverage revision must read STALE_PROJECTION with no current claim.

`drop` removes the database and the work folder, and only those this tool made (the marker records the database).

Guards: `--db` must start with `assetops_s302`, be a plain identifier and never end in `_test`; `--work` must be a
`var/s302*` folder directly under this repository's `var/`.
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
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = Path(sys.executable)
PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
PG_ADMIN = f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops"
API_PORT, WEB_PORT = 8932, 5442
MARKER = ".s302-walkthrough-work"
SITE = "KOBO-001"
FULL_DAY = "2026-10-06"

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
from s3_claim_limit_records import build

engine = create_engine(url)
runner = CaseRunner(PostgresFoundationStore(url), engine)
manifest = build(runner, url)
(out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
state = {"now": runner.now.isoformat(), "seq": [[list(k), v] for k, v in runner.seq.items()],
         "binding_set_revision_id": str(runner.kit.doc["mapping"]["binding_set_id"])}
with engine.connect() as c:
    from sqlalchemy import text
    state["set_revision_id"] = str(c.execute(text(
        "SELECT id FROM signal_binding_set_revision WHERE site_id = :s ORDER BY valid_from DESC, recorded_at DESC LIMIT 1"),
        {"s": runner.site}).scalar_one())
(out / "runner-state.json").write_text(json.dumps(state, indent=2))
engine.dispose()
print("built:", ", ".join(f"{k} {v['day']} {v['status']}" for k, v in manifest["cases"].items()))
'''

LATE = r'''
import json, sys
from datetime import datetime
from pathlib import Path
url, out = sys.argv[1], Path(sys.argv[2])
from sqlalchemy import create_engine
from test_s2_evidence_ledger_postgres import Kit
from test_s4_finding_store_postgres import CaseRunner
from assetops_backend.analytics import dispatch_v3
from s3_claim_limit_records import SIG, _at, _selected, deliver

state = json.loads((out / "runner-state.json").read_text())
engine = create_engine(url)
runner = CaseRunner.__new__(CaseRunner)  # the prepared Site; no second conversion or setup
runner.engine, runner.model = engine, dispatch_v3
runner.kit = Kit(engine, state["set_revision_id"])
runner.tenant, runner.site = runner.kit.principal.tenant_id, runner.kit.principal.site_id
runner.seq = {tuple(k): v for k, v in state["seq"]}
runner.now = datetime.fromisoformat(state["now"])
day = sys.argv[3]
before = _selected(url, runner, day)
deliver(runner, [(*SIG["soc"], _at(day, 8, 12), "79", "GOOD")], "2026-10-30T11:00:00Z")
# No worker pass: the recompute job stays outstanding, so the day's selection is withdrawn from currentness
# (STALE_PROJECTION) and the other cases' selections are left exactly as prepared.
after = _selected(url, runner, day)
state["now"] = runner.now.isoformat()
state["seq"] = [[list(k), v] for k, v in runner.seq.items()]
(out / "runner-state.json").write_text(json.dumps(state, indent=2))
(out / "late.json").write_text(json.dumps({"day": day, "before": before, "after": after}, indent=2))
engine.dispose()
print("late:", before["interval_revision_ids"], "->", after["interval_revision_ids"], after["status"])
'''


def say(text: str = "") -> None:
    print(text, flush=True)


class Walk:
    def __init__(self, db: str, work: str) -> None:
        if not re.fullmatch(r"assetops_s302[a-z0-9_]{0,40}", db) or db.endswith("_test"):
            raise SystemExit(f"Refused: --db {db!r} must start with assetops_s302, be a plain lower-case "
                             "identifier and must not end in _test")
        path = (REPO / work).resolve() if not Path(work).is_absolute() else Path(work).resolve()
        if path.parent != (REPO / "var").resolve() or not path.name.startswith("s302"):
            raise SystemExit(f"Refused: --work {path} must be a var/s302* folder directly under {REPO / 'var'}")
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
        if not self.owned():
            return None
        for line in (self.work / MARKER).read_text(encoding="utf-8").splitlines():
            if line.startswith("db="):
                return line[3:].strip()
        return None

    def db_exists(self, c) -> bool:
        return c.execute("SELECT 1 FROM pg_database WHERE datname = %s", (self.db,)).fetchone() is not None

    def load(self, name: str) -> dict:
        path = self.work / name
        if not path.is_file():
            raise SystemExit(f"Missing {path}: run prepare first.")
        return json.loads(path.read_text(encoding="utf-8"))

    # --- prepare ----------------------------------------------------------------------------------------------------

    def prepare(self, port: int) -> None:
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
        for stale in ("manifest.json", "runner-state.json", "gates.json", "verify.json", "late.json", "attest.json"):
            (self.work / stale).unlink(missing_ok=True)
        (self.work / MARKER).write_text(f"created by tools/s302_claim_limit_walkthrough.py\ndb={self.db}\n", encoding="utf-8")
        archive = subprocess.run(["git", "archive", "--format=tar", "HEAD", "backend", "gateway", "host", "simulator",
                                  "contracts", "config", "contract-fixtures"], cwd=REPO, capture_output=True,
                                 check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(self.tree, filter="data")
        (self.tree / "var" / "sites").mkdir(parents=True)
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

        say("=== 3. s3-claim-limit-records-v1 through Batch V2 ingestion and the S3 worker ===")
        say("  " + self.py("-c", BUILD, self.url, str(self.work), tests=True,
                           cwd=self.tree / "backend" / "tests").stdout.strip().splitlines()[-1])

        say("=== 4. S2 Evidence comparison, then the Performance comparison ===")
        gates = {}
        for name, module in (("evidence", "assetops_backend.evidence_migration"),
                             ("performance", "assetops_backend.performance_migration")):
            done = self.py("-m", module, "run", "--tenant", "demo", "--site", SITE, check=False)
            last = (done.stdout.strip().splitlines() or ["(no output)"])[-1]
            gates[name] = {"exit": done.returncode, "passed": done.returncode == 0, "last_line": last}
            say(f"  {name}: exit {done.returncode} - {last}")
            if done.returncode != 0:
                (self.work / "gates.json").write_text(json.dumps(gates, indent=2))
                raise SystemExit(f"FAILED: the {name} comparison did not pass; the claim-limit read stays closed.\n"
                                 f"{done.stderr.strip()[-2000:]}")
        (self.work / "gates.json").write_text(json.dumps(gates, indent=2))

        say("=== 5. Every case's selected revision through the served route ===")
        verify = self.check(port, after_late=False)
        (self.work / "verify.json").write_text(json.dumps(verify, indent=2))
        say("Prepared. Next: serve.")

    # --- served-route checks ----------------------------------------------------------------------------------------

    def start_api(self, port: int) -> subprocess.Popen:
        logs = self.work / "logs"
        logs.mkdir(exist_ok=True)
        log = open(logs / f"api-{port}.log", "a", encoding="utf-8")
        proc = subprocess.Popen([str(PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(port)],
                                cwd=str(self.tree / "host"), env=self.env(), stdout=log, stderr=subprocess.STDOUT)
        return proc

    def get(self, port: int, path: str) -> tuple[int, dict]:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=30) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            raw = e.read() or b"{}"
            try:
                return e.code, json.loads(raw)
            except ValueError:
                return e.code, {}

    def check(self, port: int, *, after_late: bool) -> dict:
        m = self.load("manifest.json")
        proc = self.start_api(port)
        try:
            for _ in range(120):
                try:
                    self.get(port, "/api/health")
                    break
                except (urllib.error.URLError, ConnectionError, OSError):
                    if proc.poll() is not None:
                        raise SystemExit(f"API exited ({proc.returncode}); see {self.work / 'logs'}")
                    time.sleep(1)
            route = f"/api/sites/{SITE}/performance/dispatch/windows/{{day}}/claim-limit?revision={{rev}}"
            plan = []
            for name, case in m["cases"].items():
                plan.append((name, case["day"], case["interval_revision_ids"][0], case["expect"]))
            withdrawn = m["cases"]["late-revision"]["withdrawn"]["interval_revision_ids"][0]
            plan.append(("late-revision/withdrawn", m["cases"]["late-revision"]["day"], withdrawn,
                         {"currentness": "HISTORICAL", "ceiling": None}))
            if after_late:
                late = self.load("late.json")
                plan = [p for p in plan if p[0] != "full-candidate"]
                plan.append(("full-candidate/after-late", late["day"], late["before"]["interval_revision_ids"][0],
                             {"currentness": "STALE_PROJECTION", "ceiling": None}))
            out, bad = {}, []
            for name, day, rev, expect in plan:
                status, body = self.get(port, route.format(day=day, rev=rev))
                limit = body.get("claim_limit") or {}
                got = {"http": status, "currentness": body.get("currentness"), "ceiling": limit.get("ceiling"),
                       "support": limit.get("support"), "historical_ceiling": (limit.get("historical_ceiling") or {}).get("ceiling"),
                       "assessment_revision_id": body.get("assessment_revision_id"),
                       "run_id": (body.get("run") or {}).get("run_id"), "cohort_status": (body.get("run") or {}).get("cohort_status"),
                       "watermarks": body.get("watermarks"), "accepted_evidence_ids": len(body.get("accepted_evidence_ids") or [])}
                ok = status == 200 and got["assessment_revision_id"] == rev and all(
                    got.get(k) == v for k, v in expect.items() if k in ("currentness", "ceiling", "support"))
                if expect.get("ceiling") is None and "ceiling" in expect and limit.get("current_positive_claim"):
                    ok = False
                out[name] = {"day": day, "revision": rev, "expect": expect, "got": got, "ok": ok}
                say(f"  {'ok ' if ok else 'BAD'} {name:34} {day} {got['currentness']:16} {got['ceiling']} {got['support']}")
                if not ok:
                    bad.append(name)
            status, body = self.get(port, route.format(day=FULL_DAY, rev="00000000-0000-4000-8000-000000000000"))
            out["refusal/unknown-revision"] = {"http": status, "code": (body.get("detail") or {}).get("code")
                                               if isinstance(body.get("detail"), dict) else body.get("detail")}
            say(f"  refusal for an unknown revision: {status} {out['refusal/unknown-revision']['code']}")
            if bad:
                raise SystemExit(f"FAILED: served reads do not match the manifest: {', '.join(bad)}")
            return out
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()

    # --- serve / late / attest / drop -------------------------------------------------------------------------------

    def links(self, web: int) -> None:
        m = self.load("manifest.json")
        base = f"http://127.0.0.1:{web}/sites/{SITE}/evidence?view=analysis"
        c = m["cases"]
        rows = [
            ("No assessment selected (Analysis, nothing chosen)", base),
            ("Full coverage (current, Candidate)", f"{base}&day={c['full-candidate']['day']}&revision={c['full-candidate']['interval_revision_ids'][0]}"),
            ("Missing solar reading (current, Indeterminate)", f"{base}&day={c['missing-pv']['day']}&revision={c['missing-pv']['interval_revision_ids'][0]}"),
            ("Unreliable and conflicting readings (current, limited)",
             f"{base}&day={c['poor-quality-conflict']['day']}&revision={c['poor-quality-conflict']['interval_revision_ids'][0]}"),
            ("Earlier version after a late reading (audit only)",
             f"{base}&day={c['late-revision']['day']}&revision={c['late-revision']['withdrawn']['interval_revision_ids'][0]}"),
            ("Out of date, being redone", f"{base}&day={c['stale-selection']['day']}&revision={c['stale-selection']['interval_revision_ids'][0]}"),
            ("Day chosen, no assessment selected", f"{base}&day={c['full-candidate']['day']}"),
            ("Refused: revision from another day",
             f"{base}&day={c['missing-pv']['day']}&revision={c['full-candidate']['interval_revision_ids'][0]}"),
        ]
        for label, url in rows:
            say(f"  {label}\n    {url}")
        say(f"  Mock to compare: frontend/mockups/v69/index.html#/evidence-analysis")

    def serve(self, port: int, web: int) -> None:
        self.load("manifest.json")
        proc = self.start_api(port)
        say(f"API on http://127.0.0.1:{port} (log {self.work / 'logs' / f'api-{port}.log'}), pid {proc.pid}")
        say(f'Frontend, in a second PowerShell at frontend/:  $env:ASSETOPS_API_PORT="{port}"; '
            f"npm.cmd run dev -- --port {web} --strictPort")
        self.links(web)
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()

    def late(self) -> None:
        self.load("runner-state.json")
        say(f"=== Late battery-charge reading for {FULL_DAY} 08:12, then the S3 worker ===")
        say("  " + self.py("-c", LATE, self.url, str(self.work), FULL_DAY, tests=True,
                           cwd=self.tree / "backend" / "tests").stdout.strip().splitlines()[-1])
        say("Reload the full-coverage URL: it now reads 'Out of date · being redone', with no current conclusion.")

    def attest(self, port: int) -> None:
        gates = self.load("gates.json")
        failed = [k for k in ("evidence", "performance") if not gates.get(k, {}).get("passed")]
        if failed:
            raise SystemExit(f"ATTEST FAILED: comparison(s) did not pass: {', '.join(failed)}")
        after_late = (self.work / "late.json").is_file()
        out = self.check(port, after_late=after_late)
        (self.work / "attest.json").write_text(json.dumps({"gates": gates, "after_late": after_late, "reads": out},
                                                          indent=2))
        say(f"ATTEST PASSED: both comparisons passed; {len(out) - 1} served reads match"
            f"{' (after late)' if after_late else ''}.")

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
            if recorded != self.db:
                raise SystemExit(f"Not removing {self.work}: its marker records database {recorded or 'nothing'}, "
                                 f"not {self.db}")
            shutil.rmtree(self.work)
            say(f"removed {self.work}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="tools/s302_claim_limit_walkthrough.py")
    parser.add_argument("--db", required=True, help="private database, assetops_s302*")
    parser.add_argument("--work", required=True, help="work folder var/s302* under this repository")
    parser.add_argument("--port", type=int, default=API_PORT, help="API port")
    parser.add_argument("--web-port", type=int, default=WEB_PORT, help="frontend port")
    parser.add_argument("cmd", choices=["prepare", "links", "serve", "late", "attest", "drop"])
    args = parser.parse_args()
    walk = Walk(args.db, args.work)
    if args.cmd == "prepare":
        walk.prepare(args.port)
    elif args.cmd == "links":
        walk.links(args.web_port)
    elif args.cmd == "serve":
        walk.serve(args.port, args.web_port)
    elif args.cmd == "late":
        walk.late()
    elif args.cmd == "attest":
        walk.attest(args.port)
    else:
        walk.drop()


if __name__ == "__main__":
    main()
