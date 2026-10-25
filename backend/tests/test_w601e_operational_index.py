"""W6-01e (E1): the global Operational records root `GET /api/work/operational-records?kind=`.

`.agent/W6-01-build-spec.md` section 1 (operational row), the E1 card, section 3.1 (A1Q2 R3, X2) and the "E1-E2
pre-flight rulings" P-E1-1..10. Rows are written by `tools/w601_seed.py --fixture operational` (P-E1-9) through the
real W4 `WorkService` and the ordered write clock from `--clock 2026-10-21T12:00:00Z`, and read through the
constructor read-clock override. Unreachable consistency states use a rolled-back controlled mutation only.
Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` DB.
"""

from __future__ import annotations

import base64
import importlib.util
import json
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

REPO = Path(__file__).resolve().parents[2]
CLOCK = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)  # P-E1-9: the operational fixture clock
READ_NOW = CLOCK + timedelta(seconds=5)  # after the correction at `--clock + 1s`
HISTORICAL = "2026-10-21T12:00:00Z"  # before the correction: the original log is selected
WINDOW = {"from": "2026-10-14T00:00:00Z", "to": "2026-10-21T00:00:00Z"}
BROAD = {"from": "2026-10-13T00:00:00Z", "to": "2026-10-21T00:00:00Z"}
KEY = "e1" * 32
ROUTE = "operational-records"
KINDS = ("OPERATOR_LOG", "MANUAL_READING", "SHIFT_NOTE", "SITE_VISIT")
ROW_KEYS = {"site_code", "site_name", "site_id", "site_code_key", "canonical_record_id", "root_id", "head_id", "code",
            "kind", "body", "root_occurred_at", "occurred_at", "recorded_at", "period_end", "actor_kind", "actor_id",
            "quantity", "unit", "source_document_sha256", "case_id", "case_kind", "case_code", "state",
            "supersedes_record_id", "correction_reason", "source_provenance", "links", "site_domain"}
ENVELOPE = {"schema_version", "scope", "window", "known_at", "status", "coverage", "total_count", "state_counts", "rows",
            "next_cursor", "selection_token"}
WIRE_SECOND = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
CHANGED = "The work list changed; request page one without a cursor."
BAD_CURSOR = "The cursor is not an estate cursor."
DOWN = "Work records could not be read or saved."

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text

    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.global_work_api import build_global_work_router
    from assetops_backend.work.adapters.postgres_global_read import GlobalReadTx, PostgresGlobalWorkRead
    from assetops_backend.work.composition import _link_read_ports
    from assetops_backend.work.global_index import (CURSOR_KEY_ENV, GlobalWorkIndexService, GlobalWorkRefusal,
                                                    encode_global_cursor, parse_global_request)

    _spec = importlib.util.spec_from_file_location("w601_seed", REPO / "tools" / "w601_seed.py")
    seedmod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(seedmod)


@pytest.fixture()
def key(monkeypatch):
    monkeypatch.setenv(CURSOR_KEY_ENV, KEY)


def seed(fixture: str = "operational", clock: datetime = CLOCK) -> dict:
    out = seedmod.seed(URL, fixture, clock)
    out["tenants"] = {s["tenant"]: s["tenant_id"] for s in out["sites"]}
    out["scopes"] = {(s["tenant"], s["site_code"]): s for s in out["sites"]}
    return out


class Api:
    """The global router over a private reader; `at` is the A1Q Q6 constructor-only read clock."""

    def __init__(self, tenant: str | None, at: datetime | None = READ_NOW, *, deny: tuple[str, ...] = (),
                 service: bool = True, url: str | None = None) -> None:
        self.read = PostgresGlobalWorkRead(url or URL, link_rows=build_link_rows_reader(), ports=_link_read_ports(),
                                           test_read_clock_override=None if at is None else (lambda: at))
        app = FastAPI()
        app.include_router(build_global_work_router(
            GlobalWorkIndexService(self.read) if service else None, lambda: tenant,
            access=lambda request, code: 403 if code in deny else None))
        self.client = TestClient(app)

    def get(self, root: str = ROUTE, window: dict | None = None, **params):
        query = {**(window or WINDOW), **params}
        return self.client.get(f"/api/work/{root}", params={k: v for k, v in query.items() if v is not None})

    def ok(self, root: str = ROUTE, window: dict | None = None, **params) -> dict:
        response = self.get(root, window, **params)
        assert response.status_code == 200, response.text
        return response.json()

    def close(self) -> None:
        self.read.dispose()


