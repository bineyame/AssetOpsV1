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


def test_ev_index_wire_after_a_later_head_and_conflict_409s(ev) -> None:
    """Readiness 53 and review L1 over HTTP: after a later selected head the intent-bearing row keeps its live Finding
    href and the detail reads the same href; the EV 409 conflict literal is the wire body, with zero writes."""
    from test_w504_ev_intent_postgres import _later_head

    own, valid = members(ev)
    api = Api(ev)
    try:
        body = ev_action(ev)
        created = api.post("", body).json()
        aid = created["id"]
        refused(api.post("", {**body, "title": "Other title"}), 409, "DOMAIN_INTENT_CONFLICT",
                "This Action declaration has a newer version; reload it.")
        intent = ev_intent(ev, [own], valid)
        assert api.post(f"/{aid}/intents", intent).status_code == 201
        refused(api.post(f"/{aid}/intents", ev_intent(ev, [own], valid, key="w504-api-second-root")), 409,
                "DOMAIN_INTENT_CONFLICT", "This Action declaration has a newer version; reload it.")
        assert counts(ev.engine) == [1, 1, 0]
        _later_head(ev)
        raised = api.get(f"/actions/{aid}").json()["action"]["raised_at"]
        index = api.get("/action-index", **{"from": raised[:10] + "T00:00:00Z", "to": raised[:10] + "T23:59:59Z"})
        assert index.status_code == 200, index.text
        row = next(r for r in index.json()["rows"] if r["action_id"] == aid)
        detail = api.get(f"/actions/{aid}").json()
        assert row["origin"]["href"] == detail["links"]["finding"]["href"] is not None
        assert index.json()["status"] == "CURRENT" and detail["status"] == "CURRENT"
    finally:
        api.close()


# ==== W5-04a V1b producer (round 3): K0 route/shape and clock refusal (readiness 29) ==============================
# Separate from the two tests above. Drives the non-test producer library `tools/w504_ev_work_cases.py` against the
# real EV routes over W2-05b's `interrupted` replay (the merged registered path; the shifted EV-W504-DEPOT replay is
# blocked, questions Q8-Q10).

if URL:
    import sys as _sys
    from datetime import timedelta as _timedelta
    from pathlib import Path as _Path
    from types import SimpleNamespace as _NS

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[2] / "tools"))
    import w504_ev_work_cases as producer  # noqa: E402

    from sqlalchemy import text  # noqa: E402

    from ev_depth_cases import HI, LO  # noqa: E402


def _ev_reads(ev):
    from assetops_backend.analytics.composition import build_ev_read_service
    from assetops_backend.ev_assessment_api import build_ev_assessment_router
    from assetops_backend.ev_scenarios.service import EvScenarioService
    from assetops_backend.ev_scenarios.store import PostgresEvScenarioStore
    from assetops_backend.ev_scenarios_api import build_ev_scenarios_router
    from assetops_backend.financials.composition import build_ev_site_read_service

    site = _NS(id=ev.s, site_type="EV_CHARGING")
    registry = _NS(imported=lambda code: site if code.upper() == ev.code else None,
                   tenant=lambda: _NS(id=ev.t))
    reads, site_reads = build_ev_read_service(URL), build_ev_site_read_service(URL)
    store = PostgresEvScenarioStore.from_url(URL)
    app = FastAPI()
    app.include_router(build_ev_assessment_router(registry, reads))
    app.include_router(build_ev_scenarios_router(registry, EvScenarioService(store, reads, site_reads)))
    client = TestClient(app)

    def get(path, params):
        response = client.get(path, params=params)
        return response.status_code, response.json()

    def close():
        for closing in (reads.dispose, site_reads.dispose, store.dispose):
            try:
                closing()
            except Exception:  # noqa: BLE001 - teardown keeps going
                pass
    return get, close


