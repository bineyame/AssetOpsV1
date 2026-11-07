"""CH-6a2 L0 (build sheet CH-6 §A3, R5, R6, R11, R12, R13; CH6a2-R Q1, Q2, Q4, Q5, Q6; CH-6a1 L1-L3): the
OutcomeEvaluator truth tables over frozen facts. Pure: no database, no app."""
from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest

from assetops_backend.chain.outcomes import (
    POTENTIAL_STATES, NodeInputs, OutcomeEvaluator, headroom_signal_on)
from assetops_backend.chain.ports import SnapshotRow
from assetops_backend.chain.read import MoneyHead
from assetops_backend.chain.strategies.base import NOT_PRICED, ContributionContext
from assetops_backend.chain.strategies.graded_verdict import grade_counts
from assetops_backend.chain.strategies import REGISTRY
from assetops_backend.chain.vocabulary import LIMIT_MIXED, MG1_NO_DAY
from assetops_backend.outcomes.objectives import ObjectiveFact, Reading
from assetops_backend.outcomes.outcome_map import records_for

T, S = UUID(int=1), UUID(int=2)
EV = OutcomeEvaluator()


def row(day: int, grade: str, measure: str = "productive_kwh", kwh: str | None = "10", *, subject: str = "asset:a",
        cls: str = "MEASURED", amount: str | None = None, currency: str | None = "USD", month: int = 10):
    money = None if amount is None else {"amount": amount, "currency": currency}
    value = None if kwh is None else {"kwh": kwh}
    return SnapshotRow(T, S, date(2026, month, day), "ASSET", subject, measure, cls, 1, grade != "NOT_EXPECTED",
                       100, 100, "100", grade, value, money, "p", "c", 1, "fp")


def inp(rows=(), objectives=(), readings=None, hi=13, lo=None, **kw) -> NodeInputs:
    return NodeInputs("MG-W402-001", "mini_grid", "Africa/Nairobi",
                      (date(2026, 10, lo or hi), date(2026, 10, hi)), tuple(rows), tuple(objectives),
                      readings or {}, **kw)


def mg1(target: str = "300", k: int = 3) -> ObjectiveFact:
    return ObjectiveFact("MG-1", "productive_use_kwh", "AT_LEAST", Decimal(target), False, "t", "DECLARED", "r",
                         min_checked_days=k)


def at_most(key: str, measure: str, target: str = "0") -> ObjectiveFact:
    return ObjectiveFact(key, measure, "AT_MOST", Decimal(target), target == "0", "t", "DECLARED", "r")


# ---- A3.1 MG-1 (R5) ---------------------------------------------------------------------------------------------

def test_mg1_mix_complete_partial_low_no_data_and_a_declared_row():
    rows = [row(1, "COMPLETE"), row(2, "COMPLETE"), row(3, "PARTIAL", kwh="5"), row(4, "LOW", kwh="100"),
            row(5, "NO_DATA", kwh=None), row(6, "COMPLETE", kwh="999", cls="DECLARED")]
    i = inp(rows, [mg1("20")], hi=13)
    r = EV.readings(i)["MG-1"]
    assert r.value == Decimal("25")          # PARTIAL added unscaled, LOW never, DECLARED ignored
    assert (r.checked_days, r.elapsed_days, r.month_days, r.complete) == (2, 13, 31, False)
    kpi = EV.nodes(i, "MG-1")["kpi"]
    assert kpi.value == "MET"                # met on 2 checked days (missing days can only add)
    assert kpi.days == {"complete": 2, "partial": 1, "low": 1, "no_data": 9, "pending": 0, "expected": 13}
    assert kpi.basis == "CHECKED_DAYS" and kpi.text == "25 kWh so far this month, on 2 of 13 days checked"


def test_mg1_too_early_on_one_day_and_pace():
    i = inp([row(1, "COMPLETE", kwh="5")], [mg1("1000")], hi=3)
    kpi = EV.nodes(i, "MG-1")["kpi"]
    assert kpi.value == "TOO_EARLY" and "on 1 checked day; too early to judge (needs 3 checked days)" in kpi.text
    on = [row(d, "COMPLETE", kwh="40") for d in (1, 2, 3)]
    assert EV.nodes(inp(on, [mg1("310")], hi=3), "MG-1")["kpi"].value == "ON_PACE"
    behind = [row(d, "COMPLETE", kwh="5") for d in (1, 2, 3)]
    kpi = EV.nodes(inp(behind, [mg1("310")], hi=3), "MG-1")["kpi"]
    assert kpi.value == "BEHIND_PACE" and kpi.basis == "COMPLETE"
    assert kpi.text == "15 kWh so far this month, on 3 of 3 days checked · averages 5 kWh a day; the target needs " \
                       "10 kWh a day"


