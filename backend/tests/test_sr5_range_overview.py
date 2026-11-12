"""SR-5a (rev 9 §9.4): the one-Site `site-range-overview-1` read and its route, no database. The world is
`test_cov_partial_portfolio.partial_estate`'s: KOBO-001 reads the real `estate-coverage/2` rule over a 7-day period
with two unchecked days and one stored PRICED Finding on a checked day; the range body is composed on the same
snapshot and selectors as the Portfolio, so its coverage entry and partial money equal the Portfolio's."""

from __future__ import annotations

import json
import logging
import os
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.estate import coverage, evidence_money, financials, index, site_range
from assetops_backend.estate.portfolio import EstatePortfolioService
from assetops_backend.estate.scope import EstateRequest, EstateStoreUnavailable, PORTFOLIO_CURSOR_KEY_ENV
from assetops_backend.estate.site_range import (
    CLEAR, FINDINGS, NO_READINGS, NOT_ANALYSED, NOT_ENOUGH_READINGS, NOT_EXPECTED, READINGS_CONFLICT,
    STILL_PROCESSING, _day_state, site_range_body)
from assetops_backend.estate_portfolio_api import build_estate_portfolio_router
from assetops_backend.outcome_api import RANGE_ROUTE, build_outcome_router
from test_cov_partial import PRICED, Snap
from test_cov_partial_portfolio import PARTIAL_DAYS, PARTIAL_HEAD
from test_w302_evidence_api import CUT, D0, MG, T, WINDOW, FakeStore
from test_w302_money_api import MoneySnapshot
from test_w303_portfolio_api import KEY_HEX

GOLDEN = Path(__file__).parent / "fixtures" / "sr5_range_overview" / "kobo_partial.json"
REGEN = "ASSETOPS_REGEN_SR5_GOLDEN"
KOBO = "KOBO-001"
SITES = {code: SimpleNamespace(tenant_id=T, id=sid, site_code=code, name=f"{code} name", site_type=kind,
                               timezone=None)
         for code, sid, kind in ((KOBO, MG, "MINIGRID"), ("COLD 1", None, "COLDCHAIN"), ("EV-1", None, "EV_CHARGING"))}


@pytest.fixture(autouse=True)
def _cursor_key(monkeypatch):
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, KEY_HEX)


class Registry:
    def tenant(self):
        return SimpleNamespace(id=T)

    def imported(self, code):
        return SITES.get(code)


class Responses:
    """A `ResponseStore` double: records the stored route and composes."""

    def __init__(self) -> None:
        self.routes: list = []

    def serve(self, route, compose):
        self.routes.append(route)
        return compose()[route.route]


@pytest.fixture()
def world(monkeypatch):
    """`partial_estate`'s world, plus the KOBO-001 dispatch days and Finding index the range body reads."""
    snap_days = Snap(PARTIAL_DAYS, [PARTIAL_HEAD], consequence=PRICED)

    def fake(snap, t, s, domain, from_, to, k):
        if str(s) == str(MG) and domain == coverage.MINI_GRID:
            return coverage.site_coverage(snap_days, t, s, domain, from_, to, k)
        if domain == coverage.ACTIONS:
            return coverage.not_applicable() if str(s) != str(MG) else {
                **coverage._empty("CURRENT"), "match_state": "COMPLETE", "job_state": "SETTLED",
                "source_freshness": "RECENT", "watermark": CUT}
        return {**coverage._empty("CURRENT"), "watermark": CUT, "match_state": "COMPLETE", "job_state": "SETTLED",
                "source_freshness": "RECENT"}
    for module in (index, evidence_money, financials):
        monkeypatch.setattr(module, "site_coverage", fake)
    monkeypatch.setattr(site_range, "dispatch_days", lambda snap, t, s, lo, hi, k: snap_days.dispatch_days(
        t, s, lo, hi, k) if str(s) == str(MG) else [])

    class PortfolioSnap(MoneySnapshot):
        def cited_provenance_many(self, t, items):
            return [self.cited_provenance(t, *x) for x in items]

        def awaiting_verification(self, *a):
            return 0

        def selected_windows(self, *a):
            return []

        def finding_index(self, t, s, k):
            return snap_days.finding_index(t, s, k)

    service = EstatePortfolioService(FakeStore(PortfolioSnap()))
    return SimpleNamespace(service=service)


