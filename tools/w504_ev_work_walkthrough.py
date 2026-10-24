"""W5-04a V1b: the EV work walkthrough CLI (pre-flight 23, readiness 29/31), modeled on W5-02's cold walkthrough.

    python tools/w504_ev_work_walkthrough.py [--work var/w504a_ev_work] [--tag k1] prepare
    python tools/w504_ev_work_walkthrough.py [--work ...] [--tag ...] serve
    python tools/w504_ev_work_walkthrough.py [--work ...] [--tag ...] attest
    python tools/w504_ev_work_walkthrough.py [--work ...] [--tag ...] drop

- `prepare`: one private `w504a_<mode>_<tag>_test` database per DB mode (never another name), migrated to head with
  the product Alembic config. Per mode a child process (`DATABASE_URL` = that DB) reads `R`, runs the shifted
  private replay (`w504_ev_work_cases.replay_shifted`), reads K0 through the public EV routes (readiness 29), then
  posts through the public domain-work routes: `positive` and `zero` each get the positive Action ('Investigate
  connector 2' / 'Charging operations' / due null) and its intent (returned Finding revision, sorted selected
  session IDs, sorted accepted evidence IDs, null case/record); `zero` never gets an INC or WR and both W4 case
  reads must be complete zero. `pending`/`stale`/`unknown` are isolated DBs, recorded only if the merged selector
  returns that state, otherwise `unavailable` in the manifest.
- `serve`: one uvicorn API per DB mode with a ready fixture, plus `forbidden` (positive DB, a principal granted no
  Site: real 403) and `unavailable` (positive DB; `attest` stops only this recorded PID for the 503 capture).
- `attest`: on `positive`, the separate SERVICE-attested INC and WR (+ its record) with the returned EV connector
  asset, then explicit domain Action case links; K3 per case, K4 per link, all from returned `recorded_at`.
- `drop`: stops only recorded PIDs (`taskkill /PID <pid> /T /F`, never `/IM`), drops only marker-listed
  `w504a_*_test` databases, removes the work folder.

Manifest: `<work>/manifest.json` with every ID, clock (R, D, K0-K4 and the evidence clock per record clock), selector
argument and status. Nothing imports `backend/tests`. On merged code the replay is blocked (questions Q8-Q10), so
`prepare` records `blocked` with the reason and exits 3 without inventing a fixture.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import w504_ev_work_cases as P  # noqa: E402

PY = Path(sys.executable)
PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
PG_ADMIN = f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops"
MARKER = ".w504a-walkthrough-work"
SCHEMA = "w504a-ev-work-walkthrough-1"
FIXTURE_MODES = ("positive", "zero")
STATE_MODES = tuple(P.ISOLATED_STATES)
DB_MODES = FIXTURE_MODES + STATE_MODES
PORTS = {"positive": 8981, "zero": 8982, "pending": 8983, "stale": 8984, "unknown": 8985, "forbidden": 8986,
         "unavailable": 8987}
PRINCIPAL = "service:w401-fixture"
BLOCKED = 3
DB_NAME = re.compile(r"w504a_[a-z]+_[a-z0-9]+_test")


def say(text: str = "") -> None:
    print(text, flush=True)


def now_text() -> str:
    return P.iso(datetime.now(timezone.utc))


# ---- child side (runs with DATABASE_URL = one private *_test DB) ----------------------------------------------


def _clients(url: str):
    """In-process public routes over the product app: domain-work writes with the server SERVICE principal, plus a
    W4 Site work router with the same principal for the INC/WR commands (the product app mounts W4 writes as 403)."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from assetops_backend import main as M
    from assetops_backend.config import load_feature_flags
    from assetops_backend.sites.cutover import ImportedSiteRegistry
    from assetops_backend.sites.foundation_service import FoundationService
    from assetops_backend.work.composition import build_work_index_service, build_work_service
    from assetops_backend.work_api import W401_FIXTURE_SERVICE_PRINCIPAL_ID, build_work_router

    app = M.create_app(load_feature_flags(), domain_work_principal=lambda r, c: W401_FIXTURE_SERVICE_PRINCIPAL_ID)
    registry = ImportedSiteRegistry(FoundationService(M.build_foundation_store(url), M.DEVELOPMENT_TENANT_SLUG,
                                                      M.utc_now))
    cases = FastAPI()
    cases.include_router(build_work_router(build_work_service(url), registry.ledger_scope, (M.WORK_UNAVAILABLE,),
                                           principal=lambda r, c: W401_FIXTURE_SERVICE_PRINCIPAL_ID,
                                           lists=build_work_index_service(url)))
    return TestClient(app), TestClient(cases)


