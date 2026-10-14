"""S4-02c phase 2: the evidence no-op predicate, the retry schedule and the runner's selection (no database).

Packet `tasks/S4-02c-evidence-consequence-work.md` items 3-4 and re-review N1/N4, phase 1 review L2.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from assetops_backend.financials.recompute import (
    ERROR_EVIDENCE_LOCATOR_NOT_IN_SITE, ERROR_EVIDENCE_NOT_ACCEPTED, NO_OP_ASSET, NO_OP_OUTSIDE_CANDIDATE_TIME,
    NO_OP_ROLE, NO_OP_SUPERSEDED, ConsequenceRecomputeWorker, evidence_no_op, retry_due_at)

T = datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc)
GEN = "11111111-1111-1111-1111-111111111111"


def m(minutes: int) -> datetime:
    return T + timedelta(minutes=minutes)


def target(start=5, end=10, *, role="generator_power", asset=GEN, revision_no=1, latest=1, spans=((5, 30),),
           quality="GOOD"):
    return {"evidence": {"role": role, "asset_id": asset, "interval_start": None if start is None else m(start),
                         "interval_end": None if end is None else m(end), "accepted": True, "quality": quality},
            "revision": {"revision_no": revision_no, "latest_revision_no": latest, "generator_asset_id": GEN,
                         "claim": {"candidate_spans": [{"start": m(a).isoformat(), "end": m(b).isoformat()}
                                                       for a, b in spans]}}}


class TestNoOpPredicate:
    def test_only_the_cases_quantify_cannot_examine_are_no_ops(self) -> None:
        assert evidence_no_op(target()) is None
        assert evidence_no_op(target(revision_no=1, latest=2)) == NO_OP_SUPERSEDED
        assert evidence_no_op(target(role="pv_power")) == NO_OP_ROLE
        assert evidence_no_op(target(asset="22222222-2222-2222-2222-222222222222")) == NO_OP_ASSET
        assert evidence_no_op(target(asset=None)) == NO_OP_ASSET
        assert evidence_no_op(target(start=None, end=None)) == NO_OP_OUTSIDE_CANDIDATE_TIME

    def test_quality_never_makes_a_no_op(self) -> None:
        """Re-review N1: a non-GOOD same-asset mean in Candidate time changes `examined_evidence_ids`."""
        for quality in ("SUSPECT", "UNAVAILABLE"):
            assert evidence_no_op(target(quality=quality)) is None

    def test_strict_half_open_overlap_with_merged_positive_width_candidate_spans(self) -> None:
        assert evidence_no_op(target(0, 5)) == NO_OP_OUTSIDE_CANDIDATE_TIME  # ends at the span start
        assert evidence_no_op(target(30, 35)) == NO_OP_OUTSIDE_CANDIDATE_TIME  # starts at the span end
        assert evidence_no_op(target(29, 31)) is None
        # Touching spans merge; a gap between components holds no Candidate time.
        spans = ((5, 10), (10, 15), (20, 25))
        assert evidence_no_op(target(9, 11, spans=spans)) is None
        assert evidence_no_op(target(15, 20, spans=spans)) == NO_OP_OUTSIDE_CANDIDATE_TIME
        # A zero-width span holds no time, even for a reading spanning its instant.
        assert evidence_no_op(target(40, 50, spans=((5, 30), (45, 45)))) == NO_OP_OUTSIDE_CANDIDATE_TIME
        assert evidence_no_op(target(5, 10, spans=())) == NO_OP_OUTSIDE_CANDIDATE_TIME


def test_retry_schedule_is_1_2_4_8_16_then_16_minutes_without_a_cap() -> None:
    assert [(retry_due_at(T, n) - T) // timedelta(minutes=1) for n in range(1, 9)] == [1, 2, 4, 8, 16, 16, 16, 16]


class Store:
    def __init__(self, pending, target=None, claimed=True) -> None:
        self.pending, self.target, self.claimed = pending, target, claimed
        self.attempts: list[dict] = []
        self.claims = 0

    @contextmanager
    def claim_site(self, tenant_id, site_id):
        self.claims += 1
        yield self.claimed

    def pending_work(self, tenant_id, site_id):
        return list(self.pending)

    def evidence_target(self, *args):
        return self.target

    def latest_revisions_overlapping(self, *args, **kw):
        raise AssertionError("evidence work fell through to the assumption-range recompute")

    def load_input(self, *args, **kw):
        raise AssertionError("refused evidence work derived a consequence")

    def append(self, *args, **kw):
        raise AssertionError("refused evidence work appended a consequence")

    def record_attempt(self, tenant_id, site_id, work_id, **kw) -> int:
        self.attempts.append({"work_id": work_id, **kw})
        return len(self.attempts)


def work(enqueued: int, *, last_attempt_no=None, last_finished: int | None = None, cause="EVIDENCE_ACCEPTED"):
    return {"id": uuid4(), "cause": cause, "finding_id": uuid4(), "finding_revision_id": uuid4(),
            "accepted_evidence_id": uuid4(), "enqueued_at": m(enqueued), "last_attempt_no": last_attempt_no,
            "last_finished_at": None if last_finished is None else m(last_finished)}


class TestRunnerSelection:
    def test_a_claimed_site_is_skipped_and_nothing_is_touched(self) -> None:
        store = Store([work(0)], claimed=False)
        report = ConsequenceRecomputeWorker(store, None).run(uuid4(), uuid4(), 10, now=m(60))
        assert (report.claimed, report.outcomes, store.attempts) == (False, [], [])

    def test_due_selection_eligibility_order_limit_and_counts(self) -> None:
        fresh_old = work(0)
        failed_due = work(1, last_attempt_no=1, last_finished=2)  # due at 3
        failed_early = work(1, last_attempt_no=3, last_finished=8)  # due at 12: deferred at now=10
        fresh_new = work(5)
        store = Store([fresh_old, failed_due, failed_early, fresh_new],
                      target=target(revision_no=1, latest=2))
        report = ConsequenceRecomputeWorker(store, None).run(uuid4(), uuid4(), 2, now=m(10))
        assert [o.work_id for o in report.outcomes] == [fresh_old["id"], failed_due["id"]]
        assert report.counts() == {"selected": 2, "appended": 0, "replayed": 0, "no_op": 2, "failed": 0,
                                   "deferred": 1, "backlog": 2}
        assert [a["no_op_reason"] for a in store.attempts] == [NO_OP_SUPERSEDED, NO_OP_SUPERSEDED]
        assert all(a["succeeded"] and a["consequence_revision_ids"] == () for a in store.attempts)
        # Later: the newer fresh row became eligible (5) before the 16-minute retry of a fifth failure (8 + 16).
        store = Store([work(0, last_attempt_no=5, last_finished=8), fresh_new], target=target(latest=2))
        report = ConsequenceRecomputeWorker(store, None).run(uuid4(), uuid4(), 1, now=m(30))
        assert [o.work_id for o in report.outcomes] == [fresh_new["id"]]

    def test_never_attempted_work_is_due_whatever_the_clock(self) -> None:
        store = Store([work(60)], target=target(latest=2))
        assert ConsequenceRecomputeWorker(store, None).run(uuid4(), uuid4(), 1, now=m(0)).counts()["selected"] == 1

    def test_the_injected_clock_is_used_when_no_now_is_passed(self) -> None:
        store = Store([work(0, last_attempt_no=1, last_finished=0)], target=target(latest=2))
        w = ConsequenceRecomputeWorker(store, None, clock=lambda: m(0) + timedelta(seconds=59))
        assert w.run(uuid4(), uuid4(), 5).counts()["deferred"] == 1
        w = ConsequenceRecomputeWorker(store, None, clock=lambda: m(1))
        assert w.run(uuid4(), uuid4(), 5).counts()["selected"] == 1

    def test_a_run_needs_a_positive_limit(self) -> None:
        with pytest.raises(ValueError):
            ConsequenceRecomputeWorker(Store([]), None).run(uuid4(), uuid4(), 0, now=m(0))


@pytest.mark.parametrize(("tgt", "code"), [
    ({"evidence": None, "revision": target()["revision"]}, ERROR_EVIDENCE_LOCATOR_NOT_IN_SITE),
    ({"evidence": target()["evidence"], "revision": None}, ERROR_EVIDENCE_LOCATOR_NOT_IN_SITE),
    ({"evidence": {**target()["evidence"], "accepted": False}, "revision": target()["revision"]},
     ERROR_EVIDENCE_NOT_ACCEPTED),
])
def test_an_unreadable_locator_is_a_typed_failure_without_fallback(tgt, code) -> None:
    """C4 worker half: never an unscoped lookup, assumption-range recompute or derive."""
    store = Store([], target=tgt)
    out = ConsequenceRecomputeWorker(store, None).process(uuid4(), uuid4(), work(0))
    assert (out.succeeded, out.error_code, out.no_op_reason) == (False, code, None)
    (attempt,) = store.attempts
    assert attempt["succeeded"] is False and attempt["error_code"] == code and "no_op_reason" not in attempt
