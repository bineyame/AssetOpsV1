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
walkthrough-only schedule loop (one tick every 120 s, then the Performance comparison) that stops with serve. After
the first tick it pre-warms the story-week Portfolio outcome summary once and prints "ready:" when that returns 2xx.
`drop` removes the database and work folder only when the work folder's marker records this tool made them.

Guards: `--db` must match `^assetops_(demo3|polish)_[a-z0-9]{1,20}_test$`; `--work` must be a `var/demo3*` or
`var/polish*` folder directly under this repository's `var/` (POLISH Addendum 9 Q1). A wall cap of twice the expected time stops only the PIDs this tool started.
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

import demo_story_days as sd

REPO = Path(__file__).resolve().parents[1]
PY = Path(sys.executable)
PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
PG_ADMIN = f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops"
DB_RE = re.compile(r"^assetops_(demo3|polish)_[a-z0-9]{1,20}_test$")
WORK_PREFIXES = ("demo3", "polish")
MARKER = ".demo3-combined-work"
STORY_FILE = REPO / "backend" / "conversions" / "demo-combined-story-v1.json"
API_PORT, WEB_PORT = 8990, 5490
TICK_EVERY_SECONDS = 120
SITES = ("kobo", "cold", "ev")
SITE_CODE = {"kobo": "KOBO-001", "cold": "COLD-LAB-001", "ev": "EV-LAB-001"}
#: Expected wall seconds per step; the cap is twice the sum of the selected steps. Kobo is
#: `kobo_expected_seconds` (DEMO-SPARSE U3 measured about 105 s per Kobo run: 110 s per run + 60 s).
EXPECTED_SECONDS = {"tree": 30, "kobo": 250, "cold": 300, "ev": 200, "finish": 90}
KEY_NAMES = ("ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX", "ASSETOPS_WORK_CURSOR_KEY_HEX")
TICK = ("-m", "assetops_backend.scheduling.run", "tick", "--environment", "default", "--max-sites", "5",
        "--s3-jobs", "10", "--consequence-items", "100")
_OFFSET = re.compile(r"^S([+-]\d+)d (\d{2}):(\d{2})$")


class StoryClockError(SystemExit):
    pass


def kobo_expected_seconds(days_doc: dict) -> int:
    return 110 * sum(1 for e in days_doc["sites"].get("kobo", []) if e["kind"] != "missing") + 60


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


def _trial(kobo: dict, days: list, window_hour: str) -> None:
    """The trial pair's instants (the DEMO-A chain's `runs` and `windows`) from the day list's trial-* kinds."""
    hh, mm = (int(x) for x in window_hour.split(":"))
    for name, kind in (("baseline", "trial-before"), ("later", "trial-after")):
        run = next(r for r in days if r.site == "kobo" and r.kind == kind)
        kobo["runs"][name] = {"start": iso(run.start), "end": iso(run.end), "foundation_known_at": iso(run.known_at),
                              "received_at": iso(run.received_at), "sequence_epoch": run.epoch,
                              "scenario": run.scenario}
        day = at(run.day + "T00:00:00Z")
        kobo["windows"][f"{name}_start"] = iso(day + timedelta(hours=hh, minutes=mm))


def story_day(db_now: datetime, doc: dict | None = None) -> datetime:
    doc = doc or json.loads(STORY_FILE.read_text(encoding="utf-8"))
    return floor_day(db_now) + timedelta(days=doc["story_day_offset_days"])