def _req(**kw) -> EstateRequest:
    lo = kw.pop("from_", D0)
    return EstateRequest("portfolio", lo, kw.pop("to", lo + timedelta(days=7)), kw.pop("known_at", None), lens="all")


def _client(service, responses=None) -> TestClient:
    app = FastAPI()
    app.include_router(build_outcome_router(None, Registry(), estate=service, tenant=lambda: T,
                                            responses=responses))
    app.include_router(build_estate_portfolio_router(service, lambda: T, authenticate=lambda request: None,
                                                     access=lambda request, code: None))
    return TestClient(app)


def _range(c, code=KOBO, **query):
    return c.get(RANGE_ROUTE.format(site_code=code) + "?" + urlencode({**WINDOW, **query}))


# --- the body ----------------------------------------------------------------------------------------------------

def test_body_equals_portfolio_coverage_and_partial_money(world) -> None:
    c = _client(world.service)
    body = _range(c).json()
    portfolio = c.get("/api/estate/portfolio?" + urlencode({**WINDOW, "limit": 100})).json()
    entry = next(s for s in portfolio["coverage"]["sites"] if s["site_id"] == str(MG))
    assert body["schema_version"] == "site-range-overview-1"
    assert body["coverage"] == {k: v for k, v in entry.items() if k != "money"}
    assert body["coverage"]["state"] == "PARTIAL"
    assert body["money"]["partial"] == entry.get("money")
    assert body["money"]["partial"]["analysed_days"] == 5


def test_days_gap_set_equals_coverage_gaps(world) -> None:
    body = site_range_body(world.service, T, KOBO, _req())
    gaps = {(g["day"], site_range.STATE_OF_REASON[g["reason"]]) for g in body["coverage"]["days"]["gaps"]}
    gap_days = {(d["day"], d["state"]) for d in body["days"] if d["state"] not in (FINDINGS, CLEAR, NOT_EXPECTED)}
    assert gap_days == gaps and len(gaps) == 2
    assert [d["day"] for d in body["days"]] == [(D0 + timedelta(days=n)).date().isoformat() for n in range(7)]
    assert body["dispatch"]["days_requested"] == 7 and body["dispatch"]["days_analysed"] == 5
    assert body["dispatch"]["days_with_findings"] == sum(1 for d in body["days"] if d["state"] == FINDINGS)
    for d in body["days"]:
        if d["state"] == NOT_ANALYSED:
            assert d["finding_count"] is None and d["accepted_readings"] is None and d["money"] is None
            assert d["money_state"] == "WITHHELD"


def test_findings_counted_on_the_episode_day(world) -> None:
    body = site_range_body(world.service, T, KOBO, _req())
    by_day = {d["day"]: d for d in body["days"]}
    episode_day = PARTIAL_HEAD["episode_start"].date().isoformat()
    if body["findings"]["count"]:
        assert by_day[episode_day]["state"] == FINDINGS and by_day[episode_day]["finding_count"] >= 1
    assert body["findings"]["count"] == body["findings"]["confirmed"] + body["findings"]["not_confirmed"]
    assert body["links"] == {"findings": "/sites/KOBO-001/findings", "day": "/sites/KOBO-001?day={day}"}


def test_contract_golden(world) -> None:
    body = _range(_client(world.service)).json()
    if os.environ.get(REGEN) == "1":
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    assert body == json.loads(GOLDEN.read_text())


# --- the route ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("query", [
    {"from": "2026-10-13T06:00:00Z"},                       # not midnight
    {"to": "2026-11-14T00:00:00Z"},                         # over 31 days
    {"to": None},                                           # missing `to`
    {"from": "2026-10-20T00:00:00Z"},                       # empty window
    {"from": "yesterday"},                                  # not an instant
])
def test_bad_window_is_422(world, query) -> None:
    params = {k: v for k, v in {**WINDOW, **query}.items() if v is not None}
    r = _client(world.service).get(RANGE_ROUTE.format(site_code=KOBO) + "?" + urlencode(params))
    assert r.status_code == 422 and r.json()["detail"]["code"] == "INVALID_WINDOW"