def test_producer_k0_route_shape_and_positive_payloads(ev) -> None:
    """Readiness 29: K0 is the public `/ev/financials/scenarios` `window.committed_watermark` (no `known_at`), equal
    to the `/ev/sessions` `window.known_at` with the same bounds; the Finding/session come from that window; the
    producer's exact Action/intent bodies are accepted by the public domain-work routes."""
    own, valid = members(ev)
    get, close = _ev_reads(ev)
    api = Api(ev)
    try:
        status, scenarios = get(f"/api/sites/{ev.code}/ev/financials/scenarios",
                                {"from": producer.text_of(LO), "to": producer.text_of(HI)})
        assert status == 200, scenarios
        assert set(scenarios["window"]) == {"from", "to", "known_at", "committed_watermark"}
        status, sessions = get(f"/api/sites/{ev.code}/ev/sessions",
                               {"from": producer.text_of(LO), "to": producer.text_of(HI)})
        assert status == 200, sessions
        assert "committed_watermark" not in sessions["window"]
        selected = producer.read_k0(get, ev.code, LO, HI)
        assert selected.k0 == producer.instant(scenarios["window"]["committed_watermark"])
        assert selected.k0 == producer.instant(sessions["window"]["known_at"])
        assert (selected.finding_revision_id, selected.session_id.lower()) == (str(ev.revision["id"]), own.lower())
        assert selected.accepted_evidence_ids and set(selected.accepted_evidence_ids) <= {v.lower() for v in valid}
        # Ruling 35: the Action is raised at current DB time (the domain service's raised_at window), after K0.
        with ev.engine.connect() as c:
            raised = c.execute(text("SELECT clock_timestamp()")).scalar_one() - _timedelta(seconds=1)
        posted = producer.action_body(selected, raised, "w504a-producer-action")
        assert (posted["title"], posted["owner_label"], posted["due_at"]) == (
            "Investigate connector 2", "Charging operations", None)
        action = api.post("", posted)
        assert action.status_code == 201, action.text
        body = action.json()
        # The K1 command response carries only identity and clock; the literals are read back from storage below.
        assert set(body) == {"schema_version", "id", "action_code", "recorded_at"}
        declared = producer.instant(body["recorded_at"])
        posted_intent = producer.intent_body(selected, selected.finding_revision_id, declared,
                                             "w504a-producer-intent")
        intent = api.post(f"/{body['id']}/intents", posted_intent)
        assert intent.status_code == 201, intent.text
        assert set(intent.json()) == {"schema_version", "intent_id", "action_id", "recorded_at", "selection_token"}
        wanted = {"finding_revision_id": selected.finding_revision_id, "work_case_id": None, "work_record_id": None,
                  "accepted_evidence_ids": sorted(selected.accepted_evidence_ids),
                  "session_ids": [selected.session_id.lower()]}
        assert posted_intent["basis"] == wanted
        with ev.engine.connect() as c:
            row = c.execute(text(
                "SELECT a.title, a.owner_label, a.due_at, i.basis FROM domain_action a JOIN domain_action_intent i "
                "ON i.action_id = a.id WHERE a.id = :a"), {"a": body["id"]}).one()
        assert (row[0], row[1], row[2]) == ("Investigate connector 2", "Charging operations", None)
        assert row[3] == wanted
        detail = api.get(f"/actions/{body['id']}")
        assert detail.status_code == 200, detail.text
        shown = detail.json()
        assert (shown["action"]["title"], shown["action"]["owner_label"], shown["action"]["due_at"]) == (
            "Investigate connector 2", "Charging operations", None)
        assert shown["intent"]["basis"] == wanted and shown["intent"]["id"] == intent.json()["intent_id"]
    finally:
        api.close()
        close()


def test_producer_refuses_mismatched_window_or_clock(ev) -> None:
    """Readiness 29: a session list read at another cutoff (explicit earlier `known_at`) or other bounds refuses
    preparation; the producer never substitutes a clock."""
    get, close = _ev_reads(ev)
    try:
        bounds = {"from": producer.text_of(LO), "to": producer.text_of(HI)}
        _, scenarios = get(f"/api/sites/{ev.code}/ev/financials/scenarios", bounds)
        k0 = producer.instant(scenarios["window"]["committed_watermark"])
        earlier = producer.iso(k0 - _timedelta(seconds=30))
        status, historical = get(f"/api/sites/{ev.code}/ev/sessions", {**bounds, "known_at": earlier})
        # Either the selector answers the earlier cutoff (its known_at is then not K0) or it refuses that read;
        # in both cases the producer cannot prepare from it.
        assert status in (200, 404, 409, 422), historical
        if status == 200:
            assert producer.instant(historical["window"]["known_at"]) != k0
            with pytest.raises(producer.ProducerRefused):
                producer.cross_check_k0(scenarios, historical, LO, HI)
        _, current = get(f"/api/sites/{ev.code}/ev/sessions", bounds)
        assert producer.cross_check_k0(scenarios, current, LO, HI) == k0
        with pytest.raises(producer.ProducerRefused):
            producer.cross_check_k0(scenarios, current, LO, HI + _timedelta(hours=1))

        def shifted(path, params):  # a sessions read answering another window than the one requested
            status, body = get(path, params)
            if path.endswith("/ev/sessions"):
                body = {**body, "window": {**body["window"], "to": producer.iso(HI + _timedelta(minutes=5))}}
            return status, body
        with pytest.raises(producer.ProducerRefused):
            producer.read_k0(shifted, ev.code, LO, HI)
    finally:
        close()
