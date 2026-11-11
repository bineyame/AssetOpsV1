"""PARTIAL-MONEY (D-E5.45 owner option 2, label D-E5.46): a PARTIAL mini-grid Site's money is the lines of its
analysed Site-local days only, never estimated, scaled or filled for a gap day. Fake one-transaction snapshots over
the real `site_coverage` and `select_financial_scope`; no database."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from assetops_backend.estate import coverage, financials
from assetops_backend.estate.scope import EstateRequest
from test_cov_partial import D0, PRICED, S, T, Snap, day, head
from test_estate_coverage_local_days import LOCAL, N, grades
from test_gap_reasons import CONFLICT, TOO_FEW, indeterminate

K = D0 + timedelta(days=N + 1)
SITE = {"site_id": S, "site_code": "KOBO 001", "site_name": "Kobo", "site_type": "MINIGRID",
        "site_code_key": "kobo 001"}
OPERATING = financials.OPERATING


class MoneySnap(Snap):
    """`Snap` whose stored consequence is per Finding revision (one priced line per head)."""

    def __init__(self, days, heads, prices) -> None:
        super().__init__(days, heads)
        self.prices = prices

    def consequence(self, t, s, frid, k):
        low, high, currency = self.prices[str(frid)]
        h = next(x for x in self._heads if x["finding_revision_id"] == str(frid))
        n = str(frid)[-1]
        return {**PRICED, "consequence_revision_id": f"c{n}", "amount_low": low, "amount_high": high,
                "currency": currency, "price": {"value": "1.2", "state": "DECLARED"},
                "cited": {"assumption_revision_ids": ["p1"], "power_evidence_ids": [f"e{n}"]},
                "window_start": h["episode_start"], "window_end": h["episode_end"], "quantity_low": "1",
                "quantity_high": "2", "quantity_unit": "L"}


def on_day(n: int, hours: tuple[int, int] = (8, 9)) -> dict:
    base = D0 + timedelta(days=n)
    return head(base + timedelta(hours=hours[0]), base + timedelta(hours=hours[1]), n)


def scope_of(monkeypatch, days, heads, prices, day_grades):
    monkeypatch.setattr(coverage, "day_grades_provider", lambda *a: (day_grades, None))
    req = EstateRequest(kind="financials", from_=D0, to=D0 + timedelta(days=N), known_at=None)
    per_site, lines, applicable, *_ = financials.select_financial_scope(
        MoneySnap(days, heads, prices), T, req, {"k": K, "sites": [SITE]})
    (_, _, cov, site_lines), = per_site
    return cov, site_lines, lines, applicable


def week(prices_by_day: dict[int, tuple[str, str, str]]):
    heads = [on_day(n) for n in prices_by_day]
    return heads, {h["finding_revision_id"]: prices_by_day[n] for n, h in zip(prices_by_day, heads)}


SIX = {n: (f"{n + 1}.00", f"{n + 2}.50", "USD") for n in (0, 1, 2, 4, 5, 6)}


def test_1_one_no_readings_day_amount_is_exactly_the_other_six_days_lines(monkeypatch) -> None:
    heads, prices = week({**SIX, 3: ("1000.00", "2000.00", "USD")})
    cov, site_lines, _, _ = scope_of(monkeypatch, [day(i) for i in range(N)], heads, prices, grades(d3="NO_DATA"))
    assert cov["state"] == "PARTIAL"
    block = financials.partial_money(SITE, cov, site_lines)
    assert block["amount"] == {"low": str(sum(Decimal(p[0]) for p in SIX.values())),
                               "high": str(sum(Decimal(p[1]) for p in SIX.values())), "currency": "USD"}
    assert (block["state"], block["analysed_days"], block["requested_days"], block["line_count"]) == (
        "SUMMED", 6, 7, 6)
    assert block["gaps"] == [{"day": LOCAL[3].isoformat(), "state": "UNASSESSED", "reason": "NO_READINGS"}]


def test_2_a_gap_days_own_line_is_never_included(monkeypatch) -> None:
    spanning = head(D0 + timedelta(days=2, hours=22), D0 + timedelta(days=3, hours=2), 7)
    heads, prices = week({**SIX, 3: ("1000.00", "2000.00", "USD")})
    prices[spanning["finding_revision_id"]] = ("500.00", "600.00", "USD")
    cov, site_lines, lines, _ = scope_of(monkeypatch, [day(i) for i in range(N)], [*heads, spanning], prices,
                                         grades(d3="NO_DATA"))
    keys = {x["consequence_revision_id"] for x in site_lines}
    assert "c3" not in keys and "c7" not in keys and len(site_lines) == 6
    assert [(x["eligibility"], x["reason_codes"]) for x in site_lines] == [("ELIGIBLE", [])] * 6
    # the Site's Finding rows: a head on a no-readings day is not shown (D-E5.42 rule, unchanged); the analysed-day
    # heads are priced
    by_frid = {r["finding_revision_id"]: r["consequence"] for r in cov["rows"]}
    assert heads[-1]["finding_revision_id"] not in by_frid and spanning["finding_revision_id"] not in by_frid
    assert by_frid[heads[0]["finding_revision_id"]]["amount_low"] == "1.00"


@pytest.mark.parametrize("limits", [CONFLICT, TOO_FEW])
def test_2b_a_data_gap_days_finding_row_shows_no_current_amount_and_has_no_line(monkeypatch, limits) -> None:
    spanning = head(D0 + timedelta(days=2, hours=22), D0 + timedelta(days=3, hours=2), 7)
    heads, prices = week({**SIX, 3: ("1000.00", "2000.00", "USD")})
    prices[spanning["finding_revision_id"]] = ("500.00", "600.00", "USD")
    days = [indeterminate(i, limits) if i == 3 else day(i) for i in range(N)]
    cov, site_lines, _, _ = scope_of(monkeypatch, days, [*heads, spanning], prices, grades())
    by_frid = {r["finding_revision_id"]: r["consequence"] for r in cov["rows"]}
    for h in (heads[-1], spanning):  # shown (a data fact withholds no Finding), but never current money
        assert by_frid[h["finding_revision_id"]]["state"] == "UNKNOWN"
        assert by_frid[h["finding_revision_id"]]["amount_low"] is None
    assert {x["consequence_revision_id"] for x in site_lines} == {"c0", "c1", "c2", "c4", "c5", "c6"}


def test_3_category_covered_only_for_partial_with_an_analysed_day(monkeypatch) -> None:
    heads, prices = week(SIX)
    _, _, _, applicable = scope_of(monkeypatch, [day(i) for i in range(N)], heads, prices, grades(d3="NO_DATA"))
    assert applicable == {OPERATING: True}
    real = financials.site_coverage

    def none_analysed(*a, **kw):
        out = real(*a, **kw)
        return {**out, "days": {**out["days"], "checked": 0}}
    monkeypatch.setattr(financials, "site_coverage", none_analysed)
    _, site_lines, _, applicable = scope_of(monkeypatch, [day(i) for i in range(N)], heads, prices,
                                            grades(d3="NO_DATA"))
    assert applicable == {OPERATING: False} and site_lines == []


def test_4_a_pending_site_is_still_withheld(monkeypatch) -> None:
    heads, prices = week(SIX)
    cov, site_lines, _, applicable = scope_of(monkeypatch, [day(i) for i in range(N)], heads, prices,
                                              grades(d3="PENDING"))
    assert cov["state"] == "PENDING_RECOMPUTE"
    assert site_lines == [] and applicable == {OPERATING: False}
    assert financials.partial_money(SITE, cov, site_lines) is None


def test_6_no_total_across_currencies(monkeypatch) -> None:
    heads, prices = week({0: ("1.00", "2.00", "USD"), 1: ("3.00", "4.00", "KES")})
    cov, site_lines, _, _ = scope_of(monkeypatch, [day(i) for i in range(N)], heads, prices, grades(d3="NO_DATA"))
    block = financials.partial_money(SITE, cov, site_lines)
    assert block["state"] == "CURRENCY_MIXED" and block["amount"] is None
    assert block["analysed_days"] == 6 and block["line_count"] == 2


@pytest.mark.parametrize("limits,reason", [(CONFLICT, "READINGS_CONFLICT"), (TOO_FEW, "NOT_ENOUGH_READINGS")])
def test_a_data_gap_day_is_out_of_the_money_and_the_analysed_count_alike(monkeypatch, limits, reason) -> None:
    """The money, its "n of m analysed" count and the coverage line's gap clause read one day set: the Site's
    `days` block. A conflict / not-enough day graded COMPLETE by the chain is still not an analysed day here."""
    heads, prices = week({**SIX, 3: ("1000.00", "2000.00", "USD")})
    days = [indeterminate(i, limits) if i == 3 else day(i) for i in range(N)]
    cov, site_lines, _, _ = scope_of(monkeypatch, days, heads, prices, grades())  # every day COMPLETE-graded
    assert cov["state"] == "PARTIAL"
    block = financials.partial_money(SITE, cov, site_lines)
    assert "c3" not in {x["consequence_revision_id"] for x in site_lines}
    assert block["analysed_days"] == cov["days"]["checked"] == 6 and block["requested_days"] == 7
    assert block["gaps"] == cov["days"]["gaps"] == [{"day": LOCAL[3].isoformat(), "state": "UNASSESSED",
                                                     "reason": reason}]
    assert Decimal(block["amount"]["low"]) == sum(Decimal(p[0]) for p in SIX.values())


def test_a_current_site_has_no_partial_money_block(monkeypatch) -> None:
    heads, prices = week(SIX)
    cov, site_lines, _, _ = scope_of(monkeypatch, [day(i) for i in range(N)], heads, prices, grades())
    assert cov["state"] == "CURRENT" and len(site_lines) == 6
    assert financials.partial_money(SITE, cov, site_lines) is None
