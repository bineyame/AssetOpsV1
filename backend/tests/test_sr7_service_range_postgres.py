"""SR-7a (rev 10 §10.3, D-SR.26): `site-service-range-1` over stored `chain.day` snapshots, through the real Postgres
chain reader and the real `ResponseStore`.

One mini-grid Site (`test_ch9_service_v2_postgres`'s `_installed`). Day 1 is derived end to end: 24 `mini-service/2`
hour heads -> `CriticalServed` (the ch9 shape: 144 served / 156.0 demand / 12.0 unserved kWh over 24 covered hours)
-> a `critical_served` snapshot row. The other days are stored rows of each kind. Pins:
- a counted day equals the stored `critical_served` value, and the hours come from the row's seconds (D-SR.26);
- a NO_VALUE day (analysed, no value) and a LOW day (NOT_ENOUGH_READINGS, value never shown, not counted);
- the totals sum the counted days only;
- stored (`ResponseStore`, first serve and the stored hit) and live (no store) bodies are equal.
Depends on the packet's Q-J1 (UTC-midnight window -> UTC dates read as the Site's local day) and Q-J2 (LOW never
counted). Needs ASSETOPS_TEST_DATABASE_URL (`assetops_sr7_test`).
"""

from __future__ import annotations

import dataclasses
import hashlib
import os
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_w203_cold_migration_postgres import _replica
    from test_w402_migration_postgres import revision
    from test_w402_mini_stage_postgres import _installed, _rows

    from assetops_backend.chain.adapters.postgres_chain_inputs import PostgresChainInputs
    from assetops_backend.chain.adapters.postgres_response_store import PostgresResponseRows
    from assetops_backend.chain.adapters.postgres_snapshot_store import PostgresSnapshotStore
    from assetops_backend.chain.composition import build_chain_reader
    from assetops_backend.chain.grading import COMPLETE, classify_day, covered_seconds
    from assetops_backend.chain.measure_impls import CriticalServed
    from assetops_backend.chain.measures import MEASURES
    from assetops_backend.chain.ports import DayCtx, SnapshotRow
    from assetops_backend.chain.response_store import ResponseStore
    from assetops_backend.mini_depth.store import PostgresMiniDepthStore
    from assetops_backend.mini_depth_api import SERVICE_RANGE_ROUTE, build_service_range_router
    from assetops_backend.mini_depth.service_range import hour_link

UTC = timezone.utc
TZ = "Africa/Nairobi"
DAYS = [date(2026, 10, 20 + i) for i in range(6)]
WINDOW = "from=2026-10-20T00:00:00Z&to=2026-10-26T00:00:00Z"
SERVED_DAY = {"served_kwh": "144", "demand_kwh": "156.0", "unserved_kwh": "12.0"}


def _crit(code: str, delivered, unserved) -> dict:
    return {"role": "CRITICAL", "asset_id": code, "asset_code": code, "load_label": code, "delivered_kw": delivered,
            "requested_evidence_state": "ACCEPTED", "assessment": "SUPPORTED", "unserved_kwh": unserved,
            "coverage": {"required_seconds": 3600, "observed_seconds": 3600, "source_count": 1, "gaps": []},
            "evidence_ids": []}


def _unclassified() -> dict:
    return {"role": "UNCLASSIFIED", "asset_id": "load-mill", "asset_code": "load-mill", "load_label": "load-mill",
            "delivered_kw": 16.333333333333332, "requested_evidence_state": "MISSING", "assessment": "UNKNOWN",
            "unserved_kwh": None, "coverage": {"required_seconds": 3600, "observed_seconds": 3600,
                                                "source_count": 1, "gaps": []}, "evidence_ids": []}