def test_mg1_missed_only_on_a_full_month():
    full = [row(d, "COMPLETE", kwh="1") for d in range(1, 32)]
    assert EV.nodes(inp(full, [mg1("300")], hi=31), "MG-1")["kpi"].value == "MISSED"
    one_partial = full[:-1] + [row(31, "PARTIAL", kwh="1")]
    assert EV.nodes(inp(one_partial, [mg1("300")], hi=31), "MG-1")["kpi"].value == "BEHIND_PACE"
    not_over = [row(d, "COMPLETE", kwh="1") for d in range(1, 31)]
    assert EV.nodes(inp(not_over, [mg1("300")], hi=30), "MG-1")["kpi"].value == "BEHIND_PACE"


def test_mg1_no_counted_day_is_not_judged_sales_not_recorded():
    kpi = EV.nodes(inp([row(1, "LOW")], [mg1()], hi=2), "MG-1")["kpi"]
    assert (kpi.value, kpi.text) == ("NOT_JUDGED", MG1_NO_DAY)


def test_mg1_weakest_subject_decides_the_day():
    rows = [row(1, "COMPLETE"), row(1, "PARTIAL", subject="asset:b"), row(2, "COMPLETE"),
            row(2, "LOW", subject="asset:b")]
    r = EV.readings(inp(rows, [mg1()], hi=2))["MG-1"]
    assert r.value == Decimal("20") and r.checked_days == 0    # day 1 PARTIAL (both added), day 2 LOW (none)


# ---- A3.1 non-monthly (R6) --------------------------------------------------------------------------------------

def test_cc1_chamber_no_data_is_not_judged_and_met_when_read():
    o = at_most("CC-1", "excursions")
    reading = {"CC-1": Reading(0, True, "No excursions")}
    gap = [row(1, "COMPLETE", "chamber_temp_c", kwh=None)]          # day 2 has no row: NO_DATA
    kpi = EV.nodes(inp(gap, [o], reading, lo=1, hi=2), "CC-1")["kpi"]
    # CH6b1-R4 H2: a mini kpi's reading is the board day's, so its days are counted over that day (day 2, no row:
    # NOT_KNOWN, one expected day with no data) and its span is that day, not the week. Before R4 the days were
    # counted over days 1-2 (CHECKED_DAYS); the not-judged value and the text are unchanged.
    assert kpi.value == "NOT_JUDGED" and kpi.text == "No excursions" and kpi.basis == "NOT_KNOWN"
    assert kpi.span == (date(2026, 10, 2), date(2026, 10, 2)) and kpi.days["no_data"] == 1
    assert EV.readings(inp(gap, [o], reading, lo=1, hi=2))["CC-1"].complete is False
    read = gap + [row(2, "COMPLETE", "chamber_temp_c", kwh=None)]
    assert EV.nodes(inp(read, [o], reading, lo=1, hi=2), "CC-1")["kpi"].value == "MET"


def test_cc1_partial_day_is_not_met():
    o = at_most("CC-1", "excursions")
    rows = [row(1, "COMPLETE", "chamber_temp_c", kwh=None), row(2, "PARTIAL", "chamber_temp_c", kwh=None)]
    assert EV.nodes(inp(rows, [o], {"CC-1": Reading(0, True, "x")}, lo=1, hi=2), "CC-1")["kpi"].value == "NOT_JUDGED"


def test_mg2_at_most_miss_proven_on_a_partial_day():
    o = at_most("MG-2", "avoidable_generator_minutes", "5")
    rows = [row(11, "PARTIAL", "avoidable_gen_min", kwh=None)]
    kpi = EV.nodes(inp(rows, [o], {"MG-2": Reading(12, False, "12 min longer than needed on this day")}, hi=11),
                   "MG-2")["kpi"]
    assert kpi.value == "MISSED" and kpi.basis == "CHECKED_DAYS"


