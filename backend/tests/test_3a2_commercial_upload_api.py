"""3A2 (spec §4 settings, §5, §6 "API, no database"; D-3A2.6, D-3A2.9, D-3A2.15, R2, R3, R7, R8): the upload routes
over the in-memory services, and the RC4 settings check.

A `FastAPI` with only this router; the people are 3C1a's `People`. The expected role lists, codes and words are written
here from the spec (W2).
"""
from __future__ import annotations

import asyncio
import json
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from sqlalchemy.exc import InterfaceError, OperationalError

from assetops_backend.accounts.composition import ACCOUNTS_UNAVAILABLE
from assetops_backend.commercial.composition import UploadSettings, commercial_upload_settings
from assetops_backend.commercial.model import StoreRefused
from assetops_backend.commercial.uploads import MAX_UPLOAD_BYTES
from assetops_backend.commercial_upload_api import build_commercial_upload_router
from assetops_backend.config import ConfigurationError
from assetops_backend.reading_upload_api import _body_within
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.ports import SiteStoreUnavailable
from test_3a2_commercial_upload_service import KOBO, b_bill, b_budget, encode, make_world
from test_3c1a_person_work import People

UNAVAILABLE = (*ACCOUNTS_UNAVAILABLE, OperationalError, InterfaceError, SiteStoreUnavailable, FoundationStoreError)
SITE = f"/api/sites/{KOBO}/commercial-uploads"
ORG = "/api/organisation/commercial-uploads"
UPLOADERS = ["ANALYST", "FINANCE_AND_COMMERCIAL_LEAD"]
DECIDERS = ["FINANCE_AND_COMMERCIAL_LEAD", "OPERATOR_EXECUTIVE"]
NAME = {"x-file-name": "kobo-billing-2026-10.json", "content-type": "application/json"}


@pytest.fixture(scope="module")
def people() -> People:
    p = People()
    p.sign("amina")
    return p


def scope_of(people: People, *, known: bool = True, boom: BaseException | None = None):
    sites = {KOBO: people.kobo, "KISIWA-001": people.kisiwa} if known else {}

    def scope(site_code: str):
        if boom is not None:
            raise boom
        code = site_code.upper()
        return (code, people.acme, sites[code]) if code in sites else None

    return scope


def client(people: People, *, world=None, uploads="world", accounts="people", access=None, scope=None):
    world = world or make_world(people)
    app = FastAPI()
    kwargs = {} if access is None else {"access": access}
    app.include_router(build_commercial_upload_router(
        world.svc if uploads == "world" else uploads, scope or scope_of(people),
        accounts=people.svc if accounts == "people" else accounts, unavailable=UNAVAILABLE, **kwargs))
    c = TestClient(app)
    c.world = world
    return c


def as_(people: People, who: str | None, **headers) -> dict:
    return {**people.cookie(who), **headers}


def post_file(c, people, who, base=SITE, obj=None, dry="true", headers=NAME, query=""):
    data = encode(obj if obj is not None else b_bill())
    return c.post(f"{base}?dry_run={dry}{query}", content=data, headers=as_(people, who, **headers))


def decide(c, people, who, upload_id, body, base=SITE):
    return c.post(f"{base}/{upload_id}/decision", content=json.dumps(body),
                  headers=as_(people, who, **{"content-type": "application/json"}))


def code(response) -> tuple[int, str]:
    return response.status_code, response.json()["code"]


# --- 1: the refusal order, both paths ------------------------------------------------------------------------------

class DownAccounts:
    def resolve(self, token):
        raise OperationalError("SELECT", {}, Exception("down"))


def test_1_site_refusal_order(people) -> None:
    assert code(post_file(client(people, access=lambda r, s: 401), people, "ana")) == (401, "UNAUTHENTICATED")
    assert code(post_file(client(people, access=lambda r, s: 403), people, "ana")) == (403, "SITE_SCOPE_FORBIDDEN")
    assert code(post_file(client(people, scope=scope_of(people, known=False)), people, "ana")) == (
        404, "SITE_NOT_FOUND")
    assert code(post_file(client(people, uploads=None), people, "ana")) == (403, "COMMERCIAL_UPLOAD_OFF")
    assert code(post_file(client(people, accounts=DownAccounts()), people, "ana")) == (
        503, "COMMERCIAL_UPLOAD_UNAVAILABLE")
    c = client(people)
    assert code(post_file(c, people, None)) == (401, "PERSON_REQUIRED")
    assert code(post_file(c, people, "hugo")) == (404, "SITE_NOT_FOUND")
    refused = post_file(c, people, "peter")
    assert code(refused) == (403, "PERSON_ROLE_REQUIRED") and refused.json()["params"] == {"roles": UPLOADERS}
    _request_steps(c, people, SITE)


