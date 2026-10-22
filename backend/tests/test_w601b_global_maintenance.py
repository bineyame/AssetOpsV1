"""W6-01b (B1): the global Maintenance and Preventive roots `GET /api/work/maintenance` and `/api/work/preventive`.

`.agent/W6-01-build-spec.md` section 1, the B1 card, section 3.1 (A1Q2 R2/R3, A2Q1 X1/X2/X9, CL3-4) and the
"B1-B3 pre-flight rulings" P-B1-1..13. Rows are written by `tools/w601_seed.py` through the real W4 `WorkService` and
the ordered write clock from the B1 `--clock 2026-10-20T12:00:00Z` (P-B1-1), read through the constructor
read-clock override. Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` DB.
"""

from __future__ import annotations

import importlib.util
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

REPO = Path(__file__).resolve().parents[2]
CLOCK = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)  # P-B1-1: the B1 fixture clock
READ_NOW = CLOCK + timedelta(seconds=5)  # after the historical plan correction at `--clock + 4s`
WINDOW = {"from": "2026-10-14T00:00:00Z", "to": "2026-10-21T00:00:00Z"}
KEY = "b1" * 32
MAINTENANCE_KEYS = {"site_code", "site_name", "site_id", "site_code_key", "case_id", "code", "kind", "revision_id",
                    "title", "narrative", "occurred_at", "created_at", "recorded_at", "state", "owner", "asset_id",
                    "asset_label", "incident_id", "record_id", "activity", "outcome_note", "finding_links",
                    "action_links", "source_provenance", "links"}
PREVENTIVE_KEYS = {"site_code", "site_name", "site_id", "site_code_key", "canonical_plan_id", "root_id", "head_id",
                   "code", "title", "trigger_kind", "next_due_at", "next_due_hours", "state", "asset_id",
                   "asset_label", "root_occurred_at", "occurred_at", "recorded_at", "supersedes_plan_id",
                   "correction_reason", "source_provenance", "links"}
ENVELOPE = {"schema_version", "scope", "window", "known_at", "status", "coverage", "total_count", "state_counts", "rows",
            "next_cursor", "selection_token"}

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text

    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.global_work_api import build_global_work_router
    from assetops_backend.work import model as m
    from assetops_backend.work.adapters.postgres_global_read import PostgresGlobalWorkRead
    from assetops_backend.work.adapters.postgres_work_read import PostgresWorkRead
    from assetops_backend.work.composition import _link_read_ports
    from assetops_backend.work.global_index import CURSOR_KEY_ENV, GlobalWorkIndexService
    from assetops_backend.work.site_index import WorkIndexService, parse_list_request

    _spec = importlib.util.spec_from_file_location("w601_seed", REPO / "tools" / "w601_seed.py")
    seedmod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(seedmod)


@pytest.fixture()
def key(monkeypatch):
    monkeypatch.setenv(CURSOR_KEY_ENV, KEY)


def seed(fixture: str, clock: datetime = CLOCK) -> dict:
    out = seedmod.seed(URL, fixture, clock)
    out["tenants"] = {s["tenant"]: s["tenant_id"] for s in out["sites"]}
    return out


class Api:
    """The global router over a private reader; `at` is the A1Q Q6 constructor-only read clock."""

    def __init__(self, tenant: str | None, at: datetime | None = READ_NOW, *, deny: tuple[str, ...] = (),
                 authenticate=None, service: bool = True) -> None:
        self.read = PostgresGlobalWorkRead(URL, link_rows=build_link_rows_reader(), ports=_link_read_ports(),
                                           test_read_clock_override=None if at is None else (lambda: at))
        app = FastAPI()
        kwargs = {} if authenticate is None else {"authenticate": authenticate}
        app.include_router(build_global_work_router(
            GlobalWorkIndexService(self.read) if service else None, lambda: tenant,
            access=lambda request, code: 403 if code in deny else None, **kwargs))
        self.client = TestClient(app)

    def get(self, root: str, **params):
        query = {**WINDOW, **params}
        return self.client.get(f"/api/work/{root}", params={k: v for k, v in query.items() if v is not None})

    def ok(self, root: str, **params) -> dict:
        response = self.get(root, **params)
        assert response.status_code == 200, response.text
        return response.json()

    def close(self) -> None:
        self.read.dispose()


