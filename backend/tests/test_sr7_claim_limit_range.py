"""SR-7b (rev 10 §10.3, D-SR.24/25): `site-claim-limit-range-1` body and route, no database. The body runs the
real `EstatePortfolioService._scope` and `claim_limit_read.reduce_day` over a stub `EvidenceMoneySnapshot`; the
dispatch days are stubbed at `coverage.dispatch_days`' seam (the AR-3 rows / D-ANY.10 compose are their own tests)."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.analytics import claim_limit_read as w1
from assetops_backend.claim_limit_api import RANGE_ROUTE, build_claim_limit_range_router
from assetops_backend.estate import claim_limit_range as clr
from assetops_backend.estate.portfolio import EstatePortfolioService
from assetops_backend.estate.scope import EstateStoreUnavailable, estate_request
from assetops_backend.sites.ports import SiteStoreUnavailable

T = UUID("00000000-0000-4000-8000-000000000001")
MG = UUID("00000000-0000-4000-8000-0000000000a1")
COLD = UUID("00000000-0000-4000-8000-0000000000c1")
KOBO = "KOBO-001"
READ_AT = datetime(2026, 11, 10, 8, tzinfo=timezone.utc)
LO, HI = datetime(2026, 11, 1, tzinfo=timezone.utc), datetime(2026, 11, 5, tzinfo=timezone.utc)
WINDOW = "from=2026-11-01T00:00:00Z&to=2026-11-05T00:00:00Z"
D = [date(2026, 11, 1 + i) for i in range(4)]
R = [UUID(f"00000000-0000-4000-8000-0000000001{i:02d}") for i in range(4)]
SITES = {KOBO: SimpleNamespace(tenant_id=T, id=MG, site_code=KOBO, name="Kobo", site_type="MINIGRID",
                               timezone="Africa/Nairobi"),
         "COLD-1": SimpleNamespace(tenant_id=T, id=COLD, site_code="COLD-1", name="Cold", site_type="COLDCHAIN",
                                   timezone=None)}


def _interval(rid, state, ceiling="CANDIDATE_AVOIDABLE", positive=True, statement="Up to 12 kW", reasons=()):
    return {"assessment_revision_id": str(rid), "state": state, "ceiling": ceiling, "current_positive_claim": positive,
            "statement": statement, "support": None, "supported_minutes": 60, "historical_ceiling": None,
            "currentness": "CURRENT", "accepted_evidence_ids": ["e1"], "reasons": list(reasons), "selected": True}


def _projection(day, rid, intervals, available=True, reasons=()):
    return {"day": day.isoformat(), "site_id": str(MG), "available": available, "currentness": "CURRENT",
            "intervals": intervals, "window_reasons": [], "window_assessment_revision_id": rid, "known_at": READ_AT,
            "reasons": list(reasons)}


#: Day 1 one positive Candidate ceiling; day 2 contradictory; day 3 no selected revision; day 4 unreconstructable.
PROJECTIONS = {
    D[0]: _projection(D[0], R[0], [_interval(R[0], "FULL")]),
    D[1]: _projection(D[1], R[1], [_interval(R[1], "CONTRADICTORY"),
                                   _interval(R[2], "FULL", reasons=[{"code": "MISSING_ROLE",
                                                                     "role": "GENERATOR", "text": "x"}])]),
    D[2]: _projection(D[2], None, []),
    D[3]: _projection(D[3], R[3], [], available=False, reasons=[
        {"code": "HISTORICAL_SELECTION_UNAVAILABLE", "text": "x"}, {"code": "LINEAGE_GONE", "text": "y"}]),
}
DAYS = [{"day": d, "available": d != D[2], "selection": None if d == D[2] else {"id": 1},
         "window_assessment_revision_id": None if d == D[2] else (R[0] if d == D[0] else R[1] if d == D[1] else R[3]),
         "window_start": datetime.combine(d, datetime.min.time(), timezone.utc),
         "window_end": datetime.combine(d, datetime.min.time(), timezone.utc) + timedelta(days=1)} for d in D]


class Snap:
    def __init__(self):
        self.read_at, self.basis_historical, self.noted, self.calls = READ_AT, False, [], []

    def imported_sites(self, t, to):
        return [{"site_id": MG, "site_code": KOBO, "site_name": "Kobo", "site_type": "MINIGRID"},
                {"site_id": COLD, "site_code": "COLD-1", "site_name": "Cold", "site_type": "COLDCHAIN"}]

    def note_page_days(self, t, s, lo, hi, k, days):
        self.noted.append((s, lo, hi, k, len(days)))

    def claim_limit_on(self, t, s, day, rid, k, mode):
        self.calls.append((day, rid, k, mode))
        return PROJECTIONS[day]


class Service:
    _scope = staticmethod(EstatePortfolioService._scope)

    def __init__(self, fail=None):
        self.snap, self.fail = Snap(), fail

    def read_snapshot(self, work):
        if self.fail is not None:
            raise self.fail
        return work(self.snap)


@pytest.fixture(autouse=True)
def _days(monkeypatch):
    monkeypatch.setattr(clr, "dispatch_days", lambda snap, t, s, lo, hi, k: list(DAYS))


def _body(service=None, known_at=None):
    service = service or Service()
    return clr.claim_limit_range_body(service, T, KOBO, estate_request("evidence", LO, HI, known_at), "Africa/Nairobi")


def test_each_day_row_is_reduce_day_of_the_one_day_projection() -> None:
    service = Service()
    body = _body(service)
    assert body["schema_version"] == "site-claim-limit-range-1"
    assert [r["state"] for r in body["days"]] == ["FULL", "CONTRADICTORY", "NO_SELECTION", "UNKNOWN"]
    for row, d in zip(body["days"], D):
        reduced = w1.reduce_day(PROJECTIONS[d])
        assert row["current_ceiling"] == reduced["current_ceiling"]
        assert row["ceiling_statement"] == reduced["ceiling_statement"]
        assert row["available"] == reduced["available"]
        assert row["gap_count"] == len(reduced["gaps"])
        if row["state"] != "NO_SELECTION":
            assert row["state"] == reduced["state"]
    first = body["days"][0]
    assert first["current_ceiling"] == "CANDIDATE_AVOIDABLE" and first["ceiling_statement"] == "Up to 12 kW"
    assert first["revision_id"] == str(R[0]) == first["window_assessment_revision_id"]
    assert first["link"] == f"/sites/KOBO-001/evidence?day=2026-11-01&revision={R[0]}"
    assert body["days"][1]["current_ceiling"] is None and body["days"][1]["gap_count"] == 1  # no invented ceiling
    third = body["days"][2]
    assert third["revision_id"] is None and third["link"] is None
    fourth = body["days"][3]
    assert [r["code"] for r in fourth["reasons"]] == ["HISTORICAL_SELECTION_UNAVAILABLE", "LINEAGE_GONE"]
    # The evidence-money pattern: the page's days are noted, and each day is read at the scope's cutoff, live.
    assert service.snap.noted == [(MG, LO, HI, READ_AT, 4)]
    assert [(c[1], c[2], c[3]) for c in service.snap.calls] == [(R[0], READ_AT, "live"), (R[1], READ_AT, "live"),
                                                                (None, READ_AT, "live"), (R[3], READ_AT, "live")]


def test_summary_and_window() -> None:
    body = _body()
    assert body["summary"] == {"days_with_positive_claim": 1, "days_indeterminate": 2, "days_without_selection": 1,
                               "days_requested": 4}
    assert body["window"] == {"from": "2026-11-01T00:00:00Z", "to": "2026-11-05T00:00:00Z",
                              "known_at": "2026-11-10T08:00:00Z", "basis": "CURRENT"}
    assert body["site"] == {"site_code": KOBO, "site_name": "Kobo", "timezone": "Africa/Nairobi"}


def test_historical_cutoff_reads_historical_mode() -> None:
    service = Service()
    k = datetime(2026, 11, 6, tzinfo=timezone.utc)
    body = _body(service, known_at=k)
    assert body["window"]["basis"] == "HISTORICAL" and {c[3] for c in service.snap.calls} == {"historical"}
    assert {c[2] for c in service.snap.calls} == {k}


def test_cold_site_is_not_applicable() -> None:
    with pytest.raises(clr.ClaimLimitRangeNotApplicable):
        clr.claim_limit_range_body(Service(), T, "COLD-1", estate_request("evidence", LO, HI))
    assert clr.claim_limit_range_body(Service(), T, "NOPE", estate_request("evidence", LO, HI)) is None


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


def _open(code, t, s):
    return True, "Cutover open"


def _client(estate, access=None, gate=_open, responses=None, registry=None):
    app = FastAPI()
    kwargs = {k: v for k, v in (("access", access), ("gate", gate)) if v is not None}
    app.include_router(build_claim_limit_range_router(estate, registry or Registry(), responses=responses, **kwargs))
    return TestClient(app)


def _get(client, code=KOBO, query=WINDOW):
    return client.get(f"/api/sites/{code}/claim-limit-range?{query}")


def test_route_serves_the_body_through_the_stored_route() -> None:
    responses = Responses()
    r = _get(_client(Service(), responses=responses))
    assert r.status_code == 200 and r.json()["summary"]["days_requested"] == 4
    (route,) = responses.routes
    assert route.route == RANGE_ROUTE and route.sites == (MG,) and route.watermark_sites == (MG,)
    # SR-7 review L3: the key's values, not only its names.
    assert {**route.request, "site": str(route.request["site"])} == {"site": str(MG), "from": LO, "to": HI, "known_at": None}


def test_known_at_takes_part_in_the_stored_route_key() -> None:
    """SR-7 review L3: a second request with `known_at` is a different stored key carrying that instant."""
    responses = Responses()
    assert _get(_client(Service(), responses=responses)).status_code == 200
    assert _get(_client(Service(), responses=responses), query=f"{WINDOW}&known_at=2026-11-05T06:00:00Z").status_code == 200
    live, pinned = responses.routes
    assert live.request["known_at"] is None
    assert pinned.request["known_at"] == datetime(2026, 11, 5, 6, tzinfo=timezone.utc)
    assert {k: v for k, v in live.request.items() if k != "known_at"} == {k: v for k, v in pinned.request.items() if k != "known_at"}


@pytest.mark.parametrize("query", ["from=2026-11-01T00:00:00Z", "from=2026-11-01T06:00:00Z&to=2026-11-05T00:00:00Z",
                                   "from=2026-11-01T00:00:00Z&to=2026-12-03T00:00:00Z"])
def test_bad_windows_are_422(query) -> None:
    r = _get(_client(Service()), query=query)
    assert r.status_code == 422 and r.json()["detail"]["code"] == "INVALID_WINDOW"


def test_refusals() -> None:
    assert _get(_client(Service()), code="COLD-1").json()["detail"]["code"] == "CLAIM_LIMIT_RANGE_NOT_APPLICABLE"
    nope = _get(_client(Service()), code="NOPE")
    assert nope.status_code == 404 and nope.json()["detail"]["code"] == "SITE_NOT_FOUND"  # SR-7 review L1
    store = _get(_client(Service(), registry=Registry(fail=True)))
    assert store.status_code == 503 and store.json()["detail"]["code"] == "SITE_STORE_UNAVAILABLE"
    assert _get(_client(Service(), access=lambda req, code: 401)).status_code == 401
    assert _get(_client(Service(), access=lambda req, code: 403)).status_code == 403
    none = _get(_client(None))
    assert none.status_code == 503 and none.json()["detail"]["code"] == "SITE_CLAIM_LIMIT_RANGE_UNAVAILABLE"
    down = _get(_client(Service(fail=EstateStoreUnavailable("x"))))
    assert down.status_code == 503 and down.json()["detail"]["code"] == "SITE_CLAIM_LIMIT_RANGE_UNAVAILABLE"
    closed = _get(_client(Service(), gate=lambda code, t, s: (False, "Cutover closed")))
    assert closed.status_code == 409 and closed.json()["detail"]["claim_limit"] is None
    assert closed.json()["detail"]["code"] == "PERFORMANCE_CUTOVER_CLOSED"  # SR-7 review L1


def test_one_perf_line_per_request(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="assetops.perf"):
        assert _get(_client(Service())).status_code == 200
    lines = [json.loads(r.getMessage()) for r in caplog.records if r.name == "assetops.perf"]
    assert [x["route"] for x in lines] == [RANGE_ROUTE]
