"""CH-6a3 R2a L2m (build sheet CH6a3-R2, H2; section A8 item 3): the Kobo Grow row's node claims on `mechanism_db()`
(the MD-0 Kobo mechanism Site, 14 days), asserted by recomputation from the stored `site_day_snapshot` rows.

- The MD-0 data has COMPLETE `productive_kwh` days, so NOT_KNOWN on a window that holds COMPLETE days is a defect.
- The earnings amount is the sum of the stored day money of the counted days; the "Why?" price line reproduces the
  figure as kWh x price (M5); ONE-SOURCE (H3): money, subline and sales line all come from the earnings claim.
- The mechanism Site is Kobo only (MD0-S2): the EV one-source case is `test_out_b3_cold_ev.py` (stored-row fakes).
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import text

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_md0_mechanism_postgres import mech  # noqa: F401  (the clone + derive fixture)

    import mechanism_dataset as md
    import test_out_b4_board_postgres as b4

SPEC = md.load() if URL else None
COUNTED = ("COMPLETE", "PARTIAL")


def _stored(engine, site_id, lo, hi) -> list[dict]:
    """The latest-revision `productive_kwh` rows of the Site over [lo, hi] (the rows the evaluator reads)."""
    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT DISTINCT ON (local_day, subject_kind, subject_ref) local_day, grade, value, money "
            "FROM site_day_snapshot WHERE site_id = :s AND measure = 'productive_kwh' "
            "AND local_day BETWEEN :lo AND :hi ORDER BY local_day, subject_kind, subject_ref, revision DESC"),
            {"s": site_id, "lo": lo, "hi": hi}).mappings().all()
    return [dict(r) for r in rows]


def _grow(body: dict) -> dict:
    return next(r for r in body["rows"] if r["category"] == "GROW_REVENUE")


def _expected_earnings(rows: list[dict]) -> tuple[int, Decimal, Decimal]:
    """(counted days, sum of stored day money, sum of stored kWh) over the COUNTED days that carry money."""
    counted = [r for r in rows if r["grade"] in COUNTED and r["money"] and r["money"].get("amount") is not None]
    money = sum((Decimal(str(r["money"]["amount"])) for r in counted), Decimal(0))
    kwh = sum((Decimal(str(r["value"]["kwh"])) for r in counted), Decimal(0))
    return len(counted), money, kwh




def check_earnings(row: dict, stored: list[dict]) -> None:
    """Earnings node against the stored rows of the board day (recomputed, never a literal). NOT_KNOWN on a COMPLETE
    day is a defect; a day with no counted row reads "Not known yet" and states no money."""
    e = row["nodes"]["earnings"]
    assert e is not None, row["nodes"]
    days, money, kwh = _expected_earnings(stored)
    if not days:
        assert e["basis"] == "NOT_KNOWN" and e["value"] is None and row["headline_money"] is None, (e, row)
        return
    assert e["basis"] != "NOT_KNOWN", e  # COMPLETE stored day: a NOT_KNOWN here is a defect
    assert Decimal(str(e["value"]["amount"])) == money, (e, money)
    assert Decimal(str(e["value"]["kwh"])) == kwh, (e, kwh)
    assert e["days"]["complete"] == sum(1 for r in stored if r["grade"] == "COMPLETE"), e["days"]
    hm = row["headline_money"]
    assert Decimal(hm["amount_low"]) == Decimal(hm["amount_high"]) == money, (hm, money)


def check_price_line(row: dict) -> None:
    """The "Why?" energy price line exists for a known figure and reproduces it: kWh x price == amount (M5)."""
    from assetops_backend.chain.why import price_lines

    e = row["nodes"]["earnings"]
    energy, _fuel = price_lines(e)
    assert energy is not None, e
    price = Decimal(str(e["value"]["price"]["amount"]))
    assert Decimal(str(e["value"]["kwh"])) * price == Decimal(str(e["value"]["amount"])), e["value"]
    assert f"{price.normalize():f}" in energy and f"{Decimal(str(e['value']['kwh'])).normalize():f}" in energy, energy


def check_one_source(row: dict) -> None:
    """H3: money, subline and the sales line all state the earnings claim's kWh and price, nothing else."""
    from assetops_backend.site_outcomes.mini import num, price_text

    e = row["nodes"]["earnings"]["value"]
    kwh, price = num(Decimal(str(e["kwh"]))), price_text(e["price"]["amount"])
    sales = next(x["text"] for x in row["contributors"] if x["key"] == "productive_sales")
    assert sales.startswith(f"{kwh} kWh used by"), (sales, kwh)
    assert row["subline"].startswith(sales) and f"at the declared price of {price} " in row["subline"], row["subline"]
    hm = row["headline_money"]
    assert Decimal(hm["amount_low"]) == Decimal(str(e["amount"])), (hm, e)


