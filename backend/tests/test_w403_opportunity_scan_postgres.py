"""W4-03 unit 4: the opportunity worker scan and reconcile (`.agent/W4-03-build-spec.md` closure 2 Q4, closure 4
S2/S5/S6, u3 "Unit 4 dry-read"): exact five-day study windows, routine retention edge, missing days, historical
reconcile and coalescing under the study-key advisory lock.
"""

from __future__ import annotations

import os
from datetime import date, timedelta

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_w402_reads_postgres import CODE, DAYS, ZONE, _ingest, _midnight, _reconcile, _setup
    from test_w403_scenarios_postgres import mg

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.mini_decisions import projection
    from assetops_backend.mini_decisions.store import PostgresMiniDecisionStore
    from assetops_backend.mini_decisions.worker import MiniOpportunityWorker
    from assetops_backend.mini_depth.inputs import local_noon


def worker(engine) -> "MiniOpportunityWorker":
    return MiniOpportunityWorker(PostgresAssessmentStore(URL), PostgresMiniDecisionStore(engine))


def jobs(engine) -> list:
    with engine.connect() as c:
        return c.execute(text(
            "SELECT id, tenant_id, site_id, window_start, window_end, cause_evidence_id, status, available_at, "
            "created_at FROM recompute_job WHERE domain = 'mini_opportunity' ORDER BY window_start, id")).all()


def test_study_window_and_hash_vectors() -> None:
    w = projection.study_window(date(2026, 10, 6), date(2026, 10, 10), ZONE)
    assert (w.start, w.end) == (_midnight(date(2026, 10, 6)), _midnight(date(2026, 10, 11)))
    assert projection.study_days(date(2026, 10, 10)) == DAYS
    from uuid import UUID
    t, s = UUID(int=1), UUID(int=2)
    noon = local_noon(DAYS[0], ZONE)
    missing = [projection.DayHead(d, local_noon(d, ZONE)) for d in DAYS]
    base = projection.input_sha256(t, s, DAYS[0], DAYS[-1], missing)
    assert base.startswith("sha256:") and len(base) == 71
    # Selection seq/time are excluded; revision ID, digest, decision and accepted IDs are included.
    head = projection.DayHead(DAYS[0], noon, 7, None, "r1", "sha256:" + "0" * 64, "ELIGIBLE", ("e1",))
    one = projection.input_sha256(t, s, DAYS[0], DAYS[-1], [head] + missing[1:])
    reseq = projection.DayHead(DAYS[0], noon, 9, None, "r1", "sha256:" + "0" * 64, "ELIGIBLE", ("e1",))
    assert projection.input_sha256(t, s, DAYS[0], DAYS[-1], [reseq] + missing[1:]) == one != base
    for change in ({"mini_revision_id": "r2"}, {"input_sha256": "sha256:" + "1" * 64}, {"decision": "LIMITED"},
                   {"evidence_ids": ("e1", "e2")}):
        changed = projection.DayHead(**{**head.__dict__, **change})
        assert projection.input_sha256(t, s, DAYS[0], DAYS[-1], [changed] + missing[1:]) != one