def read(tenant: str, kind: str, at: datetime = READ_NOW, **params) -> dict:
    api = Api(tenant, at)
    try:
        return api.ok(kind, **params)
    finally:
        api.close()


def all_rows(tenant: str, kind: str, **params) -> list[dict]:
    api = Api(tenant)
    try:
        body = api.ok(kind, limit="5", **params)
        rows = list(body["rows"])
        while body["next_cursor"]:
            body = api.ok(kind, limit="5", cursor=body["next_cursor"], **params)
            rows.extend(body["rows"])
        return rows
    finally:
        api.close()


def refusal(response, status: int, code: str, message: str) -> None:
    assert response.status_code == status, response.text
    assert response.json() == {"detail": {"code": code, "message": message, "rows": None, "total_count": None}}


def query(known_at: str) -> str:
    return "&".join(f"{k}={quote(v, safe='')}" for k, v in (*WINDOW.items(), ("known_at", known_at)))


def z(at: datetime) -> str:
    return at.strftime("%Y-%m-%dT%H:%M:%SZ")


# --- maintenance: counts, paging, states, owner, records, fallback hrefs -------------------------------------------

def test_state_counts_cover_full_selection(store, key) -> None:  # noqa: F811
    """X1 / P-B1-4: the exact seven-request set over two Sites, counts over the full selection on both pages."""
    info = seed("maintenance")
    demo = info["tenants"]["demo"]
    api, nobody = Api(demo), Api(demo, deny=("KOBO-001", "KOBO-002"))
    expected = {"OPEN": 4, "IN_PROGRESS": 1, "COMPLETED": 1, "CANCELLED": 1}
    try:
        one = api.ok("maintenance", limit="5")
        two = api.ok("maintenance", limit="5", cursor=one["next_cursor"])
        empty = nobody.ok("maintenance")
    finally:
        api.close()
        nobody.close()
    assert set(one) == ENVELOPE and one["schema_version"] == "global-work-index-1"
    assert one["total_count"] == 7 and len(one["rows"]) == 5 and len(two["rows"]) == 2
    assert two["next_cursor"] is None and two["status"] == "CURRENT"
    assert one["state_counts"] == expected and two["state_counts"] == expected
    assert sum(one["state_counts"].values()) == one["total_count"]
    assert empty["status"] == "EMPTY_SCOPE"
    assert empty["state_counts"] == {"OPEN": 0, "IN_PROGRESS": 0, "COMPLETED": 0, "CANCELLED": 0}
    rows = one["rows"] + two["rows"]
    assert all(set(r) == MAINTENANCE_KEYS and r["kind"] == "MAINTENANCE_REQUEST" for r in rows)
    by_title = {r["title"]: r for r in rows}
    assert set(by_title) == {"Inspect starter", "Inspect transfer switch", "Replace breaker", "Check feeder contacts",
                             "Inspect pump", "Check panel door", "Inspect inverter relay"}
    assert sorted(r["site_code"] for r in rows) == ["KOBO-001"] * 5 + ["KOBO-002"] * 2
    assert {t: r["state"] for t, r in by_title.items()} == {
        "Inspect starter": "OPEN", "Inspect transfer switch": "OPEN", "Replace breaker": "OPEN",
        "Check feeder contacts": "CANCELLED", "Inspect pump": "IN_PROGRESS", "Check panel door": "COMPLETED",
        "Inspect inverter relay": "OPEN"}
    # Sort: root created_at desc (each request took the next write second), then Site key, Site ID, case ID.
    assert [r["created_at"] for r in rows] == sorted((r["created_at"] for r in rows), reverse=True)
    assert rows[0]["title"] == "Inspect inverter relay"


