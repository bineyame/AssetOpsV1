"""DD-1b2b O4-O6 L0: the pure parts of the new finish rows (`tools/demo_combined_rows.py`). No database. Each guard has
a case that must fail, so none is vacuous."""
from __future__ import annotations

import copy
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import demo_combined_rows as rows  # noqa: E402
from assetops_backend.chain.vocabulary import MG1_NO_DAY  # noqa: E402

ZERO = {"dirty": 0, "snapshots_pending": 0, "threads_pending": 0, "mini_deferred": 0, "opportunity_live": 0}


def test_drain_summary_passes_at_zero_and_fails_on_any_remaining_count() -> None:
    rec = {"name": "drain-1", "ticks": 3, "N": 5, "over_n": False, "seconds": 9.0, "end": {"KOBO-001": ZERO}}
    assert rows.drain_summary(rec)["ticks"] == 3
    with pytest.raises(AssertionError):
        rows.drain_summary({**rec, "end": {"KOBO-001": {**ZERO, "threads_pending": 1}}})
    with pytest.raises(AssertionError):
        rows.drain_summary({**rec, "end": {}})


def test_a_drain_record_with_verdict_fail_fails_even_with_zero_counts() -> None:
    rec = {"name": "drain-1", "ticks": 3, "N": 5, "over_n": False, "seconds": 9.0, "end": {"KOBO-001": ZERO},
           "verdict": "done"}
    assert rows.drain_summary(rec)["ticks"] == 3
    with pytest.raises(AssertionError):
        rows.drain_summary({**rec, "verdict": "fail", "reason": "counts failed"})


def test_expected_threads_group_by_site_and_mechanism_in_episode_order() -> None:
    portfolio = [
        {"finding_id": "B", "site_code": "KOBO-001", "mechanism": "GEN", "episode_start": "2026-11-02"},
        {"finding_id": "A", "site_code": "KOBO-001", "mechanism": "GEN", "episode_start": "2026-11-01"},
        {"finding_id": "C", "site_code": "COLD-LAB-001", "mechanism": "COLD", "episode_start": "2026-11-01"},
        {"finding_id": "E", "site_code": "EV-LAB-001", "mechanism": "EVI", "episode_start": "2026-11-01"},
    ]
    kobo = {"days": [{"findings": ["B", "A"]}]}
    cold = {"days": [{"findings": ["C"]}]}
    out = rows.build_expected_threads(kobo, cold, portfolio, {"study": {"opportunity_id": "OPP-1"}})
    by = {t["name"]: t for t in out}
    assert by["kobo-gen"]["findings"] == ["a", "b"]
    assert by["cold-cold"]["findings"] == ["c"] and by["ev-evi"]["findings"] == ["e"]
    assert by["kobo-headroom"]["opportunities"] == ["OPP-1"]
    assert rows.build_expected_threads(kobo, cold, portfolio, None)[-1]["name"] != "kobo-headroom"


def _l3(window: str = "week", n: int = 3, m: int = 2, **over: object) -> dict:
    f = {"rule": "COH-17", "site_code": None, "window": window, "subject": "L3",
         "detail": f"{n} distinct Verified threads in the table, claim {m}", "bodies": ["portfolio.week.p1.json"]}
    f.update(over)
    return f


def test_coh17_allowed_only_for_the_l3_mill_recurrence_shape() -> None:
    # 1. allowed: L3, week, n - m == 1, recurs: carries the reason and the owner
    f = _l3()
    faults, allowed = rows.coh_split([f, _l3("month")], recurs=True)
    assert faults == [] and [a["window"] for a in allowed] == ["week", "month"]
    assert allowed[0] == {**f, "reason": rows.COH17_REASON, "owner": "BL-07"}
    assert "CH6b3-R4" in rows.COH17_REASON
    # each of 2-8 must fail
    assert rows.coh_split([f], recurs=False) == ([f], [])  # 2. recurs False
    s = _l3("S")
    assert rows.coh_split([s], recurs=True) == ([s], [])  # 3. window S
    two = _l3(n=4, m=2)
    assert rows.coh_split([two], recurs=True) == ([two], [])  # 4. n - m == 2
    summary = _l3(subject="summary", detail="a stamped bundle lacks the summary body")
    assert rows.coh_split([summary], recurs=True) == ([summary], [])  # 5. site-less, subject summary
    window = _l3(subject="window", detail="the `/estate/chain` window is not the requested one")
    assert rows.coh_split([window], recurs=True) == ([window], [])  # 6. site-less, subject window
    kobo = _l3(site_code="KOBO-001")
    assert rows.coh_split([kobo], recurs=True) == ([kobo], [])  # 7. a Kobo-Site COH-17 (a V2 row)
    first, second = _l3("month"), _l3("month")  # 8. a second L3 on the same window
    faults, allowed = rows.coh_split([first, second], recurs=True)
    assert len(allowed) == 1 and faults == [second]
    other = {"rule": "COH-2", "site_code": "KOBO-001"}
    assert rows.coh_split([other], recurs=True) == ([other], [])


def _coh2(site: str, subject: str, body: str) -> dict:
    return {"rule": "COH-2", "site_code": site, "subject": subject, "bodies": [body, "portfolio.week.p1.json"]}


def test_coh2_is_allowed_only_for_a_recorded_cold_or_ev_action_from_the_domain_index() -> None:
    ids = rows.recorded_action_ids({"fault_day": {"action": {"id": "A-EV"}}}, {"fixture": {"action": {"id": "A-COLD"}}})
    assert ids == {"A-EV", "A-COLD"}
    cold = _coh2("COLD-LAB-001", "A-COLD", "action_index.COLD-LAB-001.week.p1.json")
    ev = _coh2("EV-LAB-001", "A-EV", "action_index.EV-LAB-001.month.p1.json")
    faults, allowed = rows.coh_split([cold, ev], recurs=False, action_ids=ids)
    assert faults == [] and [a["subject"] for a in allowed] == ["A-COLD", "A-EV"]
    assert all(a["reason"] == rows.COH2_REASON for a in allowed)
    # each must fail: Kobo, an estate-index Action on Cold, an unknown Action id, the wrong Site's index, no ids at all
    kobo = _coh2("KOBO-001", "A-COLD", "action_index.KOBO-001.week.p1.json")  # only the Site test can refuse this
    estate = _coh2("COLD-LAB-001", "A-COLD", "action_index.COLD-LAB-001.week.p1.json")
    estate["bodies"].append("actions.week.p1.json")  # the Action also came from the estate index
    unknown = _coh2("COLD-LAB-001", "A-OTHER", "action_index.COLD-LAB-001.week.p1.json")
    wrong = _coh2("COLD-LAB-001", "A-COLD", "action_index.EV-LAB-001.week.p1.json")
    for bad in (kobo, estate, unknown, wrong):
        assert rows.coh_split([bad], recurs=True, action_ids=ids) == ([bad], [])
    assert rows.coh_split([cold], recurs=False) == ([cold], [])


def test_calendar_asserts_no_data_for_unbuilt_days_and_nothing_for_built_ones() -> None:
    built = {date(2026, 11, 1), date(2026, 11, 3)}
    want = rows.calendar_expectations(date(2026, 11, 1), date(2026, 11, 5), built)
    assert want == {"2026-11-01": None, "2026-11-02": "NO_DATA", "2026-11-03": None, "2026-11-04": "NO_DATA",
                    "2026-11-05": None}


def _page(before="42.0", after="110.0", state="VERIFIED"):
    return {"state": state, "line": "x", "metrics": [{"before": before, "after": after}]}


def test_mill_page_needs_verified_and_exactly_42_to_110() -> None:
    assert rows.mill_page(_page())["after"] == "110.00"
    for bad in (_page(state="INEFFECTIVE"), _page(before="41.9"), _page(after="110.5"), {"state": "VERIFIED"}):
        with pytest.raises(AssertionError):
            rows.mill_page(bad)


def _value_page(**over):
    """A fixture page body as `summary_wire` would serve it at 42.00 -> 110.00 and 0.25 USD (built by the backend)."""
    from assetops_backend.actions.verification_families import mill_value
    from assetops_backend.financials.fuel_cost import PriceSelection

    from decimal import Decimal

    details = {"baseline": {"days": ["d1", "d2", "d3"], "mean_kwh_per_day": "42.00"},
               "later": {"days": ["d5", "d6", "d7"], "mean_kwh_per_day": "110.00"}}
    value = mill_value(details, "VERIFIED", PriceSelection("PRICED", None, "rev-1", Decimal("0.25"), "USD"))
    return {"state": "VERIFIED", "metrics": [{"before": "42.00", "after": "110.00", "days_before": 3,
                                              "days_after": 3}], "value": {**value, **over}}


def test_mill3b_recomputes_the_value_from_the_shown_means_and_the_v1_fixture_price() -> None:
    price = rows.productive_price_v1(Path(__file__).resolve().parents[1] / "conversions"
                                     / "demo-productive-price-publications.json")
    from decimal import Decimal

    assert price == Decimal("0.25")
    got = rows.mill_value_page(_value_page(), price)
    assert got["per_day"] == "17.00" and got["revision_id"] == "rev-1" and got["price"] == "0.25"
    assert got["text"].startswith("About 17.00 USD a day more in estimated sales")
    for bad in (_value_page(per_day="17.01"), _value_page(state="UNPRICED"), _value_page(text="x"),
                _value_page(cost_text="x"), {**_value_page(), "value": None}):
        with pytest.raises(AssertionError):
            rows.mill_value_page(bad, price)
    with pytest.raises(AssertionError):  # a different declared price fails the recomputation
        rows.mill_value_page(_value_page(), Decimal("0.26"))


def _mill5_bodies(mill_text: str | None = None, headline: str = "2 verified results", kobo_actions: int = 1,
                  claim: int = 2, source_class: str | None = "REGISTERED_SIMULATION",
                  ) -> tuple[dict, dict, dict]:
    """The board, week chain and verdict-page bodies. WD-1m-R2: the mill entry carries the suffix of the verdict
    page's `outcome.source_class` (the default is an example class, as on the S+0 Kobo story)."""
    from assetops_backend.chain.vocabulary import provenance_suffix
    from assetops_backend.outcomes.display_code import display_code
    from assetops_backend.site_outcomes.mini import VERIFICATION_TEXT

    trial = VERIFICATION_TEXT["VERIFIED"].format(code=display_code("ACT-000001"), suffix=provenance_suffix(None))
    mill = mill_text or VERIFICATION_TEXT["VERIFIED"].format(code=display_code("ACT-000002"),
                                                             suffix=provenance_suffix(source_class))
    board = {"rows": [{"category": "ASSURE_PERFORMANCE", "headline": headline, "contributors": [
        {"key": "verified_results", "text": trial, "link_ref": {"kind": "ACTION", "id": "a1"}},
        {"key": "verified_results", "text": mill, "link_ref": {"kind": "DOMAIN_VERDICT", "id": "mill"}}]}]}
    chain = {"counts": {"count.verified_results": {"value": claim}},
             "sites": [{"code": "KOBO-001", "threads": {"open": 1, "in_hand": 0, "verified": 1,
                                                        "verified_actions": kobo_actions}},
                       {"code": "COLD-LAB-001", "threads": {"open": 0, "in_hand": 1, "verified": 0,
                                                            "verified_actions": 0}}]}
    page = {"state": "VERIFIED", "outcome": {"outcome": "VERIFIED", "source_class": source_class}}
    return board, chain, page


def _mill5(bodies: tuple[dict, dict, dict], mill_id: str = "mill") -> dict:
    board, chain, page = bodies
    return rows.mill_assure(board, chain, mill_id, "ACT-000002", page)


def test_mill5_reads_the_mill_entry_the_headline_and_the_week_claim() -> None:
    """MB-1-R §2.5 MILL-5 (L0, beside MILL-3b): a pass and one failing body per assertion."""
    got = _mill5(_mill5_bodies())
    assert got["verified_entries"] == 2 and got["week_claim"] == 2
    assert got["mill_text"].endswith(" on example data")
    for bad in (_mill5_bodies(mill_text="ACT-002 not yet verified", headline="1 verified result"),  # wrong text
                _mill5_bodies(headline="3 verified results"),                                     # count != entries
                _mill5_bodies(kobo_actions=0, claim=1),                                           # mill not counted
                _mill5_bodies(claim=3)):                                                          # claim != Σ
        with pytest.raises(AssertionError):
            _mill5(bad)
    with pytest.raises(AssertionError):  # another Action id is not the mill
        _mill5(_mill5_bodies(), "other")


def test_mill5_fails_a_mill_entry_without_its_example_suffix_and_a_kobo_page_without_a_class() -> None:
    """WD-1m-R2: an example-class page whose board entry is plain FAILS; a None class on the S+0 Kobo page FAILS even
    when the board entry is plain too (the write path did not run)."""
    from assetops_backend.outcomes.display_code import display_code
    from assetops_backend.site_outcomes.mini import VERIFICATION_TEXT

    plain = VERIFICATION_TEXT["VERIFIED"].format(code=display_code("ACT-000002"), suffix="")
    with pytest.raises(AssertionError):
        _mill5(_mill5_bodies(mill_text=plain))
    with pytest.raises(AssertionError):
        _mill5(_mill5_bodies(mill_text=plain, source_class=None))


def _pva_cost_check(amount: str = "4.125") -> dict:
    return {"state": "MODELLED_IMPROVEMENT", "currency": "USD",
            "priced_total": {"amount": amount, "currency": "USD", "basis": "TRIAL_HOUR_MODELLED_FUEL",
                             "fuel_change_l": "3.3"}}


