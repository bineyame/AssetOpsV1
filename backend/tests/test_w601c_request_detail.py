"""W6-01c (C1): the exact global request detail `GET /api/work/requests/{case_id}?site_id=&known_at=`.

`.agent/W6-01-build-spec.md` section 1 Detail DTO, the C1 card, G5, X4, CL3-3, CL3-5 and the "C1-C3 pre-flight
rulings" (P-C1-1..11). Rows are written by `tools/w601_seed.py` through the real W4 `WorkService` on the B1 clock
`2026-10-20T12:00:00Z` and read through the constructor read-clock override. The missing-CREATED case is inserted by
raw SQL inside a rolled-back transaction. Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` DB.
"""

from __future__ import annotations

import importlib.util
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

REPO = Path(__file__).resolve().parents[2]
CLOCK = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)  # P-B1-1 / C1 ruling: the B1 fixture clock
READ_NOW = CLOCK + timedelta(seconds=5, microseconds=123456)
TOP = {"schema_version", "selected", "work_detail", "work_asset", "history", "links"}
LINKS = {"site", "overview", "record", "history", "source_incident", "findings", "actions"}
OPERATIONAL = {"canonical_record_id", "head_id", "code", "kind", "body", "root_occurred_at", "occurred_at",
               "recorded_at"}
REVISION = {"id", "revision_no", "supersedes_revision_id", "title", "reason", "occurred_at", "recorded_at",
            "actor_kind", "actor_id"}
NOT_FOUND = ("WORK_CASE_NOT_FOUND", "No work case with this ID at this site.")
DOWN = ("WORK_STORE_UNAVAILABLE", "Work records could not be read or saved.")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text

    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.global_work_api import build_global_work_router
    from assetops_backend.sites.ports import SiteStoreUnavailable
    from assetops_backend.work.adapters.postgres_global_read import GlobalReadTx, PostgresGlobalWorkRead
    from assetops_backend.work.adapters.postgres_work_read import PostgresWorkRead
    from assetops_backend.work.composition import _link_read_ports
    from assetops_backend.work.detail import WorkDetailService
    from assetops_backend.work.global_detail import GlobalWorkDetailService
    from assetops_backend.work.model import WorkStoreUnavailable
    from assetops_backend.work_api import W401_FIXTURE_SERVICE_PRINCIPAL_ID, build_work_router

    _spec = importlib.util.spec_from_file_location("w601_seed", REPO / "tools" / "w601_seed.py")
    seedmod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(seedmod)


def seed(fixture: str) -> dict:
    out = seedmod.seed(URL, fixture, CLOCK)
    out["scopes"] = {(s["tenant"], s["site_code"]): (s["site_code"], UUID(s["tenant_id"]), UUID(s["site_id"]))
                     for s in out["sites"]}
    out["requests"] = [w["case_id"] for w in out["written"] if w["kind"] == "MAINTENANCE_REQUEST"]
    return out


def demo_scope(info: dict, tenant: str = "demo"):
    """The server's tenant registry scope: Site code to (code, tenant_id, site_id) of one tenant only."""
    return lambda code: next((v for (t, c), v in info["scopes"].items() if t == tenant and c == code), None)


class Api:
    """The global router with only the C1 detail route in use; `at` is the constructor-only read clock."""

    def __init__(self, scope, at: datetime | None = READ_NOW, *, deny: tuple[str, ...] = (), access=None,
                 authenticate=None, details=None, no_details: bool = False, url: str | None = None) -> None:
        self.read = PostgresGlobalWorkRead(url or URL, link_rows=build_link_rows_reader(), ports=_link_read_ports(),
                                           test_read_clock_override=None if at is None else (lambda: at))
        kwargs = {} if authenticate is None else {"authenticate": authenticate}
        app = FastAPI()
        app.include_router(build_global_work_router(
            None, lambda: None, access=access or (lambda request, code: 403 if code in deny else None),
            unavailable=(SiteStoreUnavailable,), scope=scope,
            details=None if no_details else GlobalWorkDetailService(self.read) if details is None else details,
            **kwargs))
        self.client = TestClient(app)

    def get(self, case_id: str, *params: tuple[str, str]):
        return self.client.get(f"/api/work/requests/{case_id}", params=list(params))

    def ok(self, case_id: str, site: str = "KOBO-001", known_at: str | None = None) -> dict:
        params = [("site_id", site)] + ([] if known_at is None else [("known_at", known_at)])
        response = self.get(case_id, *params)
        assert response.status_code == 200, response.text
        return response.json()

    def close(self) -> None:
        self.read.dispose()