def test_1_organisation_refusal_order(people) -> None:
    assert code(post_file(client(people, uploads=None), people, "ana", ORG)) == (403, "COMMERCIAL_UPLOAD_OFF")
    assert code(post_file(client(people, accounts=DownAccounts()), people, "ana", ORG)) == (
        503, "COMMERCIAL_UPLOAD_UNAVAILABLE")
    assert code(post_file(client(people, accounts=None), people, "ana", ORG)) == (401, "PERSON_REQUIRED")
    c = client(people)
    assert code(post_file(c, people, None, ORG)) == (401, "PERSON_REQUIRED")
    assert code(post_file(c, people, "peter", ORG)) == (403, "PERSON_ROLE_REQUIRED")
    _request_steps(c, people, ORG)


def _request_steps(c, people, base) -> None:
    def bad(response, field):
        assert code(response) == (422, "UPLOAD_BAD_REQUEST") and response.json()["params"] == {"field": field}

    bad(post_file(c, people, "ana", base, dry="maybe"), "dry_run")
    bad(post_file(c, people, "ana", base, query="&file_name=x.json"), "file_name")
    bad(post_file(c, people, "ana", base, headers={"content-type": "application/json"}), "file_name")
    for name in ("%FF", "a%2Fb.json", "a\\b.json", "%20%20", "x" * 201):
        bad(post_file(c, people, "ana", base, headers={**NAME, "x-file-name": name}), "file_name")
    assert code(post_file(c, people, "ana", base, query="&reader=csv-v9")) == (422, "UPLOAD_READER_UNKNOWN")
    assert code(post_file(c, people, "ana", base, headers={**NAME, "content-type": "text/csv"})) == (
        415, "UPLOAD_UNSUPPORTED_TYPE")
    assert post_file(c, people, "ana", base).status_code == 200
    decision = decide(c, people, "fiona", uuid4(), {"decision": "ACCEPT"}, base)
    assert code(decision) == (404, "UPLOAD_NOT_FOUND")
    assert code(c.post(f"{base}/{uuid4()}/decision", content=b"{}", headers=as_(people, "fiona"))) == (
        415, "JSON_REQUIRED")
    assert code(decide(c, people, "fiona", "not-a-uuid", {"decision": "ACCEPT"}, base)) == (404, "UPLOAD_NOT_FOUND")


# --- 2, 3, 4: roles, the person, the decision body -----------------------------------------------------------------

def test_2_roles(people) -> None:
    c = client(people)
    for who in ("ana", "fiona"):
        assert post_file(c, people, who).status_code == 200, who
    for who in ("peter", "fatma", "amina"):
        refused = post_file(c, people, who)
        assert code(refused) == (403, "PERSON_ROLE_REQUIRED") and refused.json()["params"]["roles"] == UPLOADERS
    first = post_file(c, people, "ana", dry="false")
    assert first.status_code == 201 and first.json()["submitted_role"] == "ANALYST"
    refused = decide(c, people, "ana", first.json()["upload_id"], {"decision": "ACCEPT"})
    assert code(refused) == (403, "PERSON_ROLE_REQUIRED") and refused.json()["params"]["roles"] == DECIDERS
    done = decide(c, people, "amina", first.json()["upload_id"], {"decision": "DECLINE", "reason": "Wrong file."})
    assert done.status_code == 201 and done.json()["decision"]["role"] == "OPERATOR_EXECUTIVE"
    second = post_file(c, people, "fiona", dry="false")
    done = decide(c, people, "fiona", second.json()["upload_id"], {"decision": "ACCEPT"})
    assert done.status_code == 201 and done.json()["state"] == "ACCEPTED"
    listed = c.get(SITE, headers=as_(people, "peter"))
    assert listed.status_code == 200 and len(listed.json()["uploads"]) == 2
    assert c.get(f"{SITE}/{second.json()['upload_id']}", headers=as_(people, "peter")).status_code == 200
    assert code(c.get(ORG, headers=as_(people, "peter"))) == (403, "PERSON_ROLE_REQUIRED")
    assert c.get(ORG, headers=as_(people, "amina")).json() == {"uploads": []}
    hugo = c.get(SITE, headers=as_(people, "hugo"))
    unknown = client(people, scope=scope_of(people, known=False)).get(SITE, headers=as_(people, "fiona"))
    assert hugo.status_code == 404 and hugo.content == unknown.content