@pytest.fixture()
def world(store, engine):  # noqa: F811
    tenant_id, site_id = _installed(store, engine)
    ctx = type("Ctx", (), {"t": tenant_id, "s": site_id})
    mini = PostgresMiniDepthStore(engine)
    lo = datetime(2026, 10, 20, tzinfo=ZoneInfo(TZ)).astimezone(UTC)
    result = {"status": "LIMITED", "cards": {}, "critical_delivered_coverage": None, "rows": [
        _crit("load-clinic", 6, 0.5), _unclassified()], "limitations": [], "coverage": {"gaps": []}}
    for n in range(24):
        a = lo + timedelta(hours=n)
        mini.append_selection(dataclasses.replace(
            revision(ctx, lo=a, hi=a + timedelta(hours=1), digest=f"d{n}", result=result),
            model_version="mini-service/2"), job_id=None, backfill=True)
    _replica(engine, f"DELETE FROM recompute_job WHERE site_id = '{site_id}' AND domain LIKE 'mini\\_%'")

    dctx = DayCtx(tenant_id, site_id, "MG", "MINIGRID", TZ, DAYS[0], lo, lo + timedelta(days=1), None)
    got = CriticalServed(PostgresChainInputs(engine=engine)).inputs(dctx, "SITE")
    covered = covered_seconds(got.covered, dctx.period_start_utc, dctx.period_end_utc)
    spec = MEASURES["critical_served"]
    assert classify_day(True, 24 * 3600, covered, got.pending, None, spec.threshold) == COMPLETE
    derived = CriticalServed(None).measure(dctx, "SITE", got)
    assert derived == SERVED_DAY

    def snap(day, grade, value, covered_s, required_s=86400):
        return SnapshotRow(tenant_id, site_id, day, "SITE", "SITE", "critical_served", "MEASURED", 1,
                           grade != "NOT_EXPECTED", required_s, covered_s, "0", grade, value, None, "p1", "c1", 1,
                           hashlib.sha256(str(day).encode()).hexdigest())
    snaps = PostgresSnapshotStore(engine=engine)
    stored = {DAYS[0]: snap(DAYS[0], COMPLETE, derived, covered),
              DAYS[1]: snap(DAYS[1], "PARTIAL", {"served_kwh": "20", "demand_kwh": "20", "unserved_kwh": "0"},
                            5 * 3600 + 1800, 8 * 3600),
              DAYS[2]: snap(DAYS[2], "COMPLETE", None, 24 * 3600),
              DAYS[3]: snap(DAYS[3], "LOW", {"served_kwh": "9", "demand_kwh": "9", "unserved_kwh": "0"}, 3600),
              DAYS[4]: snap(DAYS[4], "NO_DATA", None, 0)}  # DAYS[5] has no row at all
    for row in stored.values():
        snaps.append(row)

    with engine.connect() as c:
        r = c.execute(text("SELECT site_code, name FROM site WHERE id = :s"), {"s": site_id}).one()
    ref = SimpleNamespace(tenant_id=tenant_id, id=site_id, site_code=r.site_code, name=r.name, site_type="MINIGRID",
                          timezone=TZ)

    class Registry:
        def tenant(self):
            return SimpleNamespace(id=tenant_id)

        def imported(self, code):
            return ref if code == ref.site_code else None

    reader, dispose = build_chain_reader(URL)

    def client(responses):
        app = FastAPI()
        app.include_router(build_service_range_router(lambda: reader, Registry(), access=lambda request, code: None,
                                                      responses=responses))
        return TestClient(app)
    try:
        yield SimpleNamespace(code=ref.site_code, derived=derived, covered=covered, client=client,
                              responses=lambda: ResponseStore(PostgresResponseRows(engine=engine), lambda: "v1"))
    finally:
        dispose()


def _get(client, code, query=WINDOW):
    response = client.get(f"/api/sites/{code}/service-range?{query}")
    assert response.status_code == 200, response.text
    return response.json()


def test_counted_day_hours_no_value_low_and_totals(world) -> None:
    out = _get(world.client(None), world.code)
    assert out["schema_version"] == "site-service-range-1"
    assert [d["local_day"] for d in out["days"]] == [d.isoformat() for d in DAYS]
    served, partial, novalue, low, nodata, absent = out["days"]
    # a counted day equals the stored critical_served value; its hours come from the row seconds
    assert (served["state"], served["served_kwh"], served["unserved_kwh"], served["demand_kwh"]) == (
        "SHORTFALL", "144", "12.0", "156.0")
    assert (served["covered_hours"], served["operating_hours"]) == (world.covered / 3600, 24.0) == (24.0, 24.0)
    assert (partial["state"], partial["covered_hours"], partial["operating_hours"]) == ("SERVED_ALL", 5.5, 8.0)
    assert (served["partial"], partial["partial"], novalue["partial"], low["partial"]) == (False, True, False, False)
    assert served["hour_link"] == hour_link(world.code, DAYS[0], TZ)
    # NO_VALUE: analysed, no figure
    assert (novalue["state"], novalue["served_kwh"], novalue["covered_hours"]) == ("NO_VALUE", None, 24.0)
    # LOW: named, its stored value is not shown and not counted
    assert (low["state"], low["served_kwh"], low["unserved_kwh"], low["covered_hours"]) == (
        "NOT_ENOUGH_READINGS", None, None, 1.0)
    assert nodata["state"] == "NO_READINGS" and absent["state"] == "NO_READINGS"
    assert absent["covered_hours"] is None and absent["operating_hours"] is None
    # totals: the two counted days only (144 + 20, 12.0 + 0, 156.0 + 20)
    assert out["totals"] == {"served_kwh": "164", "unserved_kwh": "12.0", "demand_kwh": "176.0",
                             "days_counted": 2, "days_requested": 6}


def test_stored_and_live_bodies_are_equal(world) -> None:
    live = _get(world.client(None), world.code)
    responses = world.responses()
    first = _get(world.client(responses), world.code)
    hit = _get(world.client(responses), world.code)
    assert first == live and hit == live
