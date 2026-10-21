"""W4-03 unit 4: B3 W1 fences and the tick's OPPORTUNITY stage on Postgres (`.agent/W4-03-build-spec.md` closure 4
B3/S1, u3 "Unit 4 dry-read"). An MG `mini_opportunity` job enqueued, coalesced, leased and settled leaves the W1
Finding matcher fence and the Site Evidence pending-job projection unchanged, while a W1-domain job stays visible to
both; the unchanged-fence tick path still returns SKIPPED_UNCHANGED_FENCE with an opportunity job settled in that
tick; the token-scoped counters; an opportunity-only Site; and a resumed tick that adds no revision or selection.
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import _release_connections  # noqa: F401
    from test_s4_schedule_tick_postgres import (  # noqa: F401
        DAY_A,
        DAY_B,
        FAST,
        block,
        by_site,
        deliver,
        kobo,
        make_tick,
    )
    from test_w203_cold_migration_postgres import _replica
    from test_w402_reads_postgres import CODE, DAYS, _midnight, _setup
    from test_w403_opportunity_worker_postgres import counts, worker
    from test_w403_scenarios_postgres import mg

    from assetops_backend.analytics import dispatch_v3
    from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore
    from assetops_backend.analytics.assessment_ports import Window
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.mini_decisions import projection
    from assetops_backend.mini_decisions.store import PostgresMiniDecisionStore
    from assetops_backend.scheduling import stages
    from assetops_backend.scheduling.composition import build_schedule_store
    from assetops_backend.scheduling.tick import TickLimits

STUDY = (_midnight(DAYS[0]), _midnight(DAYS[-1] + timedelta(days=1))) if URL else None


def fences(engine, t, s) -> tuple:
    with engine.connect() as c:
        fence = PostgresFindingStore._fence(c, t, s, dispatch_v3.ANALYTIC_ID)
    return fence, PostgresEvidenceLedger(URL).site_window(t, s, None, None)["projection"]


def test_b3_opportunity_job_is_invisible_to_both_w1_fences(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    before = fences(engine, t, s)
    w = worker(engine)
    assert [q.action for q in w.reconcile(CODE, *STUDY)] == ["INSERTED"]
    assert fences(engine, t, s) == before
    assert [q.action for q in w.reconcile(CODE, *STUDY)] == ["COALESCED"]
    assert fences(engine, t, s) == before
    [done] = w.run_pending(scan=False)
    assert done.status == "DONE" and counts(engine)[:4] == (1, 1, 1, 1)
    assert fences(engine, t, s) == before
    # A W1-domain job remains visible to both.
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, status, "
            "available_at, created_at) VALUES (:id, :t, :s, 'dispatch', :lo, :hi, 'PENDING', now(), now())"),
            {"id": uuid4(), "t": t, "s": s, "lo": STUDY[0], "hi": STUDY[0] + timedelta(hours=1)})
    fence, projection_rows = fences(engine, t, s)
    assert fence != before[0] and fence.job_count == before[0].job_count + 1
    assert projection_rows != before[1] and any(r["status"] == "PENDING" for r in projection_rows)


def test_u4b_stage_deferred_counts_this_sites_pending_and_leased_only(store, engine) -> None:  # noqa: F811
    """u4b item 4 (final review M4): the real `stages.opportunity` over this Site's due job that fails on its last
    attempt, a not-yet-due PENDING job, a LEASED job and another Site's PENDING job. `deferred` is this Site's
    `live_opportunity_jobs` after the loop (PENDING + LEASED = 2), `failed` the terminal outcomes of this invocation;
    the foreign job neither runs nor counts. A Site with no renewable heads, so the stage's scan queues nothing."""
    _, t, s = _setup(store, engine)
    lo = STUDY[0]
    ids = {name: uuid4() for name in ("doomed", "later", "leased", "foreign")}
    rows = (  # (name, tenant, site, window_end, status, available_at, lease_until, attempts)
        ("doomed", t, s, lo + timedelta(hours=1), "PENDING", "now() - interval '1 hour'", "NULL", 2),
        ("later", t, s, STUDY[1], "PENDING", "now() + interval '1 day'", "NULL", 0),
        ("leased", t, s, STUDY[1], "LEASED", "now() - interval '1 hour'", "now() + interval '1 hour'", 1),
        ("foreign", uuid4(), uuid4(), STUDY[1], "PENDING", "now() - interval '2 hours'", "NULL", 0),
    )
    _replica(engine, *(
        "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, status, available_at, "
        f"lease_until, attempts, created_at) VALUES ('{ids[n]}', '{tt}', '{ss}', 'mini_opportunity', "
        f"'{lo.isoformat()}', '{hi.isoformat()}', '{st}', {at}, {until}, {a}, now())"
        for n, tt, ss, hi, st, at, until, a in rows))
    result = stages.opportunity(URL, {"tenant_id": str(t), "site_id": str(s), "limit": 5})
    assert result["code"] == "OK", result
    assert [(str(o["job_id"]), o["status"]) for o in result["outcomes"]] == [(str(ids["doomed"]), "FAILED")], result
    assert (result["processed"], result["failed"], result["deferred"]) == (1, 1, 2)
    assert sorted((j["id"], j["status"]) for j in result["live_jobs"]) == sorted(
        [(ids["later"], "PENDING"), (ids["leased"], "LEASED")])
    with engine.connect() as c:
        status = dict(c.execute(text("SELECT id, status FROM recompute_job WHERE id = ANY(:i)"),
                                {"i": list(ids.values())}).all())
    assert status == {ids["doomed"]: "FAILED", ids["later"]: "PENDING", ids["leased"]: "LEASED",
                      ids["foreign"]: "PENDING"}
    _replica(engine, f"DELETE FROM recompute_job WHERE id = '{ids['foreign']}'")