def test_3_no_session_with_the_switch_unset(people, monkeypatch) -> None:
    monkeypatch.delenv("ASSETOPS_REQUIRE_PERSON", raising=False)
    c = client(people)
    for response in (post_file(c, people, None), c.get(SITE), c.get(ORG), post_file(c, people, None, ORG),
                     decide(c, people, None, uuid4(), {"decision": "ACCEPT"})):
        assert code(response) == (401, "PERSON_REQUIRED")
        assert response.json()["message"] == "Sign in to continue."


@pytest.mark.parametrize("key", ["actor", "person_id"])
def test_4_a_body_naming_the_actor(people, key) -> None:
    c = client(people)
    upload = post_file(c, people, "ana", dry="false").json()
    response = decide(c, people, "fiona", upload["upload_id"], {"decision": "ACCEPT", key: str(uuid4())})
    assert code(response) == (422, "UPLOAD_DECISION_INVALID") and response.json()["params"] == {"field": key}
    for body, field in (([1], "body"), ({"decision": "MAYBE"}, "decision"), ({}, "decision")):
        response = decide(c, people, "fiona", upload["upload_id"], body)
        assert response.json()["params"] == {"field": field}, body
    big = c.post(f"{SITE}/{upload['upload_id']}/decision", content=b'{"decision": "DECLINE", "reason": "' +
                 b"x" * 5000 + b'"}', headers=as_(people, "fiona", **{"content-type": "application/json"}))
    assert code(big) == (422, "UPLOAD_DECISION_INVALID") and big.json()["params"] == {"field": "body"}


# --- 5, 6, 7: size and type, what responses hold, a store fault ---------------------------------------------------

def test_5_size_and_type(people) -> None:
    c = client(people)
    over = c.post(f"{SITE}?dry_run=true", content=b" " * (MAX_UPLOAD_BYTES + 1), headers=as_(people, "ana", **NAME))
    assert code(over) == (413, "FILE_TOO_LARGE") and over.json()["message"] == "The file is larger than 8 MB."
    # The route reads through `_body_within`, which stops at the first chunk past the limit (no content-length).
    sent: list[int] = []

    async def receive():
        sent.append(1)
        return {"type": "http.request", "body": b" " * 2**20, "more_body": len(sent) < 40}

    request = Request({"type": "http", "method": "POST", "headers": [], "path": SITE, "query_string": b""}, receive)
    assert asyncio.run(_body_within(request, MAX_UPLOAD_BYTES)) is None and len(sent) == 9
    assert code(post_file(c, people, "ana", headers={**NAME, "content-type": "text/csv"})) == (
        415, "UPLOAD_UNSUPPORTED_TYPE")


def test_6_responses(people) -> None:
    c = client(people)
    responses = [post_file(c, people, "ana"), post_file(c, people, "ana", dry="false")]
    upload_id = responses[-1].json()["upload_id"]
    responses += [c.get(SITE, headers=as_(people, "fiona")), c.get(f"{SITE}/{upload_id}", headers=as_(people, "ana")),
                  decide(c, people, "fiona", upload_id, {"decision": "ACCEPT"}), post_file(c, people, "ana"),
                  post_file(c, people, "ana", dry="false"), c.get(SITE), post_file(c, people, "ana", ORG, b_budget())]
    batch = c.world.store.uploads[0].batch
    for response in responses:
        assert response.headers["cache-control"] == "no-store", response.request.url
        assert "C-0412" not in response.text and batch not in response.text and '"batch"' not in response.text
    assert responses[4].json()["result"]["counts"] == responses[0].json()["counts"]


