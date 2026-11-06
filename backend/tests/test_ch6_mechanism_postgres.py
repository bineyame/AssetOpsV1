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


def _cost(body: dict) -> dict:
    return next(r for r in body["rows"] if r["category"] == "OPTIMIZE_COST")


def check_potential_money(row: dict) -> dict:
    """SUPPORTED potential: a kW range and its money line = kW x 1 h x the declared price (the earnings price)."""
    p = row["nodes"]["potential"]
    assert p is not None and p["value"], p  # a study carries no day counts: its basis is not the test
    v = p["value"]
    price = Decimal(str(row["nodes"]["earnings"]["value"]["price"]["amount"]))
    assert v.get("money_low") is not None, v  # SUPPORTED and priced: the money line exists
    assert Decimal(str(v["money_low"])) == Decimal(str(v["low"])) * price, (v, price)
    assert Decimal(str(v["money_high"])) == Decimal(str(v["high"])) * price, (v, price)
    return v


def check_fuel_line(row: dict) -> None:
    """MG-2 earnings: litres x the one declared fuel price equals the figure; with no stored price, no figure/line."""
    e = row["nodes"]["earnings"]
    val = (e or {}).get("value") or {}
    if val.get("litres_low") is None:  # Known Deviation: no stored price, the fuel line is omitted
        assert not val.get("price"), e
        return
    price = Decimal(str(val["price"]["amount"]))
    assert Decimal(str(val["litres_low"])) * price == Decimal(str(val["low"])), (val, price)
    assert Decimal(str(val["litres_high"])) * price == Decimal(str(val["high"])), (val, price)


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
    # H2 (M-R1): the SUPPORTED potential on D13 carries its money line, recomputed as headroom kW x 1 h x the declared price.
    pot = check_potential_money(row13)
    # MG-2 on D11 (MISSED) and D12 (MET): the fuel-cost claim is litres x the one declared fuel price, else the omission.
    with b4._client() as c:
        mg2 = {n: _cost(b4._board(c, "KOBO-001", f"mech_d{n}", date=md.day(SPEC, n).isoformat())[0]) for n in (11, 12)}
    for n, row in mg2.items():
        check_fuel_line(row)
    # FINDING (M-R1): on mechanism_db() the dispatch / chain_findings ports are closed (no Performance comparison
    # report), so MG-2 reads NOT_JUDGED / NOT_KNOWN on D11 and D12 and check_fuel_line takes its omission path. The
    # MISSED / MET verdicts and the litres x price figure cannot be proven here until that port is fed (open item).
    assert all(r["nodes"]["kpi"]["value"] == "NOT_JUDGED" for r in mg2.values()), mg2
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
    wrong["nodes"]["potential"]["value"]["money_high"] = "2.01"
    with pytest.raises(AssertionError):  # the potential money line differs from kW x 1 h x price
        check_potential_money(wrong)
    fuel = {"nodes": {"earnings": {"value": {"litres_low": "2", "litres_high": "4", "low": "1.00", "high": "2.00",
                                             "price": {"amount": "0.50"}}}}}
    check_fuel_line(fuel)  # litres x price reproduces the figure
    fuel["nodes"]["earnings"]["value"]["high"] = "2.10"
    with pytest.raises(AssertionError):  # litres x price no longer reproduces the figure
        check_fuel_line(fuel)
    wrong = copy.deepcopy(row13)
    wrong["nodes"]["earnings"]["value"]["amount"] = "61.00"
    with pytest.raises(AssertionError):  # the figure differs from the stored rows
        check_earnings(wrong, seen[13][1])
