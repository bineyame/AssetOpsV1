"""3C0a (spec §5, §6, §9; R9, R12-R14, P5, P6, P9, MB2): the seven account routes over an in-memory store.

`create_app(accounts=...)` with `DATABASE_URL` unset; the client talks https (the cookie is `Secure` by default),
http only for the `off` case (R12a).
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from assetops_backend.accounts.service import AccountService
from assetops_backend.config import ConfigurationError
from test_3c0a_accounts_service import PW, Clock, MemoryStore

ROUTES = [("POST", "/api/auth/sign-in"), ("POST", "/api/auth/sign-out"), ("GET", "/api/auth/me"),
          ("GET", "/api/organisation/people"), ("GET", "/api/organisation/role-grants"),
          ("POST", "/api/organisation/role-grants"),
          ("POST", "/api/organisation/role-grants/00000000-0000-0000-0000-000000000000/removal")]
POSTS = [path for method, path in ROUTES if method == "POST"]


class World:
    def __init__(self) -> None:
        self.store, self.clock = MemoryStore(), Clock()
        self.svc = AccountService(self.store, clock=self.clock)
        self.tenant = self.store.add_tenant("acme", "Acme Power")
        self.site = self.store.add_site(self.tenant, "KOBO-001")
        self.exec_id = self.svc.onboard_create("acme", "amina@acme.example", "Amina", PW, executive=True)
        self.joseph = self.svc.onboard_create("acme", "joseph@acme.example", "Joseph", PW, executive=False)


@pytest.fixture()
def env(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("ASSETOPS_SESSION_COOKIE_SECURE", raising=False)
    return monkeypatch


def _app(world: World | None):
    from assetops_backend.main import create_app
    return create_app(accounts=None if world is None else world.svc)


@pytest.fixture()
def world(env) -> World:
    return World()


@pytest.fixture()
def client(world: World) -> TestClient:
    return TestClient(_app(world), base_url="https://testserver")


def _cookie(response) -> tuple[str, dict[str, str]]:
    """(value, {attribute name lower case: value lower case}) of the one Set-Cookie header (P9)."""
    [header] = response.headers.get_list("set-cookie")
    first, *rest = [part.strip() for part in header.split(";")]
    name, value = first.split("=", 1)
    assert name == "assetops_session"
    attrs = {}
    for part in rest:
        key, _, val = part.partition("=")
        attrs[key.strip().lower()] = val.strip().lower()
    return value, attrs


def _sign_in(client: TestClient, email: str = "amina@acme.example", pw: str = PW):
    return client.post("/api/auth/sign-in", json={"email": email, "password": pw})


def _code(response) -> str:
    return response.json()["code"]


# --- the cookie -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("setting, secure", [(None, True), ("on", True), ("off", False)])
def test_the_cookie_attributes(env, setting, secure) -> None:
    if setting is not None:
        env.setenv("ASSETOPS_SESSION_COOKIE_SECURE", setting)
    world = World()
    client = TestClient(_app(world), base_url="https://testserver" if secure else "http://testserver")
    response = _sign_in(client)
    assert response.status_code == 200, response.text
    value, attrs = _cookie(response)
    assert value and value != "\"\""
    expected = {"httponly": "", "samesite": "strict", "path": "/api", "max-age": "43200"}
    if secure:
        expected["secure"] = ""
    assert attrs == expected
    me = client.get("/api/auth/me")
    assert me.status_code == 200 and me.json()["person"]["person_id"] == str(world.exec_id)
    out = client.post("/api/auth/sign-out", json={})
    assert out.status_code == 204
    cleared, cleared_attrs = _cookie(out)
    assert cleared in ("", "\"\"")
    assert cleared_attrs.pop("max-age") == "0"
    cleared_attrs.pop("expires", None)
    assert cleared_attrs == {k: v for k, v in expected.items() if k != "max-age"}
    assert client.get("/api/auth/me").status_code == 401


def test_a_bad_cookie_setting_refuses_create_app(env) -> None:
    env.setenv("ASSETOPS_SESSION_COOKIE_SECURE", "yes")
    with pytest.raises(ConfigurationError, match="ASSETOPS_SESSION_COOKIE_SECURE must be 'on', 'off' or unset"):
        _app(World())


# --- sign-in refusals -------------------------------------------------------------------------------------------

def test_refused_sign_ins_are_identical(client: TestClient, world: World) -> None:
    world.svc.onboard_create("acme", "peter@acme.example", "Peter", PW, executive=False)
    world.clock.advance(seconds=1)  # the status row after the ACTIVE one (state is the latest row by time)
    world.svc.onboard_set_status("peter@acme.example", "DISABLED", "left")
    world.store.add_bare_account(world.tenant, "nocred@acme.example", "No Cred", world.clock.now)
    answers = [_sign_in(client, email, pw) for email, pw in (
        ("nobody@acme.example", PW), ("amina@acme.example", PW + "!"), ("not an email", PW),
        ("peter@acme.example", PW), ("nocred@acme.example", PW), ("amina@acme.example", PW + "z" * 120))]
    assert {r.status_code for r in answers} == {401}
    assert len({r.content for r in answers}) == 1
    assert answers[0].json() == {"code": "SIGN_IN_REFUSED", "message": "The email or password is not right.",
                                 "words": {"key": "accounts.sign_in_refused", "params": {}}}
    assert all("set-cookie" not in r.headers for r in answers)
    headers = [{k: v for k, v in r.headers.items() if k != "content-length"} for r in answers]
    assert all(h == headers[0] for h in headers)


def test_the_sixth_attempt_is_429_with_minutes_in_params(client: TestClient, world: World) -> None:
    for _ in range(5):
        assert _sign_in(client, pw="wrong password!").status_code == 401
    locked = _sign_in(client)
    assert locked.status_code == 429
    assert locked.json() == {"code": "SIGN_IN_LOCKED", "message": "Too many attempts. Try again in a few minutes.",
                             "words": {"key": "accounts.sign_in_locked", "params": {"minutes": 15}}}


# --- generic refusals -------------------------------------------------------------------------------------------

@pytest.mark.parametrize("path", POSTS)
def test_a_form_body_is_415_on_every_post(client: TestClient, path: str) -> None:
    response = client.post(path, data={"email": "a@b"})
    assert response.status_code == 415 and _code(response) == "JSON_REQUIRED"
    assert response.json()["message"] == "Send the request as JSON."


def _bad(response, field: str) -> None:
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "ACCOUNTS_BAD_REQUEST"
    assert response.json()["words"] == {"key": "accounts.accounts_bad_request", "params": {"field": field}}
    assert response.json()["message"] == f"The request is not complete: {field}."


@pytest.mark.parametrize("path", POSTS)
def test_unknown_keys_and_bodies_are_422_on_every_post(client: TestClient, path: str) -> None:
    _bad(client.post(path, json={"actor": "x", "zeta": 1, "email": "a@b", "password": PW, "person_id": "x",
                                 "role": "ANALYST"}), "actor")
    _bad(client.post(path, content=b"{not json", headers={"Content-Type": "application/json"}), "body")
    _bad(client.post(path, json=[1, 2]), "body")
    _bad(client.post(path, content=json.dumps({"x": "y" * 5 * 1024}).encode(),
                     headers={"Content-Type": "application/json"}), "body")


def test_missing_and_wrong_typed_keys_name_the_field_in_listed_order(client: TestClient) -> None:
    _bad(client.post("/api/auth/sign-in", json={}), "email")
    _bad(client.post("/api/auth/sign-in", json={"email": "a@b"}), "password")
    _bad(client.post("/api/auth/sign-in", json={"email": 5, "password": 5}), "email")
    _bad(client.post("/api/organisation/role-grants", json={"role": "ANALYST"}), "person_id")
    _bad(client.post("/api/organisation/role-grants", json={"person_id": "x", "role": None}), "role")
    _bad(client.post("/api/organisation/role-grants", json={"person_id": "x", "role": "ANALYST", "site_code": 3}),
         "site_code")


def test_refusal_order_503_415_422_401(env, client: TestClient) -> None:
    grants = "/api/organisation/role-grants"
    # 415 before 401: a form body with no session.
    assert client.post(grants, data={"a": "b"}).status_code == 415
    # 422 before 401.
    _bad(client.post(grants, json={"actor": "me"}), "actor")
    # 401 once the body is right, then the service.
    good = {"person_id": "x", "role": "ANALYST"}
    assert client.post(grants, json=good).status_code == 401 and _code(client.post(grants, json=good)) == "NOT_SIGNED_IN"
    # Sign-out never answers 401.
    assert client.post("/api/auth/sign-out", json={}).status_code == 204
    # 503 before everything when no service is composed.
    bare = TestClient(_app(None), base_url="https://testserver")
    assert bare.post(grants, data={"a": "b"}).status_code == 503


def test_cache_control_no_store_on_all_seven_routes(client: TestClient, world: World) -> None:
    for method, path in ROUTES:  # refusals and the anonymous sign-out
        response = client.request(method, path, json={} if method == "POST" else None)
        assert response.headers.get("cache-control") == "no-store", (path, response.status_code)
    assert _sign_in(client).headers["cache-control"] == "no-store"
    for method, path in ROUTES[2:5]:
        response = client.request(method, path)
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    granted = client.post("/api/organisation/role-grants", json={"person_id": str(world.joseph), "role": "ANALYST"})
    assert granted.status_code == 201 and granted.headers["cache-control"] == "no-store"
    removed = client.post(f"/api/organisation/role-grants/{granted.json()['grant_id']}/removal", json={})
    assert removed.status_code == 201 and removed.headers["cache-control"] == "no-store"
    assert client.post("/api/auth/sign-out", json={}).headers["cache-control"] == "no-store"


def test_a_store_outage_is_503(client: TestClient, world: World, env) -> None:
    def down(*_args, **_kwargs):
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    assert _sign_in(client).status_code == 200  # a cookie, so every route reaches the store
    env.setattr(world.store, "guarded_attempt", down)
    response = _sign_in(client)
    assert response.status_code == 503 and response.json()["code"] == "ACCOUNTS_UNAVAILABLE"
    assert response.json()["message"] == "Sign-in is not available on this server."
    env.setattr(world.store, "session", down)
    env.setattr(world.store, "revoke", down)
    for method, path in ROUTES[1:]:
        if path.endswith("/role-grants") and method == "POST":
            body = {"person_id": "x", "role": "ANALYST"}
        else:
            body = {} if method == "POST" else None
        response = client.request(method, path, json=body)
        assert response.status_code == 503, (path, response.status_code, response.text)


def test_no_accounts_and_no_url_answers_503_on_all_seven(env) -> None:
    from assetops_backend.main import create_app
    bare = TestClient(create_app(), base_url="https://testserver")
    for method, path in ROUTES:
        response = bare.request(method, path, json={} if method == "POST" else None)
        assert response.status_code == 503 and _code(response) == "ACCOUNTS_UNAVAILABLE", (path, response.text)
        assert response.headers["cache-control"] == "no-store"


# --- success shapes ---------------------------------------------------------------------------------------------

def test_success_shapes(client: TestClient, world: World) -> None:
    signed = _sign_in(client)
    body = signed.json()
    assert set(body) == {"person", "tenant", "session_expires_at"}
    assert body["tenant"] == {"slug": "acme", "name": "Acme Power"}
    assert body["session_expires_at"] == "2026-11-20T20:00:00+00:00"
    assert body["person"] == {"person_id": str(world.exec_id), "display_name": "Amina", "email": "amina@acme.example",
                              "status": "ACTIVE",
                              "roles": [{"grant_id": body["person"]["roles"][0]["grant_id"],
                                         "role": "OPERATOR_EXECUTIVE", "site_code": None}]}
    assert client.get("/api/auth/me").json() == body

    world.clock.advance(seconds=1)
    granted = client.post("/api/organisation/role-grants",
                          json={"person_id": str(world.joseph), "role": "SITE_MANAGER", "site_code": "kobo-001"})
    assert granted.status_code == 201, granted.text
    record = granted.json()
    assert record == {"row_id": record["row_id"], "grant_id": record["row_id"], "person_id": str(world.joseph),
                      "display_name": "Joseph", "role": "SITE_MANAGER", "site_code": "KOBO-001", "action": "GRANTED",
                      "by": {"person_id": str(world.exec_id), "display_name": "Amina"},
                      "at": "2026-11-20T08:00:01+00:00"}
    world.clock.advance(seconds=1)
    analyst = client.post("/api/organisation/role-grants",
                          json={"person_id": str(world.joseph), "role": "ANALYST", "site_code": None}).json()
    world.clock.advance(seconds=1)
    removed = client.post(f"/api/organisation/role-grants/{record['grant_id']}/removal", json={})
    assert removed.status_code == 201
    assert removed.json()["action"] == "REMOVED" and removed.json()["grant_id"] == record["grant_id"]

    rows = client.get("/api/organisation/role-grants").json()["rows"]
    assert [r["row_id"] for r in rows] == [removed.json()["row_id"], analyst["row_id"], record["row_id"],
                                           body["person"]["roles"][0]["grant_id"]]
    assert rows[-1]["by"] == {"service": "service:onboarding"}
    people = client.get("/api/organisation/people").json()["people"]
    assert [p["display_name"] for p in people] == ["Amina", "Joseph"]
    assert people[1]["roles"] == [{"grant_id": analyst["grant_id"], "role": "ANALYST", "site_code": None}]


def test_domain_refusals_through_the_routes(client: TestClient, world: World) -> None:
    _sign_in(client, "joseph@acme.example")
    response = client.post("/api/organisation/role-grants", json={"person_id": str(world.exec_id), "role": "ANALYST"})
    assert response.status_code == 403 and _code(response) == "ROLE_REQUIRED"
    assert client.post("/api/organisation/role-grants/not-a-uuid/removal", json={}).status_code == 403
    _sign_in(client)
    for body, status, code in (
            ({"person_id": "not-a-uuid", "role": "ANALYST"}, 404, "PERSON_NOT_FOUND"),
            ({"person_id": str(world.joseph), "role": "WIZARD"}, 422, "ROLE_UNKNOWN"),
            ({"person_id": str(world.joseph), "role": "SITE_MANAGER"}, 422, "ROLE_SITE_RULE"),
            ({"person_id": str(world.joseph), "role": "SITE_MANAGER", "site_code": "NOPE"}, 404, "SITE_NOT_FOUND")):
        response = client.post("/api/organisation/role-grants", json=body)
        assert (response.status_code, _code(response)) == (status, code)
    removal = client.post("/api/organisation/role-grants/not-a-uuid/removal", json={})
    assert (removal.status_code, _code(removal)) == (404, "GRANT_NOT_FOUND")
    client.post("/api/organisation/role-grants", json={"person_id": str(world.joseph), "role": "ANALYST"})
    again = client.post("/api/organisation/role-grants", json={"person_id": str(world.joseph), "role": "ANALYST"})
    assert again.status_code == 409 and again.json()["message"] == "Joseph already holds this role."


def test_me_without_a_tenant_row_is_503(client: TestClient, world: World) -> None:
    """MB2: the tenant is never invented."""
    _sign_in(client)
    del world.store.tenants[world.tenant]
    response = client.get("/api/auth/me")
    assert response.status_code == 503 and _code(response) == "ACCOUNTS_UNAVAILABLE"


def test_a_lone_surrogate_password_gets_the_one_401_body(client: TestClient, world: World) -> None:
    def raw(email: str):  # the JSON escape `\\ud800` decodes to a lone surrogate `str` on the server
        body = ('{"email": "%s", "password": "\\ud800aaaaaaaaaaaaaa"}' % email).encode("ascii")
        return client.post("/api/auth/sign-in", content=body, headers={"content-type": "application/json"})
    known, unknown = raw("amina@acme.example"), raw("nobody@acme.example")
    assert known.status_code == 401 and _code(known) == "SIGN_IN_REFUSED"
    assert unknown.status_code == 401 and unknown.content == known.content