def read(tenant: str, at: datetime = READ_NOW, window: dict | None = None, **params) -> dict:
    api = Api(tenant, at)
    try:
        return api.ok(ROUTE, window, **params)
    finally:
        api.close()


def all_rows(tenant: str, at: datetime = READ_NOW, window: dict | None = None, **params) -> list[dict]:
    api = Api(tenant, at)
    try:
        body = api.ok(ROUTE, window, limit="5", **params)
        rows = list(body["rows"])
        while body["next_cursor"]:
            body = api.ok(ROUTE, window, limit="5", cursor=body["next_cursor"], **params)
            rows.extend(body["rows"])
        return rows
    finally:
        api.close()


def refusal(response, status: int, code: str, message: str) -> None:
    assert response.status_code == status, response.text
    assert response.json() == {"detail": {"code": code, "message": message, "rows": None, "total_count": None}}


def cursor_body(cursor: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode("utf-8"))


def remac(cursor: str, **changes) -> str:
    body = {k: v for k, v in cursor_body(cursor).items() if k != "mac"}
    return encode_global_cursor({**body, **changes}, bytes.fromhex(KEY))


def counts(tenant: str, at: datetime = READ_NOW, **params) -> dict[str, int]:
    out = {"all": read(tenant, at, **params)["total_count"]}
    for kind in KINDS:
        out[kind] = read(tenant, at, kind=kind, **params)["total_count"]
    return out


def later_writer(info: dict, seconds: int):
    sites = {(s["tenant"], s["site_code"]): {"tenant": s["tenant_id"], "site": s["site_id"],
                                             "site_code": s["site_code"]} for s in info["sites"]}
    return seedmod.Writer(URL, seedmod.WriteClock(CLOCK + timedelta(seconds=seconds)), sites, CLOCK)


def stored(info: dict, kind: str, site_code: str, tenant: str = "demo") -> list[dict]:
    tid = info["tenants"][tenant]
    return [r for r in info["operational_records"]
            if r["kind"] == kind and r["site_code"] == site_code and r["tenant_id"] == tid]


class SameConnection:
    """The read port over one caller-owned connection, so a rolled-back controlled mutation is visible."""

    def __init__(self, c) -> None:
        self.c = c

    def snapshot(self, work):
        return work(GlobalReadTx(self.c, READ_NOW, build_link_rows_reader(), _link_read_ports()))


def request(**params):
    return parse_global_request(ROUTE, list({**WINDOW, **params}.items()))


# --- P-E1-10 focused tests ----------------------------------------------------------------------------------------

def test_four_kinds_and_filtered_zero(store, key) -> None:  # noqa: F811
    """All four kinds are stored and selectable; the standard window holds an exact SITE_VISIT filtered zero."""
    info = seed()
    demo = info["tenants"]["demo"]
    body = read(demo)
    assert set(body) == ENVELOPE and body["schema_version"] == "global-work-index-1"
    assert body["state_counts"] is None and body["status"] == "CURRENT" and body["total_count"] == 7
    assert all(set(r) == ROW_KEYS and r["site_domain"] == "MINIGRID" for r in body["rows"])
    zero = read(demo, kind="SITE_VISIT")
    assert zero["total_count"] == 0 and zero["rows"] == [] and zero["next_cursor"] is None
    assert zero["state_counts"] is None and zero["status"] == "CURRENT"
    broad = all_rows(demo, window=BROAD)
    assert sorted({r["kind"] for r in broad}) == sorted(KINDS) and len(broad) == 8
    visit = read(demo, window=BROAD, kind="SITE_VISIT")
    assert visit["total_count"] == 1
    assert visit["rows"][0]["site_code"] == "KOBO-002" and visit["rows"][0]["root_occurred_at"] == "2026-10-13T09:00:00Z"
    assert visit["rows"][0]["state"] == "SUBMITTED" and visit["rows"][0]["actor_id"] == "service:w401-fixture"