def detail(info: dict, case_id: str, known_at: str | None = None, at: datetime = READ_NOW) -> dict:
    api = Api(demo_scope(info), at)
    try:
        body = api.ok(case_id, known_at=known_at)
    finally:
        api.close()
    assert set(body) == TOP and set(body["links"]) == LINKS
    return body


def site_detail(info: dict, case_id: str, known_at: str | None = None, at: datetime = READ_NOW) -> dict:
    read = PostgresWorkRead(URL, link_rows=build_link_rows_reader(), ports=_link_read_ports(),
                            test_read_clock_override=lambda: at)
    app = FastAPI()
    app.include_router(build_work_router(None, demo_scope(info), details=WorkDetailService(read)))
    try:
        response = TestClient(app).get(f"/api/sites/KOBO-001/work/cases/{case_id}",
                                       params={} if known_at is None else {"known_at": known_at})
    finally:
        read.dispose()
    assert response.status_code == 200, response.text
    return response.json()


def refused(response, status: int, code: str, message: str) -> None:
    assert response.status_code == status, response.text
    assert response.json() == {"detail": {"code": code, "message": message}}
    assert (response.headers.get("www-authenticate") == "Bearer") == (status == 401)


def writer(info: dict, start: datetime):
    sites = {k: {"tenant": v[1], "site": v[2], "site_code": v[0]} for k, v in info["scopes"].items()}
    return seedmod.Writer(URL, seedmod.WriteClock(start), sites, CLOCK)


def iso(at: datetime) -> str:
    return at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# --- parity, selection and ordering ---------------------------------------------------------------------------------

def test_site_parity(store) -> None:  # noqa: F811
    """The nested `work_detail` is the W4 Site body byte for byte, at the read time and at an explicit cutoff."""
    info = seed("detail")
    for case_id in info["requests"]:
        assert detail(info, case_id)["work_detail"] == site_detail(info, case_id)
        cut = "2026-10-20T11:59:07.5Z"  # after both creates, before the CANCEL and the REC
        assert detail(info, case_id, cut)["work_detail"] == site_detail(info, case_id, cut)
    body = detail(info, info["requests"][0])
    assert body["selected"] == {"site_code": "KOBO-001", "site_id": str(info["scopes"][("demo", "KOBO-001")][2]),
                                "case_id": info["requests"][0], "case_code": body["work_detail"]["case"]["code"],
                                "case_kind": "MAINTENANCE_REQUEST", "known_at": iso(READ_NOW),
                                "site_domain": "MINIGRID"}
    assert body["schema_version"] == "global-work-detail-1" and body["work_asset"] is None


def test_corrected_ordering(store) -> None:  # noqa: F811
    """`history.revisions` are the case revisions at K by `(recorded_at, id)`; the nested selection is the last."""
    info = seed("detail")
    first = info["requests"][0]
    body = detail(info, first)
    revisions = body["history"]["revisions"]
    assert [set(r) for r in revisions] == [REVISION, REVISION]
    assert [r["revision_no"] for r in revisions] == [1, 2]
    assert revisions[1]["supersedes_revision_id"] == revisions[0]["id"]
    assert [r["reason"] for r in revisions] == [None, "Inspection scope corrected"]
    assert [r["title"] for r in revisions] == ["Inspect starter and control circuit",
                                               "Inspect starter and control circuit again"]
    assert [r["recorded_at"] for r in revisions] == sorted(r["recorded_at"] for r in revisions)
    assert body["work_detail"]["selected_revision"]["id"] == revisions[1]["id"]
    assert [e["kind"] for e in body["work_detail"]["events"]] == ["CREATED", "ASSIGN", "COMMENT", "COMPLETE", "REOPEN"]
    early = detail(info, first, "2026-10-20T11:59:05Z")  # before the revision at 11:59:06
    assert [r["revision_no"] for r in early["history"]["revisions"]] == [1]
    assert early["work_detail"]["selected_revision"]["id"] == revisions[0]["id"]


def test_detail_history_fixture_changes_selection(store) -> None:  # noqa: F811
    """C2 historical producer: `detail-history` corrects the first request at `--clock + 2s`; the read at `+1s`
    selects the earlier revision and the current read the correction."""
    info = seed("detail-history")
    first = info["requests"][0]
    then = detail(info, first, "2026-10-20T12:00:01Z")
    now = detail(info, first)
    assert then["work_detail"]["selected_revision"]["title"] == "Inspect starter and control circuit again"
    assert now["work_detail"]["selected_revision"]["title"] == seedmod.HISTORY_TITLE
    assert [r["revision_no"] for r in now["history"]["revisions"]] == [1, 2, 3]
    assert now["history"]["revisions"][2]["recorded_at"] == "2026-10-20T12:00:02.000000Z"


