"""W4-03 unit 4: the opportunity lease loop and projection (`.agent/W4-03-build-spec.md` closure 2 Q4, closure 4
S2/S3/S5/S7/S20, u3 "Unit 4 dry-read", "Unit-4 rulings (u4)"): exact five-day selection, unchanged reselection,
late evidence, missing day, job window mismatch and interrupted lease retry.
"""

from __future__ import annotations

import os
from datetime import timedelta

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_w402_reads_postgres import CODE, DAYS, ZONE, _ingest, _midnight, _reconcile, _setup
    from test_w403_scenarios_postgres import mg

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.assessment_ports import Window
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import link_rows_on
    from assetops_backend.mini_decisions import projection
    from assetops_backend.mini_decisions.store import PostgresMiniDecisionStore
    from assetops_backend.mini_decisions.worker import MiniOpportunityWorker
    from assetops_backend.mini_depth import projection as mini_projection
    from assetops_backend.mini_depth.inputs import load_hour_inputs, local_noon
    from assetops_backend.mini_depth.read import MiniDepthRead, renewable_revisions
    from assetops_backend.mini_depth.store import PostgresMiniDepthStore

STUDY = (_midnight(DAYS[0]), _midnight(DAYS[-1] + timedelta(days=1))) if URL else None


def worker(engine, **options) -> "MiniOpportunityWorker":
    return MiniOpportunityWorker(PostgresAssessmentStore(URL), PostgresMiniDecisionStore(engine),
                                 MiniDepthRead(engine, link_rows_on), **options)


def counts(engine) -> tuple[int, int, int, int, int]:
    with engine.connect() as c:
        return tuple(c.execute(text(
            "SELECT (SELECT count(*) FROM recompute_job WHERE domain = 'mini_opportunity'), "
            "(SELECT count(*) FROM mini_opportunity), (SELECT count(*) FROM mini_opportunity_revision), "
            "(SELECT count(*) FROM mini_opportunity_selection), (SELECT count(*) FROM mini_opportunity_evidence)"
        )).one())


def revisions(engine) -> list:
    with engine.connect() as c:
        return c.execute(text(
            "SELECT r.id, r.revision_no, r.selected_hours, r.result, r.input_sha256, r.producer_id, r.source_job_id, "
            "r.model_version, o.first_day, o.last_day FROM mini_opportunity_revision r JOIN mini_opportunity o "
            "ON o.id = r.opportunity_id ORDER BY r.revision_no")).all()


def pins(engine, t, s, days=DAYS) -> list:
    """The selected renewable heads `(seq, revision id, decision, accepted IDs)` of each day."""
    with PostgresMiniDecisionStore(engine).snapshot() as c:
        return projection.day_heads(PostgresMiniDecisionStore(engine), c, t, s, ZONE, days)


def reselect_same(engine, t, s, heads) -> None:
    """Closure 4 S5's harmless rerun: each day's same inputs at its stored cutoff reuse the stored W4-02 revision and
    append only a new selection seq."""
    mini = PostgresMiniDepthStore(engine)
    with mini.snapshot() as c:
        for h in heads:
            cutoff = renewable_revisions(c, t, s, [h.mini_revision_id])[h.mini_revision_id]["knowledge_cutoff"]
            inputs = load_hour_inputs(c, t, s, local_noon(h.local_day, ZONE), cutoff)
            mini.append_selection(mini_projection.project("renewable", inputs), job_id=None, backfill=True,
                                  connection=c)


def project(engine, w=None):
    w = w or worker(engine)
    queued = w.reconcile(CODE, *STUDY)
    return queued, w.run_pending(scan=False)