def test_kind_filter_before_count_and_cursor(store, key) -> None:  # noqa: F811
    """The filter applies to the selected head before the count, token, sort and page slice (P-E1-2/3)."""
    info = seed()
    demo = info["tenants"]["demo"]
    assert counts(demo) == {"all": 7, "OPERATOR_LOG": 2, "MANUAL_READING": 2, "SHIFT_NOTE": 3, "SITE_VISIT": 0}
    api = Api(demo)
    try:
        page = api.ok(limit="2", kind="SHIFT_NOTE")
        assert page["total_count"] == 3 and len(page["rows"]) == 2
        assert {r["kind"] for r in page["rows"]} == {"SHIFT_NOTE"}
        assert cursor_body(page["next_cursor"])["filter"] == "SHIFT_NOTE"
        two = api.ok(limit="2", kind="SHIFT_NOTE", cursor=page["next_cursor"])
        assert two["total_count"] == 3 and len(two["rows"]) == 1 and two["next_cursor"] is None
        assert two["selection_token"] == page["selection_token"]
        # absent and explicit `all` normalise to `all`, including page two
        first = api.ok(limit="5")
        assert cursor_body(first["next_cursor"])["filter"] == "all"
        explicit = api.ok(limit="5", kind="all")
        assert explicit["selection_token"] == first["selection_token"]
        for second in (api.ok(limit="5", kind="all", cursor=first["next_cursor"]),
                       api.ok(limit="5", cursor=explicit["next_cursor"])):
            assert len(second["rows"]) == 2 and second["total_count"] == 7
        tokens = {api.ok(kind=k)["selection_token"] for k in ("all", *KINDS)}
        assert len(tokens) == 5
        # sort: selected head `(recorded_at desc, ...)`; the corrected log's head is the latest write
        rows = all_rows(demo)
        assert [r["recorded_at"] for r in rows] == sorted((r["recorded_at"] for r in rows), reverse=True)
        assert rows[0]["correction_reason"] == "Log wording corrected after review"
    finally:
        api.close()


def test_correction_head_keeps_root_window(store, key) -> None:  # noqa: F811
    """Root occurrence governs membership and the root code stays; the head supplies kind/body/case (P-E1-3). C1's
    request history stays root-`case_id` membership even when a later head names another case."""
    info = seed()
    demo = info["tenants"]["demo"]
    log = stored(info, "OPERATOR_LOG", "KOBO-001")[0]
    head = next(r for r in info["operational_records"] if r["canonical_record_id"] == log["id"] and r["id"] != log["id"])
    current = {r["root_id"]: r for r in all_rows(demo)}[log["id"]]
    assert current["head_id"] == head["id"] and current["kind"] == "SHIFT_NOTE"
    assert current["code"] == log["code"] and current["root_occurred_at"] == "2026-10-18T09:00:00Z"
    assert current["occurred_at"] == "2026-10-18T09:00:00Z" and current["supersedes_record_id"] == log["id"]
    assert current["correction_reason"] == "Log wording corrected after review"
    assert current["body"].startswith("Shift note at KOBO-001") and current["case_kind"] == "INCIDENT"
    past = {r["root_id"]: r for r in all_rows(demo, known_at=HISTORICAL)}[log["id"]]
    assert past["head_id"] == log["id"] and past["kind"] == "OPERATOR_LOG" and past["correction_reason"] is None
    assert past["supersedes_record_id"] is None and past["body"].startswith("Operator log at KOBO-001")
    assert read(demo, known_at=HISTORICAL)["status"] == "HISTORICAL"
    assert counts(demo, known_at=HISTORICAL) == {"all": 7, "OPERATOR_LOG": 3, "MANUAL_READING": 2, "SHIFT_NOTE": 2,
                                                 "SITE_VISIT": 0}
    # a correction (later head) outside the window keeps the root in its root-occurrence window
    reading = stored(info, "MANUAL_READING", "KOBO-001")[0]
    incident = next(w for w in info["written"] if w["kind"] == "INCIDENT")
    req = next(w for w in info["written"] if w["kind"] == "MAINTENANCE_REQUEST")
    writer = later_writer(info, 2)
    try:
        writer.post_operational_record(
            ("demo", "KOBO-001"), incident["case_id"], "Manual reading at KOBO-001: Fuel tank dip: 198 L",
            kind="MANUAL_READING", occurred_at=CLOCK - timedelta(days=1), quantity="198", unit="L",
            correction={"supersedes_record_id": reading["id"], "canonical_record_id": reading["id"],
                        "correction_reason": "Case corrected to the incident"})
    finally:
        writer.close()
    row = {r["root_id"]: r for r in all_rows(demo)}[reading["id"]]
    assert row["root_occurred_at"] == "2026-10-18T09:02:00Z" and row["occurred_at"] == "2026-10-20T12:00:00Z"
    assert row["case_id"] == incident["case_id"] and row["case_kind"] == "INCIDENT"
    assert reading["id"] not in {r["root_id"] for r in all_rows(demo, window={"from": "2026-10-20T00:00:00Z",
                                                                               "to": "2026-10-21T00:00:00Z"})}
    scope = info["scopes"][("demo", "KOBO-001")]
    reads = PostgresGlobalWorkRead(URL, link_rows=build_link_rows_reader(), ports=_link_read_ports(),
                                   test_read_clock_override=lambda: READ_NOW)
    try:
        history = reads.snapshot(lambda gx: gx.case_operational_records(
            uuid.UUID(scope["tenant_id"]), uuid.UUID(scope["site_id"]), req["case_id"], READ_NOW))
    finally:
        reads.dispose()
    assert [h["canonical_record_id"] for h in history] == [reading["id"]]  # C1: root case membership, unchanged


