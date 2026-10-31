"""DEMO-A: the combined three-Site demo dataset (KOBO-001, COLD-LAB-001, EV-LAB-001) in one private database.

    python tools/demo_combined.py --db assetops_demo3_main_test --work var/demo3_main prepare
    python tools/demo_combined.py --db assetops_demo3_main_test --work var/demo3_main links
    python tools/demo_combined.py --db assetops_demo3_main_test --work var/demo3_main serve
    python tools/demo_combined.py --db assetops_demo3_main_test --work var/demo3_main tick
    python tools/demo_combined.py --db assetops_demo3_main_test --work var/demo3_main drop

Build sheet: `AssetOpsV1-plan2/.agent/build-sheet-DEMO-COMBINED.md` (rev 1 + Addendum 1). Every story instant comes
from `backend/conversions/demo-combined-story-v1.json` resolved against one story day
S = floor_utc_day(DB now at prepare) - 2 d (written to `<work>/story.json`); nothing reads `datetime.now()` for a
story instant. The data is registered Lab simulation placed on a story calendar plus prepared example work records
(actor `service:w401-fixture`); it is never presented as live operation.

`prepare` (nothing outside the named database and work folder is written):
1. `git archive HEAD` into `<work>/tree` with `var/sites/kobo-001.yaml` only; one database, migrated to head once.
2. The Sites in increasing install instant (Addendum 1 R3): Kobo (`tools/demo_combined_kobo.py`), GreenHarvest
   (`tools/demo_combined_cold.py`), Depot (`tools/demo_combined_ev.py`), each a child process in the tree.
3. Objectives, the S2 Evidence comparison, two schedule ticks, the Performance comparison, the self-check.
`serve` runs `host/lab_app.py` on --port (default 8990) with the cursor keys from `<work>/keys.json`, plus a
walkthrough-only schedule loop (one tick every 120 s, then the Performance comparison) that stops with serve.
`drop` removes the database and work folder only when the work folder's marker records this tool made them.

Guards: `--db` must match `^assetops_demo3_[a-z0-9]{1,20}_test$`; `--work` must be a `var/demo3*` folder directly
under this repository's `var/`. A wall cap of twice the expected time stops only the PIDs this tool started.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PY = Path(sys.executable)
PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
PG_ADMIN = f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops"
DB_RE = re.compile(r"^assetops_demo3_[a-z0-9]{1,20}_test$")
MARKER = ".demo3-combined-work"
STORY_FILE = REPO / "backend" / "conversions" / "demo-combined-story-v1.json"
API_PORT, WEB_PORT = 8990, 5490
TICK_EVERY_SECONDS = 120
SITES = ("kobo", "cold", "ev")
SITE_CODE = {"kobo": "KOBO-001", "cold": "COLD-LAB-001", "ev": "EV-LAB-001"}
#: Expected wall seconds per step (U1 measured Kobo at 246 s); the cap is twice the sum of the selected steps.
EXPECTED_SECONDS = {"tree": 30, "kobo": 250, "cold": 300, "ev": 200, "finish": 90}
KEY_NAMES = ("ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX", "ASSETOPS_WORK_CURSOR_KEY_HEX")
TICK = ("-m", "assetops_backend.scheduling.run", "tick", "--environment", "default", "--max-sites", "5",
        "--s3-jobs", "10", "--consequence-items", "100")
_OFFSET = re.compile(r"^S([+-]\d+)d (\d{2}):(\d{2})$")


class StoryClockError(SystemExit):
    pass


def say(text: str = "") -> None:
    print(text, flush=True)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def floor_day(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _resolve(node: Any, S: datetime) -> Any:
    if isinstance(node, dict):
        return {k: _resolve(v, S) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve(v, S) for v in node]
    if isinstance(node, str):
        m = _OFFSET.match(node)
        if m:
            return iso(S + timedelta(days=int(m.group(1)), hours=int(m.group(2)), minutes=int(m.group(3))))
    return node


def resolve_story(db_now: datetime, doc: dict | None = None) -> dict:
    """The story clock: S, every resolved instant, the install clocks and their order. Raises
    `INSTALL_CLOCK_CONFLICT` / `STORY_CLOCK_OUT_OF_RANGE` (Addendum 1 R3, sheet section 3 U2)."""
    doc = doc or json.loads(STORY_FILE.read_text(encoding="utf-8"))
    S = floor_day(db_now) + timedelta(days=doc["story_day_offset_days"])
    story = _resolve({k: v for k, v in doc.items() if k in SITES}, S)
    kobo = story["kobo"]
    kobo["install_at"] = kobo["install_fixed"]
    kobo["price_recorded_at"] = iso(at(kobo["install_fixed"]) + timedelta(hours=kobo["price_after_install_hours"]))
    ev = story["ev"]
    ev["setup_at"] = iso(at(ev["install_at"]) + timedelta(hours=ev["setup_after_install_hours"]))
    ev["day_delta_days"] = (at(ev["e_start"]) - at(ev["base_e_start"])).days
    cold = story["cold"]
    failure = at(cold["failure_night_day"])
    # w502's fixed offsets from the failure night's d16 (OUT-C U3: visits wr_at - 24 d / - 11 d, WR at d16 + 20 min).
    cold["earliest_row_at"] = iso(failure + timedelta(hours=16, minutes=20) - timedelta(days=24))
    earliest = {
        "kobo": min([at(v["at"]) for v in kobo["visits"] + kobo["plans"]] +
                    [at(kobo["runs"]["baseline"]["foundation_known_at"])]),
        "cold": min(at(cold["earliest_row_at"]), at(cold["normal_night_day"]) + timedelta(hours=16)),
        "ev": min([at(v["at"]) for v in ev["visits"] + ev["plans"]] + [at(ev["e_start"])]),
    }
    installs = {name: at(story[name]["install_at"]) for name in SITES}
    order = sorted(SITES, key=lambda n: installs[n])
    if len(set(installs.values())) != len(installs):
        raise StoryClockError(f"INSTALL_CLOCK_CONFLICT: install instants are not distinct {installs}")
    lead = timedelta(hours=doc["install_min_lead_hours"])
    for name in SITES:
        if installs[name] + lead > earliest[name]:
            raise StoryClockError(f"INSTALL_CLOCK_CONFLICT: {name} installs at {iso(installs[name])}, less than "
                                  f"{lead} before its earliest row {iso(earliest[name])}")
    floor = db_now - timedelta(days=doc["max_backdate_days"]) + timedelta(hours=doc["backdate_margin_hours"])
    work_rows = [v["at"] for v in kobo["visits"] + kobo["plans"] + ev["visits"] + ev["plans"]] + [cold["earliest_row_at"]]
    for value in work_rows:
        if at(value) < floor or at(value) > db_now + timedelta(minutes=5):
            raise StoryClockError(f"STORY_CLOCK_OUT_OF_RANGE: work occurred_at {value} is outside "
                                  f"[{iso(floor)}, {iso(db_now + timedelta(minutes=5))}]")
    return {"schema": doc["schema"], "label": doc["label"], "db_now": iso(db_now), "S": iso(S),
            "S_date": S.date().isoformat(), "install_order": order,
            "installs": {n: iso(installs[n]) for n in order}, "earliest_rows": {n: iso(v) for n, v in earliest.items()},
            **story}


class Demo:
    def __init__(self, db: str, work: str) -> None:
        if not DB_RE.fullmatch(db):
            raise SystemExit(f"Refused: --db {db!r} must match {DB_RE.pattern}")
        path = (REPO / work).resolve() if not Path(work).is_absolute() else Path(work).resolve()
        if path.parent != (REPO / "var").resolve() or not path.name.startswith("demo3"):
            raise SystemExit(f"Refused: --work {path} must be a var/demo3* folder directly under {REPO / 'var'}")
        self.db, self.work, self.tree = db, path, path / "tree"
        self.url = f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{db}"
        self.deadline: float | None = None
        self.started: list[int] = []

    # ---- environment -------------------------------------------------------------------------------------------
    def env(self, *, keys: bool = False) -> dict[str, str]:
        out = dict(os.environ)
        parts = ["backend", "backend/tests", "contracts", "gateway", "simulator", "host", "host/tests",
                 "gateway/tests", "tools"]
        out["PYTHONPATH"] = os.pathsep.join(str(self.tree / p) for p in parts)
        out["DATABASE_URL"] = out["ASSETOPS_TEST_DATABASE_URL"] = self.url
        out["PYTHONUNBUFFERED"] = "1"
        for k in ("ASSETOPS_TEST_RUN_ID", "ASSETOPS_TEST_DATABASE_BASE_URL"):
            out.pop(k, None)
        for k in KEY_NAMES:
            out.pop(k, None)
        if keys:
            out.update(json.loads((self.work / "keys.json").read_text(encoding="utf-8")))
        return out

    def py(self, *argv: str, cwd: Path | None = None, check: bool = True, label: str = "") -> subprocess.CompletedProcess:
        """One child in the tree, bounded by the wall cap; on the cap it kills only that child's process tree."""
        logs = self.work / "logs"
        logs.mkdir(exist_ok=True)
        name = label or argv[0].split("/")[-1].split("\\")[-1]
        log_path = logs / f"{len(list(logs.iterdir())):02d}-{re.sub(r'[^a-z0-9_.-]', '_', name.lower())[:40]}.log"
        with open(log_path, "w", encoding="utf-8") as log:
            proc = subprocess.Popen([str(PY), *argv], cwd=str(cwd or self.tree), env=self.env(), stdout=log,
                                    stderr=subprocess.STDOUT, text=True)
            self.started.append(proc.pid)
            remaining = None if self.deadline is None else max(1.0, self.deadline - time.monotonic())
            try:
                code = proc.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                _kill_tree(proc.pid)
                raise SystemExit(f"WALL CAP reached during {name}; stopped PID {proc.pid} (log {log_path})")
        output = log_path.read_text(encoding="utf-8", errors="replace")
        done = subprocess.CompletedProcess(argv, code, output, "")
        if check and code != 0:
            raise SystemExit(f"FAILED: {name} (exit {code}); log {log_path}\n{output[-3000:]}")
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

    def story(self) -> dict:
        path = self.work / "story.json"
        if not path.is_file():
            raise SystemExit("Run prepare first.")
        return json.loads(path.read_text(encoding="utf-8"))

    # ---- prepare -----------------------------------------------------------------------------------------------
    def prepare(self, sites: tuple[str, ...] = SITES, finish: bool = True) -> dict:
        import psycopg

        cap = 2 * (EXPECTED_SECONDS["tree"] + sum(EXPECTED_SECONDS[s] for s in sites) +
                   (EXPECTED_SECONDS["finish"] if finish else 0))
        self.deadline = time.monotonic() + cap
        began = time.monotonic()
        if self.work.exists() and any(self.work.iterdir()) and not self.owned():
            raise SystemExit(f"Refused: {self.work} exists, is not empty and was not made by this tool")
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            if self.exists(c, self.db) and self.marker_db() != self.db:
                raise SystemExit(f"Refused: database {self.db} exists and {self.work / MARKER} does not record that "
                                 "this tool made it; choose another --db")
        say(f"=== 1. Private tree (git HEAD), database {self.db}, story clock (wall cap {cap} s) ===")
        if self.work.exists():
            for child in self.work.iterdir():
                if child.name != MARKER:
                    shutil.rmtree(child) if child.is_dir() else child.unlink()
        self.work.mkdir(parents=True, exist_ok=True)
        (self.work / MARKER).write_text(f"created by tools/demo_combined.py\ndb={self.db}\n", encoding="utf-8")
        self.tree.mkdir()
        archive = subprocess.run(["git", "archive", "--format=tar", "HEAD", "backend", "gateway", "host", "simulator",
                                  "contracts", "config", "contract-fixtures", "tools"], cwd=REPO,
                                 capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(self.tree, filter="data")
        (self.tree / "var" / "sites").mkdir(parents=True)
        shutil.copy2(self.tree / "backend" / "tests" / "fixtures" / "s1" / "kobo-001.yaml",
                     self.tree / "var" / "sites" / "kobo-001.yaml")
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True)
        probe = self.py("-c", "import assetops_backend;print(assetops_backend.__file__)", label="isolation").stdout
        if str(self.tree).lower() not in probe.lower():
            raise SystemExit(f"Isolation failed: assetops_backend resolves to {probe.strip()}")
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE)")
            c.execute(f"CREATE DATABASE {self.db}")
        self.py("-c", "import sys, pg_harness\nfrom alembic import command\n"
                      "command.upgrade(pg_harness._alembic(sys.argv[1]), 'head')", self.url, label="migrate",
                cwd=self.tree / "backend" / "tests")
        with psycopg.connect(PG_ADMIN.rsplit("/", 1)[0] + "/" + self.db, autocommit=True) as c:
            db_now = c.execute("SELECT clock_timestamp()").fetchone()[0]
        story = resolve_story(db_now)
        story["code"] = head.stdout.strip()
        story["sites"] = [s for s in story["install_order"] if s in sites]
        (self.work / "story.json").write_text(json.dumps(story, indent=2), encoding="utf-8")
        keys = {k: secrets.token_hex(32) for k in KEY_NAMES}
        (self.work / "keys.json").write_text(json.dumps(keys), encoding="utf-8")
        say(f"  tree {self.tree} (code {story['code']}); S = {story['S']}; install order {story['install_order']}")

        timings: dict[str, float] = {}
        for n, site in enumerate(story["sites"], start=2):
            say(f"=== {n}. {SITE_CODE[site]} (installs {story['installs'][site]}) ===")
            t0 = time.monotonic()
            done = self.py(str(self.tree / "tools" / f"demo_combined_{site}.py"), "build", self.url, str(self.work),
                           cwd=self.tree / "backend" / "tests", label=f"build-{site}")
            timings[site] = round(time.monotonic() - t0, 1)
            say("  " + (done.stdout.strip().splitlines() or ["(no output)"])[-1] + f"  [{timings[site]} s]")
        if finish:
            t0 = time.monotonic()
            self.finish(story)
            timings["finish"] = round(time.monotonic() - t0, 1)
        manifest = {"db": self.db, "S": story["S"], "code": story["code"], "sites": story["sites"],
                    "timings_seconds": timings, "wall_seconds": round(time.monotonic() - began, 1),
                    "wall_cap_seconds": cap}
        for site in story["sites"]:
            path = self.work / f"{site}.json"
            manifest[site] = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
        (self.work / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
        say(f"Prepared in {manifest['wall_seconds']} s (cap {cap} s). Next: links, serve.")
        return manifest

    def finish(self, story: dict) -> None:
        say("=== Objectives, S2 comparison, two ticks, Performance comparison ===")
        if set(story["sites"]) == set(SITES):
            done = self.py("-m", "assetops_backend.declare_objective", "fixture", "--file",
                           str(self.tree / "backend" / "conversions" / "demo-objectives.json"), label="objectives")
            lines = [json.loads(x) for x in done.stdout.splitlines() if x.startswith("{")]
            (self.work / "objectives.json").write_text(json.dumps(lines, indent=2), encoding="utf-8")
            say(f"  objectives: {len(lines)} lines")
        if "kobo" in story["sites"]:
            done = self.py("-m", "assetops_backend.evidence_migration", "run", "--tenant", "demo", "--site", "KOBO-001",
                           label="s2-comparison")
            say("  " + (done.stdout.strip().splitlines() or ["(no output)"])[-1])
        self.tick(times=2)
        if set(story["sites"]) == set(SITES):
            done = self.py(str(self.tree / "tools" / "demo_combined_finish.py"), "check", self.url, str(self.work),
                           cwd=self.tree / "backend" / "tests", label="self-check", check=False)
            tail = done.stdout.strip().splitlines()
            say("  " + (tail or ["(no output)"])[-1])
            if done.returncode != 0:
                raise SystemExit(f"SELF-CHECK FAILED; see {self.work / 'check.json'}")

    def tick(self, times: int = 1) -> None:
        for _ in range(times):
            done = self.py(*TICK, label="tick", check=False)
            say("  tick: " + (done.stdout.strip().splitlines() or ["(no output)"])[-1][:160])
        for site in ("KOBO-001",):
            done = self.py("-m", "assetops_backend.performance_migration", "run", "--tenant", "demo", "--site", site,
                           label="performance", check=False)
            say("  performance: " + (done.stdout.strip().splitlines() or ["(no output)"])[-1][:160])

    # ---- reading -----------------------------------------------------------------------------------------------
    def links(self, web: int) -> None:
        story = self.story()
        S = at(story["S"])
        frm, to = iso(S), iso(S + timedelta(days=1))
        base = f"http://localhost:{web}"
        rows = [("Portfolio, story day S", f"{base}/portfolio?from={frm}&to={to}")]
        for site in story["sites"]:
            rows.append((f"{SITE_CODE[site]} outcome board, day S", f"{base}/sites/{SITE_CODE[site]}/outcomes?from={frm}&to={to}"))
        kobo = self.work / "kobo.json"
        if kobo.is_file():
            k = json.loads(kobo.read_text(encoding="utf-8"))
            rows += [("KOBO-001 Overview, day S", f"{base}/sites/KOBO-001/overview?date={story['S_date']}"),
                     (f"Action {k.get('action_code')} verification", f"{base}/sites/KOBO-001/actions/{k['action']}/verification"),
                     ("Finding", f"{base}/sites/KOBO-001/findings/{k['finding']}?revision_id={k['finding_revision']}")]
        say(f"Story day S = {story['S_date']} (dates move on every rebuild; quote them from here). Code {story['code']}.")
        for label, url in rows:
            say(f"  {label}\n    {url}")

    def serve(self, port: int, web: int) -> None:
        self.story()
        logs = self.work / "logs"
        logs.mkdir(exist_ok=True)
        log = open(logs / f"api-{port}.log", "w", encoding="utf-8")
        api = subprocess.Popen([str(PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(port)],
                               cwd=str(self.tree / "host"), env=self.env(keys=True), stdout=log,
                               stderr=subprocess.STDOUT)
        import urllib.request

        for _ in range(240):
            if api.poll() is not None:
                raise SystemExit(f"API exited; see {log.name}")
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2).read()
                break
            except Exception:
                time.sleep(0.5)
        else:
            _kill_tree(api.pid)
            raise SystemExit(f"API did not answer on port {port}")
        say(f"API on http://127.0.0.1:{port} (PID {api.pid}). Walkthrough-only schedule loop: one tick every "
            f"{TICK_EVERY_SECONDS} s, then the Performance comparison; it stops with serve.")
        say(f'Frontend, from frontend/:  $env:ASSETOPS_API_PORT="{port}"; npm.cmd run dev -- --port {web} --strictPort')
        self.links(web)
        try:
            while api.poll() is None:
                self.tick()
                for _ in range(TICK_EVERY_SECONDS):
                    if api.poll() is not None:
                        break
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            if api.poll() is None:
                _kill_tree(api.pid)

    def drop(self) -> None:
        import psycopg

        recorded = self.marker_db()
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            if self.exists(c, self.db):
                if recorded != self.db:
                    raise SystemExit(f"Not dropping {self.db}: {self.work / MARKER} does not record that this tool "
                                     f"made it (recorded: {recorded or 'nothing'})")
                c.execute(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE)")
                say(f"dropped database {self.db}")
            else:
                say(f"database {self.db} does not exist")
        if self.work.exists():
            if recorded != self.db:
                raise SystemExit(f"Not removing {self.work}: its marker does not record database {self.db}")
            shutil.rmtree(self.work)
            say(f"removed {self.work}")


def _kill_tree(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
        return
    import signal

    try:
        os.killpg(os.getpgid(pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="tools/demo_combined.py")
    parser.add_argument("--db", required=True, help="private database, assetops_demo3_<name>_test")
    parser.add_argument("--work", required=True, help="work folder var/demo3* under this repository")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--sites", default=",".join(SITES), help="development only: a subset of kobo,cold,ev")
    p.add_argument("--no-finish", action="store_true", help="development only: skip objectives/comparisons/ticks")
    lk = sub.add_parser("links")
    lk.add_argument("--web-port", type=int, default=WEB_PORT)
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=API_PORT)
    s.add_argument("--web-port", type=int, default=WEB_PORT)
    sub.add_parser("tick")
    sub.add_parser("drop")
    args = parser.parse_args(argv)
    demo = Demo(args.db, args.work)
    if args.cmd == "prepare":
        sites = tuple(s for s in args.sites.split(",") if s)
        if not set(sites) <= set(SITES):
            raise SystemExit(f"--sites must be a subset of {SITES}")
        demo.prepare(sites, finish=not args.no_finish)
    elif args.cmd == "links":
        demo.links(args.web_port)
    elif args.cmd == "serve":
        demo.serve(args.port, args.web_port)
    elif args.cmd == "tick":
        demo.story()
        demo.tick()
    else:
        demo.drop()


if __name__ == "__main__":
    main()
