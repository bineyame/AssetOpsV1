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
from assetops_backend.estate.portfolio import EstatePortfolioService
from assetops_backend.estate.scope import (
    MESSAGES, EstateSelectionInconsistent, EstateStoreUnavailable, encode_cursor, selection_token)
from assetops_backend.estate_portfolio_api import build_estate_portfolio_router

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
               "_assessments": [FINDING[31]], "_cited": [FINDING[32]], "_token_cited": []}
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


def _payload(cursor):
    return json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))


def test_cursor_lens_window_cutoff_and_v1_token(world) -> None:
    c = client(world)
    one = get(c, {**WINDOW, "limit": 1}).json()
    assert one["schema_version"] == "estate-portfolio-1" and one["status"] == "CURRENT"
    assert one["lens"] == "all" and one["order"].startswith("episode_start desc nulls last")
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
        assert len(payload["after"]) == 5 and payload["selection_token"] == one["selection_token"]
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
        return get(c, {**WINDOW, **params, "cursor": encode_cursor(two)})

    assert page_two().status_code == 200
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
    # A well-formed nonmember marker passes the fence and is 422.
    stranger = {**two, "after": [two["after"][0], "zzz", MG, FINDING[9], FINDING[29]]}
    refused(get(c, {**WINDOW, "cursor": encode_cursor(stranger)}), 422, "INVALID_CURSOR")
    # Malformed five-part markers are 422 at the parser.
    for bad in ([None, "", MG, FINDING[1], FINDING[21]], [None, "k", "x", FINDING[1], FINDING[21]], [None, "k", MG]):
        refused(get(c, {**WINDOW, "cursor": encode_cursor({**two, "after": bad})}), 422, "INVALID_CURSOR")
    # Explicit historical page one stays HISTORICAL on page two through the captured basis mode.
    hist = get(c, {**WINDOW, "known_at": "2026-10-19T00:00:00Z", "limit": 1}).json()
    assert hist["status"] == "HISTORICAL" and _payload(hist["next_cursor"])["page_one_mode"] == "historical"
    cont = get(c, {**WINDOW, "cursor": hist["next_cursor"]}).json()
    assert cont["status"] == "HISTORICAL" and cont["window"]["known_at"] == "2026-10-19T00:00:00Z"
    # A live page two keeps CURRENT although its captured cutoff precedes the read time.
    world.read_at = READ_AT + timedelta(hours=1)
    live = get(c, {**WINDOW, "cursor": encode_cursor(two)}).json()
    assert live["status"] == "CURRENT" and live["window"]["known_at"] == "2026-10-20T12:00:00Z"