def test_kind_cursor_mismatch(store, key) -> None:  # noqa: F811
    """A valid MAC cursor whose filter differs from the request filter is 409; bad shapes and kinds are 422."""
    info = seed()
    demo = info["tenants"]["demo"]
    api = Api(demo)
    try:
        page = api.ok(limit="5")
        refusal(api.get(limit="5", kind="OPERATOR_LOG", cursor=page["next_cursor"]), 409, "WORK_BASIS_CHANGED",
                CHANGED)
        notes = api.ok(limit="2", kind="SHIFT_NOTE")
        refusal(api.get(limit="2", cursor=notes["next_cursor"]), 409, "WORK_BASIS_CHANGED", CHANGED)
        refusal(api.get(limit="2", kind="all", cursor=notes["next_cursor"]), 409, "WORK_BASIS_CHANGED", CHANGED)
        refusal(api.get("incidents", limit="5", cursor=page["next_cursor"]), 409, "WORK_BASIS_CHANGED", CHANGED)
        for forged in (remac(page["next_cursor"], filter=None), remac(page["next_cursor"], filter="BOGUS"),
                       remac(page["next_cursor"], filter=["all"])):
            refusal(api.get(limit="5", cursor=forged), 422, "INVALID_CURSOR", BAD_CURSOR)
        for bad in ("", "operator_log", "BOGUS", "All"):
            refusal(api.get(kind=bad), 422, "INVALID_CURSOR", BAD_CURSOR)
        repeated = api.client.get(f"/api/work/{ROUTE}", params=[*WINDOW.items(), ("kind", "all"), ("kind", "all")])
        refusal(repeated, 422, "INVALID_CURSOR", BAD_CURSOR)
        for root in ("incidents", "maintenance", "preventive"):
            refusal(api.get(root, kind="all"), 422, "INVALID_CURSOR", BAD_CURSOR)
    finally:
        api.close()


def test_old_route_cursor_filter_stays_null(store, key) -> None:  # noqa: F811
    """P-E1-2: the three old roots keep `filter: null`; a string filter re-MACed onto their cursor is 422."""
    incidents = seedmod.seed(URL, "incidents", CLOCK)
    old = Api({s["tenant"]: s["tenant_id"] for s in incidents["sites"]}["demo"])
    try:
        first = old.ok("incidents", limit="2")
        assert cursor_body(first["next_cursor"])["filter"] is None
        refusal(old.get("incidents", limit="2", cursor=remac(first["next_cursor"], filter="all")), 422,
                "INVALID_CURSOR", BAD_CURSOR)
    finally:
        old.close()