def test_owner_payload_and_latest_record(store, key) -> None:  # noqa: F811
    """Owner is the latest ASSIGN payload assignee; record fields are the W4 Site row's latest record (P-B1-12)."""
    info = seed("maintenance")
    demo = info["tenants"]["demo"]
    body = read(demo, "maintenance")
    rows = all_rows(demo, "maintenance")
    by_title = {r["title"]: r for r in rows}
    assert by_title["Inspect pump"]["owner"] == "Field team B"
    assert by_title["Check panel door"]["owner"] == "Field team C"
    assert by_title["Inspect starter"]["owner"] is None
    done = by_title["Check panel door"]
    assert done["activity"] == "Inspected panel door contacts." and done["outcome_note"] == "Operation not verified."
    assert by_title["Inspect starter"]["record_id"] is None and by_title["Inspect starter"]["activity"] is None
    # A second, later record on the same request becomes the selected one.
    sites = seedmod._existing_sites(URL)
    writer = seedmod.Writer(URL, seedmod.WriteClock(CLOCK + timedelta(seconds=1)), sites, CLOCK)
    try:
        later = writer.record(seedmod.B, done["case_id"], "Second inspection of the door contacts.", None)
    finally:
        writer.close()
    after = {r["title"]: r for r in all_rows(demo, "maintenance")}["Check panel door"]
    assert after["record_id"] == later and after["activity"] == "Second inspection of the door contacts."
    assert after["outcome_note"] is None
    # W4 Site row parity for the same window and cutoff.
    site = sites[seedmod.B]
    site_read = PostgresWorkRead(URL, link_rows=build_link_rows_reader(), ports=_link_read_ports(),
                                 test_read_clock_override=lambda: READ_NOW)
    try:
        w4 = WorkIndexService(site_read).read(site["tenant"], site["site"], "KOBO-002", "maintenance",
                                              parse_list_request(WINDOW["from"], WINDOW["to"], None,
                                                                 [m.iso(READ_NOW)], None), access_basis="test")
    finally:
        site_read.dispose()
    [w4_row] = [r["wire"] if "wire" in r else r for r in w4["rows"] if (r.get("wire") or r)["case_id"] ==
                done["case_id"]]
    assert (after["record_id"], after["activity"], after["outcome_note"]) == (
        w4_row["record_id"], w4_row["activity"], w4_row["outcome_note"])
    assert body["status"] == "CURRENT"


def test_site_maintenance_fallback_href(store, key) -> None:  # noqa: F811
    """P-B1-13 / A1Q Q8: label `Site maintenance`, the same window and the response `known_at`; no detail href."""
    info = seed("maintenance")
    demo = info["tenants"]["demo"]
    body = read(demo, "maintenance")
    for row in body["rows"]:
        assert row["links"]["site"] == {"label": row["site_name"], "href": f"/sites/{row['site_code']}"}
        assert row["links"]["site_maintenance"] == {
            "label": "Site maintenance",
            "href": f"/sites/{row['site_code']}/work/maintenance?{query(body['known_at'])}"}
        assert row["links"]["detail"] is None
    historical = read(demo, "maintenance", known_at=z(CLOCK))
    assert historical["status"] == "HISTORICAL" and historical["known_at"] == z(CLOCK)
    assert historical["rows"][0]["links"]["site_maintenance"]["href"].endswith(quote(z(CLOCK), safe=""))