def _pva_summary(trial: bool = True, detail: str | None = None, mill_amount: str | None = None) -> dict:
    """The week summary as `portfolio_cards` builds it from a Kobo Assure row's `verified_values` (backend code)."""
    from assetops_backend.chain.vocabulary import estate_income
    from assetops_backend.outcomes.display_code import display_code
    from assetops_backend.site_outcomes.mini import VALUE_LINE_MILL, VALUE_LINE_TRIAL_FUEL
    from assetops_backend.site_outcomes.read import portfolio_cards

    v = _value_page()["value"]
    d = mill_amount or v["per_day"]
    entries = [{"key": "mill", "action_code": "ACT-000002", "basis": v["basis"], "amount": d, "currency": "USD",
                "text": VALUE_LINE_MILL.format(code=display_code("ACT-000002"), d=d, cur="USD")}]
    if trial:
        entries.append({"key": "a1", "action_code": "ACT-001", "basis": "TRIAL_HOUR_MODELLED_FUEL", "amount": "4.12",
                        "currency": "USD", "text": VALUE_LINE_TRIAL_FUEL.format(
                            code=display_code("ACT-001"), l="3.3", amount="4.12", cur="USD")})
    sites = [{"site_code": "KOBO-001", "site_name": "Kobo", "earnings": None, "rows": [
        {"category": "ASSURE_PERFORMANCE", "nodes": {"kpi": None, "earnings": None, "potential": None,
                                                    "verified_values": entries}}]}]
    cards = portfolio_cards(sites, None, estate_income([]), [], None, 0)
    if detail is not None:
        cards["ASSURE_PERFORMANCE"]["detail"] = detail
    return {"sites": sites, "cards": cards}


def test_pva_reads_the_mill_line_the_trial_case_and_no_sum() -> None:
    """PV-1-R §5 PV-A (L0): a pass per trial case and one failing body per assertion."""
    got = rows.pv_values(_pva_summary(), _value_page(), "ACT-000002", "ACT-001", _pva_cost_check())
    assert got["trial_case"] == "credited" and len(got["value_lines"]) == 2 and got["sums_checked"] == 1
    got = rows.pv_values(_pva_summary(trial=False), _value_page(), "ACT-000002", "ACT-001", None)
    assert got["trial_case"] == "not credited" and got["trial_line"] is None
    for summary, cc in ((_pva_summary(mill_amount="17.01"), _pva_cost_check()),    # the mill line != its page
                        (_pva_summary(trial=False), _pva_cost_check()),             # credited, no trial line
                        (_pva_summary(), None),                                     # a trial line, not credited
                        (_pva_summary(detail="21.12 USD"), _pva_cost_check())):     # a card holds the sum
        with pytest.raises(AssertionError):
            rows.pv_values(summary, _value_page(), "ACT-000002", "ACT-001", cc)


def test_pva_zero_addend_is_no_sum_but_a_planted_nonzero_sum_is_still_found() -> None:
    """R3u U1 site 3: an entry amount of 0.00 shows no adding (mill + 0.00 is the mill's own printed amount)."""
    summary = _pva_summary()
    summary["sites"][0]["rows"][0]["nodes"]["verified_values"][1]["amount"] = "0.00"
    got = rows.pv_values(summary, _value_page(), "ACT-000002", "ACT-001", _pva_cost_check())
    assert got["sums_checked"] == 0
    with pytest.raises(AssertionError, match="holds a sum"):
        rows.pv_values(_pva_summary(detail="21.12 USD"), _value_page(), "ACT-000002", "ACT-001", _pva_cost_check())


KW = re.compile(r"\d+–\d+ kW of daytime solar unused")


def _grow(headline="Nothing", potential="No potential found yet", money=None, sales="0 kWh used by Grain mill"):
    return {"headline": headline, "headline_money": money, "potential": potential,
            "contributors": [{"key": "productive_sales", "text": sales}]}


def test_wk2b_restated_passes_and_each_clause_can_fail() -> None:
    assert rows.wk2b(_grow(), KW)["sales"].startswith("0 kWh")
    for bad in (_grow(money={"amount_high": 1}), _grow(headline="5–9 kW of daytime solar unused"),
                _grow(sales="12 kWh used by Grain mill"), _grow(potential="Spare solar 5 kW")):
        with pytest.raises(AssertionError):
            rows.wk2b(bad, KW)


def test_wk2b_with_eligible_days_reads_not_judged_yet_with_no_kw_and_no_money() -> None:
    """D-E5.13 item 4: the study ending S has eligible days (v4), so the potential is the "Not judged yet" sentence."""
    ok = "Not judged yet: 2 of the 5 study days have no reading"
    assert rows.wk2b(_grow(potential={"text": ok}), KW, 3)["potential"] == ok
    one = "Not judged yet: 1 of the 5 study days has no reading"
    assert rows.wk2b({**_grow(potential=None), "nodes": {"potential": {"text": one}}}, KW, 4)["potential"] == one
    for bad in (_grow(), _grow(potential={"text": "Not judged yet: 1 of the 5 study days have no reading"}),
                _grow(potential={"text": ok, "value_line": "12–20 kW over 6 daylight hours"}),
                {**_grow(potential={"text": ok, "money": {"amount_high": 1}})},
                {**_grow(potential="Spare 5 kW"), "nodes": {"potential": {"text": ok}}}):
        with pytest.raises(AssertionError):
            rows.wk2b(bad, KW, 3)
    with pytest.raises(AssertionError):  # 0 eligible days (v3): the sentence is "No potential found yet"
        rows.wk2b(_grow(potential={"text": ok}), KW, 0)


WEEK = [f"2026-11-0{d}" for d in range(2, 9)]  # S = 8 Nov: S-6 .. S


def _calendar(missed, partial):
    """A `days.json` Kobo list: full days carry a complement, story-only days do not, missed days have a `missing`
    entry or none."""
    out = []
    for day in WEEK:
        if day in missed:
            if day == missed[0]:
                out.append({"site": "kobo", "day": day, "kind": "missing", "has_run": False})
            continue
        out.append({"site": "kobo", "day": day, "kind": "trial-before" if day in partial else "steady"})
        if day not in partial:
            out += [{"site": "kobo", "day": day, "kind": k, "complement_of": "steady"} for k in ("night-early", "mill-rest")]
    return out


def _grades(no_data, partial):
    by_day = {d: "NO_DATA" if d in no_data else "PARTIAL" if d in partial else "COMPLETE" for d in WEEK}
    return {m: {"SITE:SITE": dict(by_day)} for m in rows.WEEK_GAP_MEASURES}


def test_week_gap_pattern_passes_on_v4_and_fails_on_client4s_v3_pattern() -> None:
    """D-E5.13 item 3: WK-GAP passes on one missed day (S-4) and one partly checked day (S); it fails on client4's
    real v3 pattern (NO_DATA 4 and 6 Nov, PARTIAL 5, 7 and 8 Nov), whether the calendar or only the grades are v3."""
    v4_missed, v4_partial = ["2026-11-04"], ["2026-11-08"]
    v3_missed, v3_partial = ["2026-11-04", "2026-11-06"], ["2026-11-05", "2026-11-07", "2026-11-08"]
    assert rows.week_day_classes(_calendar(v4_missed, v4_partial), WEEK) == (v4_missed, v4_partial)
    assert rows.week_day_classes(_calendar(v3_missed, v3_partial), WEEK) == (v3_missed, v3_partial)
    got = rows.week_gap_pattern(_grades(v4_missed, v4_partial), WEEK, v4_missed, v4_partial)
    assert got["complete"] == ["2026-11-02", "2026-11-03", "2026-11-05", "2026-11-06", "2026-11-07"]
    assert len(got["measures"]) == 4
    with pytest.raises(AssertionError):  # must-fail: client4's pattern, calendar and grades
        rows.week_gap_pattern(_grades(v3_missed, v3_partial), WEEK, v3_missed, v3_partial)
    with pytest.raises(AssertionError):  # must-fail: a v4 calendar whose snapshots read the v3 pattern
        rows.week_gap_pattern(_grades(v3_missed, v3_partial), WEEK, v4_missed, v4_partial)
    for measure in rows.WEEK_GAP_MEASURES:  # each measure is checked on its own
        bad = _grades(v4_missed, v4_partial)
        bad[measure]["SITE:SITE"]["2026-11-06"] = "PARTIAL"
        with pytest.raises(AssertionError):
            rows.week_gap_pattern(bad, WEEK, v4_missed, v4_partial)
        bad = _grades(v4_missed, v4_partial)
        del bad[measure]
        with pytest.raises(AssertionError):
            rows.week_gap_pattern(bad, WEEK, v4_missed, v4_partial)
    bad = _grades(v4_missed, v4_partial)
    del bad["productive_kwh"]["SITE:SITE"]["2026-11-04"]  # a day with no snapshot row
    with pytest.raises(AssertionError):
        rows.week_gap_pattern(bad, WEEK, v4_missed, v4_partial)


def test_gap_gated_keys_on_the_schema_version() -> None:
    """D-E5.21: gated for schema version >= 4 (dict or bare int); ungated only for an explicit version below 4; fails
    closed (gated) when the schema or version is missing or unreadable."""
    assert rows.gap_gated({"id": "x", "version": 4}) and rows.gap_gated({"version": 5}) and rows.gap_gated(4)
    assert not rows.gap_gated({"id": "x", "version": 3}) and not rows.gap_gated(3)
    for unreadable in ({}, None, {"id": "x"}, {"version": "4"}, {"version": None}, "3", True, []):
        assert rows.gap_gated(unreadable), unreadable


def _wkgap_ctx(version: int, missed, partial):
    import demo_combined_finish as finish
    return finish, finish.Ctx(client=None, work=Path("."), story={"S": "2026-11-08T00:00:00+00:00"},
                              days=_calendar(missed, partial), days_schema={"id": "x", "version": version})


def test_wkgap_row_gates_v4_and_reports_on_client4s_v3(monkeypatch) -> None:
    """D-E5.21: on client4's v3 fixture (2 NO_DATA + 3 PARTIAL) the WK-GAP row returns `gated: false` with the pattern
    it read; on v4 the same data raises. Must-fail: a v4 build with a bad pattern still fails, and without the gate
    (`_wkgap_assert` called directly) the v3 fixture raises."""
    v4_missed, v4_partial = ["2026-11-04"], ["2026-11-08"]
    v3_missed, v3_partial = ["2026-11-04", "2026-11-06"], ["2026-11-05", "2026-11-07", "2026-11-08"]
    finish, v3 = _wkgap_ctx(3, v3_missed, v3_partial)
    grades = _grades(v3_missed, v3_partial)
    monkeypatch.setattr(finish, "_week_grades", lambda ctx, lo, hi: {m: {"SITE:SITE": dict(g["SITE:SITE"])}
                                                                      for m, g in grades.items()})
    got = finish.wkgap(v3)
    assert got["gated"] is False and got["calendar"] == 3
    assert got["missed"] == v3_missed and got["partial"] == v3_partial
    _, v4_bad = _wkgap_ctx(4, v3_missed, v3_partial)  # must-fail: v4 with the v3 pattern
    with pytest.raises(AssertionError):
        finish.wkgap(v4_bad)
    _, v4_grades_bad = _wkgap_ctx(4, v4_missed, v4_partial)  # must-fail: v4 calendar, snapshots read the v3 pattern
    with pytest.raises(AssertionError):
        finish.wkgap(v4_grades_bad)
    with pytest.raises(AssertionError):  # the ungated case raises once the gate is dropped
        finish._wkgap_assert(v3, [f"2026-11-0{d}" for d in range(2, 9)], v3_missed, v3_partial)


MONTH = [(datetime(2026, 11, 8) + timedelta(days=n)).date().isoformat() for n in range(-28, 1)]  # S-28 .. S


def _month(s_offsets_missing, s_offsets_partial, unbuilt=()):
    """A `days.json` Kobo month: `missing` entries, story-only entries, full days (with complements), and unbuilt
    offsets with no entry at all; plus the grades such a build reads (unbuilt days read NO_DATA)."""
    cal, by_day = [], {}
    for n, day in zip(range(-28, 1), MONTH):
        if n in unbuilt:
            by_day[day] = "NO_DATA"
        elif n in s_offsets_missing:
            cal.append({"site": "kobo", "day": day, "kind": "missing", "has_run": False})
            by_day[day] = "NO_DATA"
        elif n in s_offsets_partial:
            cal.append({"site": "kobo", "day": day, "kind": "overuse"})
            by_day[day] = "PARTIAL"
        else:
            cal += [{"site": "kobo", "day": day, "kind": "steady-before"},
                    {"site": "kobo", "day": day, "kind": "night-early", "complement_of": "steady-before"}]
            by_day[day] = "COMPLETE"
    return cal, {m: {"SITE:SITE": dict(by_day)} for m in rows.WEEK_GAP_MEASURES}


V4_MONTH_MISSING, V4_MONTH_PARTIAL = (-10, -4), (-28, -21, -14, -7, 0)


