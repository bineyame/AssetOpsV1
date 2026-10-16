"""S6-03 owner walkthrough: Site > Work > Actions over a private database.

    python tools/s603_site_work_walkthrough.py --db assetops_s603_owner1 --work var/s603_owner1 prepare
    python tools/s603_site_work_walkthrough.py --db assetops_s603_owner1 --work var/s603_owner1 serve    # until Ctrl+C
    python tools/s603_site_work_walkthrough.py --db assetops_s603_owner1 --work var/s603_owner1 attest
    python tools/s603_site_work_walkthrough.py --db assetops_s603_owner1 --work var/s603_owner1 drop

What `prepare` does (nothing outside the named database and work folder is written):
1. `git archive HEAD` of backend/gateway/host/simulator/contracts/config into `<work>/tree`, with its own `var/`
   holding only the Kobo Site file the stored import record names (the S1 test fixture).
2. `CREATE DATABASE <db>`, migrated to head. An existing database of that name is dropped first only when the
   work folder's marker records that this tool made it; otherwise `prepare` refuses.
3. Runs `D-action-records` (`backend/tests/s6_action_records.py::build`, the producer
   `tools/s601b_action_walkthrough.py` uses) with the second Action accepted five minutes after the first, through
   the normal Action creation and event path. Nothing is hand-inserted.
4. Writes `<work>/walkthrough.json`: the Action IDs, persisted creation times, the positive window (the persisted
   creation days) and the assessed-zero window (the 31 days ending where the first Action was created).
5. Runs the Performance comparison so the origin Finding / FindingRevision reads are released, and records whether
   it passed in `<work>/performance.json`.

`serve` checks the private tree's app entry serves the index, starts the real API (`host/lab_app.py`) with
DATABASE_URL = the private database, and prints the frontend command and the positive and zero Site Work URLs.
`attest` fails unless the Performance comparison passed; it then reads both windows through the Site Action index
service on the private database, checks them against an independent SQL count and prints IDs, fence and links.
`drop` removes the database and the work folder, only when the marker records that this tool made them.

Guards: `--db` must start with `assetops_s603_owner`, be a plain identifier and never end in `_test`; `--work` must be
a `var/s603_owner*` folder directly under this repository's `var/`.
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
API_PORT, WEB_PORT = 8943, 5443
MARKER = ".s603-walkthrough-work"
SITE = "KOBO-001"

BUILD = r'''
import json, sys
from datetime import timedelta, timezone
from pathlib import Path
url, out = sys.argv[1], Path(sys.argv[2])
import pg_harness
from alembic import command
command.upgrade(pg_harness._alembic(url), "head")
from sqlalchemy import create_engine, text
from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
from test_s4_finding_store_postgres import CaseRunner
from test_s6_action_store_postgres import CASES
from test_s6_action_records_postgres import make_harness
from s6_action_records import build, fixture_grants

engine = create_engine(url)
runner = CaseRunner(PostgresFoundationStore(url), engine)
build(runner, CASES, make_harness(runner), second_created_after=timedelta(minutes=5))
findings = {f["anchor_start"].date().isoformat(): f["id"] for f in runner.reload()["findings"]}
(out / "action-demo-grants.json").write_text(json.dumps(fixture_grants(runner.tenant, runner.site, findings), indent=2))
with engine.connect() as c:
    rows = [dict(r._mapping) for r in c.execute(text(
        "SELECT id, action_code, created_at, origin_finding_id, origin_finding_revision_id FROM action "
        "WHERE site_id = :s ORDER BY created_at DESC, id"), {"s": runner.site})]
z = lambda t: t.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
first = min(r["created_at"] for r in rows).astimezone(timezone.utc)
last = max(r["created_at"] for r in rows).astimezone(timezone.utc)
lo = first.replace(hour=0, minute=0, second=0, microsecond=0)
hi = last.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
ids = {"site": "KOBO-001", "tenant_id": str(runner.tenant), "site_id": str(runner.site),
       "actions": [{"id": str(r["id"]), "code": r["action_code"], "created_at": z(r["created_at"]),
                    "finding": str(r["origin_finding_id"]), "finding_revision": str(r["origin_finding_revision_id"])}
                   for r in rows],
       "positive": {"from": z(lo), "to": z(hi)},
       "zero": {"from": z(first - timedelta(days=31)), "to": z(first)}}
(out / "walkthrough.json").write_text(json.dumps(ids, indent=2))
engine.dispose()
print("built:", len(rows), "Actions", [r["action_code"] for r in rows])
'''

ATTEST = r'''
import json, sys
from datetime import datetime
from pathlib import Path
from uuid import UUID
url, work = sys.argv[1], Path(sys.argv[2])
ids = json.loads((work / "walkthrough.json").read_text())
from sqlalchemy import create_engine, text
from assetops_backend.actions.adapters.postgres_action_store import PostgresActionStore
from assetops_backend.actions.site_index import ActionIndexService, parse_request
store = PostgresActionStore(url)
service = ActionIndexService(store)
engine = create_engine(url)
out, failures = {}, []
for name in ("positive", "zero"):
    w = ids[name]
    body = service.read(UUID(ids["tenant_id"]), UUID(ids["site_id"]), "KOBO-001",
                        parse_request(w["from"], w["to"], None, None), access_basis="walkthrough attest")
    with engine.connect() as c:
        n = c.execute(text("SELECT count(*) FROM action WHERE site_id = :s AND created_at >= :lo AND created_at < :hi"),
                      {"s": ids["site_id"], "lo": datetime.fromisoformat(w["from"].replace("Z", "+00:00")),
                       "hi": datetime.fromisoformat(w["to"].replace("Z", "+00:00"))}).scalar_one()
    if body["total_count"] != n:
        failures.append(f"{name}: index {body['total_count']} != SQL count {n}")
    out[name] = {"window": w, "total_count": body["total_count"], "sql_count": n, "fence": body["fence"],
                 "rows": [{"code": r["action_code"], "action_id": r["action_id"], "created_at": r["created_at"],
                           "finding_revision_id": r["origin"]["finding_revision_id"],
                           "event": [r["selected_event"]["kind"], r["selected_event"]["id"]],
                           "state": r["state"]["application"], "links": r["links"]} for r in body["rows"]]}
if out["positive"]["total_count"] < 2:
    failures.append("positive window lists fewer than two Actions")
if out["zero"]["total_count"] != 0:
    failures.append("zero window is not zero")
store.dispose()
engine.dispose()
print(json.dumps(out, indent=2))
if failures:
    print("ATTEST FAILED: " + "; ".join(failures))
    sys.exit(1)
print("ATTEST OK")
'''


def say(text: str = "") -> None:
    print(text, flush=True)


class Walk:
    def __init__(self, db: str, work: str) -> None:
        if not re.fullmatch(r"assetops_s603_owner[a-z0-9_]{0,40}", db) or db.endswith("_test"):
            raise SystemExit(f"Refused: --db {db!r} must start with assetops_s603_owner, be a plain lower-case "
                             "identifier and must not end in _test")
        path = (REPO / work).resolve() if not Path(work).is_absolute() else Path(work).resolve()
        if path.parent != (REPO / "var").resolve() or not path.name.startswith("s603_owner"):
            raise SystemExit(f"Refused: --work {path} must be a var/s603_owner* folder directly under {REPO / 'var'}")
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
            out["ASSETOPS_TEST_DATABASE_URL"] = self.url  # the builder's test modules read it at import
        out["ASSETOPS_ACTION_DEMO_GRANTS"] = str(self.work / "action-demo-grants.json")
        return out

    def py(self, *argv: str, tests: bool = False, check: bool = True, cwd: Path | None = None):
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
        (self.work / MARKER).write_text(f"created by tools/s603_site_work_walkthrough.py\ndb={self.db}\n",
                                        encoding="utf-8")
        (self.work / "performance.json").unlink(missing_ok=True)
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

        say("=== 3. D-action-records through the real stores and Action API ===")
        say("  " + self.py("-c", BUILD, self.url, str(self.work), tests=True,
                           cwd=self.tree / "backend" / "tests").stdout.strip().splitlines()[-1])

        say("=== 4. Performance comparison (releases the origin Finding reads) ===")
        done = self.py("-m", "assetops_backend.performance_migration", "run", "--tenant", "demo", "--site", SITE,
                       check=False)
        passed = done.returncode == 0
        last = (done.stdout.strip().splitlines() or ["(no output)"])[-1]
        (self.work / "performance.json").write_text(json.dumps({"passed": passed, "exit": done.returncode,
                                                                "last_line": last}), encoding="utf-8")
        say("  " + last)
        if not passed:
            say(f"  The comparison did not pass (exit {done.returncode}); attest will fail.")
            say("  " + done.stderr.strip()[-2000:].replace("\n", "\n  "))
        say("Prepared. Next: serve (in this window), then the frontend command it prints.")

    def ids(self) -> dict:
        path = self.work / "walkthrough.json"
        if not path.is_file():
            raise SystemExit("Run prepare first.")
        return json.loads(path.read_text(encoding="utf-8"))

    def urls(self, web: int) -> None:
        from urllib.parse import urlencode

        i = self.ids()
        base = f"http://127.0.0.1:{web}/sites/{SITE}/work"
        say(f"  Positive window (Actions created {i['positive']['from']} to {i['positive']['to']}, end excluded):")
        say(f"    {base}?{urlencode(i['positive'])}")
        say("  Same window, one Action per page (to see Next page):")
        say(f"    {base}?{urlencode({**i['positive'], 'limit': 1})}")
        say("  Zero window (31 days ending where the first Action was created):")
        say(f"    {base}?{urlencode(i['zero'])}")
        say(f"  No window (choose-window state):\n    {base}")
        for a in i["actions"]:
            say(f"  {a['code']}  Action {a['id']}  created {a['created_at']}  Finding version {a['finding_revision']}")

    def serve(self, port: int, web: int) -> None:
        self.ids()
        entry = self.tree / "host" / "lab_app.py"
        if not entry.is_file():
            raise SystemExit(f"App entry missing: {entry}")
        probe = self.py("-c", "import lab_app;print(any(getattr(r,'path','')=='/api/sites/{site_code}/action-index' "
                              "for r in lab_app.app.routes))", cwd=self.tree / "host", check=False)
        if probe.stdout.strip().splitlines()[-1:] != ["True"]:
            raise SystemExit(f"The private app does not serve the Site Action index:\n{probe.stdout}\n{probe.stderr}")
        logs = self.work / "logs"
        logs.mkdir(exist_ok=True)
        log = open(logs / f"api-{port}.log", "w", encoding="utf-8")
        proc = subprocess.Popen([str(PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(port)],
                                cwd=str(self.tree / "host"), env=self.env(), stdout=log, stderr=subprocess.STDOUT)
        say(f"API (python -m uvicorn lab_app:app --host 127.0.0.1 --port {port}, from {self.tree / 'host'}, "
            f"DATABASE_URL = {self.db}) on http://127.0.0.1:{port}, pid {proc.pid}, log {logs / f'api-{port}.log'}")
        say(f'Frontend, second PowerShell in frontend/:  $env:ASSETOPS_API_PORT="{port}"; '
            f"npm.cmd run dev -- --port {web} --strictPort")
        self.urls(web)
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()

    def attest(self) -> None:
        path = self.work / "performance.json"
        result = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"passed": False}
        if not result.get("passed"):
            raise SystemExit(f"ATTEST FAILED: the Performance comparison did not pass ({result})")
        done = self.py("-c", ATTEST, self.url, str(self.work), check=False)
        say(done.stdout.strip())
        if done.returncode != 0:
            raise SystemExit(f"ATTEST FAILED (exit {done.returncode})\n{done.stderr[-3000:]}")

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
    parser = argparse.ArgumentParser(prog="tools/s603_site_work_walkthrough.py")
    parser.add_argument("--db", required=True, help="private database, assetops_s603_owner*")
    parser.add_argument("--work", required=True, help="work folder var/s603_owner* under this repository")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare")
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=API_PORT)
    s.add_argument("--web-port", type=int, default=WEB_PORT)
    sub.add_parser("attest")
    sub.add_parser("drop")
    args = parser.parse_args()
    walk = Walk(args.db, args.work)
    if args.cmd == "prepare":
        walk.prepare()
    elif args.cmd == "serve":
        walk.serve(args.port, args.web_port)
    elif args.cmd == "attest":
        walk.attest()
    else:
        walk.drop()


if __name__ == "__main__":
    main()
