"""W4-03 unit 8: explicit decision-to-work associations and the Site Work decision-context overlay over Postgres
(`.agent/W4-03-build-spec.md` "Work connection"; closure 1 case link and overlay; closure 4 B1/B2/N4; "Unit-5..12
rulings (u5)" unit 8 and the u6 unit-8 paragraph).

The MG study is projected by the unit-4 worker over the MG-W402-001 authored cases. W4-01 cases are created through
W4-01 `WorkService` in process (B2), never over HTTP; the W4-03 association goes through the router with the
injected W4-03 principal.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, imported, store  # noqa: F401
    from test_w402_reads_postgres import CODE, DAYS
    from test_w403_opportunity_read_postgres import bare_root, now, page, service
    from test_w403_opportunity_worker_postgres import project
    from test_w403_scenarios_postgres import load_command, mg, principal_for, selected_pins, tariff_command

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import link_rows_on
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.finding_api import ACCESS_BASIS
    from assetops_backend.mini_decisions.model import GRANT_PREFIX, DecisionPrincipal
    from assetops_backend.mini_decisions.scenarios import ScenarioService
    from assetops_backend.mini_decisions.store import PostgresMiniDecisionStore
    from assetops_backend.mini_decisions.work_links import WorkLinkService
    from assetops_backend.mini_decisions_api import build_mini_decisions_router
    from assetops_backend.mini_depth.read import MiniDepthRead
    from assetops_backend.work.adapters.postgres_work_read import PostgresWorkRead
    from assetops_backend.work.composition import _link_read_ports, build_work_service
    from assetops_backend.work.site_index import WorkIndexService, parse_list_request

WRITE_KEYS = {"schema_version", "id", "case_id", "kind", "decision_id", "recorded_at"}
CASE_PRINCIPAL = "service:w401-fixture"
CASE_ACTOR = {"kind": "SERVICE", "id": CASE_PRINCIPAL, "attestation": "service=w401-fixture;job=positive-case;rule=w401/1"}
ROUTE = f"/api/sites/{CODE}/work/decision-links"
CONTEXTS = f"/api/sites/{CODE}/work/decision-contexts"
UNAVAILABLE = "Decision context unavailable"


def ago(**delta) -> str:
    return (datetime.now(timezone.utc) - timedelta(**delta)).isoformat().replace("+00:00", "Z")


def new_case(t, s, kind, key, **over) -> str:
    """A W4-01 case through `WorkService` in process (closure 4 B2), never a W4-01 HTTP POST."""
    body = {"kind": kind, "occurred_at": ago(hours=1), "asset_id": None, "finding_links": [], "action_links": [],
            "title": "Witnessed start request failed" if kind == "INCIDENT" else "Inspect starter circuit",
            "narrative": "Operator observed a failed start request; cause not established.",
            "cited_accepted_evidence_ids": [], "actor": dict(CASE_ACTOR), "idempotency_key": key, **over}
    status, out = build_work_service(URL).create_case(t, s, body, CASE_PRINCIPAL)
    assert status == 201
    return out["id"]


def api(engine, t, s, *, who="principal", grant=None, site_type="MINIGRID") -> TestClient:
    registry = SimpleNamespace(
        tenant=lambda: SimpleNamespace(id=t),
        imported=lambda code: SimpleNamespace(id=s, site_code=CODE, site_type=site_type) if code == CODE else None)
    principal = principal_for(t, s) if who == "principal" else who
    app = FastAPI()
    app.include_router(build_mini_decisions_router(
        None, registry, command_access=lambda r, c: grant, principal=lambda r, c: principal,
        work_links=WorkLinkService(PostgresMiniDecisionStore(engine))))
    return TestClient(app)


def body(key, case_id, *, opportunity_id=None, scenario_id=None, **actor) -> dict:
    return {"schema_version": "mini-decision-link-command-1", "idempotency_key": key,
            "actor": {"kind": "SERVICE", "id": "service:w403-fixture",
                      "attestation": "service=w403-fixture;job=positive-decisions;rule=w403/1", **actor},
            "case_id": str(case_id), "scenario_id": None if scenario_id is None else str(scenario_id),
            "opportunity_id": None if opportunity_id is None else str(opportunity_id)}


def link_count(engine) -> int:
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM mini_decision_work_link")).scalar_one()


def work_rows(engine) -> int:
    with engine.connect() as c:
        return sum(c.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
                   for table in ("work_case", "incident", "maintenance_work_request", "work_case_revision",
                                 "work_case_finding_link", "work_case_action_link", "work_case_evidence",
                                 "work_event", "maintenance_record"))


def scenarios_for(engine):
    return ScenarioService(PostgresMiniDecisionStore(engine), MiniDepthRead(engine, link_rows_on))


def other_site(store, engine) -> object:  # noqa: F811
    """A second imported Site: its case is foreign to MG-W402-001 (B1 cross-Site refusal)."""
    imported(store, code="W403-OTHER-001")
    with engine.connect() as c:
        return c.execute(text("SELECT id FROM site WHERE site_code_key = lower('W403-OTHER-001')")).scalar_one()


def test_same_site_explicit_link_only(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    project(engine)
    oid = page(service(engine), t, s)["rows"][0]["opportunity"]["id"]
    _, scenario = scenarios_for(engine).create(t, s, principal_for(t, s), tariff_command("w403-u8-scn-01"))
    incident = new_case(t, s, "INCIDENT", "w403-u8-case-01")
    client = api(engine, t, s)

    created = client.post(ROUTE, json=body("w403-u8-lnk-01", incident, opportunity_id=oid))
    assert created.status_code == 201 and set(created.json()) == WRITE_KEYS
    out = created.json()
    assert (out["schema_version"], out["case_id"], out["kind"], out["decision_id"]) == (
        "mini-decision-link-write-1", incident, "OPPORTUNITY", oid)
    assert out["recorded_at"].endswith("Z") and len(out["recorded_at"].split(".")[1]) == 7
    # Exact retry: the original body with 200; changed content under the same key: 409; nothing new stored.
    again = client.post(ROUTE, json=body("w403-u8-lnk-01", incident, opportunity_id=oid))
    assert again.status_code == 200 and again.json() == out
    changed = client.post(ROUTE, json=body("w403-u8-lnk-01", incident, scenario_id=scenario["id"]))
    assert changed.status_code == 409 and changed.json()["detail"]["code"] == "DECISION_DUPLICATE_KEY"
    # A scenario association names its kind.
    scn = client.post(ROUTE, json=body("w403-u8-lnk-02", incident, scenario_id=scenario["id"]))
    assert scn.status_code == 201 and (scn.json()["kind"], scn.json()["decision_id"]) == ("SCENARIO", scenario["id"])
    assert link_count(engine) == 2

    # Unknown and foreign case: 404 WORK_CASE_NOT_FOUND (W4-01's own code and message).
    foreign_site = other_site(store, engine)
    foreign_case = new_case(t, foreign_site, "INCIDENT", "w403-u8-case-02")
    for case_id in (uuid4(), foreign_case):
        r = client.post(ROUTE, json=body("w403-u8-lnk-03", case_id, opportunity_id=oid))
        assert r.status_code == 404 and r.json()["detail"] == {"code": "WORK_CASE_NOT_FOUND",
                                                               "message": "No work case with this ID at this site."}
    # Foreign or unknown decision in the body: 422 DECISION_LINK_SCOPE_INVALID.
    foreign_scenario = uuid4()
    for decision in ({"opportunity_id": uuid4()}, {"scenario_id": foreign_scenario}):
        r = client.post(ROUTE, json=body("w403-u8-lnk-04", incident, **decision))
        assert r.status_code == 422 and r.json()["detail"]["code"] == "DECISION_LINK_SCOPE_INVALID"
    # The foreign Site's own registry cannot link its case to the MG opportunity either.
    cross = api(engine, t, foreign_site)
    r = cross.post(ROUTE, json=body("w403-u8-lnk-05", foreign_case, opportunity_id=oid))
    assert r.status_code == 422 and r.json()["detail"]["code"] == "DECISION_LINK_SCOPE_INVALID"
    # Shape: exactly one decision ID; closed keys; the actor rules.
    for bad in (body("w403-u8-lnk-06", incident),
                body("w403-u8-lnk-06", incident, opportunity_id=oid, scenario_id=scenario["id"]),
                {**body("w403-u8-lnk-06", incident, opportunity_id=oid), "extra": 1},
                {**body("w403-u8-lnk-06", incident, opportunity_id=oid),
                 "schema_version": "mini-opportunity-scenario-command-1"},
                body("w403-u8-lnk-06", "not-a-uuid", opportunity_id=oid),
                body("short", incident, opportunity_id=oid)):
        r = client.post(ROUTE, json=bad)
        assert r.status_code == 422 and r.json()["detail"]["code"] == "DECISION_INPUT_INVALID"
    r = client.post(ROUTE, json=body("w403-u8-lnk-07", incident, opportunity_id=oid, kind="USER"))
    assert r.status_code == 403 and r.json()["detail"]["code"] == "DECISION_USER_AUTH_REQUIRED"
    r = client.post(ROUTE, json=body("w403-u8-lnk-08", incident, opportunity_id=oid,
                                     attestation="service=x;job=j;rule=r"))
    assert r.status_code == 422 and r.json()["detail"]["code"] == "DECISION_ATTESTATION_INVALID"
    # An already-linked pair under a new key is not a second association (reading, PR-10.1).
    r = client.post(ROUTE, json=body("w403-u8-lnk-09", incident, opportunity_id=oid))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "DECISION_DUPLICATE_KEY"
    # Scope and grant precede the body; a non-MINIGRID Site authors no decision link.
    for refused in (api(engine, t, s, grant=403), api(engine, t, s, who=None),
                    api(engine, t, s, who=DecisionPrincipal("SERVICE", "service:w403-fixture", t, uuid4(),
                                                            GRANT_PREFIX + "service:w403-fixture"))):
        r = refused.post(ROUTE, content=b"not json")
        assert r.status_code == 403 and r.json()["detail"]["code"] == "DECISION_WRITE_FORBIDDEN"
    r = api(engine, t, s, site_type="COLD_ROOM").post(ROUTE, json=body("w403-u8-lnk-10", incident,
                                                                        opportunity_id=oid))
    assert r.status_code == 422 and r.json()["detail"]["code"] == "DECISION_LINK_SCOPE_INVALID"
    assert link_count(engine) == 2


def test_contexts_at_cutoff_order_and_unlinked_cases(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    project(engine)
    oid = page(service(engine), t, s)["rows"][0]["opportunity"]["id"]
    code = page(service(engine), t, s)["rows"][0]["opportunity"]["code"]
    who = principal_for(t, s)
    scenarios = scenarios_for(engine)
    pins = selected_pins(engine, t, s)
    _, scenario = scenarios.create(t, s, who, load_command("w403-u8-scn-11", pins))
    bare = str(bare_root(engine, t, s, DAYS[1], DAYS[-1] + timedelta(days=1)))
    incident = new_case(t, s, "INCIDENT", "w403-u8-case-11")
    request = new_case(t, s, "MAINTENANCE_REQUEST", "w403-u8-case-12")
    unlinked = new_case(t, s, "INCIDENT", "w403-u8-case-13")
    client = api(engine, t, s)
    k0 = now(engine)
    # Scenario first in time, then the opportunity: the overlay still orders OPPORTUNITY before SCENARIO.
    assert client.post(ROUTE, json=body("w403-u8-lnk-11", incident, scenario_id=scenario["id"])).status_code == 201
    assert client.post(ROUTE, json=body("w403-u8-lnk-12", incident, opportunity_id=oid)).status_code == 201
    assert client.post(ROUTE, json=body("w403-u8-lnk-13", request, opportunity_id=bare)).status_code == 201
    k1 = now(engine)
    status, _ = scenarios.correct(t, s, who, scenario["id"], {
        **load_command("w403-u8-scn-12", pins), "name": "Grain mill corrected trial",
        "supersedes_revision_id": scenario["revision_id"], "correction_reason": "Rename the trial."})
    assert status == 201

    ids = ",".join((incident, request, unlinked))
    r = client.get(CONTEXTS, params={"case_ids": ids, "known_at": k1})
    assert r.status_code == 200
    got = r.json()
    assert set(got) == {"schema_version", "known_at", "contexts"} and got["schema_version"] == "mini-work-contexts-1"
    assert got["known_at"] == k1 and list(got["contexts"]) == [incident, request, unlinked]
    assert got["contexts"][incident] == [
        {"kind": "OPPORTUNITY", "id": oid, "label": code, "url": f"/sites/{CODE}/opportunities/{oid}"},
        {"kind": "SCENARIO", "id": scenario["id"], "label": f"{scenario['code']} · Grain mill one-hour trial",
         "url": None}]
    # A linked root with no visible selected revision.
    assert got["contexts"][request] == [{"kind": "OPPORTUNITY", "id": bare, "label": UNAVAILABLE, "url": None}]
    assert got["contexts"][unlinked] == []
    # The current read names the corrected scenario; the old cutoff shows no association.
    latest = client.get(CONTEXTS, params={"case_ids": incident}).json()["contexts"][incident]
    assert latest[1]["label"] == f"{scenario['code']} · Grain mill corrected trial"
    assert client.get(CONTEXTS, params={"case_ids": ids, "known_at": k0}).json()["contexts"] == {
        incident: [], request: [], unlinked: []}
    # An unknown or foreign case refuses the whole read.
    foreign_case = new_case(t, other_site(store, engine), "INCIDENT", "w403-u8-case-14")
    for extra in (str(uuid4()), foreign_case):
        r = client.get(CONTEXTS, params={"case_ids": f"{incident},{extra}", "known_at": k1})
        assert r.status_code == 404 and r.json()["detail"]["code"] == "WORK_CASE_NOT_FOUND"
    # A case created after the cutoff is not visible at it.
    late = new_case(t, s, "INCIDENT", "w403-u8-case-15")
    assert client.get(CONTEXTS, params={"case_ids": late, "known_at": k1}).status_code == 404
    # Query shape: 1-100 distinct lowercase UUIDs; one known_at, not in the future.
    for bad in ("", incident.upper(), f"{incident},{incident}", ",".join(str(uuid4()) for _ in range(101)),
                "nope"):
        r = client.get(CONTEXTS, params={"case_ids": bad})
        assert r.status_code == 422 and r.json()["detail"]["code"] == "DECISION_INPUT_INVALID", bad
    assert client.get(CONTEXTS).json()["detail"]["code"] == "DECISION_INPUT_INVALID"
    r = client.get(CONTEXTS, params={"case_ids": incident, "known_at": "2999-01-01T00:00:00Z"})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "INVALID_KNOWN_AT"


def test_unlinked_cases_keep_full_count_and_unverified_outcome(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    project(engine)
    oid = page(service(engine), t, s)["rows"][0]["opportunity"]["id"]
    linked = new_case(t, s, "INCIDENT", "w403-u8-case-21")
    unlinked = new_case(t, s, "INCIDENT", "w403-u8-case-22")
    request = new_case(t, s, "MAINTENANCE_REQUEST", "w403-u8-case-23")
    window = (ago(hours=3), ago(minutes=-5))
    reads = PostgresWorkRead(URL, link_rows=build_link_rows_reader(), ports=_link_read_ports())
    lists = WorkIndexService(reads)

    def listing(kind, known=None, limit=None, cursor=None):
        req = parse_list_request(window[0], window[1], limit, [] if known is None else [known], cursor)
        return lists.read(t, s, CODE, kind, req, access_basis=ACCESS_BASIS)

    try:
        k0 = now(engine)
        before = {kind: listing(kind, k0) for kind in ("incidents", "maintenance")}
        first_page = listing("incidents", k0, limit="1")
        rows_before = work_rows(engine)
        client = api(engine, t, s)
        assert client.post(ROUTE, json=body("w403-u8-lnk-21", linked, opportunity_id=oid)).status_code == 201
        assert client.post(ROUTE, json=body("w403-u8-lnk-22", request, opportunity_id=oid)).status_code == 201
        # No W4-01 row is written; the same-cutoff W4-01 lists, page and cursor are byte-identical.
        assert work_rows(engine) == rows_before
        for kind, envelope in before.items():
            assert listing(kind, k0) == envelope
        assert listing("incidents", k0, limit="1") == first_page
        second = listing("incidents", k0, limit="1", cursor=first_page["next_cursor"])
        assert second["total_count"] == 2 and len(second["rows"]) == 1
        # The current lists keep every case, the full count and the unverified maintenance outcome.
        current = {kind: listing(kind) for kind in ("incidents", "maintenance")}
        assert current["incidents"]["total_count"] == 2
        assert {r["case_id"] for r in current["incidents"]["rows"]} == {linked, unlinked}
        assert current["maintenance"]["total_count"] == 1
        [maintenance] = current["maintenance"]["rows"]
        assert maintenance["outcome_state"] == "UNVERIFIED" and maintenance["url"] is None
        assert all(r["url"] is None for r in current["incidents"]["rows"])
        # The overlay is separate: the unlinked case maps to [], the linked ones to the opportunity.
        # The overlay reads the W4-01 list's exact `known_at`.
        params = {"case_ids": ",".join((linked, unlinked, request)), "known_at": current["incidents"]["known_at"]}
        contexts = client.get(CONTEXTS, params=params).json()["contexts"]
        assert contexts[unlinked] == [] and [c["id"] for c in contexts[linked]] == [oid]
        assert [c["id"] for c in contexts[request]] == [oid]
    finally:
        reads.dispose()