def test_month_gap_clause_passes_on_amended_v4_and_fails_on_the_unbuilt_stretch() -> None:
    """D-E5.19 item 3: the month clause passes when NO_DATA is exactly the `missing` days (S-10, S-4) and PARTIAL
    exactly the story-only days; it fails on the un-amended v4 (S-27..S-22 unbuilt, reading NO_DATA), on v3 (also
    S-4, S-2 unbuilt) and when one measure reads a full day PARTIAL."""
    cal, grades = _month(V4_MONTH_MISSING, V4_MONTH_PARTIAL)
    missed, partial = rows.month_day_classes(cal, MONTH)
    assert missed == ["2026-10-29", "2026-11-04"]
    assert partial == ["2026-10-11", "2026-10-18", "2026-10-25", "2026-11-01", "2026-11-08"]
    got = rows.month_gap_pattern(grades, MONTH, missed, partial)
    assert got["days"] == 29 and len(got["measures"]) == 4
    for unbuilt in ((-27, -26, -25, -24, -23, -22), (-27, -26, -25, -24, -23, -22, -4, -2)):  # un-amended v4; v3
        cal, grades = _month((-10,), V4_MONTH_PARTIAL, unbuilt)
        missed, partial = rows.month_day_classes(cal, MONTH)
        assert missed == ["2026-10-29"]  # an unbuilt day is not a `missing` day
        with pytest.raises(AssertionError):
            rows.month_gap_pattern(grades, MONTH, missed, partial)
    cal, grades = _month(V4_MONTH_MISSING, V4_MONTH_PARTIAL)
    missed, partial = rows.month_day_classes(cal, MONTH)
    for measure in rows.WEEK_GAP_MEASURES:
        bad = copy.deepcopy(grades)
        bad[measure]["SITE:SITE"]["2026-10-15"] = "PARTIAL"
        with pytest.raises(AssertionError):
            rows.month_gap_pattern(bad, MONTH, missed, partial)
    bad = copy.deepcopy(grades)
    del bad["critical_served"]["SITE:SITE"]["2026-10-15"]  # no snapshot on a full day counts as NO_DATA: fails
    with pytest.raises(AssertionError):
        rows.month_gap_pattern(bad, MONTH, missed, partial)
    ok = copy.deepcopy(grades)
    del ok["critical_served"]["SITE:SITE"]["2026-11-04"]  # no snapshot on a `missing` day is no checked reading: passes
    assert rows.month_gap_pattern(ok, MONTH, missed, partial)["measures"]["critical_served|SITE:SITE"][
        "no_snapshot"] == ["2026-11-04"]


def test_site_days_segment_reads_one_site_part() -> None:
    line = ("Kobo mini-grid: 5 of 7 days checked · 1 partly checked · GreenHarvest Cold Room: 3 of 7 days checked "
            "· 1 with too little data, not counted")
    assert rows.site_days_segment(line, "Kobo mini-grid") == "5 of 7 days checked · 1 partly checked"
    assert rows.site_days_segment(line, "GreenHarvest Cold Room") == \
        "3 of 7 days checked · 1 with too little data, not counted"
    assert rows.site_days_segment("Kobo mini-grid: 2 of 7 days checked · 3 partly checked", "Kobo mini-grid") == \
        "2 of 7 days checked · 3 partly checked"
    assert rows.site_days_segment(None, "Kobo mini-grid") is None


def test_wk2c_fails_if_any_kw_or_money_shows() -> None:
    ok = {"text": rows.LIMITED_TEXT}
    assert rows.wk2c(_grow(potential=ok), {"status": "LIMITED", "eligible_days": 5})["status"] == "LIMITED"
    for bad in ({"text": rows.LIMITED_TEXT + " 12–20 kW"}, {**ok, "value_line": "x"}, {**ok, "money": {"a": 1}},
                {"text": rows.LIMITED_TEXT + " about 40 USD"}, {"text": "No potential found yet"}):
        with pytest.raises(AssertionError):
            rows.wk2c(_grow(potential=bad), None)
    with pytest.raises(AssertionError):
        rows.wk2c(_grow(potential=ok), {"status": "SUPPORTED", "eligible_days": 5})


def test_board_faults() -> None:
    ok = {"read_state": "AVAILABLE", "rows": [{"category": "A", "state": "ON_TRACK"}]}
    assert rows.board_faults(ok) == []
    # must-fail: a board whose producer read failed (R8 B1)
    assert rows.board_faults({"read_state": "PARTIAL", "rows": []}) == ["read_state PARTIAL"]
    assert rows.board_faults({"read_state": "PARTIAL", "failed": ["MINI"], "rows": []}) == [
        "read_state PARTIAL (failed: ['MINI'])"]
    assert rows.board_faults({"rows": []}) == ["read_state None"]
    assert rows.board_faults({"read_state": "AVAILABLE", "x": "PRODUCER_NOT_SETTLED", "rows": []}) == [
        "PRODUCER_NOT_SETTLED"]


def test_ev_group_must_not_be_empty_and_unplaced_ids_are_returned() -> None:
    with pytest.raises(AssertionError):
        rows.require_ev_group([{"site_code": "KOBO-001"}])
    rows.require_ev_group([{"site_code": "EV-LAB-001"}])
    unplaced: list = []
    rows.build_expected_threads({"days": [{"findings": ["K1"]}]}, {"days": []}, [], None, unplaced)
    assert unplaced == [{"site_code": "KOBO-001", "finding_id": "k1"}]


def test_calendar_does_not_assert_today() -> None:
    want = rows.calendar_expectations(date(2026, 11, 1), date(2026, 11, 3), {date(2026, 11, 1)})
    assert want == {"2026-11-01": None, "2026-11-02": "NO_DATA", "2026-11-03": None}


def test_ex1_compare_flags_a_changed_assure_line_or_a_new_finding() -> None:
    import demo_combined_ex1 as ex1

    board = {"rows": [{"category": "ASSURE_PERFORMANCE", "headline": "1 verified", "count": 1, "state": "OK",
                       "issues": [{"kind": "FINDING", "text": "t", "ref": {"finding_id": "f1"}}]}]}
    before = ex1.summarise(board, board)
    assert ex1.compare(before, ex1.summarise(board, board))["unchanged"]
    changed = {"rows": [{**board["rows"][0], "headline": "2 verified"}]}
    assert not ex1.compare(before, ex1.summarise(changed, board))["unchanged"]
    extra = {"rows": [{**board["rows"][0], "issues": [*board["rows"][0]["issues"],
                                                       {"kind": "FINDING", "ref": {"finding_id": "f2"}}]}]}
    assert ex1.compare(before, ex1.summarise(board, extra))["diff"]["S+1.new_findings"] == ["f2"]


def test_after_tool_sums_five_minute_kw_per_local_day_and_gates_the_quote() -> None:
    from datetime import datetime, timezone

    import demo_combined_after as after

    t = lambda h, m=0: datetime(2026, 10, 23, h, m, tzinfo=timezone.utc)  # noqa: E731
    rows_ = [("pv", "a", t(8), "12"), ("pv", "a", t(8), "12"), ("pv", "a", t(8, 5), "12"), ("pv", "a", t(8, 10), "x"),
             ("pv", "a", t(22), "12")]  # a duplicate and a non-numeric are skipped; 22:00Z is the next local day
    got = after.kwh_per_local_day(rows_, lambda d, s: (d, s) == ("pv", "a"))
    assert got == {"2026-10-23": 2 * 12 * after.Decimal(5) / 60, "2026-10-24": 12 * after.Decimal(5) / 60}
    assert after.quotable(96.4, 22.4) and after.quotable(96.0, 22.8)
    assert not after.quotable(90.0, 22.4) and not after.quotable(96.4, 30.0)  # must-fail: figures that moved


# ---- DD1b2-R13 B2: the pure asserts of the after tool; each has a case that must fail ------------------------------

def _o12_grow(potential: str = "No potential found yet", solar: str = "Spare solar on 1 of 3 well-observed days") -> dict:
    return {"nodes": {"potential": {"text": potential}}, "contributors": [{"key": "a", "text": "x"},
                                                                           {"key": "b", "text": solar}]}


def test_o12_needs_no_potential_and_a_contributor_with_spare_solar_seen() -> None:
    import demo_combined_after as after

    assert after.o12_grow_nodes(_o12_grow())["potential"] == "No potential found yet"
    for bad in (_o12_grow(potential="96 kW of daytime solar unused"), _o12_grow(solar="Not available yet · spare solar "
                "not checked on the last 5 days"), _o12_grow(solar="Spare solar on 0 of 3 well-observed days")):
        with pytest.raises(AssertionError):
            after.o12_grow_nodes(bad)


def test_o12_s5_reads_not_judged_yet_with_no_kw_and_no_money() -> None:
    import demo_combined_after as after

    ok = "Not judged yet: 4 of the 5 study days have no reading"
    assert after.o12_s5_grow(_o12_grow(potential=ok), "Open")["thread_state_label"] == "Open"
    bad_solar = _o12_grow(potential=ok, solar="Spare solar on 0 of 3 well-observed days")
    money = {**_o12_grow(potential=ok), "nodes": {"potential": {"text": ok, "money": {"amount_high": 1}}}}
    for bad in (_o12_grow(), _o12_grow(potential="Not judged yet: 12 kW spare"), bad_solar, money):
        with pytest.raises(AssertionError):
            after.o12_s5_grow(bad, None)


def test_why_price_line_equals_the_stored_price_and_money_equals_kwh_times_price() -> None:
    import demo_combined_after as after

    p = after.Decimal("0.25")
    line = ["168.3 kWh × 0.25 USD/kWh"]
    assert after.why_price_line(line, {"amount_high": "42.08"}, p, "USD")["state"] == "PRICED"
    assert after.why_price_line(["Nothing has been recorded for this yet"], None, p, "USD")["state"] == "LIMITED"
    for args in ((["168.3 kWh × 0.30 USD/kWh"], None), (line, {"amount_high": "42.00"}),
                 (["Nothing has been recorded for this yet"], {"amount_high": "42.08"})):
        with pytest.raises(AssertionError):
            after.why_price_line(args[0], args[1], p, "USD")


def test_protect_why_must_name_both_cold_threads_and_agreed_actions_must_read_so() -> None:
    import demo_combined_after as after

    nodes = [{"kind": "thread", "ids": ["t1"]}, {"kind": "thread", "ids": ["t2"]}, {"kind": "action", "ids": ["a"]}]
    assert after.protect_names_threads(nodes, "t1", ["t2"])["other_threads"] == {"t2": "named"}
    gap = after.protect_names_threads(nodes[:1] + nodes[2:], "t1", ["t2"])  # t2 missing: recorded, not a failure
    assert gap["other_threads"] == {"t2": "BL-50 known gap: not named"}
    with pytest.raises(AssertionError):
        after.protect_names_threads(nodes[1:], "t1", ["t2"])  # ACT-000002's thread missing: fails
    assert after.action_agreed({"COLD": ["Action agreed", "Open"], "EV": ["Action agreed"]})
    with pytest.raises(AssertionError):
        after.action_agreed({"COLD": ["Open"], "EV": ["Action agreed"]})


def test_fuel_rows_sit_on_story_days_only_and_s14_s7_are_priced_with_quantity_zero() -> None:
    import demo_combined_after as after

    from datetime import datetime, timezone

    def w(day: int):  # a window start whose Site-local (UTC+3) day is 2026-10-<day>
        return datetime(2026, 10, day, 0, 0, tzinfo=timezone.utc)

    kinds = {"2026-10-22": "overuse", "2026-10-29": "overuse", "2026-10-28": "steady"}
    offs = {"2026-10-22": -14, "2026-10-29": -7, "2026-10-28": -8}
    good = [(w(22), "PRICED", 0, 5), (w(29), "PRICED", 0, 7)]
    assert after.fuel_rows_ok(good, kinds, offs)["rows"] == 2
    for bad in ([*good, (w(28), "PRICED", 0, 5)],  # a steady day
                [*good, (w(25), "PRICED", 0, 5)],  # not a story day at all
                [(w(22), "PRICED", 0, 5)],  # no S-7 row
                [(w(22), "PRICED", 0, 0), (w(29), "PRICED", 0, 7)],  # S-14 old priced-at-0 shape
                [(w(22), "PRICED", 0, 5), (w(29), "PRICED", 1, 7)],  # S-7 low not 0
                [(w(22), "UNPRICED", 0, 5), (w(29), "PRICED", 0, 7)]):  # S-14 not PRICED
        with pytest.raises(AssertionError):
            after.fuel_rows_ok(bad, kinds, offs)


def test_action_index_recurrence_and_link_reports() -> None:
    import demo_combined_after as after

    assert after.action_index_ok([{"code": "ACT-000002"}], "ACT-000002", "cold") == 1
    for rows_ in ([], [{"code": "ACT-000009"}]):
        with pytest.raises(AssertionError):
            after.action_index_ok(rows_, "ACT-000002", "cold")
    ev = [("OPEN", "2026-10-17"), ("RECURRED", "2026-10-31")]
    assert after.recurrence_holds(ev, "2026-11-07")
    for bad in ([*ev, ("RECURRED", "2026-11-07")], [*ev, ("WITHDRAWN", "2026-11-07")], ev[:1], [*ev, ("CLOSED", "x")]):
        with pytest.raises(AssertionError):
            after.recurrence_holds(bad, "2026-11-07")
    assert after.known_at_links([{"a": ["/x?known_at=2026-11-05", "/y"]}]) == ["/x?known_at=2026-11-05"]
    assert after.site_links({"h": "/sites/COLD-LAB-001/x", "o": "/sites/KOBO-001"}, ("COLD-LAB-001",)) == [
        "/sites/COLD-LAB-001/x"]