def test_subsecond_cutoff(store) -> None:  # noqa: F811
    """P-C1-8: one effective instant at full microsecond precision for every selection and every generated URL."""
    info = seed("detail")
    first = info["requests"][0]
    before = detail(info, first, "2026-10-20T11:59:05.999999Z")  # the revision is recorded at 11:59:06.000000
    at = detail(info, first, "2026-10-20T11:59:06.000000Z")
    assert before["selected"]["known_at"] == "2026-10-20T11:59:05.999999Z"
    assert [r["revision_no"] for r in before["history"]["revisions"]] == [1]
    assert [r["revision_no"] for r in at["history"]["revisions"]] == [1, 2]
    encoded = quote("2026-10-20T11:59:05.999999Z", safe="")
    assert before["links"]["overview"]["href"].endswith(f"&known_at={encoded}")
    # No requested cutoff: the snapshot read time with its microseconds, and no `known_at` in any URL.
    current = detail(info, first)
    assert current["selected"]["known_at"] == "2026-10-20T12:00:05.123456Z"
    assert all("known_at" not in current["links"][k]["href"] for k in ("overview", "record", "history"))


def test_exact_cutoff_hrefs(store) -> None:  # noqa: F811
    """P-C1-5/6: canonical Overview / Maintenance record / History values; `known_at` only when supplied."""
    info = seed("detail")
    first = info["requests"][0]
    base = f"/maintenance/requests/{first}"
    plain = detail(info, first)["links"]
    assert plain["overview"] == {"label": "Overview", "href": f"{base}?site_id=KOBO-001"}
    assert plain["record"] == {"label": "Maintenance record", "href": f"{base}/record?site_id=KOBO-001"}
    assert plain["history"] == {"label": "History", "href": f"{base}/history?site_id=KOBO-001"}
    pinned = detail(info, first, "2026-10-20T12:00:01Z")["links"]
    tail = "&known_at=2026-10-20T12%3A00%3A01.000000Z"
    assert pinned["overview"]["href"] == f"{base}?site_id=KOBO-001{tail}"
    assert pinned["record"]["href"] == f"{base}/record?site_id=KOBO-001{tail}"
    assert pinned["history"]["href"] == f"{base}/history?site_id=KOBO-001{tail}"


def test_site_name_label(store) -> None:  # noqa: F811
    """P-C1-7: `links.site.label` is the stored Site name read in the same snapshot, not the Site code."""
    info = seed("detail")
    engine_ = create_engine(URL)
    try:
        with engine_.connect() as c:
            name = c.execute(text("SELECT name FROM site WHERE id = :s"),
                             {"s": info["scopes"][("demo", "KOBO-001")][2]}).scalar_one()
    finally:
        engine_.dispose()
    assert detail(info, info["requests"][0])["links"]["site"] == {"label": name, "href": "/sites/KOBO-001"}


def test_work_asset_code_and_type(store) -> None:  # noqa: F811
    """`work_asset` is the scoped stored Asset code/type of the case's `asset_id`; null without one."""
    info = seed("detail")
    code, tenant, site = info["scopes"][("demo", "KOBO-001")]
    engine_ = create_engine(URL)
    try:
        with engine_.connect() as c:
            asset_id, asset_code, asset_type = c.execute(text(
                "SELECT CAST(id AS text), asset_code, asset_type FROM asset WHERE site_id = :s ORDER BY asset_code "
                "LIMIT 1"), {"s": site}).one()
    finally:
        engine_.dispose()
    w = writer(info, CLOCK + timedelta(seconds=1))
    try:
        _, made = w.svc.create_case(tenant, site, {
            "kind": "MAINTENANCE_REQUEST", "occurred_at": "2026-10-18T10:00:00Z", "asset_id": asset_id,
            "finding_links": [], "action_links": [], "title": "Inspect the asset", "narrative": "Asset inspection.",
            "cited_accepted_evidence_ids": [], "actor": dict(seedmod.ACTOR), "idempotency_key": "w601c-asset-0001"},
            W401_FIXTURE_SERVICE_PRINCIPAL_ID)
    finally:
        w.close()
    assert detail(info, made["id"])["work_asset"] == {"code": asset_code, "type": asset_type}
    assert detail(info, info["requests"][0])["work_asset"] is None