def test_exact_five_day_selection_and_unchanged_reselection(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    queued, outcomes = project(engine)
    assert [q.action for q in queued] == ["INSERTED"]
    [done] = outcomes
    assert (done.status, done.first_day, done.last_day) == ("DONE", DAYS[0], DAYS[-1])
    assert done.projected.selection_seq is not None and not done.projected.reused
    [rev] = revisions(engine)
    heads = pins(engine, t, s)
    assert (rev.revision_no, rev.producer_id, rev.model_version, rev.source_job_id) == (
        1, "mini-opportunity/1", "mini-opportunity/1", done.job_id)
    assert (rev.first_day, rev.last_day) == (DAYS[0], DAYS[-1])
    assert rev.input_sha256 == projection.input_sha256(t, s, DAYS[0], DAYS[-1], heads) == done.projected.input_sha256
    # The five pins are the exact selected tuples, seq included.
    assert [(p["local_day"], p["selection_seq"], p["mini_revision_id"], p["evidence_ids"])
            for p in rev.selected_hours] == [(h.local_day.isoformat(), h.selection_seq, h.mini_revision_id,
                                              list(h.evidence_ids)) for h in heads]
    assert rev.selected_hours[0]["window_from"] == projection.iso(local_noon(DAYS[0], ZONE).start)
    # The MG integration fixture's actual outcome: 4 ELIGIBLE + the 6 Oct EXCLUDED day.
    result = rev.result
    assert set(result) == {"status", "assessed_days", "eligible_days", "headroom_kw", "day_rows", "limitations"}
    assert [r["decision"] for r in result["day_rows"]] == [h.decision for h in heads]
    assert (result["assessed_days"], result["eligible_days"]) == (5, 4)
    assert result == projection.frozen_result(heads, result_class(engine, t, s, heads))
    with engine.connect() as c:
        linked = sorted(str(r[0]) for r in c.execute(text("SELECT evidence_id FROM mini_opportunity_evidence")))
        assert c.execute(text("SELECT status FROM recompute_job WHERE id = :j"), {"j": done.job_id}).scalar() == "DONE"
    assert linked == sorted({i for h in heads for i in h.evidence_ids})
    before = counts(engine)
    assert before[:4] == (1, 1, 1, 1)

    # An unchanged W4-02 rerun appends new selection seqs only: zero new job, revision or selection.
    reselect_same(engine, t, s, heads)
    reselected = pins(engine, t, s)
    assert [h.selection_seq for h in reselected] != [h.selection_seq for h in heads]
    assert [h.hash_day() for h in reselected] == [h.hash_day() for h in heads]
    w = worker(engine)
    # Only the 10 Oct noon is retained at this instant, so the scan considers exactly this study.
    w.jobs.test_clock_override = lambda: local_noon(DAYS[-1], ZONE).start + timedelta(days=5)
    assert w.enqueue_from_selections(t, s) == [] and w.run_pending(scan=False) == []
    assert counts(engine) == before
    # The unchanged study is not queued again by reconcile either.
    assert w.reconcile(CODE, *STUDY) == []
    # Resume: a duplicate job for the same study reuses the revision and appends no selection.
    w.jobs.enqueue_opportunity_job(t, s, DAYS[0], DAYS[-1], Window(*STUDY))
    [again] = w.run_pending(scan=False)
    assert (again.status, again.projected.reused, again.projected.selection_seq) == ("DONE", True, None)
    assert again.projected.revision_id == done.projected.revision_id
    assert counts(engine)[1:] == before[1:] and counts(engine)[0] == 2


def result_class(engine, t, s, heads):
    present = [h for h in heads if h.mini_revision_id]
    with PostgresMiniDecisionStore(engine).snapshot() as c:
        blocks = MiniDepthRead(engine, link_rows_on).provenance_blocks(
            c, tenant_id=t, site_id=s, selected_revision_ids=[h.mini_revision_id for h in present],
            selected_evidence_ids=[i for h in present for i in h.evidence_ids], pending_evidence_ids=None)
    return blocks["selected_source_provenance"]["classification"]


def test_late_evidence_changes_the_head_and_missing_day(store, engine) -> None:  # noqa: F811
    installed, t, s = _setup(store, engine)
    _reconcile(engine, DAYS[1:])  # selected before any evidence exists; 6 Oct has no selection
    _, [first] = project(engine)
    [r1] = revisions(engine)
    assert first.status == "DONE" and r1.result["status"] == "UNKNOWN"
    assert r1.result["day_rows"][0] == {"local_day": "2026-10-06", "decision": None, "opportunity_kwh": None,
                                        "constraints": [], "evidence_ids": []}
    assert r1.result["limitations"][0] == {"code": "RENEWABLE_DAY_MISSING", "evidence_ids": []}
    assert r1.selected_hours[0]["selection_seq"] is None and r1.selected_hours[0]["mini_revision_id"] is None
    assert r1.result["headroom_kw"] is None
    # Late evidence and a new W4-02 selection change the physical identity: a new job, revision 2 and selection.
    _ingest(engine, installed)
    _reconcile(engine, DAYS)
    queued, [second] = project(engine)
    assert [q.action for q in queued] == ["INSERTED"] and second.status == "DONE"
    r1_again, r2 = revisions(engine)
    assert r1_again.result == r1.result and r2.revision_no == 2 and r2.input_sha256 != r1.input_sha256
    assert (r2.result["assessed_days"], r2.result["eligible_days"]) == (5, 4)
    assert counts(engine)[:4] == (2, 1, 2, 2)


def test_job_window_mismatch_refuses_without_history(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    w = worker(engine, max_attempts=1)
    # A four-day window is not an exact five-day study; the job fails and nothing is written.
    four = Window(STUDY[0], STUDY[1] - timedelta(days=1))
    w.jobs.enqueue_opportunity_job(t, s, DAYS[0], DAYS[-2], four)
    [out] = w.run_pending(scan=False)
    assert out.status == "FAILED" and "five-day" in out.error
    assert counts(engine)[1:4] == (0, 0, 0)
    # The store refuses a revision whose job window is not the study, too.
    good = w.jobs.enqueue_opportunity_job(t, s, DAYS[0], DAYS[-1], Window(*STUDY))[1]
    store_ = PostgresMiniDecisionStore(engine)
    from assetops_backend.mini_decisions.store import MiniDecisionWriteRefused
    with pytest.raises(MiniDecisionWriteRefused, match="exactly this five-day study"):
        with store_.transaction() as c:
            store_._check_job(c, t, s, good, backfill=False, study_window=(four.start, four.end))


def test_interrupted_lease_retries_once(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    w = worker(engine)
    w.reconcile(CODE, *STUDY)
    # A crashed worker leased the job and never settled it; the lease expires and the next pass projects it once.
    lease = w.jobs.lease_opportunity_job(timedelta(seconds=1))
    assert lease is not None and counts(engine)[1:4] == (0, 0, 0)
    w._test_clock = lambda: lease.knowledge_cutoff + timedelta(minutes=1)
    [out] = w.run_pending(scan=False)
    assert out.status == "DONE" and out.job_id == lease.job_id
    assert counts(engine)[:4] == (1, 1, 1, 1)
    # The stale lease cannot settle afterwards.
    from assetops_backend.analytics.assessment_ports import LeaseLost
    with pytest.raises(LeaseLost):
        with PostgresMiniDecisionStore(engine).transaction() as c:
            w.jobs.settle_opportunity_job(c, lease)