def test_case_link_by_kind(store, key) -> None:  # noqa: F811
    """INCIDENT opens its Site incidents root-occurrence day; MAINTENANCE_REQUEST opens the exact request; only an
    explicit inbound cutoff is carried (P-E1-6). The link follows the selected head's case."""
    info = seed()
    demo = info["tenants"]["demo"]
    incident = next(w for w in info["written"] if w["kind"] == "INCIDENT")
    req = next(w for w in info["written"] if w["kind"] == "MAINTENANCE_REQUEST")
    log = stored(info, "OPERATOR_LOG", "KOBO-001")[0]
    reading = stored(info, "MANUAL_READING", "KOBO-001")[0]
    day = "from=2026-10-19T00%3A00%3A00Z&to=2026-10-20T00%3A00%3A00Z"  # incident root occurrence 2026-10-19 09:00
    rows = {r["root_id"]: r for r in all_rows(demo)}
    assert rows[log["id"]]["links"]["case"] == {"label": incident["code"],
                                                "href": f"/sites/KOBO-001/work/incidents?{day}"}
    assert rows[log["id"]]["case_code"] == incident["code"] and rows[log["id"]]["case_id"] == incident["case_id"]
    assert rows[reading["id"]]["links"]["case"] == {
        "label": req["code"], "href": f"/maintenance/requests/{req['case_id']}?site_id=KOBO-001"}
    assert rows[reading["id"]]["case_kind"] == "MAINTENANCE_REQUEST"
    unlinked = [r for r in rows.values() if r["root_id"] not in (log["id"], reading["id"])]
    assert unlinked and all(r["links"]["case"] is None and r["case_id"] is None and r["case_kind"] is None
                            and r["case_code"] is None for r in unlinked)
    assert all(r["links"]["site"] == {"label": r["site_name"], "href": f"/sites/{r['site_code']}"}
               for r in rows.values())
    pinned = {r["root_id"]: r for r in all_rows(demo, known_at=HISTORICAL)}
    cut = "&known_at=" + quote("2026-10-21T12:00:00.000000Z", safe="")
    assert pinned[log["id"]]["links"]["case"]["href"] == f"/sites/KOBO-001/work/incidents?{day}{cut}"
    assert pinned[reading["id"]]["links"]["case"]["href"] == (
        f"/maintenance/requests/{req['case_id']}?site_id=KOBO-001{cut}")
    # a head moving the reading to the incident points the global row at the head case
    writer = later_writer(info, 2)
    try:
        writer.post_operational_record(
            ("demo", "KOBO-001"), incident["case_id"], "Manual reading at KOBO-001: Fuel tank dip: 198 L",
            kind="MANUAL_READING", occurred_at=seedmod.OPERATIONAL_AT + timedelta(minutes=2), quantity="198",
            unit="L", correction={"supersedes_record_id": reading["id"], "canonical_record_id": reading["id"],
                                  "correction_reason": "Case corrected to the incident"})
    finally:
        writer.close()
    moved = {r["root_id"]: r for r in all_rows(demo)}[reading["id"]]
    assert moved["links"]["case"] == {"label": incident["code"], "href": f"/sites/KOBO-001/work/incidents?{day}"}


def test_non_submitted_and_missing_case_fail_closed(store, key) -> None:  # noqa: F811
    """P-E1-4/5: a non-SUBMITTED head or an unresolvable named case is 503, never a badge, a skip or `case:null`."""
    info = seed()
    demo = uuid.UUID(info["tenants"]["demo"])
    log = stored(info, "SHIFT_NOTE", "KOBO-002")[0]
    reading = stored(info, "MANUAL_READING", "KOBO-001")[0]
    mutations = (
        ("UPDATE operational_record SET state = 'ACCEPTED' WHERE id = :i", log["id"], "SHIFT_NOTE"),
        ("UPDATE operational_record SET case_id = :o WHERE id = :i", reading["id"], "OPERATOR_LOG"),
    )
    engine_ = create_engine(URL)
    try:
        for sql, target, kind in mutations:
            with engine_.connect() as c:
                tx = c.begin()
                try:
                    c.execute(text("SET LOCAL session_replication_role = replica"))  # controlled mutation only
                    c.execute(text(sql), {"i": target, "o": str(uuid.uuid4())})
                    service = GlobalWorkIndexService(SameConnection(c))
                    for params in ({}, {"kind": kind}):  # a filtered read fails closed too
                        with pytest.raises(GlobalWorkRefusal) as caught:
                            service.read(demo, ROUTE, request(**params), lambda code: True)
                        assert caught.value.status == 503 and caught.value.code == "WORK_STORE_UNAVAILABLE"
                finally:
                    tx.rollback()
    finally:
        engine_.dispose()
    assert read(info["tenants"]["demo"])["total_count"] == 7  # rolled back


