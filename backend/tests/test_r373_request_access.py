"""R373 (audit B19-15, High D3): one Site-read access seam for Site Work and global Work.

`.agent/post-W6-R373-rulings.md` Q2-Q6. `create_app(site_read_access=...)` passes ONE callable to the W4 Site Work
router, the domain-work `WorkGate` and the global Work router (request detail and the four lists). A denied Site
answers W4's 403 `SITE_SCOPE_FORBIDDEN` on both request-detail routes, byte-identical for an existing linked request,
an unknown UUID, a malformed ID and a request at another Site, so no request existence or state leaks; the global
lists silently drop the denied Site from rows, counts, paging and the cursor scope.

Every test composes the product app through `assetops_backend.main.create_app`, so removing the shared wiring from
`main.py` fails them (non-vacuity, recorded in `.agent/post-W6-R373-packet.md`). The no-database tests run anywhere;
the Postgres tests need ASSETOPS_TEST_DATABASE_URL naming a `*_test` database and use the reviewed producers: the
`tools/w601_seed.py` `detail-linked` mini request, the W5-02 cold replay with a bound domain Action, and the W5-04
EV replay with a bound EV domain Action.
"""

from __future__ import annotations

import base64
import importlib.util
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from assetops_backend import main

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
needs_db = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

REPO = Path(__file__).resolve().parents[2]
CLOCK = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)  # the W6-01 B1 fixture clock
WINDOW = {"from": "2026-10-14T00:00:00Z", "to": "2026-10-21T00:00:00Z"}
KEY = "a7" * 32
UNKNOWN = "00000000-0000-4000-8000-000000000373"
MALFORMED = "not-a-case-id"
ROOTS = ("incidents", "maintenance", "preventive", "operational-records")


def forbidden(code: str) -> bytes:
    return json.dumps({"detail": {"code": "SITE_SCOPE_FORBIDDEN", "message": f"No access to Site '{code}'."}},
                      separators=(",", ":")).encode()


class Grant:
    """A server-side Site grant: the one callable handed to `create_app(site_read_access=...)`."""

    def __init__(self, *sites: str) -> None:
        self.sites = {s.upper() for s in sites}

    def __call__(self, request, code: str) -> int | None:
        return None if code.upper() in self.sites else 403


def app(monkeypatch, access, database: str | None) -> TestClient:
    if database is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", database)
    monkeypatch.setenv("ASSETOPS_WORK_CURSOR_KEY_HEX", KEY)
    return TestClient(main.create_app(site_read_access=access))


def site_detail(client: TestClient, code: str, case_id: str):
    return client.get(f"/api/sites/{code}/work/cases/{case_id}")


def global_detail(client: TestClient, code: str, case_id: str):
    return client.get(f"/api/work/requests/{case_id}", params={"site_id": code})


def denied_identically(client: TestClient, code: str, case_ids: list[str]) -> None:
    """Ruling Q3: every ID, on both routes, gets the same 403 bytes; nothing about the case varies the body."""
    expected = forbidden(code)
    for case_id in case_ids:
        for response in (site_detail(client, code, case_id), global_detail(client, code, case_id)):
            assert response.status_code == 403, (case_id, response.text)
            assert response.content == expected, (case_id, response.content)
            assert "www-authenticate" not in response.headers


# --- without a database: the shared callable reaches every Work read before scope or store ------------------------

def test_denied_site_is_the_same_403_on_both_detail_routes_without_a_database(monkeypatch) -> None:
    client = app(monkeypatch, Grant(), None)
    denied_identically(client, "KOBO-001", [UNKNOWN, MALFORMED, str(uuid4())])
    # The domain-work read is behind the same gate.
    response = client.get("/api/sites/KOBO-001/domain-work/action-index")
    assert response.status_code == 403 and response.json()["detail"]["code"] == "SITE_SCOPE_FORBIDDEN"


