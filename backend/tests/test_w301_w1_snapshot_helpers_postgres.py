"""W3-01 Run 5 (q5) Lane A prerequisite: the connection-taking W1 reads at an explicit cutoff.

Each test persists rows before and after a cutoff through the real S2 ingestion, S3 worker, S4 matcher and
S6 Action service (the S4 `CaseRunner` and the S6 harness; no row is seeded), then calls the `*_on` helpers on
ONE caller-owned REPEATABLE READ connection and checks that only rows recorded by the cutoff are selected and
that the helpers leave the caller's transaction open. Requires ASSETOPS_TEST_DATABASE_URL (backend/TESTING.md).
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import SPEC, URL, CaseRunner  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s6_action_store_postgres import CASES, T_ACCEPT, harness, run_case

    import pg_harness
    from assetops_backend.actions.adapters.postgres_action_store import PostgresActionStore
    from assetops_backend.analytics import dispatch_v3
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.adapters.postgres_finding_store import FindingPinRefused, PostgresFindingStore
    from assetops_backend.analytics.dispatch_read import DispatchReadService
    from assetops_backend.analytics.finding_episode import DOMAIN

ANALYTIC = "dispatch"
F06 = next(c for c in SPEC["cases"] if c["case_id"] == "F06")
F06_DAY = datetime(2026, 10, 15, tzinfo=timezone.utc)
LIVE = datetime(9000, 1, 1, tzinfo=timezone.utc)


@pytest.fixture()
def runner(store, engine):  # noqa: F811
    owned = CaseRunner(store, engine)
    yield owned
    pg_harness.dispose(owned.findings)


@contextmanager
def caller_snapshot(engine):  # noqa: F811
    """The caller's one REPEATABLE READ transaction; every helper must run inside it and leave it open."""
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
        with c.begin():
            yield c
            assert c.in_transaction(), "a helper ended the caller's transaction"


def head_ids(snap: dict) -> set:
    return {h["finding_revision_id"] for h in snap["heads"]}


def test_finding_snapshot_on_excludes_later_revision_merge_and_match(runner) -> None:
    for step in F06["steps"][:6]:  # deliver, assess, match, release, assess, match
        runner.step(step)
    cutoff = runner.now
    before = runner.findings.index_snapshot(runner.tenant, runner.site, DOMAIN, ANALYTIC)
    assert before["heads"] and before["match_pass"] and before["merges"] == []
    for step in F06["steps"][6:]:  # release, assess, match: later revisions, a merge, a later pass
        runner.step(step)
    store = PostgresFindingStore(URL)
    try:
        with caller_snapshot(runner.engine) as c:
            then = store.index_snapshot_on(c, runner.tenant, runner.site, DOMAIN, ANALYTIC, cutoff)
            now = store.index_snapshot_on(c, runner.tenant, runner.site, DOMAIN, ANALYTIC, LIVE)
            # the rows after the cutoff exist (the proof is not vacuous) ...
            assert now["merges"] and head_ids(now) != head_ids(before)
            assert now["match_pass"]["match_pass_id"] != before["match_pass"]["match_pass_id"]
            assert now["selection_seqs"] != before["selection_seqs"]
            # ... and the cutoff read selects exactly what was recorded by then
            assert head_ids(then) == head_ids(before) and then["merges"] == []
            assert all(h["merged_into_finding_id"] is None for h in then["heads"])
            assert then["match_pass"] == before["match_pass"]
            assert then["deferred_windows"] == before["deferred_windows"]
            assert then["selection_seqs"] == before["selection_seqs"] and then["known_at"] == cutoff
            assert set(then["selected_runs"]) == set(then["selection_seqs"])
            assert "fence" not in then  # a current writer fence is never a historical matcher proof
            # exact pinned lineage: the before-cutoff pins read like the W1 wrapper; later or missing pins refuse
            pins = sorted(head_ids(before), key=str)
            assert store.index_lineage_on(c, runner.tenant, runner.site, pins, cutoff) == \
                runner.findings.index_lineage(runner.tenant, runner.site, pins)
            later = sorted(head_ids(now) - head_ids(before), key=str)
            with pytest.raises(FindingPinRefused) as refused:
                store.index_lineage_on(c, runner.tenant, runner.site, [pins[0], later[0]], cutoff)
            assert refused.value.later == [str(later[0])] and refused.value.missing == []
            missing = uuid4()
            with pytest.raises(FindingPinRefused) as refused:
                store.index_lineage_on(c, runner.tenant, runner.site, [missing], LIVE)
            assert refused.value.missing == [str(missing)]
            # the live fence on `c` is the existing writer fence
            assert store.fence_on(c, runner.tenant, runner.site, ANALYTIC) == \
                runner.findings.fence(runner.tenant, runner.site, ANALYTIC)
        # the W1 wrapper is unchanged: the live index with the writer fence
        wrapper = runner.findings.index_snapshot(runner.tenant, runner.site, DOMAIN, ANALYTIC)
        assert head_ids(wrapper) == head_ids(now) and wrapper["merges"] == now["merges"]
        assert wrapper["match_pass"] == now["match_pass"] and "selected_runs" not in wrapper
        assert wrapper["fence"] == runner.findings.fence(runner.tenant, runner.site, ANALYTIC)
    finally:
        pg_harness.dispose(store)