def resolve_story(db_now: datetime, doc: dict | None = None, days_doc: dict | None = None) -> dict:
    """The story clock: S, every resolved instant, the install clocks and their order, and the day list in build
    order (`days`). Raises `INSTALL_CLOCK_CONFLICT` / `STORY_CLOCK_OUT_OF_RANGE` (Addendum 1 R3) and the day
    list's `StoryDaysError` codes (DEMO-SPARSE U2)."""
    doc = doc or json.loads(STORY_FILE.read_text(encoding="utf-8"))
    days_doc = days_doc or sd.load()
    S = story_day(db_now, doc)
    story = _resolve({k: v for k, v in doc.items() if k in SITES}, S)
    kobo = story["kobo"]
    kobo["import_at"] = iso(at(kobo["install_at"]) - timedelta(hours=kobo["import_before_install_hours"]))
    kobo["price_recorded_at"] = iso(at(kobo["install_at"]) + timedelta(hours=kobo["price_after_install_hours"]))
    # DD1a1-R7: the Kobo Action's effective instant is the Foundation revision boundary a complement may not span
    days = sd.resolve(days_doc, S, db_now=db_now, installs={n: at(story[n]["install_at"]) for n in SITES},
                      revision_boundaries=(at(kobo["action"]["effective_from"]),))
    kobo["runs"], kobo["windows"] = {}, {}
    _trial(kobo, days, days_doc["trial"]["window_hour"])
    kobo["trial"] = dict(days_doc["trial"])
    ev = story["ev"]
    ev["setup_at"] = iso(at(ev["install_at"]) + timedelta(hours=ev["setup_after_install_hours"]))
    ev["day_delta_days"] = (at(ev["e_start"]) - at(ev["base_e_start"])).days
    cold = story["cold"]
    failure = at(cold["failure_night_day"])
    # w502's fixed offsets from the failure night's d16 (OUT-C U3: visits wr_at - 24 d / - 11 d, WR at d16 + 20 min).
    cold["earliest_row_at"] = iso(failure + timedelta(hours=16, minutes=20) - timedelta(days=24))
    earliest = {
        "kobo": min([at(v["at"]) for v in kobo["visits"] + kobo["plans"]] +
                    [r.start for r in days if r.site == "kobo" and r.has_run]),
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
            "days": [r.payload() for r in days], **story}


#: POLISH §4 P-01/P-02: the route forms `story_links` prints (the board is the Site Overview; there is no
#: `/sites/{code}/outcomes` or `/sites/{code}/overview` route).
LINK_FORMS = ("/portfolio?", "/findings?", "/maintenance/preventive?", "/maintenance?", "/sites/KOBO-001?date=",
              "/sites/COLD-LAB-001?from=", "/sites/EV-LAB-001/ev?from=", "/sites/KOBO-001/actions/",
              "/sites/KOBO-001/findings/")


def story_week_query(story: dict) -> str:
    """The Portfolio and Findings week window around story day S (from S-6d to S+1d)."""
    S = at(story["S"])
    return f"from={iso(S - timedelta(days=6))}&to={iso(S + timedelta(days=1))}"


PREWARM_TIMEOUT_SECONDS = 900


def prewarm(port: int, story: dict, fetch: Any = None, clock: Any = time.monotonic) -> bool:
    """POLISH whole-diff review item 8: request the Portfolio outcome-summary for the story week once, so the first
    Portfolio a presenter opens is not the cold one. Prints "ready:" only when that request has returned a 2xx
    status (WALK1-2 L-B); any other status prints "prewarm returned {status}", and a request that never returns
    prints a warning; neither prints a "ready:" line."""
    import urllib.error
    import urllib.request

    url = f"http://127.0.0.1:{port}/api/estate/outcome-summary?{story_week_query(story)}"
    if fetch is None:
        def fetch(target: str) -> int:
            try:
                with urllib.request.urlopen(target, timeout=PREWARM_TIMEOUT_SECONDS) as response:
                    response.read()
                    return response.status
            except urllib.error.HTTPError as error:
                return error.code
    say("Pre-warming the Portfolio for the story week (outcome summary, once); wait for the ready: line.")
    started = clock()
    try:
        status = fetch(url)
    except Exception as error:  # noqa: BLE001 - any transport failure means "not warmed"
        say(f"pre-warm did not finish ({type(error).__name__}: {error}); open the Portfolio week link and wait until "
            "the outcome matrix fills before the client joins.")
        return False
    if not 200 <= int(status) < 300:
        say(f"prewarm returned {status}; open the Portfolio week link and wait until the outcome matrix fills "
            "before the client joins.")
        return False
    say(f"ready: Portfolio outcome summary for the story week answered HTTP {status} in {clock() - started:.0f} s. "
        "Do not restart serve once the client has joined.")
    return True