def test_allowed_site_advances_past_access_to_the_existing_refusals(monkeypatch) -> None:
    client = app(monkeypatch, Grant("KOBO-001"), None)
    for response in (site_detail(client, "KOBO-001", UNKNOWN), global_detail(client, "KOBO-001", UNKNOWN)):
        assert response.status_code in (503, 404), response.text
        assert response.json()["detail"]["code"] != "SITE_SCOPE_FORBIDDEN"
    # Ruling Q2: the detail keeps its 503 when no detail service is composed (no database here), after access.
    assert global_detail(client, "KOBO-001", UNKNOWN).json()["detail"]["code"] == "WORK_STORE_UNAVAILABLE"


def test_the_default_composition_still_admits_the_development_operator(monkeypatch) -> None:
    """Ruling Q1: today's default product principal is admitted on both routes (no 403); R373 fixes the wiring."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(main.create_app())
    for response in (site_detail(client, "KOBO-001", UNKNOWN), global_detail(client, "KOBO-001", UNKNOWN)):
        assert response.status_code != 403, response.text


# --- Postgres: one real linked request per vertical ---------------------------------------------------------------

if URL:
    from sqlalchemy import text

    from test_s1_bindings_postgres import engine, imported, store  # noqa: F401
    from test_w202_cold_replay_postgres import chain  # noqa: F401
    from test_w401_work_service_postgres import PRINCIPAL, request as request_body
    from test_w502_domain_intent_postgres import cold  # noqa: F401
    from test_w502_domain_work_links_postgres import bind
    import test_w205b_ev_replay_postgres as ev_replay
    from ev_depth_cases import settled
    from test_w504_ev_intent_postgres import REVISION_COLS, _case, _now, ev_action, ev_service

    from assetops_backend.work.composition import _link_read_ports, build_work_service

    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from test_w502_domain_intent_postgres import head_event, link_body

    _spec = importlib.util.spec_from_file_location("w601_seed", REPO / "tools" / "w601_seed.py")
    seedmod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(seedmod)


def other_site_request(when: datetime, occurred: datetime) -> SimpleNamespace:
    """A second demo Site (KOBO-002) with one W4 request: the 'request at another Site' and the granted list Site."""
    owned = PostgresFoundationStore(URL)
    try:
        result = imported(owned, "KOBO-002", when - timedelta(days=1))
    finally:
        owned._engine.dispose()
    t, s = result.tenant.id, result.site.id
    work = build_work_service(URL)
    try:
        status, made = work.create_case(t, s, request_body(f"r373-other-{uuid4().hex[:8]}",
                                                         occurred_at=occurred.strftime("%Y-%m-%dT%H:%M:%S.%fZ")), PRINCIPAL)
    finally:
        work._store.dispose()
    assert status == 201, made
    return SimpleNamespace(code="KOBO-002", t=t, s=s, request=made["id"])


def vertical_proof(monkeypatch, code: str, linked: str, other: SimpleNamespace, window: dict[str, str],
                   other_window: dict[str, str] | str | None = None) -> None:
    """Ruling Q6, per vertical: granted reads the linked request on both routes and lists it; denied is the identical
    403 for the linked, unknown, malformed and foreign-Site IDs, and the lists drop it with no refusal."""
    granted = app(monkeypatch, Grant(code, other.code), URL)
    site_body = site_detail(granted, code, linked)
    assert site_body.status_code == 200, site_body.text
    detail = global_detail(granted, code, linked)
    assert detail.status_code == 200, detail.text
    assert detail.json()["work_detail"]["case"]["id"] == linked
    assert detail.json()["work_detail"]["action_links"] or detail.json()["work_detail"]["finding_links"], \
        "the vertical's request must be a real linked request (ruling Q6)"
    # `other_window` is for a request written at a different clock than the linked one (mini: fixture clock vs wall
    # clock), so no single window has to span both and grow past the 31-day maximum as real time passes.
    if other_window == "own":  # a one-day window around the other request's own recorded created_at: no wall-clock read here
        stamp = global_detail(granted, other.code, other.request).json()["work_detail"]["case"]["created_at"]
        other_window = midnight_window(datetime.fromisoformat(stamp.replace("Z", "+00:00")), datetime.fromisoformat(stamp.replace("Z", "+00:00")))
    other_window = other_window or window
    assert linked in [r["case_id"] for r in granted.get("/api/work/maintenance", params=window).json()["rows"]]
    assert other.request in [r["case_id"] for r in granted.get("/api/work/maintenance", params=other_window).json()["rows"]]

    denied = app(monkeypatch, Grant(other.code), URL)
    denied_identically(denied, code, [linked, UNKNOWN, MALFORMED, other.request])
    body = denied.get("/api/work/maintenance", params=window)
    assert body.status_code == 200, body.text
    rows = body.json()["rows"]
    assert linked not in [r["case_id"] for r in rows]
    assert all(r["site_code"] != code for r in rows)
    other_rows = denied.get("/api/work/maintenance", params=other_window).json()["rows"]
    assert other.request in [r["case_id"] for r in other_rows]
    # The other Site's request is still readable where it lives: the denial is per Site, not per principal.
    assert global_detail(denied, other.code, other.request).status_code == 200


@needs_db
def test_mini_linked_request_is_denied_identically_and_filtered(store, monkeypatch) -> None:  # noqa: F811
    info = seedmod.seed(URL, "detail-linked", CLOCK)
    other = other_site_request(CLOCK - timedelta(days=3), CLOCK - timedelta(days=2))
    vertical_proof(monkeypatch, "KOBO-001", info["request_id"], other, midnight_window(CLOCK - timedelta(days=5), CLOCK), "own")


# --- Postgres: all four global lists drop a denied Site from rows, counts, paging and the cursor scope ------------

def cursor_sites(cursor: str) -> list[str]:
    return json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode())["authorized_site_ids"]


def walk(client: TestClient, root: str, params: dict[str, str]) -> tuple[dict, list[dict], list[str]]:
    first = client.get(f"/api/work/{root}", params={**params, "limit": "1"})
    assert first.status_code == 200, first.text
    body, rows, cursors = first.json(), list(first.json()["rows"]), []
    page = body
    while page["next_cursor"]:
        cursors.append(page["next_cursor"])
        nxt = client.get(f"/api/work/{root}", params={**params, "limit": "1", "cursor": page["next_cursor"]})
        assert nxt.status_code == 200, nxt.text
        page = nxt.json()
        rows.extend(page["rows"])
    return body, rows, cursors


@needs_db
@pytest.mark.parametrize("root,fixture", [("incidents", "incidents"), ("maintenance", "maintenance"),
                                          ("preventive", "preventive"),
                                          ("operational-records", "operational")])
def test_global_lists_drop_a_denied_site(root, fixture, store, monkeypatch) -> None:  # noqa: F811
    info = seedmod.seed(URL, fixture, CLOCK)
    demo = {s["site_code"]: s["site_id"] for s in info["sites"] if s["tenant"] == "demo"}
    params = {**WINDOW, "known_at": "2026-10-20T12:00:10Z"}
    if root == "operational-records":
        params["kind"] = "OPERATOR_LOG"
    full, full_rows, full_cursors = walk(app(monkeypatch, Grant("KOBO-001", "KOBO-002"), URL), root, params)
    assert any(r["site_code"] == "KOBO-001" for r in full_rows), "non-empty proof: the denied Site has rows"
    assert full_cursors, "non-empty proof: the wider grant pages (limit 1), so the cursor checks below run"
    assert all(demo["KOBO-001"] in cursor_sites(c) for c in full_cursors)

    body, rows, cursors = walk(app(monkeypatch, Grant("KOBO-002"), URL), root, params)
    assert [r for r in rows if r["site_code"] == "KOBO-001"] == []
    assert rows == [r for r in full_rows if r["site_code"] != "KOBO-001"]
    assert body["total_count"] == len(rows) < full["total_count"]
    if body["state_counts"] is not None:
        assert sum(body["state_counts"].values()) == len(rows)
    assert bool(cursors) == (len(rows) > 1)
    for cursor in cursors:
        assert demo["KOBO-001"] not in cursor_sites(cursor) and demo["KOBO-002"] in cursor_sites(cursor)
    # A cursor minted under the wider grant never pages the narrower one into the denied Site's rows.
    if full_cursors:
        replay = app(monkeypatch, Grant("KOBO-002"), URL).get(
            f"/api/work/{root}", params={**params, "limit": "1", "cursor": full_cursors[0]})
        assert replay.status_code != 200 or all(r["site_code"] != "KOBO-001" for r in replay.json()["rows"])
    # Fully denied: an empty scope, still never a Site 403/404.
    empty = app(monkeypatch, Grant(), URL).get(f"/api/work/{root}", params=params)
    assert empty.status_code == 200 and empty.json()["rows"] == [] and empty.json()["total_count"] == 0


# The `store`-based tests (mini, lists) run before the replay-chain ones (cold, EV), whose teardown recreates the
# database and would drop the module-scoped `engine` connection the `store` fixture truncates with.


def midnight_window(before: datetime, after: datetime) -> dict[str, str]:
    lo = (before - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    hi = after.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return {"from": lo.strftime("%Y-%m-%dT%H:%M:%SZ"), "to": hi.strftime("%Y-%m-%dT%H:%M:%SZ")}


@needs_db
def test_cold_linked_request_is_denied_identically_and_filtered(cold, monkeypatch) -> None:  # noqa: F811
    b = bind(cold)
    other = other_site_request(b.before, b.before - timedelta(minutes=1))
    vertical_proof(monkeypatch, cold.code, b.request, other, midnight_window(b.before, b.after))


@pytest.fixture()
def ev(tmp_path, monkeypatch):
    """The W5-04 `ev` fixture (`test_w504_ev_intent_postgres.ev`) over the W2-05b EV replay chain. The EV `chain`
    fixture name is taken here by the cold one, so its factory is restated under this fixture, unchanged."""
    opened = []

    def make(case: str):
        ev_replay.hold_uuids(monkeypatch, 0x0500 + ev_replay.CASES.index(case) + 1)
        built = ev_replay.Chain(case, tmp_path / case)
        opened.append(built)
        return built.open()

    try:
        built = settled(make, "interrupted")
        with built.engine.connect() as c:
            row = c.execute(text(
                f"SELECT {REVISION_COLS} FROM finding_revision WHERE site_id = :s AND domain = 'ev_charging' "
                "AND lifecycle = 'SUPPORTED' ORDER BY created_at DESC, id LIMIT 1"), {"s": built.site_id}).first()
        assert row is not None, "the EV replay wrote no SUPPORTED EV Finding revision"
        work = build_work_service(URL)
        yield SimpleNamespace(t=built.tenant_id, s=built.site_id, code=built.site_code, engine=built.engine,
                              built=built, revision=dict(row._mapping), ports=_link_read_ports(), work=work)
        work._store.dispose()
    finally:
        for b in opened:
            b.close()


@needs_db
def test_ev_linked_request_is_denied_identically_and_filtered(ev, monkeypatch) -> None:
    """The EV bind equivalent: an EV domain Action through the composed command service, explicitly linked to a W4
    request at its selected head (the W5-04 path, not raw SQL)."""
    svc = ev_service(ev)
    try:
        status, action = svc.create_action(ev.t, ev.s, ev.code, ev_action(ev, "r373-ev-action"), PRINCIPAL)
        assert status == 201, action
        before = _now(ev)
        case_id, revision_id, _ = _case(ev, "r373-ev-request")
        status, _ = svc.post_case_link(ev.t, ev.s, ev.code, action["id"],
                                       link_body(case_id, revision_id, head_event(ev, case_id), key="r373-ev-link"),
                                       PRINCIPAL)
        assert status == 201
        after = _now(ev)
    finally:
        svc._store.dispose()
    other = other_site_request(before, before - timedelta(minutes=1))
    vertical_proof(monkeypatch, ev.code, case_id, other, midnight_window(before, after))