# ---- DD1b2-R10 restated rows -------------------------------------------------------------------------------------

def test_headroom_occurrences_come_from_stored_studies_with_eligible_days() -> None:
    one = [("OPP-1", date(2026, 10, 21), 5)]
    two = [*one, ("OPP-2", date(2026, 11, 4), 1)]
    none = [*two, ("OPP-3", date(2026, 11, 5), 0), ("OPP-4", date(2026, 11, 6), None)]
    assert rows.headroom_opportunities(one) == ["OPP-1"]
    assert rows.headroom_opportunities(two) == ["OPP-1", "OPP-2"]
    assert rows.headroom_opportunities(none) == ["OPP-1", "OPP-2"]  # a study with 0 eligible days is not added
    assert rows.headroom_opportunities([("OPP-3", date(2026, 11, 5), 0)]) == []
    out = rows.build_expected_threads({"days": []}, {"days": []}, [], {"study": {"opportunity_id": "OPP-1"}}, None,
                                      rows.headroom_opportunities(two))
    assert out[-1]["opportunities"] == ["OPP-1", "OPP-2"]
    # no stored list: the pinned study alone, as before
    assert rows.build_expected_threads({"days": []}, {"days": []}, [], {"study": {"opportunity_id": "OPP-1"}}
                                       )[-1]["opportunities"] == ["OPP-1"]


def test_unknown_outcomes_pass_only_as_not_judged() -> None:
    ok = {"CC-1": ("UNKNOWN", "OBJECTIVE_NOT_JUDGED"), "CC-5": ("NO_OBJECTIVE", "NO_OBJECTIVE_DECLARED"),
          "CC-2": ("ON_TRACK", None)}
    assert rows.unknown_only_not_judged(ok) == ["CC-1"]
    for bad in ({"MG-2": ("UNKNOWN", "PRODUCER_NOT_SETTLED")}, {"MG-2": ("UNKNOWN", "OBJECTIVES_NOT_READ")},
                {"MG-2": ("UNKNOWN", None)}, {"CC-5": ("NO_OBJECTIVE", "OBJECTIVES_NOT_READ")}):
        with pytest.raises(AssertionError):
            rows.unknown_only_not_judged(bad)


def test_wk4_has_three_branches_and_each_can_fail() -> None:
    early = "Productive electricity sales: at least 300 kWh · too early to judge (needs 3 checked days)"
    none = "Productive electricity sales: at least 300 kWh sold for productive use a month · " + MG1_NO_DAY
    judged = "Productive electricity sales: 120 kWh so far this month"
    assert rows.wk4("UNKNOWN", early, 1) == "TOO_EARLY"
    assert rows.wk4("UNKNOWN", none, 0) == "NO_FULL_DAY"
    assert rows.wk4("ON_TRACK", judged, 3) == "JUDGED"
    for args in (("ON_TRACK", none, 0), ("UNKNOWN", "no days line", 0), ("UNKNOWN", judged, 3), ("WATCH", early, 1),
                 ("UNKNOWN", none, 2)):
        with pytest.raises(AssertionError):
            rows.wk4(*args)


def _day(start, end, kind="normal"):
    return {"kind": kind, "start": start, "end": end}


def test_index_gaps_are_the_utc_days_no_run_touches() -> None:
    from datetime import datetime, timezone

    days = [_day("2026-10-08T03:00:00Z", "2026-10-08T11:00:00Z"),
            _day("2026-10-25T21:00:00Z", "2026-10-26T03:00:00Z", "night"),  # the night run covers UTC 10-26
            _day("2026-10-27T03:00:00Z", "2026-10-27T11:00:00Z"), _day(None, None, "missing")]
    lo, hi = datetime(2026, 10, 7, tzinfo=timezone.utc), datetime(2026, 10, 28, tzinfo=timezone.utc)
    gaps = rows.expected_index_gaps(days, lo, hi)
    assert "2026-10-26" not in gaps and "2026-10-25" not in gaps  # touched by the night run
    assert "2026-10-07" in gaps and "2026-10-09" in gaps and "2026-10-27" not in gaps and "2026-10-08" not in gaps
    # must-fail: without the night run 10-26 is a gap (and the set differs)
    assert "2026-10-26" in rows.expected_index_gaps([days[0], days[2]], lo, hi)
    assert rows.expected_index_gaps([], lo, hi)[0] == "2026-10-07"


def test_site_day_start_is_the_local_midnight_in_utc() -> None:
    from zoneinfo import ZoneInfo

    got = rows.site_day_start(date(2026, 11, 5), ZoneInfo("Africa/Nairobi"))
    assert got.strftime("%Y-%m-%dT%H:%M:%SZ") == "2026-11-04T21:00:00Z"
    assert got.strftime("%Y-%m-%dT%H:%M:%SZ") != "2026-11-05T00:00:00Z"


def _ev(money, line, headline="estimated charging income"):
    return {"headline": headline, "headline_money": money,
            "contributors": [{"key": "charging_delivered", "text": line}]}


def test_wk1_money_needs_a_counted_day_and_a_counted_day_needs_money() -> None:
    unknown = "Not known yet · 0 of 1 day checked · 1 with too little data, not counted"
    assert rows.wk1(_ev(None, unknown))["known"] is False
    m = {"amount_high": "9.00", "currency": "USD"}
    assert rows.wk1(_ev(m, "12 kWh with a complete meter record"))["known"] is True
    with pytest.raises(AssertionError):
        rows.wk1(_ev(m, unknown))  # money on a day with too little data
    with pytest.raises(AssertionError):
        rows.wk1(_ev(None, "12 kWh with a complete meter record"))
    with pytest.raises(AssertionError):
        rows.wk1({"headline": "x", "headline_money": None, "contributors": []})


def test_potential_is_read_from_the_node_and_both_node_and_chip_are_barred() -> None:
    chip = {"label": "Opportunity", "text": "Productive-use headroom"}
    node = {"text": rows.LIMITED_TEXT, "value": None, "days_line": None}
    g = {**_grow(potential=chip), "nodes": {"potential": node}}
    assert rows.wk2c(g, {"status": "LIMITED", "eligible_days": 5})["status"] == "LIMITED"
    for bad_node, bad_chip in (({**node, "text": rows.LIMITED_TEXT + " 12–20 kW"}, chip), ({**node, "value": "5 kW"}, chip),
                               (node, {**chip, "text": "5 kW spare"}), (node, {**chip, "money": {"a": 1}}),
                               ({"text": "No potential found yet"}, chip)):
        with pytest.raises(AssertionError):
            rows.wk2c({**_grow(potential=bad_chip), "nodes": {"potential": bad_node}}, None)
    b = {**_grow(potential=None), "nodes": {"potential": {"text": "No potential found yet"}}}
    assert rows.wk2b(b, KW)["potential"] == "No potential found yet"
    with pytest.raises(AssertionError):
        rows.wk2b({**b, "nodes": {"potential": {"text": "Spare solar 5 kW"}}}, KW)


# ---- FUEL-1 A3-R §3.9: the idle-fuel finish rows, pass and fail ---------------------------------------------------

def _stored(**over) -> dict:
    """One idle morning's head consequence row as SQL returns it (expected values computed, never typed from a run)."""
    from decimal import Decimal
    from fractions import Fraction

    high = Fraction(11, 10) * Fraction(12000, 3600) * Fraction(33, 10)
    row = {"model_id": "fuel-cost-2", "state": "PRICED", "idle_seconds": 12000,
           "no_load_fuel_rate_l_per_h": Decimal("3.3"), "no_load_fuel_rate_basis": "GENERIC_DEFAULT",
           "sfc_upper_multiplier": Decimal("1.10"), "quantity_high_exact": f"{high.numerator}/{high.denominator}",
           "quantity_high": Decimal(high.numerator) / high.denominator, "amount_low": Decimal(0),
           "amount_high": Decimal(high.numerator) / high.denominator * Decimal("1.25"), "currency": "USD",
           "price_value": Decimal("1.25")}
    return {**row, **over}


def _idle_cost_row(stored: dict) -> dict:
    from assetops_backend.chain.outcomes import _litres
    from assetops_backend.financials.consequence_read import display
    from assetops_backend.site_outcomes.mini import idle_headline

    shown = display({k: stored[k] for k in ("state", "currency", "amount_low", "amount_high")})
    return {"headline": idle_headline({"idle_seconds": stored["idle_seconds"], "rate": "3.3",
                                       "basis": stored["no_load_fuel_rate_basis"],
                                       "litres_high": _litres(stored["quantity_high"])}),
            "headline_money": {"amount_low": shown["amount_low"], "amount_high": shown["amount_high"], "currency": "USD"}}


def test_a3_idle_morning_passes_and_fails() -> None:
    s = _stored()
    got = rows.idle_morning("2026-10-25", s, _idle_cost_row(s))
    assert got["shown_high"] == "15.13" and got["idle_seconds"] == 12000
    for bad in (dict(idle_seconds=11700), dict(model_id="fuel-cost-1"), dict(quantity_high_exact="131/10")):
        with pytest.raises(AssertionError):
            rows.idle_morning("2026-10-25", _stored(**bad), _idle_cost_row(s))
    with pytest.raises(AssertionError):
        rows.idle_morning("2026-10-25", s, {**_idle_cost_row(s), "headline": "possible extra fuel cost on this day"})
    with pytest.raises(AssertionError):
        rows.idle_morning("2026-10-25", s, {**_idle_cost_row(s), "headline_money": {"amount_high": "15.12"}})


def test_a3_never_summed_and_steady_day() -> None:
    assert rows.never_summed(["15.13", "15.13", "15.13"], [{"t": "15.13 USD"}]) == 4
    with pytest.raises(AssertionError):
        rows.never_summed(["15.13", "15.13"], [{"t": ["total 30.26 USD"]}])
    # stored amounts: 15.125 x 2 -> 30.25 / 30.26; x 3 -> 45.38 / 45.39
    stored = ["15.125", "15.125", "15.125"]
    assert rows.never_summed(stored, [{"t": "15.13 USD, 15.12 USD"}]) == 4
    for shown in ("30.25", "30.26", "45.38", "45.39"):
        with pytest.raises(AssertionError):
            rows.never_summed(stored, [{"t": [f"idle fuel total {shown} USD"]}])
    assert rows.steady_day("d", [], {"headline": "possible extra fuel cost on this day"})["stored_rows"] == 0
    with pytest.raises(AssertionError):
        rows.steady_day("d", [{"idle_seconds": 600}], {"headline": "x"})
    with pytest.raises(AssertionError):
        rows.steady_day("d", [], _idle_cost_row(_stored()))


def _trial(**over) -> tuple[dict, dict]:
    pt = {"amount": "4.125", "currency": "USD", "basis": "TRIAL_HOUR_MODELLED_FUEL", "window": ["a", "b"],
          "fuel_change_l": "3.3"}
    result = {"formula": "trial-fuel-comparison/2", "state": "MODELLED_IMPROVEMENT", "priced_total": pt,
              "windows": {"baseline": {"idle_seconds": 3600}, "later": {"idle_seconds": 0}},
              "no_load": {"value_l_per_h": "3.3", "basis": "GENERIC_DEFAULT"},
              "price": {"value": "1.25", "currency": "USD"}, "change_per_demand_kwh": {"nominal": "0.275"}}
    result.update(over)
    cc = {"state": "MODELLED_IMPROVEMENT", "priced_total": result["priced_total"], "price_per_litre": "1.25"}
    return cc, result


def test_a3_trial_cost_passes_and_fails() -> None:
    assert rows.trial_cost(*_trial())["fuel_change_l"] == "3.3"
    for bad in (dict(windows={"baseline": {"idle_seconds": 3300}, "later": {"idle_seconds": 0}}),
                dict(no_load={"value_l_per_h": "3.3", "basis": None}),
                dict(state="MODELLED_NO_IMPROVEMENT")):
        with pytest.raises(AssertionError):
            rows.trial_cost(*_trial(**bad))
    cc, result = _trial()
    with pytest.raises(AssertionError):
        rows.trial_cost(cc, {**result, "priced_total": {**result["priced_total"], "amount": "4.13"}})


def test_a3_optimize_card_and_trial_page() -> None:
    from assetops_backend.chain.vocabulary import FUEL_VALUE_PAGE

    claim = {"key": "money.possible_extra_fuel_cost", "value": {"low": "0.00"}, "text": "0.00 to 15.13 USD"}
    summary = {"sites": [{"site_code": "KOBO-001", "rows": [{"category": "OPTIMIZE_COST", "nodes": {"earnings": claim}}]},
                         {"site_code": "COLD-LAB-001", "rows": []}],
               "cards": {"OPTIMIZE_COST": {"value": {"text": claim["text"]}, "claim": claim}}}
    assert rows.optimize_card(summary)["text"] == claim["text"]
    with pytest.raises(AssertionError):
        rows.optimize_card({**summary, "cards": {"OPTIMIZE_COST": {"value": {"text": "Not known yet"}, "claim": None}}})
    _, result = _trial()
    want = FUEL_VALUE_PAGE.format(l="3.3", amount="4.12 USD", p="1.25", cur="USD", basis="a generic idle fuel rate")
    assert rows.trial_page({"fuel_value": want}, result) == want
    with pytest.raises(AssertionError):
        rows.trial_page({}, result)


