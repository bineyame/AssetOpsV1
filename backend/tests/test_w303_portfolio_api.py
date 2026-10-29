"""W3-03 run 1a: the unmounted Portfolio router and service over fake selectors (no database).

Refusal order and bodies, the lifecycle/lens membership, Portfolio re-sort, five-member cursor and its fence, and
the full-scope `estate-selection/2` token. The persisted proof is `test_w303_portfolio_scope_snapshot_postgres.py`.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.estate import portfolio
from assetops_backend.estate.coverage import DOMAIN_OF_SITE_TYPE
from assetops_backend.estate.index import _finding_links
from assetops_backend.estate.portfolio import EstatePortfolioService
from assetops_backend.estate.scope import (
    MESSAGES, PORTFOLIO_CURSOR_KEY_ENV, EstateSelectionInconsistent, EstateStoreUnavailable, encode_cursor,
    encode_portfolio_cursor, parse_request, selection_token)
from assetops_backend.estate_portfolio_api import build_estate_portfolio_router
from test_w301_estate_index_postgres import URL as _PG_URL

if _PG_URL:
    from test_w301_estate_index_postgres import engine  # noqa: F401 - fixture for the builder test

T = UUID("30000000-0000-4000-8000-000000000001")
MG, CO = "30000000-0000-4000-8000-000000000011", "30000000-0000-4000-8000-000000000012"
READ_AT = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)
WINDOW = {"from": "2026-10-13T00:00:00Z", "to": "2026-10-20T00:00:00Z"}
D0 = datetime(2026, 10, 13, tzinfo=timezone.utc)
SITES = [{"site_id": UUID(MG), "site_code": "KOBO 001", "site_name": "Kobo", "site_type": "MINIGRID",
          "site_code_key": "kobo 001"},
         {"site_id": UUID(CO), "site_code": "COLD-1", "site_name": "Cold", "site_type": "COLDCHAIN",
          "site_code_key": "cold-1"}]
FINDING = {n: f"40000000-0000-4000-8000-0000000000{n:02d}" for n in range(1, 40)}
EMPTY_ARRAYS = {"selected_finding_revision_ids": [], "selected_action_event_ids": [],
                "selected_assessment_revision_ids": [], "selected_consequence_revision_ids": [],
                "selected_assumption_revision_ids": [], "cited_accepted_evidence_ids": []}
REFUSAL_KEYS = {"code", "message", "rows", "total_count", "value_cards", "objectives", "money"}
KEY_HEX = "5c" * 32  # test-only (r1b Q-1b-1); never a committed default for any server
KEY = bytes.fromhex(KEY_HEX)


@pytest.fixture(autouse=True)
def _cursor_key(monkeypatch):
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, KEY_HEX)


def signed(payload):
    """A validly signed Portfolio cursor over `payload` (its `mac`, if any, dropped and recomputed)."""
    return encode_portfolio_cursor({k: v for k, v in payload.items() if k != "mac"}, KEY)


def cov(state="CURRENT", **arrays):
    return {"state": state, "selection_id": None, "watermark": D0, "match_state": "COMPLETE",
            "job_state": "SETTLED", "source_freshness": "RECENT", "rows": [], **EMPTY_ARRAYS, **arrays}


def finding(site, n, at, lifecycle="SUPPORTED", flags=()):
    sid = str(site["site_id"])
    return {"finding_id": FINDING[n], "finding_revision_id": FINDING[n + 20], "site_id": sid,
            "site_code": site["site_code"], "site_name": site["site_name"], "finding_label": f"Finding {n}",
            "title": f"title {n}", "priority": None, "confidence": None, "confidence_reasons": [],
            "lifecycle": lifecycle, "lens_flags": list(flags),
            "consequence": {"state": "UNPRICED", "amount": None, "amount_low": None, "amount_high": None},
            "source_provenance": {"classification": "UNKNOWN"}, "episode_start": None if at is None else at.isoformat(),
            # Post-W6 W3-estate: the real `select_finding_scope` link shape (no recorded window: cold/EV null).
            "links": _finding_links(site["site_code"], DOMAIN_OF_SITE_TYPE[site["site_type"]], FINDING[n],
                                    FINDING[n + 20], None, READ_AT),
            "_at": at, "_site": site, "_domain": site["site_type"], "_episode_end": None, "_mechanism": None}


class World:
    """The fake one-transaction store, plus the four selectors patched into `portfolio`."""

    def __init__(self, monkeypatch) -> None:
        self.sites = list(SITES)
        self.merged_revision = FINDING[39]
        self.inconsistent = 0
        self.down = False
        self.reads = 0
        self.read_at = READ_AT
        for name in ("select_finding_scope", "select_action_scope", "select_evidence_scope",
                     "select_financial_scope"):
            monkeypatch.setattr(portfolio, name, getattr(self, name))

    def read(self, work):
        self.reads += 1
        if self.down:
            raise EstateStoreUnavailable("down")
        if self.inconsistent:
            self.inconsistent -= 1
            raise EstateSelectionInconsistent("pin")
        snap = type("Snap", (), {})()
        snap.read_at = self.read_at
        snap.imported_sites = lambda tenant, to: [s for s in self.sites]
        snap.cited_provenance = lambda t, s, cited, selected: {"classification": "UNKNOWN", "selected": selected}
        snap.cited_provenance_many = lambda t, items: [snap.cited_provenance(t, *x) for x in items]
        return work(snap)

    def rows(self):
        mg, co = SITES
        merged = finding(mg, 5, D0 + timedelta(days=3), lifecycle="MERGED")
        merged["finding_revision_id"] = self.merged_revision
        return [finding(mg, 1, D0 + timedelta(days=1), flags=("COST",)), finding(co, 2, D0 + timedelta(days=2)),
                finding(co, 3, None, lifecycle="UNCONFIRMED"), finding(mg, 4, D0 + timedelta(days=2)), merged]

    def select_finding_scope(self, snap, t, req, scope):
        per = [(s, "mini_grid" if s["site_type"] == "MINIGRID" else "cold_chain",
                cov(selected_finding_revision_ids=[r["finding_revision_id"] for r in self.rows()
                                                   if r["site_id"] == str(s["site_id"])]))
               for s in scope["sites"]]
        ids = {str(s["site_id"]) for s in scope["sites"]}
        return per, [r for r in self.rows() if r["site_id"] in ids]

    def select_action_scope(self, snap, t, req, scope):
        return [(s, cov(selected_action_event_ids=[FINDING[30]] if s["site_type"] == "MINIGRID" else []))
                for s in scope["sites"]], []

    def select_evidence_scope(self, snap, t, req, scope):
        row = {"raw_state": "FULL", "readiness": "FULL", "selected_revision_ids": [FINDING[31]],
               "_assessments": [FINDING[31]], "_cited": [FINDING[32]], "_token_cited": [],
               "window_start": None, "window_end": None,
               "links": {"site": "/sites/X", "site_readiness": "/sites/X",
                         "site_readiness_label": "Opens current Site view"}}
        return [(s, "mini_grid" if s["site_type"] == "MINIGRID" else "cold_chain", cov(), [dict(row)])
                for s in scope["sites"]], []

    def select_financial_scope(self, snap, t, req, scope):
        per = [(s, "mini_grid" if s["site_type"] == "MINIGRID" else "cold_chain",
                {**cov(), "_sessions": [], "_windows_covered": True}, []) for s in scope["sites"]]
        return per, [], {}, [], [], []


@pytest.fixture()
def world(monkeypatch):
    return World(monkeypatch)


def client(world, *, authenticate=lambda request: None, service=True):
    app = FastAPI()
    app.include_router(build_estate_portfolio_router(EstatePortfolioService(world) if service else None,
                                                     lambda: T, authenticate=authenticate,
                                                     access=lambda request, code: None))
    return TestClient(app)


def get(c, params):
    return c.get("/api/estate/portfolio?" + urlencode(params, doseq=True))


def refused(response, status, code):
    assert response.status_code == status, response.text
    detail = response.json()["detail"]
    assert set(detail) == REFUSAL_KEYS and set(response.json()) == {"detail"}
    assert detail == {"code": code, "message": MESSAGES[code], "rows": None, "total_count": None,
                      "value_cards": None, "objectives": None, "money": None}


def test_auth_before_parse_and_all_refusals(world) -> None:
    # 401 runs before the parser and any read: a malformed request is still UNAUTHENTICATED.
    locked = client(world, authenticate=lambda request: 401)
    response = get(locked, [("lens", "money"), ("state", "x")])
    refused(response, 401, "UNAUTHENTICATED")
    assert response.headers["WWW-Authenticate"] == "Bearer" and world.reads == 0
    c = client(world)
    cases = [
        ([("to", WINDOW["to"])], 422, "INVALID_WINDOW"),
        ([("from", WINDOW["from"]), ("from", WINDOW["from"]), ("to", WINDOW["to"])], 422, "INVALID_WINDOW"),
        ([*WINDOW.items(), ("state", "all")], 422, "INVALID_CURSOR"),  # Portfolio forbids `state`
        ([*WINDOW.items(), ("lens", "all"), ("lens", "cost")], 422, "INVALID_CURSOR"),
        ([*WINDOW.items(), ("site", MG)], 422, "INVALID_CURSOR"),
        ([*WINDOW.items(), ("lens", "money")], 422, "INVALID_LENS"),
        ([*WINDOW.items(), ("limit", "0")], 422, "INVALID_LIMIT"),
        ([*WINDOW.items(), ("known_at", "2026-10-19T00:00:00+03:00")], 422, "INVALID_KNOWN_AT"),
        ([*WINDOW.items(), ("known_at", "2026-10-21T00:00:00Z")], 422, "INVALID_KNOWN_AT"),  # after read time
        ([*WINDOW.items(), ("cursor", "not-a-cursor")], 422, "INVALID_CURSOR"),
    ]
    for params, status, code in cases:
        refused(get(c, params), status, code)
    # Store outage and an unconfigured product database are 503; an inconsistent pin is retried once, then 409.
    world.down = True
    refused(get(c, WINDOW), 503, "ESTATE_STORE_UNAVAILABLE")
    world.down = False
    refused(get(client(world, service=False), WINDOW), 503, "ESTATE_STORE_UNAVAILABLE")
    world.inconsistent = 2
    refused(get(c, WINDOW), 409, "ESTATE_SELECTION_INCONSISTENT")
    world.inconsistent = 1  # one retry recovers
    assert get(c, WINDOW).status_code == 200


def _encode(payload) -> str:
    """A cursor envelope with exactly these fields (no signing): the URL-safe base64 of compact JSON."""
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _payload(cursor):
    return json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))


def test_cursor_lens_window_cutoff_and_v1_token(world) -> None:
    c = client(world)
    one = get(c, {**WINDOW, "limit": 1}).json()
    assert one["schema_version"] == "estate-portfolio-1" and one["status"] == "CURRENT"
    assert one["lens"] == "all" and one["order"].startswith("group_rank asc, episode_start desc nulls last")  # CC-R2
    assert one["coverage"]["state"] == "COMPLETE" and one["scope"]["covered_site_count"] == 2
    assert (one["coverage"]["finding_state"], one["coverage"]["evidence_state"],
            one["coverage"]["money_state"]) == ("COMPLETE", "COMPLETE", "COMPLETE")
    # Lifecycle membership (MERGED out), then nonnull episode desc, null last, then (site_code_key, site_id, ...).
    assert one["summary"]["finding_count"] == 4 and one["total_count"] == 4
    order, cursor = [], None
    while True:
        body = get(c, {**WINDOW, "limit": 1, **({"cursor": cursor} if cursor else {})}).json()
        assert body["total_count"] == 4 and body["selection_token"] == one["selection_token"]
        order += [r["finding_id"] for r in body["rows"]]
        cursor = body["next_cursor"]
        if cursor is None:
            break
        payload = _payload(cursor)
        assert payload["v"] == 1 and payload["kind"] == "portfolio" and payload["lens"] == "all"
        assert payload["state_filter"] is None and payload["page_one_mode"] == "live"
        # CC-R2: the six-part marker; every fake-world row investigates first (group_rank 1).
        assert len(payload["after"]) == 6 and payload["after"][0] == 1
        assert payload["selection_token"] == one["selection_token"]
    # D0+2 ties: COLD-1 (cold-1) before KOBO 001 (kobo 001); the null episode is last.
    assert order == [FINDING[2], FINDING[4], FINDING[1], FINDING[3]]
    two = _payload(get(c, {**WINDOW, "limit": 1}).json()["next_cursor"])
    row = one["rows"][0]
    assert row["site_code"] == "COLD-1" and row["links"] == {"site": "/sites/COLD-1", "finding": None, "action": None}
    kobo = next(r for r in get(c, {**WINDOW, "limit": 4}).json()["rows"] if r["finding_id"] == FINDING[4])
    assert kobo["links"]["site"] == "/sites/KOBO%20001" and kobo["domain"] == "MINIGRID"
    assert kobo["links"]["finding"] == f"/sites/KOBO%20001/findings/{FINDING[4]}?revision_id={FINDING[24]}"
    assert kobo["action_id"] is None and kobo["application_state"] is None and kobo["mechanism"] is None
    # Lens membership on the server; the cost lens has its own total.
    cost = get(c, {**WINDOW, "lens": "cost"}).json()
    assert [r["finding_id"] for r in cost["rows"]] == [FINDING[1]] and cost["total_count"] == 1
    assert cost["summary"]["finding_count"] == 4 and cost["selection_token"] != one["selection_token"]

    # The token is the literal estate-selection/2 over full per-Site unions (the MERGED head included).
    items = []
    for site, domain in ((SITES[0], "mini_grid"), (SITES[1], "cold_chain")):
        sid = str(site["site_id"])
        frids = [r["finding_revision_id"] for r in world.rows() if r["site_id"] == sid]
        items.append({**cov(), "site_id": site["site_id"], "domain": domain,
                      "selected_finding_revision_ids": frids,
                      "selected_action_event_ids": [FINDING[30]] if domain == "mini_grid" else [],
                      "selected_assessment_revision_ids": [FINDING[31]],
                      "cited_accepted_evidence_ids": [FINDING[32]]})
    assert one["selection_token"] == selection_token(T, [MG, CO], D0, D0 + timedelta(days=7), READ_AT, "all",
                                                     None, items)

    def page_two(**params):
        return get(c, {**WINDOW, **params, "cursor": signed(two)})

    assert two["mac"] == _payload(signed(two))["mac"] and len(two["mac"]) == 64
    assert page_two().status_code == 200
    # r1b Q-1b-1: the unsigned v1 form, a wrong MAC and a MAC over other fields are 422 before any basis check.
    unsigned = {k: v for k, v in two.items() if k != "mac"}
    refused(get(c, {**WINDOW, "cursor": encode_cursor(unsigned)}), 422, "INVALID_CURSOR")
    refused(get(c, {**WINDOW, "cursor": encode_cursor({**two, "mac": "0" * 64})}), 422, "INVALID_CURSOR")
    refused(get(c, {**WINDOW, "cursor": encode_cursor({**two, "page_one_mode": "historical"})}), 422,
            "INVALID_CURSOR")
    refused(page_two(lens="cost"), 409, "ESTATE_BASIS_CHANGED")
    refused(page_two(**{"from": "2026-10-12T00:00:00Z"}), 409, "ESTATE_BASIS_CHANGED")
    refused(page_two(known_at="2026-10-19T00:00:00Z"), 409, "ESTATE_BASIS_CHANGED")
    # A changed MERGED head (outside the visible rows) changes the full-scope token: page two is fenced.
    world.merged_revision = FINDING[38]
    refused(page_two(), 409, "ESTATE_BASIS_CHANGED")
    world.merged_revision = FINDING[39]
    # A changed grant is 409 before the marker lookup.
    world.sites = SITES[:1]
    refused(page_two(), 409, "ESTATE_BASIS_CHANGED")
    world.sites = list(SITES)
    # A validly signed cursor whose captured grant or selection differs is 409, not 422.
    refused(get(c, {**WINDOW, "cursor": signed({**two, "selection_token": "estate-selection/2:" + "0" * 64})}),
            409, "ESTATE_BASIS_CHANGED")
    refused(get(c, {**WINDOW, "cursor": signed({**two, "authorized_site_ids": [MG]})}), 409, "ESTATE_BASIS_CHANGED")
    # A well-formed nonmember marker passes the fence and is 422.
    stranger = {**two, "after": [two["after"][0], "zzz", MG, FINDING[9], FINDING[29]]}
    refused(get(c, {**WINDOW, "cursor": signed(stranger)}), 422, "INVALID_CURSOR")
    # Malformed five-part markers are 422 at the parser.
    for bad in ([None, "", MG, FINDING[1], FINDING[21]], [None, "k", "x", FINDING[1], FINDING[21]], [None, "k", MG]):
        refused(get(c, {**WINDOW, "cursor": signed({**two, "after": bad})}), 422, "INVALID_CURSOR")
    # Explicit historical page one stays HISTORICAL on page two through the captured basis mode.
    hist = get(c, {**WINDOW, "known_at": "2026-10-19T00:00:00Z", "limit": 1}).json()
    assert hist["status"] == "HISTORICAL" and _payload(hist["next_cursor"])["page_one_mode"] == "historical"
    cont = get(c, {**WINDOW, "cursor": hist["next_cursor"]}).json()
    assert cont["status"] == "HISTORICAL" and cont["window"]["known_at"] == "2026-10-19T00:00:00Z"
    # A live page two keeps CURRENT although its captured cutoff precedes the read time.
    world.read_at = READ_AT + timedelta(hours=1)
    live = get(c, {**WINDOW, "cursor": signed(two)}).json()
    assert live["status"] == "CURRENT" and live["window"]["known_at"] == "2026-10-20T12:00:00Z"
    # A missing or malformed key is 503 with the exact refusal body on page one, page two and an empty scope.
    for value in (None, "zz" * 32, KEY_HEX[:-2]):
        with pytest.MonkeyPatch.context() as mp:
            if value is None:
                mp.delenv(PORTFOLIO_CURSOR_KEY_ENV)
            else:
                mp.setenv(PORTFOLIO_CURSOR_KEY_ENV, value)
            for params in (WINDOW, {**WINDOW, "cursor": signed(two)}):
                reads = world.reads
                response = get(c, params)
                refused(response, 503, "ESTATE_STORE_UNAVAILABLE")
                assert world.reads == reads  # r1b2 R1: refused at the API boundary, zero store reads
                assert response.json() == {"detail": {
                    "code": "ESTATE_STORE_UNAVAILABLE", "message": "Estate records could not be read.", "rows": None,
                    "total_count": None, "value_cards": None, "objectives": None, "money": None}}
                assert KEY_HEX not in response.text
            world.sites = []
            reads = world.reads
            refused(get(c, WINDOW), 503, "ESTATE_STORE_UNAVAILABLE")
            assert world.reads == reads
            world.sites = list(SITES)
            # r1b2 R2: the envelope is parsed before the key check, so a malformed envelope is 422 even without a
            # key; a well-shaped envelope with a wrong MAC needs the key, so it is 503 here. Both make zero reads.
            wrong_mac = _encode({**_payload(signed(two)), "mac": "0" * 64})
            for cursor, status, code in (("not*base64", 422, "INVALID_CURSOR"),
                                         (_encode({k: v for k, v in _payload(signed(two)).items() if k != "mac"}),
                                          422, "INVALID_CURSOR"),
                                         (_encode({**_payload(signed(two)), "mac": "ABC"}), 422, "INVALID_CURSOR"),
                                         (wrong_mac, 503, "ESTATE_STORE_UNAVAILABLE")):
                reads = world.reads
                refused(get(c, {**WINDOW, "cursor": cursor}), status, code)
                assert world.reads == reads, cursor
    # With a valid key the same wrong-MAC envelope is 422 after the snapshot opens (MAC verified in the snapshot).
    refused(get(c, {**WINDOW, "cursor": wrong_mac}), 422, "INVALID_CURSOR")


def test_builder_uses_one_connection_scoped_reader_and_refuses_missing_database(monkeypatch, request) -> None:
    """r1a2 item 3: the actual Lane B composition builder; no database is 503, never an empty estate."""
    from assetops_backend.estate.composition import build_estate_portfolio_service
    from test_w301_estate_index_postgres import URL

    assert build_estate_portfolio_service(None) is None and build_estate_portfolio_service("") is None
    app = FastAPI()
    app.include_router(build_estate_portfolio_router(build_estate_portfolio_service(None), lambda: None))
    refused(TestClient(app).get("/api/estate/portfolio", params=WINDOW), 503, "ESTATE_STORE_UNAVAILABLE")
    if not URL:
        pytest.skip("ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
    request.getfixturevalue("engine")  # the migrated run-owned test database
    from assetops_backend.estate.adapters.postgres_evidence_money_read import (
        EvidenceMoneySnapshot, PostgresEvidenceMoneyRead)

    service = build_estate_portfolio_service(URL)
    seen: list = []
    for name in ("select_finding_scope", "select_action_scope", "select_evidence_scope", "select_financial_scope"):
        real = getattr(portfolio, name)
        monkeypatch.setattr(portfolio, name, lambda snap, *a, _real=real: seen.append(snap) or _real(snap, *a))
    try:
        assert isinstance(service, EstatePortfolioService) and isinstance(service.store, PostgresEvidenceMoneyRead)
        # An unknown tenant has no authorized Site: one snapshot, EMPTY_SCOPE, still through all four selectors.
        req = parse_request("portfolio", list(WINDOW.items()))
        body = service.portfolio(UUID(int=0), req, lambda code: True)
        assert body["status"] == "EMPTY_SCOPE" and body["rows"] == []
        assert len(seen) == 4 and len({id(s) for s in seen}) == 1 and isinstance(seen[0], EvidenceMoneySnapshot)
        assert len({id(s._c) for s in seen}) == 1
    finally:
        service.store.dispose()


PROJECTIONS = ("summary", "value_cards", "objectives", "evidence_prompt", "opportunity", "progress", "footer",
               "selected_lines", "money", "scope_disclosure", "coverage", "status", "total_count", "selection_token")


def test_full_scope_projections_ignore_page_size_and_empty_scope(world) -> None:
    """Run 1b on the fake world: every projection is full scope (limits 1 and 4 agree), with the closure-1 literal
    slots; an empty scope keeps every key with zero counts and no money."""
    c = client(world)
    one, four = get(c, {**WINDOW, "limit": 1}).json(), get(c, {**WINDOW, "limit": 4}).json()
    assert {k: one[k] for k in PROJECTIONS} == {k: four[k] for k in PROJECTIONS}
    assert [(x["key"], x["state"], x["tone"]) for x in one["value_cards"]] == [
        ("OPERATING_COST", "NO_LINE", "neutral"), ("SERVICE_PRODUCT_RISK", "UNKNOWN", "neutral"),
        ("PRODUCTIVE_USE", "UNSUPPORTED", "neutral"), ("ASSET_LIFE", "UNSUPPORTED", "neutral"),
        ("VERIFIED_RECOVERY", "NOT_ESTABLISHED", "neutral")]
    assert one["value_cards"][0]["display_value"] == "No supported value"  # r3b exact literal
    assert one["value_cards"][1]["destination"] == "/findings/risks"
    assert [o["site_id"] for o in one["objectives"]] == [MG, CO]
    cells = {o["site_id"]: {x["key"]: x["state"] for x in o["cells"]} for o in one["objectives"]}
    assert cells[MG] == {"SERVICE_PRODUCT": "UNKNOWN", "BACKUP": "UNKNOWN", "ASSET_CONDITION": "UNKNOWN",
                         "COST_CONTROL": "UNASSESSED", "EVIDENCE": "FULL"}
    assert cells[CO]["COST_CONTROL"] == "NOT_APPLICABLE" and cells[CO]["EVIDENCE"] == "FULL"
    assert one["evidence_prompt"] == {"state": "NO_GAP", "text": "No selected decision-changing evidence step",
                                      "site_id": None, "site_code": None, "gap_code": None, "destination": "/evidence"}
    assert one["progress"] == {"state": "NO_COMPARABLE_BASELINE", "completed_activity_count": None,
                               "pending_trial_count": 0, "verified_resolution_count": 0, "recovered_value": None,
                               "rows": []}
    assert one["summary"] == {"finding_count": 4, "priority_site_count": None, "opportunity_count": 0,
                              "evidence_gap_site_count": 0, "accepted_action_count": 0,
                              "verified_resolution_count": 0, "combined_value": None,
                              "combined_value_state": "NOT_COMPARABLE",
                              # CC-R2: the fake world's rows carry no source class, so all four investigate first.
                              "placement_counts": {"NEEDS_INVESTIGATION": 4, "ACT_NOW": 0, "COMPARE_VALUE": 0,
                                                   "UNPRICED_RISK": 0, "MONITOR": 0},
                              # OUT-A2: the fake rows carry no mechanism, so every member is NOT_MAPPED.
                              "category_counts": dict.fromkeys(
                                  ("GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"),
                                  {"open_findings": 0, "sites_with_primary_finding": 0})}
    assert one["money"] == {"groups": [], "exclusions": [], "diagnostics": [], "estate_total": None}
    assert one["footer"] is None and one["selected_lines"] == []
    site = one["scope_disclosure"]["sites"][0]
    assert set(site) == {"site_id", "site_code", "site_name", "domain", "window", "coverage",
                         "selected_revision_ids", "source_provenance"}
    assert site["window"] == WINDOW and FINDING[31] in site["selected_revision_ids"]
    # Historical display: the EVIDENCE cell is UNKNOWN for the current objective.
    hist = get(c, {**WINDOW, "known_at": "2026-10-19T00:00:00Z"}).json()
    assert {x["key"]: x["state"] for x in hist["objectives"][0]["cells"]}["EVIDENCE"] == "UNKNOWN"
    # r1b2 R13: a null-step-only gap Site counts in `evidence_gap_site_count` (1) while the prompt is NO_GAP.
    real = world.select_evidence_scope

    def null_step(snap, t, req, scope):
        per, _ = real(snap, t, req, scope)
        mg = next(s for s in scope["sites"] if str(s["site_id"]) == MG)
        row = {"site_id": MG, "site_code": mg["site_code"], "site_name": mg["site_name"], "capability_key": "backup",
               "_key": (mg["site_code_key"], MG, "backup"),
               "_gaps": [{"key": ("mini_grid", "G-NULL", "role"), "domain": "mini_grid", "gap_code": "G-NULL",
                          "missing_role": "role", "label": "label", "next_step": None}]}
        return per, [row]

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(portfolio, "select_evidence_scope", null_step)
        gapped = get(c, WINDOW).json()
    assert gapped["summary"]["evidence_gap_site_count"] == 1 and gapped["evidence_prompt"]["state"] == "NO_GAP"
    world.sites = []
    empty = get(c, WINDOW).json()
    assert empty["status"] == "EMPTY_SCOPE" and empty["objectives"] == [] and empty["footer"] is None
    assert empty["summary"]["finding_count"] == 0 and empty["summary"]["accepted_action_count"] == 0
    # CC-R2: an EMPTY finding state gives zero placement counts, never nulls.
    assert empty["summary"]["placement_counts"] == dict.fromkeys(
        ("NEEDS_INVESTIGATION", "ACT_NOW", "COMPARE_VALUE", "UNPRICED_RISK", "MONITOR"), 0)
    assert empty["scope_disclosure"] == {"sites": [], "exclusions": []}


def test_out_a2_row_categories_and_category_counts(world, monkeypatch) -> None:
    """OUT-A2: a ranked row's `categories` equal the Findings row's (Site type -> coverage domain, ruling A-Q5);
    `category_counts` keeps all four keys, counts any-role members and distinct primary Sites, skips NOT_MAPPED
    members, and is null per value unless the Finding coverage is known (ruling A-Q11)."""
    from assetops_backend.outcomes.outcome_map import categories_for

    mechanisms = {FINDING[1]: "GENERATOR_SUPPORT_CANDIDATE", FINDING[2]: "COLD_START_FAILURE",
                  FINDING[3]: "COLD_EXCURSION"}  # FINDING[4] stays null: NOT_MAPPED
    real_rows = world.rows
    monkeypatch.setattr(world, "rows", lambda: [{**r, "_mechanism": mechanisms.get(r["finding_id"])}
                                                for r in real_rows()])
    body = get(client(world), WINDOW).json()
    for row in body["rows"]:
        domain = DOMAIN_OF_SITE_TYPE[row["domain"]]
        assert row["categories"] == categories_for(f"FINDING:{mechanisms.get(row['finding_id'], 'UNMAPPED')}",
                                                   domain), row["finding_id"]
    assert body["summary"]["category_counts"] == {
        "GROW_REVENUE": {"open_findings": 0, "sites_with_primary_finding": 0},
        "OPTIMIZE_COST": {"open_findings": 2, "sites_with_primary_finding": 1},  # F1 moves, F2 checked
        "PROTECT_ASSET": {"open_findings": 3, "sites_with_primary_finding": 1},  # F2+F3 share one cold Site
        "ASSURE_PERFORMANCE": {"open_findings": 0, "sites_with_primary_finding": 0}}
    real_scope = world.select_finding_scope

    def unknown(snap, t, req, scope):
        per, rows = real_scope(snap, t, req, scope)
        return [(s, d, {**c, "state": "UNKNOWN"}) for s, d, c in per], rows

    monkeypatch.setattr(portfolio, "select_finding_scope", unknown)
    body = get(client(world), WINDOW).json()
    assert body["summary"]["finding_count"] is None
    assert body["summary"]["category_counts"] == dict.fromkeys(
        ("GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"),
        {"open_findings": None, "sites_with_primary_finding": None})


def test_evidence_prompt_null_steps_and_coverage_precedence_pure() -> None:
    """S13 (no persisted null-step producer): incomplete coverage wins; null-step gaps are skipped; the first Site
    with a code in the group's own order is chosen."""
    gap = lambda step, ids, codes: {"gap_code": f"G-{step}", "next_step": step, "site_ids": ids,  # noqa: E731
                                    "site_codes": codes, "site_names": [f"name {c}" for c in codes]}
    gaps = [gap(None, [MG], ["KOBO 001"]), gap("Upload a log", [CO, MG], [None, "KOBO 001"])]
    assert portfolio.evidence_prompt("PARTIAL", gaps)["state"] == "COVERAGE_INCOMPLETE"
    assert portfolio.evidence_prompt("UNKNOWN", [])["text"] == "Evidence coverage incomplete"
    chosen = portfolio.evidence_prompt("COMPLETE", gaps)
    assert (chosen["state"], chosen["site_id"], chosen["gap_code"]) == ("AVAILABLE", MG, "G-Upload a log")
    assert chosen["text"] == "Upload a log at name KOBO 001 to address the selected evidence gap."
    assert portfolio.evidence_prompt("COMPLETE", gaps[:1])["state"] == "NO_GAP"
