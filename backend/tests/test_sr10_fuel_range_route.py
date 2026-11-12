"""SR-10b (rev 10b.2/10b.3 tests, D-SR.31/32/45): `GET /api/sites/{code}/fuel-range` on stubs (no database).

A stub period reader returning stored `mini_depth.fuel_day` rows (and a real `PeriodReadResult` for the pending and
absent rules) plus a real `ChainReader` over a fake snapshot port for the day grades. Covers the body, `window_days`
(a 7-day Nairobi window is 7 rows), an absent row (STILL_PROCESSING), a pending row, refusals (422/404/401/403/503),
the stored-route key and watermark Site, and the perf line."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from assetops_backend.chain import read as cr
from assetops_backend.chain.period_read import PeriodRead, PeriodReadResult
from assetops_backend.chain.ports import SnapshotRow
from assetops_backend.mini_depth import period_rows as pr
from assetops_backend.mini_depth.read import _Head, _Hour
from assetops_backend.mini_depth.inputs import local_hour
from assetops_backend.mini_depth_api import DAY_RANGE_ROUTES, build_day_range_router
from assetops_backend.sites.ports import SiteStoreUnavailable

TENANT = UUID("00000000-0000-0000-0000-0000000000a1")
SITE = UUID("00000000-0000-0000-0000-0000000000b1")
COLD = UUID("00000000-0000-0000-0000-0000000000c1")
EV = UUID("00000000-0000-0000-0000-0000000000d1")
TZ = "Africa/Nairobi"
D0 = date(2026, 11, 1)
URL = "/api/sites/KOBO-001/fuel-range"
WEEK = {"from": "2026-11-01T00:00:00Z", "to": "2026-11-08T00:00:00Z"}
KIND = "mini_depth.fuel_day"
ROUTE = DAY_RANGE_ROUTES["fuel"]


def _hour(day: date, h: int, use: tuple | None, status: str = "SUPPORTED") -> dict:
    w = local_hour(day, h, TZ)
    head = None if use is False else _Head(1, uuid4(), w.start, "sha", {
        "status": status, "limitations": [],
        "cards": {"expected_use_l": None if use is None else {"low": use[0], "high": use[1]}, "residual_l": None}},
        ())
    return pr.hour_json(_Hour(day, w, head, "SETTLED" if head else "NONE", "CURRENT" if head else "UNKNOWN",
                              None, ()))


def _row(day: date, hours: list[dict]) -> PeriodRead:
    return PeriodRead(SimpleNamespace(site_id=SITE, local_day=day, kind=KIND, body={"hours": hours}))


def _full(day: date, use=(1, 2)) -> PeriodRead:
    return _row(day, [_hour(day, h, use) for h in range(24)])


#: D0, D1 assessed (24/24), D2 one hour missing, D3 absent, D4 pending at k, D5 no assessment, D6 not expected.
ROWS = [_full(D0), _full(D0 + timedelta(1), (0.5, 0.75)),
        _row(D0 + timedelta(2), [_hour(D0 + timedelta(2), h, (1, 1)) for h in range(23)]
             + [_hour(D0 + timedelta(2), 23, False)]),
        _full(D0 + timedelta(4)),
        _row(D0 + timedelta(5), [_hour(D0 + timedelta(5), h, False) for h in range(24)]),
        _full(D0 + timedelta(6))]


class Periods:
    def __init__(self, rows=ROWS, fail=False):
        self.rows, self.fail, self.calls = list(rows), fail, []

    def read(self, tenant_id, sites, kinds, from_day, to_day, known_at=None, log_absent=True):
        self.calls.append((tenant_id, [s.site_id for s in sites], list(kinds), from_day, to_day, known_at))
        if self.fail:
            raise SiteStoreUnavailable("down")
        rows = [r for r in self.rows if from_day <= r.row.local_day <= to_day]
        have = {r.row.local_day for r in rows}
        absent = tuple((SITE, from_day + timedelta(i), KIND) for i in range((to_day - from_day).days + 1)
                       if from_day + timedelta(i) not in have)
        return PeriodReadResult(rows, {(SITE, D0 + timedelta(4), KIND): ("dirty",)}, 2, absent)


def _snap(day, grade, measure="productive_kwh"):
    return SnapshotRow(tenant_id=TENANT, site_id=SITE, local_day=day, subject_kind="SITE", subject_ref="SITE",
                       measure=measure, evidence_class="MEASURED", revision=1, expected=grade != "NOT_EXPECTED",
                       required_seconds=1, covered_seconds=1, coverage_pct="100", grade=grade, value=None,
                       money=None, policy_version="p", calendar_version="c", catalogue_version=1,
                       input_fp=f"{day}-{measure}")


class Port:
    def __init__(self, fail=False):
        self.fail, self.calls = fail, []

    def snapshots(self, tenant_id, site_id, lo, hi, measures, known_at):
        self.calls.append((tenant_id, site_id, lo, hi, known_at))
        if self.fail:
            raise SiteStoreUnavailable("down")
        out = []
        for i in range((hi - lo).days + 1):
            d = lo + timedelta(i)
            grade = "NOT_EXPECTED" if d == D0 + timedelta(6) else "COMPLETE"
            out += [_snap(d, grade, m) for m in measures]
        return tuple(out)


@dataclass
class Site:
    tenant_id: UUID
    id: UUID
    site_code: str
    name: str
    site_type: str
    timezone: str


SITES = {"KOBO-001": Site(TENANT, SITE, "KOBO-001", "Kobo", "MINIGRID", TZ),
         "COLD-001": Site(TENANT, COLD, "COLD-001", "Cold", "COLDCHAIN", TZ),
         "EV-001": Site(TENANT, EV, "EV-001", "EV", "EV_CHARGING", TZ)}


class Registry:
    def __init__(self, fail=False):
        self.fail = fail

    def tenant(self):
        if self.fail:
            raise SiteStoreUnavailable("down")
        return SimpleNamespace(id=TENANT)

    def imported(self, code):
        return SITES.get(code)


class Store:
    def __init__(self):
        self.requests = []

    def serve(self, req, compose, if_none_match=None):
        self.requests.append(req)
        return Response(json.dumps(compose()[req.route]), media_type="application/json")


def client(periods=None, port=None, *, chain=True, access=lambda r, c: None, registry=None, responses=None):
    periods = Periods() if periods is None else periods
    reader = cr.ChainReader(port or Port()) if chain else None
    app = FastAPI()
    app.include_router(build_day_range_router("fuel", lambda: periods, lambda: reader, registry or Registry(),
                                              access=access, responses=responses,
                                              now=lambda: datetime(2026, 11, 12, tzinfo=timezone.utc)))
    return TestClient(app)


def _body(**kw):
    response = client(**kw).get(URL, params=WEEK)
    assert response.status_code == 200, response.text
    return response.json()


def test_each_day_reads_its_stored_day_row_and_state():
    body = _body()
    assert body["schema_version"] == "site-fuel-range-1"
    assert body["site"] == {"site_code": "KOBO-001", "site_name": "Kobo", "timezone": TZ}
    assert body["window"] == {"from": "2026-11-01T00:00:00.000000Z", "to": "2026-11-08T00:00:00.000000Z",
                              "known_at": None}
    days = body["days"]
    assert [d["local_day"] for d in days] == [(D0 + timedelta(i)).isoformat() for i in range(7)]  # D-SR.45: 7 rows
    assert [(d["state"], d["partial"]) for d in days] == [
        ("ASSESSED", False), ("ASSESSED", False), ("ASSESSED", True), ("STILL_PROCESSING", False),
        ("STILL_PROCESSING", False), ("NO_ASSESSMENT", True), ("NOT_EXPECTED", False)]
    assert days[0]["expected_use_l"] == {"low": 24, "high": 48} and days[0]["hours_assessed"] == 24
    assert (days[2]["hours_assessed"], days[2]["hours_missing"]) == (23, 1)
    assert days[4]["hours_pending"] == 24  # a dirty day at k: every stored hour is PENDING_RECOMPUTE
    assert days[0]["hour_link"] == ("/sites/KOBO-001/performance/fuel"
                                    "?from=2026-11-01T09%3A00%3A00Z&to=2026-11-01T10%3A00%3A00Z")
    assert not any(k.startswith("residual") for d in days for k in d)
    # D-SR.51 (3): an absent day is unknown, not zero
    assert days[3]["stored"] is False and days[0]["stored"] is True
    assert all(days[3][k] is None for k in ("hours_expected", "hours_assessed", "hours_pending", "hours_missing",
                                            "status_counts", "expected_use_l", "hours_with_use"))


def test_range_reads_rows_with_the_kill_switch_empty(monkeypatch):
    """D-SR.52: ASSETOPS_PERIOD_READ_KINDS selects stored rows over a compose, but the day kinds have no compose, so the
    range still reads the stored rows with the switch empty."""
    monkeypatch.setenv("ASSETOPS_PERIOD_READ_KINDS", "")
    periods = Periods()
    body = _body(periods=periods)
    assert periods.calls and periods.calls[0][2] == [KIND]
    assert body["days"][0]["state"] == "ASSESSED" and body["days"][0]["stored"] is True


def test_totals_sum_counted_days_only():
    assert _body()["totals"] == {"days_counted": 3, "days_requested": 7, "partial": True,
                                 "expected_use_l": {"low": 59, "high": 89}}


def test_one_period_read_and_one_chain_read_over_window_days_with_known_at():
    periods, port = Periods(), Port()
    known = datetime(2026, 11, 9, 10, tzinfo=timezone.utc)
    response = client(periods, port).get(URL, params={**WEEK, "known_at": "2026-11-09T10:00:00Z"})
    assert response.status_code == 200
    assert periods.calls == [(TENANT, [SITE], [KIND], D0, D0 + timedelta(6), known)]
    assert port.calls == [(TENANT, SITE, D0, D0 + timedelta(6), known)]


def test_thirty_one_days_is_allowed():
    response = client().get(URL, params={"from": "2026-10-01T00:00:00Z", "to": "2026-11-01T00:00:00Z"})
    assert response.status_code == 200 and len(response.json()["days"]) == 31


@pytest.mark.parametrize("params,code", [
    ({}, "INVALID_WINDOW"),
    ({"from": "2026-11-01T00:00:00Z"}, "INVALID_WINDOW"),
    ({"from": "2026-11-01T03:00:00Z", "to": "2026-11-08T00:00:00Z"}, "INVALID_WINDOW"),
    ({"from": "2026-11-08T00:00:00Z", "to": "2026-11-01T00:00:00Z"}, "INVALID_WINDOW"),
    ({"from": "2026-10-01T00:00:00Z", "to": "2026-11-02T00:00:00Z"}, "INVALID_WINDOW"),
    ({"from": "2026-11-01", "to": "2026-11-08"}, "INVALID_WINDOW"),
    ({**WEEK, "known_at": "yesterday"}, "INVALID_KNOWN_AT"),
])
def test_window_refusals(params, code):
    response = client().get(URL, params=params)
    assert (response.status_code, response.json()["detail"]["code"]) == (422, code)


def test_admission_lookup_type_and_unavailable_refusals():
    def code(response):
        return response.status_code, response.json()["detail"]["code"]

    assert code(client(access=lambda r, c: 401).get(URL, params=WEEK)) == (401, "UNAUTHENTICATED")
    assert code(client(access=lambda r, c: 403).get(URL, params=WEEK)) == (403, "SITE_SCOPE_FORBIDDEN")
    assert code(client().get("/api/sites/NOPE/fuel-range", params=WEEK)) == (404, "SITE_NOT_FOUND")
    for other in ("COLD-001", "EV-001"):
        assert code(client().get(f"/api/sites/{other}/fuel-range", params=WEEK)) == \
            (404, "FUEL_RANGE_NOT_APPLICABLE")
    for kw in ({"registry": Registry(fail=True)}, {"chain": False}, {"periods": Periods(fail=True)},
               {"port": Port(fail=True)}):
        assert code(client(**kw).get(URL, params=WEEK)) == (503, "SITE_FUEL_RANGE_UNAVAILABLE"), kw


def test_stored_route_key_and_watermark_site_and_body_equal_compose():
    store = Store()
    params = {**WEEK, "known_at": "2026-11-09T10:00:00Z"}
    response = client(responses=store).get(URL, params=params)
    assert response.status_code == 200
    (req,) = store.requests
    assert req.route == ROUTE == "/api/sites/{site_code}/fuel-range" and req.tenant_id == TENANT
    assert dict(req.request) == {"site": str(SITE), "from": "2026-11-01T00:00:00.000000Z",
                                 "to": "2026-11-08T00:00:00.000000Z", "known_at": "2026-11-09T10:00:00.000000Z"}
    assert req.sites == (SITE,) and req.watermark_sites == (SITE,)
    assert response.json() == client().get(URL, params=params).json()


def test_the_route_writes_a_perf_line(caplog):
    caplog.set_level("INFO")
    assert client().get(URL, params=WEEK).status_code == 200
    assert any(ROUTE in r.getMessage() for r in caplog.records)