def _ok(response, *statuses: int) -> dict:
    if response.status_code not in (statuses or (200, 201)):
        raise P.ProducerRefused(f"{response.request.method} {response.request.url.path} answered "
                                f"{response.status_code}: {response.text[:400]}")
    return response.json()


def _recorded(body: dict, *path: str) -> str:
    value = body
    for key in path:
        value = value.get(key) if isinstance(value, dict) else None
    if not isinstance(value, str):
        raise P.ProducerRefused(f"the response has no {'.'.join(path)} clock: {json.dumps(body)[:300]}")
    return value


def _db_now(url: str) -> datetime:
    from sqlalchemy import create_engine, text

    engine = create_engine(url)
    try:
        with engine.connect() as c:
            return c.execute(text("SELECT clock_timestamp()")).scalar_one()
    finally:
        engine.dispose()


def _declare(url: str, mode: str, tag: str, replayed: dict, db_now: datetime) -> dict:
    """K0 through the public reads, then the positive Action and intent through the public domain-work routes."""
    app, cases = _clients(url)
    code = replayed["site_code"]
    lo, hi = P.shifted_window(db_now)
    selected = P.read_k0(lambda path, params: (lambda r: (r.status_code, r.json()))(app.get(path, params=params)),
                         code, lo, hi)
    base = f"/api/sites/{code}/domain-work/actions"
    raised = selected.k0 + (_db_now(url) - selected.k0) / 2
    action = _ok(app.post(base, json=P.action_body(selected, raised, f"w504a-{mode}-action-{tag}")), 201)
    intent = _ok(app.post(f"{base}/{action['id']}/intents", json=P.intent_body(
        selected, selected.finding_revision_id, _db_now(url), f"w504a-{mode}-intent-{tag}")), 201)
    detail = _ok(app.get(f"/api/sites/{code}/domain-work/actions/{action['id']}"), 200)
    reads = {}
    if mode == "zero":
        bounds = {"from": P.text_of(lo), "to": P.text_of(hi), "limit": 5}
        for kind in ("incidents", "maintenance"):
            reads[kind] = _ok(app.get(f"/api/sites/{code}/work/{kind}", params=bounds), 200)
        if not P.zero_reads_complete(reads["incidents"], reads["maintenance"]):
            raise P.ProducerRefused("mock-zero: a W4 case read is not complete zero")
    k1, k2 = _recorded(action, "recorded_at"), _recorded(intent, "recorded_at")
    return {"mode": mode, "status": "ready", "site_code": code, "tenant_id": replayed.get("tenant_id"),
            "site_id": replayed.get("site_id"), "R": P.iso(db_now), "D": P.iso(P.day_d(db_now)),
            "selection": selected.manifest(), "action": action, "intent": intent, "detail_status": detail.get("status"),
            "clocks": {"K0": P.iso(selected.k0), "K1": k1, "K2": k2,
                       "evidence_clock": {"K1": P.iso(P.evidence_clock_for(P.instant(k1), [selected.k0])),
                                          "K2": P.iso(P.evidence_clock_for(P.instant(k2), [selected.k0]))}},
            "selector_arguments": {"from": P.text_of(lo), "to": P.text_of(hi), "known_at": None,
                                   "findings_known_at": selected.findings_window.get("known_at")},
            "short_name": P.SHORT_NAME, "zero_reads": reads}