def test_request_root_created_at_window(store, key) -> None:  # noqa: F811
    """P-B1-1: membership is the root `created_at`. A request created at `to` with an in-window occurrence is out;
    a request created just before `to` stays in, with its later out-of-window revision selected."""
    info = seed("zero")
    demo = info["tenants"]["demo"]
    sites = seedmod._existing_sites(URL)
    to = datetime(2026, 10, 21, tzinfo=timezone.utc)
    inside = seedmod.Writer(URL, seedmod.WriteClock(to - timedelta(seconds=1)), sites, CLOCK)
    try:
        kept = inside.request(seedmod.A, None, "Created just before the window end")
        outside = inside.request(seedmod.A, None, "Created at the window end")  # takes `to` exactly
        inside.revise(seedmod.A, kept["id"], kept["revision"]["id"], "Revised after the window end",
                      "Corrected after review.", "Title corrected")
    finally:
        inside.close()
    body = read(demo, "maintenance", to + timedelta(hours=1))
    assert [r["case_id"] for r in body["rows"]] == [kept["id"]]
    [row] = body["rows"]
    assert row["title"] == "Revised after the window end" and row["created_at"] == "2026-10-20T23:59:59Z"
    assert row["occurred_at"] == "2026-10-18T10:00:00Z" and row["recorded_at"] == "2026-10-21T00:00:01Z"
    assert outside["id"] not in {r["case_id"] for r in body["rows"]}
    later = read(demo, "maintenance", to + timedelta(hours=1),
                 **{"from": "2026-10-21T00:00:00Z", "to": "2026-10-22T00:00:00Z"})
    assert [r["case_id"] for r in later["rows"]] == [outside["id"]]


def test_unknown_state_is_503(store, key) -> None:  # noqa: F811
    """P-B1-11: an event chain outside the four reachable states is a consistency failure, never an uncounted row."""
    info = seed("maintenance")
    demo = info["tenants"]["demo"]
    done = {r["title"]: r for r in all_rows(demo, "maintenance")}["Check panel door"]
    engine_ = create_engine(URL)
    try:
        with engine_.begin() as c:
            c.execute(text(
                "INSERT INTO work_event (id, tenant_id, site_id, case_id, kind, payload, occurred_at, recorded_at, "
                "actor_kind, actor_id, authorization_basis, attestation, idempotency_key, payload_sha256) "
                "SELECT :id, tenant_id, site_id, id, 'OPEN_VERIFICATION', '{}'::jsonb, :at, :at, 'SERVICE', "
                "'service:w401-fixture', 'test', 'test', 'w601b-open-verification', :sha FROM work_case "
                "WHERE id = :c"), {"id": uuid.uuid4(), "at": CLOCK, "c": done["case_id"], "sha": "0" * 64})
    finally:
        engine_.dispose()
    api = Api(demo)
    try:
        refusal(api.get("maintenance"), 503, "WORK_STORE_UNAVAILABLE", "Work records could not be read or saved.")
    finally:
        api.close()


def test_detail_fixture_events_and_cancel(store, key) -> None:  # noqa: F811
    """P-B1-5 / X9: the C2-C4 request (CREATED, ASSIGN, COMMENT, COMPLETE, REOPEN, a revision) and its CANCEL."""
    info = seed("detail")
    demo = info["tenants"]["demo"]
    rows = {r["code"]: r for r in read(demo, "maintenance")["rows"]}
    assert len(rows) == 2
    [first] = [r for r in rows.values() if r["title"] == "Inspect starter and control circuit again"]
    [second] = [r for r in rows.values() if r["title"] == "Check spare relay"]
    assert first["state"] == "IN_PROGRESS" and first["owner"] == "Maintenance lead"
    assert first["narrative"] == "Repeat the starter check and record the witnessed test."
    assert first["activity"] == "Inspected starter relay and control wiring."
    assert first["outcome_note"] == "Witnessed start test still required."
    assert second["state"] == "CANCELLED" and second["narrative"] == "Spare relay check requested."
    engine_ = create_engine(URL)
    try:
        with engine_.connect() as c:
            kinds = list(c.execute(text("SELECT kind FROM work_event WHERE case_id = :c ORDER BY recorded_at, id"),
                                   {"c": first["case_id"]}).scalars())
            reasons = list(c.execute(text("SELECT reason FROM work_case_revision WHERE case_id = :c "
                                          "ORDER BY recorded_at, id"), {"c": first["case_id"]}).scalars())
            cancel = c.execute(text("SELECT payload FROM work_event WHERE case_id = :c AND kind = 'CANCEL'"),
                               {"c": second["case_id"]}).scalar_one()
            seconds = list(c.execute(text(
                "SELECT recorded_at FROM (SELECT recorded_at FROM work_event UNION ALL SELECT recorded_at FROM "
                "work_case_revision UNION ALL SELECT recorded_at FROM maintenance_record) x ORDER BY 1")).scalars())
    finally:
        engine_.dispose()
    assert kinds == ["CREATED", "ASSIGN", "COMMENT", "COMPLETE", "REOPEN"]
    assert reasons == [None, "Inspection scope corrected"]
    assert cancel == {"reason": "Duplicate request; first inspection covers the relay"}
    # Each command took the next write-clock second (the CREATED event and the root revision share theirs).
    assert all(b > a for a, b in zip(sorted(set(seconds)), sorted(set(seconds))[1:]))


