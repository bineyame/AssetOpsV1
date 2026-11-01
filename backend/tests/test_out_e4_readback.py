"""OUT-E E4: the cost check read back on the Site outcome board, with fake ports (`.agent/build-sheet-OUT-E.md` E4).

Every Cost-line state and the 11 reason words; rounding (1/24 -> 0.042, 11/240 -> 0.046); equal bounds give one
figure; the before/after line attributed only on VERIFIED, "Status changed; not attributed" otherwise, unchanged
verdicts stated plainly; no line without a MG-2 objective or with a non-zero target; the Assure line; no code on screen.
"""

from __future__ import annotations

import re
from dataclasses import replace
from decimal import Decimal

import pytest

import test_out_b2_mini as b2
import test_out_d4_board as d4
from assetops_backend.financials.trial_fuel_comparison import REASSESSMENT_REASONS
from assetops_backend.outcomes.objectives import AT_MOST, ObjectiveFact
from assetops_backend.site_outcomes import board, mini
from assetops_backend.site_outcomes.board import ActionFact, assemble

COST, ASSURE = mini.COST, mini.ASSURE
IMPROVED = {"state": "MODELLED_IMPROVEMENT", "reason": None, "nominal": "1/24", "upper": "11/240",
            "currency": "USD", "recorded_at": "2026-11-02T10:00:00+00:00"}
HOURS = {"before_seconds": 900, "after_seconds": 0}
CHANGE = ("Estimated effect of the trial (not money saved): 0.042–0.046 USD less supply cost per kWh.")
ATTRIBUTED = "Goal before the trial: missed; after: met."
MG2 = ObjectiveFact("MG-2", "avoidable_generator_minutes", AT_MOST, Decimal(0), True, "t", "DECLARED", "r1")


def action(state: str = "VERIFIED", cost=IMPROVED, hours=HOURS) -> ActionFact:
    return ActionFact("a48", "ACT-048", "", "f104", "f104r", True, False, state, "/a48", cost_check=cost,
                      trial_hours=hours)


def test_cost_line_every_state() -> None:
    assert board.cost_line(action()) == CHANGE
    assert board.cost_line(action(cost=dict(IMPROVED, state="MODELLED_NO_IMPROVEMENT", nominal="0", upper="0"))) == (
        "Estimated effect of the trial (not money saved): no lower supply cost per kWh.")
    for state in ("VERIFIED", "INEFFECTIVE", "INCONCLUSIVE"):
        assert board.cost_line(action(state, cost=None)) == "Not calculated yet"
    for state in ("PENDING", "REASSESSMENT_PENDING", "NO_PLAN", None):
        assert board.cost_line(action(state, cost=None)) is None


@pytest.mark.parametrize("reason", REASSESSMENT_REASONS)
def test_cost_line_reason_words(reason: str) -> None:
    line = board.cost_line(action("INEFFECTIVE", cost=dict(IMPROVED, state="UNAVAILABLE", reason=reason,
                                                            nominal=None, upper=None)))
    assert line == f"Modelled change not calculated: {board.COST_REASON_WORDS[reason]}"
    assert reason not in line and "_" not in line
    assert set(board.COST_REASON_WORDS) == set(REASSESSMENT_REASONS)


def test_rounding_half_even_and_one_figure_when_equal() -> None:
    assert (board._round3("1/24"), board._round3("11/240")) == ("0.042", "0.046")
    assert (board._round3("0.0425"), board._round3("0.0435"), board._round3("0.125")) == ("0.042", "0.044", "0.125")
    assert board._round3("-1/24") == "-0.042" and board._round3("3") == "3.000"
    assert board.per_kwh_amount({"nominal": "1/24", "upper": "0.0416"}) == "0.042"
    assert board.per_kwh_amount(IMPROVED) == "0.042–0.046"


def test_before_after_attribution() -> None:
    assert board.trial_line(action(), MG2) == ATTRIBUTED
    for state in ("INEFFECTIVE", "INCONCLUSIVE"):
        assert board.trial_line(action(state), MG2) == "Status changed; not attributed"
        assert board.trial_line(action(state, hours={"before_seconds": 0, "after_seconds": 0}), MG2) == (
            "Supply cost per kWh: met before and after the trial")
        assert board.trial_line(action(state, hours={"before_seconds": 60, "after_seconds": 30}), MG2) == (
            "Supply cost per kWh: missed before and after the trial")


