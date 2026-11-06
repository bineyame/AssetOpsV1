"""CH-6a2 L0 (build sheet CH-6 R8, R11, §S.2, §A4; CH6a2-R Q1, Q3, Q5, Q6): the node claim texts. Pure."""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from assetops_backend.chain import vocabulary as v
from assetops_backend.outcomes.objectives import ObjectiveFact, judge_month
from assetops_backend.site_outcomes import mini

FIXTURE = Path(__file__).resolve().parents[2] / "frontend" / "src" / "shell" / "__fixtures__" / "money-text.json"


def _days(complete=0, partial=0, low=0, no_data=0, pending=0, expected=None):
    e = complete + partial + low + no_data + pending if expected is None else expected
    return {"complete": complete, "partial": partial, "low": low, "no_data": no_data, "pending": pending,
            "expected": e}


def test_money_text_equals_board_money_text_on_the_shared_fixture():
    rows = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert len(rows) > 10
    for row in rows:
        assert v.money_text(row["low"], row["high"], row["currency"]) == row["text"], row


def test_money_text_one_amount_and_money2():
    assert v.money_text("2.5") == "2.50"
    assert v.money_text("2.5", None, "USD") == "2.50 USD"
    assert v.money_text(None) is None
    assert [v.money2(x) for x in ("0.005", "0.015", "-0.001", "-1.255", "10")] == [
        "0.00", "0.02", "0.00", "-1.26", "10.00"]


A4 = {
    "money.days": "{amount} over {k} of {m} days checked",
    "money.days_partial": "{amount} over {k} of {m} days checked · {p} partly checked",
    "money.income_suffix": " · not billed or collected",
    "money.not_known": "Not known yet",
    "money.currency_mixed": "Not shown · amounts in more than one currency",
    "potential.value": "{lo}–{hi} kW of daytime solar unused",
    "potential.money": "{lo}–{hi} {cur} per hour of use, at the declared price",
    "potential.none": "No potential found yet",
    "target.none": "No target set yet",
    "target.days_none": "No target, so no days are judged yet",
    "days_line.many": "{k} of {m} days checked",
    "days_line.partial": " · {p} partly checked",
    "days_line.low": " · {n} with too little data, not counted",
    "days_line.no_data_one": "No readings on {day}",
    "row.target_note": "{k} of {m} outcomes have a target",
    # CH-6b1: the income earnings nodes
    "income.at_least": "At least {total} estimated income, from checked days",
    "income.site": "{site}: {text}",
    "income.site_not_known": "{site}: not known yet",
    "income.total": "Estimated income from checked days: {total}",
}


def test_templates_are_the_a4_table():
    assert v.NODE_TEXT == A4


def test_mg1_texts_moved_unchanged_and_mini_imports_them():
    assert v.MG1_SO_FAR == "{mtd} kWh so far this month, on {c} of {e} days checked"
    assert v.MG1_PACE == v.MG1_SO_FAR + " · averages {avg} kWh a day; the target needs {need} kWh a day"
    assert v.MG1_TOO_EARLY == ("{mtd} kWh so far this month, on {c} checked {d}; too early to judge "
                               "(needs {k} checked days)")
    assert v.MG1_MISSED == "{mtd} kWh this month, all {m} days checked"
    for name in ("MG1_SO_FAR", "MG1_PACE", "MG1_TOO_EARLY", "MG1_MISSED"):
        assert getattr(mini, name) is getattr(v, name)
    assert v.MG1_NO_DAY == mini.MG1_ACTUAL


def _mg1(target="300", k=3):
    return ObjectiveFact("MG-1", "productive_use_kwh", "AT_LEAST", Decimal(target), False, "t", "DECLARED", "r",
                         min_checked_days=k)


def test_mg1_text_with_no_counted_day():
    assert v.mg1_text("NOT_JUDGED", None, 0, 5, 31, Decimal("300"), 3) == "sales not recorded"


def test_verdict_claim():
    c = v.verdict_claim("MG-1", "ON_PACE", _days(complete=3, expected=3), "x")
    assert (c.key, c.value, c.basis, c.text) == ("verdict.MG-1", "ON_PACE", "COMPLETE", "x")
    c = v.verdict_claim("CC-1", "NOT_JUDGED", _days(complete=1, no_data=1), None)
    assert c.basis == "CHECKED_DAYS" and c.text == "Not known yet"
    # CH6a2-R Q6: no objective -> nothing judged: no days, NOT_KNOWN, "No target set yet".
    c = v.verdict_claim("EV-3", None, _days(complete=3), "ignored")
    assert (c.value, c.days, c.basis, c.text) == (None, None, "NOT_KNOWN", "No target set yet")


def test_money_claim_texts():
    m = {"amount": Decimal("7.5"), "currency": "USD"}
    c = v.money_claim("estimated_income", m, _days(complete=3))
    assert c.text == "7.50 USD over 3 of 3 days checked · not billed or collected" and c.basis == "COMPLETE"
    assert c.to_json()["value"] == {"amount": "7.5", "currency": "USD"}
    c = v.money_claim("estimated_income", m, _days(complete=6, partial=1, low=1))
    assert c.text == "7.50 USD over 6 of 8 days checked · 1 partly checked · not billed or collected"
    assert c.basis == "CHECKED_DAYS"
    c = v.money_claim("estimated_income", None, _days(complete=2), "CURRENCY_MIXED")
    assert (c.value, c.basis, c.text) == (None, "NOT_KNOWN", "Not shown · amounts in more than one currency")
    assert v.money_claim("estimated_income", None, _days(), "NO_RECORDS").text == "Not known yet"
    # A stored consequence range with no days (CH6a2-R Q2): NOT_KNOWN, the amount alone, no income suffix.
    c = v.money_claim("possible_extra_fuel_cost", {"low": Decimal("3"), "high": Decimal("5"), "currency": "USD"},
                      None)
    assert (c.basis, c.days, c.text) == ("NOT_KNOWN", None, "3.00 to 5.00 USD")
    assert c.value == {"low": "3", "high": "5", "currency": "USD"}


def test_potential_claim_lines():
    money = {"low": Decimal("4.5"), "high": Decimal("5"), "currency": "USD"}
    c = v.potential_claim("daytime_solar_headroom", {"low": "18"}, None,
                          v.potential_lines(Decimal("18.0"), Decimal("20"), money))
    assert c.text == "18–20 kW of daytime solar unused\n4.50–5.00 USD per hour of use, at the declared price"
    assert c.basis == "NOT_KNOWN" and c.key == "potential.daytime_solar_headroom"
    assert v.potential_lines(Decimal("18"), Decimal("20"), None) == ["18–20 kW of daytime solar unused"]
    assert v.potential_claim("x", None, None, []).text == "No potential found yet"


def test_days_line():
    assert v.days_line(None) is None
    assert v.days_line(_days(complete=3, partial=1, low=1)) == (
        "3 of 5 days checked · 1 partly checked · 1 with too little data, not counted")
    assert v.days_line(_days(complete=2, pending=1)) == "2 of 3 days checked"
    assert v.days_line(_days(no_data=1), date(2026, 11, 1)) == "No readings on 1 Nov"
    assert v.days_line(_days(no_data=1)) == "0 of 1 days checked"