def test_stress_request_revision_and_lengths(store, key) -> None:  # noqa: F811
    """X2 / P-B1-6/7: the long request, owner, narrative, activity, revision reason and plan title."""
    info = seed("stress")
    demo = info["tenants"]["demo"]
    [row] = [r for r in read(demo, "maintenance")["rows"]]
    assert len(row["title"]) == 200 and row["title"] == seedmod.STRESS_REQUEST_TITLE
    # W6-01b build rulings (Q2) item 4: the expressions store 4,000 and 500 characters; that is the contract.
    assert len(row["owner"]) == 128 and row["narrative"] == seedmod.STRESS_NARRATIVE and len(row["narrative"]) == 4000
    assert row["activity"] == seedmod.STRESS_ACTIVITY and len(row["activity"]) == 4000
    assert row["outcome_note"] == "Authored note"
    engine_ = create_engine(URL)
    try:
        with engine_.connect() as c:
            revisions = c.execute(text("SELECT title, narrative, reason FROM work_case_revision WHERE case_id = :c "
                                       "ORDER BY recorded_at, id"), {"c": row["case_id"]}).all()
            records = c.execute(text("SELECT count(*) FROM maintenance_record WHERE case_id = :c "
                                     "AND supersedes_record_id IS NOT NULL"), {"c": row["case_id"]}).scalar_one()
    finally:
        engine_.dispose()
    assert len(revisions) == 2 and revisions[1][2] == seedmod.STRESS_REASON and len(revisions[1][2]) == 500
    assert revisions[1][0] == revisions[0][0] and revisions[1][1] == revisions[0][1]  # title/narrative unchanged
    assert records == 0  # the correction is a case revision, never a record successor
    [plan] = read(demo, "preventive")["rows"]
    assert len(plan["title"]) == 200 and plan["title"] == seedmod.STRESS_PLAN_TITLE


# --- preventive ------------------------------------------------------------------------------------------------

def test_preventive_draft_rows_and_run_hours(store, key) -> None:  # noqa: F811
    """P-B1-4/9/10: five `demo` DRAFT plans (other tenant excluded), null counts, canonical hours text."""
    info = seed("preventive")
    demo = info["tenants"]["demo"]
    body = read(demo, "preventive", limit="5")
    assert set(body) == ENVELOPE and body["state_counts"] is None and body["total_count"] == 5
    assert body["next_cursor"] is None
    rows = body["rows"]
    assert all(set(r) == PREVENTIVE_KEYS and r["state"] == "DRAFT" for r in rows)
    by_title = {r["title"]: r for r in rows}
    assert set(by_title) == {"Inspect filters", "Generator 500-hour service", "Check battery cabinet",
                             "Inspect pump seals", "Review switchgear"}
    assert {t: r["site_code"] for t, r in by_title.items()} == {
        "Inspect filters": "KOBO-001", "Generator 500-hour service": "KOBO-001", "Check battery cabinet": "KOBO-001",
        "Inspect pump seals": "KOBO-002", "Review switchgear": "KOBO-002"}
    hours = by_title["Generator 500-hour service"]
    assert (hours["trigger_kind"], hours["next_due_hours"], hours["next_due_at"]) == ("RUN_HOURS", "500", None)
    assert by_title["Review switchgear"]["next_due_hours"] == "750"
    cal = by_title["Inspect filters"]
    assert (cal["trigger_kind"], cal["next_due_at"], cal["next_due_hours"]) == ("CALENDAR", "2026-10-29T00:00:00Z",
                                                                                 None)
    assert by_title["Inspect pump seals"]["next_due_at"] == "2026-10-25T00:00:00Z"
    for r in rows:
        assert r["root_id"] == r["canonical_plan_id"] == r["head_id"] and r["supersedes_plan_id"] is None
        assert r["root_occurred_at"] == r["occurred_at"] == "2026-10-18T11:00:00Z"
        assert r["asset_id"] is None and r["asset_label"] is None and r["code"].startswith("PM-")
        assert r["links"] == {"site": {"label": r["site_name"], "href": f"/sites/{r['site_code']}"}}
        assert r["source_provenance"]["state"] in {"UNKNOWN", "COMPLETE", "INCOMPLETE"}
    assert [r["recorded_at"] for r in rows] == sorted((r["recorded_at"] for r in rows), reverse=True)
    other = read(info["tenants"]["w601-other"], "preventive")
    assert [r["title"] for r in other["rows"]] == ["Other tenant plan"]


