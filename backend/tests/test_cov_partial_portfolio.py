"""COV-PARTIAL U2: the Portfolio `PARTIAL` status (build sheet §3, S1-S6) and the never-on-track audit over every
estate root (X1, X2). Fake selectors and snapshots; no database."""

from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlencode
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.chain.claims import CLAIM_KEYS, EstateCounts
from assetops_backend.chain.vocabulary import count_claim
from assetops_backend.estate import coverage, evidence_money, financials, index, portfolio
from assetops_backend.estate.portfolio import EstatePortfolioService
from assetops_backend.estate_api import build_estate_router
from assetops_backend.estate_evidence_money_api import build_estate_evidence_money_router
from assetops_backend.estate_portfolio_api import build_estate_portfolio_router
from test_cov_partial import PRICED, Snap, day, head
from test_w302_evidence_api import CUT, D0, MG, T, WINDOW, FakeStore
from test_w302_money_api import MoneySnapshot
from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
from test_w303_portfolio_api import KEY_HEX, MG as P_MG, SITES as P_SITES, World, cov as p_cov


@pytest.fixture(autouse=True)
def _cursor_key(monkeypatch):
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, KEY_HEX)

# --- S1-S6: the Portfolio status order over the W3-03 fake selectors ------------------------------------------

EXTRA = {"site_id": "30000000-0000-4000-8000-000000000013", "site_code": "KOBO 002", "site_name": "Kobo 2",
         "site_type": "MINIGRID", "site_code_key": "kobo 002"}


class StateWorld(World):
    """W3-03's fake world with one coverage state per Site applied to its F, E and M coverage."""

    def __init__(self, monkeypatch, states) -> None:
        super().__init__(monkeypatch)
        self.sites = [*P_SITES, {**EXTRA, "site_id": UUID(EXTRA["site_id"])}]
        self.states = states

    def _state(self, s, c):
        st = self.states.get(s["site_code"], "CURRENT")
        extra = {"job_state": "PENDING"} if st == "PENDING_RECOMPUTE" else {}
        return {**c, "state": st, **extra}

    def select_finding_scope(self, snap, t, req, scope, cutoffs=None):
        per, rows = super().select_finding_scope(snap, t, req, scope, cutoffs)
        return [(s, d, self._state(s, c)) for s, d, c in per], rows

    def select_evidence_scope(self, snap, t, req, scope):
        per, gaps = super().select_evidence_scope(snap, t, req, scope)
        return [(s, d, self._state(s, c), r) for s, d, c, r in per], gaps

    def select_financial_scope(self, snap, t, req, scope):
        per, *rest = super().select_financial_scope(snap, t, req, scope)
        return ([(s, d, self._state(s, c), lines) for s, d, c, lines in per], *rest)


def portfolio_status(monkeypatch, states, historical=False) -> dict:
    w = StateWorld(monkeypatch, states)
    app = FastAPI()
    app.include_router(build_estate_portfolio_router(EstatePortfolioService(w), lambda: T,
                                                     authenticate=lambda request: None,
                                                     access=lambda request, code: None))
    response = TestClient(app).get("/api/estate/portfolio?" + urlencode(
        {"from": "2026-10-13T00:00:00Z", "to": "2026-10-20T00:00:00Z",
         **({"known_at": "2026-10-20T06:00:00Z"} if historical else {})}))
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("states,status", [
    ({"KOBO 001": "PARTIAL"}, "PARTIAL"),                                            # S1
    ({"KOBO 001": "PARTIAL", "KOBO 002": "UNKNOWN"}, "UNKNOWN"),                     # S2
    ({"KOBO 001": "PARTIAL", "KOBO 002": "PENDING_RECOMPUTE"}, "PENDING"),           # S3
    ({"KOBO 001": "PARTIAL", "KOBO 002": "PARTIAL", "COLD-1": "PARTIAL"}, "PARTIAL"),  # S5
    ({}, "CURRENT"),                                                                 # S6
    ({"KOBO 002": "UNKNOWN"}, "UNKNOWN"),                                            # S6
])
def test_s1_s6_portfolio_status_order(monkeypatch, states, status) -> None:
    body = portfolio_status(monkeypatch, states)
    assert body["status"] == status
    if "PARTIAL" in states.values():
        assert body["status"] != "CURRENT"


def test_s4_historical_wins(monkeypatch) -> None:
    assert portfolio_status(monkeypatch, {"KOBO 001": "PARTIAL"}, historical=True)["status"] == "HISTORICAL"


def test_partial_status_constant_and_unit() -> None:
    assert portfolio.PARTIAL_STATUS == "PARTIAL"
    assert portfolio.finding_unit("mini_grid", p_cov("PARTIAL")) == portfolio.U  # not covered: unit U


# --- X1, X2: one live PARTIAL mini-grid Site through every estate root -------------------------------------------

