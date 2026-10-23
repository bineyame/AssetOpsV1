"""W5-02a K1a: the domain-work command routes - shared W4 gate order, wire bodies, 201/200 retry and refusals.

`.agent/W5-02-build-spec.md` "Command/read wire" (refusal order) and Architect pre-flight ruling A2. The success
path uses the ordinary cold replay fixture of `test_w502_domain_intent_postgres.py`. Requires
ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_w202_cold_replay_postgres import chain  # noqa: F401
    from test_w401_work_service_postgres import ACTOR
    from test_w502_domain_intent_postgres import (COLD, action_body, cold, counts, head_event, intent_body,  # noqa: F401
                                                  link_body, w4_request)

    from assetops_backend.domain_work_api import build_domain_work_router
    from assetops_backend.main import create_app
    from assetops_backend.work import domain_action as d
    from assetops_backend.work.composition import build_domain_action_read_service, build_domain_intent_service
    from assetops_backend.work.model import MESSAGES
    from assetops_backend.work_api import W401_FIXTURE_SERVICE_PRINCIPAL_ID, WorkGate

BASE = "/api/sites/{code}/domain-work/actions"


class Api:
    def __init__(self, t, s, *, access=None, command_access=None, principal=True, service=True, reads=True) -> None:
        self.svc = build_domain_intent_service(URL) if service else None
        self.reads = build_domain_action_read_service(URL) if reads else None
        scope = {COLD: (COLD, t, s), COLD.lower(): (COLD, t, s)}.get
        kwargs = {"principal": (lambda r, c: W401_FIXTURE_SERVICE_PRINCIPAL_ID) if principal else (lambda r, c: None)}
        if access is not None:
            kwargs["access"] = access
        if command_access is not None:
            kwargs["command_access"] = command_access
        app = FastAPI()
        app.include_router(build_domain_work_router(self.svc, WorkGate(scope, **kwargs), reads=self.reads))
        self.client = TestClient(app)

    def post(self, suffix: str, body, code: str = COLD):
        url = BASE.format(code=code) + suffix
        if body is None:
            return self.client.post(url, content=b"not json", headers={"content-type": "application/json"})
        return self.client.post(url, json=body)

    def get(self, path: str, code: str = COLD, **params):
        return self.client.get(f"/api/sites/{code}/domain-work{path}", params=params)

    def close(self) -> None:
        if self.svc is not None:
            self.svc._store.dispose()
        if self.reads is not None:
            self.reads._reads.dispose()


def refused(response, status: int, code: str, message: str) -> None:
    assert response.status_code == status, response.text
    assert response.json() == {"detail": {"code": code, "message": message}}, response.text


ROUTES = ("", f"/{uuid4()}/intents", f"/{uuid4()}/case-links")


def test_gate_order_before_shape() -> None:
    t, s = uuid4(), uuid4()
    for status, code, message in ((401, "UNAUTHENTICATED", "Sign in to read work."),
                                  (403, "SITE_SCOPE_FORBIDDEN", f"No access to Site '{COLD}'.")):
        api = Api(t, s, access=lambda r, c, v=status: v)
        try:
            for suffix in ROUTES:
                r = api.post(suffix, None)
                refused(r, status, code, message)
                if status == 401:
                    assert r.headers["www-authenticate"] == "Bearer"
        finally:
            api.close()
    api = Api(t, s)
    try:
        for suffix in ROUTES:
            refused(api.post(suffix, None, code="NOPE-001"), 404, "SITE_NOT_FOUND",
                    "No imported Site 'NOPE-001' in this tenant.")
    finally:
        api.close()
    for grant, status, code, message in ((401, 401, "UNAUTHENTICATED", "Sign in to read work."),
                                         (403, 403, "WORK_WRITE_FORBIDDEN", MESSAGES["WORK_WRITE_FORBIDDEN"])):
        api = Api(t, s, command_access=lambda r, c, g=grant: g)
        try:
            for suffix in ROUTES:
                refused(api.post(suffix, None), status, code, message)
        finally:
            api.close()
    for suffix in ROUTES:  # no store: 503 before the principal and the body
        refused(Api(t, s, service=False).post(suffix, None), 503, "WORK_STORE_UNAVAILABLE",
                MESSAGES["WORK_STORE_UNAVAILABLE"])
    api = Api(t, s, principal=False)
    try:
        for suffix in ROUTES:  # absent server SERVICE principal: 403 before the closed shape
            refused(api.post(suffix, None), 403, "WORK_WRITE_FORBIDDEN", MESSAGES["WORK_WRITE_FORBIDDEN"])
    finally:
        api.close()
    api = Api(t, s)
    try:
        for suffix in ROUTES:  # then the closed shape: 422 with the exact cold literal, nothing read
            refused(api.post(suffix, None), 422, "DOMAIN_INTENT_INVALID", d.MESSAGES["DOMAIN_INTENT_INVALID"])
            refused(api.post(suffix, {"actor": dict(ACTOR)}), 422, "DOMAIN_INTENT_INVALID",
                    d.MESSAGES["DOMAIN_INTENT_INVALID"])
    finally:
        api.close()


def test_create_app_mounts_domain_work_routes() -> None:
    """`create_app` mounts the three routes behind the shared gate: an unmounted route would be a bare
    `{"detail":"Not Found"}`; here the registry scope answers a typed refusal (404, or 503 without a product DB)."""
    client = TestClient(create_app(domain_work_principal=lambda r, c: W401_FIXTURE_SERVICE_PRINCIPAL_ID))
    for suffix in ROUTES:
        r = client.post(BASE.format(code="NOPE-404") + suffix, json={})
        assert (r.status_code, r.json()["detail"]["code"]) in ((404, "SITE_NOT_FOUND"),
                                                               (503, "WORK_STORE_UNAVAILABLE")), r.text


def test_wire_201_200_and_refusals(cold) -> None:
    api = Api(cold.t, cold.s)
    try:
        body = action_body(cold)
        first = api.post("", body)
        assert first.status_code == 201, first.text
        created = first.json()
        assert set(created) == {"schema_version", "id", "action_code", "recorded_at"}
        again = api.post("", body)
        assert again.status_code == 200 and again.json() == created
        refused(api.post("", {**body, "title": "Other"}), 409, "DOMAIN_INTENT_CONFLICT",
                d.MESSAGES["DOMAIN_INTENT_CONFLICT"])
        refused(api.post("", action_body(cold, "w502-api-action-02", origin_finding_revision_id=str(uuid4()))),
                422, "DOMAIN_INTENT_LINK_INVALID", d.MESSAGES["DOMAIN_INTENT_LINK_INVALID"])
        refused(api.post("", {**body, "actor": {**ACTOR, "attestation": "nope"}}), 422, "WORK_ATTESTATION_INVALID",
                MESSAGES["WORK_ATTESTATION_INVALID"])
        aid = created["id"]
        refused(api.post(f"/{uuid4()}/intents", intent_body(cold)), 404, "ACTION_NOT_FOUND",
                d.MESSAGES["ACTION_NOT_FOUND"])
        wr = w4_request(cold, "w502-api-request-01")
        lb = link_body(wr["id"], wr["revision"]["id"], head_event(cold, wr["id"]))
        r = api.post(f"/{aid}/case-links", lb)
        assert r.status_code == 201 and r.json()["schema_version"] == "domain-action-case-link-1", r.text
        assert api.post(f"/{aid}/case-links", lb).json() == r.json()
        refused(api.post(f"/{aid}/case-links", {**lb, "case_event_id": wr["revision"]["id"]}), 409,
                "DOMAIN_INTENT_BASIS_CHANGED", d.MESSAGES["DOMAIN_INTENT_BASIS_CHANGED"])
        ib = intent_body(cold, work_case_id=wr["id"])
        r = api.post(f"/{aid}/intents", ib)
        assert r.status_code == 201, r.text
        assert set(r.json()) == {"schema_version", "intent_id", "action_id", "recorded_at", "selection_token"}
        retry = api.post(f"/{aid}/intents", ib)
        assert retry.status_code == 200 and retry.json() == r.json()
        assert counts(cold.engine) == [1, 1, 1]
    finally:
        api.close()


# ---- K1b: GET /actions/{action_id} (domain-action-intent-read-1) ---------------------------------------------------

def read_refused(response, status: int, code: str, message: str) -> None:
    """A refused detail read: the typed refusal with `intent:null,results:null` and no count."""
    assert response.status_code == status, response.text
    assert response.json() == {"detail": {"code": code, "message": message, "intent": None, "results": None}},         response.text


def test_detail_read_gate_refusals_and_wire(cold) -> None:
    path = f"/actions/{uuid4()}"
    for status, code, message in ((401, "UNAUTHENTICATED", "Sign in to read work."),
                                  (403, "SITE_SCOPE_FORBIDDEN", f"No access to Site '{COLD}'.")):
        api = Api(cold.t, cold.s, access=lambda r, c, v=status: v)
        try:
            read_refused(api.get(path, known_at="not-an-instant"), status, code, message)
        finally:
            api.close()
    api = Api(cold.t, cold.s, reads=False)
    try:
        read_refused(api.get(path, code="NOPE-001"), 404, "SITE_NOT_FOUND", "No imported Site 'NOPE-001' in this tenant.")
        read_refused(api.get(path, known_at="bad"), 503, "WORK_STORE_UNAVAILABLE", MESSAGES["WORK_STORE_UNAVAILABLE"])
    finally:
        api.close()
    api = Api(cold.t, cold.s)
    try:
        read_refused(api.get(path, known_at="2026-01-01T00:00:00"), 422, "INVALID_KNOWN_AT",
                     MESSAGES["INVALID_KNOWN_AT"])
        read_refused(api.get(path, known_at="2999-01-01T00:00:00Z"), 422, "INVALID_KNOWN_AT",
                     MESSAGES["INVALID_KNOWN_AT"])  # a future cutoff refuses before the Action lookup
        read_refused(api.get(path), 404, "ACTION_NOT_FOUND", d.MESSAGES["ACTION_NOT_FOUND"])
        read_refused(api.get("/actions/not-a-uuid"), 404, "ACTION_NOT_FOUND", d.MESSAGES["ACTION_NOT_FOUND"])
        created = api.post("", action_body(cold, "w502-api-read-01")).json()
        r = api.get(f"/actions/{created['id']}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert set(body) == {"schema_version", "site_code", "action", "known_at", "status", "intent", "results",
                             "links", "source_provenance", "selection_token"}
        assert body["schema_version"] == "domain-action-intent-read-1" and body["action"]["domain"] == "COLDCHAIN"
        assert (body["intent"], body["results"]) == (None, None) and body["action"]["id"] == created["id"]
        assert body["action"]["action_code"] == created["action_code"] and body["selection_token"].startswith("sha256:")
    finally:
        api.close()