def test_a_declared_row_does_not_complete_a_day():
    o = at_most("MG-2", "avoidable_generator_minutes", "5")
    rows = [row(12, "COMPLETE", "avoidable_gen_min", kwh=None, cls="DECLARED")]
    kpi = EV.nodes(inp(rows, [o], {"MG-2": Reading(0, True, "0 min")}, hi=12), "MG-2")["kpi"]
    assert kpi.value == "NOT_JUDGED" and kpi.basis == "NOT_KNOWN"


def test_mg5_days_are_the_board_day_critical_served_row():
    o = at_most("MG-5", "unserved_critical_kwh")
    rows = [row(12, "COMPLETE", "critical_served", kwh=None), row(13, "COMPLETE", "critical_served", kwh=None)]
    kpi = EV.nodes(inp(rows, [o], {"MG-5": Reading(Decimal(0), True, "0 kWh not served over the whole day")},
                       lo=12, hi=13), "MG-5")["kpi"]
    assert kpi.value == "MET" and kpi.days["expected"] == 1 and kpi.basis == "COMPLETE"


def test_no_objective_is_no_target():
    kpi = EV.nodes(inp([row(1, "COMPLETE")], [], hi=1), "MG-1")["kpi"]
    assert (kpi.value, kpi.days, kpi.basis, kpi.text) == (None, None, "NOT_KNOWN", "No target set yet")


# ---- A3.2 earnings ----------------------------------------------------------------------------------------------

def test_earnings_partial_unscaled_and_days():
    rows = [row(7, "COMPLETE", amount="2.50"), row(8, "PARTIAL", amount="0.75"), row(9, "LOW", amount="9.00")]
    e = EV.nodes(inp(rows, hi=9, lo=7), "MG-1")["earnings"]
    # CH6a3-R Q3: kWh of the counted days only (the LOW day adds neither money nor kWh); no declared price given.
    assert e.value == {"amount": "3.25", "currency": "USD", "kwh": "20"} and e.basis == "CHECKED_DAYS"
    assert e.text == "3.25 USD over 1 of 3 days checked · 1 partly checked · not billed or collected"


def test_earnings_zero_kwh_priced_is_zero_money():
    e = EV.nodes(inp([row(7, "COMPLETE", kwh="0", amount="0")], hi=7), "MG-1")["earnings"]
    assert e.text == "0.00 USD over 1 of 1 day checked · not billed or collected" and e.basis == "COMPLETE"


def test_earnings_currency_mixed():
    rows = [row(7, "COMPLETE", amount="1"), row(8, "COMPLETE", amount="1", currency="KES")]
    e = EV.nodes(inp(rows, hi=8, lo=7), "MG-1")["earnings"]
    assert (e.value, e.basis, e.text) == (None, "NOT_KNOWN", "Not shown · amounts in more than one currency")


def test_ev_earnings_reads_charging_kwh():
    e = EV.nodes(inp([row(9, "COMPLETE", "charging_kwh", amount="36")], hi=9), "EV-3")["earnings"]
    assert e.key == "money.estimated_charging_income" and e.text.startswith("36.00 USD over 1 of 1 day checked")


def test_mg2_earnings_is_the_stored_consequence_with_no_days():
    head = MoneyHead(True, Decimal("3"), Decimal("5"), "USD", None)
    i = inp(money_heads={"F1": head}, lead_findings={"GENERATOR_SUPPORT_CANDIDATE": "F1"})
    e = EV.nodes(i, "MG-2")["earnings"]
    assert (e.days, e.basis, e.text) == (None, "NOT_KNOWN", "3.00 to 5.00 USD")
    assert EV.nodes(inp(), "MG-2")["earnings"].text == "Not known yet"


# ---- A3.3 potential (R11, R12, R13; CH6a2-R Q1, Q2, Q4) ---------------------------------------------------------

def item(state="OPEN", status="SUPPORTED", headroom=("18", "20"), day_grades=None, limit_line=None):
    study = {"status": status, "headroom_kw": None if headroom is None else {"low": headroom[0], "high": headroom[1]},
             "window_hours": 6, "first_day": "2026-10-07", "last_day": "2026-10-11"}
    if day_grades is not None:
        study["day_grades"] = day_grades
    return {"state": state, "study": study, "limit_line": limit_line}


PRICE = {"amount": "0.25", "currency": "USD"}


def test_potential_supported_value_and_money_lines():
    p = EV.nodes(inp(opportunity=item(), price=PRICE), "MG-1")["potential"]
    assert p.text == "18–20 kW of daytime solar unused\n4.50–5.00 USD per hour of use, at the declared price"
    assert p.value == {"low": "18", "high": "20", "unit": "kW", "money_low": "4.50", "money_high": "5.00",
                       "currency": "USD"}
    assert (p.days, p.basis) == (None, "NOT_KNOWN")          # the item carries no study day grades (MD-CH6-4)


