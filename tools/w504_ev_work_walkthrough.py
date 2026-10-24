"""W5-04a V1b: the EV work walkthrough CLI (readiness 29, 31, 34-38), modeled on W5-02's cold walkthrough.

    python tools/w504_ev_work_walkthrough.py [--work var/w504a_ev_work] [--tag k1] prepare
    python tools/w504_ev_work_walkthrough.py [--work ...] [--tag ...] serve
    python tools/w504_ev_work_walkthrough.py [--work ...] [--tag ...] attest
    python tools/w504_ev_work_walkthrough.py [--work ...] [--tag ...] drop

- `prepare`: one private `w504a_<mode>_<tag>_test` database per DB mode (`positive`, `zero`, `unknown`; never
  another name), migrated to head with the product Alembic config. Per mode a child process (`DATABASE_URL` and
  `ASSETOPS_TEST_DATABASE_URL` = that DB) installs the registered EV-LAB-001 Foundation and runs the registered
  scenario UNMODIFIED through the registered parser/Host stage/gateway upload/Batch V2 ingestion and the selected
  EV worker (`native_replay`; ruling 36: the only importer of the existing `backend/tests`/`host/tests` helpers),
  then reads K0 over the evidence window E through the public EV routes (readiness 29) and posts the positive Action
  ('Investigate connector 2' / 'Charging operations' / due null, raised at current DB time) and its intent through
  the public domain-work routes. `zero` never gets an INC or WR and both W4 case reads over W are complete zero.
  `unknown` replays `ev-missing-meter` and is recorded only if the merged selector returns UNKNOWN; `pending` and
  `stale` are not produced by an unmodified registered replay and are recorded `unavailable`.
- `serve`: one uvicorn API per ready DB mode, plus `forbidden` (positive DB, a principal granted no Site: real 403)
  and `unavailable` (positive DB; `attest` stops only this recorded PID for the 503 capture).
- `attest`: on `positive`, the separate SERVICE-attested INC and WR (+ its record) at current DB time with the
  returned EV connector asset, then explicit domain Action case links; K3 per case/record, K4 per link, from
  returned `recorded_at`; `K0 < K1 <= K2 <= K3 <= K4` and the Work window W are enforced before capture.
- `drop`: stops only recorded PIDs (`taskkill /PID <pid> /T /F`, never `/IM`), drops only marker-listed
  `w504a_*_test` databases, removes the work folder.

Manifest: `<work>/manifest.json`, with E and W labelled separately, every ID, clock (R, K0-K4 and the evidence clock
per record clock), selector argument and status. `Chain.decision_clock()` is never read as K0.
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
from collections import Counter
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
SCHEMA = "w504a-ev-work-walkthrough-2"
FIXTURE_MODES = ("positive", "zero")
DB_MODES = FIXTURE_MODES + ("unknown",)
#: Not produced by an unmodified registered replay (build spec "EV producer, UI and registry"): pure vectors.
UNPRODUCED = {"pending": "a late accepted event before W5-03 reassessment needs a modified replay",
              "stale": "a superseded source binding before reselection needs a modified replay"}
PORTS = {"positive": 8981, "zero": 8982, "unknown": 8985, "forbidden": 8986, "unavailable": 8987}
PRINCIPAL = "service:w401-fixture"
BLOCKED = 3
DB_NAME = re.compile(r"w504a_[a-z]+_[a-z0-9]+_test")
CASE_OF = {P.POSITIVE_SCENARIO: "interrupted", P.UNKNOWN_SCENARIO: "missing-meter"}


def say(text: str = "") -> None:
    print(text, flush=True)


def now_text() -> str:
    return P.iso(datetime.now(timezone.utc))


# ---- child side (runs with DATABASE_URL = one private *_test DB) ----------------------------------------------


def native_replay(scenario_id: str, tmp: Path, *, fresh: bool = False) -> dict:
    """Ruling 36: the registered, unmodified EV replay of `scenario_id` at EV-LAB-001 over E through the existing
    test-module gateway/central/Chain helpers (the private `*_test` fixture adapter W5-02's cold walkthrough uses).
    This is the walkthrough child's single, explicit test-helper import; the library imports none. Real Host stage,
    gateway subprocess upload, Batch V2 ingestion and the selected EV worker; the gateway is stopped before return.
    Public IDs and clocks are read afterwards from product routes only (never `Chain.decision_clock()`)."""
    for extra in (REPO / "backend" / "tests", REPO / "host", REPO / "host" / "tests", REPO / "gateway" / "tests"):
        if str(extra) not in sys.path:
            sys.path.insert(0, str(extra))
    if not os.environ.get("ASSETOPS_TEST_DATABASE_URL", "").split("?")[0].endswith("_test"):
        raise P.ProducerRefused("the registered replay helpers need ASSETOPS_TEST_DATABASE_URL naming a *_test DB")
    import test_w205b_ev_replay_postgres as registered  # noqa: PLC0415 - ruling 36, child only
    from test_w206_ev_store_postgres import run_worker, select_exact  # noqa: PLC0415 - ruling 36, child only

    case = CASE_OF.get(scenario_id)
    if case is None or case not in registered.CASES:
        raise P.ProducerRefused(f"{scenario_id} is not a registered EV replay case")
    window = (P.instant(registered.WINDOW["start"]), P.instant(registered.WINDOW["end"]))
    if registered.EV != P.SITE_CODE or window != (P.E_START, P.E_END):
        raise P.ProducerRefused(f"the registered replay is {registered.EV} {window}, not {P.SITE_CODE} E")
    built = registered.Chain(case, tmp)
    gateway_pid = None
    try:
        built.open(fresh=fresh)
        gateway_pid = built.process.process.pid
        built.start_release_upload()
        outcomes = run_worker(built)
        select_exact(built, P.E_START, P.E_END)
        decisions = Counter(d[1] for b in built.batches() for d in b["dispositions"])
        if built.site_code != P.SITE_CODE or not decisions.get("ACCEPTED"):
            raise P.ProducerRefused(f"the replay accepted no envelope at {built.site_code}: {dict(decisions)}")
        facts = {"scenario_id": scenario_id, "case": case, "site_code": built.site_code,
                 "tenant_id": str(built.tenant_id), "site_id": str(built.site_id), "run_id": built.run.run_id,
                 "evidence_window": {"from": P.iso(P.E_START), "to": P.iso(P.E_END)},
                 "dispositions": dict(decisions), "worker_outcomes": len(outcomes), "gateway_pid": gateway_pid}
    finally:
        built.close()
    if gateway_pid is not None and built.process.process.poll() is None:
        raise P.ProducerRefused(f"the replay gateway pid {gateway_pid} is still running after close")
    return facts


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


def _getter(client):
    return lambda path, params: (lambda r: (r.status_code, r.json()))(client.get(path, params=params))


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
            return c.execute(text("SELECT clock_timestamp()")).scalar_one().astimezone(timezone.utc)
    finally:
        engine.dispose()


def _bounds(lo: datetime, hi: datetime, **extra) -> dict:
    return {"from": P.text_of(lo), "to": P.text_of(hi), **extra}


def _site_read(app) -> dict:
    """Ruling 38: the stored Site display name and zone, read back (never written by the producer)."""
    response = app.get(f"/api/sites/{P.SITE_CODE}")
    body = response.json() if response.status_code == 200 else {}
    site = body.get("site", body) if isinstance(body, dict) else {}
    return {"code": P.SITE_CODE, "display_name": site.get("display_name") or site.get("name"),
            "timezone": site.get("timezone"), "short_name_manifest_only": P.SHORT_NAME}


def _declare(url: str, mode: str, tag: str, replayed: dict) -> dict:
    """K0 over E through the public reads, then the positive Action (raised at current DB time) and its intent."""
    app, _ = _clients(url)
    code = P.SITE_CODE
    selected = P.read_k0(_getter(app), code, P.E_START, P.E_END)
    base = f"/api/sites/{code}/domain-work/actions"
    now = _db_now(url)
    posted = P.action_body(selected, now, f"w504a-{mode}-action-{tag}", db_now=now)
    action = _ok(app.post(base, json=posted), 201)
    posted_intent = P.intent_body(selected, selected.finding_revision_id, _db_now(url), f"w504a-{mode}-intent-{tag}")
    intent = _ok(app.post(f"{base}/{action['id']}/intents", json=posted_intent), 201)
    detail = _ok(app.get(f"{base}/{action['id']}"), 200)
    shown = detail["action"]
    if (shown["title"], shown["owner_label"], shown["due_at"]) != tuple(P.ACTION.values()) \
            or detail["intent"]["basis"] != posted_intent["basis"]:
        raise P.ProducerRefused("the stored Action/intent read back differs from the posted literals")
    k0, k1, k2 = selected.k0, P.instant(_recorded(action, "recorded_at")), P.instant(_recorded(intent, "recorded_at"))
    order = P.clock_order(k0, k1, k2)
    db_now = _db_now(url)
    work = P.bounded_work_window(db_now, {"K1": k1})
    lo, hi = work["from"], work["to"]
    index = _ok(app.get(f"/api/sites/{code}/domain-work/action-index", params=_bounds(lo, hi, limit=5)), 200)
    if action["id"].lower() not in P.listed_ids(index, "action_id"):
        raise P.ProducerRefused("the Action is not listed in the domain-work index over W")
    reads = {}
    if mode == "zero":
        for kind in ("incidents", "maintenance"):
            reads[kind] = _ok(app.get(f"/api/sites/{code}/work/{kind}", params=_bounds(lo, hi, limit=5)), 200)
        if not P.zero_reads_complete(reads["incidents"], reads["maintenance"]):
            raise P.ProducerRefused("mock-zero: a W4 case read over W is not complete zero")
    return {"mode": mode, "status": "ready", "site": _site_read(app), "replay": replayed, "R": P.iso(db_now),
            "evidence_window_E": {"from": P.iso(P.E_START), "to": P.iso(P.E_END),
                                  "use": "immutable EV Finding/intent basis and K0 reads only"},
            "work_window_W": {"from": P.iso(lo), "to": P.iso(hi), "recomputed": work["recomputed"],
                              "contains": work["contains"],
                              "use": "Actions, Incidents and Maintenance tabs and the Action detail URL"},
            "selection": selected.manifest(), "action_posted": posted, "action": action,
            "intent_posted": posted_intent, "intent": intent, "detail_status": detail.get("status"),
            "detail_known_at": detail.get("known_at"), "index_known_at": index.get("known_at"),
            "work_urls": _work_urls(code, action["id"], lo, hi),
            "clocks": {"K0": P.iso(k0), "K1": P.iso(k1), "K2": P.iso(k2), "order": order,
                       "evidence_clock": {"K1": P.iso(P.evidence_clock_for(k1, [k0])),
                                          "K2": P.iso(P.evidence_clock_for(k2, [k0]))}},
            "selector_arguments": {"E": _bounds(P.E_START, P.E_END, known_at=None),
                                   "findings_known_at": selected.findings_window.get("known_at"),
                                   "W": _bounds(lo, hi)},
            "zero_reads": reads}


def _work_urls(code: str, action_id: str, lo: datetime, hi: datetime) -> dict:
    query = urllib.parse.urlencode(_bounds(lo, hi))
    return {"actions": f"/sites/{code}/work?{query}", "incidents": f"/sites/{code}/work/incidents?{query}",
            "maintenance": f"/sites/{code}/work/maintenance?{query}",
            "action_detail": f"/sites/{code}/actions/{action_id}/verification?{query}"}


def _unknown(url: str, tag: str, replayed: dict) -> dict:
    """Ruling 34: `ev-missing-meter` is recorded only if it yields the exact selected UNKNOWN state."""
    app, _ = _clients(url)
    code = P.SITE_CODE
    get = _getter(app)
    bounds = _bounds(P.E_START, P.E_END)
    status, scenarios = get(f"/api/sites/{code}/ev/financials/scenarios", bounds)
    status2, sessions = get(f"/api/sites/{code}/ev/sessions", bounds)
    if status != 200 or status2 != 200:
        return {"status": "unavailable", "reason": f"EV reads answered {status}/{status2}", "replay": replayed}
    k0 = P.cross_check_k0(scenarios, sessions, P.E_START, P.E_END)
    status, findings = get(f"/api/sites/{code}/ev/findings",
                           {**bounds, "known_at": str(scenarios["window"]["committed_watermark"])})
    supported = [f for f in (findings.get("items") or []) if f.get("lifecycle") == "SUPPORTED"] if status == 200 else []
    base = {"mode": "unknown", "replay": replayed, "K0": P.iso(k0), "wanted_state": P.ISOLATED_STATES["unknown"],
            "sessions": [{k: s.get(k) for k in ("session_id", "state", "connector_asset_id")}
                         for s in sessions.get("items") or []]}
    if len(supported) != 1:
        return {**base, "status": "unavailable",
                "reason": f"the replay selected {len(supported)} SUPPORTED EV Findings, so no Action detail state"}
    finding = supported[0]
    now = _db_now(url)
    body = {"domain": P.SITE_TYPE, "origin_finding_id": str(finding["finding_id"]),
            "origin_finding_revision_id": str(finding["revision_id"]), **P.ACTION, "raised_at": P.iso(now),
            "actor": dict(P.SERVICE_ACTOR), "idempotency_key": f"w504a-unknown-action-{tag}"}
    action = _ok(app.post(f"/api/sites/{code}/domain-work/actions", json=body), 201)
    detail = _ok(app.get(f"/api/sites/{code}/domain-work/actions/{action['id']}"), 200)
    if detail.get("status") != P.ISOLATED_STATES["unknown"]:
        return {**base, "status": "unavailable", "action": action, "returned_state": detail.get("status"),
                "reason": "the merged selector did not return UNKNOWN for this replay"}
    return {**base, "status": "ready", "action": action, "returned_state": detail.get("status")}


def _attest(url: str, tag: str, built: dict) -> dict:
    """Submitted-case mode on `positive`: INC and WR (+ record) at current DB time, explicit case links, then the
    clock order and the Work window W are enforced and every row is asserted in the W lists."""
    from sqlalchemy import create_engine, text

    app, cases = _clients(url)
    code, aid = P.SITE_CODE, built["action"]["id"]
    asset = built["selection"]["connector_asset_id"]
    if not asset:
        raise P.ProducerRefused("the selected session returned no EV connector asset ID")
    times = P.submitted_case_times(_db_now(url))
    route = f"/api/sites/{code}/work/cases"
    posted = {"incident": P.incident_body(asset, times["incident"], f"w504a-inc-{tag}"),
              "request": P.request_body(asset, times["request"], f"w504a-wr-{tag}"),
              "record": P.record_body(times["record"], f"w504a-rec-{tag}")}
    inc = _ok(cases.post(route, json=posted["incident"]), 201)
    wr = _ok(cases.post(route, json=posted["request"]), 201)
    rec = _ok(cases.post(f"{route}/{wr['id']}/records", json=posted["record"]), 201)
    engine = create_engine(url)
    links = {}
    try:
        with engine.connect() as c:  # read-only lineage, as W5-02's walkthrough
            created = {str(r[0]): r[1] for r in c.execute(text(
                "SELECT CAST(id AS text), created_at FROM work_case WHERE id IN (:a, :b)"),
                {"a": inc["id"], "b": wr["id"]})}
            narrative = c.execute(text("SELECT narrative FROM work_case_revision WHERE id = :r"),
                                  {"r": wr["revision"]["id"]}).scalar_one()
        if narrative != P.WORK_REQUEST["narrative"] or posted["request"]["narrative"] != P.WORK_REQUEST["narrative"]:
            raise P.ProducerRefused(f"the WR narrative posted/returned is not the ruling-37 literal: {narrative!r}")
        for key, case in (("incident", inc), ("request", wr)):
            with engine.connect() as c:
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
    clocks = built["clocks"]
    k0, k1, k2 = (P.instant(clocks[k]) for k in ("K0", "K1", "K2"))
    order = P.clock_order(k0, k1, k2, [P.instant(v) for v in k3.values()], [P.instant(v) for v in k4.values()])
    db_now = _db_now(url)
    work = P.bounded_work_window(db_now, {"K1": k1, "incident.occurred_at": times["incident"],
                                          "maintenance.created_at": created[wr["id"]].astimezone(timezone.utc)})
    lo, hi = work["from"], work["to"]
    lists = {"actions": _ok(app.get(f"/api/sites/{code}/domain-work/action-index", params=_bounds(lo, hi, limit=5)),
                            200),
             "incidents": _ok(app.get(f"/api/sites/{code}/work/incidents", params=_bounds(lo, hi, limit=5)), 200),
             "maintenance": _ok(app.get(f"/api/sites/{code}/work/maintenance", params=_bounds(lo, hi, limit=5)), 200)}
    wanted = {"actions": ("action_id", aid), "incidents": ("case_id", inc["id"]), "maintenance": ("case_id", wr["id"])}
    for tab, (key, ident) in wanted.items():
        if ident.lower() not in P.listed_ids(lists[tab], key):
            raise P.ProducerRefused(f"{ident} is not listed in the {tab} read over W {P.iso(lo)}..{P.iso(hi)}")
    return {"incident": inc, "request": wr, "record": rec, "links": links, "asset_id": asset, "posted": posted,
            "wr_narrative": narrative,
            "work_window_W": {"from": P.iso(lo), "to": P.iso(hi), "recomputed": work["recomputed"],
                              "contains": work["contains"], "R": P.iso(db_now)},
            "work_urls": _work_urls(code, aid, lo, hi),
            "list_known_at": {tab: body.get("known_at") for tab, body in lists.items()},
            "clocks": {"K3": k3, "K4": k4, "order": order,
                       "evidence_clock": {f"K3.{k}": P.iso(P.evidence_clock_for(P.instant(v), [k0]))
                                          for k, v in k3.items()}
                       | {f"K4.{k}": P.iso(P.evidence_clock_for(P.instant(v), [k0])) for k, v in k4.items()}}}


def child(op: str, mode: str, work: Path, tag: str) -> int:
    url = os.environ["DATABASE_URL"]
    out = work / "build" / f"{mode}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        if op == "prepare":
            scenario = P.UNKNOWN_SCENARIO if mode == "unknown" else P.POSITIVE_SCENARIO
            replayed = native_replay(scenario, work / "chain" / mode)
            doc = _unknown(url, tag, replayed) if mode == "unknown" else _declare(url, mode, tag, replayed)
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

    def env(self, db_url: str, *, replay: bool = False) -> dict[str, str]:
        """The child environment: product `DATABASE_URL`; for the replay child also `ASSETOPS_TEST_DATABASE_URL`
        naming the same private `*_test` DB (the registered replay helpers read it, ruling 36)."""
        out = {k: v for k, v in os.environ.items() if not k.startswith("ASSETOPS_TEST_")}
        if replay:
            out["ASSETOPS_TEST_DATABASE_URL"] = db_url
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
        argv = [str(PY), str(Path(__file__).resolve()), "--work", str(self.work), "--tag", self.tag, "_child", op, mode]
        done = subprocess.run(argv, cwd=str(REPO / "backend"), env=self.env(self.url(mode), replay=True),
                              capture_output=True, text=True, timeout=1800)
        (self.work / "logs").mkdir(parents=True, exist_ok=True)
        (self.work / "logs" / f"child-{op}-{mode}.log").write_text(done.stdout + "\n" + done.stderr,
                                                                    encoding="utf-8")
        if done.returncode not in (0, 2):
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
        for mode, reason in UNPRODUCED.items():
            modes[mode] = {"mode": mode, "status": "unavailable", "wanted_state": P.ISOLATED_STATES[mode],
                           "reason": reason + "; use the pure adapter/component vector", "db": None}
            say(f"{mode}: unavailable - {reason}")
        self.write_manifest(modes)
        return 0 if all(modes[m]["status"] == "ready" for m in FIXTURE_MODES) else BLOCKED

    def write_manifest(self, modes: dict, **extra) -> None:
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO), capture_output=True, text=True)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO), capture_output=True, text=True)
        current = json.loads(self.manifest_path().read_text(encoding="utf-8")) if self.manifest_path().is_file() \
            else {}
        current.update({"schema": SCHEMA, "revision": revision.stdout.strip(), "dirty": bool(dirty.stdout.strip()),
                        "work": str(self.work), "principal": PRINCIPAL, "site": {
                            "code": P.SITE_CODE, "short_name_manifest_only": P.SHORT_NAME, "timezone": P.TIMEZONE},
                        "windows": {"E": {"from": P.iso(P.E_START), "to": P.iso(P.E_END),
                                          "use": "evidence basis and K0 reads only"},
                                    "W": "per mode work_window_W (current DB day); Work tabs and Action detail URL"},
                        "modes": modes, "written_at": now_text(), **extra})
        self.manifest_path().write_text(json.dumps(current, indent=2, default=str), encoding="utf-8")

    def serve(self) -> int:
        manifest = json.loads(self.manifest_path().read_text(encoding="utf-8"))
        ready = [m for m, d in manifest["modes"].items() if d["status"] == "ready"]
        if "positive" not in ready:
            raise SystemExit("Refused: no ready positive fixture to serve (see manifest modes)")
        code = P.SITE_CODE
        plan = {m: (m, [code]) for m in ready if m in self.dbs}
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
        site = P.SITE_CODE
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
