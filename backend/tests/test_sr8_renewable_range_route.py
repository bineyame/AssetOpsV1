"""SR-8 (rev 10 §10.4, rev 10a §10a.3, D-SR.27): `GET /api/sites/{code}/renewable-range` on stubs (no database).

A real `ChainReader` over a fake snapshot port: each D-SR.27 day state from a stored `daylight_headroom_kw` row,
the absent-row day (D-SR.16: a missing row reads the chain's NO_DATA, never "nothing known"), the averages over
COUNTED days only, hours from the row's seconds, the one-day link, refusals, the stored-route key and the perf line.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from assetops_backend.chain import read as cr
from assetops_backend.chain.ports import SnapshotRow
from assetops_backend.mini_depth_api import RENEWABLE_RANGE_ROUTE, build_renewable_range_router
from assetops_backend.sites import renewable_range as rr
from assetops_backend.sites.ports import SiteStoreUnavailable

TENANT = UUID("00000000-0000-0000-0000-0000000000a1")
SITE = UUID("00000000-0000-0000-0000-0000000000b1")
COLD = UUID("00000000-0000-0000-0000-0000000000c1")
TZ = "Africa/Nairobi"
D0 = date(2026, 11, 1)
URL = "/api/sites/KOBO-001/renewable-range"
WEEK = {"from": "2026-11-01T00:00:00Z", "to": "2026-11-08T00:00:00Z"}


def _row(day, grade, value, measure="daylight_headroom_kw", covered=36000, required=43200):
    return SnapshotRow(tenant_id=TENANT, site_id=SITE, local_day=day, subject_kind="SITE", subject_ref="SITE",
                       measure=measure, evidence_class="MEASURED", revision=1, expected=True,
                       required_seconds=required, covered_seconds=covered, coverage_pct="83.3", grade=grade,
                       value=value, money=None, policy_version="p", calendar_version="c", catalogue_version=1,
                       input_fp=f"{day}-{measure}")


def _band(low, high, decision="ELIGIBLE", hours=6):
    return {"low_kw": low, "high_kw": high, "decision": decision, "window_hours": hours}


def _nulls(state):
    return {"low_kw": None, "high_kw": None, "decision": None, "window_hours": None, "result_state": state}


#: One week: COUNTED x2, EXCLUDED (bounds shown), CONFLICT, MISSING_HOUR, no row (D-SR.16), PENDING.
ROWS = [
    _row(D0, "COMPLETE", _band("10.5", "20")),
    _row(D0 + timedelta(1), "COMPLETE", _band("11", "21.25")),
    _row(D0 + timedelta(2), "COMPLETE", _band("50", "60", "EXCLUDED", 0)),
    _row(D0 + timedelta(3), "COMPLETE", _nulls("CONFLICT")),
    _row(D0 + timedelta(4), "PARTIAL", _nulls("MISSING_HOUR"), covered=32400),
    _row(D0 + timedelta(6), "PENDING", None, covered=0),
    _row(D0, "COMPLETE", {"served_kwh": "1"}, measure="critical_served"),
]


class Port:
    def __init__(self, rows=ROWS, fail=False):
        self.rows, self.fail, self.calls = list(rows), fail, []

    def snapshots(self, tenant_id, site_id, lo, hi, measures, known_at):
        self.calls.append((tenant_id, site_id, lo, hi, known_at))
        if self.fail:
            raise SiteStoreUnavailable("down")
        return tuple(r for r in self.rows if lo <= r.local_day <= hi and r.measure in measures)


@dataclass
class Site:
    tenant_id: UUID
    id: UUID
    site_code: str
    name: str
    site_type: str
    timezone: str


SITES = {"KOBO-001": Site(TENANT, SITE, "KOBO-001", "Kobo", "MINIGRID", TZ),
         "COLD-001": Site(TENANT, COLD, "COLD-001", "Cold", "COLDCHAIN", TZ)}


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


def client(port=None, *, reader=True, access=lambda r, c: None, registry=None, responses=None):
    port = Port() if port is None else port
    chain = cr.ChainReader(port) if reader else None
    app = FastAPI()
    app.include_router(build_renewable_range_router(lambda: chain, registry or Registry(), access=access,
                                                    responses=responses))
    return TestClient(app)


def _body(**kw):
    response = client(**kw).get(URL, params=WEEK)
    assert response.status_code == 200, response.text
    return response.json()


# ---- body ----------------------------------------------------------------------------------------------------------

def test_each_day_reads_its_stored_row_and_state():
    body = _body()
    assert body["schema_version"] == "site-renewable-range-1"
    assert body["site"] == {"site_code": "KOBO-001", "site_name": "Kobo", "timezone": TZ}
    assert body["window"] == {"from": "2026-11-01T00:00:00.000000Z", "to": "2026-11-08T00:00:00.000000Z",
                              "known_at": None}
    days = body["days"]
    assert [d["local_day"] for d in days] == [(D0 + timedelta(i)).isoformat() for i in range(7)]
    assert [d["state"] for d in days] == ["COUNTED", "COUNTED", "EXCLUDED", "CONFLICT", "MISSING_HOUR",
                                          "NO_DATA", "PENDING"]
    assert [d["grade"] for d in days] == ["COMPLETE", "COMPLETE", "COMPLETE", "COMPLETE", "PARTIAL", "NO_DATA",
                                          "PENDING"]
    assert (days[0]["low_kw"], days[0]["high_kw"], days[0]["decision"], days[0]["window_hours"]) == \
        ("10.5", "20", "ELIGIBLE", 6)
    assert (days[2]["low_kw"], days[2]["high_kw"], days[2]["decision"]) == ("50", "60", "EXCLUDED")
    for d in days[3:]:
        assert d["low_kw"] is None and d["high_kw"] is None
    assert (days[0]["covered_hours"], days[0]["operating_hours"]) == (10.0, 12.0)
    assert (days[4]["covered_hours"], days[4]["operating_hours"]) == (9.0, 12.0)
    assert (days[5]["covered_hours"], days[5]["operating_hours"]) == (None, None)


def test_absent_row_inside_the_range_reads_the_chain_no_data_grade():
    """D-SR.16 / rev 10 §10.1: a day with no stored row reads the chain read's own NO_DATA, as `day_gaps` does."""
    day = _body()["days"][5]
    assert (day["grade"], day["state"]) == ("NO_DATA", "NO_DATA")
    assert D0 + timedelta(5) in cr.day_gaps(ROWS, [D0 + timedelta(5)], ("daylight_headroom_kw",))