class FaultyStore:
    def __getattr__(self, name):
        return getattr(self.inner, name)

    def __init__(self, inner) -> None:
        self.inner = inner

    def add_upload(self, row) -> None:
        raise StoreRefused("commercial_upload_secret_check")


def test_7_a_store_fault(people) -> None:
    world = make_world(people)
    world.svc._store = FaultyStore(world.store)
    response = post_file(client(people, world=world), people, "ana", dry="false")
    assert code(response) == (500, "COMMERCIAL_STORE_FAULT")
    assert "secret" not in response.text and "commercial_upload" not in response.json()["params"]
    assert response.json()["message"] == "The export could not be kept. Nothing was changed."


# --- 8: the settings (RC4) -----------------------------------------------------------------------------------------

DB = "postgresql+psycopg://u:p@127.0.0.1:55432/"


@pytest.mark.parametrize("switch, name", [(None, "assetops_test"), ("off", "assetops_test"), ("off", None),
                                          (None, None), ("on", "assetops_op_pilot1")])
def test_8_settings_allowed(monkeypatch, switch, name) -> None:
    _env(monkeypatch, switch, key_dir="/keys")
    settings = commercial_upload_settings(None if name is None else DB + name)
    assert settings == UploadSettings("/keys", switch == "on")


@pytest.mark.parametrize("switch, name, key_dir", [
    ("on", "assetops_test", "/keys"), ("on", None, "/keys"), ("off", "assetops_op_pilot1", "/keys"),
    (None, "assetops_op_pilot1", "/keys"), ("off", "ASSETOPS_OP_X", "/keys"), ("on", "ASSETOPS_OP_X", "/keys"),
    ("ON", "assetops_op_pilot1", "/keys"), ("true", "assetops_op_pilot1", "/keys"), ("", "assetops_test", "/keys"),
    ("on", "assetops_test", None), ("off", "assetops_op_pilot1", None)])
def test_8_settings_refused(monkeypatch, switch, name, key_dir) -> None:
    _env(monkeypatch, switch, key_dir=key_dir)
    with pytest.raises(ConfigurationError, match="Real operator data needs its own database"):
        commercial_upload_settings(None if name is None else DB + name)


def test_8_create_app_refuses_first(monkeypatch) -> None:
    from assetops_backend.main import create_app

    _env(monkeypatch, "on", key_dir=None)
    monkeypatch.setenv("DATABASE_URL", DB + "assetops_test")
    with pytest.raises(ConfigurationError, match="Real operator data needs its own database"):
        create_app()


def _env(monkeypatch, switch, *, key_dir) -> None:
    for name, value in (("ASSETOPS_REAL_OPERATOR_DATA", switch), ("ASSETOPS_PSEUDONYM_KEY_DIR", key_dir)):
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)


# --- 9, 10: the file name, an unavailable scope --------------------------------------------------------------------

def test_9_the_file_name_travels_in_a_header(people) -> None:
    c = client(people)
    sent = post_file(c, people, "ana", dry="false", headers={**NAME, "x-file-name": "arrears_%C3%A9t%C3%A9.csv"})
    assert sent.status_code == 201 and sent.json()["file_name"] == "arrears_été.csv"
    assert c.world.store.uploads[0].file_name == "arrears_été.csv"
    assert c.get(SITE, headers=as_(people, "fiona")).json()["uploads"][0]["file_name"] == "arrears_été.csv"
    for query, headers in (("&file_name=x.json", NAME), ("", {"content-type": "application/json"}),
                           ("", {**NAME, "x-file-name": "%FF"})):
        response = post_file(c, people, "ana", dry="false", headers=headers, query=query)
        assert code(response) == (422, "UPLOAD_BAD_REQUEST") and response.json()["params"] == {"field": "file_name"}


@pytest.mark.parametrize("boom", [SiteStoreUnavailable("down"), FoundationStoreError("down")])
def test_10_an_unavailable_scope(people, boom) -> None:
    c = client(people, scope=scope_of(people, boom=boom))
    for response in (post_file(c, people, "ana"), c.get(SITE, headers=as_(people, "ana"))):
        assert code(response) == (503, "COMMERCIAL_UPLOAD_UNAVAILABLE")
        assert response.headers["cache-control"] == "no-store"