def test_potential_supported_without_a_price_is_one_line():
    p = EV.nodes(inp(opportunity=item()), "MG-1")["potential"]
    assert p.text == "18–20 kW of daytime solar unused" and "money_low" not in p.value


def test_potential_limited_is_the_limit_line_only():
    p = EV.nodes(inp(opportunity=item(status="LIMITED", headroom=None, limit_line=LIMIT_MIXED), price=PRICE),
                 "MG-1")["potential"]
    assert (p.text, p.value) == (LIMIT_MIXED, None) and "\n" not in p.text


def test_potential_days_from_the_study_day_grades():
    grades = {"2026-10-07": "COMPLETE", "2026-10-08": "COMPLETE", "2026-10-09": "COMPLETE",
              "2026-10-10": "PARTIAL", "2026-10-11": "LOW"}
    p = EV.nodes(inp(opportunity=item(day_grades=grades), price=PRICE), "MG-1")["potential"]
    assert p.days == {"complete": 3, "partial": 1, "low": 1, "no_data": 0, "pending": 0, "expected": 5}
    assert p.basis == "CHECKED_DAYS"


@pytest.mark.parametrize("state", ["OPEN", "RECURRED", "REOPENED", "CHANGE_APPLIED", "ACTION_IN_HAND"])
def test_potential_shown_in_q4_states(state):
    assert EV.nodes(inp(opportunity=item(state=state)), "MG-1")["potential"].value is not None


@pytest.mark.parametrize("state", ["RESOLVED_MONITORING", "CLOSED", "WITHDRAWN"])
def test_potential_none_in_other_states(state):
    p = EV.nodes(inp(opportunity=item(state=state), price=PRICE), "MG-1")["potential"]
    assert (p.value, p.text, p.basis) == (None, "No potential found yet", "NOT_KNOWN")


def test_potential_none_without_a_thread_and_states_are_the_ruling():
    assert EV.nodes(inp(), "MG-1")["potential"].text == "No potential found yet"
    # CH6a3-R D2: defined by exclusion over every lifecycle state.
    assert set(POTENTIAL_STATES) == {"OPEN", "RECURRED", "REOPENED", "CHANGE_APPLIED", "ACTION_IN_HAND"}


def test_action_in_hand_shows_the_study_but_no_signal():
    it = item(state="ACTION_IN_HAND")
    assert EV.nodes(inp(opportunity=it, price=PRICE), "MG-1")["potential"].value is not None
    assert headroom_signal_on(it) is False


def test_ev_potential_is_the_warning_title():
    w = SimpleNamespace(kind="CHARGERS_MOSTLY_IDLE", title="Chargers used under a fifth of capacity")
    assert EV.nodes(inp(warnings=(w,)), "EV-3")["potential"].text == "Chargers used under a fifth of capacity"
    p = EV.nodes(inp(), "EV-3")["potential"]
    assert (p.text, p.days, p.basis) == ("No potential found yet", None, "NOT_KNOWN")


def test_cold_has_no_potential_or_earnings():
    n = EV.nodes(inp(), "CC-1")
    assert n["potential"] is None and n["earnings"] is None


def test_headroom_signal_on_is_open_or_recurred():
    assert [headroom_signal_on({"state": s}) for s in ("OPEN", "RECURRED", "REOPENED", "CHANGE_APPLIED")] == [
        True, True, False, False]
    assert headroom_signal_on(None) is False


# ---- CH-6a1 L1-L3 -----------------------------------------------------------------------------------------------

def test_l1_day_grade_is_the_one_day_rule():
    c = grade_counts([row(1, "COMPLETE"), row(1, "NOT_EXPECTED", subject="asset:b"),
                      row(2, "NO_DATA"), row(2, "NOT_EXPECTED", subject="asset:b"),
                      row(3, "NOT_EXPECTED")])
    assert (c["COMPLETE"], c["NO_DATA"], c["NOT_EXPECTED"]) == (1, 1, 1)


def _earn(rows):
    rec = records_for("MEASURE:productive_kwh", "earnings")[0]
    return REGISTRY.resolve(rec.strategy).effect(ContributionContext(rec, day_rows=tuple(rows)))