# --- operational records (CL3-3, P-C1-4, P-C1-10) --------------------------------------------------------------------

def test_case_linked_operational_record_root_time(store) -> None:  # noqa: F811
    """CL3-3: the `detail` REC on the first request, root occurrence `--clock` minus 2 days; none on the second."""
    info = seed("detail")
    first, second = info["requests"]
    [rec] = [c for c in info["commands"] if "operational_record_id" in c]
    items = detail(info, first)["history"]["operational_records"]
    assert items == [{"canonical_record_id": rec["canonical_record_id"], "head_id": rec["operational_record_id"],
                      "code": rec["code"], "kind": "OPERATOR_LOG", "body": "Checked the starter after the inspection.",
                      "root_occurred_at": "2026-10-18T12:00:00.000000Z", "occurred_at": "2026-10-18T12:00:00.000000Z",
                      "recorded_at": "2026-10-20T11:59:09.000000Z"}]
    assert rec["case_id"] == first and rec["code"].startswith("REC-")
    assert detail(info, second)["history"]["operational_records"] == []
    # Before the REC was recorded it is not selected.
    assert detail(info, first, "2026-10-20T11:59:08Z")["history"]["operational_records"] == []


def test_cross_case_root_head_correction(store) -> None:  # noqa: F811
    """P-C1-4: membership is the immutable root's `case_id`; the head at K supplies kind/body/times even when it
    names another case; a root is never admitted because a later head names the request."""
    info = seed("detail")
    first, second = info["requests"]
    [rec] = [c for c in info["commands"] if "operational_record_id" in c]
    w = writer(info, CLOCK + timedelta(seconds=10))
    site = ("demo", "KOBO-001")
    try:
        moved = w.post_operational_record(site, second, "Relay check belongs to the spare relay request.",
                                          kind="SHIFT_NOTE", occurred_at=CLOCK - timedelta(days=1), correction={
                                              "supersedes_record_id": rec["operational_record_id"],
                                              "canonical_record_id": rec["canonical_record_id"],
                                              "correction_reason": "Linked to the wrong request"})
        other = w.post_operational_record(site, second, "Spare relay checked.",
                                          occurred_at=CLOCK - timedelta(days=2, hours=1))
        w.post_operational_record(site, first, "Spare relay checked for the starter request.",
                                  occurred_at=CLOCK - timedelta(days=1), correction={
                                      "supersedes_record_id": other["id"], "canonical_record_id": other["id"],
                                      "correction_reason": "Moved to the starter request"})
    finally:
        w.close()
    at = CLOCK + timedelta(seconds=20)
    [item] = detail(info, first, at=at)["history"]["operational_records"]
    assert item["canonical_record_id"] == rec["canonical_record_id"] and item["code"] == rec["code"]
    assert item["head_id"] == moved["id"] and item["kind"] == "SHIFT_NOTE"
    assert item["body"] == "Relay check belongs to the spare relay request."
    assert item["root_occurred_at"] == "2026-10-18T12:00:00.000000Z"
    assert item["occurred_at"] == "2026-10-19T12:00:00.000000Z"
    assert item["recorded_at"] == "2026-10-20T12:00:10.000000Z"
    [own] = detail(info, second, at=at)["history"]["operational_records"]
    assert own["canonical_record_id"] == other["id"] and own["code"] == other["public_code"]
    assert own["body"] == "Spare relay checked for the starter request."
    # At a cutoff before the correction the root is its own head.
    [early] = detail(info, first, iso(CLOCK + timedelta(seconds=9)), at=at)["history"]["operational_records"]
    assert early["head_id"] == rec["operational_record_id"] and early["kind"] == "OPERATOR_LOG"


# --- links (CL3-5, P-C1-1, P-C1-11) ----------------------------------------------------------------------------------