def story_links(story: dict, days: list[dict], kobo: dict | None, web: int) -> list[tuple[str, str]]:
    """The walkthrough links (POLISH §4, Addendum 9 Q3): week and month lists around S, one board per story day (Kobo
    by `date`; cold and EV on the day's event window from `days.json`, or the whole calendar day when the day has
    no event), the Kobo Overview on S, and the Kobo Action's verification and Finding when `kobo.json` exists."""
    S = at(story["S"])
    base = f"http://localhost:{web}"
    week = story_week_query(story)
    month = f"from={iso(S - timedelta(days=28))}&to={iso(S + timedelta(days=3))}"
    rows = [("Portfolio, week to story day S", f"{base}/portfolio?{week}"),
            ("Findings, week to story day S", f"{base}/findings?{week}"),
            ("Maintenance, Preventive, month to S+3d", f"{base}/maintenance/preventive?{month}"),
            ("Maintenance, month to S+3d", f"{base}/maintenance?{month}")]
    for site in story["sites"]:
        code = SITE_CODE[site]
        for d in sorted((d for d in days if d["site"] == site), key=lambda d: d["offset"]):
            label = f"{code} board, {d['kind']} day S{d['offset']:+d}d ({d['day']})"
            if site == "kobo":
                rows.append((label, f"{base}/sites/{code}?date={d['day']}"))
                continue
            start, end = d.get("start"), d.get("end")
            if not start or not end:
                day = datetime.fromisoformat(d["day"]).replace(tzinfo=timezone.utc)
                start, end = iso(day), iso(day + timedelta(days=1))
                label += ", no event: whole day"
            path = f"/sites/{code}/ev" if site == "ev" else f"/sites/{code}"
            rows.append((label, f"{base}{path}?from={start}&to={end}"))
    if kobo is not None:
        rows += [("KOBO-001 Overview, day S", f"{base}/sites/KOBO-001?date={story['S_date']}"),
                 (f"Action {kobo.get('action_code')} verification",
                  f"{base}/sites/KOBO-001/actions/{kobo['action']}/verification"),
                 ("Finding", f"{base}/sites/KOBO-001/findings/{kobo['finding']}?revision_id={kobo['finding_revision']}")]
    return rows


