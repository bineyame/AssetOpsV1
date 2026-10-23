"""W6-01a (A1): the global Incidents root `GET /api/work/incidents` over real Postgres (`global-work-index-1`).

`.agent/W6-01-build-spec.md` section 1 (wire, parser, refusals, envelope, incident row), section 3.1 (A1Q G1-G3 and
the Q3-Q9 rulings) and section 4 (fixture producer and clocks). Rows are written by `tools/w601_seed.py` through the
real W4 `WorkService` with the server-side fixture principal and the ordered write clock from
`--clock 2026-10-22T12:00:00Z`; reads construct `PostgresGlobalWorkRead(..., test_read_clock_override=...)` directly
(current `12:00:02Z`, historical `known_at=12:00:00Z`). Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` DB.
"""

from __future__ import annotations

import base64
import importlib.util
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

REPO = Path(__file__).resolve().parents[2]
CLOCK = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)
READ_NOW = CLOCK + timedelta(seconds=2)
WINDOW = {"from": "2026-10-15T00:00:00Z", "to": "2026-10-22T00:00:00Z"}
KEY = "a1" * 32
ROW_KEYS = {"site_code", "site_name", "site_id", "site_code_key", "case_id", "code", "kind", "revision_id", "title",
            "narrative", "occurred_at", "created_at", "recorded_at", "state", "owner", "asset_id", "asset_label",
            "incident_id", "linked_request_codes", "finding_links", "action_links", "source_provenance", "links"}
ENVELOPE = {"schema_version", "scope", "window", "known_at", "status", "coverage", "total_count", "state_counts", "rows",
            "next_cursor", "selection_token"}

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.global_work_api import build_global_work_router
    from assetops_backend.work.adapters.postgres_global_read import PostgresGlobalWorkRead
    from assetops_backend.work.composition import _link_read_ports
    from assetops_backend.work.global_index import CURSOR_KEY_ENV, GlobalWorkIndexService

    _spec = importlib.util.spec_from_file_location("w601_seed", REPO / "tools" / "w601_seed.py")
    seedmod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(seedmod)


@pytest.fixture()
def key(monkeypatch):
    monkeypatch.setenv(CURSOR_KEY_ENV, KEY)


def seed(fixture: str) -> dict:
    out = seedmod.seed(URL, fixture, CLOCK)
    out["tenants"] = {s["tenant"]: s["tenant_id"] for s in out["sites"]}
    out["by_title"] = {}
    return out


class Api:
    """The global router over a private reader; `at` is the A1Q Q6 constructor-only read clock."""

    def __init__(self, tenant: str | None, at: datetime | None = READ_NOW, *, deny: tuple[str, ...] = (),
                 authenticate=None, url: str | None = None, service: bool = True) -> None:
        self.at, self.calls = at, 0

        def clock() -> datetime:
            self.calls += 1
            return self.at

        self.read = PostgresGlobalWorkRead(url or URL, link_rows=build_link_rows_reader(), ports=_link_read_ports(),
                                           test_read_clock_override=None if at is None else clock)
        app = FastAPI()
        kwargs = {} if authenticate is None else {"authenticate": authenticate}
        app.include_router(build_global_work_router(
            GlobalWorkIndexService(self.read) if service else None, lambda: tenant,
            access=lambda request, code: 403 if code in deny else None, **kwargs))
        self.client = TestClient(app)

    def get(self, **params):
        query = {**WINDOW, **params}
        return self.client.get("/api/work/incidents", params={k: v for k, v in query.items() if v is not None})

    def ok(self, **params) -> dict:
        response = self.get(**params)
        assert response.status_code == 200, response.text
        return response.json()

    def close(self) -> None:
        self.read.dispose()


def refusal(response, status: int, code: str, message: str) -> None:
    assert response.status_code == status, response.text
    assert response.json() == {"detail": {"code": code, "message": message, "rows": None, "total_count": None}}


def cursor_payload(cursor: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))


