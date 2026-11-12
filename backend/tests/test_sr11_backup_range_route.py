"""SR-11 (rev 10b.3 tests, D-SR.31/32/45): `GET /api/sites/{code}/backup-range` on stubs (no database).

The SR-10b generic `build_day_range_router("backup", ...)` over stored `mini_depth.backup_day` rows: per day the
backup start sequences de-duplicated by `chain_id` (latest hour wins), the backup day states, the start-success null
rule, the slowest recovery, and never an outage count. Also `window_days` (a 7-day Nairobi window is 7 rows), the
absent and pending rows (STILL_PROCESSING), refusals (422/404/401/403/503), the stored-route key and watermark Site,
the perf line, and the `main.py` wiring. The chain-grade port, Site registry and response store stubs are SR-10b's."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.chain import read as cr
from assetops_backend.chain.period_read import PeriodRead, PeriodReadResult
from assetops_backend.mini_depth import period_rows as pr
from assetops_backend.mini_depth.inputs import local_hour
from assetops_backend.mini_depth.read import _Head, _Hour
from assetops_backend.mini_depth_api import DAY_RANGE_ROUTES, build_day_range_router
from assetops_backend.sites.ports import SiteStoreUnavailable
from test_sr10_fuel_range_route import D0, SITE, TENANT, TZ, NoDataPort, Port, Registry, Store

URL = "/api/sites/KOBO-001/backup-range"
WEEK = {"from": "2026-11-01T00:00:00Z", "to": "2026-11-08T00:00:00Z"}
KIND = "mini_depth.backup_day"
ROUTE = DAY_RANGE_ROUTES["backup"]


def _chain(cid: str, result: str, seconds: int | None, start: str, target: int = 120) -> dict:
    return {"chain_id": cid, "outage_start": start, "steps": [], "service_outcome": "RESTORED", "result": result,
            "critical_recovery": None if seconds is None else {"seconds": seconds, "target_seconds": target},
            "coverage": None, "evidence_ids": []}


def _hour(day: date, h: int, chains=(), successes: int | None = None, status: str = "SUPPORTED",
          head: bool = True) -> dict:
    w = local_hour(day, h, TZ)
    body = {"status": status, "limitations": [{"code": "BACKUP_BUS_PARTIAL"}] if status == "LIMITED" else [],
            "cards": {"outage_count": None, "start_success_count": successes, "last_witnessed_test_at": None,
                      "critical_recovery": None},
            "rows": list(chains)}
    head_ = _Head(1, uuid4(), w.start, "sha", body, ()) if head else None
    return pr.hour_json(_Hour(day, w, head_, "SETTLED" if head else "NONE", "CURRENT" if head else "UNKNOWN",
                              None, ()))


def _row(day: date, special: dict[int, dict] | None = None, missing: tuple[int, ...] = ()) -> PeriodRead:
    special = special or {}
    hours = [special.get(h) or _hour(day, h, head=h not in missing) for h in range(24)]
    return PeriodRead(SimpleNamespace(site_id=SITE, local_day=day, kind=KIND, body={"hours": hours}))


def _d(i: int) -> date:
    return D0 + timedelta(i)


#: D0 c1 INCOMPLETE at 02:00 then PASS at 03:00 (latest hour wins) + c2 PASS (c1 and c2 tie on 90 s: the earliest
#: start wins, D-SR.51.2) + cX PASS starting 23:50 local, which D1's 00:00 hour reports again (crosses midnight);
#: D1 c3 FAIL, c6 PASS with no recovery (skipped), a LIMITED hour; D2 c4 INCOMPLETE with one hour missing;
#: D3 absent; D4 pending at k; D5 no sequence; D6 not expected (grade).
CROSS = "2026-11-01T20:50:00Z"  # 23:50 Nairobi on D0
ROWS = [
    _row(_d(0), {2: _hour(_d(0), 2, [_chain("c1", "INCOMPLETE", None, "2026-10-31T23:10:00Z")]),
                 3: _hour(_d(0), 3, [_chain("c1", "PASS", 90, "2026-10-31T23:10:00Z", 120),
                                     _chain("c2", "PASS", 90, "2026-11-01T00:30:00Z", 150)], successes=1),
                 23: _hour(_d(0), 23, [_chain("cX", "PASS", 40, CROSS)])}),
    _row(_d(1), {0: _hour(_d(1), 0, [_chain("cX", "PASS", 40, CROSS)]),
                 5: _hour(_d(1), 5, [_chain("c3", "FAIL", 600, "2026-11-02T02:00:00Z"),
                                     _chain("c6", "PASS", None, "2026-11-02T02:20:00Z")], successes=0),
                 6: _hour(_d(1), 6, status="LIMITED")}),
    _row(_d(2), {8: _hour(_d(2), 8, [_chain("c4", "INCOMPLETE", None, "2026-11-03T05:00:00Z")])}, missing=(23,)),
    _row(_d(4), {9: _hour(_d(4), 9, [_chain("c5", "PASS", 30, "2026-11-05T06:00:00Z")], successes=1)}),
    _row(_d(5)),
    _row(_d(6)),
]


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
        return PeriodReadResult(rows, {(SITE, _d(4), KIND): ("dirty",)}, 2, absent)


def client(periods=None, port=None, *, chain=True, access=lambda r, c: None, registry=None, responses=None):
    periods = Periods() if periods is None else periods
    reader = cr.ChainReader(port or Port()) if chain else None
    app = FastAPI()
    app.include_router(build_day_range_router("backup", lambda: periods, lambda: reader, registry or Registry(),
                                              access=access, responses=responses,
                                              now=lambda: datetime(2026, 11, 12, tzinfo=timezone.utc)))
    return TestClient(app)


def _body(**kw):
    response = client(**kw).get(URL, params=WEEK)
    assert response.status_code == 200, response.text
    return response.json()


def _keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in _keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in _keys(v)}
    return set()


def test_each_day_reads_its_stored_backup_day_row_and_state():
    body = _body()
    assert body["schema_version"] == "site-backup-range-1"
    assert body["site"] == {"site_code": "KOBO-001", "site_name": "Kobo", "timezone": TZ}
    days = body["days"]
    assert [d["local_day"] for d in days] == [_d(i).isoformat() for i in range(7)]  # D-SR.45: 7 rows
    assert [(d["state"], d["partial"]) for d in days] == [
        ("SEQUENCES_PASSED", False), ("SEQUENCE_FAILED", True), ("SEQUENCE_INCOMPLETE", True),
        ("STILL_PROCESSING", False), ("STILL_PROCESSING", False), ("NO_SEQUENCE", False), ("NOT_EXPECTED", False)]
    assert days[0]["hour_link"] == ("/sites/KOBO-001/performance/backup"
                                    "?from=2026-11-01T09%3A00%3A00Z&to=2026-11-01T10%3A00%3A00Z")
    assert (days[2]["hours_assessed"], days[2]["hours_missing"]) == (23, 1)
    assert days[1]["limitations"] == ["BACKUP_BUS_PARTIAL"] and days[1]["status_counts"]["LIMITED"] == 1
    assert days[4]["hours_pending"] == 24 and days[4]["sequences"] == []  # a pending hour's head is not summed
    assert [d["stored"] for d in days] == [True, True, True, False, True, True, True]


def test_no_reading_days_read_no_data_not_no_sequence_and_are_not_counted():
    """D-SR.70/72: D3 (absent row) and D5 (stored row, was NO_SEQUENCE) have no readings: NO_DATA, nulls, uncounted."""
    body = _body(port=NoDataPort())
    days = body["days"]
    assert [d["state"] for d in days][3:] == ["NO_DATA", "STILL_PROCESSING", "NO_DATA", "NOT_EXPECTED"]
    assert (days[3]["stored"], days[5]["stored"]) == (False, True)
    for d in (days[3], days[5]):
        assert d["partial"] is False and d["sequences"] is None and d["sequence_counts"] is None
        assert d["hours_assessed"] is None and d["hour_link"]
    assert "NO_DATA" not in {s for s in ("SEQUENCES_PASSED", "SEQUENCE_FAILED", "SEQUENCE_INCOMPLETE", "NO_SEQUENCE")}


def test_an_absent_day_is_unknown_not_zero():
    """D-SR.51.3 / D-SR.58 Q1: the absent row's counts, figures and `sequences` are null; stored rows never carry
    null counts, and a stored day without a sequence lists `[]`."""
    days = _body()["days"]
    absent = days[3]
    for key in ("hours_expected", "hours_assessed", "hours_pending", "hours_missing", "status_counts",
                "sequence_counts", "start_success_count", "slowest_recovery", "sequences"):
        assert absent[key] is None, key
    assert days[5]["stored"] is True and days[5]["sequences"] == []  # D-SR.58 Q1: a stored day with none has []
    for d in days[:3] + days[4:]:
        assert None not in (d["hours_expected"], d["hours_assessed"], d["status_counts"], d["sequence_counts"])


def test_sequences_are_deduplicated_by_chain_latest_hour_wins():
    d0 = _body()["days"][0]
    assert [(s["chain_id"], s["result"]) for s in d0["sequences"]] == [("c1", "PASS"), ("c2", "PASS"),
                                                                        ("cX", "PASS")]
    assert set(d0["sequences"][0]) == {"chain_id", "outage_start", "result", "service_outcome", "critical_recovery"}
    assert d0["sequence_counts"] == {"PASS": 3, "FAIL": 0, "INCOMPLETE": 0}


def test_slowest_recovery_skips_nulls_and_ties_go_to_the_earliest_start():
    days = _body()["days"]
    assert days[0]["slowest_recovery"] == {"seconds": 90, "target_seconds": 120}  # c1 (23:10) over c2 (00:30)
    assert days[1]["slowest_recovery"] == {"seconds": 600, "target_seconds": 120}  # c6's null is skipped


def test_start_successes_sum_non_null_hours_and_are_null_when_all_are():
    days = _body()["days"]
    assert [d["start_success_count"] for d in days][:3] == [1, 0, None]
    assert [d["start_success_count"] for d in days][4:] == [None, None, None]
    assert days[2]["slowest_recovery"] is None  # an INCOMPLETE sequence has no recovery


def test_never_an_outage_count():
    body = _body()
    keys = _keys(body)
    assert not any("outage" in k for k in keys - {"outage_start"})
    assert "outage_start" in keys  # the sequence's start time is shown; the set above is not vacuous


def test_totals_sum_counted_days_only():
    assert _body()["totals"] == {"days_counted": 4, "days_requested": 7, "partial": True,
                                 "sequence_counts": {"PASS": 4, "FAIL": 1, "INCOMPLETE": 1},
                                 "start_success_count": 1}


def test_a_sequence_crossing_local_midnight_counts_once_in_the_totals():
    """D-SR.51.4: cX is reported by D0's 23:00 hour and D1's 00:00 hour; each day lists it, the window counts it
    once (de-duplicated by chain_id, latest day wins). Non-vacuous: the per-day PASS counts sum to 5."""
    body = _body()
    days = body["days"]
    assert "cX" in [s["chain_id"] for s in days[0]["sequences"]]
    assert "cX" in [s["chain_id"] for s in days[1]["sequences"]]
    assert sum(d["sequence_counts"]["PASS"] for d in days if d["state"] in (
        "SEQUENCES_PASSED", "SEQUENCE_FAILED", "SEQUENCE_INCOMPLETE", "NO_SEQUENCE")) == 5
    assert body["totals"]["sequence_counts"]["PASS"] == 4


def test_one_period_read_and_one_chain_read_over_window_days_with_known_at():
    periods, port = Periods(), Port()
    known = datetime(2026, 11, 9, 10, tzinfo=timezone.utc)
    response = client(periods, port).get(URL, params={**WEEK, "known_at": "2026-11-09T10:00:00Z"})
    assert response.status_code == 200
    assert periods.calls == [(TENANT, [SITE], [KIND], D0, _d(6), known)]
    assert port.calls == [(TENANT, SITE, D0, _d(6), known)]


@pytest.mark.parametrize("params,code", [
    ({}, "INVALID_WINDOW"),
    ({"from": "2026-11-01T03:00:00Z", "to": "2026-11-08T00:00:00Z"}, "INVALID_WINDOW"),
    ({"from": "2026-10-01T00:00:00Z", "to": "2026-11-02T00:00:00Z"}, "INVALID_WINDOW"),
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
    assert code(client().get("/api/sites/NOPE/backup-range", params=WEEK)) == (404, "SITE_NOT_FOUND")
    for other in ("COLD-001", "EV-001"):
        assert code(client().get(f"/api/sites/{other}/backup-range", params=WEEK)) == \
            (404, "BACKUP_RANGE_NOT_APPLICABLE")
    for kw in ({"registry": Registry(fail=True)}, {"chain": False}, {"periods": Periods(fail=True)},
               {"port": Port(fail=True)}):
        assert code(client(**kw).get(URL, params=WEEK)) == (503, "SITE_BACKUP_RANGE_UNAVAILABLE"), kw


def test_stored_route_key_and_watermark_site_and_body_equal_compose():
    store = Store()
    params = {**WEEK, "known_at": "2026-11-09T10:00:00Z"}
    response = client(responses=store).get(URL, params=params)
    assert response.status_code == 200
    (req,) = store.requests
    assert req.route == ROUTE == "/api/sites/{site_code}/backup-range" and req.tenant_id == TENANT
    assert dict(req.request) == {"site": str(SITE), "from": "2026-11-01T00:00:00.000000Z",
                                 "to": "2026-11-08T00:00:00.000000Z", "known_at": "2026-11-09T10:00:00.000000Z"}
    assert req.sites == (SITE,) and req.watermark_sites == (SITE,)
    assert response.json() == client().get(URL, params=params).json()


def test_the_route_writes_a_perf_line(caplog):
    caplog.set_level("INFO")
    assert client().get(URL, params=WEEK).status_code == 200
    assert any(ROUTE in r.getMessage() for r in caplog.records)


def test_main_wires_both_day_range_routes():
    from assetops_backend.main import app

    paths = set(app.openapi()["paths"])
    assert {DAY_RANGE_ROUTES["fuel"], DAY_RANGE_ROUTES["backup"]} <= paths


def test_chain_ids_are_unique_across_one_stored_days_hours():
    """D-SR.60: a chain belongs to the one hour holding its LOSS (`rules.assess_backup_hour` bounds it at the hour
    end), so summing hour-card start successes over a day or window never double counts. Outages here span an hour
    boundary and local midnight; the 24 projected hours of the day hold each chain_id once. Non-vacuous: 3 chains."""
    from decimal import Decimal

    from assetops_backend.mini_depth import projection, rules

    day, src = _d(0), uuid4()
    midnight = local_hour(day, 0, TZ).start

    def supply(minutes: float, state: str) -> rules.Observation:
        return rules.Observation(uuid4(), src, "site_supply_state", midnight + timedelta(minutes=minutes), "GOOD",
                                 state, None, None, None)

    series = [supply(-60, "ENERGIZED"),
              supply(11 * 60 + 50, "LOST"), supply(13 * 60 + 20, "ENERGIZED"),  # 11:50-13:20: spans two hours
              supply(15 * 60 + 10, "LOST"), supply(15 * 60 + 20, "ENERGIZED"),  # inside one hour
              supply(23 * 60 + 40, "LOST"), supply(24 * 60 + 30, "ENERGIZED")]  # 23:40-00:30: crosses midnight
    ids = []
    for h in range(24):
        hour = rules.assess_backup_hour(local_hour(day, h, TZ), series, [], Decimal("5"), critical_asset_id=None)
        ids += [str(r["chain_id"]) for r in projection._backup(hour)["rows"]]
    nxt = rules.assess_backup_hour(local_hour(day + timedelta(1), 0, TZ), series, [], Decimal("5"),
                                   critical_asset_id=None)
    assert len(ids) == 3 and len(set(ids)) == 3
    assert not set(str(r["chain_id"]) for r in projection._backup(nxt)["rows"]) & set(ids)