@pytest.mark.parametrize("code,status,refusal", [
    ("COLD 1", 404, "RANGE_OVERVIEW_NOT_APPLICABLE"), ("EV-1", 404, "RANGE_OVERVIEW_NOT_APPLICABLE"),
    ("NOPE-9", 404, "SITE_NOT_FOUND")])
def test_not_applicable_and_unknown_sites(world, code, status, refusal) -> None:
    r = _range(_client(world.service), code)
    assert r.status_code == status and r.json()["detail"]["code"] == refusal


def test_site_outside_the_estate_scope_is_404(world, monkeypatch) -> None:
    monkeypatch.setattr(EstatePortfolioService, "_scope", staticmethod(
        lambda snap, t, req, admit: {"sites": [], "k": CUT}))
    r = _range(_client(world.service))
    assert r.status_code == 404 and r.json()["detail"]["code"] == "SITE_NOT_FOUND"


@pytest.mark.parametrize("refusal,status", [(401, 401), (403, 403)])
def test_admission_through_the_board_seams(world, refusal, status) -> None:
    app = FastAPI()
    app.include_router(build_outcome_router(None, Registry(), estate=world.service, tenant=lambda: T,
                                            access=lambda request, code: refusal))
    r = _range(TestClient(app))
    assert r.status_code == status


def test_unavailable_store_and_no_estate_are_503(world) -> None:
    down = EstatePortfolioService(FakeStore(EstateStoreUnavailable("down")))
    for service in (down, None):
        r = _range(_client(service))
        assert r.status_code == 503 and r.json()["detail"]["code"] == "SITE_RANGE_OVERVIEW_UNAVAILABLE"


def test_stored_response_key_watermark_and_perf_line(world, caplog) -> None:
    responses = Responses()
    with caplog.at_level(logging.INFO, logger="assetops.perf"):
        r = _range(_client(world.service, responses), known_at="2026-10-20T06:00:00Z")
    assert r.status_code == 200
    (route,) = responses.routes
    assert route.route == RANGE_ROUTE and route.tenant_id == T
    assert set(route.request) == {"site", "from", "to", "known_at"} and route.request["site"] == MG
    assert route.sites == (MG,) and route.watermark_sites == (MG,)
    lines = [json.loads(x.getMessage()) for x in caplog.records if x.name == "assetops.perf"]
    assert [x["route"] for x in lines] == [RANGE_ROUTE] and lines[0]["status"] == "ok"


# --- the day precedence table (D-E5.46 order) --------------------------------------------------------------------

D = date(2026, 10, 13)
SELECTED = {"available": True, "selection": {"seq": 5}, "jobs": []}


@pytest.mark.parametrize("row,grade,reasons,count,state", [
    (SELECTED, "NOT_EXPECTED", {D: READINGS_CONFLICT}, 2, NOT_EXPECTED),
    (SELECTED, "NO_DATA", {D: READINGS_CONFLICT}, 2, NO_READINGS),
    (SELECTED, "PENDING", {D: READINGS_CONFLICT}, 2, STILL_PROCESSING),
    ({**SELECTED, "jobs": [{"status": "LEASED"}]}, None, {D: READINGS_CONFLICT}, 2, STILL_PROCESSING),
    (SELECTED, None, {D: READINGS_CONFLICT}, 2, READINGS_CONFLICT),
    (SELECTED, None, {D: NOT_ENOUGH_READINGS}, 0, NOT_ENOUGH_READINGS),
    ({**SELECTED, "selection": None}, None, {}, 2, NOT_ANALYSED),
    ({**SELECTED, "available": False}, None, {}, 2, NOT_ANALYSED),
    (None, None, {}, 0, NOT_ANALYSED),
    ({**SELECTED, "_unmatched": True}, None, {}, 2, STILL_PROCESSING),
    (SELECTED, "COMPLETE", {}, 2, FINDINGS),
    (SELECTED, None, {}, 0, CLEAR),
])
def test_day_state_precedence(row, grade, reasons, count, state) -> None:
    assert _day_state(D, row, grade, reasons, count) == state
