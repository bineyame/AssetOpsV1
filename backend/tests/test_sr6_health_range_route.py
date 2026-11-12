"""SR-6a (rev 10 §10.2, rev 10a §10a.1, D-SR.19-23): mini-grid Health over a range, `site-health-range-1`, no
database. The world is SR-5a's (`test_sr5_range_overview.world`: KOBO-001 over 7 days, two unchecked days), so the
Health day states are pinned against the range Overview's on the same snapshot (D-SR.22). Registration and the two
grouped counts are injected doubles; their SQL is exercised by `test_sr6_health_range_postgres.py`."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.parse import urlencode
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend import source_health_api
from assetops_backend.estate.portfolio import EstatePortfolioService
from assetops_backend.estate.range_days import ANALYSED, NO_READINGS, NOT_EXPECTED
from assetops_backend.estate.scope import EstateRequest, EstateStoreUnavailable
from assetops_backend.estate.site_range import CLEAR, FINDINGS, site_range_body
from assetops_backend.evidence.source_health import RegisteredGateway, RegisteredSource
from assetops_backend.sites import site_health_range
from assetops_backend.sites.site_health_range import (
    IN_CONTACT, NO_CONTACT, PARTIAL_CONTACT, READINGS, READINGS_ONLY, gateway_contact, health_range_body,
    source_state)
from assetops_backend.source_health_api import HEALTH_RANGE_ROUTE, build_health_range_router
from test_sr5_range_overview import KOBO, SITES, Responses, _cursor_key, world  # noqa: F401 - pytest fixtures
from test_w302_evidence_api import CUT, D0, MG, T, WINDOW, FakeStore

G1, G2 = UUID("20000000-0000-4000-8000-000000000001"), UUID("20000000-0000-4000-8000-000000000002")
S1, S2 = UUID("30000000-0000-4000-8000-000000000001"), UUID("30000000-0000-4000-8000-000000000002")
CONN = object()
GATEWAYS = (RegisteredGateway(T, MG, G1, "edge-1", "LIVE", D0 - timedelta(days=30), False, 60),
            RegisteredGateway(T, MG, G2, "edge-2", "LIVE", D0 + timedelta(days=2, hours=5), True, 60))
SOURCES = (RegisteredSource(T, MG, G1, S1, "meter-1", False), RegisteredSource(T, MG, G2, S2, "meter-2", False))
DAY = [(D0 + timedelta(days=n)).date() for n in range(7)]
FULL = 24 * 60  # one diagnostic a minute over a whole day
DIAG = {(str(G1), DAY[0]): {"n": FULL, "first_at": D0, "last_at": D0 + timedelta(hours=23, minutes=59)},
        (str(G1), DAY[1]): {"n": 600, "first_at": D0 + timedelta(days=1), "last_at": D0 + timedelta(days=1, hours=10)}}
READS = {(str(S1), DAY[0]): {"n": 288, "last_at": D0 + timedelta(hours=23)},
         (str(S1), DAY[2]): {"n": 100, "last_at": D0 + timedelta(days=2, hours=9)},
         (str(S2), DAY[3]): {"n": 5, "last_at": D0 + timedelta(days=3, hours=1)}}
BATTERY = {"configuration": "NOT_CONFIGURED", "batteries": []}


class Calls:
    def __init__(self) -> None:
        self.seen: list = []

    def registration(self, c, t, s):
        self.seen.append(("registration", c, t, s))
        return GATEWAYS, SOURCES

    def counts(self, c, t, s, lo, hi, k):
        self.seen.append(("counts", c, t, s, lo, hi, k))
        return DIAG, READS


@pytest.fixture()
def health(world, monkeypatch):
    world.service.store.outcomes[0]._c = CONN  # the snapshot's one connection
    calls = Calls()
    monkeypatch.setattr(source_health_api, "battery_entry", lambda view, at, basis: BATTERY)
    return SimpleNamespace(service=world.service, calls=calls)


def _req(**kw) -> EstateRequest:
    lo = kw.pop("from_", D0)
    return EstateRequest("portfolio", lo, kw.pop("to", lo + timedelta(days=7)), kw.pop("known_at", None), lens="all")


def _body(health) -> dict:
    return health_range_body(health.service, T, KOBO, _req(), health.calls.registration, health.calls.counts)


class Registry:
    service = SimpleNamespace(read=lambda site, tenant, a, b: SimpleNamespace(now=CUT))

    def tenant(self):
        return SimpleNamespace(id=T)

    def imported(self, code):
        return SITES.get(code)


def _client(service, responses=None, access=lambda request, code: None, calls=None) -> TestClient:
    calls = calls or Calls()
    app = FastAPI()
    app.include_router(build_health_range_router(service, Registry(), responses, registration=calls.registration,
                                                 counts=calls.counts, access=access))
    return TestClient(app)


def _get(c, code=KOBO, **query):
    params = {k: v for k, v in {**WINDOW, **query}.items() if v is not None}
    return c.get(HEALTH_RANGE_ROUTE.format(site_code=code) + "?" + urlencode(params))


# --- the body -----------------------------------------------------------------------------------------------------

def test_days_pin_equal_the_range_overview(health) -> None:
    """D-SR.22: Health ANALYSED days are exactly the Overview's FINDINGS/CLEAR days; every other state is equal."""
    mine = {d["day"]: d for d in _body(health)["days"]}
    theirs = {d["day"]: d for d in site_range_body(health.service, T, KOBO, _req())["days"]}
    assert list(mine) == list(theirs) == [d.isoformat() for d in DAY]
    for day, d in mine.items():
        other = theirs[day]["state"]
        assert (d["state"] == ANALYSED) == (other in (FINDINGS, CLEAR))
        if d["state"] != ANALYSED:
            assert d["state"] == other
        assert d["accepted_readings"] == theirs[day]["accepted_readings"]
    assert sum(1 for d in mine.values() if d["state"] == ANALYSED) == 5