def test_r3p_expected_site_codes_read_from_data() -> None:
    """DIESEL-1-R3p CO-6: the core three Sites, plus Kisiwa iff the dataset holds it (a three-Site prepare stays green)."""
    import demo_combined_finish as finish

    assert finish.expected_site_codes(False) == ["COLD-LAB-001", "EV-LAB-001", "KOBO-001"]
    assert finish.expected_site_codes(True) == ["COLD-LAB-001", "EV-LAB-001", "KISIWA-001", "KOBO-001"]


def _r3p_optimize_summary(kisiwa_priced: bool = True, kobo_priced: bool = True) -> dict:
    kobo = {"key": "money.possible_extra_fuel_cost", "value": {"low": "0.00"}, "text": "0.00 to 15.13 USD"}
    kis = {"key": "money.possible_extra_fuel_cost", "value": {"low": "1.10"}, "text": "1.10 to 6.40 USD"}
    row = lambda claim: [{"category": "OPTIMIZE_COST", "nodes": {"earnings": claim}}]  # noqa: E731
    return {"sites": [{"site_code": "KOBO-001", "site_name": "Kobo Mini-grid", "rows": row(kobo) if kobo_priced else []},
                      {"site_code": "COLD-LAB-001", "rows": []},
                      {"site_code": "KISIWA-001", "site_name": "Kisiwa Island Mini-grid",
                       "rows": row(kis) if kisiwa_priced else []}]}


def test_r3p_optimize_card_two_priced_sites_listed_never_summed() -> None:
    """DIESEL-1-R3p CH5D1-O1: Kobo and Kisiwa priced -> "Costs at 2 sites", claim None, each Site's claim on its own."""
    detail = ("Kobo Mini-grid: 0.00 to 15.13 USD possible extra fuel cost · "
              "Kisiwa Island Mini-grid: 1.10 to 6.40 USD possible extra fuel cost")
    summary = {**_r3p_optimize_summary(),
               "cards": {"OPTIMIZE_COST": {"value": {"text": "Costs at 2 sites"}, "claim": None, "detail": detail}}}
    allowed = ("KOBO-001", "KISIWA-001")
    assert rows.optimize_card(summary, allowed=allowed) == {"text": "Costs at 2 sites",
                                                            "priced": ["KOBO-001", "KISIWA-001"]}
    with pytest.raises(AssertionError):  # Kisiwa priced but not allowed
        rows.optimize_card(summary)
    with pytest.raises(AssertionError):  # a summed or reworded detail
        rows.optimize_card({**summary, "cards": {"OPTIMIZE_COST": {**summary["cards"]["OPTIMIZE_COST"],
                                                                   "detail": "1.10 to 21.53 USD"}}}, allowed=allowed)
    with pytest.raises(AssertionError):  # Kobo unpriced
        unpriced = {**_r3p_optimize_summary(kobo_priced=False), "cards": summary["cards"]}
        rows.optimize_card(unpriced, allowed=allowed)
    # One priced Site with Kisiwa allowed keeps the single-Site assertions (three-Site dataset).
    one = _r3p_optimize_summary(kisiwa_priced=False)
    claim = one["sites"][0]["rows"][0]["nodes"]["earnings"]
    one["cards"] = {"OPTIMIZE_COST": {"value": {"text": claim["text"]}, "claim": claim}}
    assert rows.optimize_card(one, allowed=allowed) == {"text": claim["text"]}


def _kis8_summary(line_text: str | None = None, amount_detail: str = "Service disruptions recorded") -> dict:
    from assetops_backend.chain.vocabulary import card_text

    entry = {"key": "f4", "night_date": "2026-10-14", "basis": "UNEXPLAINED_FUEL_AT_DECLARED_PRICE",
             "litres_low": "61.2", "litres_high": "98.4", "amount_low": "76.55", "amount_high": "122.95",
             "currency": "USD", "text": "Unexplained fuel on the night of 14 Oct: about 61.2–98.4 L"}
    site = {"site_code": "KISIWA-001", "site_name": "Kisiwa", "rows": [
        {"category": "PROTECT_ASSET", "nodes": {"unexplained_fuel": [entry]}}]}
    line = card_text("protect.fuel_line", site="Kisiwa", text=line_text or entry["text"])
    card = {"detail": amount_detail, "fuel_lines": [line], "fuel_note": card_text("protect.fuel_separate")}
    return {"sites": [site], "cards": {"PROTECT_ASSET": card}}


def test_kis8_protect_passes_on_the_node_line_and_fails_otherwise() -> None:
    """KIS-8a (DIESEL-1-R3j §9j.12): pass on the night-4 line; fail on a differing line, a missing night or a sum."""
    out = rows.kis8_protect(_kis8_summary(), date(2026, 10, 14))
    assert out["uf1"] == "pass" and out["line"].startswith("Kisiwa · Unexplained fuel on the night of 14 Oct")
    with pytest.raises(AssertionError):
        rows.kis8_protect(_kis8_summary(line_text="something else"), date(2026, 10, 14))
    with pytest.raises(AssertionError):
        rows.kis8_protect(_kis8_summary(), date(2026, 10, 15))
    with pytest.raises(AssertionError):
        rows.kis8_protect(_kis8_summary(amount_detail="199.50 USD in all"), date(2026, 10, 14))  # low + high


# ---- DIESEL-K9: COH-10's Kisiwa fuel thread (DIESEL-1-R3p §9p.7 item 5) ------------------------------------------------

KIS_FID = "1E0D2C3B-0000-4000-8000-00000000F0E1"


def test_kisiwa_fuel_thread_is_added_only_with_kisiwa_json() -> None:
    three = rows.build_expected_threads({"days": []}, {"days": []}, [], None)
    assert rows.build_expected_threads({"days": []}, {"days": []}, [], None, kisiwa=None) == three
    assert not any(t["site_code"] == "KISIWA-001" for t in three)  # a three-Site dataset stays as it was
    four = rows.build_expected_threads({"days": []}, {"days": []}, [], None, kisiwa={"finding": {"id": KIS_FID}})
    assert four == [*three, {"name": "kisiwa-fuel", "site_code": "KISIWA-001", "mechanism": "UNEXPLAINED_FUEL",
                             "findings": [KIS_FID.lower()]}]
    # K7-F's `kisiwa.json` may carry the id on its Action only (the `story_links` rule)
    assert rows.kisiwa_fuel_thread({"action": {"finding_id": KIS_FID}})["findings"] == [KIS_FID.lower()]
    with pytest.raises(AssertionError):
        rows.kisiwa_fuel_thread({"action": {"id": "A"}})


class _Coh10Bundle:
    """The reads `chain_coherence.coh10_thread_identity` makes: one stamped estate window, no board days."""

    def __init__(self, portfolio_rows: list[dict]) -> None:
        self.manifest = {"threads": True}
        self._bodies = {"portfolio.week": {"rows": portfolio_rows}}

    def estate_windows(self) -> list[str]:
        return ["week"]

    def day_windows(self) -> list[str]:
        return []

    def get(self, name: str):
        return self._bodies.get(name)

    def files(self, name: str) -> list[str]:
        return [f"{name}.json"]


def _kis_row(thread: dict | None) -> dict:
    return {"finding_id": KIS_FID, "site_code": "KISIWA-001", "mechanism": "UNEXPLAINED_FUEL", "thread": thread}


def test_coh10_judges_the_kisiwa_fuel_thread() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "checks"))
    import chain_coherence as cc

    threads = [rows.kisiwa_fuel_thread({"finding": {"id": KIS_FID}})]
    ok = _kis_row({"id": "T1", "occurrence_no": 1, "occurrences": 1})
    assert cc.coh10_thread_identity(_Coh10Bundle([ok]), threads) == []
    # fails: the fuel row is on no Portfolio row (K8 not merged, or the Finding dropped out of the estate lists)
    missing = cc.coh10_thread_identity(_Coh10Bundle([]), threads)
    assert [(f["rule"], f["site_code"], f["subject"]) for f in missing] == [("COH-10", "KISIWA-001", "kisiwa-fuel")]
    # fails: the row shows the Finding as occurrence 1 of 2
    split = cc.coh10_thread_identity(_Coh10Bundle([_kis_row({"id": "T1", "occurrence_no": 1, "occurrences": 2})]),
                                     threads)
    assert len(split) == 1 and "expected 1 of 1" in split[0]["detail"], split


def test_kis8_wording_passes_on_clean_bodies_and_fails_otherwise() -> None:
    """KIS-8 wording half (DIESEL-1 H4): clean bodies naming Kisiwa pass; a forbidden word anywhere fails; a read
    that names no Kisiwa body fails (not vacuous)."""
    clean = {"fuel": {"site_code": "KISIWA-001", "rows": [{"text": "Unexplained fuel on the night of 14 Oct"}]},
             "board": {"site_code": "KOBO-001", "rows": []}}
    assert rows.kis8_wording(clean) == {"bodies": 2, "naming_site": 1, "hits": 0}
    for bad in ({"text": "possible theft"}, {"lines": ["Fuel was siphoned"]}, {"Stolen": 1}):
        with pytest.raises(AssertionError):
            rows.kis8_wording({**clean, "other": bad})
    with pytest.raises(AssertionError):
        rows.kis8_wording({"board": {"site_code": "KOBO-001"}})


# ---- DIESEL-K9 (DIESEL-1-R3q §9q.2-§9q.4): KIS-1, KIS-2, KIS-6, KIS-7 L0 bodies ------------------------------------------

def test_kis_rows_are_wired_after_kis8a_in_order() -> None:
    import demo_combined_finish as finish

    ids = [c[0] for c in finish.CHECKS]
    at = ids.index("KIS-8a")
    assert ids[at + 1:at + 5] == ["KIS-1", "KIS-2", "KIS-6", "KIS-7"], ids[at:]
    assert ids.index("KIS-7") < ids.index("KIS-8")  # KIS-8's wording read sees their bodies


def _kis1_inputs():
    """Real revisions: `register_in` on the in-memory Foundation store (confirms `components[].properties[]`)."""
    import copy
    from uuid import UUID

    from foundation_fakes import InMemoryFoundationStore
    import demo_combined_kisiwa as kis
    from test_k1_kisiwa_fixtures import IMPORT_AT, INSTALL_AT

    store = InMemoryFoundationStore()
    reg = kis.register_in(store, IMPORT_AT, INSTALL_AT)
    revs = [{"valid_from": r.valid_from, "superseded_at": r.superseded_at, "content": copy.deepcopy(r.content)}
            for r in store.revisions(UUID(reg["tenant_id"]), UUID(reg["site_id"]))]
    prices = [{"state": "PRICED", "revision_id": "p1", "value": rows.Decimal("1.25"), "currency": "USD"}
              for _ in range(10)]
    return revs, reg, prices


def _set_prop(rev: dict, component: str, key: str, value=None, drop: bool = False) -> None:
    comp = next(c for c in rev["content"]["components"] if c["component_id"] == component)
    if drop:
        comp["properties"] = [p for p in comp["properties"] if p["property_key"] != key]
    else:
        next(p for p in comp["properties"] if p["property_key"] == key)["value"] = value


def test_kis1_foundation_as_known_now_passes_and_each_break_fails() -> None:
    revs, reg, prices = _kis1_inputs()
    got = rows.kis1(revs, reg, prices, 10)
    assert (got["stop_soc_threshold"], got["no_load"], got["sensor_accuracy"], got["price"], got["windows_priced"]) == (
        "90 %", "4.9 L/h GENERIC_DEFAULT", "10 L GENERIC_DEFAULT", "1.25 USD (v1)", 10)
    current = [r for r in revs if r["superseded_at"] is None]
    for name, edit in (
            ("stop 60 in one revision", lambda r: _set_prop(r[0], "generator", "stop-soc-threshold", 60)),
            ("no-load 3.3", lambda r: _set_prop(r[-1], "generator", "generator-no-load-fuel-rate", 3.3)),
            ("missing accuracy basis", lambda r: _set_prop(r[-1], "fuel-tank", "fuel-level-sensor-accuracy-basis",
                                                           drop=True))):
        broken, _, _ = _kis1_inputs()
        edit([r for r in broken if r["superseded_at"] is None])
        with pytest.raises((AssertionError, StopIteration)):
            rows.kis1(broken, reg, prices, 10)
            pytest.fail(name)
    with pytest.raises(AssertionError, match="more than one price revision"):
        rows.kis1(revs, reg, [*prices[:-1], {**prices[-1], "revision_id": "p2"}], 10)
    # L2: a priced subset of the stored nights is not "every night window"; the expected count is the story's
    with pytest.raises(AssertionError, match="not every stored night window was priced"):
        rows.kis1(revs, reg, prices[:3], 10)
    with pytest.raises(AssertionError, match="not every stored night window was priced"):
        rows.kis1(revs, reg, [], 10)
    assert rows.kis1(revs, reg, prices[:3], 3)["windows_priced"] == 3
    # L3: a Site with no current revision is a plain assertion, not "Kisiwa missing"
    superseded = [{**r, "superseded_at": r["valid_from"]} for r in revs]
    with pytest.raises(AssertionError, match="no current Foundation revision") as caught:
        rows.kis1(superseded, reg, prices, 10)
    assert not isinstance(caught.value, rows.KisiwaMissing)
    assert len(current) >= 1


def test_kis_1_reads_the_night_count_from_kisiwa_json() -> None:
    import inspect

    import demo_combined_finish as finish

    src = inspect.getsource(finish.kis_1)
    assert "kisiwa.json" in src and '["runs"]' in src and "nights" in src and "10" not in re.sub(r"R3q|9q\.\d", "", src)


