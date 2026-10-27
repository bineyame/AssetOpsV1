"""CC-R2 (D5): `estate.placement.place` over hand-built Portfolio rows (pure; no database).

One case per rule and per reason code (`.agent/build-spec-commercial-2026-10-27.md` "CC-R2" Rules, Reason texts,
Confidence), the two precedence cases the gate names (MIXED + PRICED investigates first; Verified + PRICED is
monitored), and the six-part Portfolio cursor marker.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from assetops_backend.estate import placement
from assetops_backend.estate.placement import GROUP_LABEL, GROUPS, POLICY_VERSION, REASON_TEXT, place
from assetops_backend.estate.scope import _marker_ok

OPEN, CLOSED = None, datetime(2026, 10, 6, 9, tzinfo=timezone.utc)
OTHER = "1a2b3c4d-0000-4000-8000-000000000009"
COVERED = {"state": "CURRENT"}
UUID_A = "30000000-0000-4000-8000-000000000001"


def row(*, src="REGISTERED_SIMULATION", lifecycle="SUPPORTED", cons="UNPRICED", end=CLOSED, recurs=None,
        transition=None, mechanism=None):
    return {"lifecycle": lifecycle, "source_provenance": None if src is None else {"state": src},
            "consequence": None if cons is None else {"state": cons}, "_episode_end": end,
            "_recurs_after": recurs, "_transition": transition, "_mechanism": mechanism, "_revision_no": 1}


def action(label):
    """An Action dict whose `portfolio.workflow_label` is `label` (None = no accepted Action)."""
    if label is None:
        return None
    base = {"resolution_state": None, "verification_outcome": None, "application_state": None, "_raw": {}}
    return {**base, **{
        "Verified": {"resolution_state": "RESOLVED", "verification_outcome": "VERIFIED"},
        "Resolution withdrawn": {"resolution_state": "RESOLUTION_WITHDRAWN"},
        "Outcome pending": {"_raw": {"_verification_window": True}},
        "Pending": {"application_state": "PENDING"},
        "Applied": {"application_state": "APPLIED"},
        "No action yet": {},
    }[label]}


def placed(r, label=None, cov=COVERED, line_group=None):
    p = place(r, action(label), cov, line_group)
    return p.group, [x.code for x in p.reasons]


def test_groups_labels_and_reason_texts_are_the_fixed_policy() -> None:
    assert POLICY_VERSION == "estate-placement/1"
    assert GROUPS == ("NEEDS_INVESTIGATION", "ACT_NOW", "COMPARE_VALUE", "UNPRICED_RISK", "MONITOR")
    assert GROUP_LABEL == {"NEEDS_INVESTIGATION": "Needs investigation first", "ACT_NOW": "Act now",
                           "COMPARE_VALUE": "Compare value", "UNPRICED_RISK": "Unpriced risk", "MONITOR": "Monitor"}
    assert len(REASON_TEXT) == 20
    # CC-R1-Q1 ruling: the verified-change text says "test data", never "simulated".
    assert REASON_TEXT["VERIFIED_WATCH_RETURN"] == "Change verified on test data; watch for a return"
    assert not any("simulat" in t.lower() or "saving" in t.lower() or "saved" in t.lower()
                   for t in REASON_TEXT.values())


@pytest.mark.parametrize("facts, codes", [
    ({"src": "MIXED"}, ["EVIDENCE_SOURCE_MIXED"]),
    ({"src": "UNKNOWN"}, ["EVIDENCE_SOURCE_UNKNOWN"]),
    ({"src": None}, ["EVIDENCE_SOURCE_UNKNOWN"]),
    ({"lifecycle": "UNCONFIRMED"}, ["LIFECYCLE_UNCONFIRMED"]),
    ({"cons": "WITHHELD"}, ["CONSEQUENCE_WITHHELD"]),
    ({"src": "MIXED", "lifecycle": "UNCONFIRMED", "cons": "WITHHELD"},
     ["EVIDENCE_SOURCE_MIXED", "LIFECYCLE_UNCONFIRMED", "CONSEQUENCE_WITHHELD"]),  # all that apply, in order
])
def test_rule_1_needs_investigation(facts, codes) -> None:
    assert placed(row(**facts, end=OPEN), None) == ("NEEDS_INVESTIGATION", codes)


def test_source_key_missing_reads_as_unknown() -> None:
    r = {**row(), "source_provenance": {}}
    assert placed(r) == ("NEEDS_INVESTIGATION", ["EVIDENCE_SOURCE_UNKNOWN"])


def test_mixed_and_priced_investigates_first_not_compare_value() -> None:
    assert placed(row(src="MIXED", cons="PRICED"), "Verified", line_group="COMPARABLE") == (
        "NEEDS_INVESTIGATION", ["EVIDENCE_SOURCE_MIXED"])


@pytest.mark.parametrize("label, code", [
    (None, "NO_ACTION_RECORDED"), ("No action yet", "ACTION_PENDING"), ("Pending", "ACTION_PENDING"),
    ("Outcome pending", "OUTCOME_PENDING"), ("Resolution withdrawn", "RESOLUTION_WITHDRAWN"),
])
def test_rule_2_act_now_action_reasons(label, code) -> None:
    assert placed(row(end=OPEN), label) == ("ACT_NOW", ["EPISODE_OPEN", code])


def test_rule_2_signals_in_order_with_recurrence_text() -> None:
    r = row(end=OPEN, recurs=OTHER, transition="REOPENED", mechanism="GENERATOR_SUPPORT_CANDIDATE")
    p = place(r, None, COVERED, None)
    assert (p.group, p.group_rank) == ("ACT_NOW", 2)
    assert [(x.code, x.text) for x in p.reasons] == [
        ("RECURRED", "Returned after an earlier episode (Finding 1a2b3c4d)"),
        ("REOPENED", "Reopened after it had closed"),
        ("EPISODE_OPEN", "The episode is still open"),
        ("NO_ACTION_RECORDED", "No accepted Action; open the recommendation")]
    assert placed(row(recurs=OTHER), None) == ("ACT_NOW", ["RECURRED", "NO_ACTION_RECORDED"])
    assert placed(row(transition="REOPENED"), "Pending") == ("ACT_NOW", ["REOPENED", "ACTION_PENDING"])


def test_rule_2_needs_a_signal_and_open_action_work() -> None:
    # A signal with a verified or applied change is monitored; open action work without a signal is not ACT_NOW.
    assert placed(row(end=OPEN), "Verified") == ("MONITOR", ["VERIFIED_WATCH_RETURN"])
    assert placed(row(end=OPEN), "Applied") == ("MONITOR", ["APPLIED_AWAITING_PLAN"])
    assert placed(row(end=CLOSED), None) == ("UNPRICED_RISK", ["UNPRICED_OTHER"])


@pytest.mark.parametrize("label, code", [("Verified", "VERIFIED_WATCH_RETURN"), ("Applied", "APPLIED_AWAITING_PLAN")])
def test_rule_3_monitor_runs_before_compare_value(label, code) -> None:
    assert placed(row(cons="PRICED"), label, line_group="COMPARABLE") == ("MONITOR", [code])
    p = place(row(cons="PRICED"), action(label), COVERED, "COMPARABLE")
    assert p.group_rank == 5


@pytest.mark.parametrize("line_group, code", [
    ("COMPARABLE", "PRICED_COMPARABLE"), ("SINGLE_LINE", "PRICED_SINGLE"), ("INELIGIBLE", "PRICED_SINGLE"),
    ("CONFLICT", "PRICED_SINGLE"), (None, "PRICED_SINGLE"),
])
def test_rule_4_compare_value(line_group, code) -> None:
    p = place(row(cons="PRICED"), None, COVERED, line_group)
    assert (p.group, p.group_rank, [x.code for x in p.reasons]) == ("COMPARE_VALUE", 3, [code])


@pytest.mark.parametrize("mechanism, code", [
    ("COLD_EXCURSION", "UNPRICED_PRODUCT_EXPOSURE"), ("COLD_START_FAILURE", "UNPRICED_START_FAILURE"),
    ("EV_INTERRUPTION", "UNPRICED_SERVICE_INTERRUPTION"), ("GENERATOR_SUPPORT_CANDIDATE", "UNPRICED_OTHER"),
    (None, "UNPRICED_OTHER"),
])
def test_rule_5_unpriced_risk(mechanism, code) -> None:
    p = place(row(mechanism=mechanism), None, COVERED, None)
    assert (p.group, p.group_rank, [x.code for x in p.reasons]) == ("UNPRICED_RISK", 4, [code])
    assert p.reasons[0].text == REASON_TEXT[code]


def test_rule_6_no_consequence_is_monitor() -> None:
    assert placed(row(cons=None)) == ("MONITOR", ["NO_OPEN_SIGNAL"])
    # A consequence object without a state is "no consequence" too.
    assert placed({**row(), "consequence": {}}) == ("MONITOR", ["NO_OPEN_SIGNAL"])


def test_every_reason_code_is_reachable() -> None:
    seen: set[str] = set()
    for src in ("REGISTERED_SIMULATION", "MIXED", "UNKNOWN"):
        for lifecycle in ("SUPPORTED", "UNCONFIRMED"):
            for cons in (None, "PRICED", "UNPRICED", "WITHHELD"):
                for end in (OPEN, CLOSED):
                    for recurs, transition in ((None, None), (OTHER, None), (None, "REOPENED")):
                        for label in (None, "No action yet", "Pending", "Outcome pending", "Resolution withdrawn",
                                      "Verified", "Applied"):
                            for mech in ("COLD_EXCURSION", "COLD_START_FAILURE", "EV_INTERRUPTION", None):
                                for lg in ("COMPARABLE", None):
                                    r = row(src=src, lifecycle=lifecycle, cons=cons, end=end, recurs=recurs,
                                            transition=transition, mechanism=mech)
                                    seen |= {x.code for x in place(r, action(label), COVERED, lg).reasons}
    assert seen == set(REASON_TEXT)


@pytest.mark.parametrize("facts, cov, state, reasons", [
    ({}, COVERED, "SUPPORTED_SOURCE_COHERENT", ["Supported claim", "Registered simulation source"]),
    ({"src": "AUTHORED_DEMONSTRATION"}, {"state": "HISTORICAL"}, "SUPPORTED_SOURCE_COHERENT",
     ["Supported claim", "Authored demonstration source"]),
    ({"src": "MIXED", "lifecycle": "UNCONFIRMED"}, COVERED, "UNKNOWN", ["Unconfirmed claim", "Mixed sources"]),
    ({"src": "UNKNOWN"}, COVERED, "UNKNOWN", ["Supported claim", "Source not resolved"]),
    ({"src": None}, COVERED, "UNKNOWN", ["Supported claim", "Source not resolved"]),
    ({"lifecycle": "UNCONFIRMED"}, COVERED, "LIMITED", ["Unconfirmed claim", "Registered simulation source"]),
    ({"cons": "WITHHELD"}, {"state": "PARTIAL"}, "LIMITED",
     ["Supported claim", "Registered simulation source", "Cost basis withheld",
      "Site coverage incomplete; other Findings may be missing"]),
    ({}, {"state": "UNKNOWN"}, "SUPPORTED_SOURCE_COHERENT",
     ["Supported claim", "Registered simulation source", "Site coverage incomplete; other Findings may be missing"]),
])
def test_confidence_from_row_facts_with_site_text_only(facts, cov, state, reasons) -> None:
    p = place(row(**facts), None, cov, None)
    assert (p.confidence, list(p.confidence_reasons)) == (state, reasons)
    assert p.group == place(row(**facts), None, COVERED, None).group  # R5.6: site coverage never moves a row


def test_wire_shape() -> None:
    p = place(row(end=OPEN, recurs=OTHER), None, COVERED, None)
    assert p.wire() == {"policy_version": "estate-placement/1", "group": "ACT_NOW", "group_rank": 2, "reasons": [
        {"code": "RECURRED", "text": "Returned after an earlier episode (Finding 1a2b3c4d)"},
        {"code": "EPISODE_OPEN", "text": "The episode is still open"},
        {"code": "NO_ACTION_RECORDED", "text": "No accepted Action; open the recommendation"}]}
    assert p.confidence in placement.CONFIDENCE_STATES


def test_six_part_portfolio_marker_passes_and_five_part_fails() -> None:
    six = [1, "2026-10-06T04:00:00.000000Z", "kobo-001", UUID_A, UUID_A, UUID_A]
    assert _marker_ok("portfolio", six) and _marker_ok("portfolio", [5, None, *six[2:]])
    assert not _marker_ok("portfolio", six[1:])  # the pre-CC-R2 five-part form
    for rank in (0, 6, True, False, "1", 1.0, None):
        assert not _marker_ok("portfolio", [rank, *six[1:]]), rank
