"""W5-04a V1b: the domain-work routes for an EV Site - readiness-28 refusal order over HTTP, readiness-7/30 foreign
session and evidence refusals with zero writes, and the EV detail/index wire.

`.agent/W5-04-build-spec.md` "Frozen contract" (Command/read, refusal order), readiness rulings 7, 27, 28 and 30.
The EV Finding is W2-05b's registered `interrupted` replay (`test_w504_ev_intent_postgres.ev`). Producer K0 route
and clock tests (rulings 8/29) belong to the V1b producer, not this file. Requires ASSETOPS_TEST_DATABASE_URL naming a
`*_test` database.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_w504_ev_intent_postgres import (EV_INVALID, EV_LINK, chain, counts, ev, ev_action,  # noqa: F401
                                              ev_intent, members)

    from assetops_backend.domain_work_api import build_domain_work_router
    from assetops_backend.work import domain_action as d
    from assetops_backend.work.composition import build_domain_action_read_service, build_domain_intent_service
    from assetops_backend.work_api import W401_FIXTURE_SERVICE_PRINCIPAL_ID, WorkGate

BASE = "/api/sites/{code}/domain-work"


class Api:
    def __init__(self, ev) -> None:
        self.svc = build_domain_intent_service(URL)
        self.reads = build_domain_action_read_service(URL)
        self.code = ev.code
        scope = {ev.code: (ev.code, ev.t, ev.s), ev.code.lower(): (ev.code, ev.t, ev.s)}.get
        gate = WorkGate(scope, principal=lambda r, c: W401_FIXTURE_SERVICE_PRINCIPAL_ID)
        app = FastAPI()
        app.include_router(build_domain_work_router(self.svc, gate, reads=self.reads))
        self.client = TestClient(app)

    def post(self, suffix: str, body):
        return self.client.post(BASE.format(code=self.code) + "/actions" + suffix, json=body)

    def get(self, path: str, **params):
        return self.client.get(BASE.format(code=self.code) + path, params=params)

    def close(self) -> None:
        self.svc._store.dispose()
        self.reads._reads.dispose()


def refused(response, status: int, code: str, message: str) -> None:
    assert response.status_code == status, response.text
    assert response.json() == {"detail": {"code": code, "message": message}}, response.text


def test_ev_refusal_order_over_http(ev) -> None:
    """Readiness 28: neutral malformed shape before an unknown Action, 404 for a valid shared shape with malformed EV
    criteria or missing `session_ids`, the EV literal for the same body against the resolved EV Action, then the EV
    link literal for a foreign session or evidence ID (readiness 7/30); only the root is ever written."""
    own, valid = members(ev)
    api = Api(ev)
    try:
        refused(api.post("", {**ev_action(ev), "domain": "ev"}), 422, "DOMAIN_INTENT_INVALID",
                d.NEUTRAL_DOMAIN_INVALID)
        first = api.post("", ev_action(ev))
        assert first.status_code == 201, first.text
        aid = first.json()["id"]
        unknown = str(uuid4())
        rows = [{"key": k, "label": label, "required_evidence": req} for k, label, req in d.EV_CRITERIA]
        two = ev_intent(ev, [own], valid[:1], criteria=rows[:2])
        no_sessions = ev_intent(ev, [own], valid[:1])
        del no_sessions["basis"]["session_ids"]
        refused(api.post(f"/{unknown}/intents", {**two, "criteria": "three"}), 422, "DOMAIN_INTENT_INVALID",
                d.NEUTRAL_INTENT_INVALID)
        refused(api.post(f"/{unknown}/case-links", {"case_id": "x"}), 422, "DOMAIN_INTENT_INVALID",
                d.NEUTRAL_CASE_LINK_INVALID)
        for body in (two, no_sessions):
            refused(api.post(f"/{unknown}/intents", body), 404, "ACTION_NOT_FOUND", d.MESSAGES["ACTION_NOT_FOUND"])
            refused(api.post("/not-a-uuid/intents", body), 404, "ACTION_NOT_FOUND", d.MESSAGES["ACTION_NOT_FOUND"])
            refused(api.post(f"/{aid}/intents", body), 422, "DOMAIN_INTENT_INVALID", EV_INVALID)
        foreign = str(uuid4())
        refused(api.post(f"/{aid}/intents", ev_intent(ev, [own, foreign], valid[:1])), 422,
                "DOMAIN_INTENT_LINK_INVALID", EV_LINK)
        refused(api.post(f"/{aid}/intents", ev_intent(ev, [own], [valid[0], foreign])), 422,
                "DOMAIN_INTENT_LINK_INVALID", EV_LINK)
        assert counts(ev.engine) == [1, 0, 0]
    finally:
        api.close()


def test_ev_detail_and_index_wire(ev) -> None:
    """The K1 wire shapes for EV: `domain-action-intent-read-1` with three PENDING results and the EV summary row in
    `site-domain-action-index-1`."""
    own, valid = members(ev)
    api = Api(ev)
    try:
        created = api.post("", ev_action(ev)).json()
        empty = api.get(f"/actions/{created['id']}")
        assert empty.status_code == 200, empty.text
        assert (empty.json()["intent"], empty.json()["results"]) == (None, None)
        declared = api.post(f"/{created['id']}/intents", ev_intent(ev, [own], valid))
        assert declared.status_code == 201, declared.text
        body = api.get(f"/actions/{created['id']}").json()
        assert set(body) == {"schema_version", "site_code", "action", "known_at", "status", "intent", "results",
                             "links", "source_provenance", "selection_token"}
        assert body["schema_version"] == "domain-action-intent-read-1" and body["action"]["domain"] == "EV_CHARGING"
        assert body["intent"]["basis"]["session_ids"] == [own] and body["intent"]["basis"]["accepted_evidence_ids"] == valid
        assert [r["result"] for r in body["results"]] == ["PENDING"] * 3
        assert all(r["evidence_ids"] == [] for r in body["results"])
        raised = body["action"]["raised_at"]
        index = api.get("/action-index", **{"from": raised[:10] + "T00:00:00Z", "to": raised[:10] + "T23:59:59Z"})
        assert index.status_code == 200, index.text
        row = next(r for r in index.json()["rows"] if r["action_id"] == created["id"])
        assert (row["domain"], row["state"], row["criterion_summary"]) == (
            "EV_CHARGING", "OPEN", "A complete witnessed session and no repeat fault")
    finally:
        api.close()