def _kis2_body(**over):
    from fractions import Fraction

    from assetops_backend.financials import fuel_cost, fuel_cost_v2

    intervals = [{"mean_kw": "10", "duration_seconds": 1200, "sfc_l_per_kwh": "0.25"},   # 10 kW x 1/3 h x 0.25
                 {"mean_kw": "0", "duration_seconds": 300, "sfc_l_per_kwh": "0.3"}]     # idle 300 s x 4.9 L/h
    exact = Fraction(str(fuel_cost_v2.MULTIPLIER)) * (Fraction(5, 6) + Fraction(300, 3600) * Fraction("4.9"))
    head = {"id": "c1", "finding_id": "f1", "finding_revision_id": "r1", "state": "PRICED", "model_id": "fuel-cost-2",
            "idle_seconds": 300, "no_load_fuel_rate_l_per_h": "4.9", "no_load_fuel_rate_basis": "GENERIC_DEFAULT",
            "sfc_upper_multiplier": str(fuel_cost_v2.MULTIPLIER),
            "quantity_high_exact": f"{exact.numerator}/{exact.denominator}",
            "quantity_high": fuel_cost.to_decimal_ceiling(exact)}
    head.update(over)
    return {"f1": head}, {"c1": intervals}, [{"finding_id": "f1", "revision_id": "r1", "lifecycle": "SUPPORTED"}]


def test_kis2_is_fuel_cost_2_over_the_stored_intervals_exactly() -> None:
    from decimal import ROUND_HALF_UP, localcontext
    from fractions import Fraction

    from assetops_backend.financials import fuel_cost

    heads, ivs, latest = _kis2_body()
    got = rows.kis2(heads, ivs, latest)
    assert got["findings"] == 1 and got["per_finding"][0]["idle_seconds"] == 300
    exact = Fraction(heads["f1"]["quantity_high_exact"])
    with localcontext() as ctx:
        ctx.prec, ctx.rounding = fuel_cost.QUANTITY_DIGITS, ROUND_HALF_UP
        half_up = rows.Decimal(exact.numerator) / rows.Decimal(exact.denominator)
    assert half_up != fuel_cost.to_decimal_ceiling(exact)  # the fixture distinguishes the two roundings
    for name, (h, i, l) in {
            "x1.00 multiplier": _kis2_body(sfc_upper_multiplier="1.00"),
            "dropped idle interval": (heads, {"c1": ivs["c1"][:1]}, latest),
            "half-up quantity_high": _kis2_body(quantity_high=half_up),
            "fuel-cost-1": _kis2_body(model_id="fuel-cost-1"),
            "UNPRICED": _kis2_body(state="UNPRICED"),
            "not SUPPORTED": (heads, ivs, [{**latest[0], "lifecycle": "CANDIDATE"}]),
            "head cites an older revision (L1)": _kis2_body(finding_revision_id="r0"),
            "idle seconds": _kis2_body(idle_seconds=0)}.items():
        with pytest.raises(AssertionError):
            rows.kis2(h, i, l)
            pytest.fail(name)
    with pytest.raises(AssertionError, match="no Kisiwa dispatch Finding"):
        rows.kis2({}, {}, [])


FOUR = ["COLD-LAB-001", "EV-LAB-001", "KISIWA-001", "KOBO-001"]


def _kis6(verdict: str = "VERIFIED", verified: int = 1, board_protect: str = "NEEDS_ATTENTION",
          objectives=FOUR, card_value: int = 2, value_lines=("Kobo mini-grid: 42.00 USD",)):
    from zoneinfo import ZoneInfo

    s_day = date(2026, 11, 7)
    start = rows.site_day_start(s_day, ZoneInfo("Africa/Dar_es_Salaam")).strftime("%Y-%m-%dT%H:%M:%SZ")
    kis_rows = [{"category": "PROTECT_ASSET", "state": "NEEDS_ATTENTION"},
                {"category": "ASSURE_PERFORMANCE", "state": "ON_TRACK", "nodes": {"verified_values": []}}]
    summary = {"sites": [{"site_code": c} for c in FOUR if c != "KISIWA-001"] + [
        {"site_code": "KISIWA-001", "site_name": "Kisiwa island mini-grid", "rows": kis_rows, "window_basis": "DAY",
         "window": {"from": start, "to": "x"}}],
        "cards": {"ASSURE_PERFORMANCE": {"claim": {"value": card_value}, "value_lines": list(value_lines)}}}
    chain = {"sites": [{"code": c, "threads": {"verified": verified if c == "KISIWA-001" else 0}} for c in FOUR],
             "counts": {"count.verified_results": {"value": 2}}}
    portfolio = {"objectives": [{"site_code": c} for c in objectives]}
    board = {"rows": [{"category": "PROTECT_ASSET", "state": board_protect},
                      {"category": "ASSURE_PERFORMANCE", "state": "ON_TRACK"}]}
    return summary, chain, portfolio, board, {"verdict": {"state": verdict, "stored": True}}, s_day


def test_kis6_counts_cells_and_assure_pass_and_each_item_fails() -> None:
    got = rows.kis6(*_kis6())
    # R3u U5: a dict verdict VERIFIED passes and reaches the Assure card claim and the H2 asserts (the return)
    assert got["want_verified"] == 1 and got["assure_card"] == 2 and got["sites"]["objectives"] == FOUR
    assert got["verdict"] == "VERIFIED" and got["chain_verified_results"] == 2
    s, ch, po, bo, doc, day = _kis6()
    with pytest.raises(AssertionError, match="Kisiwa verified threads"):  # no verdict at all: want 0, chain says 1
        rows.kis6(s, ch, po, bo, {"verdict": None}, day)
    assert rows.kis6(*_kis6(verdict="INEFFECTIVE", verified=0))["want_verified"] == 0  # read from data, never forced
    for name, body in {"1: three objective Sites": _kis6(objectives=FOUR[:2] + FOUR[3:]),
                       "2: a cell differs from the S board": _kis6(board_protect="ON_TRACK"),
                       "3: verified against the verdict": _kis6(verdict="INEFFECTIVE", verified=1),
                       "3: card against the chain count": _kis6(card_value=1),
                       "3: a Kisiwa value line (H2)": _kis6(value_lines=("Kisiwa island mini-grid: 3.00 USD",))}.items():
        with pytest.raises(AssertionError):
            rows.kis6(*body)
            pytest.fail(name)
    summary, *rest = _kis6()
    with pytest.raises(rows.KisiwaMissing):
        rows.kis6({**summary, "sites": summary["sites"][:3]}, *rest)


def _cost(high):
    return None if high is None else {"key": "money.possible_extra_fuel_cost", "text": f"{high} USD",
                                      "value": {"low": high, "high": high, "currency": "USD"}}


def _site7(code, high):
    return {"site_code": code, "site_name": code.title(),
            "rows": [{"category": "OPTIMIZE_COST", "nodes": {"earnings": _cost(high)}}]}


def _kis7(kisiwa_high: str | None = None, extra: str = "", kobo_high: str = "15.125"):
    """An S summary as the server lists it (cold, kisiwa, kobo); the Optimize card follows the priced Sites."""
    from assetops_backend.chain.vocabulary import COST_SMALL, card_text, sites_text

    sites = [_site7("COLD-LAB-001", None), _site7("KISIWA-001", kisiwa_high), _site7("KOBO-001", kobo_high)]
    priced = [(s, s["rows"][0]["nodes"]["earnings"]) for s in sites if s["rows"][0]["nodes"]["earnings"]]
    if len(priced) == 1:
        card = {"claim": priced[0][1], "value": {"text": priced[0][1]["text"]}, "detail": extra}
    else:
        detail = " · ".join(card_text("cost.site", site=s["site_name"], text=c["text"],
                                      small=COST_SMALL[c["key"].removeprefix("money.")]) for s, c in priced)
        card = {"claim": None, "value": {"text": card_text("cost.sites", sites=sites_text(len(priced)))},
                "detail": detail + extra}
    return {"sites": sites, "cards": {"OPTIMIZE_COST": card}}


def _utc(m, d, h, mi):
    from datetime import datetime, timezone
    return datetime(2026, m, d, h, mi, tzinfo=timezone.utc)


# the two PRICED night-1 heads of the real story (Kisiwa is UTC+3): 20:40-22:05 on 28 Oct and 01:55-03:15 on 29 Oct
_HEADS7 = [{"finding_id": "f1", "episode_start": _utc(10, 28, 17, 40), "episode_end": _utc(10, 28, 19, 5),
            "state": "PRICED", "amount_high": "7.5", "currency": "USD"},
           {"finding_id": "f2", "episode_start": _utc(10, 28, 22, 55), "episode_end": _utc(10, 29, 0, 15),
            "state": "PRICED", "amount_high": "3.0", "currency": "USD"}]
_S7 = date(2026, 11, 3)


def _board7(high="7.5", asked=None):
    def board_at(day):
        if asked is not None:
            asked.append(day)
        return {"rows": [{"category": "OPTIMIZE_COST", "nodes": {"earnings": _cost(high)}}]}
    return board_at


def test_kis7_expectations_from_data_pass_and_each_break_fails() -> None:
    asked: list[str] = []
    got = rows.kis7(_kis7(), [_kis7()], _HEADS7, _S7, _board7(asked=asked))
    # no Kisiwa head overlaps S (3 Nov): Kisiwa unpriced on S, Kobo alone priced; d1 is the Kisiwa local date of the
    # earliest priced head's start (28 Oct 20:40), whose lead head is f1
    assert got["priced_on_s"] == ["KOBO-001"] and got["kisiwa_priced_on_s"] is False
    assert got["d1"] == "2026-10-28" and asked == ["2026-10-28"] and got["d1_amount_high"] == "7.5"
    assert got["sums_checked"] == 0 and "not reached" in got["multi_site_bodies"]
    assert got["d1_priced"] == "priced and equal"
    # R3u U8: item 3 (d1 priced) asserts again: an unpriced d1 or a differing d1 amount fails
    for board in (_board7(None), _board7("7.6")):
        with pytest.raises(AssertionError, match="KIS-7 item 3"):
            rows.kis7(_kis7(), [_kis7()], _HEADS7, _S7, board)
    # a lead head that is not PRICED fails too (d1 lead is f1)
    with pytest.raises(AssertionError, match="KIS-7 item 3"):
        rows.kis7(_kis7(), [_kis7()], [{**_HEADS7[0], "state": "UNPRICED"}, _HEADS7[1]], _S7, _board7())
    # the R3s2 report-only form stays reachable (K10 held)
    unpriced = rows.kis7(_kis7(), [_kis7()], _HEADS7, _S7, _board7(None), item3_report_only=True)
    assert unpriced["d1_amount_high"] is None
    assert "REPORT-ONLY (R3s2)" in unpriced["d1_priced"]
    assert "d1 is unsettled: no `productive_kwh` subject (R3s2)" in unpriced["d1_priced"]
    assert "differs" in rows.kis7(_kis7(), [_kis7()], _HEADS7, _S7, _board7("7.6"),
                                  item3_report_only=True)["d1_priced"]
    for name, args in {
            "Kisiwa priced on S while expected unpriced": (_kis7("7.5"), [_kis7()], _HEADS7, _S7, _board7()),
            "item 1: card differs from the priced Sites": ({**_kis7(), "cards": {"OPTIMIZE_COST": {
                "claim": None, "value": {"text": "x"}, "detail": ""}}}, [_kis7()], _HEADS7, _S7, _board7()),
            "two priced Sites summed (item 4)": (_kis7("7.5", extra=" Total 22.63 USD"),
                                                  [_kis7("7.5", extra=" Total 22.63 USD")], _HEADS7,
                                                  date(2026, 10, 28), _board7()),
            "no priced head at all": (_kis7(), [_kis7()], [{**h, "state": "NOT_PRICED"} for h in _HEADS7], _S7,
                                      _board7())}.items():
        with pytest.raises(AssertionError):
            rows.kis7(*args)
            pytest.fail(name)
    with pytest.raises(rows.KisiwaMissing):
        rows.kis7({"sites": [{"site_code": "KOBO-001"}]}, [], _HEADS7, _S7, _board7())


def test_kis7_item3_compares_through_money2_r3t4() -> None:
    """R3t4 §9t4: an unrounded stored amount equals the two-place board amount; a one-cent difference fails;
    a different currency fails."""
    heads = [{**_HEADS7[0], "amount_high": "26.27739583"}, _HEADS7[1]]
    got = rows.kis7(_kis7(), [_kis7()], heads, _S7, _board7("26.28"))
    assert got["d1_priced"] == "priced and equal"
    with pytest.raises(AssertionError, match="KIS-7 item 3"):
        rows.kis7(_kis7(), [_kis7()], heads, _S7, _board7("26.29"))
    with pytest.raises(AssertionError, match="KIS-7 item 3"):
        rows.kis7(_kis7(), [_kis7()], [{**heads[0], "currency": "EUR"}, heads[1]], _S7, _board7("26.28"))


def test_kis7_priced_on_s_when_a_head_overlaps_and_two_priced_sites_are_never_summed() -> None:
    s_day = date(2026, 10, 28)  # S local day [27 Oct 21:00Z, 28 Oct 21:00Z) holds f1
    two = _kis7("7.5")
    got = rows.kis7(two, [two], _HEADS7, s_day, _board7())
    assert got["priced_on_s"] == ["KISIWA-001", "KOBO-001"] and got["sums_checked"] >= 1  # server Site order
    with pytest.raises(AssertionError):  # expected priced on S, but the S summary shows Kisiwa unpriced
        rows.kis7(_kis7(), [_kis7()], _HEADS7, s_day, _board7())
    with pytest.raises(AssertionError):  # a summed string
        rows.kis7(two, [two, _kis7("7.5", extra=" Total 22.63 USD")], _HEADS7, s_day, _board7())


