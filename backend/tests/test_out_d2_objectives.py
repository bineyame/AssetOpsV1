"""OUT-D U2: the pure objective verdict and status rules 4c, 7, 7b, 7c (build sheet OUT-D §3 U2, §4)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from assetops_backend.outcomes import objectives as obj
from assetops_backend.outcomes.catalogue import OUTCOME_BY_KEY
from assetops_backend.outcomes.objectives import (
    AT_LEAST, AT_MOST, MEASURES, MET, MISSED, NOT_JUDGED, ObjectiveFact, Reading, judge, target_text)
from assetops_backend.outcomes.status import (
    FINDING, NEEDS_ATTENTION, NO_OBJECTIVE, NOT_MEASURED, ON_TRACK, OPPORTUNITY, SIGNAL_OPPORTUNITY, STATUS_POLICY,
    UNKNOWN, WARNING, WATCH, Signal, outcome_state)
from test_out_a1_outcome_map import _vocabulary_patterns

MG1, MG2, MG7, EV2 = (OUTCOME_BY_KEY[k] for k in ("MG-1", "MG-2", "MG-7", "EV-2"))


def fact(comparison: str, target) -> ObjectiveFact:
    return ObjectiveFact("MG-2", "avoidable_generator_minutes", comparison, Decimal(target), Decimal(target) == 0,
                         "t", "DECLARED", "r1")


def reading(value, complete=True) -> Reading:
    return Reading(None if value is None else Decimal(value), complete, "a")


@pytest.mark.parametrize(("comparison", "target", "value", "complete", "verdict"), [
    (AT_MOST, "0", "12", True, MISSED),
    (AT_MOST, "0", "12", False, MISSED),       # the miss is proven without a complete window
    (AT_MOST, "5", "5", True, MET),
    (AT_MOST, "5", "3", False, NOT_JUDGED),    # MET needs a complete window
    (AT_MOST, "5", None, True, NOT_JUDGED),
    (AT_LEAST, "300", "300", False, MET),      # the met is proven without a complete window
    (AT_LEAST, "300", "301", True, MET),
    (AT_LEAST, "300", "120", True, MISSED),
    (AT_LEAST, "300", "120", False, NOT_JUDGED),
    (AT_LEAST, "300", None, True, NOT_JUDGED),
])
def test_judge_branches(comparison, target, value, complete, verdict) -> None:
    assert judge(fact(comparison, target), reading(value, complete)) == verdict


def test_judge_without_reading_is_not_judged() -> None:
    assert judge(fact(AT_MOST, "0"), None) == NOT_JUDGED


def st(outcome, signals=(), *, objective=None, objectives_ok=True, settled=True, readiness=None):
    return outcome_state(outcome, settled=settled, signals=signals, readiness=readiness, objective=objective,
                         objectives_ok=objectives_ok)


def test_policy_is_v2() -> None:
    assert STATUS_POLICY == "outcome-status/2" and obj.POLICY == "outcome-objectives/1"


def test_rule4c_missed_needs_attention_and_loses_only_its_reason_to_4a() -> None:
    assert st(MG2, objective=MISSED) == (NEEDS_ATTENTION, "OBJECTIVE_MISSED")
    assert st(MG2, objective=MET) != (NEEDS_ATTENTION, "OBJECTIVE_MISSED")
    assert st(MG2, [Signal(FINDING, "MG-2", True, True)], objective=MISSED) == (NEEDS_ATTENTION, "PRIMARY_FINDING_OPEN")
    assert st(MG2, [Signal(WARNING, "MG-2", True, True, status_effect=NEEDS_ATTENTION)], objective=MISSED) == (
        NEEDS_ATTENTION, "WARNING_NEEDS_ATTENTION")
    # 4c beats WATCH and OPPORTUNITY.
    assert st(MG2, [Signal(FINDING, "MG-2", True, True, applied=True)], objective=MISSED)[0] == NEEDS_ATTENTION
    assert st(MG1, [Signal(SIGNAL_OPPORTUNITY, "MG-1", True, True)], objective=MISSED)[0] == NEEDS_ATTENTION


def test_rule7_met_is_on_track_and_loses_to_watch_and_opportunity() -> None:
    assert st(MG2, objective=MET) == (ON_TRACK, "OBJECTIVE_MET")
    assert st(MG2) == (NO_OBJECTIVE, "NO_OBJECTIVE_DECLARED")
    assert st(MG2, [Signal(FINDING, "MG-2", True, True, applied=True)], objective=MET)[0] == WATCH
    assert st(MG7, readiness="LIMITED", objective=MET)[0] == WATCH
    assert st(MG1, [Signal(SIGNAL_OPPORTUNITY, "MG-1", True, True)], objective=MET)[0] == OPPORTUNITY


def test_rule7b_not_judged_is_unknown_after_opportunity() -> None:
    assert st(MG2, objective=NOT_JUDGED) == (UNKNOWN, "OBJECTIVE_NOT_JUDGED")
    assert st(MG1, [Signal(SIGNAL_OPPORTUNITY, "MG-1", True, True)], objective=NOT_JUDGED) == (
        OPPORTUNITY, "OPPORTUNITY_OPEN")  # Kobo Grow keeps Opportunity


def test_rule7c_failed_objectives_read_is_unknown_never_no_objective() -> None:
    assert st(MG2, objectives_ok=False) == (UNKNOWN, "OBJECTIVES_NOT_READ")
    assert st(MG2, objectives_ok=True) == (NO_OBJECTIVE, "NO_OBJECTIVE_DECLARED")
    assert st(MG2, objective=MET, objectives_ok=False) == (ON_TRACK, "OBJECTIVE_MET")


def test_not_measured_and_unsettled_beat_an_objective() -> None:
    assert not EV2.measured
    assert st(EV2, objective=MISSED)[0] == NOT_MEASURED
    assert st(MG2, objective=MISSED, settled=False)[0] == UNKNOWN


def test_measures_table() -> None:
    assert set(MEASURES) == {"avoidable_generator_minutes", "productive_use_kwh", "unserved_critical_kwh",
                             "backup_start_failures", "interrupted_sessions", "energy_cost_per_km"}
    assert {m.outcome for m in MEASURES.values()} == {"MG-2", "MG-1", "MG-5", "CC-6", "EV-1", "EV-2"}
    assert all(m.outcome in OUTCOME_BY_KEY and m.key == k for k, m in MEASURES.items())
    # Ruling Q1: only energy cost per km is a value measure, and it alone carries money.
    assert [k for k, m in MEASURES.items() if m.kind == obj.VALUE] == ["energy_cost_per_km"]
    assert all(m.unit != obj.MONEY_UNIT for m in MEASURES.values() if m.kind == obj.LEADING)
    assert [k for k, m in MEASURES.items() if m.zero_only] == ["backup_start_failures"]
    assert {m.window_rule for m in MEASURES.values() if m.outcome.startswith("MG")} == {obj.BOARD_DAY}
    assert {m.window_rule for m in MEASURES.values() if not m.outcome.startswith("MG")} == {obj.BOARD_WINDOW}


def test_target_texts() -> None:
    m = MEASURES
    assert target_text(m["avoidable_generator_minutes"], target_is_zero=True, number="0") == (
        "Supply cost per kWh: no generator time longer than needed")
    assert target_text(m["avoidable_generator_minutes"], target_is_zero=False, number="30") == (
        "Supply cost per kWh: at most 30 min a day with the generator on longer than needed")
    assert target_text(m["productive_use_kwh"], target_is_zero=False, number="300") == (
        "Productive electricity sales: at least 300 kWh sold for productive use a month")
    assert target_text(m["unserved_critical_kwh"], target_is_zero=True, number="0") == (
        "Reliable service: all critical demand served")
    assert target_text(m["energy_cost_per_km"], target_is_zero=False, number="0.20", currency="USD") == (
        "Energy cost per km: at most 0.20 USD per km")
    assert target_text(m["interrupted_sessions"], target_is_zero=False, number="2") == (
        "Buses ready for service: at most 2 interrupted charging sessions")


def test_every_template_passes_vocabulary() -> None:
    patterns = _vocabulary_patterns()
    copy = ([m.target_zero for m in MEASURES.values()] + [m.target_any for m in MEASURES.values()]
            + list(obj.VERDICT_LABEL.values()) + [c["label"] for c in obj.VERDICT_CHIP.values()]
            + [obj.CONTRIBUTOR_LABEL, obj.CHAMBER_RANGE_TARGET])
    hits = [(text, name) for text in copy for name, pattern in patterns if pattern.search(text)]
    assert hits == []
    assert any(p.search("critical load") for _, p in patterns)  # non-vacuous: "load" is caught
    assert set(obj.VERDICT_CHIP) == set(obj.VERDICT_LABEL) == {MET, MISSED, NOT_JUDGED}