def test_scope_and_thirty_one_day_boundary(store, key) -> None:  # noqa: F811
    info = seed()
    demo, other = info["tenants"]["demo"], info["tenants"]["w601-other"]
    theirs = read(other)
    assert theirs["total_count"] == 1 and theirs["rows"][0]["kind"] == "SITE_VISIT"
    assert theirs["scope"]["tenant_id"] == other and theirs["rows"][0]["body"].startswith("Site visit at the other")
    assert all(r["site_code"] in ("KOBO-001", "KOBO-002") and "other tenant" not in r["body"] for r in all_rows(demo))
    api = Api(demo, deny=("KOBO-002",))
    try:
        body = api.ok(limit="5")
        assert body["total_count"] == 4 and {r["site_code"] for r in body["rows"]} == {"KOBO-001"}
        assert body["scope"]["authorized_site_count"] == 1
    finally:
        api.close()
    none = Api(demo, deny=("KOBO-001", "KOBO-002"))
    try:
        empty = none.ok(known_at=HISTORICAL)
        assert empty["status"] == "EMPTY_SCOPE" and empty["total_count"] == 0 and empty["rows"] == []
        assert empty["coverage"] == {"state": "EMPTY_SCOPE", "reason": "NO_ACCESSIBLE_SITES", "sites": []}
    finally:
        none.close()
    day = {"from": "2026-10-18T00:00:00Z", "to": "2026-10-19T00:00:00Z"}
    assert read(demo, window=day)["total_count"] == 7
    assert read(demo, window={"from": "2026-10-17T00:00:00Z", "to": "2026-10-18T00:00:00Z"})["total_count"] == 0
    assert read(demo, window={"from": "2026-09-20T00:00:00Z", "to": "2026-10-21T00:00:00Z"})["total_count"] == 8
    api = Api(demo)
    try:
        refusal(api.get(window={"from": "2026-09-19T00:00:00Z", "to": "2026-10-21T00:00:00Z"}), 422,
                "INVALID_WINDOW", "from and to must be UTC instants in order, at most 31 days apart.")
        refusal(api.get(known_at="2026-10-23T00:00:00Z"), 422, "INVALID_KNOWN_AT",
                "known_at must be UTC and no later than the read time.")
        refusal(api.get(limit="0"), 422, "INVALID_LIMIT", "limit must be an integer from 1 to 100.")
    finally:
        api.close()


def test_operational_basis_changes_with_head_and_case(store, key) -> None:  # noqa: F811
    """P-E1-7: a later head (body or case) changes the selection token and a reused cursor is 409."""
    info = seed()
    demo = info["tenants"]["demo"]
    historical = read(demo, known_at=HISTORICAL)["selection_token"]
    api = Api(demo)
    try:
        page = api.ok(limit="5")
        assert page["selection_token"] != historical
        visit = stored(info, "OPERATOR_LOG", "KOBO-002")[0]
        writer = later_writer(info, 2)
        try:
            writer.post_operational_record(
                ("demo", "KOBO-002"), None, "Operator log at KOBO-002: pump started late.", kind="OPERATOR_LOG",
                occurred_at=seedmod.OPERATIONAL_AT + timedelta(minutes=4),
                correction={"supersedes_record_id": visit["id"], "canonical_record_id": visit["id"],
                            "correction_reason": "Wording corrected"})
        finally:
            writer.close()
        refusal(api.get(limit="5", cursor=page["next_cursor"]), 409, "WORK_BASIS_CHANGED", CHANGED)
        body_changed = api.ok(limit="5")["selection_token"]
        assert body_changed != page["selection_token"]
        incident = next(w for w in info["written"] if w["kind"] == "INCIDENT")
        note = stored(info, "SHIFT_NOTE", "KOBO-001")[0]
        writer = later_writer(info, 3)
        try:
            writer.post_operational_record(
                ("demo", "KOBO-001"), incident["case_id"], "Shift note at KOBO-001: handover completed with no open "
                "alarms.", kind="SHIFT_NOTE", occurred_at=seedmod.OPERATIONAL_AT + timedelta(minutes=3),
                correction={"supersedes_record_id": note["id"], "canonical_record_id": note["id"],
                            "correction_reason": "Case named"})
        finally:
            writer.close()
        case_changed = api.ok(limit="5")["selection_token"]
        assert case_changed not in (body_changed, page["selection_token"])
    finally:
        api.close()


