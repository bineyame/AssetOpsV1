"""W5-02b K2a/K2b: private cold Site Action list walkthrough producer (`prepare|serve|attest|drop`).

    python tools/w502_cold_work_walkthrough.py prepare     # private *_test DBs, replay, real K1a writes, manifest
    python tools/w502_cold_work_walkthrough.py serve       # one API per DB + 403 + 503 processes, PIDs recorded
    python tools/w502_cold_work_walkthrough.py attest      # re-read lineage; print per-mode status from the real GET
    python tools/w502_cold_work_walkthrough.py drop        # stop only recorded PIDs, drop only this tool's DBs

`.agent/W5-02-build-spec.md` P-G-5 / P-K2b-4-5, "Producer and clocks (K1c)", K1c rulings 2-3 and the run-5
STALE/UNKNOWN rulings. Nothing outside the tool's `*_test` databases and its work folder (`var/w502b*`, gitignored)
is written. `prepare`:

1. `git archive HEAD` of backend/gateway/host/simulator/contracts/config/contract-fixtures/tools into
   `<work>/tree`, so every process runs the committed code, never the shared working tree.
2. Per database mode (`positive`, `worstcase`, `pending`, `stale`, `unknown`) a fresh `w502b_<mode>_<tag>_test`
   database. A child process with ASSETOPS_TEST_DATABASE_URL = that database runs the test-only shifted producer
   (`tools/w502_cold_work_cases.py` + `backend/tests/test_w502_cold_scenario_producer.py`: the generated scenario
   registered only in that process's `FakeScenarios`, Host Lab -> gateway -> Batch V2, then the W2-03 worker).
   `stale` uses the run-5 wider 90-minute window; `unknown` the no-probe replay plus the test-only seeded
   empty-support selection (ruling 3). `K0` is corroborated against the selected Finding revision and the W5-01
   selection's source provenance before any write.
3. Writes, with exact returned IDs: the SERVICE-attested Incident, Maintenance request and its record through the
   W4 service (the product app injects no W4 SERVICE principal), and the domain Action, both case links and the
   intent through the real `POST /api/sites/{site}/domain-work/...` routes of `assetops_backend.main.create_app`
   composed with the W4 fixture SERVICE principal (`domain_work_principal`). Nothing is direct-inserted except the
   ruled UNKNOWN selection seed. `worstcase` adds five Actions through the same POST (160-code-point title and owner,
   mixed due dates). `pending` then releases the late accepted reading and leaves its recompute job unrun.
4. Reads each mode's real `GET .../domain-work/action-index` in process and writes `<work>/manifest.json`.

`serve` starts, per mode, `uvicorn` over a tool-local entry (`<work>/serve_entry.py`) that imports the product
`host/lab_app.py` app and puts, ahead of its domain-work routes, the same `build_domain_work_router` with a `WorkGate`
whose read access is a server-configured operator principal scoped to that Site (`<work>/principal-<mode>.json`,
nothing a client sends). The `forbidden` process holds an operator principal with no Site grant (403
`SITE_SCOPE_FORBIDDEN` from the real gate). K2 ruling 3 (option b): the `unavailable` process serves the healthy
positive DB for the app (the Site read stays healthy) and gives the domain-work router alone an unreachable private
DB URL (`W502B_DOMAIN_WORK_DB_URL`), so the real `WORK_STORE_UNAVAILABLE` 503 renders inside the cold-work panel.
No product router changes.

Guards: `--work` must be a `var/w502b*` folder directly under this repository's `var/`; database names are
`w502b_<mode>_<tag>_test`; `drop` acts only on what the work folder's marker and pid file record.
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
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = Path(sys.executable)
PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
PG_ADMIN = f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops"
MARKER = ".w502b-walkthrough-work"
SITE = "COLD-LAB-001"
DB_MODES = ("positive", "worstcase", "pending", "stale", "unknown")
#: API port per served process; the matching frontend dev port is the API port - 3500.
PORTS = {"positive": 8971, "worstcase": 8972, "pending": 8973, "stale": 8974, "unknown": 8975,
         "forbidden": 8976, "unavailable": 8977}
UNREACHABLE = "postgresql+psycopg://assetops:unused@127.0.0.1:1/w502b_unavailable_test?connect_timeout=2"
OPERATOR = "operator:w502b-cold-lab"
UNGRANTED = "operator:w502b-ungranted"

BUILD = r'''
import json, secrets, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
mode, out = sys.argv[1], Path(sys.argv[2])
CASE = {"positive": "ordinary", "worstcase": "ordinary", "pending": "pending", "stale": "stale",
        "unknown": "no-probe"}[mode]
MECH = {"positive": "COLD_START_FAILURE", "worstcase": "COLD_START_FAILURE", "pending": "COLD_EXCURSION",
        "stale": "COLD_EXCURSION", "unknown": "COLD_START_FAILURE"}[mode]
W501 = {"positive": "CURRENT", "worstcase": "CURRENT", "pending": "CURRENT", "stale": "STALE_SOURCE",
        "unknown": "UNKNOWN"}[mode]
SITE = "COLD-LAB-001"
import test_w502_cold_scenario_producer as P
producer = P.producer
from sqlalchemy import text
from fastapi.testclient import TestClient
from test_w401_work_service_postgres import ACTOR, PRINCIPAL, incident, record, request
from test_w502_domain_intent_postgres import criteria, iso, now_utc
from assetops_backend.config import load_feature_flags
from assetops_backend.main import create_app
from assetops_backend.work.composition import build_work_service
from assetops_backend.work_api import W401_FIXTURE_SERVICE_PRINCIPAL_ID

def z(v):
    return None if v is None else iso(v) if isinstance(v, datetime) else v

def at(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

tag = secrets.token_hex(4)
built = P.produce(lambda m: P.ShiftedChain(m, out / "chain").open(), CASE)
work = build_work_service(P.URL)
doc = {"mode": mode, "case": CASE, "scenario_id": built.shifted.scenario_id, "site_code": SITE,
       "tenant_id": str(built.tenant_id), "site_id": str(built.site_id), "blocked": None}
try:
    sh = built.shifted
    if mode == "unknown":
        seed = P.seed_empty_support(built)
        assert P.support_times(built, seed.new["ar"]) == []
        doc["seeded_selection"] = {"run_id": seed.new["run_id"], "assessment_revision_id": seed.new["ar"],
                                   "seq": seed.new["seq"], "support_removed": seed.support_removed,
                                   "replaced_assessment_revision_id": seed.old["ar"]}
    if mode == "stale":
        exc = P.selected_excursion(built)
        times = P.support_times(built, exc["ar"])
        assert times and times[-1] <= sh.end < sh.window_end - timedelta(minutes=10), times
        doc["stale_support_latest"] = iso(times[-1])
    finding_id, revision_id = P.finding_revision(built, MECH)
    body = P.w501_read(built)
    selection = body["selection"]
    v4 = built.run.registered_basis.binding_set_revision_id
    with built.engine.connect() as c:
        k0 = producer.corroborate_k0(c, built.tenant_id, built.site_id, revision_id, sh, v4, selection)
        cited = sorted(str(v) for v in c.execute(text(
            "SELECT evidence_id FROM finding_revision_evidence WHERE finding_revision_id = :r"), {"r": revision_id}).scalars())
    if selection["state"] != W501:
        doc["blocked"] = f"W5-01 selection state {selection['state']}, expected {W501}"
    # K2 ruling 5: the returned COLD-LAB-001 Foundation asset `generator-1` and its returned ID; no `GEN-CR-01`
    # lookup or display remapping (MOCK DEVIATION (D4) R89 covers the mock's illustrative `GEN-CR-01`).
    gens = [a for a in built.store.registrations(built.tenant_id, built.site_id).assets if a.asset_code == "generator-1"]
    assert len(gens) == 1, [a.asset_code for a in built.store.registrations(built.tenant_id, built.site_id).assets]
    gen = gens[0]
    # K2 ruling 4: the SERVICE-attested INC occurs at D+16h11m inside the source window [D+16h, D+17h) and links both
    # returned selected cold Findings; the WR and its performed record follow it inside the same interval.
    d16 = sh.start
    assert d16 == d16.replace(hour=16, minute=0, second=0, microsecond=0) and d16.utcoffset() == timedelta(0), d16
    inc_at, wr_at, rec_at = (d16 + timedelta(minutes=m) for m in (11, 20, 40))
    assert d16 <= inc_at < wr_at < rec_at < d16 + timedelta(hours=1)
    inc_links = []
    for mech in ("COLD_START_FAILURE", "COLD_EXCURSION"):
        try:
            fid, rid = P.finding_revision(built, mech)
        except AssertionError:
            # K2 ruling 21: the no-probe UNKNOWN replay selects no COLD_EXCURSION revision, so its INC links only the
            # returned COLD_START_FAILURE Finding (expected, not blocked). Every other mode still needs both links.
            if mode == "unknown" and mech == "COLD_EXCURSION":
                continue
            doc["blocked"] = (doc["blocked"] or "") + f" INC: no selected {mech} Finding revision to link (ruling 4)"
            continue
        inc_links.append({"finding_id": fid, "finding_revision_id": rid, "mechanism": mech})
    if mode == "unknown":
        # K2 ruling 21: exactly one selected link (COLD_START_FAILURE) and no excursion link; no synthetic excursion.
        assert [x["mechanism"] for x in inc_links] == ["COLD_START_FAILURE"], inc_links
    else:
        # K2 ruling 4: both selected cold Findings are linked in every other mode.
        assert [x["mechanism"] for x in inc_links] == ["COLD_START_FAILURE", "COLD_EXCURSION"] or doc["blocked"], inc_links
    doc.update({"finding": {"id": finding_id, "revision_id": revision_id, "mechanism": MECH,
                            "assessment_revision_id": k0.assessment_revision_id, "cited_evidence_ids": cited},
                "w501": {"state": selection["state"], "assessment_revision_ids": selection.get("assessment_revision_ids"),
                         "accepted_evidence_ids": sorted(selection.get("accepted_evidence_ids") or []),
                         "window": [iso(k0.window[0]), iso(k0.window[1])]},
                "binding_set_revision_id": v4, "accepted_evidence_ids": list(k0.accepted_ids),
                "asset": {"id": str(gen.id), "code": gen.asset_code}})
    app = create_app(load_feature_flags(), domain_work_principal=lambda r, c: W401_FIXTURE_SERVICE_PRINCIPAL_ID)
    api = TestClient(app)
    base = f"/api/sites/{SITE}/domain-work"

    def post(path, payload):
        r = api.post(base + path, json=payload)
        assert r.status_code == 201, (path, r.status_code, r.text)
        return r.json()

    db_now = now_utc(built.engine)
    # Attested raised_at values lie strictly between K0 and this DB read (the Action follows its evidence).
    step = (db_now - k0.known_at) / 7
    raised = k0.known_at + step
    # K2 ruling 17: every Action raised_at is strictly after K0 and no later than the DB read before the POST.
    assert k0.known_at < raised <= db_now, (k0.known_at, raised, db_now)
    action = post("/actions", {"domain": "COLDCHAIN", "origin_finding_id": finding_id,
                               "origin_finding_revision_id": revision_id, "title": "Witness automatic-start test",
                               "owner_label": "Maintenance lead", "due_at": None, "raised_at": iso(raised),
                               "actor": dict(ACTOR), "idempotency_key": f"w502b-{mode}-action-{tag}"})
    aid = action["id"]
    flink = [{"finding_id": finding_id, "finding_revision_id": revision_id}]
    s, inc = work.create_case(built.tenant_id, built.site_id, incident(
        f"w502b-{mode}-inc-{tag}", title="Backup response failure", occurred_at=iso(inc_at),
        narrative="Grid lost, automatic start failed, chamber above policy", asset_id=str(gen.id),
        finding_links=[{"finding_id": x["finding_id"], "finding_revision_id": x["finding_revision_id"]}
                       for x in inc_links]), PRINCIPAL)
    assert s == 201, inc
    s, wr = work.create_case(built.tenant_id, built.site_id, request(
        f"w502b-{mode}-wr-{tag}", title="Starter/control inspection", occurred_at=iso(wr_at), asset_id=str(gen.id),
        finding_links=flink, incident_id=inc["id"]), PRINCIPAL)
    assert s == 201, wr
    s, rec = work.post_record(built.tenant_id, built.site_id, wr["id"], record(
        f"w502b-{mode}-rec-{tag}", activity="Starter and control inspection", occurred_at=iso(rec_at),
        outcome_note="Inspection complete; witnessed automatic-start test remains required"), PRINCIPAL)
    assert s == 201, rec
    # Ruling 4 manifest assertion: the stored INC (returned ID) has the shifted occurred_at and both selected links.
    with built.engine.connect() as c:
        stored_at = c.execute(text("SELECT occurred_at FROM work_case WHERE id = :c"), {"c": inc["id"]}).scalar_one()
        got_links = sorted([str(f), str(r)] for f, r in c.execute(text(
            "SELECT finding_id, finding_revision_id FROM work_case_finding_link WHERE case_revision_id = :r"),
            {"r": inc["revision"]["id"]}).all())
    assert stored_at == inc_at, (stored_at, inc_at)
    assert got_links == sorted([x["finding_id"], x["finding_revision_id"]] for x in inc_links), got_links
    links = {}
    for key, case in (("incident", inc), ("request", wr)):
        with built.engine.connect() as c:
            ev = str(c.execute(text("SELECT id FROM work_event WHERE case_id = :c ORDER BY recorded_at DESC, id DESC "
                                    "LIMIT 1"), {"c": case["id"]}).scalar_one())
        links[key] = post(f"/actions/{aid}/case-links", {
            "case_id": case["id"], "case_revision_id": case["revision"]["id"], "case_event_id": ev,
            "actor": dict(ACTOR), "idempotency_key": f"w502b-{mode}-link-{key}-{tag}"})
        links[key]["case_event_id"] = ev
    declared = now_utc(built.engine)
    intent = post(f"/actions/{aid}/intents", {
        "supersedes_id": None, "declared_at": iso(declared), "criteria": criteria(),
        "basis": {"finding_revision_id": revision_id, "work_case_id": wr["id"], "work_record_id": rec["id"],
                  "accepted_evidence_ids": cited}, "actor": dict(ACTOR), "idempotency_key": f"w502b-{mode}-intent-{tag}"})
    with built.engine.connect() as c:
        link_times = sorted(c.execute(text("SELECT recorded_at FROM domain_action_case_link WHERE action_id = :a"),
                                      {"a": aid}).scalars())
    K = [k0.known_at, at(action["recorded_at"]), link_times[-1], at(intent["recorded_at"])]
    assert all(a < b for a, b in zip(K, K[1:])), K
    doc["cutoffs"] = {"K0": iso(K[0]), "K1": iso(K[1]), "K2": iso(K[2]), "K3": iso(K[3]),
                      "meaning": {"K0": "max ACCEPTED ingestion_disposition.decided_at (selected evidence cutoff)",
                                  "K1": "fixture Action recorded_at", "K2": "last case link recorded_at",
                                  "K3": "intent recorded_at"}}
    doc["fixture"] = {"action": {"id": aid, "code": action["action_code"], "recorded_at": action["recorded_at"],
                                 "raised_at": iso(raised), "title": "Witness automatic-start test",
                                 "owner_label": "Maintenance lead", "due_at": None},
                      "incident": {"id": inc["id"], "revision_id": inc["revision"]["id"], "occurred_at": iso(inc_at),
                                   "finding_links": inc_links, "returned_finding_links": got_links,
                                   "source_window": [iso(d16), iso(d16 + timedelta(hours=1))],
                                   # K2 ruling 21: the selected-data link limit of this mode, stated in the manifest.
                                   "limit": ("UNKNOWN one-link limit: the no-probe replay selects no COLD_EXCURSION "
                                             "Finding revision, so the INC links only the returned COLD_START_FAILURE "
                                             "Finding (ruling 21; no synthetic excursion)") if mode == "unknown"
                                            else None},
                      "request": {"id": wr["id"], "revision_id": wr["revision"]["id"], "record_id": rec["id"],
                                  "occurred_at": iso(wr_at), "record_occurred_at": iso(rec_at)},
                      "case_links": links, "intent": intent}
    actions = [{"id": aid, "code": action["action_code"], "raised_at": iso(raised),
                "recorded_at": action["recorded_at"], "due_at": None}]
    if mode == "worstcase":
        dues = [None, timedelta(days=1), None, timedelta(days=30), timedelta(days=200)]
        for n, due in enumerate(dues):
            r_at = k0.known_at + step * (n + 2)
            assert raised < r_at <= db_now, (raised, r_at, db_now)  # ruling 17: later than the fixture Action
            head = f"Witness automatic-start test {n + 1} — long title proof "
            title = (head + "x" * 160)[:160]
            owner = (f"Maintenance lead {n + 1} — long owner proof " + "y" * 160)[:160]
            assert len(title) == len(owner) == 160
            made = post("/actions", {"domain": "COLDCHAIN", "origin_finding_id": finding_id,
                                     "origin_finding_revision_id": revision_id, "title": title, "owner_label": owner,
                                     "due_at": None if due is None else iso(r_at + due), "raised_at": iso(r_at),
                                     "actor": dict(ACTOR), "idempotency_key": f"w502b-worst-{n}-{tag}"})
            actions.append({"id": made["id"], "code": made["action_code"], "raised_at": iso(r_at),
                            "recorded_at": made["recorded_at"],
                            "due_at": None if due is None else iso(r_at + due), "title_code_points": 160,
                            "owner_code_points": 160})
    if mode == "pending":
        built.advance_late()  # the later accepted reading; its cold_chain recompute job is deliberately not run
        with built.engine.connect() as c:
            late = c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE site_id = :s "
                                  "AND decision = 'ACCEPTED'"), {"s": built.site_id}).scalar_one()
            jobs = c.execute(text("SELECT count(*) FROM recompute_job WHERE site_id = :s AND domain = 'cold_chain' "
                                  "AND status = 'PENDING'"), {"s": built.site_id}).scalar_one()
        assert late > K[3] and jobs >= 1, (late, jobs)
        doc["cutoffs"]["K_late"] = iso(late)
        doc["cutoffs"]["meaning"]["K_late"] = "late accepted reading decided_at (recompute job left PENDING)"
    doc["actions"] = actions
    day = db_now.replace(hour=0, minute=0, second=0, microsecond=0)
    win = {"from": iso(day - timedelta(days=1)), "to": iso(day + timedelta(days=1))}
    doc["window"] = win

    def index(**q):
        r = api.get(base + "/action-index", params={**win, **q})
        assert r.status_code == 200, r.text
        b = r.json()
        return {"query": {**win, **q}, "status": b["status"], "total_count": b["total_count"],
                "coverage": b["coverage"], "known_at": b["known_at"], "rows": len(b["rows"]),
                "next_cursor": b["next_cursor"] is not None, "row_ids": [x["action_id"] for x in b["rows"]]}

    reads = {}
    if mode == "positive":
        reads["positive"] = dict(index(), expected={"status": "CURRENT", "total_count": 1})
        zero = {"from": iso(day - timedelta(days=8)), "to": iso(day - timedelta(days=1))}
        r = api.get(base + "/action-index", params=zero).json()
        reads["zero"] = {"query": zero, "status": r["status"], "total_count": r["total_count"],
                         "coverage": r["coverage"], "known_at": r["known_at"], "rows": len(r["rows"]),
                         "next_cursor": r["next_cursor"] is not None, "row_ids": [],
                         "expected": {"status": "CURRENT", "total_count": 0}}
        reads["historical"] = dict(index(known_at=doc["cutoffs"]["K3"]),
                                   expected={"status": "HISTORICAL", "total_count": 1})
    elif mode == "worstcase":
        reads["worstcase"] = dict(index(), expected={"status": "CURRENT", "total_count": 6})
    else:
        expected = {"pending": "PENDING_RECOMPUTE", "stale": "STALE_SOURCE", "unknown": "UNKNOWN"}[mode]
        last = doc["cutoffs"].get("K_late") or doc["cutoffs"]["K3"]
        reads[mode] = dict(index(known_at=last), expected={"status": expected, "total_count": 1})
        reads[mode]["read_time_status"] = index()["status"]
    for name, rd in reads.items():
        if (rd["status"], rd["total_count"]) != (rd["expected"]["status"], rd["expected"]["total_count"]):
            doc["blocked"] = (doc["blocked"] or "") + f" {name}: index {rd['status']}/{rd['total_count']} != expected"
    doc["reads"] = reads
finally:
    work._store.dispose()
    built.close()
(out / f"{mode}.json").write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
print("built", mode, "blocked:", doc["blocked"], {k: (v["status"], v["total_count"]) for k, v in doc.get("reads", {}).items()})
'''

ATTEST = r'''
import json, sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID
mode, work = sys.argv[1], Path(sys.argv[2])
m = json.loads((work / f"{mode}.json").read_text(encoding="utf-8"))
import test_w502_cold_scenario_producer as P
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient
from assetops_backend.config import load_feature_flags
from assetops_backend.main import create_app

def at(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

t, s = UUID(m["tenant_id"]), UUID(m["site_id"])
w = m["w501"]["window"]
built = SimpleNamespace(tenant_id=t, site_id=s, shifted=SimpleNamespace(start=at(w[0]), window_end=at(w[1])))
k0 = at(m["cutoffs"]["K0"])
engine = create_engine(P.URL)
problems = []
with engine.connect() as c:
    accepted = sorted(str(v) for v in c.execute(text(
        "SELECT accepted_evidence_id FROM ingestion_disposition WHERE tenant_id = :t AND site_id = :s "
        "AND decision = 'ACCEPTED' AND decided_at <= :k"), {"t": t, "s": s, "k": k0}).scalars())
    watermark = c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE tenant_id = :t AND site_id = :s "
                               "AND decision = 'ACCEPTED' AND decided_at <= :k"), {"t": t, "s": s, "k": k0}).scalar_one()
    fr = c.execute(text("SELECT CAST(finding_id AS text), CAST(assessment_revision_id AS text) FROM finding_revision "
                        "WHERE id = :r AND site_id = :s"), {"r": m["finding"]["revision_id"], "s": s}).first()
    cited = sorted(str(v) for v in c.execute(text(
        "SELECT evidence_id FROM finding_revision_evidence WHERE finding_revision_id = :r"),
        {"r": m["finding"]["revision_id"]}).scalars())
    pinned = c.execute(text("SELECT CAST(origin_finding_revision_id AS text) FROM domain_action WHERE id = :a"),
                       {"a": m["fixture"]["action"]["id"]}).scalar_one()
if accepted != sorted(m["accepted_evidence_ids"]):
    problems.append("accepted envelope IDs at K0 differ from the manifest")
if watermark is None or watermark != k0:
    problems.append(f"K0 {m['cutoffs']['K0']} is not the accepted watermark ({watermark})")
if fr is None or fr[0] != m["finding"]["id"] or fr[1] != m["finding"]["assessment_revision_id"]:
    problems.append("Finding revision / assessment revision differ from the manifest")
if cited != sorted(m["finding"]["cited_evidence_ids"]) or not set(cited) <= set(accepted):
    problems.append("the Finding's cited evidence is not the manifest's accepted set")
if pinned != m["finding"]["revision_id"]:
    problems.append("the fixture Action is not pinned to the selected Finding revision")
at_k0 = P.w501_read(built, m["cutoffs"]["K0"])["selection"]
if m["finding"]["assessment_revision_id"] not in [str(x) for x in at_k0.get("assessment_revision_ids") or ()]:
    problems.append("the Finding's assessment revision is not in the W5-01 selection at K0")
prov = sorted(at_k0.get("accepted_evidence_ids") or [])
if not set(prov) <= set(accepted) or not set(cited) <= set(prov):
    problems.append("W5-01 source provenance accepted IDs disagree with the accepted envelopes / Finding citations")
now_sel = P.w501_read(built)["selection"]
expected_w501 = {"pending": "PENDING_RECOMPUTE"}.get(m["mode"], m["w501"]["state"])
if now_sel["state"] != expected_w501:
    problems.append(f"W5-01 selection now {now_sel['state']}, expected {expected_w501}")
api = TestClient(create_app(load_feature_flags()))
out = {}
for name, rd in m["reads"].items():
    b = api.get(f"/api/sites/{m['site_code']}/domain-work/action-index", params=rd["query"]).json()
    out[name] = {"status": b["status"], "total_count": b["total_count"], "known_at": b["known_at"]}
    if (b["status"], b["total_count"]) != (rd["expected"]["status"], rd["expected"]["total_count"]):
        problems.append(f"{name}: index {b['status']}/{b['total_count']} != expected {rd['expected']}")
engine.dispose()
print(json.dumps({"mode": m["mode"], "w501_now": now_sel["state"], "reads": out, "problems": problems}))
sys.exit(1 if problems else 0)
'''

SERVE_ENTRY = r'''
"""Tool-local uvicorn entry (tools/w502_cold_work_walkthrough.py serve): the product host app plus, ahead of its
domain-work routes, the same router behind a WorkGate whose read access is a server-configured operator principal."""
import json, os
from lab_app import app
from assetops_backend import main as M
from assetops_backend.domain_work_api import build_domain_work_router
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.foundation_service import FoundationService
from assetops_backend.work.composition import build_domain_action_read_service, build_domain_intent_service
from assetops_backend.work_api import WorkGate

grant = json.loads(open(os.environ["W502B_PRINCIPAL_FILE"], encoding="utf-8").read())
sites = {c.upper() for c in grant["sites"]}
access = lambda request, code: None if code.upper() in sites else 403
url = M.database_url()
# K2 ruling 3 (option b): capture-only. The Site registry and the product app keep the healthy DB; only this
# domain-work router's stores use W502B_DOMAIN_WORK_DB_URL when set (the `unavailable` process: unreachable -> 503).
work_url = os.environ.get("W502B_DOMAIN_WORK_DB_URL") or url
registry = ImportedSiteRegistry(FoundationService(M.build_foundation_store(url), M.DEVELOPMENT_TENANT_SLUG, M.utc_now))
router = build_domain_work_router(
    build_domain_intent_service(work_url) if work_url else None,
    WorkGate(registry.ledger_scope, (M.WORK_UNAVAILABLE,), access=access, command_access=access),
    (M.WORK_UNAVAILABLE,), reads=build_domain_action_read_service(work_url))
app.router.routes[0:0] = list(router.routes)
'''


def say(text: str = "") -> None:
    print(text, flush=True)


class Walk:
    def __init__(self, work: str, tag: str) -> None:
        path = (REPO / work).resolve() if not Path(work).is_absolute() else Path(work).resolve()
        if path.parent != (REPO / "var").resolve() or not path.name.startswith("w502b"):
            raise SystemExit(f"Refused: --work {path} must be a var/w502b* folder directly under {REPO / 'var'}")
        if not re.fullmatch(r"[a-z0-9]{1,12}", tag):
            raise SystemExit("Refused: --tag must be 1-12 lower-case letters/digits")
        self.work, self.tree, self.tag = path, path / "tree", tag
        self.dbs = {m: f"w502b_{m}_{tag}_test" for m in DB_MODES}

    def url(self, mode: str) -> str:
        return f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{self.dbs[mode]}"

    def env(self, db_url: str, *, tests: bool = False) -> dict[str, str]:
        out = {k: v for k, v in os.environ.items() if not k.startswith("ASSETOPS_TEST_")}
        parts = ["backend", "gateway", "simulator", "contracts", "host"] + (["backend/tests"] if tests else [])
        out["PYTHONPATH"] = os.pathsep.join(str(self.tree / p) for p in parts)
        out["DATABASE_URL"] = db_url
        out["PYTHONUNBUFFERED"] = "1"
        if tests:
            out["ASSETOPS_TEST_DATABASE_URL"] = db_url  # the producer test modules read it at import (unrouted)
        return out

    def py(self, argv: list[str], db_url: str, *, tests: bool = False, check: bool = True, cwd: Path | None = None):
        done = subprocess.run([str(PY), *argv], cwd=str(cwd or self.tree), env=self.env(db_url, tests=tests),
                              capture_output=True, text=True, timeout=1800)
        if check and done.returncode != 0:
            raise SystemExit(f"FAILED: python {' '.join(argv[:2])[:80]}\n{done.stdout[-4000:]}\n{done.stderr[-4000:]}")
        return done

    def marker(self) -> dict:
        path = self.work / MARKER
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}

    def pids_file(self) -> Path:
        return self.work / "pids.json"

    # ---- prepare ---------------------------------------------------------------------------------------------

    def prepare(self, modes: list[str]) -> None:
        import psycopg

        if self.work.exists() and any(self.work.iterdir()) and not self.marker():
            raise SystemExit(f"Refused: {self.work} exists, is not empty and was not made by this tool")
        if self.pids_file().is_file() and json.loads(self.pids_file().read_text(encoding="utf-8")):
            raise SystemExit("Refused: servers recorded in pids.json are still owned; run drop first")
        known = set(self.marker().get("dbs", []))
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            for m in modes:
                exists = c.execute("SELECT 1 FROM pg_database WHERE datname = %s", (self.dbs[m],)).fetchone()
                if exists and self.dbs[m] not in known:
                    raise SystemExit(f"Refused: database {self.dbs[m]} exists and was not made by this tool")
        say("=== 1. Private tree (git HEAD) ===")
        self.work.mkdir(parents=True, exist_ok=True)
        (self.work / MARKER).write_text(json.dumps({"tool": "tools/w502_cold_work_walkthrough.py",
                                                    "dbs": sorted(known | {self.dbs[m] for m in modes})}),
                                        encoding="utf-8")
        if self.tree.exists():
            shutil.rmtree(self.tree)
        self.tree.mkdir(parents=True)
        archive = subprocess.run(["git", "archive", "--format=tar", "HEAD", "backend", "gateway", "host", "simulator",
                                  "contracts", "config", "contract-fixtures", "tools"], cwd=REPO, capture_output=True,
                                 check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(self.tree, filter="data")
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True)
        self.revision = head.stdout.strip()
        say(f"  {self.tree} (code from {self.revision})")
        probe = self.py(["-c", "import assetops_backend;print(assetops_backend.__file__)"], self.url(modes[0]))
        if str(self.tree).lower() not in probe.stdout.strip().lower():
            raise SystemExit(f"Isolation failed: assetops_backend resolves to {probe.stdout.strip()}")
        (self.work / "serve_entry.py").write_text(SERVE_ENTRY, encoding="utf-8")
        for n, m in enumerate(modes, start=2):
            say(f"=== {n}. {m}: database {self.dbs[m]} ===")
            with psycopg.connect(PG_ADMIN, autocommit=True) as c:
                c.execute(f"DROP DATABASE IF EXISTS {self.dbs[m]} WITH (FORCE)")
                c.execute(f"CREATE DATABASE {self.dbs[m]}")
            mode_dir = self.work / "build" / m
            if mode_dir.exists():
                shutil.rmtree(mode_dir)
            mode_dir.mkdir(parents=True)
            started = time.time()
            done = self.py(["-c", BUILD, m, str(mode_dir)], self.url(m), tests=True, check=False,
                           cwd=self.tree / "backend" / "tests")
            tail = (done.stdout.strip().splitlines() or ["(no output)"])[-1]
            say(f"  {tail}  ({time.time() - started:.0f}s)")
            if done.returncode != 0:
                (mode_dir / "error.txt").write_text(done.stdout + "\n" + done.stderr, encoding="utf-8")
                say(f"  FAILED (exit {done.returncode}); recorded as blocked. {done.stderr.strip()[-1500:]}")
        self.write_manifest()

    def write_manifest(self) -> None:
        modes = {}
        for m in DB_MODES:
            path = self.work / "build" / m / f"{m}.json"
            err = self.work / "build" / m / "error.txt"
            if not path.is_file():
                modes[m] = {"blocked": "prepare failed: " + (err.read_text(encoding="utf-8")[-600:] if err.is_file()
                                                             else "not prepared"), "db": self.dbs[m]}
                continue
            doc = json.loads(path.read_text(encoding="utf-8"))
            doc.update(db=self.dbs[m], api_base=f"http://127.0.0.1:{PORTS[m]}",
                       frontend=self.frontend_hint(m))
            modes[m] = doc
        positive = modes.get("positive", {})
        principal = {
            "mechanism": "server configuration per API process (<work>/principal-<mode>.json read via "
                         "W502B_PRINCIPAL_FILE by <work>/serve_entry.py); no request header or token is sent",
            "granted": {"principal": OPERATOR, "sites": [SITE]}, "forbidden": {"principal": UNGRANTED, "sites": []},
            "writes": "prepare only, through create_app(domain_work_principal=W4 fixture SERVICE principal); "
                      "served processes inject no SERVICE principal (writes 403)"}
        extra = {
            "forbidden": {"api_base": f"http://127.0.0.1:{PORTS['forbidden']}", "db": self.dbs["positive"],
                          "site_code": SITE, "query": (positive.get("reads") or {}).get("positive", {}).get("query"),
                          "expected": {"http": 403, "code": "SITE_SCOPE_FORBIDDEN"},
                          "frontend": self.frontend_hint("forbidden")},
            "unavailable": {"api_base": f"http://127.0.0.1:{PORTS['unavailable']}", "db": self.dbs["positive"],
                            "domain_work_db_url": UNREACHABLE, "site_code": SITE,
                            "query": (positive.get("reads") or {}).get("positive", {}).get("query"),
                            "expected": {"http": 503, "code": "WORK_STORE_UNAVAILABLE", "site_read_http": 200},
                            "mechanism": "K2 ruling 3 option (b): healthy Site read, domain-work router alone on an "
                                         "unreachable private DB URL",
                            "frontend": self.frontend_hint("unavailable")}}
        manifest = {"schema": "w502b-cold-work-walkthrough-1", "revision": getattr(self, "revision", None),
                    "work": str(self.work), "site_code": SITE, "principal": principal, "modes": modes,
                    "processes": extra,
                    "notes": {"zero": "positive DB, window with no Actions (healthy COMPLETE zero)",
                              "historical": "positive DB, known_at = K3 (an earlier returned cutoff)"}}
        path = self.work / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        say(f"Manifest: {path}")

    def frontend_hint(self, mode: str) -> str:
        return (f'cd frontend; $env:ASSETOPS_API_PORT="{PORTS[mode]}"; '
                f"npm.cmd run dev -- --port {PORTS[mode] - 3500} --strictPort")

    # ---- serve -----------------------------------------------------------------------------------------------

    def serve(self) -> None:
        manifest = self.manifest()
        pids = json.loads(self.pids_file().read_text(encoding="utf-8")) if self.pids_file().is_file() else {}
        logs = self.work / "logs"
        logs.mkdir(exist_ok=True)
        plan = [(m, self.url(m), [SITE]) for m in DB_MODES if manifest["modes"][m].get("reads")]
        plan += [("forbidden", self.url("positive"), []), ("unavailable", self.url("positive"), [SITE])]
        flags = (getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0))
        for name, db_url, sites in plan:
            if name in pids and _alive(pids[name]["pid"]):
                say(f"  {name}: already running pid {pids[name]['pid']} port {pids[name]['port']}")
                continue
            port = PORTS[name]
            grant = self.work / f"principal-{name}.json"
            grant.write_text(json.dumps({"principal": UNGRANTED if not sites else OPERATOR, "sites": sites}),
                             encoding="utf-8")
            env = self.env(db_url)
            env["W502B_PRINCIPAL_FILE"] = str(grant)
            if name == "unavailable":
                env["W502B_DOMAIN_WORK_DB_URL"] = UNREACHABLE  # ruling 3: the domain-work router alone
            env["PYTHONPATH"] = os.pathsep.join([str(self.work), env["PYTHONPATH"]])
            log = open(logs / f"api-{name}-{port}.log", "w", encoding="utf-8")
            proc = subprocess.Popen([str(PY), "-m", "uvicorn", "serve_entry:app", "--host", "127.0.0.1", "--port",
                                     str(port)], cwd=str(self.tree / "host"), env=env, stdout=log,
                                    stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=flags)
            pids[name] = {"pid": proc.pid, "port": port, "db_url": db_url.replace(PW, "***"),
                          "domain_work_db_url": UNREACHABLE if name == "unavailable" else None,
                          "log": str(logs / f"api-{name}-{port}.log")}
            self.pids_file().write_text(json.dumps(pids, indent=2), encoding="utf-8")
        for name, info in pids.items():
            ok = _wait_health(info["port"])
            say(f"  {name}: pid {info['pid']} http://127.0.0.1:{info['port']} health={'ok' if ok else 'NOT UP'}")
        say("Frontend dev server (PowerShell, repository root), one per API, e.g. positive:")
        say("  " + self.frontend_hint("positive"))
        say("  Site Actions page: http://localhost:<web port>/sites/COLD-LAB-001/... with the manifest window query")

    def manifest(self) -> dict:
        path = self.work / "manifest.json"
        if not path.is_file():
            raise SystemExit("Run prepare first.")
        return json.loads(path.read_text(encoding="utf-8"))

    # ---- attest ----------------------------------------------------------------------------------------------

    def attest(self) -> None:
        manifest, failures = self.manifest(), []
        for m in DB_MODES:
            doc = manifest["modes"][m]
            if not doc.get("reads"):
                say(f"  {m}: BLOCKED ({doc.get('blocked')})")
                continue
            # K2 ruling 21: no mode is blocked; UNKNOWN has its one ruled link, every other mode both links.
            inc = (doc.get("fixture") or {}).get("incident") or {}
            mechs = [x["mechanism"] for x in inc.get("finding_links") or []]
            want = ["COLD_START_FAILURE"] if m == "unknown" else ["COLD_START_FAILURE", "COLD_EXCURSION"]
            say(f"  {m}: blocked={doc.get('blocked')} INC links={mechs} limit={inc.get('limit')}")
            if doc.get("blocked") or mechs != want or (m == "unknown") != bool(inc.get("limit")):
                failures.append(f"{m}: blocked={doc.get('blocked')} INC links {mechs} != {want} or limit missing")
            done = self.py(["-c", ATTEST, m, str(self.work / "build" / m)], self.url(m), tests=True, check=False,
                           cwd=self.tree / "backend" / "tests")
            line = (done.stdout.strip().splitlines() or ["{}"])[-1]
            say(f"  {m} (DB lineage + in-process GET): {line}")
            if done.returncode != 0:
                failures.append(f"{m}: {line[-300:]} {done.stderr.strip()[-600:]}")
        pids = json.loads(self.pids_file().read_text(encoding="utf-8")) if self.pids_file().is_file() else {}
        if pids:
            say("  Served processes (real HTTP GET action-index):")
        for m in DB_MODES:
            if m not in pids:
                continue
            for name, rd in (manifest["modes"][m].get("reads") or {}).items():
                code, body = _get(pids[m]["port"], rd["query"])
                got = (code, body.get("status"), body.get("total_count"))
                say(f"    {name:<11} :{pids[m]['port']} -> HTTP {code} status={got[1]} total_count={got[2]} "
                    f"known_at={body.get('known_at')}")
                if got != (200, rd["expected"]["status"], rd["expected"]["total_count"]):
                    failures.append(f"served {name}: {got}")
        for name in ("forbidden", "unavailable"):
            if name not in pids:
                continue
            spec = manifest["processes"][name]
            code, body = _get(pids[name]["port"], spec["query"])
            detail = body.get("detail") or {}
            say(f"    {name:<11} :{pids[name]['port']} -> HTTP {code} {detail.get('code')} {detail.get('message')!r}")
            if (code, detail.get("code")) != (spec["expected"]["http"], spec["expected"]["code"]):
                failures.append(f"served {name}: HTTP {code} {detail}")
            if "site_read_http" in spec["expected"]:
                site_code, _ = _get_path(pids[name]["port"], f"/api/sites/{SITE}")
                say(f"    {name:<11} :{pids[name]['port']} Site read -> HTTP {site_code}")
                if site_code != spec["expected"]["site_read_http"]:
                    failures.append(f"served {name}: Site read HTTP {site_code}, expected a healthy Site (ruling 3)")
        if failures:
            raise SystemExit("ATTEST FAILED: " + "; ".join(failures))
        say("ATTEST OK")

    # ---- drop ------------------------------------------------------------------------------------------------

    def drop(self) -> None:
        import psycopg

        if self.pids_file().is_file():
            pids = json.loads(self.pids_file().read_text(encoding="utf-8"))
            for name, info in list(pids.items()):
                if _alive(info["pid"]):
                    subprocess.run(["taskkill", "/PID", str(info["pid"]), "/T", "/F"], capture_output=True)
                    say(f"stopped {name} pid {info['pid']}")
                pids.pop(name)
            self.pids_file().write_text(json.dumps(pids), encoding="utf-8")
        recorded = self.marker().get("dbs", [])
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            for db in recorded:
                if not re.fullmatch(r"w502b_[a-z]+_[a-z0-9]+_test", db):
                    say(f"not dropping {db}: not a w502b *_test name")
                    continue
                c.execute(f"DROP DATABASE IF EXISTS {db} WITH (FORCE)")
                say(f"dropped database {db}")
        if self.work.exists() and self.marker():
            shutil.rmtree(self.work)
            say(f"removed {self.work}")


def _alive(pid: int) -> bool:
    done = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
    return str(pid) in done.stdout


def _get(port: int, query: dict | None) -> tuple[int, dict]:
    return _get_path(port, f"/api/sites/{SITE}/domain-work/action-index?{urllib.parse.urlencode(query or {})}")


def _get_path(port: int, path: str) -> tuple[int, dict]:
    url = f"http://127.0.0.1:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
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
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=5) as r:
                if r.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(1)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(prog="tools/w502_cold_work_walkthrough.py")
    parser.add_argument("--work", default="var/w502b_cold_work", help="work folder var/w502b* under this repository")
    parser.add_argument("--tag", default="k2", help="database name tag: w502b_<mode>_<tag>_test")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--modes", default=",".join(DB_MODES))
    sub.add_parser("serve")
    sub.add_parser("attest")
    sub.add_parser("drop")
    args = parser.parse_args()
    walk = Walk(args.work, args.tag)
    if args.cmd == "prepare":
        modes = [m for m in args.modes.split(",") if m]
        if not modes or set(modes) - set(DB_MODES):
            raise SystemExit(f"--modes must name some of {DB_MODES}")
        walk.prepare(modes)
    elif args.cmd == "serve":
        walk.serve()
    elif args.cmd == "attest":
        walk.attest()
    else:
        walk.drop()


if __name__ == "__main__":
    main()
