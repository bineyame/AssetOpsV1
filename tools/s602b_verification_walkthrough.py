"""S6-02b owner walkthrough: the Action Plan, Evidence and Verification views over a private database.

    python tools/s602b_verification_walkthrough.py --db assetops_s602b_owner --work var/s602b_owner prepare
    python tools/s602b_verification_walkthrough.py --db assetops_s602b_owner --work var/s602b_owner links
    python tools/s602b_verification_walkthrough.py --db assetops_s602b_owner --work var/s602b_owner serve
    python tools/s602b_verification_walkthrough.py --db assetops_s602b_owner --work var/s602b_owner capture
    python tools/s602b_verification_walkthrough.py --db assetops_s602b_owner --work var/s602b_owner drop

What `prepare` does (nothing outside the named database(s) and work folder is written):
1. `git archive HEAD` of backend/gateway/host/simulator/contracts/config into `<work>/tree`, with its own `var/`
   holding only the Kobo Site file the stored import record names.
2. `CREATE DATABASE <db>` migrated to head, then the public replay of manifest
   `backend/conversions/d-verification-window-v2.json` (D-verification-window, S6-02b phase 1) through the same
   code as `host/tests/test_s6_verification_replay.py`: two registered Lab runs of mini-grid v5 published by a
   real gateway process, accepted by ordinary S2 batch ingestion, assessed (S3) and matched (S4); then
   recommendation -> accept -> apply -> freeze plan -> later selection -> evaluation through the real Action API.
   The served Action is that real VERIFIED one with its exact lineage. Nothing is hand-inserted.
3. One database per TEST-SCOPED case, `<db>_<case>` (holds are battery-scoped, so cases cannot share one):
   target_miss, guardrail (with the hold on a different Finding), inconclusive, withdrawn (late evidence ->
   withdrawn resolution, overlap hold, re-settled outcome), built by `tools/s602b_test_scoped_cases.py` from
   S6-02a's own evaluator test builders. They are test-scoped examples, never Lab runs.

`serve [--case NAME]` starts the replay API (`host/lab_app.py`) on --port (default 8966) and one test-scoped case
on --port + 1 through the cases tool's wrapper (Action clock pinned to the case's recorded end; the authored
window/source fakes for the authored cases), and prints the frontend commands (web --web-port, default 5466, and
--web-port + 1). Restart `serve` with another --case to look at the next case; the frontends keep running.
`capture` (with both frontends running and no `serve` running) starts the APIs itself, runs
`tools/s602b-verification-evidence.mjs` for the replay and then for each case in turn, and stops them. `drop`
removes the databases and the work folder, only when the work folder's marker records this tool made them.

Guards: `--db` must start with `assetops_s602b`, be a plain identifier and never end in `_test`; `--work` must be a
`var/s602b*` folder directly under this repository's `var/`.
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
API_PORT, WEB_PORT = 8966, 5466
MARKER = ".s602b-walkthrough-work"
SITE = "KOBO-001"
CASES = ("target_miss", "guardrail", "inconclusive", "withdrawn", "estate")  # estate: CC-R2 D5 placement
CASES_TOOL = REPO / "tools" / "s602b_test_scoped_cases.py"

# The public replay: the replay test's own helpers, without its pytest database fixture.
REPLAY = r'''
import json, sys, tempfile
from datetime import timedelta
from pathlib import Path
url, out = sys.argv[1], Path(sys.argv[2])
import pg_harness
from alembic import command
command.upgrade(pg_harness._alembic(url), "head")
import test_s6_verification_replay as rp
import test_s1_bindings_postgres as pgb
import test_s6_verification_publication as pub
from sqlalchemy import create_engine, text
from test_s6_verification_plan_postgres import verifying
from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

M = rp.MANIFESTS["v2"]
act, win = M["action"], M["windows"]
tmp = Path(tempfile.mkdtemp(prefix="s602b-replay-", dir=str(out)))
engine = create_engine(url)
store = PostgresFoundationStore(url)
result, _ = pgb.converted(store)
pub.configure(store, result)
with engine.begin() as c:
    c.execute(text("UPDATE gateway SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
    c.execute(text("UPDATE source SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
spec = M["runs"]["baseline"]
base_run, _ = rp._draft(store, spec, M)
published = {"baseline": rp._publish_and_accept(tmp / "baseline", base_run, spec["sequence_epoch"], rp._at(spec["received_at"]))}
runner = rp.LabRunner(store, engine, result, rp._at(spec["received_at"]) + timedelta(minutes=5))
runner.step({"do": "assess"}); runner.step({"do": "match"})
h = verifying(runner)
h.clock.at = rp._at(act["accept_at"])
finding = h.findings()[act["finding_anchor_day"]]
rec = h.recommendation(finding).json()
made = h.accept(finding, rec["proposal"], idempotency_key="replay-accept-0001")
assert made.status_code == 201, made.text
action_id = made.json()["action"]["action_id"]
h.clock.at = rp._at(act["apply_at"])
current = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()["application_basis"]["current_foundation_revision_id"]
applied = h.client.post(f"/api/sites/KOBO-001/actions/{action_id}/apply", json={
    "expected_foundation_revision_id": current, "value": act["reserve_new"], "effective_from": act["effective_from"],
    "idempotency_key": "replay-apply-0001"})
assert applied.status_code == 201, applied.text
runner.now = max(runner.now, h.clock.at); runner.step({"do": "assess"}); runner.step({"do": "match"})
h.clock.at = max(rp._at(M["plan"]["freeze_at"]), runner.now + timedelta(minutes=1))
base = f"/api/sites/KOBO-001/actions/{action_id}/verification"
frozen = h.client.post(f"{base}/plans", json={"baseline_start": win["baseline_start"], "later_start": win["later_start"],
                                              "idempotency_key": "replay-freeze-0001"})
assert frozen.status_code == 201, frozen.text
plan = frozen.json()["plan"]
spec = M["runs"]["later"]
later_run, _ = rp._draft(store, spec, M)
published["later"] = rp._publish_and_accept(tmp / "later", later_run, spec["sequence_epoch"], rp._at(spec["received_at"]))
runner.now = max(runner.now, rp._at(spec["received_at"]) + timedelta(minutes=5))
runner.step({"do": "assess"}); runner.step({"do": "match"})
h.clock.at = max(rp._at(M["evaluate_at"]), runner.now + timedelta(minutes=1))
bound = h.client.post(f"{base}/plans/{plan['plan_id']}/later-selection", json={"idempotency_key": "replay-bind-0001"})
assert bound.status_code == 201, bound.text
made = h.client.post(f"{base}/evaluations", json={"idempotency_key": "replay-eval-0001"})
assert made.status_code == 201, made.text
outcome = made.json()["outcome"]
assert outcome["outcome"] == "VERIFIED", outcome["reasons"]
action = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()
events = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}/events").json()["events"]
sources = outcome["basis"]["source_resolutions"]
ids = {
    "manifest": {"id": M["schema"]["id"], "version": M["schema"]["version"], "file": "backend/conversions/d-verification-window-v2.json",
                 "scenario": M["scenario"], "model_profile": M["model_profile"]},
    "finding": str(finding), "finding_revision": rec["revision_id"],
    "action": action_id, "action_code": action["action"]["action_code"],
    "change": action["change"]["change_id"], "applied_event": action["change"]["applied_event_id"],
    "plan": plan["plan_id"], "outcome": outcome["outcome_id"], "outcome_recorded_at": outcome["recorded_at"],
    "outcome_reasons": outcome["reasons"],
    "old_foundation": plan["old_foundation_revision_id"], "new_foundation": plan["new_foundation_revision_id"],
    "events": [{"id": e["id"], "kind": e["kind"], "recorded_at": e["recorded_at"]} for e in events],
    "runs": {name: [r.get("run_id") for r in sources[name]["runs"]] for name in ("baseline", "later")},
    "run_digests": {name: [r.get("run_identity_sha256") for r in sources[name]["runs"]] for name in ("baseline", "later")},
    "publications": {name: len(sources[name]["publication_ids"]) for name in ("baseline", "later")},
    "published": published,
}
(out / "replay.json").write_text(json.dumps(ids, indent=2, default=str))
h.close(); pg_harness.dispose(runner.findings); pg_harness.dispose(store); engine.dispose()
print("replay: VERIFIED", action_id, outcome["outcome_id"])
'''


def say(text: str = "") -> None:
    print(text, flush=True)


class Walk:
    def __init__(self, db: str, work: str) -> None:
        if not re.fullmatch(r"assetops_s602b[a-z0-9_]{0,40}", db) or db.endswith("_test"):
            raise SystemExit(f"Refused: --db {db!r} must start with assetops_s602b, be a plain lower-case "
                             "identifier and must not end in _test")
        path = (REPO / work).resolve() if not Path(work).is_absolute() else Path(work).resolve()
        if path.parent != (REPO / "var").resolve() or not path.name.startswith("s602b"):
            raise SystemExit(f"Refused: --work {path} must be a var/s602b* folder directly under {REPO / 'var'}")
        self.db = db
        self.case_dbs = {name: f"{db}_{name}" for name in CASES}
        self.all_dbs = (db, *self.case_dbs.values())
        self.work, self.tree = path, path / "tree"

    def url(self, db: str) -> str:
        return f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{db}"

    def env(self, db: str, *, tests: bool = False) -> dict[str, str]:
        out = dict(os.environ)
        parts = ["backend", "gateway", "simulator", "contracts", "host"]
        if tests:
            parts += ["backend/tests", "gateway/tests", "host/tests"]
        out["PYTHONPATH"] = os.pathsep.join(str(self.tree / p) for p in parts)
        out["DATABASE_URL"] = self.url(db)
        out["PYTHONUNBUFFERED"] = "1"
        out.pop("ASSETOPS_TEST_DATABASE_URL", None)
        if tests:
            # The builders' test modules read their database from this name at import; it is the private one.
            out["ASSETOPS_TEST_DATABASE_URL"] = self.url(db)
        return out

    def py(self, db: str, *argv: str, tests: bool = False, check: bool = True,
           cwd: Path | None = None) -> subprocess.CompletedProcess:
        done = subprocess.run([str(PY), *argv], cwd=str(cwd or self.tree), env=self.env(db, tests=tests),
                              capture_output=True, text=True, timeout=1800)
        if check and done.returncode != 0:
            raise SystemExit(f"FAILED: python {' '.join(argv[:2])[:60]}\n{done.stdout[-4000:]}\n{done.stderr[-4000:]}")
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

    @staticmethod
    def exists(c, db: str) -> bool:
        return c.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db,)).fetchone() is not None

    def prepare(self) -> None:
        import psycopg

        if self.work.exists() and any(self.work.iterdir()) and not self.owned():
            raise SystemExit(f"Refused: {self.work} exists, is not empty and was not made by this tool")
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            for db in self.all_dbs:
                if self.exists(c, db) and self.marker_db() != self.db:
                    raise SystemExit(f"Refused: database {db} exists and {self.work / MARKER} does not record that "
                                     "this tool made it; drop it yourself or choose another --db")
        say("=== 1. Private tree (git HEAD) with its own var/ ===")
        if self.tree.exists():
            shutil.rmtree(self.tree)
        self.tree.mkdir(parents=True)
        (self.work / MARKER).write_text(f"created by tools/s602b_verification_walkthrough.py\ndb={self.db}\n",
                                        encoding="utf-8")
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
        probe = self.py(self.db, "-c", "import assetops_backend;print(assetops_backend.__file__)").stdout.strip()
        if str(self.tree).lower() not in probe.lower():
            raise SystemExit(f"Isolation failed: assetops_backend resolves to {probe}")

        say(f"=== 2. Databases {', '.join(self.all_dbs)} ===")
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            for db in self.all_dbs:
                c.execute(f"DROP DATABASE IF EXISTS {db} WITH (FORCE)")
                c.execute(f"CREATE DATABASE {db}")
        say("  created")

        say("=== 3. Public replay of d-verification-window-v2 (about 4 minutes) ===")
        done = self.py(self.db, "-c", REPLAY, self.url(self.db), str(self.work), tests=True,
                       cwd=self.tree / "host" / "tests")
        say("  " + done.stdout.strip().splitlines()[-1])

        say("=== 4. Test-scoped cases (S6-02a evaluator builders; not Lab runs), one database each ===")
        merged = {}
        for name, db in self.case_dbs.items():
            done = self.py(db, str(CASES_TOOL), "build", self.url(db), str(self.work), name, tests=True,
                           cwd=self.tree / "backend" / "tests")
            say("  " + done.stdout.strip().splitlines()[-1])
            merged[name] = json.loads((self.work / f"case-{name}.json").read_text(encoding="utf-8"))
        (self.work / "cases.json").write_text(json.dumps({"cases": merged}, indent=2), encoding="utf-8")

        say("=== 5. Performance comparison (releases the Finding reads) ===")
        for db in self.all_dbs:
            done = self.py(db, "-m", "assetops_backend.performance_migration", "run", "--tenant", "demo", "--site",
                           SITE, check=False)
            say(f"  {db}: " + (done.stdout.strip().splitlines() or ["(no output)"])[-1])
        say("Prepared. Next: serve, then capture.")

    def ids(self) -> tuple[dict, dict]:
        replay, cases = self.work / "replay.json", self.work / "cases.json"
        if not replay.is_file() or not cases.is_file():
            raise SystemExit("Run prepare first.")
        return json.loads(replay.read_text(encoding="utf-8")), json.loads(cases.read_text(encoding="utf-8"))

    def links(self, web: int) -> None:
        r, cases = self.ids()
        base = f"http://localhost:{web}/sites/{SITE}"
        say(f"Replayed Action {r['action_code']} ({r['action']}), manifest {r['manifest']['file']}")
        rows = [
            ("Finding (origin version)", f"{base}/findings/{r['finding']}?revision_id={r['finding_revision']}"),
            ("Recommendation with success panels", f"{base}/findings/{r['finding']}/recommendation?revision_id={r['finding_revision']}"),
            ("Action overview", f"{base}/actions/{r['action']}"),
            ("Plan (current)", f"{base}/actions/{r['action']}/plan"),
            ("Evidence (current)", f"{base}/actions/{r['action']}/evidence"),
            ("Verification (current: VERIFIED)", f"{base}/actions/{r['action']}/verification"),
            ("Verification, exact outcome (Historical label)", f"{base}/actions/{r['action']}/verification?outcome_id={r['outcome']}"),
            ("Plan, exact plan", f"{base}/actions/{r['action']}/plan?plan_revision_id={r['plan']}"),
            ("Selector conflict", f"{base}/actions/{r['action']}/verification?outcome_id={r['outcome']}&recorded_at={r['outcome_recorded_at']}"),
            ("Foundation change (later effect)", f"{base}/foundation/changes/{r['change']}"),
        ]
        for label, url in rows:
            say(f"  {label}\n    {url}")
        cbase = f"http://localhost:{web + 1}/sites/{SITE}"
        say(f"TEST-SCOPED examples (not Lab runs) on the second frontend, port {web + 1}, one case at a time "
            "(serve --case NAME):")
        for name, case in cases["cases"].items():
            if case.get("action") is None:  # CC-R2-Q6: case estate has no Action; its page is the Portfolio
                say(f"  [{name}] TEST-SCOPED: {case['label']}\n    http://localhost:{web + 1}/portfolio?from=2026-10-21T00:00:00Z&to=2026-10-22T00:00:00Z")
                continue
            say(f"  [{name}] TEST-SCOPED: {case['label']}\n    {cbase}/actions/{case['action']}/verification")
            if case.get("recommendation"):
                say(f"    hold: {cbase}/findings/{case['recommendation']['finding']}/recommendation"
                    f"?revision_id={case['recommendation']['revision']}")

    def start_api(self, db: str, port: int, case: str | None = None) -> subprocess.Popen:
        logs = self.work / "logs"
        logs.mkdir(exist_ok=True)
        log = open(logs / f"api-{port}-{case or 'replay'}.log", "w", encoding="utf-8")
        if case is None:
            argv, cwd, env = ["-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(port)], \
                self.tree / "host", self.env(db)
        else:
            argv, cwd, env = [str(CASES_TOOL), "serve", self.url(db), str(self.work), case, str(port)], \
                self.tree / "backend" / "tests", self.env(db, tests=True)
        proc = subprocess.Popen([str(PY), *argv], cwd=str(cwd), env=env, stdout=log, stderr=subprocess.STDOUT)
        import time
        import urllib.request

        for _ in range(240):
            if proc.poll() is not None:
                raise SystemExit(f"API for {db} exited; see {log.name}")
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2).read()
                break
            except Exception:
                time.sleep(0.5)
        else:
            proc.terminate()
            raise SystemExit(f"API for {db} did not answer on port {port}")
        say(f"API for {db}{' (TEST-SCOPED ' + case + ')' if case else ''} on http://127.0.0.1:{port}")
        return proc

    def serve(self, port: int, web: int, case: str) -> None:
        self.ids()
        procs = [self.start_api(self.db, port), self.start_api(self.case_dbs[case], port + 1, case)]
        say("Frontends, each in its own PowerShell window, from frontend/:")
        say(f'  $env:ASSETOPS_API_PORT="{port}"; npm.cmd run dev -- --port {web} --strictPort')
        say(f'  $env:ASSETOPS_API_PORT="{port + 1}"; npm.cmd run dev -- --port {web + 1} --strictPort')
        self.links(web)
        try:
            for proc in procs:
                proc.wait()
        except KeyboardInterrupt:
            for proc in procs:
                proc.terminate()

    def capture(self, port: int, web: int, out: str | None) -> None:
        self.ids()
        target = out or str(self.work / "evidence")
        failed = 0
        for part in ("replay", *CASES):
            proc = self.start_api(self.db, port) if part == "replay" else \
                self.start_api(self.case_dbs[part], port + 1, part)
            try:
                env = dict(os.environ, ASSETOPS_S602B_WORK=str(self.work), ASSETOPS_S602B_PART=part)
                done = subprocess.run(["node", str(REPO / "tools" / "s602b-verification-evidence.mjs"),
                                       f"http://localhost:{web}", f"http://localhost:{web + 1}", target],
                                      cwd=REPO, env=env)
                failed += done.returncode != 0
            finally:
                proc.terminate()
                proc.wait(timeout=30)
        say(f"capture: {failed} part(s) with failed claims; screenshots and results in {target}")
        raise SystemExit(1 if failed else 0)

    def drop(self) -> None:
        import psycopg

        recorded = self.marker_db()
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            for db in self.all_dbs:
                if self.exists(c, db):
                    if recorded != self.db:
                        raise SystemExit(f"Not dropping {db}: {self.work / MARKER} does not record that this tool "
                                         f"made it (recorded: {recorded or 'nothing'})")
                    c.execute(f"DROP DATABASE IF EXISTS {db} WITH (FORCE)")
                    say(f"dropped database {db}")
                else:
                    say(f"database {db} does not exist")
        if self.work.exists():
            if not self.owned() or recorded != self.db:
                raise SystemExit(f"Not removing {self.work}: its marker does not record database {self.db}")
            shutil.rmtree(self.work)
            say(f"removed {self.work}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="tools/s602b_verification_walkthrough.py")
    parser.add_argument("--db", required=True, help="private database, assetops_s602b*")
    parser.add_argument("--work", required=True, help="work folder var/s602b* under this repository")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare")
    lk = sub.add_parser("links")
    lk.add_argument("--web-port", type=int, default=WEB_PORT)
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=API_PORT)
    s.add_argument("--web-port", type=int, default=WEB_PORT)
    s.add_argument("--case", choices=CASES, default=CASES[0])
    cp = sub.add_parser("capture")
    cp.add_argument("--port", type=int, default=API_PORT)
    cp.add_argument("--web-port", type=int, default=WEB_PORT)
    cp.add_argument("--out", default=None)
    sub.add_parser("drop")
    args = parser.parse_args()
    walk = Walk(args.db, args.work)
    if args.cmd == "prepare":
        walk.prepare()
    elif args.cmd == "links":
        walk.links(args.web_port)
    elif args.cmd == "serve":
        walk.serve(args.port, args.web_port, args.case)
    elif args.cmd == "capture":
        walk.capture(args.port, args.web_port, args.out)
    else:
        walk.drop()


if __name__ == "__main__":
    main()
