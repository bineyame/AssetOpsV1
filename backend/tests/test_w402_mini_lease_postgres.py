"""W4-02 unit 4 step 1 (closure 4 S2): the mini-depth lease/settle/fail methods on the assessment store.

Leases take only the four mini domains (never a Dispatch job), a Site-scoped lease stays in its Site, settle commits
DONE with the revision and selection on the worker's connection (or rolls back with them), and a lost lease
settles nothing. Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import site  # noqa: F401
    from test_w203_cold_migration_postgres import _replica
    from test_w402_migration_postgres import mg, revision  # noqa: F401

    from assetops_backend.analytics.adapters.postgres_assessment_store import (
        MINI_JOB_DOMAINS,
        PostgresAssessmentStore,
    )
    from assetops_backend.analytics.assessment_ports import JobLease, LeaseLost
    from assetops_backend.mini_depth.store import PostgresMiniDepthStore

LO = datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc)
NOW = datetime(2026, 10, 7, 0, 0, tzinfo=timezone.utc)
LEASE = timedelta(minutes=5)


def job(engine, ctx, domain: str, lo: datetime, *, available: datetime = LO, site_id=None):
    jid = uuid4()
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, status, "
            "available_at, created_at) VALUES (:id, :t, :s, :d, :lo, :hi, 'PENDING', :av, :av)"),
            {"id": jid, "t": ctx.t, "s": site_id or ctx.s, "d": domain, "lo": lo, "hi": lo + timedelta(hours=1),
             "av": available})
    return jid


def state(engine, jid):
    with engine.connect() as c:
        return c.execute(text("SELECT status, attempts, available_at, last_error FROM recompute_job WHERE id = :i"),
                         {"i": jid}).one()


def selections(engine, jid) -> int:
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM mini_depth_selection WHERE job_id = :j"), {"j": jid}).scalar_one()


@pytest.fixture()
def jobs(mg, engine):  # noqa: F811
    store = PostgresAssessmentStore(URL)
    yield store
    _replica(engine, f"DELETE FROM recompute_job WHERE site_id = '{mg.ctx.s}' AND domain = 'dispatch'")
    store._connect_engine().dispose()


def test_mini_lease_takes_only_mini_domains_and_settles_with_the_selection(mg, engine, jobs) -> None:  # noqa: F811
    ctx = mg.ctx
    dispatch = job(engine, ctx, "dispatch", LO, available=LO - timedelta(days=1))  # older than any mini job
    first = job(engine, ctx, "mini_service", LO)

    # The Dispatch path refuses mini domains; the mini lease never takes the (older) Dispatch job.
    with pytest.raises(ValueError):
        jobs.lease_job("mini_service", NOW, LEASE)
    lease = jobs.lease_mini_job(LEASE, tenant_id=ctx.t, site_id=ctx.s, now=NOW)
    assert lease is not None and (lease.job_id, lease.domain, lease.attempts) == (first, "mini_service", 1)
    assert lease.window.start == LO and lease.knowledge_cutoff == NOW
    assert jobs.lease_mini_job(LEASE, tenant_id=ctx.t, site_id=ctx.s, now=NOW) is None  # nothing else due
    assert state(engine, dispatch)[:2] == ("PENDING", 0)
    # A Site-scoped lease of another Site sees none of this Site's work; a half scope is refused.
    second = job(engine, ctx, "mini_fuel", LO)
    assert jobs.lease_mini_job(LEASE, tenant_id=ctx.t, site_id=uuid4(), now=NOW) is None
    with pytest.raises(ValueError):
        jobs.lease_mini_job(LEASE, tenant_id=ctx.t, now=NOW)

    # Revision, selection and DONE commit together on the worker's connection.
    mini = PostgresMiniDepthStore(engine)
    with engine.begin() as c:
        appended = mini.append_selection(revision(ctx, lo=LO, hi=LO + timedelta(hours=1)), job_id=first,
                                         connection=c)
        jobs.settle_mini_job(c, lease)
    assert state(engine, first)[0] == "DONE" and selections(engine, first) == 1 and appended.seq > 0

    # A failure after the selection rolls back both: the job stays LEASED and no selection exists.
    fuel = jobs.lease_mini_job(LEASE, tenant_id=ctx.t, site_id=ctx.s, now=NOW)
    assert fuel is not None and fuel.job_id == second
    with pytest.raises(RuntimeError):
        with engine.begin() as c:
            mini.append_selection(revision(ctx, lo=LO, hi=LO + timedelta(hours=1), domain="fuel"), job_id=second,
                                  connection=c)
            jobs.settle_mini_job(c, fuel)
            raise RuntimeError("worker failed before commit")
    assert state(engine, second)[0] == "LEASED" and selections(engine, second) == 0

    # A lease that is no longer ours (another attempt, or a non-mini job) settles nothing.
    stale = JobLease(fuel.job_id, fuel.tenant_id, fuel.site_id, fuel.domain, fuel.window, fuel.attempts + 1, NOW)
    foreign = JobLease(dispatch, ctx.t, ctx.s, "mini_service", fuel.window, 0, NOW)
    for wrong in (stale, foreign):
        with pytest.raises(LeaseLost):
            with engine.begin() as c:
                jobs.settle_mini_job(c, wrong)
    assert state(engine, dispatch)[:2] == ("PENDING", 0) and state(engine, second)[0] == "LEASED"
    assert jobs.fail_mini_job(foreign, "x", max_attempts=3, backoff=LEASE, now=NOW) == "LEASE_LOST"

    # fail: back to PENDING after backoff x attempts, then FAILED on the last allowed attempt.
    assert jobs.fail_mini_job(fuel, "boom", max_attempts=2, backoff=LEASE, now=NOW) == "RETRY"
    status, attempts, available, error = state(engine, second)
    assert (status, attempts, available, error) == ("PENDING", 1, NOW + LEASE, "boom")
    again = jobs.lease_mini_job(LEASE, tenant_id=ctx.t, site_id=ctx.s, now=NOW + LEASE)
    assert again is not None and again.attempts == 2
    assert jobs.fail_mini_job(again, "boom", max_attempts=2, backoff=LEASE, now=NOW + LEASE) == "FAILED"
    assert state(engine, second)[0] == "FAILED"
    assert state(engine, dispatch)[:2] == ("PENDING", 0)  # zero Dispatch jobs touched by the mini path


def test_mini_lease_expiry_and_database_clock(mg, engine, jobs) -> None:  # noqa: F811
    ctx = mg.ctx
    jid = job(engine, ctx, "mini_backup", LO)
    lease = jobs.lease_mini_job(LEASE, max_attempts=1, tenant_id=ctx.t, site_id=ctx.s, now=NOW)
    assert lease is not None
    # An expired lease on its last allowed attempt is FAILED with a reason, never re-leased.
    assert jobs.lease_mini_job(LEASE, max_attempts=1, tenant_id=ctx.t, site_id=ctx.s,
                               now=NOW + 2 * LEASE) is None
    status, _, _, error = state(engine, jid)
    assert status == "FAILED" and error == "lease expired on attempt 1 of 1 without completing"
    # Without a test instant the lease time is the database clock, and it is the knowledge cutoff.
    job(engine, ctx, "mini_renewable", LO)
    before = datetime.now(timezone.utc)
    live = jobs.lease_mini_job(LEASE, tenant_id=ctx.t, site_id=ctx.s)
    assert live is not None and live.domain == "mini_renewable"
    assert abs((live.knowledge_cutoff - before).total_seconds()) < 60
    assert set(MINI_JOB_DOMAINS) == {"mini_renewable", "mini_service", "mini_fuel", "mini_backup"}


def test_mini_worker_lease_instant_is_the_one_cutoff(store, engine) -> None:  # noqa: F811
    """Step 4 (closure 1 Q3, closure 4 S2, q5 ruling 5): the worker leases at T and passes T unchanged to the inputs,
    digest and revision; a row received a microsecond after T is absent, a row at T is present, a re-lease after
    T+1 us takes it in; one transaction appends revision + selection(job_id) + DONE; Dispatch jobs are untouched;
    a refused input set fails the job for retry; `reconcile` appends backfill selections and writes no job."""
    from datetime import date

    from test_s2_evidence_ledger_postgres import enable
    from test_w402_authored_v4_postgres import RECEIVED, cases, ingestion, install, principal, snapshot

    from assetops_backend.mini_depth.inputs import load_hour_inputs, local_noon
    from assetops_backend.mini_depth.worker import MiniDepthWorker

    installed = install(store)
    tenant_id, site_id = installed.result.site.tenant_id, installed.result.site.id
    enable(engine, site_id)
    doc, sha = snapshot(engine, installed.binding_set.id)
    service = ingestion()
    for b in cases.build_batches(cases.load_spec(), doc, sha, "positive"):
        service.submit(principal(doc), b.body.encode("utf-8"))
    window, T = local_noon(date(2026, 10, 6), "Africa/Nairobi"), RECEIVED
    after = T + timedelta(microseconds=1)

    def load(k):
        with engine.connect() as c:
            c.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
            return load_hour_inputs(c, tenant_id, site_id, window, k)

    full = load(T)
    late = next(r.evidence_id for r in full.backup_readings())
    keep = "domain = 'mini_backup' AND window_start = '" + window.start.isoformat() + "'"
    with engine.connect() as c:
        target = c.execute(text(f"SELECT id, available_at FROM recompute_job WHERE site_id = :s AND {keep}"),
                           {"s": site_id}).one()
        dispatch_before = c.execute(text("SELECT id, status, attempts FROM recompute_job WHERE site_id = :s "
                                         "AND domain = 'dispatch' ORDER BY id"), {"s": site_id}).all()
    assert target.available_at <= T and dispatch_before
    _replica(engine, f"DELETE FROM recompute_job WHERE site_id = '{site_id}' AND domain LIKE 'mini_%' AND NOT ({keep})",
             f"UPDATE accepted_evidence SET received_at = '{after.isoformat()}' WHERE id = '{late}'")
    cut = load(T)
    assert late not in cut.evidence_ids and cut.evidence_ids and set(cut.evidence_ids) == set(full.evidence_ids) - {late}

    jobs = PostgresAssessmentStore(URL)
    mini = PostgresMiniDepthStore(engine)
    try:
        [out] = MiniDepthWorker(jobs, mini, test_lease_clock=lambda: T).run_pending(10, tenant_id, site_id)
        assert (out.status, out.job_id, out.domain, out.knowledge_cutoff) == ("DONE", target.id, "backup", T), out.error

        def revision(rid):
            with engine.connect() as c:
                row = c.execute(text("SELECT knowledge_cutoff, input_sha256, result FROM mini_depth_revision "
                                     "WHERE id = :r"), {"r": rid}).one()
                ids = {r[0] for r in c.execute(text("SELECT evidence_id FROM mini_depth_revision_evidence "
                                                    "WHERE revision_id = :r"), {"r": rid}).all()}
            return row, ids

        row, ids = revision(out.selection.revision_id)
        assert (row.knowledge_cutoff, row.input_sha256) == (T, cut.input_sha256) and ids == set(cut.evidence_ids)
        assert row.result["domain"] == "backup" and row.result["basis"]["site_timezone"] == "Africa/Nairobi"
        assert state(engine, target.id)[0] == "DONE" and selections(engine, target.id) == 1
        with engine.connect() as c:
            assert c.execute(text("SELECT id, status, attempts FROM recompute_job WHERE site_id = :s "
                                  "AND domain = 'dispatch' ORDER BY id"), {"s": site_id}).all() == dispatch_before

        ctx = type("Ctx", (), {"t": tenant_id, "s": site_id})
        again = job(engine, ctx, "mini_backup", window.start, available=after)
        [re] = MiniDepthWorker(jobs, mini, test_lease_clock=lambda: after).run_pending(10, tenant_id, site_id)
        assert (re.status, re.job_id, re.knowledge_cutoff) == ("DONE", again, after)
        row2, ids2 = revision(re.selection.revision_id)
        assert re.selection.revision_id != out.selection.revision_id and re.selection.seq > out.selection.seq
        assert row2.knowledge_cutoff == after and late in ids2 and ids2 == set(load(after).evidence_ids)

        # A refused input set (no Foundation covers 2020) fails the job for retry, writing no selection.
        old = job(engine, ctx, "mini_service", datetime(2020, 1, 1, 9, tzinfo=timezone.utc), available=after)
        [bad] = MiniDepthWorker(jobs, mini, test_lease_clock=lambda: after).run_pending(10, tenant_id, site_id)
        assert (bad.job_id, bad.status, bad.selection) == (old, "RETRY", None)
        st = state(engine, old)
        assert st[0] == "PENDING" and st[3].startswith("CONFIGURATION_MISSING") and selections(engine, old) == 0

        # Explicit backfill: all four domains at local noon, at the DB clock, no job read or written.
        with engine.connect() as c:
            code = c.execute(text("SELECT site_code FROM site WHERE id = :s"), {"s": site_id}).scalar_one()
            jobs_before = c.execute(text("SELECT count(*) FROM recompute_job WHERE site_id = :s"),
                                    {"s": site_id}).scalar_one()
        done = MiniDepthWorker(jobs, mini).reconcile(code, window.start - timedelta(minutes=30),
                                                     window.end + timedelta(minutes=30))
        assert sorted(o.domain for o in done) == ["backup", "fuel", "renewable", "service"]
        assert {(o.window, o.job_id, o.status) for o in done} == {(window, None, "DONE")}
        assert all(o.knowledge_cutoff > after for o in done)
        assert all(late in revision(o.selection.revision_id)[1] for o in done)
        with engine.connect() as c:
            assert c.execute(text("SELECT count(*) FROM recompute_job WHERE site_id = :s"),
                             {"s": site_id}).scalar_one() == jobs_before
            assert c.execute(text("SELECT count(*) FROM mini_depth_selection WHERE site_id = :s AND job_id IS NULL"),
                             {"s": site_id}).scalar_one() == 4
    finally:
        jobs._connect_engine().dispose()