class Demo:
    def __init__(self, db: str, work: str) -> None:
        if not DB_RE.fullmatch(db):
            raise SystemExit(f"Refused: --db {db!r} must match {DB_RE.pattern}")
        path = (REPO / work).resolve() if not Path(work).is_absolute() else Path(work).resolve()
        if path.parent != (REPO / "var").resolve() or not path.name.startswith(WORK_PREFIXES):
            raise SystemExit(f"Refused: --work {path} must be a var/demo3* or var/polish* folder directly under "
                             f"{REPO / 'var'}")
        self.db, self.work, self.tree = db, path, path / "tree"
        self.url = f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{db}"
        self.deadline: float | None = None
        self.started: list[int] = []
        self.holds_busy = False

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

    def serve_env(self) -> dict[str, str]:
        """CH5c-R6: the one environment of the serve child AND the tick child, so the tick's pre-built rows carry
        the server's `code_version` (the cursor keys are hashed into it). Clone settles stay keyless
        (`chain_clone.settle_env`): they are never served."""
        return self.env(keys=True)

    def py(self, *argv: str, cwd: Path | None = None, check: bool = True, label: str = "",
           serve_env: bool = False) -> subprocess.CompletedProcess:
        """One child in the tree, bounded by the wall cap; on the cap it kills only that child's process tree."""
        logs = self.work / "logs"
        logs.mkdir(exist_ok=True)
        name = label or argv[0].split("/")[-1].split("\\")[-1]
        log_path = logs / f"{len(list(logs.iterdir())):02d}-{re.sub(r'[^a-z0-9_.-]', '_', name.lower())[:40]}.log"
        with open(log_path, "w", encoding="utf-8") as log:
            proc = subprocess.Popen([str(PY), *argv], cwd=str(cwd or self.tree), env=self.serve_env() if serve_env else self.env(), stdout=log,
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
    def prepare(self, sites: tuple[str, ...] = SITES, finish: bool = True, days_file: str | None = None,
                baseline: str = "b22") -> dict:
        import psycopg

        days_path = Path(days_file).resolve() if days_file else sd.DEFAULT_FILE
        days_doc = sd.load(days_path)
        expected = {**EXPECTED_SECONDS, "kobo": kobo_expected_seconds(days_doc)}
        cap = 2 * (expected["tree"] + sum(expected[s] for s in sites) + (expected["finish"] if finish else 0))
        self.deadline = time.monotonic() + cap
        began = time.monotonic()
        if (self.work / ".busy").exists():
            raise SystemExit(f"Refused: another prepare/add-day holds {self.work / '.busy'}")
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
        (self.work / ".busy").write_text(f"prepare pid={os.getpid()}\n", encoding="utf-8")
        self.holds_busy = True
        self.tree.mkdir()
        parts = ("backend", "gateway", "host", "simulator", "contracts", "config", "contract-fixtures", "tools")
        archive = subprocess.run(["git", "archive", "--format=tar", "HEAD", *parts], cwd=REPO, capture_output=True,
                                 check=False) if shutil.which("git") else None
        if archive is not None and archive.returncode == 0:
            with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
                tar.extractall(self.tree, filter="data")
        else:  # no git here (the test container mounts the worktree without its .git): copy the checked-out files
            skip = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "node_modules")
            for part in parts:
                shutil.copytree(REPO / part, self.tree / part, ignore=skip)
        (self.tree / "var" / "sites").mkdir(parents=True)
        shutil.copy2(self.tree / "backend" / "tests" / "fixtures" / "s1" / "kobo-001.yaml",
                     self.tree / "var" / "sites" / "kobo-001.yaml")
        head = (subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True)
                if shutil.which("git") else subprocess.CompletedProcess([], 0, stdout="checked-out-copy"))
        if days_file is None:
            shipped = self.tree / sd.DEFAULT_FILE.relative_to(REPO)
            if not shipped.is_file() or sd.load(shipped) != days_doc:
                raise SystemExit(f"Refused: {sd.DEFAULT_FILE.relative_to(REPO)} differs from HEAD; commit it first")
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
        days_doc = sd.apply_baseline(days_doc, story_day(db_now), baseline)  # DD1a2-R Q6
        for site, missing in sd.uncovered_weekdays(days_doc, story_day(db_now), baseline).items():
            if missing:
                say(f"  {SITE_CODE[site]}: ruled days in the {baseline} baseline with no entry (reported, not moved): "
                    f"{', '.join(missing)}")
        story = resolve_story(db_now, days_doc=days_doc)
        days = story.pop("days")
        (self.work / "days.json").write_text(json.dumps(
            {"schema": days_doc["schema"], "source": str(days_path), "S": story["S"], "trial": days_doc["trial"],
             "days": days, "doc": days_doc}, indent=2), encoding="utf-8")
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
        if "kobo" in story["sites"]:
            self.drain_mini()
        self.tick(times=2)
        if set(story["sites"]) == set(SITES):
            done = self.py(str(self.tree / "tools" / "demo_combined_finish.py"), "check", self.url, str(self.work),
                           cwd=self.tree / "backend" / "tests", label="self-check", check=False)
            tail = done.stdout.strip().splitlines()
            say("  " + (tail or ["(no output)"])[-1])
            if done.returncode != 0:
                raise SystemExit(f"SELF-CHECK FAILED; see {self.work / 'check.json'}")

    def drain_mini(self, limit: int = 500) -> None:
        """WALK1-4 F2: the Kobo mini-depth jobs (roles-4 from commissioning) number in the hundreds and the tick's mini
        stage takes at most 10 per Site, so prepare drains them with the worker's own CLI until a pass leaves none due."""
        total = 0
        while True:
            done = self.py("-m", "assetops_backend.mini_depth.worker", "run-pending", "--limit", str(limit),
                           label="mini-depth")
            line = [x for x in done.stdout.splitlines() if x.startswith("[")]
            outcomes = json.loads(line[-1]) if line else []
            failed = [o for o in outcomes if o.get("status") == "FAILED"]
            if failed:
                raise SystemExit(f"mini-depth FAILED: {failed[:3]}")
            total += len(outcomes)
            if len(outcomes) < limit:
                break
        say(f"  mini-depth: {total} jobs processed")

    def tick(self, times: int = 1) -> None:
        """CH5c-R7 F5: the tick without its pre-build stage, then the Performance comparison (a new report moves
        `F`), then the pre-build alone in the serve env, so the next request after a loop tick is a hit."""
        for _ in range(times):
            done = self.py(*TICK, "--no-prebuild", label="tick", check=False, serve_env=True)
            say("  tick: " + (done.stdout.strip().splitlines() or ["(no output)"])[-1][:160])
        for site in ("KOBO-001",):
            done = self.py("-m", "assetops_backend.performance_migration", "run", "--tenant", "demo", "--site", site,
                           label="performance", check=False)
            say("  performance: " + (done.stdout.strip().splitlines() or ["(no output)"])[-1][:160])
        done = self.py("-m", "assetops_backend.scheduling.run", "prebuild", label="prebuild", check=False,
                       serve_env=True)
        say("  prebuild: " + (done.stdout.strip().splitlines() or ["(no output)"])[-1][:160])

    # ---- add-day (DEMO-SPARSE U4) -----------------------------------------------------------------------------
    def delivered_days(self, site_code: str) -> set[str]:
        """UTC days holding delivered (accepted) evidence for the Site: the append-only refusal basis."""
        import psycopg

        with psycopg.connect(PG_ADMIN.rsplit("/", 1)[0] + "/" + self.db, autocommit=True) as c:
            rows = c.execute(
                "SELECT DISTINCT to_char(e.source_time AT TIME ZONE 'UTC', 'YYYY-MM-DD') FROM accepted_evidence e "
                "JOIN ingestion_disposition d ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
                "JOIN site s ON s.id = e.site_id WHERE s.site_code = %s", (site_code,)).fetchall()
        return {r[0] for r in rows}

    def db_now(self) -> datetime:
        import psycopg

        with psycopg.connect(PG_ADMIN.rsplit("/", 1)[0] + "/" + self.db, autocommit=True) as c:
            return c.execute("SELECT clock_timestamp()").fetchone()[0]

    def add_day(self, site_code: str, kind: str, day: str | None = None, as_kind: str | None = None,
                assess_now: bool = False) -> dict:
        """Append one story day, live on real time (sheet U4). Refuses with a `StoryDaysError` code."""
        story = self.story()
        site = sd.CODE_SITE.get(site_code)
        if site is None:
            raise sd.StoryDaysError("UNKNOWN_KIND", f"--site must be one of {sorted(sd.CODE_SITE)}")
        if assess_now and kind == "late":
            raise sd.StoryDaysError("UNKNOWN_KIND", "--assess-now is for non-late kinds; a late day waits for a tick")
        busy = self.work / ".busy"
        try:
            fd = os.open(busy, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise SystemExit(f"Refused: another prepare/add-day holds {busy}")
        try:
            os.write(fd, f"add-day {site_code} {kind} pid={os.getpid()}\n".encode())
            os.close(fd)
            days_path = self.work / "days.json"
            doc = json.loads(days_path.read_text(encoding="utf-8"))
            current = sd.from_payload(doc["days"])
            planned = sd.plan_add_day(doc["doc"], current, site, kind, at(story["S"]), self.db_now(), day=day,
                                      as_kind=as_kind, delivered_days=self.delivered_days(site_code),
                                      installs={n: at(v) for n, v in story["installs"].items()})
            if assess_now and planned.has_run:
                planned = sd.DayRun(**{**planned.__dict__, "assess": "build"})
            out: dict = {"day": planned.day, "kind": planned.kind, "assess": planned.assess}
            if planned.has_run:
                child = self.tree / "tools" / f"demo_combined_{site}.py"
                if site != "kobo" and not child.is_file():
                    raise SystemExit(f"add-day for {site_code} is not built yet")
                self.deadline = time.monotonic() + 2 * 140
                done = self.py(str(child), "add-day", self.url, str(self.work), json.dumps(planned.payload()),
                               cwd=self.tree / "backend" / "tests", label=f"add-day-{site}")
                line = [x for x in done.stdout.splitlines() if x.startswith('{"added"')]
                out.update(json.loads(line[-1]) if line else {})
                if site == "kobo" and planned.assess == "build":
                    self.drain_mini()
            doc["days"].append(planned.payload())
            days_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
            say(f"added {site_code} {planned.day} {planned.kind}" +
                ("" if not planned.has_run else
                 " (assessed now)" if planned.assess == "build" else " (not checked yet: the next serve tick assesses it)"))
            return out
        finally:
            busy.unlink(missing_ok=True)

    def next_free_days(self) -> list[str]:
        story, doc = self.story(), json.loads((self.work / "days.json").read_text(encoding="utf-8"))
        current = sd.from_payload(doc["days"])
        lines = []
        for site in story["sites"]:
            mine = [r.offset for r in current if r.site == site]
            nxt = (max(mine) + 1) if mine else 0
            lines.append(f"python tools/demo_combined.py --db {self.db} --work {self.work.relative_to(REPO).as_posix()} "
                         f"add-day --site {SITE_CODE[site]} --kind normal --day S{nxt:+d}d")
        return lines

    # ---- reading -----------------------------------------------------------------------------------------------
    def links(self, web: int) -> None:
        story = self.story()
        days_file = self.work / "days.json"
        story_days = json.loads(days_file.read_text(encoding="utf-8"))["days"] if days_file.is_file() else []
        kobo = self.work / "kobo.json"
        k = json.loads(kobo.read_text(encoding="utf-8")) if kobo.is_file() else None
        rows = story_links(story, story_days, k, web)
        say(f"Story day S = {story['S_date']} (dates move on every rebuild; quote them from here). Code {story['code']}.")
        for label, url in rows:
            say(f"  {label}\n    {url}")
        days_path = self.work / "days.json"
        if days_path.is_file():
            say("Story days (kind per day; missing = no run, no delivery):")
            current = sd.from_payload(json.loads(days_path.read_text(encoding="utf-8"))["days"])
            for site in story["sites"]:
                cells = [f"{r.day} S{r.offset:+d}d {r.kind}" + (f" (as {r.as_kind})" if r.as_kind else "")
                         for r in sorted((r for r in current if r.site == site), key=lambda r: r.offset)]
                say(f"  {SITE_CODE[site]}: " + "; ".join(cells))

    def serve(self, port: int, web: int) -> None:
        self.story()
        logs = self.work / "logs"
        logs.mkdir(exist_ok=True)
        log = open(logs / f"api-{port}.log", "w", encoding="utf-8")
        api = subprocess.Popen([str(PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(port)],
                               cwd=str(self.tree / "host"), env=self.serve_env(), stdout=log,
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
        if (self.work / "days.json").is_file():
            say("Add a story day live (it shows as not checked yet until the next tick):")
            for line in self.next_free_days():
                say(f"  {line}")
        try:
            warmed = False
            while api.poll() is None:
                self.tick()
                if not warmed:
                    # Review item 8: after the first tick, warm the story-week Portfolio once before "ready:".
                    warmed = True
                    prewarm(port, self.story())
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
    parser.add_argument("--db", required=True, help="private database, assetops_demo3_<name>_test or assetops_polish_<name>_test")
    parser.add_argument("--work", required=True, help="work folder var/demo3* or var/polish* under this repository")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--sites", default=",".join(SITES), help="development only: a subset of kobo,cold,ev")
    p.add_argument("--no-finish", action="store_true", help="development only: skip objectives/comparisons/ticks")
    p.add_argument("--days", default=None, help="day list (default backend/conversions/demo-story-days-v1.json)")
    p.add_argument("--baseline", default="b22", choices=sorted(sd.BASELINE_FROM),
                   help="b16: the owner's fallback if the rehearsal measures the whole prepare over 3 h")
    lk = sub.add_parser("links")
    lk.add_argument("--web-port", type=int, default=WEB_PORT)
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=API_PORT)
    s.add_argument("--web-port", type=int, default=WEB_PORT)
    sub.add_parser("tick")
    ad = sub.add_parser("add-day")
    ad.add_argument("--site", required=True, choices=sorted(SITE_CODE.values()))
    ad.add_argument("--kind", required=True)
    ad.add_argument("--day", default=None, help="S[+-]Nd; default the day after the Site's last story day")
    ad.add_argument("--as", dest="as_kind", default=None, choices=sd.LATE_AS, help="late Kobo day: the run it carries")
    ad.add_argument("--assess-now", action="store_true", help="non-late kinds: assess and match in process")
    sub.add_parser("drop")
    args = parser.parse_args(argv)
    demo = Demo(args.db, args.work)
    if args.cmd == "prepare":
        sites = tuple(s for s in args.sites.split(",") if s)
        if not set(sites) <= set(SITES):
            raise SystemExit(f"--sites must be a subset of {SITES}")
        try:
            demo.prepare(sites, finish=not args.no_finish, days_file=args.days, baseline=args.baseline)
        finally:
            if demo.holds_busy:
                (demo.work / ".busy").unlink(missing_ok=True)
    elif args.cmd == "links":
        demo.links(args.web_port)
    elif args.cmd == "serve":
        demo.serve(args.port, args.web_port)
    elif args.cmd == "add-day":
        demo.add_day(args.site, args.kind, day=args.day, as_kind=args.as_kind, assess_now=args.assess_now)
    elif args.cmd == "tick":
        demo.story()
        demo.tick()
    else:
        demo.drop()


if __name__ == "__main__":
    main()