def test_source_incident_link(store) -> None:  # noqa: F811
    """CL3-5 / P-C1-1 / P-C1-11: the `detail-linked` third request carries the source incident (root occurrence day,
    `known_at` only when supplied) and lineage-true exact Finding/Action links; the `detail` requests carry none."""
    info = seedmod.seed(URL, "detail-linked", CLOCK)
    tenant, site = UUID(info["tenant_id"]), UUID(info["site_id"])
    info["scopes"] = {("demo", "KOBO-001"): ("KOBO-001", tenant, site)}
    request_id = info["request_id"]
    [incident] = [w for w in info["written"] if w["kind"] == "INCIDENT"]
    window = "from=2026-10-18T00%3A00%3A00Z&to=2026-10-19T00%3A00%3A00Z"
    body = detail(info, request_id)
    assert body["work_detail"]["case"]["incident_id"] == incident["case_id"]
    assert body["links"]["source_incident"] == {"label": f"Incident {incident['code']}",
                                                "href": f"/sites/KOBO-001/work/incidents?{window}"}
    pinned = detail(info, request_id, "2026-10-20T12:00:01Z")["links"]["source_incident"]
    assert pinned["href"] == f"/sites/KOBO-001/work/incidents?{window}&known_at=2026-10-20T12%3A00%3A01.000000Z"
    fid, frev = info["finding_id"], info["finding_revision_id"]
    assert body["links"]["findings"] == [{"label": f"Finding {fid[:8]}",
                                          "href": f"/sites/KOBO-001/findings/{fid}?revision_id={frev}"}]
    [action] = body["links"]["actions"]
    # Post-W6 W6 Q10 (R366): the stored public Action code, never `Action {id8}` when a code is stored.
    engine_ = create_engine(URL)
    try:
        with engine_.connect() as c:
            code = c.execute(text("SELECT action_code FROM action WHERE id = :a"),
                             {"a": info["action_id"]}).scalar_one()
    finally:
        engine_.dispose()
    assert code.startswith("ACT-") and action["label"] == code and action["href"]
    assert info["action_event_id"] in action["href"]
    assert info["detail_links"]["source_incident"] == body["links"]["source_incident"]
    plain = [w["case_id"] for w in info["written"] if w["kind"] == "MAINTENANCE_REQUEST"][0]
    none = detail(info, plain)["links"]
    assert none["source_incident"] is None and none["findings"] == [] and none["actions"] == []


# --- refusals (P-C1-2, P-C1-3, P-C1-9, X4) ---------------------------------------------------------------------------

def test_wrong_site_or_tenant_is_404(store) -> None:  # noqa: F811
    info = seed("detail")
    first = info["requests"][0]
    api = Api(demo_scope(info))
    try:
        refused(api.get(first, ("site_id", "KOBO-002")), 404, *NOT_FOUND)
        refused(api.get(str(uuid.uuid4()), ("site_id", "KOBO-001")), 404, *NOT_FOUND)
        refused(api.get(first, ("site_id", "NOPE-001")), 404, "SITE_NOT_FOUND",
                "No imported Site 'NOPE-001' in this tenant.")
    finally:
        api.close()
    other = Api(demo_scope(info, "w601-other"))
    try:
        refused(other.get(first, ("site_id", "KOBO-001")), 404, *NOT_FOUND)
    finally:
        other.close()
    # Before the case was created it is not found at that cutoff.
    early = Api(demo_scope(info))
    try:
        refused(early.get(first, ("site_id", "KOBO-001"), ("known_at", "2026-10-20T11:58:59Z")), 404, *NOT_FOUND)
    finally:
        early.close()


def test_incident_id_is_404(store) -> None:  # noqa: F811
    """P-C1-2: the request route serves only MAINTENANCE_REQUEST; an INCIDENT ID at its own Site is 404."""
    info = seed("incidents")
    incident = next(w for w in info["written"] if w["kind"] == "INCIDENT" and w["site_code"] == "KOBO-001"
                    and w["tenant"] == "demo")
    api = Api(demo_scope(info))
    try:
        refused(api.get(incident["case_id"], ("site_id", "KOBO-001")), 404, *NOT_FOUND)
        assert api.ok(info["requests"][0])["selected"]["case_kind"] == "MAINTENANCE_REQUEST"
    finally:
        api.close()