# ---- DIESEL-K9 R3r (DIESEL-1-R3r §9r.2): KIS-OV and the register call ----------------------------------------------------

def _ov_reads(status: int = 200, code=None):
    return [{"label": label, "status": status, "code": code, "body": {"window": label} if status == 200 else {}}
            for label in ("S-5d", "S")]


_OV_BASIS = [{"basis": "NO_LEGACY_EVIDENCE", "same_import": True, "same_sha": True}]


def test_kis_ov_is_wired_after_kis7() -> None:
    import demo_combined_finish as finish

    ids = [c[0] for c in finish.CHECKS]
    assert ids.index("KIS-OV") == ids.index("KIS-7") + 1


# ---- DATA-1 (D-E5.30): KISIWA-COHORT --------------------------------------------------------------------------------

def _cohort_windows(*statuses: tuple[str, bool]) -> list[dict]:
    return [{"window_start": datetime(2026, 11, d, 21, 0), "window_end": datetime(2026, 11, d + 1, 21, 0),
             "cohort_status": s, "has_readings": h} for d, (s, h) in enumerate(statuses, start=1)]


def test_kisiwa_cohort_is_wired_and_passes_when_every_read_day_is_selected_unique() -> None:
    import demo_combined_finish as finish

    assert "KISIWA-COHORT" in [c[0] for c in finish.CHECKS]
    got = rows.kisiwa_cohort(_cohort_windows(("SELECTED_UNIQUE", True), ("SELECTED_UNIQUE", True), ("EMPTY", False)))
    assert got == {"windows": 3, "with_readings": 2, "selected_unique": 2}


def test_kisiwa_cohort_fails_on_an_ambiguous_day_and_on_an_empty_read() -> None:
    with pytest.raises(AssertionError, match="not SELECTED_UNIQUE"):
        rows.kisiwa_cohort(_cohort_windows(("SELECTED_UNIQUE", True), ("AMBIGUOUS", True)))
    with pytest.raises(AssertionError, match="not SELECTED_UNIQUE"):
        rows.kisiwa_cohort(_cohort_windows(("EMPTY", True)))  # a day with readings but no cohort chosen
    with pytest.raises(AssertionError, match="no Kisiwa dispatch window"):
        rows.kisiwa_cohort(_cohort_windows(("EMPTY", False)))
    with pytest.raises(AssertionError, match="no Kisiwa dispatch window"):
        rows.kisiwa_cohort([])


def _stored_cohort(times: list[datetime]) -> dict:
    """A real `select_cohort` over battery-soc readings on one epoch at `times` (a repeated time is a night boundary
    published by both nights), as the selected run stores it (`payload()` through JSON, the `analytic_run.cohort`
    column the row reads)."""
    import json
    from uuid import UUID, uuid4

    from assetops_backend.analytics.assessment_inputs import AcceptedReading, Window
    from assetops_backend.analytics.cohort import select_cohort

    from datetime import timezone

    utc = [t.replace(tzinfo=timezone.utc) for t in times]
    readings = tuple(AcceptedReading(
        evidence_id=uuid4(), envelope_sha256=f"sha-{n}", batch_id=UUID(int=9), gateway_id=UUID(int=1),
        source_id=UUID(int=2), sequence_epoch="kisiwa-gw-1", sequence=n, role="battery-soc", asset_id=UUID(int=3),
        source_time=t, interval_start=None, interval_end=None, published_at=t, received_at=t, accepted_at=t,
        quality="GOOD", value="90", unit="%", foundation_revision_id=UUID(int=4), binding_set_revision_id=UUID(int=5),
        binding_revision_id=UUID(int=6), source_mode="SIMULATED") for n, t in enumerate(utc, start=1))
    lo = utc[0].replace(hour=0, minute=0)
    got = select_cohort(readings, Window(lo, lo + timedelta(days=1)))
    return json.loads(json.dumps(got.payload()))


def test_kisiwa_cohort_fails_on_a_boundary_instant_published_by_two_nights() -> None:
    """DATA-1 fix H1: two readings of one channel at the nights' shared boundary on the one session give a cohort
    that is SELECTED_UNIQUE yet holds a REPORTS_OVERLAP limit (dispatch answers it AMBIGUOUS_SERIES); the row fails
    on it, and passes on the same day with the boundary sent once."""
    boundary = datetime(2026, 10, 31, 12, 0)
    once = _stored_cohort([boundary - timedelta(minutes=5), boundary, boundary + timedelta(minutes=5)])
    twice = _stored_cohort([boundary - timedelta(minutes=5), boundary, boundary, boundary + timedelta(minutes=5)])
    assert once["status"] == twice["status"] == "SELECTED_UNIQUE", (once["status"], twice["status"])

    def window(cohort: dict) -> dict:
        return {"window_start": datetime(2026, 10, 31), "window_end": datetime(2026, 11, 1),
                "cohort_status": cohort["status"], "has_readings": True, "limits": cohort["limits"]}

    assert rows.kisiwa_cohort([window(once)]) == {"windows": 1, "with_readings": 1, "selected_unique": 1}
    with pytest.raises(AssertionError, match="REPORTS_OVERLAP") as caught:
        rows.kisiwa_cohort([window(once), window(twice)])
    assert "2026-10-31T12:00:00" in str(caught.value), caught.value


def test_kisiwa_cohort_reads_the_latest_dispatch_selection_per_window() -> None:
    """The row's read: the latest selection per window, its run's status and stored cohort limits, and whether the
    window has readings (validated against a built database's Kisiwa windows during the DATA-1 fix, read-only)."""
    import demo_combined_finish as finish

    sql = finish.KISIWA_COHORT_SQL
    assert "DISTINCT ON (s.window_start, s.window_end)" in sql and "s.seq DESC" in sql
    assert "s.analytic_id = 'dispatch'" in sql and "accepted_evidence" in sql
    assert "r.cohort -> 'limits' AS limits" in sql


_OV_REPORT = {"outcome": "PASSED", "empty_set": True}
_OV_BOARDS = {"S-5d": "AVAILABLE", "S": "AVAILABLE"}


def test_kis_ov_pass_and_each_break_fails() -> None:
    got = rows.kis_ov(_ov_reads(), _OV_BASIS, _OV_BOARDS, _OV_REPORT)
    assert got == {"overview_status": {"S-5d": 200, "S": 200}, "basis": "NO_LEGACY_EVIDENCE",
                   "performance_report": {"outcome": "PASSED", "empty_set": True}, "board_read_state": _OV_BOARDS,
                   "s5d_protect": None}
    for name, (reads, basis, boards, report) in {
            "409 awaiting evidence migration": (_ov_reads(409, "AWAITING_EVIDENCE_MIGRATION"), _OV_BASIS, _OV_BOARDS,
                                                _OV_REPORT),
            "no basis row": (_ov_reads(), [], _OV_BOARDS, _OV_REPORT),
            "two basis rows": (_ov_reads(), _OV_BASIS * 2, _OV_BOARDS, _OV_REPORT),
            "another basis": (_ov_reads(), [{**_OV_BASIS[0], "basis": "COMPARED"}], _OV_BOARDS, _OV_REPORT),
            "another import": (_ov_reads(), [{**_OV_BASIS[0], "same_import": False}], _OV_BOARDS, _OV_REPORT),
            "another digest": (_ov_reads(), [{**_OV_BASIS[0], "same_sha": False}], _OV_BOARDS, _OV_REPORT),
            "no report": (_ov_reads(), _OV_BASIS, _OV_BOARDS, None),
            "a FAILED report": (_ov_reads(), _OV_BASIS, _OV_BOARDS, {**_OV_REPORT, "outcome": "FAILED"}),
            "a PASSED report that is not empty-set": (_ov_reads(), _OV_BASIS, _OV_BOARDS,
                                                      {**_OV_REPORT, "empty_set": False}),
            "a PARTIAL S board": (_ov_reads(), _OV_BASIS, {**_OV_BOARDS, "S": "PARTIAL"}, _OV_REPORT),
            "a PARTIAL S-5d board": (_ov_reads(), _OV_BASIS, {**_OV_BOARDS, "S-5d": "PARTIAL"}, _OV_REPORT),
            "a board not read": (_ov_reads(), _OV_BASIS, {"S": "AVAILABLE"}, _OV_REPORT)}.items():
        with pytest.raises(AssertionError):
            rows.kis_ov(reads, basis, boards, report)
            pytest.fail(name)


def _s5d_board(protect="NEEDS_ATTENTION", mg8=("NEEDS_ATTENTION", "PRIMARY_FINDING_OPEN"), read_state="AVAILABLE"):
    outcomes = [{"key": "MG-5", "state": "UNKNOWN", "reason": "PRODUCER_NOT_SETTLED"}]
    if mg8 is not None:
        outcomes.append({"key": "MG-8", "state": mg8[0], "reason": mg8[1]})
    return {"read_state": read_state, "warnings": [], "rows": [
        {"category": "PROTECT_ASSET", "state": protect, "outcomes": outcomes}]}


def test_kis_ov_pins_the_s5d_protect_row_and_mg8_entry_r3u() -> None:
    """R3u U7: Protect NEEDS_ATTENTION and MG-8 {NEEDS_ATTENTION, PRIMARY_FINDING_OPEN}; the lead is not asserted."""
    got = rows.kis_ov(_ov_reads(), _OV_BASIS, _OV_BOARDS, _OV_REPORT, _s5d_board())
    assert got["s5d_protect"] == "NEEDS_ATTENTION"
    for name, board in {"the packet's UNKNOWN / PRODUCER_NOT_SETTLED shape": _s5d_board("UNKNOWN", ("UNKNOWN", "PRODUCER_NOT_SETTLED")),
                        "Protect UNKNOWN": _s5d_board(protect="UNKNOWN"),
                        "MG-8 another reason": _s5d_board(mg8=("NEEDS_ATTENTION", "OTHER")),
                        "MG-8 absent": _s5d_board(mg8=None)}.items():
        with pytest.raises(AssertionError, match="R3u-s1"):
            rows.kis_ov(_ov_reads(), _OV_BASIS, _OV_BOARDS, _OV_REPORT, board)
            pytest.fail(name)
    # the failure records the board's read_state and warnings and the second read by the local from/to pair
    with pytest.raises(AssertionError) as err:
        rows.kis_ov(_ov_reads(), _OV_BASIS, _OV_BOARDS, _OV_REPORT, _s5d_board("UNKNOWN", ("UNKNOWN", "PRODUCER_NOT_SETTLED"),
                    read_state="PARTIAL"), lambda: {"read_state": "AVAILABLE", "protect_state": "UNKNOWN"})
    text = str(err.value)
    assert "PARTIAL" in text and "second_read" in text and "'protect_state': 'UNKNOWN'" in text


def test_kis_ov_second_read_error_never_replaces_the_r3u_s1_message() -> None:
    """review-K9-r3u L2: a failing second read is recorded inside the R3u-s1 assertion, not raised in its place."""
    def boom() -> dict:
        raise RuntimeError("second read exploded")

    with pytest.raises(AssertionError, match="R3u-s1") as err:
        rows.kis_ov(_ov_reads(), _OV_BASIS, _OV_BOARDS, _OV_REPORT,
                    _s5d_board("UNKNOWN", ("UNKNOWN", "PRODUCER_NOT_SETTLED")), boom)
    assert "second_read_error" in str(err.value) and "second read exploded" in str(err.value)


_FRESH_PATH_SCRIPT = r"""
import importlib.util, sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

test_file, tools = sys.argv[1], Path(sys.argv[2])
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != (tools / "checks").resolve()]
sys.path.insert(0, str(tools))
spec = importlib.util.spec_from_file_location("finish_rows_under_test", test_file)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != (tools / "checks").resolve()]
sys.modules.pop("chain_coherence", None)
assert not any(Path(p or ".").resolve() == (tools / "checks").resolve() for p in sys.path)

import demo_combined_rows as rows
from assetops_backend.actions.verification_rules import fmt

got = rows.pv_values(mod._pva_summary(), mod._value_page(), "ACT-000002", "ACT-001", mod._pva_cost_check())
assert got["sums_checked"] == 1, got
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != (tools / "checks").resolve()]
sys.modules.pop("chain_coherence", None)

low, high = Fraction(1), Fraction(2)
windows = {"w": {"residual_low": fmt(low), "residual_high": fmt(high)}}
findings = [{"finding_id": "f", "revision_id": "r", "lifecycle": "SUPPORTED", "window_id": "w"}]
cons = {"finding_id": "f", "finding_revision_id": "r", "fuel_balance_window_id": "w", "state": "PRICED",
        "litres_low": fmt(low), "litres_high": fmt(high), "price_value": Decimal("1.25"), "price_revision_id": "p",
        "amount_low": fmt(low * Fraction(5, 4)), "amount_high": fmt(high * Fraction(5, 4)), "currency": "USD"}
prices = {"w": {"state": "PRICED", "revision_id": "p", "value": Decimal("1.25")}}
dispatch = [{"finding_id": "other", "amount_low": "0", "amount_high": "4.12"}]
out = rows.kis4(windows, findings, [cons], prices, dispatch, [])
assert out["supported"] == 1, out
print("FRESH_PATH_OK")
"""


