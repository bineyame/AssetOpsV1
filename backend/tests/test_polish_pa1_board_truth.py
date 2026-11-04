"""POLISH PA-1 board truth (`.agent/build-sheet-POLISH.md` §1.1, §1.3 copy, §1.6, §1.7, §6 D-2, Addendum 2).

- §1.1 (P-06, R626): a PRICED amount of zero reads "No fuel cost estimated: ..." with no money on the headline.
- §1.6 (P-11, R635): the EV Optimize sentence names a tariff estimate only when Grow holds a priced tariff.
- §1.7 (P-12): MG-7 settles on a CURRENT day whose reading is COMPLETE with zero intervals and readiness UNKNOWN.
- §6 D-2 (OUT-E L4): a modelled improvement is never credited to a trial that is not VERIFIED.
- §1.3 copy: the EV option reads "Investigate Connector c1", not "Investigate connector Connector c1".
"""
from __future__ import annotations

from dataclasses import replace

import test_out_b2_mini as b2
from test_out_b1_board import F130, rows_by_cat, settled
from test_out_e4_readback import IMPROVED, action

from assetops_backend.outcomes import catalogue
from assetops_backend.outcomes.catalogue import EV
from assetops_backend.site_outcomes import board, mini
from assetops_backend.site_outcomes.board import SiteFacts

GROW, COST, ASSURE = mini.GROW, mini.COST, mini.ASSURE
PRICED_EV_SENTENCE = "Energy cost per km needs odometer readings; a tariff estimate exists in Financials"
UNPRICED_EV_SENTENCE = "Energy cost per km needs odometer readings and a published charging tariff"


# --------------------------------------------------------------- §1.1 zero priced amount

def _money(**over):
    """CH-5a1: the overview money section is the ChainReader `money_head` (CH5a1-R Q5)."""
    return replace(b2.MONEY, **over)


def test_zero_priced_amount_reads_no_fuel_cost_estimated_without_money() -> None:
    _, rows = b2.run(b2.Fake(money_head=_money(amount_low="0", amount_high="0.00")))
    assert rows[COST]["headline"] == (
        "No fuel cost estimated: the generator was on but delivered no measured power")
    assert rows[COST]["headline_money"] is None


def test_non_zero_priced_amount_keeps_money_and_day_wording() -> None:
    _, rows = b2.run(b2.Fake(money_head=_money(amount_low="0", amount_high="0.01")))
    assert rows[COST]["headline"] == "possible extra fuel cost on this day"
    assert rows[COST]["headline_money"] == {"amount_low": "0", "amount_high": "0.01", "currency": "USD"}


def test_unpriced_amount_reads_no_fuel_cost_for_this_day() -> None:
    _, rows = b2.run(b2.Fake(money_head=_money(priced=False)))
    assert rows[COST]["headline"] == "No fuel cost estimated for this day" and rows[COST]["headline_money"] is None


# --------------------------------------------------------------- §1.6 EV Optimize sentence

def _ev_cost_text(money) -> str:
    facts = SiteFacts(EV, "EV-LAB-001", findings=(F130,), readiness="NONE", settled=settled(EV),
                      headline_money={GROW: money})
    return rows_by_cat(facts)[COST]["not_measured_text"]


def test_ev_optimize_sentence_needs_a_priced_tariff() -> None:
    assert _ev_cost_text(None) == UNPRICED_EV_SENTENCE
    assert _ev_cost_text({"amount_low": "12.40", "amount_high": "12.40", "currency": "USD"}) == PRICED_EV_SENTENCE
    assert catalogue.ROW_NOT_MEASURED_EV_COST_UNPRICED == UNPRICED_EV_SENTENCE


# --------------------------------------------------------------- §1.7 MG-7 on a day with no generator run

#: CH5a1-R Q2: the assessment is the dispatch body (status, claim level, limitations, intervals).
NO_RUN = {"status": "CURRENT", "window_assessment": {"claim_level": "COMPLETE"}, "limitations": [], "intervals": []}


def _no_run(dispatch=NO_RUN, readiness=None, settled=True):
    over = {"dispatch": dispatch, "day": {"readiness": readiness, "settled": settled}}
    return b2.Fake(**over) if readiness is not None else b2.Fake(refuse=("chain_day",), dispatch=dispatch)


def test_complete_zero_interval_day_settles_mg7_with_unknown_readiness() -> None:
    _, rows = b2.run(_no_run(readiness="UNKNOWN"))
    assert b2.outcome(rows[ASSURE], "MG-7") == "NO_OBJECTIVE"
    assert rows[ASSURE]["state"] == "NO_OBJECTIVE" and rows[ASSURE]["state_label"] == "No objective declared"
    readings = b2.contributor(rows[ASSURE], "readings")
    assert readings["text"] == "Generator not used on this day, so nothing to check · readings complete"
    # Addendum 4 item 3: the line's chip is the FULL chip, never Unknown, and no Assure text says Unknown
    assert readings["confidence"] == board.readiness_confidence("FULL")
    assert readings["confidence"] != mini.UNKNOWN_CHIP
    assert all("Unknown" not in (c["text"] or "") and "Unknown" not in ((c.get("confidence") or {}).get("label") or "")
               for c in rows[ASSURE]["contributors"] if c["key"] == "readings")
    assert all("Unknown" not in (c["text"] or "") for c in rows[ASSURE]["contributors"])


def test_no_run_rule_is_narrow() -> None:
    one = dict(NO_RUN, intervals=[{"revision_id": "r1"}])
    limited = dict(NO_RUN, window_assessment={"claim_level": "LIMITED"})
    cases = ((one, "UNKNOWN", True), (limited, "UNKNOWN", True), (NO_RUN, "UNKNOWN", False), (NO_RUN, None, True))
    for dispatch, readiness, settled in cases:  # stale = the board day not settled (R4)
        _, rows = b2.run(_no_run(dispatch, readiness, settled))
        assert b2.outcome(rows[ASSURE], "MG-7") == "UNKNOWN", (dispatch, readiness, settled)
        assert "Generator not used" not in b2.contributor(rows[ASSURE], "readings")["text"]
    # readiness known: the earlier rule, unchanged
    _, rows = b2.run(_no_run(readiness="FULL"))
    assert b2.contributor(rows[ASSURE], "readings")["text"] == "Example data · readiness Full"


def test_new_mini_copy_is_in_the_vocabulary_scan() -> None:
    assert mini.COST_ZERO in mini.COPY and mini.NO_RUN_READINGS in mini.COPY


# --------------------------------------------------------------- §6 D-2 (OUT-E L4)

def test_modelled_improvement_is_credited_only_to_a_verified_trial() -> None:
    assert board.cost_line(action("VERIFIED")).startswith("Estimated effect of the trial")
    for state in ("INEFFECTIVE", "INCONCLUSIVE", "PENDING", None):
        assert board.cost_line(action(state, cost=IMPROVED)) == (
            "The trial did not fix the problem, so no cost change is credited to it"), state
