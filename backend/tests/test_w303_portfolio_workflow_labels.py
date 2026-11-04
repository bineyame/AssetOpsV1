"""W3-03 run 1b: closure 5 S7 `workflow_label` literals and precedence, and the r1a Q-1a-1 exact-origin Action
comparator (pure)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from assetops_backend.estate.portfolio import (
    ActionSelectionError, _action_for, portfolio_row, progress, workflow_label)

T0 = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
FINDING, REV, OTHER_REV = "f-1", "r-1", "r-2"


def action(aid="a-1", *, app="ACCEPTED", resolution=None, outcome=None, window=False, at=T0, rev=REV, thread=None):
    # CH-5a2 B3: Actions join Finding rows on their thread only; by default each origin revision has its own thread.
    return {"action_id": aid, "action_title": f"Action {aid}", "selected_event_id": f"e-{aid}",
            "_thread_id": thread or f"t-{rev}", "_segment_no": 1,
            "source_finding_id": FINDING, "source_finding_revision_id": rev, "application_state": app,
            "resolution_state": resolution, "verification_outcome": outcome,
            "_raw": {"_verification_window": window, "_selected_recorded_at": at, "_plans": [], "_outcome_id": None}}


def finding_row(rev=REV, thread=None):
    return {"finding_id": FINDING, "finding_revision_id": rev, "_thread": {"id": thread or f"t-{rev}", "segment_no": 1}}


def test_all_seven_literal_labels_and_precedence() -> None:
    assert workflow_label(None) == "No action agreed yet"
    # Verified wins over an open window and an applied state.
    assert workflow_label(action(app="APPLIED", resolution="RESOLVED", outcome="VERIFIED", window=True)) == "Verified"
    assert workflow_label(action(app="APPLIED", resolution="RESOLUTION_WITHDRAWN", window=True)) == \
        "Resolution withdrawn"
    # An active plan with a null outcome is pending; the window wins over the application state.
    assert workflow_label(action(app="APPLIED", window=True)) == "Outcome pending"
    # A null outcome without an active plan is not pending: the application state decides.
    assert workflow_label(action(app="PENDING", window=False)) == "Pending"
    assert workflow_label(action(app="APPLIED", window=False)) == "Applied"
    # A non-VERIFIED terminal outcome or no application state is "No action yet", never "Outcome pending".
    assert workflow_label(action(app="NONE_AT_CUTOFF")) == "No action yet"
    # r1b Q-1b-2: a non-VERIFIED terminal outcome does not override a selected application fact (first match).
    assert workflow_label(action(app="APPLIED", resolution="RESOLVED", outcome="NOT_VERIFIED")) == "Applied"
    assert workflow_label(action(app="APPLIED", resolution="RESOLVED", outcome="NOT_VERIFIED", window=True)) ==         "Applied"
    assert workflow_label(action(app="PENDING", resolution="RESOLVED", outcome="NOT_VERIFIED")) == "Pending"
    # Active plan, null outcome, no application state: Outcome pending. Null outcome without a plan: not pending.
    assert workflow_label(action(app="NONE_AT_CUTOFF", window=True)) == "Outcome pending"
    assert workflow_label(action(app="NONE_AT_CUTOFF", window=False)) == "No action yet"
    # Withdrawal wins over PENDING application and any outcome.
    assert workflow_label(action(app="PENDING", resolution="RESOLUTION_WITHDRAWN", outcome="VERIFIED")) ==         "Resolution withdrawn"
    # With no application state, a non-VERIFIED terminal outcome is "No action yet".
    assert workflow_label(action(app="NONE_AT_CUTOFF", resolution="RESOLVED", outcome="NOT_VERIFIED")) == \
        "No action yet"
    assert workflow_label(action(app="FAILED")) == "No action yet"


def test_two_actions_one_exact_origin_latest_event_then_id_tie() -> None:
    older, newer = action("a-1", at=T0), action("z-9", at=T0 + timedelta(minutes=5))
    # The newer selected event wins even though its ID sorts later.
    assert _action_for(finding_row(), [older, newer])["action_id"] == "z-9"
    assert _action_for(finding_row(), [newer, older])["action_id"] == "z-9"
    # Equal selected event times choose the smaller action_id.
    tied = [action("b-2", at=T0), action("a-1", at=T0)]
    assert _action_for(finding_row(), tied)["action_id"] == "a-1"
    # r1b: both matching Actions (and one on another origin revision) remain in unpaged `progress.rows`; only the
    # Finding cell uses the tie. Order is (recorded_at desc, action_id).
    for a in (older, newer, *tied):
        a["action_code"], a["_raw"]["_plans"] = a["action_id"].upper(), []
    other = action("c-3", rev=OTHER_REV, at=T0)
    other["action_code"] = "C-3"
    covered = [({"site_id": "s"}, {"state": "CURRENT"})]
    prog, complete = progress(covered, [older, newer, other], T0 + timedelta(hours=1), {(FINDING, REV)})
    assert complete and [r["action_id"] for r in prog["rows"]] == ["z-9", "a-1", "c-3"]
    assert prog["rows"][0]["recorded_at"] == "2026-11-01T12:05:00Z" and len(prog["rows"][0]) == 11
    # r1b2 R10: the server-computed origin disclosure; c-3's origin revision is not in the selected Finding set.
    assert [r["origin_revision_selected"] for r in prog["rows"]] == [True, True, False]
    flipped, _ = progress(covered, [older, newer, other], T0 + timedelta(hours=1), {(FINDING, OTHER_REV)})
    assert [r["origin_revision_selected"] for r in flipped["rows"]] == [False, False, True]
    assert {r["origin_revision_selected"] for r in progress(covered, [older], T0, set())[0]["rows"]} == {False}
    # r1b3 P-1b-6: the disclosure depends on the full selected pair set, not on the order Actions arrive in.
    reordered, _ = progress(covered, [other, newer, older], T0 + timedelta(hours=1), {(FINDING, REV)})
    assert {r["action_id"]: r["origin_revision_selected"] for r in reordered["rows"]} == {
        r["action_id"]: r["origin_revision_selected"] for r in prog["rows"]}
    # CH-5a2 B6: `origin_selected` reads the thread (any revision): only the rows given count.
    on_thread, _ = progress(covered, [older, newer, other], T0 + timedelta(hours=1), {(FINDING, REV)}, [finding_row()])
    assert [r["origin_selected"] for r in on_thread["rows"]] == [True, True, False]
    any_rev, _ = progress(covered, [older], T0, set(), [finding_row(OTHER_REV, thread=f"t-{REV}")])
    assert [(r["origin_selected"], r["origin_revision_selected"]) for r in any_rev["rows"]] == [(True, False)]
    other_seg = finding_row()
    other_seg["_thread"]["segment_no"] = 2
    assert progress(covered, [older], T0, set(), [other_seg])[0]["rows"][0]["origin_selected"] is False
    # A row on another thread never joins; CH-5a2 B3: nor does a row with no thread (no exact-revision fallback).
    assert _action_for(finding_row(OTHER_REV), [older, newer]) is None
    assert _action_for({"finding_id": FINDING, "finding_revision_id": REV, "_thread": None}, [older]) is None
    assert _action_for(finding_row(OTHER_REV), [action("c-3", rev=OTHER_REV), newer])["action_id"] == "c-3"
    # Absence of the selected event time is an internal selection error, never a silent fallback.
    missing = action("a-0")
    missing["_raw"].pop("_selected_recorded_at")
    with pytest.raises(ActionSelectionError):
        _action_for(finding_row(), [missing, newer])