def test_averages_are_over_counted_days_only_and_partial_is_labelled():
    totals = _body()["totals"]
    assert totals == {"days_requested": 7, "days_counted": 2, "average_low_kw": "10.75",
                      "average_high_kw": "20.63", "average_label": "average headroom available in every eligible hour", "partial": True}


def test_a_full_counted_range_is_not_partial_and_an_empty_one_has_no_average():
    rows = [_row(D0 + timedelta(i), "COMPLETE", _band("1", "3")) for i in range(7)]
    assert _body(port=Port(rows))["totals"]["partial"] is False
    empty = _body(port=Port([]))["totals"]
    assert (empty["days_counted"], empty["average_low_kw"], empty["average_high_kw"], empty["partial"]) == \
        (0, None, None, True)


def test_counted_day_without_both_bounds_is_not_averaged():
    rows = [_row(D0, "COMPLETE", _band(None, "3")), _row(D0 + timedelta(1), "COMPLETE", _band("2", "4"))]
    totals = _body(port=Port(rows))["totals"]
    assert (totals["days_counted"], totals["average_low_kw"], totals["average_high_kw"]) == (1, "2.00", "4.00")


@pytest.mark.parametrize("grade,value,state", [
    ("COMPLETE", _nulls("LIMITED"), "LIMITED"),
    ("NOT_EXPECTED", None, "NOT_EXPECTED"),
    ("NO_DATA", None, "NO_DATA"),
    ("COMPLETE", None, "NO_VALUE"),
    ("LOW", _band("1", "2"), "NOT_ENOUGH_READINGS"),
    ("PARTIAL", _band("1", "2"), "COUNTED"),
    (None, None, "NO_DATA"),
])
def test_day_state_rule(grade, value, state):
    assert rr.day_state(grade, value) == state


def test_the_day_link_opens_the_one_day_depth_page_at_local_midnight():
    assert _body()["days"][0]["link"] == ("/sites/KOBO-001/performance/renewable"
                                          "?from=2026-10-31T21%3A00%3A00Z&to=2026-11-01T21%3A00%3A00Z")


def test_one_chain_read_over_the_named_days_with_known_at():
    port = Port()
    response = client(port).get(URL, params={**WEEK, "known_at": "2026-11-09T10:00:00Z"})
    assert response.status_code == 200
    assert response.json()["window"]["known_at"] == "2026-11-09T10:00:00.000000Z"
    assert port.calls == [(TENANT, SITE, D0, D0 + timedelta(6), datetime(2026, 11, 9, 10, tzinfo=timezone.utc))]


def test_thirty_one_days_is_allowed():
    response = client().get(URL, params={"from": "2026-10-01T00:00:00Z", "to": "2026-11-01T00:00:00Z"})
    assert response.status_code == 200 and len(response.json()["days"]) == 31