def test_no_before_after_line_without_zero_target_or_known_hours() -> None:
    assert board.trial_line(action(), None) is None
    assert board.trial_line(action(), replace(MG2, target=Decimal(5), target_is_zero=False)) is None  # R593
    assert board.trial_line(action(hours={"before_seconds": 900, "after_seconds": None}), MG2) is None
    assert board.trial_line(action(hours=None), MG2) is None


def run(verification: dict, rows=d4.KOBO_OBJECTIVES):
    applied = dict(b2.A48, state={"application": "APPLIED"})
    fake = b2.Fake(verification=verification, action_index={"rows": [applied], "next_cursor": None})
    return d4.run_mini(fake, rows)[1]


def act_entry(rows: dict) -> dict:
    return next(e for e in rows[COST]["earlier"] if e["text"].startswith("ACT-048"))


def test_board_cost_row_earlier_detail_and_assure_line() -> None:
    rows = run({"state": "VERIFIED", "cost_check": IMPROVED, "trial_hours": HOURS})
    entry = act_entry(rows)
    assert entry["result_label"] == "Verified on test data"
    assert entry["detail"] == f"{CHANGE} · {ATTRIBUTED}"
    assert all(e["detail"] is None for r in rows.values() for e in r["earlier"] if e is not entry)
    assure = d4.b2.contributor(rows[ASSURE], "verified_results")["text"]
    assert assure == ("ACT-048 verified on test data: estimated effect of the trial (not money saved): 0.042–0.046 USD less "
                      "supply cost per kWh")


def test_board_not_verified_credits_nothing_to_the_trial() -> None:
    no_gain = dict(IMPROVED, state="UNAVAILABLE", reason="OUTCOME_INCONCLUSIVE", nominal=None, upper=None)
    rows = run({"state": "INCONCLUSIVE", "cost_check": no_gain, "trial_hours": HOURS})
    assert act_entry(rows)["detail"] == ("Modelled change not calculated: the trial result is not determined · "
                                         "Status changed; not attributed")
    assert d4.b2.contributor(rows[ASSURE], "verified_results")["text"] == "ACT-048 result not determined"
    rows = run({"state": "VERIFIED", "cost_check": None, "trial_hours": HOURS})
    assert act_entry(rows)["detail"] == f"Not calculated yet · {ATTRIBUTED}"
    assert d4.b2.contributor(rows[ASSURE], "verified_results")["text"] == "ACT-048 verified on test data"


def test_board_no_before_after_without_the_mg2_objective() -> None:
    others = [o for o in d4.KOBO_OBJECTIVES if o["outcome_key"] != "MG-2"]
    rows = run({"state": "VERIFIED", "cost_check": IMPROVED, "trial_hours": HOURS}, others)
    assert act_entry(rows)["detail"] == CHANGE
    nonzero = [d4.objective("MG-2", "avoidable_generator_minutes", "5"), *others]
    assert act_entry(run({"state": "VERIFIED", "cost_check": IMPROVED, "trial_hours": HOURS}, nonzero))[
        "detail"] == CHANGE


def test_no_code_on_screen_and_saving_only_in_not_realised_savings() -> None:
    texts = []
    for verification in ({"state": "VERIFIED", "cost_check": IMPROVED, "trial_hours": HOURS},
                         {"state": "INEFFECTIVE", "cost_check": dict(IMPROVED, state="MODELLED_NO_IMPROVEMENT"),
                          "trial_hours": HOURS}):
        rows = run(verification)
        texts += [e["detail"] for r in rows.values() for e in r["earlier"] if e["detail"]]
        texts += [d4.b2.contributor(rows[ASSURE], "verified_results")["text"]]
    texts += [board.COST_NOT_CALCULATED.format(words=w) for w in board.COST_REASON_WORDS.values()]
    codes = [*REASSESSMENT_REASONS, "MODELLED_", "UNAVAILABLE", "trial-fuel-comparison", "candidate", "{", "}"]
    assert [(t, c) for t in texts for c in codes if c in t] == []
    assert all(m.group(0).lower() == "saved" and "not money saved" in t
               for t in texts for m in re.finditer(r"sav(?:ed|ing|e)s?", t, re.I))
    patterns = d4._vocabulary_patterns()
    assert [(t, n) for t in texts for n, p in patterns if p.search(t)] == []