PARTIAL_DAYS = [day(n, base=D0) for n in range(5)] + [day(n, base=D0, selected=False) for n in (5, 6)]
PARTIAL_HEAD = head(D0 + timedelta(hours=8), D0 + timedelta(hours=9))


@pytest.fixture()
def partial_estate(monkeypatch):
    """KOBO-001 reads the real `estate-coverage/2` rule over a 7-day period with two unchecked days and one stored
    PRICED Finding on a checked day; every other Site and domain reads the CURRENT stub of the W3-02 suites."""
    calls = []

    def fake(snap, t, s, domain, from_, to, k):
        if str(s) == str(MG) and domain == coverage.MINI_GRID:
            calls.append(domain)
            return coverage.site_coverage(Snap(PARTIAL_DAYS, [PARTIAL_HEAD], consequence=PRICED), t, s, domain,
                                          from_, to, k)
        if domain == coverage.ACTIONS:
            return coverage.not_applicable() if str(s) != str(MG) else {
                **coverage._empty("CURRENT"), "match_state": "COMPLETE", "job_state": "SETTLED",
                "source_freshness": "RECENT", "watermark": CUT}
        return {**coverage._empty("CURRENT"), "watermark": CUT, "match_state": "COMPLETE", "job_state": "SETTLED",
                "source_freshness": "RECENT"}
    for module in (index, evidence_money, financials):
        monkeypatch.setattr(module, "site_coverage", fake)

    class PortfolioSnap(MoneySnapshot):
        def cited_provenance_many(self, t, items):
            return [self.cited_provenance(t, *x) for x in items]

        def awaiting_verification(self, *a):
            return 0

        def selected_windows(self, *a):
            return []

    app = FastAPI()
    store = FakeStore(PortfolioSnap())
    service = EstatePortfolioService(store)
    for build, kw in ((build_estate_router, {}), (build_estate_evidence_money_router, {}),
                      (build_estate_portfolio_router, {"access": lambda request, code: None})):
        app.include_router(build(service, lambda: T, authenticate=lambda request: None, **kw))
    c = TestClient(app)

    def get(root, **extra):
        query = {**WINDOW, **({} if root == "scope" else {"limit": 100}), **extra}
        response = c.get(f"/api/estate/{root}?" + urlencode(query))
        assert response.status_code == 200, (root, response.text)
        assert calls, root  # the PARTIAL rule was read
        return response.json()
    return get


def _site(body, key="coverage"):
    return next(s for s in body[key]["sites"] if s["site_id"] == str(MG))


def test_x1_partial_site_never_reads_on_track(partial_estate) -> None:
    findings = partial_estate("findings")
    kobo = _site(findings)
    assert kobo["state"] == "PARTIAL"
    assert kobo["days"]["text"] == "5 of 7 days checked · 2 days not available yet"
    assert findings["status"] != "CURRENT" and findings["status"] == "UNKNOWN"
    assert findings["total_count"] is None
    kobo_rows = [r for r in findings["rows"] if r["site_id"] == str(MG)]
    assert kobo_rows and all(r["consequence"]["amount"] is None and r["consequence"]["amount_low"] is None
                             for r in kobo_rows)

    evidence = partial_estate("evidence")
    assert evidence["status"] != "CURRENT"
    assert _site(evidence)["state"] == "PARTIAL"

    money = partial_estate("financials")
    assert money["status"] != "CURRENT"
    assert not [line for line in money["rows"] if line.get("site_id") == str(MG)]

    scope = partial_estate("scope")
    assert next(x for x in scope["sites"] if x["site_id"] == str(MG))["coverage_state"] == "PARTIAL"
    assert scope["covered_site_count"] == len(scope["sites"]) - 1  # shown, not counted

    body = partial_estate("portfolio")
    # the other fake Sites carry W3-02 limits (U units), so PARTIAL or UNKNOWN; never CURRENT (S1 proves PARTIAL)
    assert body["status"] in ("PARTIAL", "UNKNOWN") and body["status"] != "CURRENT"
    assert body["summary"].get("finding_count") is None
    assert all(r.get("amount") is None and (r.get("consequence") or {}).get("amount") is None
               for r in body["rows"] if r.get("site_id") == str(MG))
    disclosed = next(s for s in body["scope_disclosure"]["sites"] if s["site_id"] == str(MG))
    assert disclosed["coverage"]["state"] == "PARTIAL" and disclosed["coverage"]["days"]["checked"] == 5


def test_x2_partial_row_is_placed_on_the_not_covered_path(partial_estate) -> None:
    body = partial_estate("portfolio")
    rows = [r for r in body["rows"] if r.get("site_id") == str(MG)]
    assert rows
    for r in rows:  # R5.6: the not-covered text, never a move into another group by coverage
        assert "Site coverage incomplete; other findings may be missing" in r["confidence_reasons"]
        assert r["placement"]["group"] is not None