def test_l2_a_low_day_adds_no_money_even_for_its_complete_subject():
    e = _earn([row(1, "COMPLETE", amount="2"), row(1, "LOW", subject="asset:b", amount="9"),
               row(2, "COMPLETE", amount="1")])
    assert e.money == {"amount": Decimal("1"), "currency": "USD"} and e.days["LOW"] == 1


@pytest.mark.parametrize("currency", [None, "None", ""])
def test_l3_an_amount_without_a_currency_is_not_priced(currency):
    e = _earn([row(1, "COMPLETE", amount="2", currency=currency)])
    assert e.money is None and e.reason == NOT_PRICED


def test_evaluator_is_frozen_input():
    i = inp()
    with pytest.raises(Exception):
        i.site_code = "x"  # type: ignore[misc]
    assert replace(i, site_code="y").site_code == "y"


def test_q1_a_limited_study_with_a_stored_headroom_has_no_money_line():
    p = EV.nodes(inp(opportunity=item(status="LIMITED", limit_line=LIMIT_MIXED), price=PRICE), "MG-1")["potential"]
    assert (p.text, p.value) == (LIMIT_MIXED, None)


# ---- CH6a3-R Q3: the price basis of a money claim -------------------------------------------------------------

def _priced(day, grade, amount, rev):
    r = row(day, grade, amount=amount)
    return r._replace(money={**r.money, "assumption_revision_id": rev}) if hasattr(r, "_replace") else         __import__("dataclasses").replace(r, money={**r.money, "assumption_revision_id": rev})


def test_earnings_one_price_names_the_declared_price():
    rows = [_priced(7, "COMPLETE", "2.50", "r1"), _priced(8, "COMPLETE", "2.50", "r1")]
    e = EV.nodes(inp(rows, hi=8, lo=7, price={**PRICE, "revision_id": "R1"}), "MG-1")["earnings"]
    assert e.value["kwh"] == "20" and e.value["price"] == {"amount": "0.25", "currency": "USD"}
    assert "price_count" not in e.value
    # CH6a3-R2 M5: kWh x price reproduces the figure the line explains
    assert Decimal(e.value["kwh"]) * Decimal(e.value["price"]["amount"]) == Decimal(e.value["amount"])


def test_earnings_price_of_another_revision_prints_no_price_line():
    """CH6a3-R2 M5: the declared price at hi is not the counted rows' revision (or carries none): no price line."""
    rows = [_priced(7, "COMPLETE", "2.50", "r1"), _priced(8, "COMPLETE", "2.50", "r1")]
    for price in ({**PRICE, "revision_id": "r2"}, PRICE):
        e = EV.nodes(inp(rows, hi=8, lo=7, price=price), "MG-1")["earnings"]
        assert e.value["amount"] == "5.00" and "price" not in e.value and "price_count" not in e.value


def test_earnings_several_prices_counts_them_and_never_names_one():
    rows = [_priced(7, "COMPLETE", "2.50", "r1"), _priced(8, "COMPLETE", "3.00", "r2")]
    e = EV.nodes(inp(rows, hi=8, lo=7, price=PRICE), "MG-1")["earnings"]
    assert e.value["price_count"] == 2 and "price" not in e.value


def test_earnings_low_day_is_not_known_with_days():
    e = EV.nodes(inp([row(9, "LOW", amount="9.00")], hi=9, lo=9, price=PRICE), "MG-1")["earnings"]
    assert (e.value, e.text) == (None, "Not known yet") and e.days["low"] == 1


def test_fuel_basis_from_the_stored_consequence():
    from assetops_backend.chain.outcomes import fuel_basis
    head = SimpleNamespace(body={"consequence": {"quantity": {"low": "1.2", "high": "1.8", "unit": "L"},
                                                 "price": {"value": "1.10", "currency": "USD"}}})
    assert fuel_basis(head) == {"litres_low": "1.2", "litres_high": "1.8",
                                "price": {"amount": "1.10", "currency": "USD"}}
    assert fuel_basis(SimpleNamespace(body={"consequence": {"quantity": {"low": "1", "high": "2"},
                                                            "price": {"value": None}}})) is None


def test_site_nodes_only_for_outcomes_with_a_record_or_objective():
    from assetops_backend.chain.outcomes import site_nodes
    out = site_nodes(inp(), ["MG-1", "MG-4", "MG-7"])
    assert set(out) == {"MG-1"} and out["MG-1"]["kpi"]["text"] == "No target set yet"