def encode(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def query(known_at: str) -> str:
    return "&".join(f"{k}={quote(v, safe='')}" for k, v in (*WINDOW.items(), ("known_at", known_at)))


# --- key, scope and tenants ---------------------------------------------------------------------------------------

def test_missing_and_malformed_cursor_key_is_503(store, monkeypatch) -> None:  # noqa: F811
    info = seed("incidents")
    api = Api(info["tenants"]["demo"])
    try:
        monkeypatch.delenv(CURSOR_KEY_ENV, raising=False)
        refusal(api.get(), 503, "WORK_STORE_UNAVAILABLE", "Work records could not be read or saved.")
        for bad in ("zz" * 32, "a1" * 31, "a1" * 33, ""):
            monkeypatch.setenv(CURSOR_KEY_ENV, bad)
            refusal(api.get(), 503, "WORK_STORE_UNAVAILABLE", "Work records could not be read or saved.")
        monkeypatch.setenv(CURSOR_KEY_ENV, KEY)
        assert api.ok()["total_count"] == 6
    finally:
        api.close()


def test_authorized_denied_site_and_two_tenants(store, key) -> None:  # noqa: F811
    info = seed("incidents")
    demo, other = info["tenants"]["demo"], info["tenants"]["w601-other"]
    full, denied, foreign = Api(demo), Api(demo, deny=("KOBO-002",)), Api(other)
    try:
        body, part, theirs = full.ok(), denied.ok(), foreign.ok()
    finally:
        for api in (full, denied, foreign):
            api.close()
    assert set(body) == ENVELOPE and body["schema_version"] == "global-work-index-1"
    assert body["scope"]["tenant_id"] == demo and body["scope"]["authorized_site_count"] == 2
    assert body["scope"]["covered_site_count"] == 2 and body["total_count"] == 6 and body["status"] == "CURRENT"
    assert [s["site_code"] for s in body["coverage"]["sites"]] == ["KOBO-001", "KOBO-002"]
    assert body["coverage"]["state"] == "COMPLETE" and body["coverage"]["reason"] is None
    assert {s["state"] for s in body["coverage"]["sites"]} == {"COVERED"}
    assert "Other tenant incident" not in {r["title"] for r in body["rows"]}
    # A denied Site is silently excluded from rows, counts, coverage and the access basis (no list 403/404).
    assert part["total_count"] == 4 and {r["site_code"] for r in part["rows"]} == {"KOBO-001"}
    assert part["scope"]["authorized_site_count"] == 1 and part["scope"]["access_basis"] != body["scope"]["access_basis"]
    assert [s["site_code"] for s in part["coverage"]["sites"]] == ["KOBO-001"]
    assert part["selection_token"] != body["selection_token"]
    # The other tenant reads only its own Site (same Site code, different tenant and Site UUID).
    assert theirs["total_count"] == 1 and theirs["rows"][0]["title"] == "Other tenant incident"
    assert theirs["rows"][0]["site_id"] not in {s["site_id"] for s in body["coverage"]["sites"]}


def test_complete_zero_and_empty_scope(store, key) -> None:  # noqa: F811
    info = seed("zero")
    demo = info["tenants"]["demo"]
    zero, nobody, no_tenant = Api(demo), Api(demo, deny=("KOBO-001", "KOBO-002")), Api(None)
    try:
        z, empty, old_empty, none = zero.ok(), nobody.ok(), nobody.ok(known_at="2026-10-22T12:00:00Z"), no_tenant.ok()
    finally:
        for api in (zero, nobody, no_tenant):
            api.close()
    assert z["total_count"] == 0 and z["rows"] == [] and z["next_cursor"] is None and z["status"] == "CURRENT"
    assert z["coverage"]["state"] == "COMPLETE" and len(z["coverage"]["sites"]) == 2
    for e in (empty, old_empty, none):  # EMPTY_SCOPE even with an earlier explicit cutoff; never a null count
        assert e["status"] == "EMPTY_SCOPE" and e["total_count"] == 0 and e["rows"] == []
        assert e["coverage"] == {"state": "EMPTY_SCOPE", "reason": "NO_ACCESSIBLE_SITES", "sites": []}
        assert e["scope"]["authorized_site_count"] == 0 and e["next_cursor"] is None
    assert none["scope"]["tenant_id"] is None


def test_candidates_imported_before_to(store, key) -> None:  # noqa: F811
    """A1Q Q5: a Site imported exactly at `to` is not a candidate; the same Site is one for a later `to`."""
    info = seed("zero")
    demo = info["tenants"]["demo"]
    source = seedmod.read_import_source(str(seedmod.KOBO_SOURCE))
    seedmod.import_site(store, tenant_slug="demo", configured_tenant_slug="demo",
                        source=seedmod.ImportSource(path="var/sites/demo-kobo-003.yaml", sha256=source.sha256,
                                                    record=seedmod.replace(source.record, site_id="KOBO-003")),
                        legacy_documents=(), clock=lambda: datetime(2026, 10, 22, tzinfo=timezone.utc))
    api = Api(demo)
    try:
        before = api.ok()
        later = api.ok(**{"from": "2026-10-16T00:00:00Z", "to": "2026-10-23T00:00:00Z"})
    finally:
        api.close()
    assert [s["site_code"] for s in before["coverage"]["sites"]] == ["KOBO-001", "KOBO-002"]
    assert [s["site_code"] for s in later["coverage"]["sites"]] == ["KOBO-001", "KOBO-002", "KOBO-003"]


# --- rows ---------------------------------------------------------------------------------------------------------

def test_same_time_uuid_tie_and_row_shape(store, key) -> None:  # noqa: F811
    info = seed("incidents")
    api = Api(info["tenants"]["demo"])
    try:
        body = api.ok()
    finally:
        api.close()
    rows = body["rows"]
    sites = {s["site_code"]: s["site_id"] for s in body["coverage"]["sites"]}
    # Every root occurs at --clock minus 2 days 3 hours: the order is site_code_key, then site_id, then case UUID.
    assert {r["occurred_at"] for r in rows} == {"2026-10-20T09:00:00Z"}
    expected = sorted(((r["site_code_key"], r["site_id"], r["case_id"]) for r in rows))
    assert [(r["site_code_key"], r["site_id"], r["case_id"]) for r in rows] == expected
    assert [r["site_code"] for r in rows] == ["KOBO-001"] * 4 + ["KOBO-002"] * 2
    for r in rows:
        assert set(r) == ROW_KEYS and r["kind"] == "INCIDENT" and r["code"].startswith("INC-")
        assert r["site_id"] == sites[r["site_code"]] and r["site_code_key"] == r["site_code"].lower()
        assert r["created_at"].endswith("Z") and len(r["created_at"]) == 20 and r["created_at"] >= "2026-10-22T11:59:00Z"
        assert r["asset_id"] is None and r["asset_label"] is None and r["incident_id"] is None
        assert r["finding_links"] == [] and r["action_links"] == []
        assert r["links"]["site"] == {"label": r["site_name"], "href": f"/sites/{r['site_code']}"}
        assert r["source_provenance"]["classification"] == "UNKNOWN"
    assert body["window"] == {**WINDOW, "bounds": "[from, to)"} and body["known_at"] == "2026-10-22T12:00:02Z"


def test_selected_revision_and_assign(store, key) -> None:  # noqa: F811
    info = seed("incidents")
    written = {w["code"] + w["site_code"]: w for w in info["written"] if w["tenant"] == "demo"}
    api = Api(info["tenants"]["demo"])
    try:
        rows = {r["title"]: r for r in api.ok()["rows"]}
    finally:
        api.close()
    first, corrected = rows["Generator stopped"], rows["Inverter fault confirmed"]
    assert "Inverter fault reported" not in rows
    assert corrected["revision_id"] != written[corrected["code"] + "KOBO-001"]["revision_id"]
    assert corrected["recorded_at"] > corrected["created_at"] and corrected["narrative"] == "Corrected after review."
    # Owner is the latest selected ASSIGN payload assignee, never the event actor.
    assert first["owner"] == "Field team A" and first["state"] == "IN_PROGRESS"
    assert all(r["owner"] is None and r["state"] == "OPEN" for t, r in rows.items() if t != "Generator stopped")
    [request] = [w for w in info["written"] if w["kind"] == "MAINTENANCE_REQUEST"]
    assert first["linked_request_codes"] == [request["code"]]
    assert all(r["linked_request_codes"] == [] for t, r in rows.items() if t != "Generator stopped")


def test_historical(store, key) -> None:  # noqa: F811
    info = seed("historical")
    api = Api(info["tenants"]["demo"])
    try:
        old = api.ok(known_at="2026-10-22T12:00:00Z")
        now = api.ok()
    finally:
        api.close()
    assert old["status"] == "HISTORICAL" and old["known_at"] == "2026-10-22T12:00:00Z" and old["total_count"] == 6
    assert "Generator stopped" in {r["title"] for r in old["rows"]}
    assert now["status"] == "CURRENT" and now["total_count"] == 7
    titles = {r["title"] for r in now["rows"]}
    assert {"Generator stopped twice", "Late incident after the historical cutoff"} <= titles
    assert old["selection_token"] != now["selection_token"]


def test_linked_request_codes_order(store, key) -> None:  # noqa: F811
    """A1Q Q7: scoped request codes whose `incident_id` is this case, ordered `(created_at, id)`, at the cutoff."""
    info = seed("incidents")
    sites = seedmod._existing_sites(URL)
    first = info["written"][0]  # "Generator stopped", the first write (demo KOBO-001)
    assert (first["tenant"], first["site_code"], first["kind"]) == ("demo", "KOBO-001", "INCIDENT")
    writer = seedmod.Writer(URL, seedmod.WriteClock(CLOCK - timedelta(seconds=10)), sites, CLOCK)
    try:
        second = writer.request(seedmod.A, first["case_id"], "Replace starter")
        unlinked = writer.request(seedmod.A, None, "Unlinked request")
    finally:
        writer.close()
    late = seedmod.Writer(URL, seedmod.WriteClock(CLOCK + timedelta(seconds=1)), sites, CLOCK)
    try:
        after = late.request(seedmod.A, first["case_id"], "After the cutoff")
    finally:
        late.close()
    api = Api(info["tenants"]["demo"])
    try:
        old = api.ok(known_at="2026-10-22T12:00:00Z")
        now = api.ok()
    finally:
        api.close()
    [request] = [w for w in info["written"] if w["kind"] == "MAINTENANCE_REQUEST"]
    pick = lambda body: [r for r in body["rows"] if r["case_id"] == first["case_id"]][0]  # noqa: E731
    assert pick(old)["linked_request_codes"] == [request["code"], second["code"]]
    assert pick(now)["linked_request_codes"] == [request["code"], second["code"], after["code"]]
    assert unlinked["code"] not in {c for r in now["rows"] for c in r["linked_request_codes"]}


def test_site_incidents_link_carries_response_known_at(store, key) -> None:  # noqa: F811
    info = seed("incidents")
    api = Api(info["tenants"]["demo"], READ_NOW + timedelta(microseconds=250_000))
    try:
        implicit, explicit = api.ok(limit="5"), api.ok(known_at="2026-10-22T12:00:01Z")
        page_two = api.ok(limit="5", cursor=implicit["next_cursor"])
    finally:
        api.close()
    assert implicit["known_at"] == "2026-10-22T12:00:02Z" and explicit["known_at"] == "2026-10-22T12:00:01Z"
    for body in (implicit, explicit, page_two):
        for r in body["rows"]:
            assert r["links"]["site_incidents"] == {
                "label": "Site incidents",
                "href": f"/sites/{r['site_code']}/work/incidents?{query(body['known_at'])}"}
    assert "from=2026-10-15T00%3A00%3A00Z&to=2026-10-22T00%3A00%3A00Z&known_at=2026-10-22T12%3A00%3A02Z" in (
        implicit["rows"][0]["links"]["site_incidents"]["href"])


def test_read_clock_override_pins_read_at(store, key) -> None:  # noqa: F811
    """A1Q Q6: the constructor-only override is called once per snapshot instead of `clock_timestamp()`."""
    info = seed("incidents")
    pinned = datetime(2026, 10, 22, 12, 0, 2, 123456, tzinfo=timezone.utc)
    api = Api(info["tenants"]["demo"], pinned)
    try:
        body = api.ok()
        assert api.calls == 1 and body["known_at"] == "2026-10-22T12:00:02Z"
        assert api.read.snapshot(lambda gx: gx.read_at) == pinned and api.calls == 2
        refusal(api.get(known_at="2026-10-22T12:00:03Z"), 422, "INVALID_KNOWN_AT",
                "known_at must be UTC and no later than the read time.")
        api.at = datetime(2026, 10, 22, 14, tzinfo=timezone(timedelta(hours=2)))
        with pytest.raises(AssertionError):
            api.read.snapshot(lambda gx: gx.read_at)
    finally:
        api.close()
    db_time = Api(info["tenants"]["demo"], None)  # no override: the DB `clock_timestamp()` of the snapshot
    try:
        before = db_time.read.snapshot(lambda gx: gx.read_at)
        real = db_time.ok()
        after = db_time.read.snapshot(lambda gx: gx.read_at)
    finally:
        db_time.close()
    assert db_time.calls == 0 and before < after
    assert before.strftime("%Y-%m-%dT%H:%M:%SZ") <= real["known_at"] <= after.strftime("%Y-%m-%dT%H:%M:%SZ")


# --- cursor -------------------------------------------------------------------------------------------------------

def test_cursor_mac_and_changed_selection(store, key, monkeypatch) -> None:  # noqa: F811
    info = seed("cursor_change")
    api = Api(info["tenants"]["demo"])
    try:
        one = api.ok(limit="5")
        assert one["total_count"] == 6 and len(one["rows"]) == 5 and one["next_cursor"]
        two = api.ok(limit="5", cursor=one["next_cursor"])
        assert [r["case_id"] for r in two["rows"]] not in [[r["case_id"]] for r in one["rows"]]
        assert len(two["rows"]) == 1 and two["next_cursor"] is None and two["total_count"] == 6
        payload = cursor_payload(one["next_cursor"])
        assert set(payload) == {"v", "route", "filter", "tenant_id", "authorized_site_ids", "access_basis", "from",
                                "to", "known_at", "page_one_mode", "selection_token", "after", "mac"}
        assert KEY not in one["next_cursor"] and KEY not in json.dumps(one)
        bad = "The cursor is not an estate cursor."
        refusal(api.get(limit="5", cursor=encode({**payload, "mac": "0" * 64})), 422, "INVALID_CURSOR", bad)
        refusal(api.get(limit="5", cursor=encode({**payload, "after": payload["after"][:3]})), 422,
                "INVALID_CURSOR", bad)
        refusal(api.get(limit="5", cursor="not-base64!"), 422, "INVALID_CURSOR", bad)
        monkeypatch.setenv(CURSOR_KEY_ENV, "b2" * 32)  # another deployment key: the MAC no longer verifies
        refusal(api.get(limit="5", cursor=one["next_cursor"]), 422, "INVALID_CURSOR", bad)
        monkeypatch.setenv(CURSOR_KEY_ENV, KEY)
        changed = "The work list changed; request page one without a cursor."
        refusal(api.get(limit="5", cursor=one["next_cursor"], **{"from": "2026-10-16T00:00:00Z"}), 409,
                "WORK_BASIS_CHANGED", changed)
        seedmod.seed(URL, "cursor_change", CLOCK, append=True)  # a selected row appended at 12:00:02Z
        api.at = READ_NOW + timedelta(seconds=1)
        refusal(api.get(limit="5", cursor=one["next_cursor"], known_at=None), 409, "WORK_BASIS_CHANGED", changed)
        assert api.ok(limit="5")["total_count"] == 7
    finally:
        api.close()
    denied = Api(info["tenants"]["demo"], deny=("KOBO-002",))
    try:
        refusal(denied.get(limit="5", cursor=one["next_cursor"]), 409, "WORK_BASIS_CHANGED", changed)
    finally:
        denied.close()


def test_continuation_status_follows_page_one(store, key) -> None:  # noqa: F811
    info = seed("incidents")
    api = Api(info["tenants"]["demo"])
    try:
        current = api.ok(limit="5")
        historical = api.ok(limit="5", known_at="2026-10-22T12:00:00Z")
        api.at = READ_NOW + timedelta(minutes=5)  # page two later: K stays the cursor's
        c2 = api.ok(limit="5", cursor=current["next_cursor"])
        h2 = api.ok(limit="5", cursor=historical["next_cursor"])
    finally:
        api.close()
    assert current["status"] == "CURRENT" and c2["status"] == "CURRENT" and c2["known_at"] == current["known_at"]
    assert historical["status"] == "HISTORICAL" and h2["status"] == "HISTORICAL"
    assert h2["known_at"] == "2026-10-22T12:00:00Z"
    assert cursor_payload(current["next_cursor"])["page_one_mode"] == "current"
    assert cursor_payload(historical["next_cursor"])["page_one_mode"] == "historical"


def test_state_counts_cover_full_selection(store, key) -> None:  # noqa: F811
    info = seed("incidents")
    [pump] = [w for w in info["written"] if w["kind"] == "INCIDENT" and w["site_code"] == "KOBO-002"
              and w["tenant"] == "demo"][:1]
    sites = seedmod._existing_sites(URL)
    writer = seedmod.Writer(URL, seedmod.WriteClock(CLOCK - timedelta(seconds=30)), sites, CLOCK)
    try:
        s = sites[seedmod.B]
        writer.svc.post_event(s["tenant"], s["site"], pump["case_id"], {
            "kind": "CLOSE", "occurred_at": seedmod.z(CLOCK - timedelta(days=1)), "payload": {"reason": "Resolved"},
            "actor": dict(seedmod.ACTOR), "idempotency_key": writer._key()}, seedmod.W401_FIXTURE_SERVICE_PRINCIPAL_ID)
    finally:
        writer.close()
    demo = info["tenants"]["demo"]
    api, nobody = Api(demo), Api(demo, deny=("KOBO-001", "KOBO-002"))
    expected = {"OPEN": 4, "IN_PROGRESS": 1, "CLOSED": 1}
    try:
        one = api.ok(limit="5")
        two = api.ok(limit="5", cursor=one["next_cursor"])
        empty = nobody.ok()
    finally:
        api.close()
        nobody.close()
    assert one["total_count"] == 6 and len(one["rows"]) == 5 and len(two["rows"]) == 1
    assert one["state_counts"] == expected and two["state_counts"] == expected
    assert empty["state_counts"] == {"OPEN": 0, "IN_PROGRESS": 0, "CLOSED": 0}


def test_page_two_known_at_wire_second(store, key) -> None:  # noqa: F811
    info = seed("incidents")
    api = Api(info["tenants"]["demo"], READ_NOW + timedelta(microseconds=500_000))
    try:
        one = api.ok(limit="5")
        cursor = one["next_cursor"]
        assert cursor_payload(cursor)["known_at"] == "2026-10-22T12:00:02.500000Z"
        assert one["known_at"] == "2026-10-22T12:00:02Z"
        whole = api.ok(limit="5", cursor=cursor, known_at="2026-10-22T12:00:02Z")
        exact = api.ok(limit="5", cursor=cursor, known_at="2026-10-22T12:00:02.500000Z")
        assert whole["rows"] == exact["rows"] and len(whole["rows"]) == 1 and whole["status"] == "CURRENT"
        changed = "The work list changed; request page one without a cursor."
        for other in ("2026-10-22T12:00:01Z", "2026-10-22T12:00:02.400000Z"):
            refusal(api.get(limit="5", cursor=cursor, known_at=other), 409, "WORK_BASIS_CHANGED", changed)
        api.at = READ_NOW  # the cursor cutoff is now later than the read time
        refusal(api.get(limit="5", cursor=cursor), 409, "WORK_BASIS_CHANGED", changed)
    finally:
        api.close()


# --- refusals -----------------------------------------------------------------------------------------------------

def test_refusals_401_422_503(store, key) -> None:  # noqa: F811
    info = seed("zero")
    demo = info["tenants"]["demo"]
    signed_out = Api(demo, authenticate=lambda request: 401)
    api, down, unwired = Api(demo), Api(demo, url="postgresql+psycopg://x:y@127.0.0.1:1/nothing_test"), Api(
        demo, service=False)
    try:
        r = signed_out.get(limit="0")  # authentication precedes parsing
        refusal(r, 401, "UNAUTHENTICATED", "Sign in to read estate records.")
        assert r.headers["WWW-Authenticate"] == "Bearer"
        window = "from and to must be UTC instants in order, at most 31 days apart."
        for params in ({"from": None}, {"to": "2026-10-21T12:00:00Z"}, {"from": "2026-09-01T00:00:00Z"},
                       {"to": "2026-10-15T00:00:00Z"}, {"from": "2026-10-15T00:00:00+02:00"}):
            refusal(api.get(**params), 422, "INVALID_WINDOW", window)
        r = api.client.get("/api/work/incidents?from=2026-10-15T00:00:00Z&from=2026-10-15T00:00:00Z"
                           "&to=2026-10-22T00:00:00Z")
        refusal(r, 422, "INVALID_WINDOW", window)
        refusal(api.get(known_at="2026-10-22T12:00:00"), 422, "INVALID_KNOWN_AT",
                "known_at must be UTC and no later than the read time.")
        for limit in ("0", "101", "x", "-1"):
            refusal(api.get(limit=limit), 422, "INVALID_LIMIT", "limit must be an integer from 1 to 100.")
        for params in ({"site_id": "KOBO-001"}, {"kind": "all"}, {"lens": "all"}):
            refusal(api.get(**params), 422, "INVALID_CURSOR", "The cursor is not an estate cursor.")
        r = api.client.get("/api/work/incidents", params=[*WINDOW.items(), ("limit", "5"), ("limit", "5")])
        refusal(r, 422, "INVALID_CURSOR", "The cursor is not an estate cursor.")
        for svc in (down, unwired):
            refusal(svc.get(), 503, "WORK_STORE_UNAVAILABLE", "Work records could not be read or saved.")
        # No list 403/404: a denied or unknown Site is never a refusal (see the denied-Site and empty-scope tests).
        assert api.ok()["total_count"] == 0
    finally:
        for a in (signed_out, api, down, unwired):
            a.close()


# --- Site parity (last: the shared Finding runner) ----------------------------------------------------------------

if URL:
    from sqlalchemy import text

    from test_s4_finding_store_postgres import run_case  # noqa: F401
    from test_s6_action_store_postgres import CASES, runner  # noqa: F401
    from test_w401_work_service_postgres import PRINCIPAL, VirtualDbClock, incident, public_finding

    from assetops_backend.finding_api import ACCESS_BASIS
    from assetops_backend.work import model as m
    from assetops_backend.work.adapters import postgres_work_store
    from assetops_backend.work.adapters.postgres_work_read import PostgresWorkRead
    from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore
    from assetops_backend.work.service import WorkService
    from assetops_backend.work.site_index import WorkIndexService, parse_list_request


def test_missing_lineage_matches_site_row(runner, monkeypatch, key) -> None:  # noqa: F811
    """A1Q Q3: a case pinned to a Finding revision absent at K carries the same provenance DTO and Finding link on
    the global row as on the W4 Site list row for the same window and cutoff."""
    run_case(runner, CASES["F01"])
    t, s = runner.tenant, runner.site
    row = public_finding(runner)
    fid, frev = row["finding_id"], row["finding_revision_id"]
    with runner.engine.connect() as c:
        made = c.execute(text("SELECT created_at FROM finding_revision WHERE id = :r"), {"r": frev}).scalar_one()
    early = made.astimezone(timezone.utc) - timedelta(hours=1)
    occurred = early - timedelta(hours=1)
    # TEST-SCOPED bypass of the command cutoff (the W4 commit-4 pattern); the scoped junction FK still holds.
    monkeypatch.setattr(postgres_work_store._Tx, "finding_pairs_in_scope", lambda self, pairs: set(pairs))
    svc = WorkService(PostgresWorkStore(URL, link_rows=build_link_rows_reader(),
                                        test_db_clock_override=VirtualDbClock(early)))
    try:
        _, broken = svc.create_case(t, s, incident("w601-missing", occurred_at=m.iso(occurred),
                                                   finding_links=[{"finding_id": fid, "finding_revision_id": frev}]),
                                    PRINCIPAL)
    finally:
        svc._store.dispose()
    k = early + timedelta(seconds=5)
    assert k < made
    lo = occurred.replace(hour=0, minute=0, second=0, microsecond=0)
    hi = lo + timedelta(days=31)
    window = (lo.strftime("%Y-%m-%dT%H:%M:%SZ"), hi.strftime("%Y-%m-%dT%H:%M:%SZ"))
    site_read = PostgresWorkRead(URL, link_rows=build_link_rows_reader(), ports=_link_read_ports(),
                                 test_read_clock_override=lambda: k + timedelta(seconds=1))
    try:
        site = WorkIndexService(site_read).read(t, s, "KOBO-001", "incidents",
                                                parse_list_request(*window, None, [m.iso(k)], None),
                                                access_basis=ACCESS_BASIS)
    finally:
        site_read.dispose()
    api = Api(str(t), k + timedelta(seconds=1))
    try:
        body = api.ok(**{"from": window[0], "to": window[1], "known_at": m.iso(k)})
    finally:
        api.close()
    [site_row] = [r for r in site["rows"] if r["case_id"] == broken["id"]]
    [global_row] = [r for r in body["rows"] if r["case_id"] == broken["id"]]
    assert global_row["source_provenance"] == site_row["source_provenance"]
    assert global_row["source_provenance"]["classification"] == "UNKNOWN"
    assert "LINK_SELECTION_MISSING" in {x["code"] for x in global_row["source_provenance"]["reasons"]}
    assert global_row["finding_links"] == [{"label": x["label"], "href": x["href"]} for x in site_row["finding_links"]]
    assert global_row["finding_links"] == [{"label": f"Finding {fid[:8]}", "href": None}]
    assert body["status"] == "HISTORICAL"


if URL:
    from test_w202_cold_replay_postgres import chain  # noqa: F401,F811
    from test_w502_domain_intent_postgres import cold  # noqa: F401
    from test_w502_domain_work_links_postgres import assert_global_domain_parity, bind


def test_domain_action_link_matches_w4(cold, key) -> None:  # noqa: F811
    """W5-02a ruling C2: an explicitly bound cold domain Action reaches the global incidents row exactly as W4's
    Site row (href, label, null event, selected IDs/citations, basis); earlier cutoff and unlinked rows unchanged."""
    b = bind(cold)
    assert_global_domain_parity(cold, b, Api, "incidents", b.incident)