def test_historical_reconcile_and_coalesced_rescan(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    w = worker(engine)
    queued = w.reconcile(CODE, _midnight(DAYS[0]), _midnight(DAYS[-1] + timedelta(days=1)))
    assert [(q.study.first_day, q.study.last_day, q.action) for q in queued] == [(DAYS[0], DAYS[-1], "INSERTED")]
    [job] = jobs(engine)
    assert (job.tenant_id, job.site_id, job.cause_evidence_id, job.status) == (t, s, None, "PENDING")
    assert (job.window_start, job.window_end) == (_midnight(DAYS[0]), _midnight(DAYS[-1] + timedelta(days=1)))
    assert job.available_at == job.created_at
    # No projection exists yet, so a repeat is changed again: it coalesces the one PENDING job, never a second.
    again = w.reconcile(CODE, _midnight(DAYS[0]), _midnight(DAYS[-1] + timedelta(days=1)))
    assert [(q.action, q.job_id) for q in again] == [("COALESCED", job.id)]
    [after] = jobs(engine)
    assert after.available_at >= job.available_at and after.created_at == job.created_at
    # A range one microsecond short of the study encloses no complete five-day study.
    short = w.reconcile(CODE, _midnight(DAYS[0]), _midnight(DAYS[-1] + timedelta(days=1)) - timedelta(microseconds=1))
    assert short == [] and len(jobs(engine)) == 1


def test_routine_scan_retention_edge_and_missing_day(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    w = worker(engine)
    last_noon = local_noon(DAYS[-1], ZONE).start
    # Exactly at the bound the last selected noon is retained (>=); one microsecond later it is not.
    w.jobs.test_clock_override = lambda: last_noon + timedelta(days=5, microseconds=1)
    assert w.enqueue_from_selections() == [] and jobs(engine) == []
    w.jobs.test_clock_override = lambda: last_noon + timedelta(days=5)
    queued = w.enqueue_from_selections(t, s)
    assert [(q.study.first_day, q.study.last_day, q.action) for q in queued] == [(DAYS[0], DAYS[-1], "INSERTED")]
    # A day earlier the 9 Oct noon is retained too: its study 5-9 Oct has a missing 5 Oct (an explicit null day).
    w.jobs.test_clock_override = lambda: last_noon + timedelta(days=4)
    queued = w.enqueue_from_selections()
    assert [(q.study.last_day, q.action) for q in queued] == [(DAYS[-2], "INSERTED"), (DAYS[-1], "COALESCED")]
    with PostgresMiniDecisionStore(engine).snapshot() as c:
        heads = projection.day_heads(PostgresMiniDecisionStore(engine), c, t, s, ZONE,
                                     projection.study_days(DAYS[-2]))
    assert heads[0].local_day == date(2026, 10, 5) and heads[0].mini_revision_id is None
    assert heads[0].hash_day() == {"local_day": "2026-10-05", "mini_revision_id": None, "input_sha256": None,
                                   "decision": None, "evidence_ids": []}
    assert all(h.mini_revision_id for h in heads[1:])
    assert len(jobs(engine)) == 2


def test_uf6_failed_job_is_retained_until_the_selected_input_changes(store, engine) -> None:  # noqa: F811
    """uF 6 (final review L10): repeated routine scans over an unchanged study with a terminal FAILED job queue
    nothing; a new W4-02 selection (late evidence) queues exactly one new job."""
    installed, t, s = _setup(store, engine)
    _reconcile(engine, DAYS[1:])  # selected before evidence: the 6-10 Oct study has a missing 6 Oct
    w = worker(engine)
    w.jobs.test_clock_override = lambda: local_noon(DAYS[-1], ZONE).start + timedelta(days=5)
    assert [(q.study.last_day, q.action) for q in w.enqueue_from_selections(t, s)] == [(DAYS[-1], "INSERTED")]
    with engine.begin() as c:  # the job's last attempt failed (as `fail_opportunity_job` leaves it)
        c.execute(text("UPDATE recompute_job SET status = 'FAILED', attempts = 3, available_at = clock_timestamp(), "
                       "last_error = 'w403 uF6 vector' WHERE domain = 'mini_opportunity'"))
    before = jobs(engine)
    for _ in range(3):
        assert w.enqueue_from_selections(t, s) == []
    assert jobs(engine) == before and {j.status for j in before} == {"FAILED"}
    _ingest(engine, installed)
    _reconcile(engine, DAYS)
    assert [(q.study.last_day, q.action) for q in w.enqueue_from_selections(t, s)] == [(DAYS[-1], "INSERTED")]
    assert [(q.study.last_day, q.action) for q in w.enqueue_from_selections(t, s)] == [(DAYS[-1], "COALESCED")]
    assert sorted(j.status for j in jobs(engine)) == ["FAILED", "PENDING"]  # exactly one new job


def test_concurrent_enqueue_coalesces_to_one_pending_job(store, engine) -> None:  # noqa: F811
    import threading

    t, s = mg(store, engine)
    window = projection.study_window(DAYS[0], DAYS[-1], ZONE)
    stores = [PostgresAssessmentStore(URL) for _ in range(4)]
    barrier, results, errors = threading.Barrier(4), [], []

    def enqueue(jobs_store) -> None:
        try:
            barrier.wait()
            results.append(jobs_store.enqueue_opportunity_job(t, s, DAYS[0], DAYS[-1], window))
        except Exception as error:  # noqa: BLE001
            errors.append(error)

    threads = [threading.Thread(target=enqueue, args=(x,)) for x in stores]
    for th in threads:
        th.start()
    for th in threads:
        th.join(60)
    assert not errors
    assert sorted(a for a, _ in results) == ["COALESCED", "COALESCED", "COALESCED", "INSERTED"]
    [job] = jobs(engine)
    assert {j for _, j in results} == {job.id} and job.status == "PENDING"