def test_plan_correction_historical_head(store, key) -> None:  # noqa: F811
    """CL3-4 as ruled by P-B1-8: the root at `--clock + 3s` and its correction at `+4s`; the root keeps its window."""
    info = seed("historical")
    demo = info["tenants"]["demo"]
    before = read(demo, "preventive", known_at=z(CLOCK))
    root = read(demo, "preventive", known_at=z(CLOCK + timedelta(seconds=3)))
    current = read(demo, "preventive")
    assert before["total_count"] == 0 and before["status"] == "HISTORICAL"
    [old] = root["rows"]
    [new] = current["rows"]
    assert root["status"] == "HISTORICAL" and current["status"] == "CURRENT"
    assert old["head_id"] == old["root_id"] and old["supersedes_plan_id"] is None
    assert old["next_due_at"] == z(CLOCK + timedelta(days=7)) and old["correction_reason"] is None
    assert old["occurred_at"] == old["root_occurred_at"] == z(CLOCK - timedelta(days=2, hours=1))
    assert new["root_id"] == old["root_id"] and new["head_id"] != old["head_id"] and new["code"] == old["code"]
    assert new["supersedes_plan_id"] == old["head_id"]
    assert new["correction_reason"] == "Due date corrected after review"
    assert new["next_due_at"] == z(CLOCK + timedelta(days=14))
    assert new["occurred_at"] == z(CLOCK - timedelta(days=1))
    assert new["root_occurred_at"] == z(CLOCK - timedelta(days=2, hours=1))
    assert new["recorded_at"] == z(CLOCK + timedelta(seconds=4))
    # A1's historical incident rows are unchanged by the plan writes.
    incidents = read(demo, "incidents", known_at=z(CLOCK))
    assert incidents["total_count"] == 6


def test_plan_basis_binds_due_correction(store, key) -> None:  # noqa: F811
    """P-B1-10: a due-date correction recorded before the cursor's cutoff changes the bound selection: 409."""
    info = seed("preventive")
    demo = info["tenants"]["demo"]
    at = CLOCK + timedelta(seconds=30)
    api = Api(demo, at)
    try:
        one = api.ok("preventive", limit="2")
        target = one["rows"][0]
        sites = seedmod._existing_sites(URL)
        site = (("demo", target["site_code"]))
        writer = seedmod.Writer(URL, seedmod.WriteClock(CLOCK + timedelta(seconds=10)), sites, CLOCK)
        try:
            writer.plan(site, target["title"], target["trigger_kind"],
                        due_at=None if target["next_due_at"] is None else seedmod.utc("2026-11-05T00:00:00Z"),
                        due_hours=None if target["next_due_hours"] is None else "900",
                        correction={"supersedes_plan_id": target["head_id"], "canonical_plan_id": target["root_id"],
                                    "correction_reason": "Due date corrected after review"})
        finally:
            writer.close()
        refusal(api.get("preventive", limit="2", cursor=one["next_cursor"]), 409, "WORK_BASIS_CHANGED",
                "The work list changed; request page one without a cursor.")
        fresh = api.ok("preventive", limit="5")
    finally:
        api.close()
    assert fresh["selection_token"] != one["selection_token"]
    assert {r["root_id"]: r for r in fresh["rows"]}[target["root_id"]]["supersedes_plan_id"] == target["head_id"]