def _attest(url: str, tag: str, built: dict) -> dict:
    """Submitted-case mode on `positive`: INC and WR (+ record), then explicit domain Action case links."""
    from sqlalchemy import create_engine, text

    app, cases = _clients(url)
    code, aid = built["site_code"], built["action"]["id"]
    asset = built["selection"]["connector_asset_id"]
    if not asset:
        raise P.ProducerRefused("the selected session returned no EV connector asset ID")
    times = P.submitted_case_times(P.instant(built["selection"]["from"]))
    route = f"/api/sites/{code}/work/cases"
    inc = _ok(cases.post(route, json=P.incident_body(asset, times["incident"], f"w504a-inc-{tag}")), 201)
    wr = _ok(cases.post(route, json=P.request_body(asset, times["request"], f"w504a-wr-{tag}")), 201)
    rec = _ok(cases.post(f"{route}/{wr['id']}/records", json=P.record_body(times["record"], f"w504a-rec-{tag}")),
              201)
    engine = create_engine(url)
    links = {}
    try:
        for key, case in (("incident", inc), ("request", wr)):
            with engine.connect() as c:  # the case's latest W4 event (read-only lineage, as W5-02's walkthrough)
                event = str(c.execute(text("SELECT id FROM work_event WHERE case_id = :c ORDER BY recorded_at DESC, "
                                           "id DESC LIMIT 1"), {"c": case["id"]}).scalar_one())
            links[key] = _ok(app.post(f"/api/sites/{code}/domain-work/actions/{aid}/case-links",
                                      json=P.case_link_body(case, event, f"w504a-link-{key}-{tag}")), 201)
            links[key]["case_event_id"] = event
    finally:
        engine.dispose()
    k3 = {"incident": _recorded(inc, "event", "recorded_at"), "request": _recorded(wr, "event", "recorded_at"),
          "record": _recorded(rec, "recorded_at")}
    k4 = {key: _recorded(link, "recorded_at") for key, link in links.items()}
    k0 = P.instant(built["clocks"]["K0"])
    return {"incident": inc, "request": wr, "record": rec, "links": links, "asset_id": asset,
            "wr_narrative_pending_ruling": P.WR_NARRATIVE_PENDING_RULING,
            "clocks": {"K3": k3, "K4": k4,
                       "evidence_clock": {f"K3.{k}": P.iso(P.evidence_clock_for(P.instant(v), [k0]))
                                          for k, v in k3.items()}
                       | {f"K4.{k}": P.iso(P.evidence_clock_for(P.instant(v), [k0])) for k, v in k4.items()}}}


def child(op: str, mode: str, work: Path, tag: str) -> int:
    url = os.environ["DATABASE_URL"]
    out = work / "build" / f"{mode}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        if op == "prepare":
            db_now = _db_now(url)
            scenario = P.UNKNOWN_SCENARIO if mode == "unknown" else P.POSITIVE_SCENARIO
            try:
                replayed = P.replay_shifted(scenario, db_now, f"{mode[:4]}{tag}".upper()[:12])
            except P.ProducerBlocked as blocked:
                doc = {"mode": mode, "status": "blocked" if mode in FIXTURE_MODES else "unavailable",
                       "reason": str(blocked), "R": P.iso(db_now), "D": P.iso(P.day_d(db_now)),
                       "scenario_id": scenario}
                out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
                return BLOCKED
            if mode in STATE_MODES:
                # Recorded only if the merged selector returns that state (spec "EV producer, UI and registry").
                doc = {"mode": mode, "status": "unavailable", "reason": "selector state check not reached",
                       "wanted_state": P.ISOLATED_STATES[mode]}
            else:
                doc = _declare(url, mode, tag, replayed, db_now)
        else:
            doc = json.loads(out.read_text(encoding="utf-8"))
            doc["submitted"] = _attest(url, tag, doc)
        out.write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
        return 0
    except P.ProducerRefused as refused:
        (work / "build" / f"{mode}.error.txt").write_text(str(refused), encoding="utf-8")
        return 2


