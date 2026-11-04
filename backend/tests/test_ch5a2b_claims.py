"""CH-5a2b L0 (build sheet CH-5a §B13 R2/R3, §B14; CH-6 §S.2): the PC-1 `Claim`, the one `count_basis`, the count
texts, `provenance_suffix`, the one thread classifier and the public GradeCounts-from-DayFacts function. Pure."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from assetops_backend.chain.read import DayFacts
from assetops_backend.chain.reader import GradeCounts, grade_counts_of
from assetops_backend.chain.threads import classify
from assetops_backend.chain.vocabulary import Claim, count_basis, count_claim, provenance_suffix, sum_days


def days(complete=0, partial=0, low=0, no_data=0, pending=0, expected=None):
    exp = complete + partial + low + no_data + pending if expected is None else expected
    return {"complete": complete, "partial": partial, "low": low, "no_data": no_data, "pending": pending,
            "expected": exp}


@pytest.mark.parametrize("d, basis", [
    (None, "NOT_KNOWN"), (days(expected=0), "NOT_KNOWN"), (days(pending=2, no_data=1), "NOT_KNOWN"),
    (days(complete=7), "COMPLETE"), (days(complete=6, partial=1), "CHECKED_DAYS"),
    (days(complete=1, no_data=6), "CHECKED_DAYS"), (days(low=3), "CHECKED_DAYS")])
def test_count_basis_is_the_one_rule(d, basis) -> None:
    assert count_basis(d) == basis


def test_count_basis_takes_grade_counts() -> None:
    g = GradeCounts(requested=7, expected=7, complete=7, partial=0, low=0, no_data=0, not_expected=0, pending=0,
                    enough_data_days=7)
    assert count_basis(g) == "COMPLETE"
    assert sum_days([g, days(complete=6, partial=1)]) == days(complete=13, partial=1)
    assert sum_days([g, None]) is None


@pytest.mark.parametrize("key, value, d, text", [
    ("count.open_threads", 1, days(complete=7), "1 open finding"),
    ("count.open_threads", 3, days(complete=7), "3 open findings"),
    ("count.open_threads", 2, days(complete=5, partial=2), "2 open on the days checked"),
    ("count.open_threads", 0, days(complete=5, partial=2), "None open on the days checked"),
    ("count.verified_results", 1, days(complete=7), "1 fix confirmed"),
    ("count.verified_results", 2, days(complete=7), "2 fixes confirmed"),
    ("count.verified_results", 1, days(complete=1, low=1), "1 confirmed on the days checked"),
    ("count.verified_results", 0, days(complete=1, low=1), "None confirmed on the days checked"),
    ("count.opportunities", 1, days(complete=7), "1 opportunity"),
    ("count.opportunities", 0, days(complete=7), "0 opportunities"),
    ("count.opportunities", 1, days(complete=6, no_data=1), "1 found on the days checked"),
    ("count.opportunities", 0, days(complete=6, no_data=1), "None found on the days checked"),
    ("count.opportunities", 1, None, "Not known yet"),
    ("count.opportunities", None, days(complete=7), "Not known yet")])
def test_count_claim_texts(key, value, d, text) -> None:
    c = count_claim(key, value, d)
    assert c.text == text
    assert c.basis == ("NOT_KNOWN" if value is None or d is None else count_basis(d))


def test_claim_wire_shape() -> None:
    assert count_claim("count.opportunities", 2, days(complete=7)).to_json() == {
        "key": "count.opportunities", "value": 2, "basis": "COMPLETE", "days": days(complete=7),
        "text": "2 opportunities"}
    assert Claim("money.x", Decimal("1.50"), "COMPLETE", None, "t").to_json()["value"] == "1.50"


def test_provenance_suffix() -> None:
    assert provenance_suffix("REGISTERED_SIMULATION") == provenance_suffix("AUTHORED_DEMONSTRATION") == " on example data"
    assert provenance_suffix("MEASURED_FIELD") == provenance_suffix(None) == provenance_suffix("MIXED") == ""


def test_classify_thread_states() -> None:
    states = ["OPEN", "RECURRED", "REOPENED", "ACTION_IN_HAND", "CHANGE_APPLIED", "RESOLVED_MONITORING", "CLOSED",
              "WITHDRAWN", None]
    assert classify(states) == {"open": 3, "in_hand": 2, "verified": 2}


def test_grade_counts_of_day_facts() -> None:
    d1, d2, d3 = date(2026, 10, 30), date(2026, 10, 31), date(2026, 11, 1)
    facts = DayFacts(days=(d1, d2, d3), grades={d1: {"m": {"s": "COMPLETE"}}, d2: {"m": {"s": "PARTIAL"}}},
                     settled=True, readiness="FULL", gaps=())
    g = grade_counts_of(facts, ["m"])
    assert (g.requested, g.expected, g.complete, g.partial, g.no_data) == (3, 3, 1, 1, 1)
