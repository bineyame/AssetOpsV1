"""W4-03 unit 5: the authored opportunity-scenario association (`.agent/W4-03-build-spec.md` closure 1 Q1-Q3,
"Unit-5..12 rulings (u5)" unit 5 command paragraph): `POST /api/sites/{code}/opportunities/{id}/scenario-links`
through the router with the injected W4-03 principal, over the persisted store.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_w402_reads_postgres import CODE, DAYS
    from test_w403_opportunity_read_postgres import codes, detail, link_body, now, page, service
    from test_w403_opportunity_worker_postgres import project
    from test_w403_scenarios_postgres import load_command, mg, principal_for, selected_pins, tariff_command

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import link_rows_on
    from assetops_backend.mini_decisions.model import GRANT_PREFIX, DecisionPrincipal
    from assetops_backend.mini_decisions.scenarios import ScenarioService
    from assetops_backend.mini_decisions.store import PostgresMiniDecisionStore
    from assetops_backend.mini_decisions_api import build_mini_decisions_router
    from assetops_backend.mini_depth.read import MiniDepthRead

WRITE_KEYS = {"schema_version", "id", "opportunity_id", "scenario_id", "recorded_at"}


def api(engine, t, s, *, who="principal", grant=None) -> TestClient:
    registry = SimpleNamespace(
        tenant=lambda: SimpleNamespace(id=t),
        imported=lambda code: SimpleNamespace(id=s, site_code=CODE, site_type="MINIGRID") if code == CODE else None)
    principal = principal_for(t, s) if who == "principal" else who
    app = FastAPI()
    app.include_router(build_mini_decisions_router(
        None, registry, command_access=lambda r, c: grant, principal=lambda r, c: principal,
        opportunities=service(engine), gate=lambda code, a, b: (True, "open")))
    return TestClient(app)


def links_count(engine) -> int:
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM mini_opportunity_scenario_link")).scalar_one()


def test_association_retry_scope_and_latest_compatible_head(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    project(engine)
    svc = service(engine)
    oid = page(svc, t, s)["rows"][0]["opportunity"]["id"]
    who = principal_for(t, s)
    scenarios = ScenarioService(PostgresMiniDecisionStore(engine), MiniDepthRead(engine, link_rows_on))
    pins = selected_pins(engine, t, s)
    _, fits = scenarios.create(t, s, who, load_command("w403-u5-lnk-01", pins))
    _, tariff = scenarios.create(t, s, who, tariff_command("w403-u5-lnk-02"))
    client = api(engine, t, s)
    route = f"/api/sites/{CODE}/opportunities/{oid}/scenario-links"

    created = client.post(route, json=link_body("w403-u5-lnk-03", oid, fits["id"]))
    assert created.status_code == 201 and set(created.json()) == WRITE_KEYS
    body = created.json()
    assert (body["schema_version"], body["opportunity_id"], body["scenario_id"]) == (
        "mini-opportunity-scenario-write-1", oid, fits["id"])
    assert body["recorded_at"].endswith("Z") and len(body["recorded_at"].split(".")[1]) == 7
    # Exact retry: the original body with 200; changed content under the same key: 409; nothing new is stored.
    again = client.post(route, json=link_body("w403-u5-lnk-03", oid, fits["id"]))
    assert again.status_code == 200 and again.json() == body
    changed = client.post(route, json=link_body("w403-u5-lnk-03", oid, tariff["id"]))
    assert changed.status_code == 409 and changed.json()["detail"]["code"] == "DECISION_DUPLICATE_KEY"
    assert links_count(engine) == 1

    # Path and body scope.
    foreign = uuid4()
    r = client.post(f"/api/sites/{CODE}/opportunities/{foreign}/scenario-links",
                    json=link_body("w403-u5-lnk-04", foreign, fits["id"]))
    assert r.status_code == 404 and r.json()["detail"] == {"code": "DECISION_NOT_FOUND",
                                                           "message": "No decision with this ID at this Site."}
    assert client.post(f"/api/sites/{CODE}/opportunities/nope/scenario-links",
                       json=link_body("w403-u5-lnk-05", oid, fits["id"])).status_code == 404
    r = client.post(route, json=link_body("w403-u5-lnk-06", oid, uuid4()))
    assert r.status_code == 422 and r.json()["detail"]["code"] == "DECISION_LINK_SCOPE_INVALID"
    r = client.post(route, json=link_body("w403-u5-lnk-07", uuid4(), fits["id"]))  # body ID differs from path
    assert r.status_code == 422 and r.json()["detail"]["code"] == "DECISION_INPUT_INVALID"
    for bad in ({**link_body("w403-u5-lnk-08", oid, fits["id"]), "extra": 1},
                {**link_body("w403-u5-lnk-08", oid, fits["id"]), "schema_version": "mini-decision-link-command-1"},
                link_body("short", oid, fits["id"])):
        assert client.post(route, json=bad).json()["detail"]["code"] == "DECISION_INPUT_INVALID"
    r = client.post(route, json=link_body("w403-u5-lnk-09", oid, fits["id"], kind="USER"))
    assert r.status_code == 403 and r.json()["detail"]["code"] == "DECISION_USER_AUTH_REQUIRED"
    r = client.post(route, json=link_body("w403-u5-lnk-10", oid, fits["id"], attestation="service=x;job=j;rule=r"))
    assert r.status_code == 422 and r.json()["detail"]["code"] == "DECISION_ATTESTATION_INVALID"
    # Scope and grant precede the body: a non-JSON body is still 403 without the grant or the principal.
    for refused in (api(engine, t, s, grant=403), api(engine, t, s, who=None),
                    api(engine, t, s, who=DecisionPrincipal("SERVICE", "service:w403-fixture", t, uuid4(),
                                                            GRANT_PREFIX + "service:w403-fixture"))):
        r = refused.post(route, content=b"not json")
        assert r.status_code == 403 and r.json()["detail"]["code"] == "DECISION_WRITE_FORBIDDEN"
    assert links_count(engine) == 1

    # The latest scenario head at the cutoff decides compatibility; the association itself never changes.
    k1 = now(engine)
    assert detail(svc, t, s, oid, k1)["opportunity"]["scenario_id"] == fits["id"]
    status, _ = scenarios.correct(t, s, who, fits["id"], {
        **load_command("w403-u5-lnk-11", pins[1:]), "supersedes_revision_id": fits["revision_id"],
        "correction_reason": "Drop the first pinned day."})
    assert status == 201
    k2 = now(engine)
    later = detail(svc, t, s, oid, k2)
    assert later["opportunity"]["scenario_id"] is None and codes(later)[-1] == "SCENARIO_BASIS_MISMATCH"
    assert [(x["scenario_id"], x["selected"], x["compatible"]) for x in later["scenario_links"]] == [
        (fits["id"], True, False)]
    assert detail(svc, t, s, oid, k1)["scenario_links"][0]["compatible"] is True
    # An incompatible scenario is still stored as authored intent and becomes the selected association.
    stored = client.post(route, json=link_body("w403-u5-lnk-12", oid, tariff["id"]))
    assert stored.status_code == 201 and links_count(engine) == 2
    latest = detail(svc, t, s, oid)
    assert [(x["scenario_id"], x["selected"], x["compatible"]) for x in latest["scenario_links"]] == [
        (tariff["id"], True, False), (fits["id"], False, False)]
    assert len(DAYS) == len(pins) == 5