def test_plan_asset_label(store, key) -> None:  # noqa: F811
    """A plan written with a stored Foundation asset carries `{asset_code} · {asset_type}`; no invented asset."""
    info = seed("zero")
    demo = info["tenants"]["demo"]
    sites = seedmod._existing_sites(URL)
    site = sites[seedmod.A]
    engine_ = create_engine(URL)
    try:
        with engine_.connect() as c:
            asset = c.execute(text("SELECT CAST(id AS text), asset_code, asset_type FROM asset WHERE site_id = :s "
                                   "ORDER BY asset_code LIMIT 1"), {"s": site["site"]}).one()
    finally:
        engine_.dispose()
    writer = seedmod.Writer(URL, seedmod.WriteClock(CLOCK - timedelta(minutes=1)), sites, CLOCK)
    try:
        made = writer.svc.post_plan(site["tenant"], site["site"], {
            "asset_id": asset[0], "title": "Inspect filters", "trigger_kind": "CALENDAR", "next_due_at": None,
            "next_due_hours": None, "occurred_at": z(CLOCK - timedelta(days=2, hours=1)), "actor": dict(seedmod.ACTOR),
            "idempotency_key": writer._key()}, seedmod.W401_FIXTURE_SERVICE_PRINCIPAL_ID)[1]
    finally:
        writer.close()
    [row] = read(demo, "preventive")["rows"]
    assert row["head_id"] == made["id"] and row["asset_id"] == asset[0].lower()
    assert row["asset_label"] == f"{asset[1]} · {asset[2]}" and row["next_due_at"] is None


# --- cursors and refusals -------------------------------------------------------------------------------------------

def test_cursor_route_and_refusals(store, key, monkeypatch) -> None:  # noqa: F811
    info = seed("maintenance")
    demo = info["tenants"]["demo"]
    api = Api(demo)
    try:
        page = api.ok("maintenance", limit="5")
        refusal(api.get("incidents", limit="5", cursor=page["next_cursor"]), 409, "WORK_BASIS_CHANGED",
                "The work list changed; request page one without a cursor.")
        refusal(api.get("preventive", cursor=page["next_cursor"]), 409, "WORK_BASIS_CHANGED",
                "The work list changed; request page one without a cursor.")
        refusal(api.get("maintenance", cursor="not-a-cursor"), 422, "INVALID_CURSOR",
                "The cursor is not an estate cursor.")
        for kind in ("maintenance", "preventive"):
            refusal(api.get(kind, **{"from": None}), 422, "INVALID_WINDOW",
                    "from and to must be UTC instants in order, at most 31 days apart.")
            refusal(api.get(kind, limit="0"), 422, "INVALID_LIMIT", "limit must be an integer from 1 to 100.")
            refusal(api.get(kind, kind="all"), 422, "INVALID_CURSOR", "The cursor is not an estate cursor.")
            refusal(api.get(kind, known_at="2026-10-23T00:00:00Z"), 422, "INVALID_KNOWN_AT",
                    "known_at must be UTC and no later than the read time.")
        monkeypatch.delenv(CURSOR_KEY_ENV)
        refusal(api.get("preventive"), 503, "WORK_STORE_UNAVAILABLE", "Work records could not be read or saved.")
    finally:
        api.close()
    unauth = Api(demo, authenticate=lambda request: 401)
    down = Api(demo, service=False)
    try:
        for kind in ("maintenance", "preventive"):
            response = unauth.get(kind)
            refusal(response, 401, "UNAUTHENTICATED", "Sign in to read estate records.")
            assert response.headers["WWW-Authenticate"] == "Bearer"
            refusal(down.get(kind), 503, "WORK_STORE_UNAVAILABLE", "Work records could not be read or saved.")
    finally:
        unauth.close()
        down.close()