def test_refusal_order_401_403_404_503(store) -> None:  # noqa: F811
    """P-C1-9: authenticate, then one `site_id`, then access 401/403, then scope 503/404, then case and cutoff;
    every refusal body is detail-only `{code, message}`."""
    info = seed("detail")
    first = info["requests"][0]
    scope = demo_scope(info)
    q = ("site_id", "KOBO-001")
    unauth = Api(scope, authenticate=lambda request: 401, deny=("KOBO-001",))
    try:
        refused(unauth.get(first, q), 401, "UNAUTHENTICATED", "Sign in to read work.")
        refused(unauth.get("not-a-uuid"), 401, "UNAUTHENTICATED", "Sign in to read work.")
    finally:
        unauth.close()
    denied = Api(scope, deny=("KOBO-001",))
    try:
        refused(denied.get(first, q), 403, "SITE_SCOPE_FORBIDDEN", "No access to Site 'KOBO-001'.")
        refused(denied.get(first), 404, *NOT_FOUND)  # the `site_id` check precedes access
    finally:
        denied.close()
    signed_out = Api(scope, access=lambda request, code: 401)
    try:
        refused(signed_out.get(first, q), 401, "UNAUTHENTICATED", "Sign in to read work.")
    finally:
        signed_out.close()

    def outage(code: str):
        raise SiteStoreUnavailable("down")

    down_url = "postgresql+psycopg://x:y@127.0.0.1:1/down_test"
    for api in (Api(outage), Api(None), Api(scope, no_details=True), Api(scope, url=down_url)):
        try:
            refused(api.get(first, q), 503, *DOWN)
        finally:
            api.close()
    api = Api(scope)
    try:
        bad_k = ("INVALID_KNOWN_AT", "'known_at' must be one UTC instant no later than the read time.")
        refused(api.get(first, q, ("known_at", "2026-10-20T12:00:00Z"), ("known_at", "2026-10-20T12:00:01Z")),
                422, *bad_k)
        refused(api.get(first, q, ("known_at", "2026-10-20T12:00:00")), 422, *bad_k)
        refused(api.get(first, q, ("known_at", "2026-10-20T12:00:06Z")), 422, *bad_k)  # after the read time
        assert api.get(first, q, ("unexpected", "value")).status_code == 200  # unknown keys are ignored
    finally:
        api.close()


def test_missing_site_id_or_bad_case_id_is_404(store) -> None:  # noqa: F811
    """A2Q X4: a missing, empty or repeated `site_id`, or a non-UUID case ID, is 404 after authentication with no
    store read (the Site scope is not consulted for `site_id` refusals; no snapshot is opened for any)."""
    info = seed("detail")
    first = info["requests"][0]
    calls: list[str] = []

    def scope(code: str):
        calls.append(code)
        return demo_scope(info)(code)

    class NoRead:
        def snapshot(self, work):
            raise AssertionError("no store read is allowed")

    api = Api(scope, details=GlobalWorkDetailService(NoRead()))
    try:
        for params in ((), (("site_id", ""),), (("site_id", "KOBO-001"), ("site_id", "KOBO-001"))):
            refused(api.get(first, *params), 404, *NOT_FOUND)
        assert calls == []
        refused(api.get("not-a-uuid", ("site_id", "KOBO-001")), 404, *NOT_FOUND)
        refused(api.get("not-a-uuid", ("site_id", "KOBO-001"), ("known_at", "bad")), 404, *NOT_FOUND)
    finally:
        api.close()


def _clone(c, table: str, source_id: str, overrides: dict, key: str = "id") -> None:
    """Copy one row with typed overrides; every text `*_key` column gets a fresh value (raw SQL, test only)."""
    cols = c.execute(text("SELECT column_name, udt_name FROM information_schema.columns WHERE table_name = :t "
                          "AND table_schema = current_schema() ORDER BY ordinal_position"), {"t": table}).all()
    values, params = [], {"src": source_id}
    for name, udt in cols:
        if name in overrides:
            values.append(f"CAST(:{name} AS {udt})")
            params[name] = overrides[name]
        elif name.endswith("_key") and udt == "text":
            values.append(f"CAST(:{name} AS text)")
            params[name] = f"w601c-missing-{table}-{name}"
        else:
            values.append(name)
    names = ", ".join(n for n, _ in cols)
    c.execute(text(f"INSERT INTO {table} ({names}) SELECT {', '.join(values)} FROM {table} "
                   f"WHERE {key} = CAST(:src AS uuid)"), params)


def test_missing_created_is_503(store) -> None:  # noqa: F811
    """P-C1-3: a request with a revision but no CREATED event (inserted by raw SQL in a rolled-back transaction) is
    503 `WORK_STORE_UNAVAILABLE` on the global route; production service paths never write it."""
    info = seed("detail")
    first = info["requests"][0]
    new = str(uuid.uuid4())
    engine_ = create_engine(URL)
    try:
        with engine_.connect() as c:
            tx = c.begin()
            try:
                _clone(c, "work_case", first, {"id": new, "public_no": "999999", "public_code": "WR-999999"})
                _clone(c, "maintenance_work_request", first, {"id": new})
                rev = c.execute(text("SELECT CAST(id AS text) FROM work_case_revision WHERE case_id = :c "
                                     "AND revision_no = 1"), {"c": first}).scalar_one()
                _clone(c, "work_case_revision", rev, {"id": str(uuid.uuid4()), "case_id": new})
                assert c.execute(text("SELECT count(*) FROM work_event WHERE case_id = :c"), {"c": new}).scalar() == 0

                class SameConnection:
                    def snapshot(self, work):
                        return work(GlobalReadTx(c, READ_NOW, build_link_rows_reader(), _link_read_ports()))

                service = GlobalWorkDetailService(SameConnection())
                _, tenant, site = info["scopes"][("demo", "KOBO-001")]
                with pytest.raises(WorkStoreUnavailable):
                    service.detail(tenant, site, "KOBO-001", new, [])
                api = Api(demo_scope(info), details=service)
                try:
                    refused(api.get(new, ("site_id", "KOBO-001")), 503, *DOWN)
                    assert api.get(first, ("site_id", "KOBO-001")).status_code == 200
                finally:
                    api.close()
            finally:
                tx.rollback()
    finally:
        engine_.dispose()


