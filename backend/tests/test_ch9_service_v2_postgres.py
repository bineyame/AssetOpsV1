"""CH-9 CH9-R4 F1 (L2): migration `0047_mini_service_v2` and `critical_served` over stored `mini-service/2` heads.

- 0047 enqueues `mini_service` work only for the hours whose selected service head is `mini-service/1` (not a `/2`
  head, not another domain), with a NULL cause; draining that work selects a `/2` head whose rows state their own
  `unserved_kwh`.
- Through the real Postgres chain reader, `critical_served` grades COMPLETE over a delivered day whose CRITICAL row is
  SUPPORTED and whose UNCLASSIFIED load has no request evidence (the real Kobo shape; F1's NO_DATA case).
"""

from __future__ import annotations

import dataclasses
import os
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_w203_cold_migration_postgres import _replica, head
    from test_w402_migration_postgres import mini_jobs, revision
    from test_w402_mini_stage_postgres import _installed, _rows

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.chain.adapters.postgres_chain_inputs import PostgresChainInputs
    from assetops_backend.chain.grading import COMPLETE, classify_day, covered_seconds
    from assetops_backend.chain.measure_impls import CriticalServed
    from assetops_backend.chain.measures import MEASURES
    from assetops_backend.chain.ports import DayCtx
    from assetops_backend.mini_depth.inputs import local_noon
    from assetops_backend.mini_depth.store import PostgresMiniDepthStore
    from assetops_backend.mini_depth.worker import MiniDepthWorker

UTC = timezone.utc
TZ = "Africa/Nairobi"


def _v2(rev):
    return dataclasses.replace(rev, model_version="mini-service/2")


def _clear(engine, site_id) -> None:  # noqa: F811
    _replica(engine, f"DELETE FROM recompute_job WHERE site_id = '{site_id}' AND domain LIKE 'mini\\_%'")


def test_0047_enqueues_v1_service_hours_only_and_drains_to_v2(store, engine) -> None:  # noqa: F811
    from alembic import command

    tenant_id, site_id = _installed(store, engine)
    ctx = type("Ctx", (), {"t": tenant_id, "s": site_id})
    mini = PostgresMiniDepthStore(engine)
    noon = local_noon(date(2026, 10, 6), TZ)
    eleven = noon.start - timedelta(hours=1)
    # Backfill heads: service /1 at noon (re-derived), service /2 at 11:00 and fuel /1 at noon (both left alone).
    mini.append_selection(revision(ctx, lo=noon.start, hi=noon.end, digest="1"), job_id=None, backfill=True)
    mini.append_selection(_v2(revision(ctx, lo=eleven, hi=noon.start, digest="2")), job_id=None, backfill=True)
    mini.append_selection(revision(ctx, lo=noon.start, hi=noon.end, domain="fuel", digest="3"), job_id=None,
                          backfill=True)
    _clear(engine, site_id)

    config = _alembic()
    engine.dispose()
    command.downgrade(config, "0046_daylight_enqueue")  # 0047's downgrade is a no-op
    command.upgrade(config, "head")
    assert head(engine) == "0047_mini_service_v2"

    jobs = mini_jobs(engine, site_id)
    assert [(j["domain"], j["window_start"], j["window_end"], j["cause_evidence_id"], j["status"]) for j in jobs] == [
        ("mini_service", noon.start, noon.end, None, "PENDING")]

    clock = datetime.now(UTC) + timedelta(minutes=1)
    assessment = PostgresAssessmentStore(URL)
    try:
        out = MiniDepthWorker(assessment, mini, test_lease_clock=lambda: clock).run_pending(5, tenant_id, site_id)
    finally:
        assessment._connect_engine().dispose()
    assert [(o.domain, o.status) for o in out] == [("service", "DONE")], [o.error for o in out]
    [newest] = _rows(engine, "SELECT r.model_version, r.result FROM mini_depth_selection s JOIN mini_depth_revision r "
                             "ON r.tenant_id = s.tenant_id AND r.site_id = s.site_id AND r.id = s.revision_id "
                             "WHERE s.site_id = :s AND s.domain = 'service' AND s.window_start = :lo "
                             "ORDER BY s.selected_at DESC, s.seq DESC LIMIT 1", s=site_id, lo=noon.start)
    assert newest["model_version"] == "mini-service/2"
    rows = newest["result"]["rows"]
    assert rows and all("unserved_kwh" in r for r in rows)
    assert all(r["unserved_kwh"] is None for r in rows if r["assessment"] != "SUPPORTED")


def _row(role: str, code: str, delivered, assessment: str, request: str, unserved) -> dict:
    return {"role": role, "asset_id": code, "asset_code": code, "load_label": code, "delivered_kw": delivered,
            "requested_evidence_state": request, "assessment": assessment, "unserved_kwh": unserved,
            "coverage": {"required_seconds": 3600, "observed_seconds": 3600, "source_count": 1, "gaps": []},
            "evidence_ids": []}


def test_critical_served_complete_over_a_delivered_day_with_unrequested_unclassified_load(store, engine) -> None:  # noqa: F811
    tenant_id, site_id = _installed(store, engine)
    ctx = type("Ctx", (), {"t": tenant_id, "s": site_id})
    mini = PostgresMiniDepthStore(engine)
    day = date(2026, 10, 20)
    lo = datetime(2026, 10, 20, tzinfo=ZoneInfo(TZ)).astimezone(UTC)
    rows = [_row("CRITICAL", "load-clinic", 6, "SUPPORTED", "ACCEPTED", 0.5),
            _row("UNCLASSIFIED", "load-mill", 16.333333333333332, "UNKNOWN", "MISSING", None)]
    result = {"status": "LIMITED", "cards": {"delivered_load_kw": 22.33, "interruptions_seen": None,
                                             "critical_delivered_kw": 6, "unserved_kwh": None},
              "critical_delivered_coverage": None, "rows": rows, "limitations": [], "coverage": {"gaps": []}}
    for n in range(24):
        a = lo + timedelta(hours=n)
        mini.append_selection(_v2(revision(ctx, lo=a, hi=a + timedelta(hours=1), digest=f"d{n}", result=result)),
                              job_id=None, backfill=True)
    _clear(engine, site_id)

    dctx = DayCtx(tenant_id, site_id, "MG", "MINIGRID", TZ, day, lo, lo + timedelta(days=1), None)
    got = CriticalServed(PostgresChainInputs(engine=engine)).inputs(dctx, "SITE")
    covered = covered_seconds(got.covered, dctx.period_start_utc, dctx.period_end_utc)
    assert (covered, got.pending) == (24 * 3600, False)
    spec = MEASURES["critical_served"]
    assert classify_day(True, 24 * 3600, covered, got.pending, None, spec.threshold) == COMPLETE
    assert CriticalServed(None).measure(dctx, "SITE", got) == {"served_kwh": "144", "demand_kwh": "156.0",
                                                               "unserved_kwh": "12.0"}
