"""W4-01 commit 3: the Site-scoped work command routes over real Postgres.

`.agent/W4-01-build-spec.md` "API wire and refusals", Review closure S25/S28, closure 2 Q6/Q28, closure 3 Q28 and
"Run 1 rulings (q1)" / "Run 2 rulings (q2)". The server SERVICE principal is injected server-side
(`W401_FIXTURE_SERVICE_PRINCIPAL_ID`); a client actor ID never authenticates it. Requires
ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from itertools import count
from uuid import UUID, uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, imported, store  # noqa: F401
    from test_w401_work_service_postgres import (ACTOR, BASIS, TABLES, at, counts, event, incident, oprec, plan,
                                                  record, request)

    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.sites.ports import SiteStoreUnavailable
    from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore
    from assetops_backend.work.composition import build_work_detail_service, build_work_index_service
    from assetops_backend.work.model import MESSAGES
    from assetops_backend.work.service import WorkService
    from assetops_backend.work.site_index import encode_cursor
    from assetops_backend.work_api import W401_FIXTURE_SERVICE_PRINCIPAL_ID, build_work_router

ISO = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z$")


def injected_ids():
    """B7: injectable UUID generation for response snapshots (`10000000-...` only under this test factory)."""
    n = count(0x101)
    return lambda: UUID(f"10000000-0000-4000-8000-{next(n):012x}")


class Api:
    def __init__(self, result, *, access=None, command_access=None, principal=True, url=URL, new_id=None,
                 service=True, scope=None) -> None:
        self.t, self.s = result.tenant.id, result.site.id
        self.store = PostgresWorkStore(url, link_rows=build_link_rows_reader())
        svc = WorkService(self.store, **({} if new_id is None else {"new_id": new_id})) if service else None
        scopes = {"KOBO-001": ("KOBO-001", self.t, self.s), "kobo-001": ("KOBO-001", self.t, self.s)}
        self.details = build_work_detail_service(url) if service else None
        self.lists = build_work_index_service(url) if service else None
        kwargs = {"principal": (lambda r, c: W401_FIXTURE_SERVICE_PRINCIPAL_ID) if principal else
                  (lambda r, c: None), "details": self.details, "lists": self.lists}
        if access is not None:
            kwargs["access"] = access
        if command_access is not None:
            kwargs["command_access"] = command_access
        app = FastAPI()
        app.include_router(build_work_router(svc, scope or scopes.get, **kwargs))
        self.client = TestClient(app)

    def post(self, path: str, body, site: str = "KOBO-001"):
        url = f"/api/sites/{site}/work/{path}"
        if body is None:
            return self.client.post(url, content=b"not json", headers={"content-type": "application/json"})
        return self.client.post(url, json=body)

    def ok(self, path: str, body, status: int = 201, site: str = "KOBO-001") -> dict:
        r = self.post(path, body, site)
        assert r.status_code == status, r.text
        return r.json()

    def get(self, case_id: str, *known: str, site: str = "KOBO-001"):
        return self.client.get(f"/api/sites/{site}/work/cases/{case_id}", params=[("known_at", k) for k in known])

    def listing(self, kind: str, site: str = "KOBO-001", **params):
        return self.client.get(f"/api/sites/{site}/work/{kind}", params=params)

    def close(self) -> None:
        self.store.dispose()
        if self.lists is not None:
            self.lists._reads.dispose()
        if self.details is not None:
            self.details._reads.dispose()


@pytest.fixture()
def site(store):  # noqa: F811
    return imported(store)


@pytest.fixture()
def api(site):
    owned = Api(site)
    yield owned
    owned.close()


def refused(response, status: int, code: str, message: str | None = None) -> None:
    assert response.status_code == status, response.text
    detail = response.json()["detail"]
    assert set(detail) == {"code", "message"}, detail  # mutation shape: no rows/total_count
    assert detail["code"] == code, detail
    assert detail["message"] == (message or MESSAGES[code]), detail


def all_routes(case_id: str) -> list[tuple[str, dict]]:
    return [("cases", incident()), (f"cases/{case_id}/events", event("COMMENT", {"text": "n"}, "w401-cmt-001")),
            (f"cases/{case_id}/revisions", {"supersedes_revision_id": str(uuid4()), "title": "t", "narrative": "n",
                                            "reason": "r", "occurred_at": at(minutes=5), "actor": dict(ACTOR),
                                            "idempotency_key": "w401-correct-001"}),
            (f"cases/{case_id}/records", record()), ("plans", plan()), ("operational-records", oprec())]


def test_scope_before_shape_401_403_404(engine, site) -> None:  # noqa: F811
    before = counts(engine)
    case = str(uuid4())
    for status, code, message in ((401, "UNAUTHENTICATED", "Sign in to read work."),
                                  (403, "SITE_SCOPE_FORBIDDEN", "No access to Site 'KOBO-001'.")):
        api = Api(site, access=lambda r, c, s=status: s)
        try:
            for path, _ in all_routes(case):
                r = api.post(path, None)  # malformed body: scope is decided before shape
                refused(r, status, code, message)
                if status == 401:
                    assert r.headers["www-authenticate"] == "Bearer"
        finally:
            api.close()
    api = Api(site)
    try:
        for path, body in all_routes(case):
            refused(api.post(path, None, site="NOPE-001"), 404, "SITE_NOT_FOUND",
                    "No imported Site 'NOPE-001' in this tenant.")
    finally:
        api.close()
    for grant, status, code, message in ((401, 401, "UNAUTHENTICATED", "Sign in to read work."),
                                         (403, 403, "WORK_WRITE_FORBIDDEN", None)):
        api = Api(site, command_access=lambda r, c, g=grant: g)
        try:
            for path, body in all_routes(case):
                refused(api.post(path, body), status, code, message)
        finally:
            api.close()
    # Run 2 reading 2: no server SERVICE principal is 403 before the closed-shape check.
    api = Api(site, principal=False)
    try:
        for path, body in all_routes(case):
            refused(api.post(path, None), 403, "WORK_WRITE_FORBIDDEN")
            refused(api.post(path, body), 403, "WORK_WRITE_FORBIDDEN")
    finally:
        api.close()
    assert counts(engine) == before
    api = Api(site)
    try:
        for path, body in all_routes(case)[1:4]:
            refused(api.post(path, body), 404, "WORK_CASE_NOT_FOUND")
            refused(api.post(path.replace(case, "not-a-uuid"), body), 404, "WORK_CASE_NOT_FOUND")
    finally:
        api.close()
    assert counts(engine) == before


def test_mutation_409_422_and_store_503(engine, site, api) -> None:  # noqa: F811
    inc = api.ok("cases", incident())
    req = api.ok("cases", request())
    before = counts(engine)
    for path, body in all_routes(inc["id"]):
        refused(api.post(path, None), 422, "WORK_INPUT_INVALID")
        refused(api.post(path, {**body, "unexpected": 1}), 422, "WORK_INPUT_INVALID")
    events = f"cases/{inc['id']}/events"
    refused(api.post(events, event("REOPEN", {"reason": "r"}, "w401-reopen-001")), 409, "WORK_TRANSITION_INVALID")
    refused(api.post(events, event("CREATED", {}, "w401-created-001")), 409, "WORK_TRANSITION_INVALID")
    refused(api.post(f"cases/{req['id']}/events", event("OPEN_VERIFICATION", {}, "w401-openv-001")), 409,
            "WORK_TRANSITION_INVALID")
    refused(api.post(f"cases/{req['id']}/events", event("VERIFIED", {}, "w401-verified-001")), 409,
            "WORK_OUTCOME_NOT_SUPPORTED")
    refused(api.post(f"cases/{req['id']}/events", event("NOT_A_KIND", {}, "w401-unknown-001")), 422,
            "WORK_INPUT_INVALID")
    refused(api.post(f"cases/{inc['id']}/records", record()), 422, "WORK_INPUT_INVALID")
    refused(api.post("cases", incident("w401-incident-002", asset_id=str(uuid4()))), 422, "WORK_LINK_SCOPE_INVALID")
    refused(api.post("cases", incident("w401-incident-003", cited_accepted_evidence_ids=[str(uuid4())])), 422,
            "WORK_LINK_SCOPE_INVALID")
    api.ok(f"cases/{req['id']}/events", event("ASSIGN", {"assignee": "lead"}, "w401-assign-001"))
    refused(api.post(f"cases/{req['id']}/events", event("COMPLETE", {"maintenance_record_id": str(uuid4())},
                                                         "w401-complete-001")), 422, "WORK_LINK_SCOPE_INVALID")
    refused(api.post("cases", incident("w401-incident-004", occurred_at=at(minutes=-10))), 422,
            "WORK_OCCURRED_AT_FUTURE")
    refused(api.post("cases", incident("w401-incident-005", occurred_at=at(days=31))), 422,
            "WORK_OCCURRED_AT_TOO_OLD")
    stale = {"supersedes_revision_id": str(uuid4()), "title": "t", "narrative": "n", "reason": "r",
             "occurred_at": at(minutes=5), "actor": dict(ACTOR), "idempotency_key": "w401-correct-009"}
    refused(api.post(f"cases/{inc['id']}/revisions", stale), 409, "WORK_CORRECTION_CONFLICT")
    root = api.ok("plans", plan())
    refused(api.post("plans", plan("w401-plan-002", supersedes_plan_id=str(uuid4()), canonical_plan_id=root["id"],
                                   correction_reason="r")), 409, "WORK_CORRECTION_CONFLICT")
    # S12/S13: no plan or OperationalRecord transition endpoint exists in W4 (an unregistered route, not a 409).
    for path in (f"plans/{root['id']}/events", f"operational-records/{uuid4()}/events"):
        assert api.post(path, {"kind": "ACTIVATE"}).status_code in (404, 405)
    after = counts(engine)
    assert {t: after[t] - before[t] for t in TABLES if after[t] != before[t]} == {
        "work_event": 1, "maintenance_plan": 1}  # only the ASSIGN and the plan root committed
    for unavailable in (Api(site, service=False), Api(site, url=None)):
        try:
            for path, body in all_routes(inc["id"]):
                refused(unavailable.post(path, body), 503, "WORK_STORE_UNAVAILABLE")
        finally:
            unavailable.close()
    assert counts(engine) == after


def test_idempotent_200_same_body(engine, site, api) -> None:  # noqa: F811
    def twice(path: str, body: dict, changed: dict) -> dict:
        first = api.ok(path, body)
        assert api.post(path, body).status_code == 200
        assert api.ok(path, body, 200) == first
        refused(api.post(path, changed), 409, "WORK_EVENT_DUPLICATE_KEY")
        return first

    inc_body, plan_body = incident(), plan()
    inc = twice("cases", inc_body, {**inc_body, "title": "Other title"})
    req = twice("cases", request(), request(narrative="Other narrative"))
    rec = twice(f"cases/{req['id']}/records", record(), record(activity="Other activity"))
    twice(f"cases/{req['id']}/events", event("ASSIGN", {"assignee": "lead"}, "w401-assign-001"),
          event("ASSIGN", {"assignee": "other"}, "w401-assign-001"))
    done = twice(f"cases/{req['id']}/events", event("COMPLETE", {"maintenance_record_id": rec["id"]},
                                                    "w401-complete-001"),
                 event("COMPLETE", {"maintenance_record_id": rec["id"]}, "w401-complete-001",
                       occurred_at=at(minutes=1)))
    assert done["state"] == "COMPLETED"
    corr = {"supersedes_revision_id": inc["revision"]["id"], "title": inc_title(), "narrative": "Corrected note.",
            "reason": "Corrected operator time note", "occurred_at": at(minutes=5), "actor": dict(ACTOR),
            "idempotency_key": "w401-correct-001"}
    rev = twice(f"cases/{inc['id']}/revisions", corr, {**corr, "reason": "Other reason"})
    root = twice("plans", plan_body, {**plan_body, "title": "Other plan"})
    twice("operational-records", oprec(case_id=inc["id"]), oprec(case_id=inc["id"], body="Other body"))
    # A retry after later changes still returns the originally stored body (Run 2 reading 7).
    api.ok(f"cases/{inc['id']}/events", event("COMMENT", {"text": "later"}, "w401-comment-001"))
    assert api.ok("cases", inc_body, 200) == inc and rev["revision_no"] == 2
    assert api.ok("plans", plan_body, 200) == root


def inc_title() -> str:
    return incident()["title"]


def test_user_actor_403_and_service_attestation_422(engine, site, api) -> None:  # noqa: F811
    inc = api.ok("cases", incident())
    before = counts(engine)
    user = {"kind": "USER", "id": "operator-1", "attestation": "I requested inspection."}
    bad = [{**ACTOR, "attestation": "service=other;job=positive-case;rule=w401/1"},
           {**ACTOR, "attestation": "service=w401-fixture;job= ;rule=w401/1"},
           {**ACTOR, "attestation": "service=w401-fixture;job=positive-case"},
           {**ACTOR, "id": "service:other", "attestation": "service=other;job=positive-case;rule=w401/1"},
           {**ACTOR, "id": "w401-fixture"}]
    for path, body in all_routes(inc["id"]):
        refused(api.post(path, {**body, "actor": user}), 403, "WORK_USER_AUTH_REQUIRED")
        for actor in bad:
            refused(api.post(path, {**body, "actor": actor}), 422, "WORK_ATTESTATION_INVALID")
    assert counts(engine) == before


def test_client_authorization_basis_422_and_server_basis_persisted(engine, site, api) -> None:  # noqa: F811
    inc = api.ok("cases", incident())
    req = api.ok("cases", request())
    before = counts(engine)
    for path, body in all_routes(req["id"]):
        for basis in (None, "", BASIS):
            refused(api.post(path, {**body, "actor": {**ACTOR, "authorization_basis": basis}}), 422,
                    "WORK_INPUT_INVALID", "A required work field or UTC time is invalid.")
    assert counts(engine) == before
    rec = api.ok(f"cases/{req['id']}/records", record())
    api.ok(f"cases/{inc['id']}/events", event("COMMENT", {"text": "noted"}, "w401-comment-001"))
    api.ok(f"cases/{inc['id']}/revisions", {"supersedes_revision_id": inc["revision"]["id"], "title": "t",
                                            "narrative": "n", "reason": "r", "occurred_at": at(minutes=5),
                                            "actor": dict(ACTOR), "idempotency_key": "w401-correct-001"})
    api.ok("plans", plan())
    api.ok("operational-records", oprec())
    with engine.connect() as c:
        for table in ("work_case", "work_case_revision", "work_event", "maintenance_record", "maintenance_plan",
                      "operational_record"):
            got = set(c.execute(text(f"SELECT DISTINCT authorization_basis FROM {table}")).scalars())
            assert got == {BASIS}, (table, got)
        assert c.execute(text("SELECT actor_id FROM maintenance_record WHERE id = :i"),
                         {"i": rec["id"]}).scalar_one() == W401_FIXTURE_SERVICE_PRINCIPAL_ID


def test_path_identity_changes_idempotency_hash(engine, site, store) -> None:  # noqa: F811
    other = imported(store, code="OTHER-001")
    api = Api(site)
    api_other = Api(other)
    try:
        body = incident()
        inc = api.ok("cases", body)
        # The hash uses the resolved scoped Site UUID, not the spelling of the code (Run 2 reading 4).
        assert api.ok("cases", body, 200, site="kobo-001") == inc
        moved = api_other.ok("cases", body, site="KOBO-001")  # same body, another Site's UUID
        assert moved["id"] != inc["id"]
        sibling = api.ok("cases", incident("w401-incident-002"))
        comment = event("COMMENT", {"text": "same body"}, "w401-comment-001")
        api.ok(f"cases/{inc['id']}/events", comment)
        api.ok(f"cases/{sibling['id']}/events", comment)
        root = api.ok("plans", plan())
        api.ok("plans", plan("w401-plan-002", supersedes_plan_id=root["id"], canonical_plan_id=root["id"],
                             correction_reason="Name the cadence"))
        with engine.connect() as c:
            cases = dict(c.execute(text("SELECT CAST(id AS text), create_payload_sha256 FROM work_case")).all())
            events = list(c.execute(text("SELECT payload_sha256 FROM work_event WHERE idempotency_key = :k"),
                                    {"k": "w401-comment-001"}).scalars())
            plans = list(c.execute(text("SELECT payload_sha256 FROM maintenance_plan")).scalars())
        assert cases[inc["id"]] != cases[moved["id"]]
        assert len(events) == 2 and len(set(events)) == 2
        assert len(set(plans)) == 2
    finally:
        api.close()
        api_other.close()


def test_plan_record_operational_literal_responses(engine, site) -> None:  # noqa: F811
    api = Api(site, new_id=injected_ids())
    try:
        inc = api.ok("cases", incident())
        assert set(inc) == {"schema_version", "id", "code", "kind", "site_id", "revision", "event", "state",
                            "source_provenance"}
        assert inc["schema_version"] == "work-case-1" and inc["kind"] == "INCIDENT" and inc["state"] == "OPEN"
        assert (inc["id"], inc["revision"], inc["event"]["id"], inc["event"]["kind"]) == (
            "10000000-0000-4000-8000-000000000101", {"id": "10000000-0000-4000-8000-000000000102", "number": 1},
            "10000000-0000-4000-8000-000000000103", "CREATED")
        assert inc["site_id"] == str(site.site.id) and re.fullmatch(r"INC-\d{6}", inc["code"])
        assert ISO.match(inc["event"]["recorded_at"])
        prov = inc["source_provenance"]
        assert prov["classification"] == "UNKNOWN" and prov["state"] == "UNKNOWN"
        assert prov["reasons"] == [{"code": "EMPTY_CITATION_SET", "accepted_evidence_ids": []}]
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", prov["basis_sha256"])
        req = api.ok("cases", request(incident_id=inc["id"]))
        assert re.fullmatch(r"WR-\d{6}", req["code"]) and req["kind"] == "MAINTENANCE_REQUEST"
        rec = api.ok(f"cases/{req['id']}/records", record())
        assert set(rec) == {"schema_version", "id", "case_id", "recorded_at", "outcome"}
        assert (rec["schema_version"], rec["case_id"], rec["outcome"]) == ("maintenance-record-1", req["id"],
                                                                          "UNVERIFIED")
        ev = api.ok(f"cases/{req['id']}/events", event("ASSIGN", {"assignee": "maintenance-lead"}, "w401-assign-001"))
        assert set(ev) == {"schema_version", "case_id", "event", "state", "revision_id"}
        assert set(ev["event"]) == {"id", "kind", "payload", "occurred_at", "recorded_at"}
        assert (ev["schema_version"], ev["state"], ev["revision_id"], ev["event"]["payload"]) == (
            "work-event-1", "IN_PROGRESS", req["revision"]["id"], {"assignee": "maintenance-lead"})
        rev = api.ok(f"cases/{inc['id']}/revisions", {
            "supersedes_revision_id": inc["revision"]["id"], "title": inc_title(),
            "narrative": "Corrected occurrence note; cause remains unknown.", "reason": "Corrected operator time note",
            "occurred_at": at(minutes=5), "actor": dict(ACTOR), "idempotency_key": "w401-correct-001"})
        assert rev == {"case_id": inc["id"], "revision_id": rev["revision_id"], "revision_no": 2,
                       "supersedes_revision_id": inc["revision"]["id"]}
        root = api.ok("plans", plan())
        assert set(root) == {"schema_version", "id", "canonical_plan_id", "public_code", "state", "recorded_at"}
        assert (root["schema_version"], root["state"], root["canonical_plan_id"]) == (
            "maintenance-plan-1", "DRAFT", root["id"])
        assert re.fullmatch(r"PM-\d{6}", root["public_code"]) and ISO.match(root["recorded_at"])
        v2 = api.ok("plans", plan("w401-plan-002", supersedes_plan_id=root["id"], canonical_plan_id=root["id"],
                                  correction_reason="Name the cadence"))
        assert v2["id"] != root["id"] and {k: v2[k] for k in ("canonical_plan_id", "public_code", "state")} == {
            k: root[k] for k in ("canonical_plan_id", "public_code", "state")}
        op = api.ok("operational-records", oprec(case_id=inc["id"]))
        assert set(op) == {"schema_version", "id", "canonical_record_id", "public_code", "state", "recorded_at"}
        assert (op["schema_version"], op["state"], op["canonical_record_id"]) == (
            "operational-record-1", "SUBMITTED", op["id"])
        assert re.fullmatch(r"REC-\d{6}", op["public_code"]) and ISO.match(op["recorded_at"])
        op2 = api.ok("operational-records", oprec("w401-oprec-002", supersedes_record_id=op["id"],
                                                  canonical_record_id=op["id"], correction_reason="Added the time"))
        assert op2["id"] != op["id"] and (op2["canonical_record_id"], op2["public_code"], op2["state"]) == (
            op["id"], op["public_code"], "SUBMITTED")
    finally:
        api.close()


# ---- Run 3 rulings 8-9 / q3 test placement: the case detail read ---------------------------------------------


def _minus_one_us(stamp: str) -> str:
    then = datetime.fromisoformat(stamp.replace("Z", "+00:00")) - timedelta(microseconds=1)
    return then.isoformat().replace("+00:00", "Z")


def test_detail_omitted_historical_and_future_known_at(engine, site) -> None:  # noqa: F811
    api = Api(site, new_id=injected_ids())
    try:
        inc = api.ok("cases", incident(occurred_at=at(minutes=30)))
        cid = inc["id"]
        cmt = api.ok(f"cases/{cid}/events", event("COMMENT", {"text": "Checked the panel."}, "w401-cmt-001"))
        response = api.get(cid)
        assert response.status_code == 200, response.text
        now = response.json()
        assert list(now) == ["schema_version", "site_code", "case", "selected_revision", "finding_links",
                             "action_links", "cited_accepted_evidence_ids", "events", "records", "source_provenance",
                             "coverage"]
        assert (now["schema_version"], now["site_code"]) == ("work-case-detail-1", "KOBO-001")
        assert now["case"] == {"id": cid, "code": inc["code"], "kind": "INCIDENT", "asset_id": None,
                               "occurred_at": now["case"]["occurred_at"], "created_at": inc["event"]["recorded_at"],
                               "state": "OPEN", "incident_id": None}
        rev = now["selected_revision"]
        assert list(rev) == ["id", "revision_no", "supersedes_revision_id", "title", "narrative", "reason",
                             "recorded_at", "actor_kind", "actor_id", "occurred_at"]
        assert (rev["id"], rev["revision_no"], rev["supersedes_revision_id"], rev["actor_kind"], rev["actor_id"],
                rev["reason"]) == (inc["revision"]["id"], 1, None, "SERVICE", "service:w401-fixture", None)
        assert [e["kind"] for e in now["events"]] == ["CREATED", "COMMENT"]
        assert now["events"][1] == {"id": cmt["event"]["id"], "kind": "COMMENT",
                                    "payload": {"text": "Checked the panel."},
                                    "occurred_at": cmt["event"]["occurred_at"],
                                    "recorded_at": cmt["event"]["recorded_at"], "actor_kind": "SERVICE",
                                    "actor_id": "service:w401-fixture"}
        assert (now["finding_links"], now["action_links"], now["cited_accepted_evidence_ids"], now["records"]) == (
            [], [], [], [])
        assert now["coverage"] == {"state": "COMPLETE", "reason": None}
        prov = now["source_provenance"]
        assert (prov["classification"], prov["state"], prov["evidence_ids"]) == ("UNKNOWN", "UNKNOWN", [])
        assert prov["reasons"] == [{"code": "EMPTY_CITATION_SET", "accepted_evidence_ids": []}]
        assert ISO.match(now["case"]["created_at"]) and all(ISO.match(e["recorded_at"]) for e in now["events"])

        # Historical cutoff at CREATED: the event prefix only, the same case and revision.
        created = inc["event"]["recorded_at"]
        then = api.get(cid, created)
        assert then.status_code == 200, then.text
        assert [e["id"] for e in then.json()["events"]] == [inc["event"]["id"]]
        assert then.json()["selected_revision"] == rev and then.json()["case"]["state"] == "OPEN"
        # Before creation the case is not found (no disclosure); a cutoff later than the read time is 422.
        refused(api.get(cid, _minus_one_us(created)), 404, "WORK_CASE_NOT_FOUND")
        refused(api.get(cid, at(minutes=-10)), 422, "INVALID_KNOWN_AT")
        refused(api.get(cid, "2026-10-06T16:11:00"), 422, "INVALID_KNOWN_AT")  # no UTC offset
        refused(api.get(cid, "yesterday"), 422, "INVALID_KNOWN_AT")
        refused(api.get(cid, created, created), 422, "INVALID_KNOWN_AT")  # repeated
    finally:
        api.close()


def test_detail_scoped_404_and_refusal_shape(engine, site, store) -> None:  # noqa: F811
    other = imported(store, code="KOBO-002")
    api = Api(site)
    try:
        cid = api.ok("cases", incident())["id"]
        refused(api.get(str(uuid4())), 404, "WORK_CASE_NOT_FOUND")
        refused(api.get("not-a-uuid"), 404, "WORK_CASE_NOT_FOUND")
        refused(api.get(cid, site="NOPE-001"), 404, "SITE_NOT_FOUND", "No imported Site 'NOPE-001' in this tenant.")
        # The same case ID under another Site of the tenant is not disclosed.
        foreign = Api(site, scope={"KOBO-001": ("KOBO-002", other.tenant.id, other.site.id)}.get)
        try:
            refused(foreign.get(cid), 404, "WORK_CASE_NOT_FOUND")
        finally:
            foreign.close()
        for status, code, message in ((401, "UNAUTHENTICATED", "Sign in to read work."),
                                      (403, "SITE_SCOPE_FORBIDDEN", "No access to Site 'KOBO-001'.")):
            denied = Api(site, access=lambda r, c, s=status: s)
            try:
                refused(denied.get(cid), status, code, message)
            finally:
                denied.close()
        # The read needs Site read access only: a refused write grant and no SERVICE principal still read.
        reader = Api(site, command_access=lambda r, c: 403, principal=False)
        try:
            assert reader.get(cid).status_code == 200
        finally:
            reader.close()
        down = Api(site, url="postgresql+psycopg://assetops:wrong@127.0.0.1:1/none_test")
        try:
            refused(down.get(cid), 503, "WORK_STORE_UNAVAILABLE")
        finally:
            down.close()
        absent = Api(site, service=False)
        try:
            refused(absent.get(cid), 503, "WORK_STORE_UNAVAILABLE")
        finally:
            absent.close()
    finally:
        api.close()


def test_scoped_site_outage_is_503(engine, site) -> None:  # noqa: F811
    """q3 reading 5 (replace): a Site scope/storage outage is 503 WORK_STORE_UNAVAILABLE on reads and writes,
    never a raw 500, an empty result or a 404; nothing is written."""
    def outage(code):
        raise SiteStoreUnavailable("site store down")

    before = counts(engine)
    api = Api(site, scope=outage)
    try:
        refused(api.get(str(uuid4())), 503, "WORK_STORE_UNAVAILABLE")
        refused(api.post("cases", incident()), 503, "WORK_STORE_UNAVAILABLE")
    finally:
        api.close()
    assert counts(engine) == before


def list_refused(response, status: int, code: str, message: str | None = None) -> None:
    """q7-5: every list refusal is `{detail:{code,message,rows:null,total_count:null}}` - never 200 empty."""
    assert response.status_code == status, response.text
    detail = response.json()["detail"]
    assert detail == {"code": code, "message": message or MESSAGES[code], "rows": None, "total_count": None}, detail


def test_list_refusal_has_null_rows_and_total(engine, site) -> None:  # noqa: F811
    """Commit 4 (Run 3 ruling 9, q7-5): both literal list paths refuse with null rows and count, in the order
    access -> Site scope -> window -> limit -> known_at -> cursor -> snapshot; store outages are 503."""
    window = {"from": "2026-10-06T00:00:00Z", "to": "2026-10-07T00:00:00Z"}
    for status, code, message in ((401, "UNAUTHENTICATED", "Sign in to read work."),
                                  (403, "SITE_SCOPE_FORBIDDEN", "No access to Site 'KOBO-001'.")):
        api = Api(site, access=lambda r, c, s=status: s)
        try:
            for kind in ("incidents", "maintenance"):
                list_refused(api.listing(kind, **{"from": "bad"}), status, code, message)  # scope before shape
        finally:
            api.close()
    api = Api(site)
    try:
        for kind in ("incidents", "maintenance"):
            list_refused(api.listing(kind, site="NOPE-001", **{"from": "bad"}), 404, "SITE_NOT_FOUND",
                         "No imported Site 'NOPE-001' in this tenant.")
            list_refused(api.listing(kind, to=window["to"]), 422, "INVALID_WINDOW",
                         "`from` is required as a UTC instant; choose a bounded window of at most 31 days.")
            list_refused(api.listing(kind, **{"from": window["from"], "to": "nope"}), 422, "INVALID_WINDOW",
                         "`to` is not an ISO-8601 instant.")
            list_refused(api.listing(kind, **{"from": "2026-10-06T00:00:00+03:00", "to": window["to"]}), 422,
                         "INVALID_WINDOW", "`from` must be a UTC instant (Z or +00:00).")
            list_refused(api.listing(kind, **{"from": window["to"], "to": window["from"]}), 422, "INVALID_WINDOW",
                         "`from` must be before `to`.")
            list_refused(api.listing(kind, **{"from": "2026-09-01T00:00:00Z", "to": window["to"]}), 422,
                         "INVALID_WINDOW", "The window may span at most 31 days.")
            for bad in ("0", "101", "five"):
                list_refused(api.listing(kind, limit=bad, **window), 422, "INVALID_LIMIT",
                             "`limit` must be an integer from 1 to 100.")
            list_refused(api.listing(kind, known_at="2999-01-01T00:00:00Z", **window), 422, "INVALID_KNOWN_AT")
            list_refused(api.client.get(f"/api/sites/KOBO-001/work/{kind}", params=[
                ("from", window["from"]), ("to", window["to"]), ("known_at", "2026-10-06T00:00:00Z"),
                ("known_at", "2026-10-06T00:00:01Z")]), 422, "INVALID_KNOWN_AT")
            list_refused(api.listing(kind, cursor="not-a-cursor", **window), 422, "INVALID_CURSOR",
                         "The cursor is not a work-list cursor.")
            # A well-formed cursor for another kind/scope is a changed basis (409), never a silent page.
            other = "maintenance" if kind == "incidents" else "incidents"
            foreign = encode_cursor({"v": 1, "tenant_id": str(api.t), "site_id": str(api.s), "kind": other,
                                     "from": "2026-10-06T00:00:00.000000Z", "to": "2026-10-07T00:00:00.000000Z",
                                     "known_at": "2026-10-06T12:00:00.000000Z", "selection_token": "sha256:0",
                                     "after": ["2026-10-06T10:00:00.000000Z", str(uuid4())]})
            list_refused(api.listing(kind, cursor=foreign, **window), 409, "WORK_BASIS_CHANGED",
                         "The work list changed; request page one without a cursor.")
            ok = api.listing(kind, **window)
            assert ok.status_code == 200 and ok.json()["total_count"] == 0 and ok.json()["rows"] == [], ok.text
    finally:
        api.close()

    def outage(code):
        raise SiteStoreUnavailable("site store down")

    for api in (Api(site, scope=outage), Api(site, service=False)):
        try:
            for kind in ("incidents", "maintenance"):
                list_refused(api.listing(kind, **window), 503, "WORK_STORE_UNAVAILABLE")
        finally:
            api.close()