def test_reads_run_on_the_snapshot_connection_in_order(health) -> None:
    body = _body(health)
    (reg, counts) = health.calls.seen
    assert reg == ("registration", CONN, T, MG)
    assert counts[:6] == ("counts", CONN, T, MG, D0, D0 + timedelta(days=7))
    k = health.service.store.outcomes[0].read_at  # no `known_at`: the snapshot's read time is the cutoff
    assert counts[6] == k
    assert body["window"] == {"from": "2026-10-13T00:00:00Z", "to": "2026-10-20T00:00:00Z",
                              "known_at": k.strftime("%Y-%m-%dT%H:%M:%SZ"), "basis": "CURRENT"}
    assert body["schema_version"] == "site-health-range-1"
    assert body["site"]["site_code"] == KOBO and body["links"] == {"day": "/sites/KOBO-001/health?day={day}"}


def test_gateway_and_source_days(health) -> None:
    body = _body(health)
    g1, g2 = body["gateways"]
    assert g1["gateway_external_id"] == "edge-1" and g1["cadence_seconds"] == 60 and g1["disabled"] is False
    assert [x["contact"] for x in g1["days"]][:3] == [IN_CONTACT, PARTIAL_CONTACT, READINGS_ONLY]
    assert g1["days"][0]["diagnostics"] == FULL and g1["days"][0]["first_received_at"] == "2026-10-13T00:00:00Z"
    assert g1["days"][3]["contact"] == NO_CONTACT and g1["days"][3]["last_received_at"] is None
    # edge-2 registered on day 2: days 0-1 NOT_EXPECTED; day 3 readings through it, no diagnostics
    assert [x["contact"] for x in g2["days"]][:4] == [NOT_EXPECTED, NOT_EXPECTED, NO_CONTACT, READINGS_ONLY]
    assert g2["disabled"] is True
    s1, s2 = body["sources"]
    assert s1["source_external_id"] == "meter-1"
    assert s1["days"][0] == {"day": DAY[0].isoformat(), "accepted_readings": 288,
                             "last_received_at": "2026-10-13T23:00:00Z", "state": READINGS}
    assert s1["days"][1]["state"] == NO_READINGS and s1["days"][1]["accepted_readings"] == 0
    assert s2["days"][3]["accepted_readings"] == 5
    summary = body["summary"]
    assert summary["days_requested"] == 7 and summary["days_with_readings"] == 3
    assert summary["days_without_readings"] == sum(1 for d in body["days"] if d["state"] == NO_READINGS)
    assert summary["gateways_in_contact_all_days"] == 0


def test_source_day_not_expected_follows_the_day_state(health, monkeypatch) -> None:
    states = {d: {"state": NOT_EXPECTED if d == DAY[0] else ANALYSED, "row": None} for d in DAY}
    monkeypatch.setattr(site_health_range, "range_day_states", lambda *a: states)
    s1 = _body(health)["sources"][0]
    assert s1["days"][0]["state"] == NOT_EXPECTED and s1["days"][0]["accepted_readings"] == 288
    assert s1["days"][2]["state"] == READINGS


H = datetime(2026, 10, 13, tzinfo=timezone.utc)
REG = H - timedelta(days=1)


