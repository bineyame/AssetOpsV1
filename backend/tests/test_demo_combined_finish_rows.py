"""DD-1b2b O4-O6 L0: the pure parts of the new finish rows (`tools/demo_combined_rows.py`). No database. Each guard has
a case that must fail, so none is vacuous."""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import demo_combined_rows as rows  # noqa: E402

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
    good = [(w(22), "PRICED", 0, 0), (w(29), "PRICED", 0, 0)]
    assert after.fuel_rows_ok(good, kinds, offs)["rows"] == 2
    for bad in ([*good, (w(28), "PRICED", 0, 0)],  # a steady day
                [*good, (w(25), "PRICED", 0, 0)],  # not a story day at all
                [(w(22), "PRICED", 0, 0)],  # no S-7 row
                [(w(22), "PRICED", 0, 0), (w(29), "PRICED", 1, 1)],  # S-7 quantity not 0
                [(w(22), "UNPRICED", 0, 0), (w(29), "PRICED", 0, 0)]):  # S-14 not PRICED
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
    none = "Productive electricity sales: at least 300 kWh sold for productive use a month · sales not recorded"
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