def test_complete_zero(store, key) -> None:  # noqa: F811
    info = seed("zero")
    demo = info["tenants"]["demo"]
    m_body, p_body = read(demo, "maintenance"), read(demo, "preventive")
    assert m_body["total_count"] == 0 and m_body["rows"] == [] and m_body["status"] == "CURRENT"
    assert m_body["state_counts"] == {"OPEN": 0, "IN_PROGRESS": 0, "COMPLETED": 0, "CANCELLED": 0}
    assert p_body["total_count"] == 0 and p_body["rows"] == [] and p_body["state_counts"] is None


# --- linked (A1Q2 R2 as replaced by the W6-01b build rulings (Q2) item 1) -----------------------------------------

def test_linked_finding_and_action_hrefs(store, key) -> None:  # noqa: F811
    """Q2 item 1: the real S4 Finding (F01, source day 2026-10-06, decided 2026-10-19) and S6 Action (accepted
    2026-10-20) pinned through W4; at each root's returned `known_at` the global hrefs equal the W4 Site rows."""
    out = seedmod.seed(URL, "linked", datetime(2026, 10, 20, 12, tzinfo=timezone.utc))
    tenant, site = out["tenant_id"], out["site_id"]
    engine_ = create_engine(URL)
    try:
        with engine_.connect() as c:
            finding_day, finding_at = c.execute(text(
                "SELECT f.anchor_start, r.created_at FROM finding_revision r JOIN finding f ON f.id = r.finding_id "
                "WHERE r.id = :r"), {"r": out["finding_revision_id"]}).one()
            action_at = c.execute(text("SELECT recorded_at FROM action_event WHERE id = :e"),
                                  {"e": out["action_event_id"]}).scalar_one()
            work_first = c.execute(text("SELECT min(created_at) FROM work_case WHERE tenant_id = :t"),
                                   {"t": tenant}).scalar_one()
    finally:
        engine_.dispose()
    assert finding_day.astimezone(timezone.utc).date().isoformat() == "2026-10-06"
    assert finding_at < action_at < work_first == datetime(2026, 10, 20, 11, 59, tzinfo=timezone.utc)
    window = ("2026-10-14T00:00:00Z", "2026-10-21T00:00:00Z")
    api = Api(tenant, None)
    try:
        inc = api.ok("incidents", **{"from": window[0], "to": window[1]})
        req = api.ok("maintenance", **{"from": window[0], "to": window[1]})
    finally:
        api.close()
    fid, aid = out["finding_id"], out["action_id"]
    for body, kind in ((inc, "incidents"), (req, "maintenance")):
        site_read = PostgresWorkRead(URL, link_rows=build_link_rows_reader(), ports=_link_read_ports())
        try:
            w4 = WorkIndexService(site_read).read(uuid.UUID(tenant), uuid.UUID(site), "KOBO-001", kind,
                                                  parse_list_request(window[0], window[1], None,
                                                                     [body["known_at"]], None), access_basis="test")
        finally:
            site_read.dispose()
        w4_rows = {(r.get("wire") or r)["case_id"]: (r.get("wire") or r) for r in w4["rows"]}
        for row in body["rows"]:
            w4_row = w4_rows[row["case_id"]]
            assert row["finding_links"] == [{"label": x["label"], "href": x["href"]} for x in w4_row["finding_links"]]
            assert row["action_links"] == [{"label": x["label"], "href": x["href"]} for x in w4_row["action_links"]]
        assert any(x["label"] == f"Finding {fid[:8]}" and x["href"] for r in body["rows"] for x in r["finding_links"])
        assert any(x["label"] == f"Action {aid[:8]}" and x["href"] for r in body["rows"] for x in r["action_links"])
    assert json.dumps(out["hrefs"])