def test_dispatch_days_on_selects_each_day_at_cutoff(runner, monkeypatch) -> None:
    runner.step(F06["steps"][0])  # deliver: the recompute job is recorded
    queued = runner.now
    runner.step(F06["steps"][1])  # assess: the job completes and selects the day's first run
    cutoff = runner.now
    for step in F06["steps"][3:5]:  # release, assess: a later selection of the same day
        runner.step(step)
    present = runner.now
    # The fixture clock runs ahead of the database clock; the transaction time is pinned to the fixture's present
    # so that both cutoffs above are historical (below it a job's present status is not its status then).
    monkeypatch.setattr(PostgresAssessmentStore, "_transaction_time", staticmethod(lambda c: present))
    store = PostgresAssessmentStore(URL)
    frm, to = F06_DAY - timedelta(hours=12), F06_DAY + timedelta(days=1, hours=6)
    try:
        with caller_snapshot(runner.engine) as c:
            then = store.select_dispatch_days_on(c, runner.tenant, runner.site, frm, to, cutoff)
            now = store.select_dispatch_days_on(c, runner.tenant, runner.site, frm, to, present)
            early = store.select_dispatch_days_on(c, runner.tenant, runner.site, frm, to, queued)
            runs = c.execute(text(
                "SELECT run_id, selected_at FROM analytic_run_selection WHERE site_id = :s AND window_start = :w "
                "ORDER BY seq"), {"s": runner.site, "w": F06_DAY}).all()
            assert store.select_dispatch_days_on(c, runner.tenant, runner.site, to, frm, LIVE) == []
        # one result per UTC day intersecting [from, to), in day order
        for days in (then, now, early):
            assert [d["day"] for d in days] == [(F06_DAY + timedelta(days=i)).date() for i in (-1, 0, 1)]
            assert [d["window_start"] for d in days] == [F06_DAY + timedelta(days=i) for i in (-1, 0, 1)]
        assert len(runs) == 2 and runs[0][1] <= cutoff < runs[1][1]  # a selection on each side of the cutoff
        # the neighbouring days are explicitly unselected, never omitted
        for days in (then, now):
            for d in (days[0], days[2]):
                assert d["available"] and d["selection"] is None and d["run_id"] is None
                assert d["assessment_revision_ids"] == [] and d["status"] == "UNASSESSED"
        # the cutoff day keeps the selection recorded by then, not the later one
        day = then[1]
        assert day["available"] and day["status"] == "CURRENT" and day["known_at"] == cutoff
        assert day["run_id"] == runs[0][0] and day["selection"]["run_id"] == runs[0][0]
        assert day["selection"]["selected_at"] <= cutoff and day["jobs"] == []
        assert day["assessment_revision_ids"] and day["window_assessment_revision_id"] is not None
        assert now[1]["run_id"] == runs[1][0] and now[1]["accepted_reading_count"] > day["accepted_reading_count"]
        # the live day matches the S3 read of the same day
        live = DispatchReadService(store).window(runner.tenant, runner.site, F06_DAY.date())
        assert live["selection"]["run_id"] == now[1]["run_id"] and live["status"] == now[1]["status"]
        # before the job finished, it was outstanding (completion selected it only afterwards)
        gap = early[1]
        assert gap["available"] is True and gap["selection"] is None and gap["run_id"] is None
        assert gap["status"] == "PENDING" and gap["unavailable_reasons"] == []
        assert [j["status"] for j in gap["jobs"]] == ["PENDING"] and len(gap["jobs"]) == 1
        job_id = gap["jobs"][0]["id"]
        assert any(r.startswith("RECOMPUTE_OUTSTANDING") and str(job_id) in r for r in gap["status_reasons"])
    finally:
        pg_harness.dispose(store)