# --- WALK1-1 (WN-2): Portfolio counts over the checked days of a PARTIAL estate ---------------------------------

DAYS = {"policy": "x", "requested": 7, "checked": 5, "gaps": [], "withheld": False, "text": "5 of 7 days checked"}


class DaysWorld(StateWorld):
    """`StateWorld` whose PARTIAL Sites carry a mini-grid `days` block on their Finding coverage."""

    def _state(self, s, c):
        out = super()._state(s, c)
        return {**out, "days": DAYS} if out["state"] == "PARTIAL" else out


CHECKED_MIX = {"complete": 5, "partial": 1, "low": 0, "no_data": 1, "pending": 0, "expected": 7}
ALL_COMPLETE = {"complete": 7, "partial": 0, "low": 0, "no_data": 0, "pending": 0, "expected": 7}


def claims_stub(days):
    """CH-5a2b: the injected one count computation (`chain.claims.EstateClaims`), returning claims over `days`."""
    def stub(tenant_id, codes, lo, hi, known_at):
        return EstateCounts({k: count_claim(k, 0, days) for k in CLAIM_KEYS}, {}, {})
    return stub


def portfolio_days(monkeypatch, states, days=None) -> dict:
    app = FastAPI()
    service = EstatePortfolioService(DaysWorld(monkeypatch, states))
    if days is not None:
        service.count_claims = claims_stub(days)
    app.include_router(build_estate_portfolio_router(service,
                                                     lambda: T, authenticate=lambda request: None,
                                                     access=lambda request, code: None))
    response = TestClient(app).get("/api/estate/portfolio?" + urlencode(
        {"from": "2026-10-13T00:00:00Z", "to": "2026-10-20T00:00:00Z"}))
    assert response.status_code == 200, response.text
    return response.json()


def test_walk1_partial_estate_counts_over_checked_days(monkeypatch) -> None:
    body = portfolio_days(monkeypatch, {"KOBO 001": "PARTIAL"}, CHECKED_MIX)
    summary = body["status"], body["summary"]
    assert summary[0] == "PARTIAL"
    s = summary[1]
    assert s["count_basis"] == "CHECKED_DAYS"
    assert isinstance(s["finding_count"], int) and isinstance(s["opportunity_count"], int)
    assert isinstance(s["category_counts"]["PROTECT_ASSET"]["sites_with_primary_finding"], int)
    assert all(isinstance(v, int) for v in s["placement_counts"].values())
    assert isinstance(s["evidence_gap_site_count"], int)  # pre-flight E1: PARTIAL Sites emit evidence rows
    assert s["checked_days"] == [{"site_id": P_MG, "site_name": "Kobo", "checked": 5, "requested": 7,
                                 "withheld": False}]
    assert s["combined_value"] is None  # money unchanged (D-W1-4)


def test_walk1_withheld_flag_rides_checked_days_and_count_stays_int(monkeypatch) -> None:
    global DAYS
    saved = DAYS
    DAYS = {**saved, "withheld": True}
    try:
        s = portfolio_days(monkeypatch, {"KOBO 001": "PARTIAL"})["summary"]
    finally:
        DAYS = saved
    assert s["checked_days"][0]["withheld"] is True
    assert isinstance(s["opportunity_count"], int)  # the number is unchanged; the client words the zero


def test_walk1_unknown_estate_stays_null_and_complete_stays_complete(monkeypatch) -> None:
    unknown = portfolio_days(monkeypatch, {"KOBO 001": "PARTIAL", "KOBO 002": "UNKNOWN"})["summary"]
    # CH-5a2b (§B14 Q9): `count_basis` is the one basis rule over the claims' day grades; with no computation
    # injected the claims are not known. `finding_count` keeps its coverage nullability until CH-6b.
    assert unknown["count_basis"] == "NOT_KNOWN" and unknown["finding_count"] is None
    assert {c["basis"] for c in unknown["claims"].values()} == {"NOT_KNOWN"}
    assert unknown["category_counts"]["PROTECT_ASSET"]["sites_with_primary_finding"] is None
    assert unknown["evidence_gap_site_count"] is None
    assert len(unknown["checked_days"]) == 1  # stated for the PARTIAL Site; the client reads it only on CHECKED_DAYS
    complete = portfolio_days(monkeypatch, {}, ALL_COMPLETE)["summary"]
    assert complete["count_basis"] == "COMPLETE" and complete["checked_days"] == []
    # Q9: complete Finding coverage over partly graded days reads the day-grade basis, not the coverage basis.
    assert portfolio_days(monkeypatch, {}, CHECKED_MIX)["summary"]["count_basis"] == "CHECKED_DAYS"
    assert isinstance(complete["finding_count"], int)