def test_pv_values_and_kis4_import_chain_coherence_without_tools_checks_on_the_path() -> None:
    """review-K9-r3u H1 (L0): both functions add tools/checks themselves, in a fresh interpreter without it."""
    import subprocess

    tools = Path(__file__).resolve().parents[2] / "tools"
    done = subprocess.run([sys.executable, "-c", _FRESH_PATH_SCRIPT, str(Path(__file__).resolve()), str(tools)],
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0 and "FRESH_PATH_OK" in done.stdout, (done.stdout[-800:], done.stderr[-1500:])


def test_performance_loop_runs_kisiwa_only_when_it_is_in_the_story(tmp_path) -> None:
    import types

    import demo_combined as dc

    def run(sites):
        seen: list[str] = []

        def py(*args, **kw):
            seen.append(args[args.index("--site") + 1] if "--site" in args else args[-1])
            return types.SimpleNamespace(stdout="ok")
        dc.Demo.performance_and_prebuild(types.SimpleNamespace(
            story=lambda: {"sites": sites}, py=py, write_prebuilt_routes=lambda: None,  # E4-C2
            work=tmp_path, tree=tmp_path, read_site_mark=lambda site: None))  # E4-C4: no mark, so every run is due
        return seen[:-1]  # the last call is the pre-build

    assert run(["kobo", "kisiwa"]) == ["KOBO-001", "KISIWA-001"]
    assert run(["kobo"]) == ["KOBO-001"]


def test_register_records_the_no_legacy_basis_after_register_in(monkeypatch, tmp_path) -> None:
    import sqlalchemy

    import demo_combined_kisiwa as kis
    import pg_harness
    from assetops_backend.sites.adapters import postgres_foundation_store as pfs
    from datetime import datetime, timezone
    from uuid import UUID

    calls: list = []
    tenant, site = "00000000-0000-0000-0000-0000000000a1", "00000000-0000-0000-0000-0000000000b2"

    class Store:
        def __init__(self, url):
            pass

        def record_no_legacy_evidence_basis(self, t, s, *, now):
            calls.append(("basis", t, s, now))

    class Conn:
        def execute(self, *a, **k):
            calls.append(("sql",))

    class Engine:
        def begin(self):
            import contextlib
            return contextlib.nullcontext(Conn())

        def dispose(self):
            pass

    import_at = datetime(2026, 10, 1, tzinfo=timezone.utc)
    install_at = datetime(2026, 10, 2, tzinfo=timezone.utc)
    monkeypatch.setattr(pfs, "PostgresFoundationStore", Store)
    monkeypatch.setattr(sqlalchemy, "create_engine", lambda url: Engine())
    monkeypatch.setattr(pg_harness, "dispose", lambda store: None)
    monkeypatch.setattr(kis, "register_in", lambda store, i, n: calls.append(("register_in",)) or
                        {"tenant_id": tenant, "site_id": site})
    monkeypatch.setattr(kis, "publish_price", lambda *a, **k: None)
    kis.register("postgresql://x", tmp_path, import_at, install_at)
    assert calls[0] == ("register_in",)
    assert calls[1] == ("basis", UUID(tenant), UUID(site), import_at)


# ---- OWN-G2 (build sheet OWN-GAPS §2.5, R2-G2 Q9): KIS-11, last-tick.json, the closing-tick retry --------------------

def _tick_report(fuel: dict | None = None, site: str = "KISIWA-001") -> dict:
    stages = {"mini": {"code": "OK"}}
    if fuel is not None:
        stages["fuel_night"] = fuel
    return {"outcome": "COMPLETED", "sites": [{"site_code": "KOBO-001", "stages": {"fuel_night": {"code": "OK"}}},
                                              {"site_code": site, "stages": stages}]}


_FUEL_OK = {"code": "OK", "eligible": True, "processed": 0, "deferred": 0}


def test_kis11_passes_on_a_visited_ok_eligible_tick_and_story_revision_one() -> None:
    out = rows.kis11(_tick_report(_FUEL_OK), {1: 1, 2: 1, 4: 1}, 1, 0)
    assert out["fuel_night"]["code"] == "OK" and out["story_nights"] == 3


def test_kis11_fails_when_kisiwa_was_not_visited_and_on_each_break() -> None:
    for report in (None, _tick_report(None), _tick_report(_FUEL_OK, site="OTHER-001")):
        with pytest.raises(AssertionError, match="KISIWA-001 was not visited by the last tick"):
            rows.kis11(report, {1: 1}, 1, 0)
    breaks = [((_tick_report({**_FUEL_OK, "code": "FAILED"}), {1: 1}, 1, 0), "not OK and eligible"),
              ((_tick_report({**_FUEL_OK, "eligible": False}), {1: 1}, 1, 0), "not OK and eligible"),
              ((_tick_report(_FUEL_OK), {1: 1, 4: 2}, 1, 0), "not revision 1"),
              ((_tick_report(_FUEL_OK), {}, 1, 0), "no Kisiwa story night"),
              ((_tick_report(_FUEL_OK), {1: 1}, 2, 0), "exactly one Kisiwa fuel Finding"),
              ((_tick_report(_FUEL_OK), {1: 1}, 1, 3), "KOBO-001 has fuel_balance_window rows")]
    for args, message in breaks:
        with pytest.raises(AssertionError, match=message):
            rows.kis11(*args)


def test_kis11_is_wired_right_after_kis9() -> None:
    import demo_combined_finish as finish

    ids = [c[0] for c in finish.CHECKS]
    assert ids.index("KIS-11") == ids.index("KIS-9") + 1


def test_last_json_object_takes_the_last_parsable_object_line() -> None:
    assert rows.last_json_object('{"a": 1}\nnoise\n{"b": 2}\n{broken\n[1]\n') == {"b": 2}
    assert rows.last_json_object("no json here\n[1, 2]\n") is None
    assert rows.last_json_object("") is None


def test_demo_tick_writes_last_tick_json_and_removes_a_stale_one(tmp_path) -> None:
    import types

    import demo_combined as dc

    outs = iter(['log\n{"outcome": "COMPLETED", "sites": []}\n', "no report\n"])
    demo = types.SimpleNamespace(work=tmp_path, performance_and_prebuild=lambda: None,
                                 py=lambda *a, **k: types.SimpleNamespace(stdout=next(outs)))
    assert dc.Demo.tick(demo) == {"outcome": "COMPLETED", "sites": []}
    assert (tmp_path / "last-tick.json").exists()
    assert dc.Demo.tick(demo) is None
    assert not (tmp_path / "last-tick.json").exists()


def test_closing_tick_retries_at_most_two_more_ticks_30_s_apart() -> None:
    import demo_combined as dc

    def run(reports):
        it, sleeps = iter(reports), []
        report, extra = dc.retry_until_visited(_tick_report(None), lambda: next(it), sleep=sleeps.append)
        return report, extra, sleeps

    assert run([_tick_report(None), _tick_report(None), _tick_report(_FUEL_OK)])[1:] == (2, [30.0, 30.0])
    report, extra, sleeps = run([_tick_report(_FUEL_OK)])
    assert extra == 1 and sleeps == [30.0] and rows.fuel_night_entry(report) == _FUEL_OK
    assert dc.retry_until_visited(_tick_report(_FUEL_OK), lambda: 1 / 0) == (_tick_report(_FUEL_OK), 0)


# ---- D-E5.40: the CO-6 / WK-GAP known-defect marker (DATA-12 removes it) -------------------------------------------

def _kd_ctx(monkeypatch, coverage_kobo, *, week_gaps=None):
    """A client6-shaped fake: Kobo missed 2026-11-04 (the v4 calendar), Portfolio coverage as given."""
    import demo_combined_finish as finish
    cal, grades = _month((-4,), (-28, -21, -14, -7, 0))
    S = datetime(2026, 11, 8)
    ctx = finish.Ctx(client=None, work=Path("."), story={"S": "2026-11-08T00:00:00+00:00"}, days=cal,
                     days_schema={"id": "x", "version": 4})
    ctx.docs = {"kobo": {"finding": "f1"}}
    by_code = {finish.KOBO: {"site_name": "Kobo mini-grid", "window_basis": "DAY", "rows": [
        {"category": "GROW_REVENUE", "state": "NO_DATA"}], "window": {"from": finish.iso(S.replace(tzinfo=finish.timezone.utc))}},
        finish.COLD: {"window_basis": "PERIOD"}, finish.EV: {"window_basis": "PERIOD"}}
    body = {"objectives": [{"site_code": c} for c in (finish.KOBO, finish.COLD, finish.EV)], "status": "CURRENT",
            "rows": [], "coverage": {"state": "CURRENT"}}
    line = "Kobo mini-grid: 5 of 7 days checked · 1 partly checked"
    summary = {"objective_site_count": 3, "cards": {c: {"days_line": line} for c in ("PROTECT_ASSET", "ASSURE_PERFORMANCE")}}
    monkeypatch.setattr(finish, "_estate", lambda c, lo, hi: (body, summary, {finish.KOBO: coverage_kobo}, by_code))
    monkeypatch.setattr(finish, "_kisiwa_present", lambda c: False)
    monkeypatch.setattr(finish, "_kobo_zone", lambda c: finish.timezone.utc)
    monkeypatch.setattr(finish, "_kobo_board_s", lambda c: {"rows": [{"category": "GROW_REVENUE", "state": "NO_DATA"}]})
    monkeypatch.setattr(finish, "_week_grades", lambda c, lo, hi: grades)
    return finish, ctx


_UTC_DEFECT = {"state": "CURRENT", "days": {"gaps": []}}
_PARTIAL_OK = {"state": "PARTIAL", "days": {"gaps": [{"day": "2026-11-04"}], "requested": 7, "checked": 6,
                                            "text": None}}


def test_co6_and_wkgap_report_the_known_coverage_defect_and_other_failures_still_fail(monkeypatch) -> None:
    finish, ctx = _kd_ctx(monkeypatch, _UTC_DEFECT)
    with pytest.raises(finish.KnownDefect) as co6:  # the exact coverage signature: reported, not an AssertionError
        finish.co6(ctx)
    assert "gaps []" in str(co6.value) and co6.value.read["kobo_days"] == {"gaps": []}
    with pytest.raises(finish.KnownDefect) as wk:
        finish.wkgap(ctx)
    assert "CO-6 coverage gaps []" in str(wk.value) and wk.value.read["kobo_days_line"].startswith("5 of 7")
    assert finish.KNOWN_DEFECTS == {"CO-6": "D-E5.38", "WK-GAP": "D-E5.38"}
    # must-fail: a different assertion in CO-6 / WK-GAP (not the coverage signature) still fails
    with pytest.raises(AssertionError):  # a wrong gap day is not the signature
        _, c2 = _kd_ctx(monkeypatch, {"state": "PARTIAL", "days": {"gaps": [{"day": "2026-11-05"}]}})
        finish.wkgap(c2)
    finish, c3 = _kd_ctx(monkeypatch, _UTC_DEFECT)
    monkeypatch.setattr(finish, "_kobo_board_s", lambda c: {"rows": [{"category": "GROW_REVENUE", "state": "COMPLETE"}]})
    with pytest.raises(AssertionError):  # the defect is present AND the board cells disagree: still fails
        finish.co6(c3)
    finish, c4 = _kd_ctx(monkeypatch, {"state": "PARTIAL", "days": {"gaps": [{"day": "2026-11-05"}]}})
    with pytest.raises(AssertionError):  # PARTIAL with the wrong gaps is not the signature
        finish.co6(c4)


def test_run_keeps_a_known_defect_out_of_failed_and_the_exit_code(monkeypatch, tmp_path, capsys) -> None:
    import json
    import demo_combined_finish as finish

    def known(ctx):
        raise finish.KnownDefect("Kobo coverage state CURRENT with gaps []", {"x": 1})

    def bad(ctx):
        raise AssertionError("other")

    monkeypatch.setattr(finish, "load", lambda work, client: type("C", (), {})())
    monkeypatch.setattr(finish, "app_client", lambda url, work: None)
    monkeypatch.setattr(finish, "idx_present", lambda: True)
    monkeypatch.setattr(finish, "CHECKS", [("CO-6", True, False, known), ("WK-GAP", True, False, known),
                                           ("CO-1", False, False, lambda c: {})])
    assert finish.run("u", tmp_path) == 0
    out = capsys.readouterr().out
    assert "KNOWN DEFECT D-E5.38" in out and "2 known defect" in out
    saved = json.loads((tmp_path / "check.json").read_text(encoding="utf-8"))["rows"]
    assert saved["CO-6"]["status"] == "known_defect" and saved["CO-6"]["known_defect"] == "D-E5.38"
    import demo_combined as dc
    assert dc.failed_rows(tmp_path / "check.json") == []  # add-dates reads no failed row
    monkeypatch.setattr(finish, "CHECKS", [("CO-6", True, False, known), ("CO-6b", True, False, bad)])
    assert finish.run("u", tmp_path) == 1  # any other failing row still fails
    monkeypatch.setattr(finish, "CHECKS", [("CO-6", True, False, lambda c: {})])
    assert finish.run("u", tmp_path) == 0
    assert "no longer reproduces; remove the marker" in capsys.readouterr().out
    monkeypatch.setattr(finish, "CHECKS", [("CO-1", False, False, known)])
    assert finish.run("u", tmp_path) == 1  # an unlisted row cannot use the marker