def test_record_opportunity_is_token_scoped_and_atomic(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    sched = build_schedule_store(URL)
    token = uuid4()
    assert sched.claim_site(t, s, token, "w403-test", 60)["claimed"]
    head = sched.site_head(t, s)
    assert (head["opportunity_processed"], head["opportunity_deferred"], head["opportunity_failed"]) == (0, 0, 0)
    assert sched.record_opportunity(t, s, token, 3, 2, 1)
    head = sched.site_head(t, s)
    assert (head["opportunity_processed"], head["opportunity_deferred"], head["opportunity_failed"]) == (3, 2, 1)
    # A lost token writes nothing; a negative count is refused before any write.
    assert not sched.record_opportunity(t, s, uuid4(), 9, 9, 9)
    with pytest.raises(ValueError, match="nonnegative"):
        sched.record_opportunity(t, s, token, 1, -1, 0)
    head = sched.site_head(t, s)
    assert (head["opportunity_processed"], head["opportunity_deferred"], head["opportunity_failed"]) == (3, 2, 1)


def test_opportunity_only_site_and_resumed_tick(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    worker(engine).reconcile(CODE, *STUDY)
    # Leave only the opportunity job: the Site is decommissioned and its other live work removed.
    _replica(engine, f"DELETE FROM recompute_job WHERE site_id = '{s}' AND domain <> 'mini_opportunity'",
             f"UPDATE site SET lifecycle = 'DECOMMISSIONED' WHERE id = '{s}'")
    tick, runner = make_tick(TickLimits(**FAST))
    report = tick.tick()
    assert report.outcome == "COMPLETED", report.failure
    [site] = [x for x in report.selected if x.site_id == s]
    assert site.reason == "EXCLUDED_WITH_WORK"
    [excluded] = [e for e in report.excluded_with_work if e["site_id"] == str(s)]
    assert [j["status"] for j in excluded["live_opportunity_jobs"]] == ["PENDING"] and excluded["live_mini_jobs"] == []
    order = [c for c, x in runner.calls if x == str(s)]
    assert order.index("mini") < order.index("opportunity") < order.index("s4")
    opp = site.stages["opportunity"]
    assert (opp["code"], opp["processed"], opp["failed"], opp["deferred"]) == ("OK", 1, 0, 0), opp
    head = tick.store.site_head(t, s)
    assert (head["opportunity_processed"], head["opportunity_deferred"], head["opportunity_failed"]) == (1, 0, 0)
    assert head["stage"] == "IDLE" and head["claim_token"] is None
    as_json = [x for x in report.as_json()["sites"] if x["site_id"] == str(s)][0]
    assert as_json["stages"]["opportunity"]["processed"] == 1
    settled = counts(engine)
    assert settled[:4] == (1, 1, 1, 1)
    # Nothing live: the next tick does not select the Site.
    again, runner2 = make_tick(TickLimits(**FAST), env=tick.environment)
    assert again.tick().outcome == "COMPLETED" and not [c for c, x in runner2.calls if x == str(s)]
    # Resume: a duplicate job for the settled study is processed without a second revision or selection.
    worker(engine).jobs.enqueue_opportunity_job(t, s, DAYS[0], DAYS[-1], Window(*STUDY))
    third, _ = make_tick(TickLimits(**FAST), env=tick.environment)
    [site3] = [x for x in third.tick().selected if x.site_id == s]
    assert site3.stages["opportunity"]["processed"] == 1 and site3.stages["opportunity"]["failed"] == 0
    assert counts(engine)[1:] == settled[1:] and counts(engine)[0] == 2


def test_unchanged_fence_tick_still_skips_with_an_opportunity_job(kobo, store, engine) -> None:  # noqa: F811
    lim = TickLimits(**FAST)
    tick, _ = make_tick(lim)
    deliver(kobo, block(DAY_A, 8, 9), block(DAY_B, 8, 9))
    assert by_site(tick.tick())[str(kobo.site)].stages["s4"]["code"] == "MATCHED"
    mini = PostgresMiniDecisionStore(engine)
    with mini.snapshot() as c:
        tz_name = mini.site_timezone(c, kobo.tenant, kobo.site)[0]
    first = date(2026, 10, 6)
    window = projection.study_window(first, first + timedelta(days=4), tz_name)
    worker(engine).jobs.enqueue_opportunity_job(kobo.tenant, kobo.site, first, first + timedelta(days=4), window)
    r = by_site(tick.tick())[str(kobo.site)]
    assert r.stages["opportunity"]["processed"] == 1 and r.stages["opportunity"]["failed"] == 0
    assert r.stages["s4"]["code"] == "SKIPPED_UNCHANGED_FENCE" and r.result == "COMPLETED"
