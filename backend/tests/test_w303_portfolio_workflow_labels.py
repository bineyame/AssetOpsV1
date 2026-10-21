"""W3-03 run 1b: closure 5 S7 `workflow_label` literals and precedence, and the r1a Q-1a-1 exact-origin Action
comparator (pure)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from assetops_backend.estate.portfolio import ActionSelectionError, _action_for, portfolio_row, workflow_label

T0 = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
FINDING, REV, OTHER_REV = "f-1", "r-1", "r-2"


def action(aid="a-1", *, app="ACCEPTED", resolution=None, outcome=None, window=False, at=T0, rev=REV):
    return {"action_id": aid, "action_title": f"Action {aid}", "selected_event_id": f"e-{aid}",
            "source_finding_id": FINDING, "source_finding_revision_id": rev, "application_state": app,
            "resolution_state": resolution, "verification_outcome": outcome,
            "_raw": {"_verification_window": window, "_selected_recorded_at": at, "_plans": [], "_outcome_id": None}}


def finding_row(rev=REV):
    return {"finding_id": FINDING, "finding_revision_id": rev}


def test_all_seven_literal_labels_and_precedence() -> None:
    assert workflow_label(None) == "Recommendation not accepted"
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
    # A different revision of the same Finding never joins.
    assert _action_for(finding_row(OTHER_REV), [older, newer]) is None
    assert _action_for(finding_row(OTHER_REV), [action("c-3", rev=OTHER_REV), newer])["action_id"] == "c-3"
    # Absence of the selected event time is an internal selection error, never a silent fallback.
    missing = action("a-0")
    missing["_raw"].pop("_selected_recorded_at")
    with pytest.raises(ActionSelectionError):
        _action_for(finding_row(), [missing, newer])