# ---- refusals ------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("params,status,code", [
    ({}, 422, "INVALID_WINDOW"),
    ({"from": "2026-11-01T00:00:00Z"}, 422, "INVALID_WINDOW"),
    ({"from": "2026-11-01T03:00:00Z", "to": "2026-11-08T00:00:00Z"}, 422, "INVALID_WINDOW"),
    ({"from": "2026-11-08T00:00:00Z", "to": "2026-11-01T00:00:00Z"}, 422, "INVALID_WINDOW"),
    ({"from": "2026-10-01T00:00:00Z", "to": "2026-11-02T00:00:00Z"}, 422, "INVALID_WINDOW"),
    ({"from": "2026-11-01", "to": "2026-11-08"}, 422, "INVALID_WINDOW"),
    ({**WEEK, "known_at": "yesterday"}, 422, "INVALID_KNOWN_AT"),
])
def test_window_refusals(params, status, code):
    response = client().get(URL, params=params)
    assert (response.status_code, response.json()["detail"]["code"]) == (status, code)


def test_window_rule_runs_before_known_at_and_refuses_in_range_words():
    """SR-8 review L2: a reversed window with a malformed `known_at` is INVALID_WINDOW (the window first, as the
    estate parser), and a malformed bound refuses with the range message, not the one-day one."""
    from assetops_backend.mini_depth_api import RANGE_REFUSALS

    reversed_ = client().get(URL, params={"from": "2026-11-08T00:00:00Z", "to": "2026-11-01T00:00:00Z",
                                          "known_at": "yesterday"})
    assert (reversed_.status_code, reversed_.json()["detail"]["code"]) == (422, "INVALID_WINDOW")
    malformed = client().get(URL, params={"from": "soon", "to": "2026-11-08T00:00:00Z"})
    assert malformed.json()["detail"] == {"code": "INVALID_WINDOW", "message": RANGE_REFUSALS["INVALID_WINDOW"][1]}


def test_admission_lookup_and_type_refusals():
    def code(response):
        return response.status_code, response.json()["detail"]["code"]

    assert code(client(access=lambda r, c: 401).get(URL, params=WEEK)) == (401, "UNAUTHENTICATED")
    assert code(client(access=lambda r, c: 403).get(URL, params=WEEK)) == (403, "SITE_SCOPE_FORBIDDEN")
    assert code(client().get("/api/sites/NOPE/renewable-range", params=WEEK)) == (404, "SITE_NOT_FOUND")
    assert code(client().get("/api/sites/COLD-001/renewable-range", params=WEEK)) == \
        (404, "RENEWABLE_RANGE_NOT_APPLICABLE")
    assert code(client(registry=Registry(fail=True)).get(URL, params=WEEK)) == \
        (503, "SITE_RENEWABLE_RANGE_UNAVAILABLE")
    assert code(client(reader=False).get(URL, params=WEEK)) == (503, "SITE_RENEWABLE_RANGE_UNAVAILABLE")
    assert code(client(Port(fail=True)).get(URL, params=WEEK)) == (503, "SITE_RENEWABLE_RANGE_UNAVAILABLE")


# ---- stored route and perf ----------------------------------------------------------------------------------------

def test_stored_route_key_and_watermark_site_and_body_equal_compose():
    store = Store()
    response = client(responses=store).get(URL, params={**WEEK, "known_at": "2026-11-09T10:00:00Z"})
    assert response.status_code == 200
    (req,) = store.requests
    assert req.route == RENEWABLE_RANGE_ROUTE and req.tenant_id == TENANT
    assert dict(req.request) == {"site": str(SITE), "from": "2026-11-01T00:00:00.000000Z",
                                 "to": "2026-11-08T00:00:00.000000Z", "known_at": "2026-11-09T10:00:00.000000Z"}
    assert req.sites == (SITE,) and req.watermark_sites == (SITE,)
    composed = client().get(URL, params={**WEEK, "known_at": "2026-11-09T10:00:00Z"}).json()
    assert response.json() == composed


def test_the_route_writes_a_perf_line(caplog):
    caplog.set_level("INFO")
    response = client().get(URL, params=WEEK)
    assert response.status_code == 200
    assert any(RENEWABLE_RANGE_ROUTE in r.getMessage() for r in caplog.records)


def test_a_low_day_with_a_value_is_never_counted_and_a_partial_eligible_day_counts_as_partial():
    """D-SR.47 Q4: LOW reads NOT_ENOUGH_READINGS even with a band; a PARTIAL-grade ELIGIBLE day is COUNTED with
    `partial: true`; per-day bounds stay the stored text, unrounded."""
    rows = [_row(D0, "LOW", _band("5", "9")), _row(D0 + timedelta(1), "PARTIAL", _band("1.234", "3.456")),
            _row(D0 + timedelta(2), "COMPLETE", _band("2", "4"))]
    body = _body(port=Port(rows))
    low, part, full = body["days"][:3]
    assert (low["state"], low["low_kw"], low["partial"]) == ("NOT_ENOUGH_READINGS", None, False)
    assert (part["state"], part["partial"], part["low_kw"], part["high_kw"]) == ("COUNTED", True, "1.234", "3.456")
    assert (full["state"], full["partial"]) == ("COUNTED", False)
    totals = body["totals"]
    assert (totals["days_counted"], totals["average_low_kw"], totals["average_high_kw"]) == (2, "1.62", "3.73")
