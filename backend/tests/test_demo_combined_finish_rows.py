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


def test_coh17_is_allowed_only_on_kobo_and_only_when_the_mill_thread_recurs() -> None:
    f17 = {"rule": "COH-17", "site_code": "KOBO-001"}
    other = {"rule": "COH-2", "site_code": "KOBO-001"}
    faults, allowed = rows.coh_split([f17, other], recurs=True)
    assert faults == [other] and allowed == [f17]
    assert rows.coh_split([f17], recurs=False) == ([f17], [])
    assert rows.coh_split([{"rule": "COH-17", "site_code": "COLD-LAB-001"}], recurs=True)[1] == []


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