@pytest.mark.parametrize("diag,reads,hi,registered,want", [
    (1440, 0, H + timedelta(days=1), REG, IN_CONTACT),
    (1296, 0, H + timedelta(days=1), REG, IN_CONTACT),           # exactly 0.9 of the day
    (1295, 50, H + timedelta(days=1), REG, PARTIAL_CONTACT),     # just under; diagnostics win over readings
    (360, 0, H + timedelta(hours=6), REG, IN_CONTACT),           # k at 06:00: only the seconds before k count
    (0, 3, H + timedelta(days=1), H + timedelta(days=2), READINGS_ONLY),  # readings beat "before registered"
    (0, 0, H + timedelta(days=1), H + timedelta(days=1), NOT_EXPECTED),
    (0, 0, H + timedelta(days=1), H + timedelta(hours=12), NO_CONTACT),   # registered that day
])
def test_gateway_contact_rule(diag, reads, hi, registered, want) -> None:
    assert gateway_contact(H.date(), diag, reads, 60, registered, H, hi) == want


@pytest.mark.parametrize("day_state,reads,want", [
    (NOT_EXPECTED, 0, NOT_EXPECTED), (ANALYSED, 1, READINGS), (ANALYSED, 0, NO_READINGS),
    (NO_READINGS, 0, NO_READINGS)])
def test_source_state_rule(day_state, reads, want) -> None:
    assert source_state(day_state, reads) == want


def test_not_a_mini_grid_site_in_scope_is_refused(health, monkeypatch) -> None:
    monkeypatch.setattr(EstatePortfolioService, "_scope", staticmethod(
        lambda snap, t, req, admit: {"sites": [{"site_type": "COLDCHAIN", "site_id": MG}], "k": CUT}))
    with pytest.raises(site_health_range.HealthRangeNotApplicable):
        _body(health)


# --- the route ----------------------------------------------------------------------------------------------------

def test_route_body_carries_the_battery_entry(health) -> None:
    r = _get(_client(health.service))
    assert r.status_code == 200
    body = r.json()
    assert body["battery"] == BATTERY and body["schema_version"] == "site-health-range-1"
    assert [d["day"] for d in body["days"]] == [d.isoformat() for d in DAY]


@pytest.mark.parametrize("query", [
    {"from": "2026-10-13T06:00:00Z"},                       # not midnight
    {"to": "2026-11-14T00:00:00Z"},                         # over 31 days
    {"to": None},                                           # missing `to`
    {"from": "2026-10-20T00:00:00Z"},                       # empty window
    {"from": "yesterday"},                                  # not an instant
])
def test_bad_window_is_422(health, query) -> None:
    r = _get(_client(health.service), **query)
    assert r.status_code == 422 and r.json()["detail"]["code"] == "INVALID_WINDOW"


@pytest.mark.parametrize("code", ["COLD 1", "EV-1"])
def test_cold_and_ev_are_not_applicable(health, code) -> None:
    r = _get(_client(health.service), code)
    assert r.status_code == 404 and r.json()["detail"]["code"] == "HEALTH_RANGE_NOT_APPLICABLE"


def test_unknown_site_and_site_outside_the_scope_are_404(health, monkeypatch) -> None:
    assert _get(_client(health.service), "NOPE-9").status_code == 404
    monkeypatch.setattr(EstatePortfolioService, "_scope", staticmethod(
        lambda snap, t, req, admit: {"sites": [], "k": CUT}))
    r = _get(_client(health.service))
    assert r.status_code == 404 and r.json()["detail"]["code"] == "SITE_NOT_FOUND"


@pytest.mark.parametrize("refusal", [401, 403])
def test_admission_as_source_health(health, refusal) -> None:
    r = _get(_client(health.service, access=lambda request, code: refusal, calls=health.calls))
    assert r.status_code == refusal
    assert not health.calls.seen


def test_unavailable_store_and_no_estate_are_503(health) -> None:
    down = EstatePortfolioService(FakeStore(EstateStoreUnavailable("down")))
    for service in (down, None):
        r = _get(_client(service))
        assert r.status_code == 503 and r.json()["detail"]["code"] == "SITE_HEALTH_RANGE_UNAVAILABLE"


def test_stored_response_key_watermark_and_perf_line(health, caplog) -> None:
    responses = Responses()
    with caplog.at_level(logging.INFO, logger="assetops.perf"):
        r = _get(_client(health.service, responses), known_at="2026-10-20T06:00:00Z")
    assert r.status_code == 200
    (route,) = responses.routes
    assert route.route == HEALTH_RANGE_ROUTE and route.tenant_id == T
    assert set(route.request) == {"site", "from", "to", "known_at"} and route.request["site"] == MG
    assert route.sites == (MG,) and route.watermark_sites == (MG,)
    lines = [json.loads(x.getMessage()) for x in caplog.records if x.name == "assetops.perf"]
    assert [x["route"] for x in lines] == [HEALTH_RANGE_ROUTE] and lines[0]["status"] == "ok"