def test_kobo_grow_row_recomputes_from_the_stored_rows(mech, monkeypatch, tmp_path) -> None:  # noqa: F811
    import calendar
    import copy
    from datetime import date

    from assetops_backend.outcomes.objectives import Reading, judge_month
    from assetops_backend.chain.outcomes import OutcomeEvaluator

    engine, m = mech
    url = engine.url.render_as_string(hide_password=False)
    b4._settle_chain(url, "KOBO-001")
    b4._serve(monkeypatch, url, tmp_path)
    facts: list = []
    real = OutcomeEvaluator._reading

    def spy(self, inp, o):  # the declared MG-1 fact the evaluator judged, for the independent judge_month
        facts.append(o)
        return real(self, inp, o)

    monkeypatch.setattr(OutcomeEvaluator, "_reading", spy)
    seen: dict[int, tuple[dict, list[dict]]] = {}
    with b4._client() as c:
        for n in range(7, 14):  # the board is one Site-local day per request; the D7-D13 week is seven reads
            d = md.day(SPEC, n)
            body, _ = b4._board(c, "KOBO-001", f"mech_d{n}", date=d.isoformat())
            seen[n] = (_grow(body), _stored(engine, m["site_id"], d, d))
    # Every day: earnings recomputed from the stored row; the delivered COMPLETE days are never NOT_KNOWN.
    counted_days = 0
    for n, (row, stored) in seen.items():
        check_earnings(row, stored)
        if _expected_earnings(stored)[0]:
            counted_days += 1
            check_price_line(row)
    assert counted_days >= 3, counted_days  # D10-D13 are delivered COMPLETE days: the set is not empty
    # The week: the sum of the stored day money of the counted days equals the sum of the board days' figures.
    week = _stored(engine, m["site_id"], md.day(SPEC, 7), md.day(SPEC, 13))
    assert sum((Decimal(str(r["nodes"]["earnings"]["value"]["amount"])) for r, _ in seen.values()
                if r["nodes"]["earnings"]["value"]), Decimal(0)) == _expected_earnings(week)[1]
    # ONE-SOURCE on one Kobo day (D13).
    row13, _ = seen[13]
    check_one_source(row13)
    # MG-1 on D13: checked days = COMPLETE productive_kwh days of the month to D13; the verdict is pure judge_month.
    d13 = md.day(SPEC, 13)
    month = _stored(engine, m["site_id"], d13.replace(day=1), d13)
    complete = sum(1 for r in month if r["grade"] == "COMPLETE")
    kpi = row13["nodes"]["kpi"]
    assert kpi["days"]["complete"] == complete and complete >= 3, (kpi["days"], complete)
    mg1 = next(o for o in facts if o.outcome_key == "MG-1")
    value = sum((Decimal(str(r["value"]["kwh"])) for r in month if r["grade"] in COUNTED), Decimal(0))
    reading = Reading(value, d13.day == calendar.monthrange(d13.year, d13.month)[1] and complete == d13.day, None,
                      complete, d13.day, calendar.monthrange(d13.year, d13.month)[1])
    assert kpi["value"] == judge_month(mg1, reading), (kpi, judge_month(mg1, reading))
    # Non-vacuity: each check fails on a wrong board (the defect each one is for).
    wrong = copy.deepcopy(row13)
    wrong["nodes"]["earnings"] = {**wrong["nodes"]["earnings"], "basis": "NOT_KNOWN", "value": None,
                                  "text": "Not known yet"}
    with pytest.raises(AssertionError):  # NOT_KNOWN on a COMPLETE day
        check_earnings(wrong, seen[13][1])
    wrong = copy.deepcopy(row13)
    wrong["nodes"]["earnings"]["value"]["price"]["amount"] = "0.26"
    with pytest.raises(AssertionError):  # price x kWh no longer reproduces the figure
        check_price_line(wrong)
    wrong = copy.deepcopy(row13)
    wrong["contributors"] = [{**x, "text": x["text"].replace("238", "239")} if x["key"] == "productive_sales" else x
                             for x in wrong["contributors"]]
    with pytest.raises(AssertionError):  # the sales line states a kWh the claim does not carry
        check_one_source(wrong)
    wrong = copy.deepcopy(row13)
    wrong["nodes"]["earnings"]["value"]["amount"] = "61.00"
    with pytest.raises(AssertionError):  # the figure differs from the stored rows
        check_earnings(wrong, seen[13][1])
