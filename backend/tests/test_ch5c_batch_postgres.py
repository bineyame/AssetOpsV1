"""CH-5c u1 (CH5c-R3 R2/R3): the batched dispatch-day read is deep-equal to the per-day path.

R2: every seeded day, live and historical cutoffs, every job state (PENDING, DONE-selected, DONE-empty, FAILED).
R3: inside one read scope bound to the REPEATABLE READ snapshot, a cutoff at the read instant shares the live key
and its result dict equals the live read; a cutoff below it keeps its own key.
L2m: with `ASSETOPS_CH5C_CLONE_URL` set (a settled chain clone, read only), parity over every Site and story day.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest

from test_s4_finding_store_postgres import SPEC, URL, CaseRunner  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import create_engine, text
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    from assetops_backend import read_scope
    from assetops_backend.analytics import dispatch_v3
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.assessment_worker import input_basis
    from assetops_backend.analytics.dispatch_read import day_window

F06 = next(c for c in SPEC["cases"] if c["case_id"] == "F06")
F06_DAY = datetime(2026, 10, 15, tzinfo=timezone.utc)
LIVE = datetime(9000, 1, 1, tzinfo=timezone.utc)
CLONE = os.environ.get("ASSETOPS_CH5C_CLONE_URL")


@pytest.fixture()
def runner(store, engine):  # noqa: F811
    owned = CaseRunner(store, engine)
    yield owned
    pg_harness.dispose(owned.findings)


@contextmanager
def snapshot(engine):  # noqa: F811
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
        with c.begin():
            yield c


def _select_dispatch_days_each(store, c, tenant_id, site_id, from_, to, known_at):
    """CH5c-R7 L7: the per-day reference path (moved out of product code); `_dispatch_day_on` without a prefetch."""
    if from_ >= to:
        return []
    live = known_at >= store._transaction_time(c)

    def basis(result):
        inputs, config_sha = input_basis(result, dispatch_v3)
        return (None if inputs.cohort.status == "EMPTY" else inputs.input_sha256), config_sha
    days = []
    day = from_.astimezone(timezone.utc).date()
    while (window := day_window(day)).start < to:
        if window.end > from_:
            days.append(store._dispatch_day_on(c, tenant_id, site_id, day, window, known_at, live, basis))
        day += timedelta(days=1)
    return days


def both(store, c, tenant, site, frm, to, k):
    """The batched and per-day results, each in its own fresh read scope (no memo sharing between them)."""
    with read_scope.scope("ch5c-batched"):
        batched = store.select_dispatch_days_on(c, tenant, site, frm, to, k)
    with read_scope.scope("ch5c-each"):
        each = _select_dispatch_days_each(store, c, tenant, site, frm, to, k)
    return batched, each


def test_batched_days_equal_per_day_at_every_cutoff_and_job_state(runner, monkeypatch) -> None:
    runner.step(F06["steps"][0])  # deliver: a PENDING job
    queued = runner.now
    runner.step(F06["steps"][1])  # assess: DONE, first selection
    cutoff = runner.now
    for step in F06["steps"][3:5]:
        runner.step(step)
    present = runner.now
    monkeypatch.setattr(PostgresAssessmentStore, "_transaction_time", staticmethod(lambda c: present))
    store = PostgresAssessmentStore(URL)
    frm, to = F06_DAY - timedelta(days=2, hours=12), F06_DAY + timedelta(days=2, hours=6)
    try:
        with snapshot(runner.engine) as c:
            for k in (queued, cutoff, present, LIVE):
                batched, each = both(store, c, runner.tenant, runner.site, frm, to, k)
                assert len(batched) == 6 and batched == each, k
            assert any(d["selection"] for d in batched)
        with runner.engine.begin() as c:  # a FAILED job and a DONE job with no selection
            ids = [r[0] for r in c.execute(text("SELECT id FROM recompute_job WHERE site_id = :s ORDER BY id"),
                                           {"s": runner.site})]
            assert ids
            c.execute(text("UPDATE recompute_job SET status = 'FAILED' WHERE id = :j"), {"j": ids[0]})
        with snapshot(runner.engine) as c:
            for k in (queued, cutoff, present, LIVE):
                batched, each = both(store, c, runner.tenant, runner.site, frm, to, k)
                assert batched == each, k
        # empty range and a single UTC-midnight-crossing hour
        with snapshot(runner.engine) as c:
            assert both(store, c, runner.tenant, runner.site, to, frm, LIVE) == ([], [])
            b, e = both(store, c, runner.tenant, runner.site, F06_DAY - timedelta(minutes=30),
                        F06_DAY + timedelta(minutes=30), LIVE)
            assert len(b) == 2 and b == e
    finally:
        pg_harness.dispose(store)


def test_cutoff_at_read_instant_shares_the_live_key(runner) -> None:
    runner.step(F06["steps"][0])
    runner.step(F06["steps"][1])
    store = PostgresAssessmentStore(URL)
    try:
        with snapshot(runner.engine) as c:
            read_at = c.execute(text("SELECT now()")).scalar_one()
            frm, to = F06_DAY, F06_DAY + timedelta(days=1)
            with read_scope.scope("ch5c-r3") as sc, read_scope.snapshot(c, read_at):
                at = store.select_dispatch_days_on(c, runner.tenant, runner.site, frm, to, read_at)
                again = store.select_dispatch_days_on(c, runner.tenant, runner.site, frm, to, read_at + timedelta(1))
                below = store.select_dispatch_days_on(c, runner.tenant, runner.site, frm, to,
                                                      read_at - timedelta(microseconds=1))
                names = sc.names()
            with read_scope.scope("ch5c-r3-unbound"):
                unshared = store.select_dispatch_days_on(c, runner.tenant, runner.site, frm, to, read_at)
            with read_scope.scope("ch5c-r3-unbound-live"):  # computed with its own cutoff, never memo-shared
                live = store.select_dispatch_days_on(c, runner.tenant, runner.site, frm, to, LIVE)
            strip = [{k: v for k, v in d.items() if k != "known_at"} for d in at]
            # one key for the two at-or-after reads, a second for the cutoff below the read instant
            assert names["assessment._window"] == 2
            assert strip == [{k: v for k, v in d.items() if k != "known_at"} for d in again]
            assert strip == [{k: v for k, v in d.items() if k != "known_at"} for d in live]  # the R3 equivalence
            assert at == unshared  # the normalised (live-keyed) dict equals the unbound read at the same cutoff
            assert len(below) == 1
    finally:
        pg_harness.dispose(store)


@pytest.mark.skipif(not CLONE, reason="ASSETOPS_CH5C_CLONE_URL is not set (L2m clone parity)")
def test_clone_parity_over_every_site_and_story_day() -> None:
    eng = create_engine(CLONE)
    store = PostgresAssessmentStore(CLONE)
    try:
        with eng.connect() as c:
            sites = c.execute(text("SELECT tenant_id, id FROM site ORDER BY id")).all()
            lo, hi = c.execute(text("SELECT min(window_start), max(window_end) FROM analytic_run_selection")).one()
        assert sites and lo is not None
        checked = 0
        with snapshot(eng) as c:
            read_at = c.execute(text("SELECT now()")).scalar_one()
            for tenant, site in sites:
                for k in (read_at, lo + (hi - lo) / 2, LIVE):
                    batched, each = both(store, c, tenant, site, lo - timedelta(hours=6), hi, k)
                    assert batched == each, (site, k)
                    checked += len(batched)
        assert checked > 0
        print(f"clone parity: {checked} day dicts equal")
    finally:
        pg_harness.dispose(store)
        eng.dispose()