# ---- operator side --------------------------------------------------------------------------------------------

SERVE_ENTRY = r'''
"""Tool-local uvicorn entry (tools/w504_ev_work_walkthrough.py serve): the product host app plus, ahead of its
domain-work routes, the same router behind a WorkGate whose access is a server-configured operator grant."""
import json, os
from lab_app import app
from assetops_backend import main as M
from assetops_backend.domain_work_api import build_domain_work_router
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.foundation_service import FoundationService
from assetops_backend.work.composition import (build_domain_action_read_service, build_domain_intent_service,
                                               build_work_index_service)
from assetops_backend.work_api import WorkGate, build_work_router

grant = json.loads(open(os.environ["W504A_PRINCIPAL_FILE"], encoding="utf-8").read())
sites = {c.upper() for c in grant["sites"]}
access = lambda request, code: None if code.upper() in sites else 403
url = M.database_url()
registry = ImportedSiteRegistry(FoundationService(M.build_foundation_store(url), M.DEVELOPMENT_TENANT_SLUG, M.utc_now))
routes = list(build_domain_work_router(
    build_domain_intent_service(url), WorkGate(registry.ledger_scope, (M.WORK_UNAVAILABLE,), access=access,
                                               command_access=access),
    (M.WORK_UNAVAILABLE,), reads=build_domain_action_read_service(url)).routes)
routes += list(build_work_router(None, registry.ledger_scope, (M.WORK_UNAVAILABLE,), access=access,
                                 command_access=access, lists=build_work_index_service(url)).routes)
app.router.routes[0:0] = routes
'''


