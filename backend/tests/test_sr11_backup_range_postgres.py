"""SR-11 (rev 10b.3, D-SR.31/45/51): `GET /api/sites/{code}/backup-range` end to end over stored
`mini_depth.backup_day` rows on a real `*_test` database (the W4-02 fixture, Nairobi; SR-10a's day-kind helpers).

- a built day reads `stored: true`, 24 hours (3 assessed, 21 missing, so partial), and its sequences are the live
  one-hour backup heads' rows de-duplicated by `chain_id`;
- the next day has no built row: `stored: false`, STILL_PROCESSING, null counts (D-SR.51.3);
- the body never carries an outage count.

The chain day grades come from SR-10b's stub snapshot port (every day COMPLETE here); the grade order is pinned by the
no-DB tests. Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped otherwise.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from dataclasses import replace
    from types import SimpleNamespace

    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import test_w402_reads_postgres as w402
    from assetops_backend.chain import read as cr
    from assetops_backend.mini_depth.inputs import local_hour
    from assetops_backend.mini_depth.read import MiniDepthRead
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import link_rows_on
    from assetops_backend.mini_depth_api import build_day_range_router
    from test_sr10_day_kinds_postgres import SAMPLED, _builder, _consume_all, _fixture, _periods, _site
    from test_sr10_fuel_range_route import Port

KIND = "mini_depth.backup_day"


def _keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in _keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in _keys(v)}
    return set()


def test_backup_range_over_stored_day_rows(store, engine) -> None:  # noqa: F811
    t, s, day = _fixture(store, engine)
    _builder(engine).build(t, _site(t, s), day, KIND)
    _consume_all(engine)
    site = SimpleNamespace(tenant_id=t, id=s, site_code=w402.CODE, name="W402", site_type="MINIGRID",
                           timezone=w402.ZONE)
    registry = SimpleNamespace(tenant=lambda: SimpleNamespace(id=t), imported=lambda c: site if c == w402.CODE else None)
    port = Port()
    port_snapshots = port.snapshots
    port.snapshots = lambda tenant_id, site_id, lo, hi, measures, known_at: tuple(  # type: ignore[method-assign]
        replace(r, tenant_id=tenant_id, site_id=site_id)
        for r in port_snapshots(tenant_id, site_id, lo, hi, measures, known_at))
    reader, periods = cr.ChainReader(port), _periods(engine)
    app = FastAPI()
    app.include_router(build_day_range_router("backup", lambda: periods, lambda: reader, registry,  # type: ignore[arg-type]
                                              now=lambda: datetime.now(timezone.utc)))
    z = "%Y-%m-%dT00:00:00Z"
    response = TestClient(app).get(f"/api/sites/{w402.CODE}/backup-range",
                                   params={"from": day.strftime(z), "to": (day + timedelta(days=2)).strftime(z)})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema_version"] == "site-backup-range-1"
    built, absent = body["days"]
    assert (built["local_day"], absent["local_day"]) == (day.isoformat(), (day + timedelta(days=1)).isoformat())

    assert built["stored"] is True and built["partial"] is True
    assert (built["hours_expected"], built["hours_assessed"], built["hours_missing"]) == (24, 3, 21)
    live = MiniDepthRead(engine, link_rows_on)
    chains: dict[str, str] = {}
    for h in SAMPLED:  # the live one-hour backup cards of the three selected hours, latest hour wins
        w = local_hour(day, h, w402.ZONE)
        card = live.read(tenant_id=t, site_id=s, site_code=w402.CODE, domain="backup", lo=w.start, hi=w.end,
                         known_at=None)
        chains.update({str(r["chain_id"]): r["result"] for r in card["rows"]})
    assert {str(q["chain_id"]): q["result"] for q in built["sequences"]} == chains
    assert len(built["sequences"]) == len({q["chain_id"] for q in built["sequences"]})
    expected = ("SEQUENCE_FAILED" if "FAIL" in chains.values() else "SEQUENCE_INCOMPLETE"
                if "INCOMPLETE" in chains.values() else "SEQUENCES_PASSED" if chains else "NO_SEQUENCE")
    assert built["state"] == expected

    assert absent["stored"] is False and absent["state"] == "STILL_PROCESSING"
    assert absent["hours_expected"] is None and absent["sequence_counts"] is None
    assert body["totals"]["days_counted"] == 1 and body["totals"]["days_requested"] == 2
    assert not any("outage" in k for k in _keys(body) - {"outage_start"})
