"""SR-7a (rev 10 §10.3, D-SR.26): `site-service-range-1` body and route, no database. The chain read is a stub
`ChainReader` whose `DayFacts` are built by the real `ChainRequest.day` over stub snapshot rows, so grades, values
and rows come through the same memoised read the board uses."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend import read_scope
from assetops_backend.chain.ports import SnapshotRow
from assetops_backend.chain.read import ChainRequest
from assetops_backend.mini_depth import service_range as sr
from assetops_backend.mini_depth_api import SERVICE_RANGE_ROUTE, build_service_range_router
from assetops_backend.sites.ports import SiteStoreUnavailable

T = UUID("00000000-0000-4000-8000-000000000001")
MG = UUID("00000000-0000-4000-8000-0000000000a1")
COLD = UUID("00000000-0000-4000-8000-0000000000c1")
KOBO = "KOBO-001"
TZ = "Africa/Nairobi"
D = [date(2026, 11, 1 + i) for i in range(7)]
WINDOW = "from=2026-11-01T00:00:00Z&to=2026-11-08T00:00:00Z"
SITES = {KOBO: SimpleNamespace(tenant_id=T, id=MG, site_code=KOBO, name="Kobo", site_type="MINIGRID", timezone=TZ),
         "COLD-1": SimpleNamespace(tenant_id=T, id=COLD, site_code="COLD-1", name="Cold", site_type="COLDCHAIN",
                                   timezone=None)}


def _row(day: date, grade: str, value: dict | None, covered: int = 36000, required: int = 43200,
         measure: str = "critical_served") -> SnapshotRow:
    return SnapshotRow(T, MG, day, "SITE", "SITE", measure, "MEASURED", 1, grade != "NOT_EXPECTED", required, covered,
                       "83.3", grade, value, None, "p1", "c1", 1, "fp")


def _value(served: str, demand: str, unserved: str) -> dict:
    return {"served_kwh": served, "demand_kwh": demand, "unserved_kwh": unserved}


#: Day 1 shortfall, day 2 fully served, day 3 analysed but no value, day 4 NO_DATA, day 5 PENDING, day 6 NOT_EXPECTED,
#: day 7 no snapshot row at all (the absent-row test, D-SR.16: the chain's missing-row rule reads NO_DATA).
ROWS = [_row(D[0], "COMPLETE", _value("40.5", "42.0", "1.5")),
        _row(D[1], "PARTIAL", _value("20", "20", "0"), covered=21600),
        _row(D[2], "COMPLETE", None),
        _row(D[3], "NO_DATA", None, covered=0),
        _row(D[4], "PENDING", None),
        _row(D[5], "NOT_EXPECTED", None, covered=0, required=0),
        _row(D[6], "COMPLETE", {"x": 1}, measure="productive_kwh")]


class Snapshots:
    def __init__(self, rows):
        self.rows, self.calls = rows, []

    def __call__(self, tenant_id, site_id, lo, hi, measures, k):
        self.calls.append((lo, hi, k))
        return [r for r in self.rows if lo <= r.local_day <= hi and r.measure in measures]


class Reader:
    def __init__(self, rows=ROWS, fail=None):
        self.ports = SimpleNamespace(snapshots=Snapshots(rows))
        self.fail = fail

    def request(self, tenant_id, k):
        if self.fail is not None:
            raise self.fail
        return ChainRequest(self, tenant_id, k)


def _facts(rows=ROWS):
    with read_scope.scope("test"):
        return Reader(rows).request(T, None).day(MG, "MINIGRID", D)


def _body(rows=ROWS, known_at=None):
    lo, hi = datetime(2026, 11, 1, tzinfo=timezone.utc), datetime(2026, 11, 8, tzinfo=timezone.utc)
    return sr.service_range_body({"site_code": KOBO, "site_name": "Kobo", "timezone": TZ}, _facts(rows), D,
                                 lo=lo, hi=hi, known_at=known_at)


def test_day_states_values_and_hours() -> None:
    body = _body()
    assert body["schema_version"] == "site-service-range-1"
    assert [d["state"] for d in body["days"]] == [
        "SHORTFALL", "SERVED_ALL", "NO_VALUE", "NO_READINGS", "STILL_PROCESSING", "NOT_EXPECTED", "NO_READINGS"]
    first, second, third = body["days"][:3]
    assert (first["served_kwh"], first["unserved_kwh"], first["demand_kwh"]) == ("40.5", "1.5", "42.0")
    assert (first["covered_hours"], first["operating_hours"], first["grade"]) == (10.0, 12.0, "COMPLETE")
    assert second["covered_hours"] == 6.0 and second["grade"] == "PARTIAL"
    assert third["served_kwh"] is None and third["covered_hours"] == 10.0
    absent = body["days"][6]
    assert absent["grade"] is None and absent["covered_hours"] is None and absent["served_kwh"] is None


def test_totals_sum_counted_days_only_and_name_the_partial() -> None:
    totals = _body()["totals"]
    assert totals == {"served_kwh": "60.5", "unserved_kwh": "1.5", "demand_kwh": "62.0",
                      "days_counted": 2, "days_requested": 7}
    empty = _body(rows=[])["totals"]
    assert empty["days_counted"] == 0 and empty["served_kwh"] is None and empty["days_requested"] == 7


def test_low_grade_is_not_enough_readings_and_never_counted() -> None:
    body = _body(rows=[_row(D[0], "LOW", _value("1", "9", "8"))])
    assert body["days"][0]["state"] == "NOT_ENOUGH_READINGS" and body["days"][0]["served_kwh"] is None
    assert body["totals"]["days_counted"] == 0


def test_hour_link_is_the_local_noon_hour() -> None:
    link = _body()["days"][0]["hour_link"]
    assert link == ("/sites/KOBO-001/performance/service?from=2026-11-01T09%3A00%3A00Z&to=2026-11-01T10%3A00%3A00Z")


def test_window_and_basis() -> None:
    k = datetime(2026, 11, 9, 6, tzinfo=timezone.utc)
    assert _body()["window"] == {"from": "2026-11-01T00:00:00Z", "to": "2026-11-08T00:00:00Z", "known_at": None,
                                 "basis": "CURRENT"}
    assert _body(known_at=k)["window"]["basis"] == "HISTORICAL"


# --- route --------------------------------------------------------------------------------------------------------

class Registry:
    def __init__(self, fail=False):
        self.fail = fail

    def tenant(self):
        if self.fail:
            raise SiteStoreUnavailable("down")
        return SimpleNamespace(id=T)

    def imported(self, code):
        return SITES.get(code)


class Responses:
    def __init__(self):
        self.routes = []

    def serve(self, route, compose):
        self.routes.append(route)
        return compose()[route.route]


def _client(reader=None, access=None, registry=None, responses=None, unavailable=()):
    app = FastAPI()
    kwargs = {} if access is None else {"access": access}
    app.include_router(build_service_range_router(lambda: reader, registry or Registry(), unavailable=unavailable,
                                                  responses=responses, **kwargs))
    return TestClient(app)


def _get(client, code=KOBO, query=WINDOW):
    return client.get(f"/api/sites/{code}/service-range?{query}")


def test_route_serves_the_body_through_the_stored_route() -> None:
    responses = Responses()
    reader = Reader()
    r = _get(_client(reader, responses=responses))
    assert r.status_code == 200
    assert [d["state"] for d in r.json()["days"]][:2] == ["SHORTFALL", "SERVED_ALL"]
    assert r.json()["site"] == {"site_code": KOBO, "site_name": "Kobo", "timezone": TZ}
    (route,) = responses.routes
    assert route.route == SERVICE_RANGE_ROUTE and route.tenant_id == T
    assert route.sites == (MG,) and route.watermark_sites == (MG,)
    assert set(route.request) == {"site", "from", "to", "known_at"}
    assert len(reader.ports.snapshots.calls) == 1  # one chain day read for the whole range


@pytest.mark.parametrize("query", [
    "from=2026-11-01T00:00:00Z",
    "from=2026-11-01T06:00:00Z&to=2026-11-08T00:00:00Z",
    "from=2026-11-01T00:00:00Z&to=2026-12-03T00:00:00Z",
    "from=2026-11-08T00:00:00Z&to=2026-11-01T00:00:00Z",
    "from=2026-11-01&to=2026-11-08",
])
def test_bad_windows_are_422(query) -> None:
    r = _get(_client(Reader()), query=query)
    assert r.status_code == 422 and r.json()["detail"]["code"] == "INVALID_WINDOW"


def test_refusals() -> None:
    assert _get(_client(Reader()), code="COLD-1").json()["detail"]["code"] == "SERVICE_RANGE_NOT_APPLICABLE"
    assert _get(_client(Reader()), code="NOPE").status_code == 404
    assert _get(_client(Reader(), access=lambda req, code: 401)).status_code == 401
    assert _get(_client(Reader(), access=lambda req, code: 403)).status_code == 403
    assert _get(_client(Reader(), registry=Registry(fail=True))).status_code == 503
    none = _get(_client(None))
    assert none.status_code == 503 and none.json()["detail"]["code"] == "SITE_SERVICE_RANGE_UNAVAILABLE"
    down = _get(_client(Reader(fail=SiteStoreUnavailable("x"))))
    assert down.status_code == 503 and down.json()["detail"]["code"] == "SITE_SERVICE_RANGE_UNAVAILABLE"


def test_one_perf_line_per_request(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="assetops.perf"):
        assert _get(_client(Reader())).status_code == 200
    lines = [json.loads(r.getMessage()) for r in caplog.records if r.name == "assetops.perf"]
    assert [x["route"] for x in lines] == [SERVICE_RANGE_ROUTE]