class Walk:
    def __init__(self, work: str, tag: str) -> None:
        path = (REPO / work).resolve() if not Path(work).is_absolute() else Path(work).resolve()
        if path.parent != (REPO / "var").resolve() or not path.name.startswith("w504a"):
            raise SystemExit(f"Refused: --work {path} must be a var/w504a* folder directly under {REPO / 'var'}")
        if not re.fullmatch(r"[a-z0-9]{1,12}", tag):
            raise SystemExit("Refused: --tag must be 1-12 lower-case letters/digits")
        self.work, self.tag = path, tag
        self.dbs = {m: f"w504a_{m}_{tag}_test" for m in DB_MODES}

    def url(self, mode: str) -> str:
        return f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{self.dbs[mode]}"

    def env(self, db_url: str) -> dict[str, str]:
        out = {k: v for k, v in os.environ.items() if not k.startswith("ASSETOPS_TEST_")}
        parts = [REPO / p for p in ("backend", "gateway", "simulator", "contracts", "host")]
        out["PYTHONPATH"] = os.pathsep.join(str(p) for p in parts)
        out["DATABASE_URL"] = db_url
        out["PYTHONUNBUFFERED"] = "1"
        return out

    def marker(self) -> dict:
        path = self.work / MARKER
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}

    def manifest_path(self) -> Path:
        return self.work / "manifest.json"

    def pids_file(self) -> Path:
        return self.work / "pids.json"

    def _child(self, op: str, mode: str) -> int:
        done = subprocess.run([str(PY), str(Path(__file__).resolve()), "--work", str(self.work), "--tag", self.tag,
                               "_child", op, mode], cwd=str(REPO / "backend"), env=self.env(self.url(mode)),
                              capture_output=True, text=True, timeout=1800)
        if done.returncode not in (0, 2, BLOCKED):
            raise SystemExit(f"FAILED child {op} {mode}\n{done.stdout[-3000:]}\n{done.stderr[-3000:]}")
        return done.returncode

    def prepare(self) -> int:
        import psycopg

        if self.marker():
            raise SystemExit(f"Refused: {self.work} already holds a walkthrough; run drop first")
        self.work.mkdir(parents=True, exist_ok=True)
        (self.work / MARKER).write_text(json.dumps({"tool": "w504a", "dbs": list(self.dbs.values())}),
                                        encoding="utf-8")
        (self.work / "serve_entry.py").write_text(SERVE_ENTRY, encoding="utf-8")
        modes = {}
        for mode, db in self.dbs.items():
            with psycopg.connect(PG_ADMIN, autocommit=True) as c:
                c.execute(f"DROP DATABASE IF EXISTS {db} WITH (FORCE)")
                c.execute(f"CREATE DATABASE {db}")
            migrated = subprocess.run([str(PY), "-m", "alembic", "-c", str(REPO / "backend" / "alembic.ini"),
                                       "upgrade", "head"], cwd=str(REPO / "backend"), env=self.env(self.url(mode)),
                                      capture_output=True, text=True, timeout=600)
            if migrated.returncode != 0:
                raise SystemExit(f"FAILED: alembic upgrade head on {db}\n{migrated.stderr[-3000:]}")
            code = self._child("prepare", mode)
            built = self.work / "build" / f"{mode}.json"
            doc = json.loads(built.read_text(encoding="utf-8")) if built.is_file() else {
                "mode": mode, "status": "refused",
                "reason": (self.work / "build" / f"{mode}.error.txt").read_text(encoding="utf-8")}
            modes[mode] = {**doc, "db": db, "child_exit": code}
            say(f"{mode}: {doc['status']}" + (f" - {doc.get('reason', '')[:200]}" if doc["status"] != "ready" else ""))
        self.write_manifest(modes)
        return 0 if all(modes[m]["status"] == "ready" for m in FIXTURE_MODES) else BLOCKED

    def write_manifest(self, modes: dict, **extra) -> None:
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO), capture_output=True, text=True)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO), capture_output=True, text=True)
        current = json.loads(self.manifest_path().read_text(encoding="utf-8")) if self.manifest_path().is_file() \
            else {}
        current.update({"schema": SCHEMA, "revision": revision.stdout.strip(), "dirty": bool(dirty.stdout.strip()),
                        "work": str(self.work), "principal": PRINCIPAL, "site": {
                            "display_name": P.DISPLAY_NAME, "short_name": P.SHORT_NAME, "timezone": P.TIMEZONE},
                        "modes": modes, "written_at": now_text(), **extra})
        self.manifest_path().write_text(json.dumps(current, indent=2, default=str), encoding="utf-8")

    def serve(self) -> int:
        manifest = json.loads(self.manifest_path().read_text(encoding="utf-8"))
        ready = [m for m, d in manifest["modes"].items() if d["status"] == "ready"]
        if "positive" not in ready:
            raise SystemExit("Refused: no ready positive fixture to serve (see manifest modes)")
        code = manifest["modes"]["positive"]["site_code"]
        plan = {m: (m, [manifest["modes"][m]["site_code"]]) for m in ready}
        plan["forbidden"] = ("positive", [])
        plan["unavailable"] = ("positive", [code])
        pids = json.loads(self.pids_file().read_text(encoding="utf-8")) if self.pids_file().is_file() else {}
        (self.work / "logs").mkdir(exist_ok=True)
        for name, (mode, sites) in plan.items():
            grant = self.work / f"principal-{name}.json"
            grant.write_text(json.dumps({"sites": sites}), encoding="utf-8")
            env = self.env(self.url(mode))
            env["PYTHONPATH"] = os.pathsep.join([str(self.work), env["PYTHONPATH"]])
            env["W504A_PRINCIPAL_FILE"] = str(grant)
            port = PORTS[name]
            log = self.work / "logs" / f"api-{name}-{port}.log"
            with open(log, "w", encoding="utf-8") as sink:
                process = subprocess.Popen(
                    [str(PY), "-m", "uvicorn", "serve_entry:app", "--host", "127.0.0.1", "--port", str(port)],
                    cwd=str(REPO / "host"), env=env, stdout=sink, stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                    | getattr(subprocess, "DETACHED_PROCESS", 0))
            pids[name] = {"pid": process.pid, "port": port, "db": self.dbs[mode], "log": str(log)}
            self.pids_file().write_text(json.dumps(pids, indent=2), encoding="utf-8")
            say(f"{name}: pid {process.pid} port {port} healthy={_wait_health(port)}")
        self.write_manifest(manifest["modes"], processes=pids)
        return 0

    def attest(self) -> int:
        manifest = json.loads(self.manifest_path().read_text(encoding="utf-8"))
        if manifest["modes"].get("positive", {}).get("status") != "ready":
            raise SystemExit("Refused: the positive fixture is not ready")
        code = self._child("attest", "positive")
        built = self.work / "build" / "positive.json"
        if code != 0:
            raise SystemExit((self.work / "build" / "positive.error.txt").read_text(encoding="utf-8"))
        manifest["modes"]["positive"] = {**json.loads(built.read_text(encoding="utf-8")),
                                         "db": self.dbs["positive"], "child_exit": 0}
        pids = json.loads(self.pids_file().read_text(encoding="utf-8")) if self.pids_file().is_file() else {}
        site = manifest["modes"]["positive"]["site_code"]
        vectors = {}
        if "forbidden" in pids:
            status, body = _get_path(pids["forbidden"]["port"], f"/api/sites/{site}/domain-work/action-index")
            vectors["forbidden"] = {"http": status, "code": (body.get("detail") or {}).get("code")}
        if "unavailable" in pids:
            info = pids["unavailable"]
            subprocess.run(["taskkill", "/PID", str(info["pid"]), "/T", "/F"], capture_output=True)
            status, _ = _get_path(info["port"], f"/api/sites/{site}/domain-work/action-index")
            vectors["unavailable"] = {"stopped_pid": info["pid"], "port": info["port"], "http_after_stop": status,
                                      "expected": "connection refused; the browser proxy reports 503"}
        self.write_manifest(manifest["modes"], vectors=vectors)
        say(json.dumps(vectors))
        return 0

    def drop(self) -> int:
        import psycopg

        if self.pids_file().is_file():
            pids = json.loads(self.pids_file().read_text(encoding="utf-8"))
            for name, info in list(pids.items()):
                if _alive(info["pid"]):
                    subprocess.run(["taskkill", "/PID", str(info["pid"]), "/T", "/F"], capture_output=True)
                    say(f"stopped {name} pid {info['pid']}")
                pids.pop(name)
            self.pids_file().write_text(json.dumps(pids), encoding="utf-8")
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            for db in self.marker().get("dbs", []):
                if not DB_NAME.fullmatch(db):
                    say(f"not dropping {db}: not a w504a *_test name")
                    continue
                c.execute(f"DROP DATABASE IF EXISTS {db} WITH (FORCE)")
                say(f"dropped database {db}")
        if self.work.exists() and self.marker():
            shutil.rmtree(self.work)
            say(f"removed {self.work}")
        return 0


def _alive(pid: int) -> bool:
    done = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
    return str(pid) in done.stdout


def _get_path(port: int, path: str) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except ValueError:
            return e.code, {}
    except (urllib.error.URLError, OSError) as e:
        return 0, {"error": str(e)}


def _wait_health(port: int, seconds: int = 90) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if _get_path(port, "/api/health")[0] == 200:
            return True
        time.sleep(1)
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--work", default="var/w504a_ev_work")
    parser.add_argument("--tag", default="k1")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "serve", "attest", "drop"):
        sub.add_parser(name)
    hidden = sub.add_parser("_child")
    hidden.add_argument("op", choices=("prepare", "attest"))
    hidden.add_argument("mode", choices=DB_MODES)
    args = parser.parse_args(argv)
    if args.command == "_child":
        return child(args.op, args.mode, Path(args.work), args.tag)
    walk = Walk(args.work, args.tag)
    return getattr(walk, args.command)()


if __name__ == "__main__":
    raise SystemExit(main())
