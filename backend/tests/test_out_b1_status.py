"""OUT-B1: outcome status rules, roll-up precedence and the mock grid (build spec §1.4, rulings B-Q16/Q17)."""
from __future__ import annotations

from itertools import combinations

import pytest

from assetops_backend.outcomes.catalogue import CATEGORIES, COLD, EV, MINI, OUTCOME_BY_KEY, SITE_OUTCOMES
from assetops_backend.outcomes.status import (
    EVIDENCE_GAP, FINDING, NEEDS_ATTENTION, NO_OBJECTIVE, NOT_APPLICABLE, NOT_MEASURED, OPPORTUNITY, PRECEDENCE,
    SIGNAL_OPPORTUNITY, STATE_LABEL, STATE_TONE, UNKNOWN, WARNING, WATCH, Signal, outcome_state, roll_up)

MG2, MG7, MG4, CC1 = (OUTCOME_BY_KEY[k] for k in ("MG-2", "MG-7", "MG-4", "CC-1"))


def state(outcome, signals=(), *, settled=True, readiness=None, applicable=True):
    return outcome_state(outcome, settled=settled, signals=signals, readiness=readiness, applicable=applicable)[0]


def finding(key, *, primary=True, open_=True, applied=False):
    return Signal(FINDING, key, primary, open_, applied)


def test_rule1_not_applicable_reserved() -> None:
    assert state(MG2, [finding("MG-2")], applicable=False) == NOT_APPLICABLE
    assert state(MG2, [finding("MG-2")]) != NOT_APPLICABLE


def test_rule2_not_measured_beats_signals() -> None:
    assert not MG4.measured
    assert state(MG4, [finding("MG-4")], settled=False) == NOT_MEASURED
    assert state(MG2) != NOT_MEASURED


def test_rule3_unsettled_is_unknown() -> None:
    assert state(MG2, [finding("MG-2")], settled=False) == UNKNOWN
    assert state(MG2, [finding("MG-2")], settled=True) == NEEDS_ATTENTION


def test_rule4_open_primary_finding_without_applied_action() -> None:
    assert outcome_state(MG2, settled=True, signals=[finding("MG-2")], readiness=None) == (
        NEEDS_ATTENTION, "PRIMARY_FINDING_OPEN")
    assert state(MG2, [finding("MG-2", open_=False)]) == NO_OBJECTIVE
    assert state(MG2, [finding("MG-5")]) == NO_OBJECTIVE  # another outcome's Finding


def test_rule4_warning_needs_attention() -> None:
    assert state(MG2, [Signal(WARNING, "MG-2", True, True, status_effect=NEEDS_ATTENTION)]) == NEEDS_ATTENTION
    assert state(MG2, [Signal(WARNING, "MG-2", True, True, status_effect=None)]) == NO_OBJECTIVE


def test_rule5_watch_cases() -> None:
    assert state(MG2, [finding("MG-2", primary=False)]) == WATCH
    assert state(MG2, [finding("MG-2", applied=True)]) == WATCH  # D4 (R542): Kobo cost after ACT-048 applied
    assert state(MG2, [Signal(WARNING, "MG-2", True, True, status_effect=WATCH)]) == WATCH
    assert state(MG7, readiness="LIMITED") == WATCH
    assert state(MG7, readiness="NONE") == WATCH
    assert state(MG7, readiness="FULL") == NO_OBJECTIVE
    assert state(MG2, readiness="LIMITED") == NO_OBJECTIVE  # readiness moves only the @EVIDENCE outcome


def test_rule6_opportunity_and_evidence_gap_has_no_effect() -> None:
    mg1 = OUTCOME_BY_KEY["MG-1"]
    assert state(mg1, [Signal(SIGNAL_OPPORTUNITY, "MG-1", True, True)]) == OPPORTUNITY
    assert state(mg1, [Signal(SIGNAL_OPPORTUNITY, "MG-1", True, False)]) == NO_OBJECTIVE
    assert state(MG7, [Signal(EVIDENCE_GAP, "MG-7", True, True)], readiness="FULL") == NO_OBJECTIVE  # B-Q16


def test_rule8_otherwise_no_objective() -> None:
    assert state(CC1) == NO_OBJECTIVE


@pytest.mark.parametrize("high,low", list(combinations(PRECEDENCE, 2)))
def test_roll_up_every_pairwise_precedence(high: str, low: str) -> None:
    assert roll_up([("A", low), ("B", high)]) == (high, "B")
    assert roll_up([("A", high), ("B", low)]) == (high, "A")


def test_roll_up_lead_tie_break_is_catalogue_order() -> None:
    assert roll_up([("X", WATCH), ("Y", WATCH), ("Z", NO_OBJECTIVE)]) == (WATCH, "X")


def test_labels_and_tones_cover_every_state() -> None:
    assert set(STATE_LABEL) == set(PRECEDENCE) == set(STATE_TONE)
    assert STATE_TONE[NO_OBJECTIVE] == "gray" and STATE_TONE[NOT_MEASURED] == "none"


def grid(domain: str, signals, readiness) -> list[str]:
    out = []
    for cat in CATEGORIES:
        pairs = [(o.key, state(o, signals, readiness=readiness)) for o in SITE_OUTCOMES
                 if o.domain == domain and o.category == cat]
        out.append(roll_up(pairs)[0])
    return out


def test_mock_grid_golden_b_column() -> None:
    mini = [Signal(SIGNAL_OPPORTUNITY, "MG-1", True, True),           # F-109 headroom
            finding("MG-2"),                                         # F-104 moves MG-2
            Signal(EVIDENCE_GAP, "MG-7", True, True)]                # F-108, issue only
    assert grid(MINI, mini, "LIMITED") == [OPPORTUNITY, NEEDS_ATTENTION, NO_OBJECTIVE, WATCH]
    cold = [finding("CC-6"), finding("CC-1", primary=False),         # F-118
            finding("CC-1")]                                         # F-119
    assert grid(COLD, cold, "LIMITED") == [NOT_MEASURED, NOT_MEASURED, NEEDS_ATTENTION, WATCH]
    ev = [finding("EV-1"), finding("EV-3", primary=False)]           # F-130
    assert grid(EV, ev, "LIMITED") == [WATCH, NOT_MEASURED, NEEDS_ATTENTION, WATCH]