if URL:
    from test_w202_cold_replay_postgres import chain  # noqa: F401,F811
    from test_w502_domain_intent_postgres import cold  # noqa: F401
    from test_w502_domain_work_links_postgres import bind, expected_link, rows_by_id, site_index
    from test_w502_domain_work_links_postgres import iso as micro_iso

    from assetops_backend.work.site_index import _action_link, action_selection_key


def test_domain_action_link_matches_w4(cold) -> None:  # noqa: F811
    """W5-02a K1c ruling 1: an explicitly bound cold domain Action on a Maintenance request reaches the global
    request detail exactly as the W4 Site link at the same cutoff; an absent or wrong-Site pin leaves href null."""
    b = bind(cold)
    scope = lambda code: (cold.code, cold.t, cold.s) if code == cold.code else None  # noqa: E731
    api = Api(scope, None)
    try:
        body = api.ok(b.request, site=cold.code, known_at=micro_iso(b.after))
        old = api.ok(b.request, site=cold.code, known_at=micro_iso(b.before))
    finally:
        api.close()
    w4 = rows_by_id(site_index(cold, "maintenance", b.window, [micro_iso(b.after)]))[b.request]["action_links"]
    domain = expected_link(cold, b.aid)
    assert w4 == [domain]
    with cold.engine.connect() as c:  # Post-W6 W6 Q10: the global label is the stored domain Action code
        code = c.execute(text("SELECT action_code FROM domain_action WHERE id = :a"), {"a": b.aid}).scalar_one()
    assert body["links"]["actions"] == [{"label": code, "href": domain["href"]}]
    assert body["selected"]["site_domain"] == "COLDCHAIN" and body["links"]["site"]["href"] == f"/sites/{cold.code}"
    assert body["links"]["actions"][0]["href"] == f"/sites/{cold.code}/actions/{b.aid}/verification"
    raw = body["work_detail"]["action_links"]
    assert raw == [{k: domain[k] for k in ("kind", "action_id", "action_event_id", "finding_revision_id")}]
    assert action_selection_key(raw[0]) == ("DOMAIN_ACTION", b.aid, cold.revision_id)
    assert old["links"]["actions"] == []
    # Absent pin (no selection) or a pin without lineage (another Site's selection never keys this link): null.
    assert _action_link(cold.code, raw[0], None)["href"] is None
    assert _action_link(cold.code, raw[0], {"lineage": False})["href"] is None


def test_action_without_a_stored_code_keeps_its_honest_label() -> None:
    """Post-W6 W6 Q10: an Action with no stored code keeps `Action {id8}`; no ACT code is invented. Only read codes
    enter the basis pairs."""
    from assetops_backend.work.global_index import coded_actions

    class Reads:
        def action_codes(self, tenant_id, site_id, ids):
            return {"00000000-0000-4000-8000-0000000000a1": "ACT-000007"}

    links = [{"action_id": "00000000-0000-4000-8000-0000000000a1", "label": "Action 00000000", "href": "/x"},
             {"action_id": "00000000-0000-4000-8000-0000000000b2", "label": "Action 00000000", "href": None}]
    out, pairs = coded_actions(Reads(), None, None, links)
    assert [x["label"] for x in out] == ["ACT-000007", "Action 00000000"]
    assert [x["href"] for x in out] == ["/x", None]
    assert pairs == [["00000000-0000-4000-8000-0000000000a1", "ACT-000007"]]


# ---- Post-W6 W6 Q2/Q3/Q4/Q10: an EV Site on every global root and the detail ----------------------------------
# The EV replay chain recreates the database on teardown, so this test stays last in the module.