def test_quantity_and_period_end_wire(store, key) -> None:  # noqa: F811
    """P-E1-8: quantity is the decimal text or null; period_end and every list instant are whole-second UTC `Z`."""
    info = seed()
    demo = info["tenants"]["demo"]
    readings = {r["site_code"]: r for r in all_rows(demo, kind="MANUAL_READING")}
    assert (readings["KOBO-001"]["quantity"], readings["KOBO-001"]["unit"]) == ("198", "L")
    assert (readings["KOBO-002"]["quantity"], readings["KOBO-002"]["unit"]) == ("42", "kg")
    assert readings["KOBO-001"]["body"] == "Manual reading at KOBO-001: Fuel tank dip: 198 L"
    assert readings["KOBO-002"]["body"] == "Manual reading at KOBO-002: Stock in chamber: 42 kg"
    others = all_rows(demo, kind="OPERATOR_LOG") + all_rows(demo, kind="SHIFT_NOTE")
    assert all(r["quantity"] is None and r["unit"] is None and r["period_end"] is None for r in others)
    scope = info["scopes"][("demo", "KOBO-001")]
    writer = later_writer(info, 2)
    try:
        writer.svc.post_operational_record(uuid.UUID(scope["tenant_id"]), uuid.UUID(scope["site_id"]), {
            "kind": "SITE_VISIT", "body": "Site visit at KOBO-001: meter read during the visit.",
            "occurred_at": "2026-10-19T08:00:00.250000Z", "period_end": "2026-10-19T10:30:00.750000Z",
            "unit": "kWh", "quantity": "12.500", "source_document_sha256": None, "case_id": None,
            "actor": dict(seedmod.ACTOR), "idempotency_key": "w601e-period-end-0001"},
            seedmod.W401_FIXTURE_SERVICE_PRINCIPAL_ID)
    finally:
        writer.close()
    visit = read(demo, kind="SITE_VISIT")["rows"][0]
    assert visit["period_end"] == "2026-10-19T10:30:00Z" and visit["occurred_at"] == "2026-10-19T08:00:00Z"
    assert (visit["quantity"], visit["unit"]) == ("12.5", "kWh")
    for row in all_rows(demo):
        for name in ("root_occurred_at", "occurred_at", "recorded_at"):
            assert WIRE_SECOND.match(row[name]), (name, row[name])
        assert row["period_end"] is None or WIRE_SECOND.match(row["period_end"])


def test_stress_record_body(store, key) -> None:  # noqa: F811
    """X2: the `stress` fixture's unlinked 4000-character OPERATOR_LOG at KOBO-001 (root occurrence `--clock` - 2d)."""
    info = seed("stress")
    rows = all_rows(info["tenants"]["demo"], kind="OPERATOR_LOG")
    assert len(rows) == 1
    row = rows[0]
    assert len(row["body"]) == 4000 and row["body"] == seedmod.STRESS_RECORD_BODY
    assert row["site_code"] == "KOBO-001" and row["case_id"] is None and row["links"]["case"] is None
    assert row["root_occurred_at"] == "2026-10-19T12:00:00Z"


def test_store_unavailable(store, key, monkeypatch) -> None:  # noqa: F811
    info = seed()
    demo = info["tenants"]["demo"]
    down = Api(demo, service=False)
    dead = Api(demo, url="postgresql+psycopg://assetops:wrong@127.0.0.1:1/none_test")
    try:
        refusal(down.get(), 503, "WORK_STORE_UNAVAILABLE", DOWN)
        refusal(dead.get(kind="OPERATOR_LOG"), 503, "WORK_STORE_UNAVAILABLE", DOWN)
    finally:
        down.close()
        dead.close()
    monkeypatch.delenv(CURSOR_KEY_ENV)
    api = Api(demo)
    try:
        refusal(api.get(), 503, "WORK_STORE_UNAVAILABLE", DOWN)
    finally:
        api.close()
