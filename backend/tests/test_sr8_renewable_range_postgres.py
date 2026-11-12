"""SR-8 (rev 10 §10.4 tests, rev 10a §10a.3, D-SR.16/27): `renewable-range` over real `site_day_snapshot` rows.

On the W4-02 MINIGRID Site (`test_w402_reads_postgres`): the five ingested days are reconciled and their
`daylight_headroom_kw` snapshots built by the real `SnapshotBuilder`; one more day holds a stored MISSING_HOUR row,
and the last day of the window has no row at all. Through the route over the real `PostgresChainRead`:

- each day's band, decision and hours equal the stored snapshot row;
- the missing-hour day reads MISSING_HOUR (the rev 10 PARTIAL day) with no band;
- the absent-row day reads the chain's NO_DATA grade (D-SR.16), never "nothing known";
- for 3 sampled days, the row's band equals the one-day depth envelope's `headroom_kw` card (range -> drill-in);
- the totals average the COUNTED days only.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    import test_w402_reads_postgres as w402
    from assetops_backend.chain.adapters.postgres_chain_read import PostgresChainRead
    from assetops_backend.chain.adapters.postgres_snapshot_store import PostgresSnapshotStore
    from assetops_backend.chain.builder import SnapshotBuilder
    from assetops_backend.chain.composition import build_chain_inputs, load_coverage_policy, load_operating_calendar
    from assetops_backend.chain.measure_impls import build_measure_set
    from assetops_backend.chain.ports import SiteRef, SnapshotRow
    from assetops_backend.chain.read import ChainReader
    from assetops_backend.mini_depth_api import build_renewable_range_router


@dataclass
class _Site:
    tenant_id: UUID
    id: UUID
    site_code: str
    name: str
    site_type: str
    timezone: str


class _Registry:
    def __init__(self, site):
        self.site = site

    def tenant(self):
        return SimpleNamespace(id=self.site.tenant_id)

    def imported(self, code):
        return self.site if code == self.site.site_code else None


def _missing_hour_row(t, s, day):
    return SnapshotRow(
        tenant_id=t, site_id=s, local_day=day, subject_kind="SITE", subject_ref="SITE",
        measure="daylight_headroom_kw", evidence_class="MEASURED", revision=1, expected=True,
        required_seconds=86400, covered_seconds=82800, coverage_pct="95.83", grade="PARTIAL",
        value={"low_kw": None, "high_kw": None, "decision": None, "window_hours": None,
               "result_state": "MISSING_HOUR"}, money=None, policy_version="sr8", calendar_version="sr8",
        catalogue_version=1, input_fp=hashlib.sha256(f"sr8-{day}".encode()).hexdigest())


def _same(text, number):
    return (text is None and number is None) or Decimal(str(text)) == Decimal(str(number))


def test_range_days_equal_the_stored_rows_and_the_one_day_depth_card(store, engine) -> None:  # noqa: F811
    installed, t, s = w402._setup(store, engine)
    w402._ingest(engine, installed)
    w402._reconcile(engine, w402.DAYS)
    snaps, inputs = PostgresSnapshotStore(URL), build_chain_inputs(URL)
    chain = PostgresChainRead(URL, action_window=lambda *a, **k: {"actions": (), "events": ()})
    try:
        builder = SnapshotBuilder(snaps, build_measure_set(inputs), load_coverage_policy(),
                                  load_operating_calendar())
        built = builder.build_range(t, SiteRef(t, s, w402.CODE, "MINIGRID", w402.ZONE), w402.DAYS[0],
                                    w402.DAYS[-1], ["daylight_headroom_kw"])
        stored = {w.row.local_day: w.row for w in built}
        assert len(stored) == 5
        missing, absent = w402.DAYS[-1] + timedelta(days=1), w402.DAYS[-1] + timedelta(days=2)
        snaps.append(_missing_hour_row(t, s, missing))

        site = _Site(t, s, w402.CODE, "W402", "MINIGRID", w402.ZONE)
        app = FastAPI()
        app.include_router(build_renewable_range_router(lambda: ChainReader(chain), _Registry(site)))
        lo, hi = w402.DAYS[0], absent + timedelta(days=1)
        response = TestClient(app).get(f"/api/sites/{w402.CODE}/renewable-range",
                                       params={"from": f"{lo}T00:00:00Z", "to": f"{hi}T00:00:00Z"})
        assert response.status_code == 200, response.text
        body = response.json()
        days = {date.fromisoformat(d["local_day"]): d for d in body["days"]}
        assert list(days) == [lo + timedelta(days=i) for i in range(7)]

        for day, row in stored.items():
            got = days[day]
            assert got["grade"] == row.grade
            assert got["decision"] == row.value["decision"] and got["window_hours"] == row.value["window_hours"]
            assert (got["low_kw"], got["high_kw"]) == (row.value["low_kw"], row.value["high_kw"])
            assert got["state"] == ("COUNTED" if row.value["decision"] == "ELIGIBLE" else "EXCLUDED")
            assert (got["covered_hours"], got["operating_hours"]) == \
                (round(row.covered_seconds / 3600, 2), round(row.required_seconds / 3600, 2))

        assert (days[missing]["state"], days[missing]["grade"], days[missing]["low_kw"]) == \
            ("MISSING_HOUR", "PARTIAL", None)
        assert (days[absent]["state"], days[absent]["grade"], days[absent]["covered_hours"]) == \
            ("NO_DATA", "NO_DATA", None)

        for day in (w402.DAYS[0], w402.DAYS[2], w402.DAYS[4]):  # range -> one-day drill-in agreement
            depth = w402._read(engine, t, s, "renewable", w402._midnight(day),
                               w402._midnight(day + timedelta(days=1)))
            card = depth["cards"]["headroom_kw"]
            assert card is not None, depth["cards"]
            assert _same(days[day]["low_kw"], card["low"]) and _same(days[day]["high_kw"], card["high"]), \
                (day, days[day], card)

        counted = [d for d in body["days"] if d["state"] == "COUNTED"]
        totals = body["totals"]
        assert totals["days_requested"] == 7 and totals["days_counted"] == len(counted) and totals["partial"]
        if counted:
            mean = sum(Decimal(d["low_kw"]) for d in counted) / len(counted)
            assert Decimal(totals["average_low_kw"]) == mean.quantize(Decimal("0.01"))
    finally:
        pg_harness.dispose(chain, inputs, snaps)