if URL:
    from test_r373_request_access import ev  # noqa: F401
    from test_w401_work_service_postgres import PRINCIPAL
    from test_w502_domain_intent_postgres import head_event, link_body
    from test_w504_ev_intent_postgres import _now, ev_action, ev_service

    from assetops_backend.work.global_index import CURSOR_KEY_ENV, GlobalWorkIndexService


def test_ev_site_rows_open_the_ev_home(ev, monkeypatch) -> None:  # noqa: F811
    """R352/R353/R359/R366 on an EV Site the current walkthrough producers cannot populate on every root: each global
    row and the detail carry `site_domain` EV_CHARGING and a Site link to `/sites/{code}/ev`; Site Work tab links stay
    on the base route; the linked request opens its Overview; the EV domain Action is labelled by its stored code."""
    monkeypatch.setenv(CURSOR_KEY_ENV, "c3" * 32)
    start = _now(ev) - timedelta(minutes=5)
    site = ("ev", ev.code)
    write = seedmod.Writer(URL, seedmod.WriteClock(start), {site: {"tenant": ev.t, "site": ev.s, "site_code": ev.code}},
                           start)
    try:
        inc = write.incident(site, "EV connector stopped")
        req = write.request(site, inc["id"], "Inspect connector c1")
        write.plan(site, "Connector quarterly inspection", "CALENDAR", due_at=start + timedelta(days=30))
        write.post_operational_record(site, req["id"], "Connector c1 checked on site.")
    finally:
        write.close()
    svc = ev_service(ev)
    try:
        status, action = svc.create_action(ev.t, ev.s, ev.code, ev_action(ev, "w6-ev-action"), PRINCIPAL)
        assert status == 201, action
        status, _ = svc.post_case_link(ev.t, ev.s, ev.code, action["id"],
                                       link_body(req["id"], req["revision"]["id"], head_event(ev, req["id"]),
                                                 key="w6-ev-link"), PRINCIPAL)
        assert status == 201
    finally:
        svc._store.dispose()
    with ev.engine.connect() as c:
        code = c.execute(text("SELECT action_code FROM domain_action WHERE id = :a"), {"a": action["id"]}).scalar_one()
    lo = (start - timedelta(days=3)).replace(hour=0, minute=0, second=0, microsecond=0)
    window = {"from": lo.strftime("%Y-%m-%dT%H:%M:%SZ"), "to": (lo + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")}
    read = PostgresGlobalWorkRead(URL, link_rows=build_link_rows_reader(), ports=_link_read_ports())
    app = FastAPI()
    app.include_router(build_global_work_router(
        GlobalWorkIndexService(read), lambda: ev.t, access=lambda request, c: None,
        unavailable=(SiteStoreUnavailable,), scope=lambda c: (ev.code, ev.t, ev.s) if c == ev.code else None,
        details=GlobalWorkDetailService(read)))
    client = TestClient(app)
    home = f"/sites/{quote(ev.code, safe='')}/ev"
    try:
        bodies = {}
        for root in ("incidents", "maintenance", "preventive", "operational-records"):
            response = client.get(f"/api/work/{root}", params=window)
            assert response.status_code == 200, response.text
            bodies[root] = response.json()["rows"]
            assert bodies[root], root
            for row in bodies[root]:
                assert row["site_domain"] == "EV_CHARGING"
                assert row["links"]["site"] == {"label": row["site_name"], "href": home}
        [inc_row] = [r for r in bodies["incidents"] if r["case_id"] == inc["id"]]
        assert inc_row["links"]["site_incidents"]["href"].startswith(f"/sites/{quote(ev.code, safe='')}/work/incidents?")
        assert inc_row["linked_requests"] == [{"label": req["code"], "href": (
            f"/maintenance/requests/{req['id']}?site_id={quote(ev.code, safe='')}")}]
        [req_row] = [r for r in bodies["maintenance"] if r["case_id"] == req["id"]]
        assert [x["label"] for x in req_row["action_links"]] == [code]
        assert req_row["links"]["site_maintenance"]["href"].startswith(
            f"/sites/{quote(ev.code, safe='')}/work/maintenance?")
        response = client.get(f"/api/work/requests/{req['id']}", params={"site_id": ev.code})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["selected"]["site_domain"] == "EV_CHARGING"
        assert body["links"]["site"]["href"] == home
        assert body["links"]["source_incident"]["href"].startswith(f"/sites/{quote(ev.code, safe='')}/work/incidents?")
        assert [x["label"] for x in body["links"]["actions"]] == [code]
    finally:
        read.dispose()
