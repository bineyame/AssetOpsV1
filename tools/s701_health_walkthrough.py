"""S7-01b owner walkthrough: Gateway contact (Site Health) and the battery screen over a private database.

    python tools/s701_health_walkthrough.py --db assetops_s701_owner1 --work var/s701_owner1 prepare
    python tools/s701_health_walkthrough.py --db assetops_s701_owner1 --work var/s701_owner1 serve    # until Ctrl+C
    python tools/s701_health_walkthrough.py --db assetops_s701_owner1 --work var/s701_owner1 deliver  # just before viewing
    python tools/s701_health_walkthrough.py --db assetops_s701_owner1 --work var/s701_owner1 attest   # while serve runs
    python tools/s701_health_walkthrough.py --db assetops_s701_owner1 --work var/s701_owner1 drop

What `prepare` does (nothing outside the named database and work folder is written):
1. `git archive HEAD` of backend/gateway/host/simulator/contracts/config into `<work>/tree`, with its own `var/sites`.
2. `CREATE DATABASE <db>`, migrated to head (an existing one is dropped only when this tool's marker records it).
3. Imports KOBO-001 and converts its bindings (S1), THEN registers the eight S7-01a case gateways on it
   (`backend/tests/s7_health_cases.py`). Order matters: eight gateways break S1's one-gateway binding check for any
   later binding publish on KOBO-001 (S7-01a review L1); this database is private, so nothing else edits it.
4. Publishes the six central cases through the authenticated central path (real clock), leaving
   `s7-never-received` without a diagnostic. KOBO-001's battery is configured and bound: condition UNKNOWN with its
   missing causal inputs.
5. Imports KOBO-002 from a copy of the Kobo file without the battery (only its disabled import gateway): Gateway
   contact reads "no enabled gateway" and the battery reads NOT_CONFIGURED.

On the real clock a 60 s cadence case reads STALE about 120 s after its last receipt (S7-01a review L4). `deliver`
re-posts the last facts of every case meant to read CURRENT (`CURRENT_CONTACT_KEYS`) at the next local sequence;
run it right before opening the URLs. `attest` reads the served API and checks each case; it asserts the
stale-cadence case only once 60 s have passed since that case's only receipt.

Guards: `--db` must start with `assetops_s701_owner`, be a plain identifier and never end in `_test`; `--work` must
be a `var/s701_owner*` folder directly under this repository's `var/`. `drop` removes only what the marker records.
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
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = Path(sys.executable)
PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
PG_ADMIN = f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops"
API_PORT, WEB_PORT = 8947, 5447
MARKER = ".s701-walkthrough-work"
SITE, OTHER = "KOBO-001", "KOBO-002"

BUILD = r'''
import json, sys
from datetime import datetime, timezone
from pathlib import Path
url, out, sites = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
import pg_harness
from alembic import command
command.upgrade(pg_harness._alembic(url), "head")
from sqlalchemy import create_engine
from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
from test_s1_bindings_postgres import converted
from test_s7_asset_boundary_postgres import without_battery
from s7_health_cases import CASES, HealthCases

store = PostgresFoundationStore(url)
result, outcome = converted(store)                       # KOBO-001 bindings exist first (review L1)
other = without_battery(store, sites, code="KOBO-002")   # writes sites/kobo-002.yaml, the file its record names
clock = lambda: datetime.now(timezone.utc)
cases = HealthCases(url, "KOBO-001", out / "cases", clock)
manifest = cases.register()
published_at = clock()
receipts = cases.publish()
cases.close()
pg_harness.dispose(store)
ids = {"site": "KOBO-001", "other_site": "KOBO-002", "site_id": str(result.site.id),
       "other_site_id": str(other.site.id), "published_at": published_at.isoformat(),
       "gateways": {k: v["gateway_id"] for k, v in manifest["gateways"].items()},
       "cadence": {c.key: c.cadence_seconds for c in CASES},
       "receipts": {k: [r["diagnostic_id"] for r in v] for k, v in receipts.items()}}
(out / "walkthrough.json").write_text(json.dumps(ids, indent=2))
print("built:", len(manifest["gateways"]), "case gateways,", sum(len(v) for v in receipts.values()), "diagnostics")
'''

DELIVER = r'''
import json, sys
from datetime import datetime, timezone
from pathlib import Path
url, out = sys.argv[1], Path(sys.argv[2])
from s7_health_cases import CURRENT_CONTACT_KEYS, HealthCases
cases = HealthCases(url, "KOBO-001", out / "cases", lambda: datetime.now(timezone.utc))
got = cases.deliver(CURRENT_CONTACT_KEYS)
cases.close()
for key, receipt in got.items():
    print(f"  {key}: diagnostic {receipt['diagnostic_id']}")
'''

#: What the owner should see per case after `deliver` (contact, reported facts).
EXPECTED = {
    "s7-current": ("CURRENT", "CURRENT"),
    "s7-delayed-old": ("CURRENT", "OLD"),
    "s7-queue-growth": ("CURRENT", None),
    "s7-clock-offset": ("CURRENT", "UNKNOWN"),
    "s7-disk-stop": ("CURRENT", None),
    "s7-disk-recovery": ("CURRENT", None),
    "s7-never-received": ("UNKNOWN", "UNKNOWN"),
}


def say(text: str = "") -> None:
    print(text, flush=True)


class Walk:
    def __init__(self, db: str, work: str) -> None:
        if not re.fullmatch(r"assetops_s701_owner[a-z0-9_]{0,40}", db) or db.endswith("_test"):
            raise SystemExit(f"Refused: --db {db!r} must start with assetops_s701_owner, be a plain lower-case "
                             "identifier and must not end in _test")
        path = (REPO / work).resolve() if not Path(work).is_absolute() else Path(work).resolve()
        if path.parent != (REPO / "var").resolve() or not path.name.startswith("s701_owner"):
            raise SystemExit(f"Refused: --work {path} must be a var/s701_owner* folder directly under {REPO / 'var'}")
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
            # The fixture's test modules read their database from this name at import; it is the private one.
            out["ASSETOPS_TEST_DATABASE_URL"] = self.url
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
        say("=== 1. Private tree (git HEAD) with its own var/sites ===")
        for stale in (self.tree, self.work / "cases"):
            if stale.exists():
                shutil.rmtree(stale)
        self.tree.mkdir(parents=True)
        (self.work / MARKER).write_text(f"created by tools/s701_health_walkthrough.py\ndb={self.db}\n", encoding="utf-8")
        archive = subprocess.run(["git", "archive", "--format=tar", "HEAD", "backend", "gateway", "host", "simulator",
                                  "contracts", "config", "contract-fixtures"], cwd=REPO, capture_output=True,
                                 check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(self.tree, filter="data")
        sites = self.tree / "var" / "sites"
        sites.mkdir(parents=True)
        # The import record names var/sites/kobo-001.yaml with the S1 fixture's digest; KOBO-002's file is written
        # by the builder (the Kobo file without its battery).
        shutil.copy2(self.tree / "backend" / "tests" / "fixtures" / "s1" / "kobo-001.yaml", sites / "kobo-001.yaml")
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

        say("=== 3. KOBO-001 bindings, then the eight case gateways and the six central cases; KOBO-002 ===")
        say("  " + self.py("-c", BUILD, self.url, str(self.work), str(sites), tests=True,
                           cwd=self.tree / "backend" / "tests").stdout.strip().splitlines()[-1])
        say("Prepared. Next: serve (keep it running), then deliver right before viewing, then attest.")

    def ids(self) -> dict:
        path = self.work / "walkthrough.json"
        if not path.is_file():
            raise SystemExit("Run prepare first.")
        return json.loads(path.read_text(encoding="utf-8"))

    def links(self, web: int, port: int) -> None:
        self.ids()
        api = f"http://127.0.0.1:{port}"
        battery = self.api(port, f"/api/sites/{SITE}/battery", quiet=True)
        say("Open these (frontend on port %d):" % web)
        say(f"  KOBO-001 Gateway contact (Site Health)    http://127.0.0.1:{web}/sites/{SITE}/health")
        if battery and battery.get("batteries"):
            asset = battery["batteries"][0]["asset_id"]
            say(f"  KOBO-001 battery (condition Unknown)      http://127.0.0.1:{web}/sites/{SITE}/assets/{asset}")
        else:
            say(f"  KOBO-001 battery: start serve first to resolve the asset ID ({api}/api/sites/{SITE}/battery)")
        say(f"  KOBO-001 battery entry                    http://127.0.0.1:{web}/sites/{SITE}/assets")
        say(f"  KOBO-002 Gateway contact (no enabled one) http://127.0.0.1:{web}/sites/{OTHER}/health")
        say(f"  KOBO-002 battery (not configured)         http://127.0.0.1:{web}/sites/{OTHER}/assets")
        say(f"  Refusal: asset outside the basis          http://127.0.0.1:{web}/sites/{OTHER}/assets/"
            "00000000-0000-4000-8000-000000000000")
        say("  Compare with the mockup: frontend/mockups/v69/index.html#/health and #/asset")

    def serve(self, port: int, web: int) -> None:
        self.ids()
        logs = self.work / "logs"
        logs.mkdir(exist_ok=True)
        log = open(logs / f"api-{port}.log", "w", encoding="utf-8")
        cmd = [str(PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(port)]
        proc = subprocess.Popen(cmd, cwd=str(self.tree / "host"), env=self.env(), stdout=log, stderr=subprocess.STDOUT)
        say(f"API: {' '.join(cmd)}  (cwd {self.tree / 'host'}, DATABASE_URL={self.url})")
        say(f"API on http://127.0.0.1:{port} (log {logs / f'api-{port}.log'}), pid {proc.pid}")
        say(f'Frontend, in a second PowerShell at {REPO / "frontend"}:')
        say(f'  $env:ASSETOPS_API_PORT="{port}"; npm.cmd run dev -- --port {web} --strictPort')
        import time
        for _ in range(60):
            if proc.poll() is not None:
                raise SystemExit(f"API exited ({proc.returncode}); see {logs / f'api-{port}.log'}")
            if self.api(port, f"/api/sites/{SITE}/battery", quiet=True):
                break
            time.sleep(1)
        self.links(web, port)
        say("Before viewing, in another shell: the same command ending `deliver`, then `attest`.")
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()

    def deliver(self) -> None:
        self.ids()
        say("Fresh receipts for every case meant to read CURRENT (view within about 2 minutes):")
        say(self.py("-c", DELIVER, self.url, str(self.work), tests=True,
                    cwd=self.tree / "backend" / "tests").stdout.rstrip())

    @staticmethod
    def api(port: int, path: str, quiet: bool = False) -> dict | None:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=10) as answer:
                return json.loads(answer.read().decode("utf-8"))
        except (urllib.error.URLError, OSError) as error:
            if quiet:
                return None
            raise SystemExit(f"Cannot read http://127.0.0.1:{port}{path} ({error}); is `serve` running?")

    def attest(self, port: int) -> None:
        ids = self.ids()
        body = self.api(port, f"/api/sites/{SITE}/source-health")
        rows = {g["gateway_external_id"]: g for g in body["gateways"]}
        problems = []
        for key, (contact, facts) in EXPECTED.items():
            row = rows[key]
            got = (row["contact"]["status"], row["reported_facts"]["status"])
            ok = got[0] == contact and (facts is None or got[1] == facts)
            say(f"  {'ok ' if ok else 'BAD'} {key}: contact {got[0]}, facts {got[1]}, "
                f"diagnostic {(row['diagnostic'] or {}).get('diagnostic_id')}, received "
                f"{row['contact']['last_received_at']}")
            if not ok:
                problems.append(f"{key}: expected contact {contact}" + (f"/facts {facts}" if facts else "")
                                + f", got {got}")
        clock = rows["s7-clock-offset"]["reported_facts"]
        if clock["fact_age_seconds"] is not None or clock["clock"]["trust"] != "UNTRUSTED":
            problems.append("s7-clock-offset: an age is stated from an untrusted clock")
        stale = rows["s7-stale-cadence"]
        waited = (datetime.now(timezone.utc) - datetime.fromisoformat(ids["published_at"])).total_seconds()
        if waited >= 60:
            ok = stale["contact"]["status"] == "STALE"
            say(f"  {'ok ' if ok else 'BAD'} s7-stale-cadence: contact {stale['contact']['status']} "
                f"({int(waited)} s after its only receipt)")
            if not ok:
                problems.append("s7-stale-cadence: expected STALE")
        else:
            say(f"  --  s7-stale-cadence: not asserted yet ({int(waited)} s < 60 s since its receipt)")
        summary = body["summary"]
        say(f"  summary: {summary['status']}, enabled {summary['enabled_gateway_count']}, disabled "
            f"{summary['disabled_gateway_count']}, counts {summary['contact_counts']}")
        other = self.api(port, f"/api/sites/{OTHER}/source-health")["summary"]
        say(f"  {OTHER}: {other['status']} / {other['reason']}")
        if (other["status"], other["reason"]) != ("NO_REGISTERED_SOURCE", "NO_ENABLED_GATEWAY"):
            problems.append(f"{OTHER}: expected NO_REGISTERED_SOURCE/NO_ENABLED_GATEWAY")
        battery = self.api(port, f"/api/sites/{OTHER}/battery")
        say(f"  {OTHER} battery: {battery['configuration']}")
        if battery["configuration"] != "NOT_CONFIGURED":
            problems.append(f"{OTHER}: battery expected NOT_CONFIGURED")
        entry = self.api(port, f"/api/sites/{SITE}/battery")
        detail = self.api(port, entry["batteries"][0]["detail_path"])
        say(f"  {SITE} battery: {detail['binding_status']}, condition {detail['physical_condition']['status']}, "
            f"{len(detail['physical_condition']['missing_causal_inputs'])} missing inputs")
        if detail["physical_condition"]["status"] != "UNKNOWN":
            problems.append(f"{SITE}: battery condition expected UNKNOWN")
        if problems:
            raise SystemExit("ATTEST FAILED:\n  " + "\n  ".join(problems))
        say("attest: ok")

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
    parser = argparse.ArgumentParser(prog="tools/s701_health_walkthrough.py")
    parser.add_argument("--db", required=True, help="private database, assetops_s701_owner*")
    parser.add_argument("--work", required=True, help="work folder var/s701_owner* under this repository")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare")
    for name in ("serve", "links", "attest"):
        s = sub.add_parser(name)
        s.add_argument("--port", type=int, default=API_PORT)
        s.add_argument("--web-port", type=int, default=WEB_PORT)
    sub.add_parser("deliver")
    sub.add_parser("drop")
    args = parser.parse_args()
    walk = Walk(args.db, args.work)
    if args.cmd == "prepare":
        walk.prepare()
    elif args.cmd == "serve":
        walk.serve(args.port, args.web_port)
    elif args.cmd == "links":
        walk.links(args.web_port, args.port)
    elif args.cmd == "deliver":
        walk.deliver()
    elif args.cmd == "attest":
        walk.attest(args.port)
    else:
        walk.drop()


if __name__ == "__main__":
    main()