def test_dispatch_days_on_done_empty_job_is_unavailable(runner, monkeypatch) -> None:
    runner.step(F06["steps"][0])  # deliver: the recompute job is recorded, still unselected
    queued = runner.now
    present = queued + timedelta(hours=1)
    monkeypatch.setattr(PostgresAssessmentStore, "_transaction_time", staticmethod(lambda c: present))
    with runner.engine.begin() as c:  # a DONE job with zero selections: its completion time is not recorded
        assert c.execute(text("UPDATE recompute_job SET status = 'DONE' WHERE site_id = :s"),
                         {"s": runner.site}).rowcount >= 1
        assert c.execute(text("SELECT count(*) FROM analytic_run_selection WHERE site_id = :s"),
                         {"s": runner.site}).scalar_one() == 0
    store = PostgresAssessmentStore(URL)
    try:
        with caller_snapshot(runner.engine) as c:
            days = store.select_dispatch_days_on(c, runner.tenant, runner.site, F06_DAY,
                                                 F06_DAY + timedelta(days=1), queued)
        day = days[0]
        assert day["available"] is False and day["status"] is None and day["selection"] is None
        assert any(r.startswith("JOB_STATE_AT_CUTOFF_UNKNOWN") for r in day["unavailable_reasons"])
    finally:
        pg_harness.dispose(store)


def test_action_window_on_excludes_later_event(runner) -> None:
    run_case(runner, CASES["F01"])
    h = harness(runner)
    try:
        finding = h.findings()["2026-10-06"]
        proposal = h.recommendation(finding).json()["proposal"]
        accepted = h.accept(finding, proposal)
        assert accepted.status_code == 201, accepted.text
        action_id = accepted.json()["action"]["action_id"]
        h.clock.at = T_ACCEPT + timedelta(hours=2)
        # occurred one hour after acceptance, recorded two hours after: recorded_at is the selection time
        observed = h.observe(action_id, T_ACCEPT + timedelta(hours=1), "observe-0001")
        assert observed.status_code == 201, observed.text
        start, end = T_ACCEPT - timedelta(days=1), T_ACCEPT + timedelta(days=1)
        cutoff = T_ACCEPT + timedelta(hours=1, minutes=30)
        store = PostgresActionStore(URL)
        try:
            with caller_snapshot(runner.engine) as c:
                then = store.site_window_on(c, runner.tenant, runner.site, start, end, cutoff)
                now = store.site_window_on(c, runner.tenant, runner.site, start, end, LIVE)
                none = store.site_window_on(c, runner.tenant, runner.site, start, end,
                                            T_ACCEPT - timedelta(seconds=1))
                outside = store.site_window_on(c, runner.tenant, runner.site, end, end + timedelta(days=1), LIVE)
            assert [str(a["id"]) for a in then["actions"]] == [str(action_id)]
            assert [e["kind"] for e in now["events"]] == ["ACCEPTED", "OBSERVED"]  # the later event exists
            assert [e["kind"] for e in then["events"]] == ["ACCEPTED"]
            assert all(e["recorded_at"] <= cutoff for e in then["events"])
            assert none == {"actions": [], "events": []} and outside == {"actions": [], "events": []}
            # the W1 wrapper is the live read in the same shape
            assert store.site_window(runner.tenant, runner.site, start, end) == now
        finally:
            pg_harness.dispose(store)
    finally:
        h.close()
