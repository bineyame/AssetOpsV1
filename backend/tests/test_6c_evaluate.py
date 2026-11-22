"""6c (`specs/6c-option-evaluator/spec.md` §5, §6 tests 2, 3, 4, 8 and 9): the study reader, the lever models, the
admission measures and the evaluator. Every expected figure is a hand-computed literal of §5."""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from assetops_backend.decisions.evaluate import OptionInput, evaluate_options
from assetops_backend.decisions.models import (SETTING_GRID_CHANGES, check_grid_changes, full_months, match_cases,
                                               months_averaged, setting_changes)
from assetops_backend.decisions.run import option_inputs, recompute_admission
from assetops_backend.decisions.adapters.study_file import read_study_bytes
from assetops_backend.decisions.study_input import StudyRefused
from assetops_backend.decisions.study_input import read_study as _read_study
from assetops_backend.runs.admission import AdmissionMeasures, admit, judge
from assetops_backend.structure.registry import REGISTRIES
from option_fixtures import (C1_CHANGES, CC, E1_CHANGES, EV, F1G_LEVER, FIXTURES, MG, REAL_LEVER, TEST_GRID,
                             TEST_LEVER, c1_base, case_doc, decision_of, e1_base, f1_base, one_off_of, study_doc,
                             write_study)

D = Decimal


def read_study(path):
    """The study file through the product's adapter (the only file read, D-P6.22's guard home)."""
    return _read_study(path, read_study_bytes)


PKG = Path(__file__).resolve().parents[1] / "assetops_backend"
USD = "USD"
DIESEL = ("diesel_price",)
F1_KEYS = ["no-action", "stop-90-reserve-25", "stop-80-reserve-30", "stop-80-reserve-25", "stop-70-reserve-30",
           "stop-70-reserve-25", "stop-60-reserve-30", "stop-60-reserve-25"]
F1_DAWN = {"worst_soc_pct": "69/2", "margin_points": "-1/2", "days_below": 4, "new_days_below": [], "days": 31}
WEAR_MISSING = ("battery_wear_rate_assumption", "DECLARED", "wear_rate")
SITE_MONTH = [("SITE_MONTH_SIMULATION", "SIMULATION", "candidate_l"),
              ("SITE_MONTH_SIMULATION", "SIMULATION", "battery_throughput_kwh")]
MG_EFFECTS = ["candidate_l", "battery_throughput_kwh", "diesel_l", "fuel_cost", "battery_wear", "cost_to_serve",
              "contribution"]
MG_UNITS = ["L", "KWH", "L", "MONEY", "MONEY", "MONEY", "MONEY"]
MG_CURRENCY = [None, None, None, USD, USD, USD, USD]


def run_f1(study=None, *, base=None, lever=TEST_LEVER, amounts=None, name="study-f1.json"):
    """F1's decision valued through `option_inputs` (the study path, §3.5) and `evaluate_options`."""
    study = read_study(FIXTURES / name) if study is None else study
    decision, options = decision_of(lever)
    by_key, _ = match_cases(decision, options, study)
    amounts = {} if amounts is None else amounts
    one_offs = {o.id: one_off_of(o, amounts.get(o.option_key, "90.00")) for o in options
                if o.generator == "SETTING_GRID" and amounts.get(o.option_key, "90.00") is not None}
    inputs = option_inputs(options, lever, study, by_key, recompute_admission(study), one_offs, grid_changes=TEST_GRID)
    outcome, rows = evaluate_options(MG, f1_base() if base is None else base, decision, lever, inputs)
    keys = [o.option_key for o in options]
    assert [r.option_id for r in rows] == [o.id for o in options]
    return outcome, dict(zip(keys, rows)), {o.option_key: o for o in options}, one_offs


def _missing(row):
    return [(m.record_kind, m.source_family, m.factor_id) for m in row.missing]


def _effects(row):
    return [(e.factor_id, e.position, e.change_per_month, e.unit, e.currency,
             [(m.record_kind, m.source_family, m.factor_id) for m in e.missing]) for e in row.effects]


def _mg_rows(*changes, wear_currency=USD):
    """The seven MINI_GRID effect rows of F1: their changes are the literals each test writes down."""
    units = ["L", "KWH", "L", "MONEY", "MONEY", "MONEY", "MONEY"]
    names = ["candidate_l", "battery_throughput_kwh", "diesel_l", "fuel_cost", "battery_wear", "cost_to_serve",
             "contribution"]
    currencies = [None, None, None, USD, wear_currency, USD, USD]
    return [(n, i, D(c), u, cur, []) for i, (n, c, u, cur) in enumerate(zip(names, changes, units, currencies))]


#: F1b's effect rows, one literal list per option: avoided L, added kWh, fuel cost at 1.25, wear at 0.05, cost to
#: serve, contribution (each worked on the page of the spec)
F1B_EFFECTS = {
    "stop-90-reserve-25": _mg_rows("-5", "0", "-5", "-6.25", "0", "-6.25", "6.25"),
    "stop-80-reserve-30": _mg_rows("-180", "10", "-180", "-225.00", "0.50", "-224.50", "224.50"),
    "stop-80-reserve-25": _mg_rows("-190", "20", "-190", "-237.50", "1.00", "-236.50", "236.50"),
    "stop-70-reserve-30": _mg_rows("-200", "50", "-200", "-250.00", "2.50", "-247.50", "247.50"),
    "stop-70-reserve-25": _mg_rows("-210", "80", "-210", "-262.50", "4.00", "-258.50", "258.50"),
    "stop-60-reserve-30": _mg_rows("-150", "100", "-150", "-187.50", "5.00", "-182.50", "182.50"),
    "stop-60-reserve-25": _mg_rows("-250", "150", "-250", "-312.50", "7.50", "-305.00", "305.00"),
}


#: F1b: (avoided L, added kWh, monthly, 12 months, value, disposition, rank, reason, admitted, first failing)
F1B = {
    "stop-90-reserve-25": (5, 0, "6.25", "75.00", "-15.00", "DEFERRED", None, "NOT_WORTH_MORE_THAN_NO_ACTION", True, None),
    "stop-80-reserve-30": (180, 10, "224.50", "2694.00", "2604.00", "ACCEPTABLE", 3, None, True, None),
    "stop-80-reserve-25": (190, 20, "236.50", "2838.00", "2748.00", "REJECTED", None, "NOT_ADMITTED_STARTS", False,
                           "starts"),
    "stop-70-reserve-30": (200, 50, "247.50", "2970.00", "2880.00", "RECOMMENDED", 1, None, True, None),
    "stop-70-reserve-25": (210, 80, "258.50", "3102.00", "3012.00", "ACCEPTABLE", 2, None, True, None),
    "stop-60-reserve-30": (150, 100, "182.50", "2190.00", "2100.00", "ACCEPTABLE", 4, None, True, None),
    "stop-60-reserve-25": (250, 150, "305.00", "3660.00", "3570.00", "REJECTED", None, "NOT_ADMITTED_FULL_CHARGE", False,
                           "full_charge"),
}


def _assert_no_action(row, source="SIMULATED"):
    assert (row.disposition, row.reason_code, row.rank, row.monthly_change, row.horizon_change, row.value,
            row.currency, row.source_class, row.evidence_class, row.missing, row.assumed, row.admission, row.dawn,
            row.effects, row.one_off_id) == ("COMPARISON", None, None, 0, 0, 0, None, source, "DERIVED", (), (), None,
                                             None, (), None)


def _assert_f1b_row(key, row, one_offs, options):
    avoided, added, monthly, horizon, value, disp, rank, reason, admitted, first = F1B[key]
    assert (row.disposition, row.reason_code, row.rank) == (disp, reason, rank), key
    assert (row.monthly_change, row.horizon_change, row.value) == (D(monthly), D(horizon), D(value)), key
    assert (row.currency, row.source_class, row.evidence_class, row.assumed, _missing(row)) \
        == (USD, "SIMULATED", "MODELLED", DIESEL, []), key
    assert row.one_off_id == one_offs[options[key].id].id
    assert (row.admission["admitted"], row.admission["first_failing_part"]) == (admitted, first)
    assert row.dawn == F1_DAWN
    assert _effects(row) == F1B_EFFECTS[key], key


# --- test 2: read_study and models --------------------------------------------------------------------------------

def test_2_f1_frame_and_identity() -> None:
    study = read_study(FIXTURES / "study-f1.json")
    assert (study.frame, study.frame_tenant, study.frame_site_code) == ("SITE_RECORD", "lakeside-power", "KOBO-001")
    assert study.sha256 == "5aa40e709c759e8e860d346efb2b747aaed46964d3a0725affd8734e42912153"
    assert study.identity["frame"] == {"kind": "SITE_RECORD", "tenant": "lakeside-power", "site_code": "KOBO-001"}
    assert list(study.cases) == F1_KEYS[1:] and study.days == 31 and study.input_class == "SIMULATED"
    assert study.baseline.measures == AdmissionMeasures(Fraction(0), 0, 2, 4)


def test_2_k1_identity_is_a_declared_season() -> None:
    study = read_study(FIXTURES / "kobo-61d-study.json")
    assert study.sha256 == "d2c5291028c2adb57c9ac1393e616db7e8a51599f1ae6440b114ae51593814e3"
    assert study.frame == "DECLARED_SEASON" and study.frame_tenant is None and study.frame_site_code is None
    assert list(study.identity) == ["input_class", "evidence_class", "commit", "model", "season",
                                    "season_inputs_digest", "trajectory_digests", "assumptions", "admission_rule",
                                    "status", "window_start", "days", "frame"]
    assert study.identity["frame"] == {"kind": "DECLARED_SEASON", "tenant": None, "site_code": None}
    assert (study.identity["commit"], study.identity["model"], study.identity["days"]) \
        == ("6fd0d6bb6b17b851a0e27d3098a592a656f56fc1", "mini-grid/8", 61)
    assert len(study.cases) == 14 and months_averaged(REAL_LEVER, study) == ()


@pytest.mark.parametrize("plant,code", [
    (lambda d: d.pop("season"), "STUDY_UNREADABLE"),
    (lambda d: d.update(days="31"), "STUDY_UNREADABLE"),
    (lambda d: d.update(days=True), "STUDY_UNREADABLE"),
    (lambda d: d["cases"][0].update(stop_soc_pct=90), "STUDY_UNREADABLE"),
    (lambda d: d["cases"][0]["avoided_l_by_month"][0].update(days="31"), "STUDY_UNREADABLE"),
    (lambda d: d["cases"][0]["admission"]["parts"][0].update(passed="yes"), "STUDY_UNREADABLE"),
    (lambda d: d["cases"][0].pop("admission"), "STUDY_UNREADABLE"),
    (lambda d: d["frame"].pop("tenant"), "STUDY_UNREADABLE"),
    (lambda d: d.update(frame="SITE_RECORD"), "STUDY_UNREADABLE"),
    (lambda d: d["cases"].append(dict(d["cases"][0])), "STUDY_UNREADABLE"),
    (lambda d: d.update(status="NOT_CALIBRATED"), "STUDY_NOT_CALIBRATED"),
    (lambda d: d.update(input_class="OBSERVED"), "STUDY_LABELS_INVALID"),
    (lambda d: d.update(evidence_class="MEASURED"), "STUDY_LABELS_INVALID"),
])
def test_2_read_study_refusals(tmp_path, plant, code) -> None:
    doc = study_doc()
    plant(doc)
    with pytest.raises(StudyRefused) as got:
        read_study(write_study(tmp_path, doc))
    assert got.value.code == code


def test_2_unreadable_bytes_and_missing_file(tmp_path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    for path in (bad, tmp_path / "absent.json"):
        with pytest.raises(StudyRefused) as got:
            read_study(path)
        assert got.value.code == "STUDY_UNREADABLE"


def test_2_another_frame_kind_is_a_declared_season(tmp_path) -> None:
    doc = study_doc()
    doc["frame"]["kind"] = "SEASON"
    assert read_study(write_study(tmp_path, doc)).frame == "DECLARED_SEASON"


def test_2_f1i_mean_of_full_months_without_scaling(tmp_path) -> None:
    doc = study_doc()
    case = case_doc(doc, "stop-70-reserve-30")
    case["avoided_l_by_month"] = [{"month": "2026-08", "days": 12, "value": {"exact": "999/1"}},
                                  {"month": "2026-09", "days": 30, "value": {"exact": "100/1"}},
                                  {"month": "2026-10", "days": 31, "value": {"exact": "200/1"}}]
    case["added_throughput_kwh_by_month"] = [{"month": m, "days": n, "value": {"exact": "0/1"}}
                                             for m, n in (("2026-08", 12), ("2026-09", 30), ("2026-10", 31))]
    study = read_study(write_study(tmp_path, doc))
    got = setting_changes(TEST_LEVER, study.cases["stop-70-reserve-30"], study, grid_changes=TEST_GRID)
    assert got["candidate_l"].delta == D(-150) and got["battery_throughput_kwh"].delta == 0
    assert full_months(study.cases["stop-70-reserve-30"], ("avoided_l_by_month", "added_throughput_kwh_by_month")) \
        == ("2026-09", "2026-10")
    assert (got["candidate_l"].evidence, got["candidate_l"].sources, got["candidate_l"].origins,
            got["candidate_l"].missing) == ("MODELLED", ("replay-study",), ("demo-simulated",), None)
    with pytest.raises(StudyRefused) as refused:  # the baseline's months differ from this case's
        months_averaged(TEST_LEVER, study, grid_changes=TEST_GRID)
    assert refused.value.code == "STUDY_UNREADABLE"


def test_2_a_declared_season_reads_no_amount() -> None:
    study = read_study(FIXTURES / "study-f1h.json")
    got = setting_changes(TEST_LEVER, study.cases["stop-70-reserve-30"], study, grid_changes=TEST_GRID)
    for leaf in ("candidate_l", "battery_throughput_kwh"):
        assert got[leaf].delta is None and got[leaf].missing == ("SITE_MONTH_SIMULATION", "SIMULATION")
    assert months_averaged(TEST_LEVER, study, grid_changes=TEST_GRID) == ()


def test_2_matching_baseline_grid_and_ignored(tmp_path) -> None:
    decision, options = decision_of(TEST_LEVER)
    doc = study_doc()
    extra = dict(case_doc(doc, "stop-90-reserve-25"), case_id="stop-90-reserve-30",
                 reserve_soc_pct={"exact": "30/1"})
    doc["cases"].append(extra)
    by_key, ignored = match_cases(decision, options, read_study(write_study(tmp_path, doc)))
    assert list(by_key) == F1_KEYS[1:] and ignored == ("stop-90-reserve-30",)
    plants = {
        "STUDY_BASELINE_MISMATCH": lambda d: d["baseline"].update(stop_soc_pct={"exact": "85/1"}),
        "STUDY_GRID_MISMATCH": lambda d: d["cases"].remove(case_doc(d, "stop-70-reserve-30")),
    }
    for code, plant in plants.items():
        doc = study_doc()
        plant(doc)
        with pytest.raises(StudyRefused) as got:
            match_cases(decision, options, read_study(write_study(tmp_path, doc)))
        assert got.value.code == code
    doc = study_doc()
    doc["cases"].append(dict(case_doc(doc, "stop-70-reserve-30"), case_id="stop-75-reserve-30",
                             stop_soc_pct={"exact": "75/1"}))
    with pytest.raises(StudyRefused, match="stop-75-reserve-30"):
        match_cases(decision, options, read_study(write_study(tmp_path, doc)))


def test_2_the_grid_model_must_match_the_lever() -> None:
    check_grid_changes({"generator_stop_reserve": REAL_LEVER}, SETTING_GRID_CHANGES)
    check_grid_changes({"test_stop_reserve": TEST_LEVER}, TEST_GRID)
    with pytest.raises(ValueError):
        check_grid_changes({"test_stop_reserve": TEST_LEVER},
                           {"test_stop_reserve": SETTING_GRID_CHANGES["generator_stop_reserve"][::-1]})
    with pytest.raises(ValueError):
        check_grid_changes({}, TEST_GRID)


# --- test 3: judge --------------------------------------------------------------------------------------------------

def test_3_judge_equals_admits_parts_on_0k4d_cases() -> None:
    from test_0k4d_admission import outcome
    cases = [outcome(), outcome(unserved=Fraction(1)), outcome(breaches=3), outcome(max_starts=7),
             outcome(longest=7), outcome(max_starts=9, longest=9)]
    bases = [outcome("baseline"), outcome("baseline", max_starts=8), outcome("baseline", longest=8)]
    for base in bases:
        for case in cases:
            assert judge(AdmissionMeasures.of(base), AdmissionMeasures.of(case)) == admit(base, case).parts


def test_3_recomputed_admission_must_agree_with_the_file(tmp_path) -> None:
    assert all(p.passed for p in recompute_admission(read_study(FIXTURES / "study-f1.json"))["stop-70-reserve-30"])
    for plant in (lambda c: c["admission"].update(admitted=False),
                  lambda c: c["admission"]["parts"][3].update(limit={"exact": "7/1"})):
        doc = study_doc()
        plant(case_doc(doc, "stop-70-reserve-30"))
        with pytest.raises(StudyRefused) as got:
            recompute_admission(read_study(write_study(tmp_path, doc)))
        assert got.value.code == "STUDY_ADMISSION_MISMATCH"


# --- test 4: evaluate_options ---------------------------------------------------------------------------------------

def test_4_f1b_every_row() -> None:
    outcome, rows, options, one_offs = run_f1()
    assert outcome == "RECOMMENDED"
    _assert_no_action(rows["no-action"])
    for key in F1_KEYS[1:]:
        _assert_f1b_row(key, rows[key], one_offs, options)


def test_4_f1a_wear_missing() -> None:
    outcome, rows, options, one_offs = run_f1(base=f1_base(wear=False))
    assert outcome == "RANKING_INCOMPLETE"
    _assert_no_action(rows["no-action"])
    first = rows["stop-90-reserve-25"]
    assert (first.value, first.disposition, first.reason_code, first.missing) \
        == (D("-15.00"), "DEFERRED", "NOT_WORTH_MORE_THAN_NO_ACTION", ())
    expected = {"stop-80-reserve-30": "DEFERRED", "stop-80-reserve-25": "REJECTED", "stop-70-reserve-30": "DEFERRED",
                "stop-70-reserve-25": "DEFERRED", "stop-60-reserve-30": "DEFERRED", "stop-60-reserve-25": "REJECTED"}
    for key, disp in expected.items():
        row = rows[key]
        avoided, added = F1B[key][:2]
        reason = F1B[key][7] if disp == "REJECTED" else "VALUE_NOT_AVAILABLE"
        assert (row.disposition, row.reason_code, row.rank) == (disp, reason, None), key
        assert (row.monthly_change, row.horizon_change, row.value, row.currency) == (None, None, None, USD), key
        assert _missing(row) == [WEAR_MISSING] and row.assumed == DIESEL and row.source_class == "SIMULATED"
        effects = list(F1B_EFFECTS[key])
        for i in (4, 5, 6):  # the wear rate is missing: the wear, cost to serve and contribution have no change
            effects[i] = (effects[i][0], i, None, "MONEY", None if i == 4 else USD, [WEAR_MISSING])
        assert _effects(row) == effects, key
    assert rows["stop-70-reserve-30"].effects[3].change_per_month == D("-250.00")


def test_4_f1c_one_off_missing() -> None:
    outcome, rows, _, _ = run_f1(amounts={"stop-60-reserve-30": None})
    assert outcome == "RANKING_INCOMPLETE"
    row = rows["stop-60-reserve-30"]
    assert (row.disposition, row.reason_code, row.rank, row.value, row.one_off_id) \
        == ("DEFERRED", "VALUE_NOT_AVAILABLE", None, None, None)
    assert (row.monthly_change, row.horizon_change, _missing(row)) == (D("182.50"), D("2190.00"),
                                                                       [("ONE_OFF", "DECISION", None)])
    for key in ("stop-80-reserve-30", "stop-70-reserve-30", "stop-70-reserve-25"):
        assert (rows[key].disposition, rows[key].reason_code, rows[key].rank) \
            == ("ACCEPTABLE", "RANKING_INCOMPLETE", None)
        assert rows[key].value == D(F1B[key][4])
    assert rows["stop-90-reserve-25"].disposition == "DEFERRED"
    assert rows["stop-80-reserve-25"].disposition == rows["stop-60-reserve-25"].disposition == "REJECTED"


def test_4_f1d_doing_nothing_is_best() -> None:
    outcome, rows, _, _ = run_f1(amounts={k: "4000.00" for k in F1_KEYS[1:]})
    assert outcome == "NO_ACTION_BEST"
    values = {"stop-90-reserve-25": "-3925.00", "stop-80-reserve-30": "-1306.00", "stop-70-reserve-30": "-1030.00",
              "stop-70-reserve-25": "-898.00", "stop-60-reserve-30": "-1810.00"}
    for key, value in values.items():
        assert (rows[key].value, rows[key].disposition, rows[key].reason_code, rows[key].rank) \
            == (D(value), "DEFERRED", "NOT_WORTH_MORE_THAN_NO_ACTION", None)


def test_4_f1e_nothing_admitted(tmp_path) -> None:
    doc = study_doc()
    for case in doc["cases"]:
        case["max_starts_in_a_day"] = 7
        adm = case["admission"]
        adm["admitted"], adm["first_failing_part"] = False, "starts"
        adm["parts"][2].update(passed=False, case_value={"exact": "7/1"})
    study = read_study(write_study(tmp_path, doc))
    outcome, rows, _, _ = run_f1(study)
    assert outcome == "NOTHING_ADMITTED"
    for key in F1_KEYS[1:]:
        assert (rows[key].disposition, rows[key].reason_code, rows[key].rank) == ("REJECTED", "NOT_ADMITTED_STARTS",
                                                                                 None)
    parts = rows["stop-60-reserve-25"].admission["parts"]
    assert [(p["name"], p["passed"]) for p in parts] == [("energy_not_served", True), ("reserve_breaches", True),
                                                         ("starts", False), ("full_charge", False)]


def test_4_f1f_an_exact_tie_goes_to_doing_nothing() -> None:
    outcome, rows, options, one_offs = run_f1(amounts={"stop-90-reserve-25": "75.00"})
    assert outcome == "RECOMMENDED"
    row = rows["stop-90-reserve-25"]
    assert (row.value, row.disposition, row.reason_code, row.rank) \
        == (D("0.00"), "DEFERRED", "WORTH_THE_SAME_AS_NO_ACTION", None)
    for key in F1_KEYS[2:]:
        _assert_f1b_row(key, rows[key], one_offs, options)


def test_4_f1h_a_declared_season_values_nothing() -> None:
    outcome, rows, _, _ = run_f1(name="study-f1h.json")
    assert outcome == "RANKING_INCOMPLETE"
    _assert_no_action(rows["no-action"])
    missing_of = {"candidate_l": [SITE_MONTH[0]], "battery_throughput_kwh": [SITE_MONTH[1]],
                  "diesel_l": [SITE_MONTH[0]], "fuel_cost": [SITE_MONTH[0]], "battery_wear": [SITE_MONTH[1]],
                  "cost_to_serve": SITE_MONTH, "contribution": SITE_MONTH}
    for key in F1_KEYS[1:]:
        row = rows[key]
        disp, reason = (("REJECTED", F1B[key][7]) if F1B[key][5] == "REJECTED"
                        else ("DEFERRED", "VALUE_NOT_AVAILABLE"))
        assert (row.disposition, row.reason_code, row.rank) == (disp, reason, None), key
        assert (row.monthly_change, row.horizon_change, row.value, _missing(row)) == (None, None, None, SITE_MONTH)
        assert (row.source_class, row.evidence_class, row.assumed, row.currency) \
            == ("SIMULATED", "MODELLED", DIESEL, USD)
        assert row.dawn == F1_DAWN and row.admission["admitted"] is F1B[key][8]
        assert _effects(row) == [(f, i, None, u, c, missing_of[f])
                                 for i, (f, u, c) in enumerate(zip(MG_EFFECTS, MG_UNITS, MG_CURRENCY))]


def test_4_f1j_a_zero_change_takes_the_one_offs_currency(tmp_path) -> None:
    doc = study_doc()
    case = case_doc(doc, "stop-90-reserve-25")
    case["avoided_l_by_month"][0]["value"] = case["added_throughput_kwh_by_month"][0]["value"] = {"exact": "0/1"}
    outcome, rows, options, one_offs = run_f1(read_study(write_study(tmp_path, doc)))
    assert outcome == "RECOMMENDED"
    row = rows["stop-90-reserve-25"]
    assert (row.monthly_change, row.value, row.currency, row.disposition, row.reason_code, _missing(row)) \
        == (0, D("-90.00"), USD, "DEFERRED", "NOT_WORTH_MORE_THAN_NO_ACTION", [])
    assert row.assumed == ()  # no price was read: nothing changed
    assert _effects(row) == _mg_rows("0", "0", "0", "0", "0", "0", "0")  # D-P6.34: every zero money effect carries USD
    for key in F1_KEYS[2:]:
        _assert_f1b_row(key, rows[key], one_offs, options)


def test_4_f1g_the_recommended_at_the_grid_edge() -> None:
    outcome, rows, _, _ = run_f1(lever=F1G_LEVER, name="study-f1g.json")
    assert outcome == "RECOMMENDED"
    assert list(rows) == ["no-action", "stop-90-reserve-25", "stop-60-reserve-30", "stop-60-reserve-25"]
    assert [(r.disposition, r.reason_code, r.rank) for r in rows.values()] == [
        ("COMPARISON", None, None), ("DEFERRED", "NOT_WORTH_MORE_THAN_NO_ACTION", None),
        ("RECOMMENDED", "AT_GRID_EDGE", 1), ("REJECTED", "NOT_ADMITTED_FULL_CHARGE", None)]


def _single(registry, base, changes, amount, key):
    decision, options = decision_of(None, registry.structure_key, current={}, keys=(key,))
    inputs = (OptionInput(options[0], None, None, None, None),
              OptionInput(options[1], changes, None, None, None if amount is None else one_off_of(options[1], amount)))
    outcome, rows = evaluate_options(registry, base, decision, None, inputs)
    return outcome, rows


def test_4_c1_a_cold_room() -> None:
    outcome, (none, row) = _single(CC, c1_base(), C1_CHANGES, "400.00", "repair-chiller")
    assert outcome == "RECOMMENDED"
    _assert_no_action(none, "RECORDED")
    assert (row.disposition, row.reason_code, row.rank, row.monthly_change, row.horizon_change, row.value) \
        == ("RECOMMENDED", None, 1, D("100.00"), D("1200.00"), D("800.00"))
    assert (row.currency, row.source_class, row.evidence_class, row.assumed, row.missing, row.admission, row.dawn) \
        == (USD, "RECORDED", "MODELLED", (), (), None, None)
    assert _effects(row) == [("model_factor", 0, D("-0.1"), "1", None, []), ("kwh_model", 1, D(-500), "KWH", None, []),
                             ("kwh", 2, D(-500), "KWH", None, []), ("energy", 3, D("-100.00"), "MONEY", USD, []),
                             ("cost_to_serve", 4, D("-100.00"), "MONEY", USD, []),
                             ("contribution", 5, D("100.00"), "MONEY", USD, [])]


def test_4_c1e_an_emulated_input() -> None:
    _, (none, row) = _single(CC, c1_base(crate_origin="source-emulated"), C1_CHANGES, "400.00", "repair-chiller")
    assert row.source_class == "EMULATED" and none.source_class == "EMULATED"


def test_4_c1b_base_kwh_missing() -> None:
    outcome, (_, row) = _single(CC, c1_base(base_kwh=False), C1_CHANGES, "400.00", "repair-chiller")
    assert outcome == "RANKING_INCOMPLETE"
    assert (row.value, row.monthly_change, row.disposition, row.reason_code, _missing(row)) \
        == (None, None, "DEFERRED", "VALUE_NOT_AVAILABLE", [("energy_model", "DECLARED", "base_kwh")])
    assert (row.source_class, row.evidence_class, row.assumed) == ("RECORDED", "MODELLED", ())


def test_4_e1_an_ev_depot() -> None:
    outcome, (_, row) = _single(EV, e1_base(), E1_CHANGES, "0.00", "night-schedule")
    assert outcome == "RECOMMENDED"
    assert (row.disposition, row.rank, row.monthly_change, row.horizon_change, row.value, row.currency) \
        == ("RECOMMENDED", 1, D("200.00"), D("2400.00"), D("2400.00"), USD)
    assert (row.source_class, row.evidence_class, row.assumed) == ("RECORDED", "MODELLED", ())
    assert [(e.factor_id, e.change_per_month, e.unit) for e in row.effects] == [
        ("peak_kwh", D(-1000), "KWH"), ("kwh_0000_0500", D(1000), "KWH"), ("scheduled_kwh_night", 0, "KWH/DAY"),
        ("supplied_kwh_night", 0, "KWH/DAY"), ("buses_short_per_night", 0, "1"), ("departures_missed", 0, "DAY"),
        ("peak_cost", D("-300.00"), "MONEY"), ("night_cost", D("100.00"), "MONEY"),
        ("energy_cost", D("-200.00"), "MONEY"), ("penalties", 0, "MONEY"), ("cost_to_serve", D("-200.00"), "MONEY"),
        ("contribution", D("200.00"), "MONEY")]


def test_4_k1_the_real_file_values_nothing() -> None:
    study = read_study(FIXTURES / "kobo-61d-study.json")
    decision, options = decision_of(REAL_LEVER)
    by_key, ignored = match_cases(decision, options, study)
    assert len(by_key) == 13 and ignored == ("stop-90-reserve-30",)
    admissions = recompute_admission(study)
    assert len(admissions) == 14 and all(all(p.passed for p in parts) for parts in admissions.values())
    one_offs = {o.id: one_off_of(o) for o in options if o.generator == "SETTING_GRID"}
    inputs = option_inputs(options, REAL_LEVER, study, by_key, admissions, one_offs)
    outcome, rows = evaluate_options(MG, f1_base(), decision, REAL_LEVER, inputs)
    assert outcome == "RANKING_INCOMPLETE"
    rows = dict(zip([o.option_key for o in options], rows))
    _assert_no_action(rows["no-action"])
    for key, row in list(rows.items())[1:]:
        assert (row.disposition, row.reason_code, row.rank, row.value, row.monthly_change, _missing(row)) \
            == ("DEFERRED", "VALUE_NOT_AVAILABLE", None, None, None, SITE_MONTH), key
        assert (row.admission["admitted"], row.source_class, row.evidence_class, row.assumed) \
            == (True, "SIMULATED", "MODELLED", DIESEL)
    dawn = rows["stop-70-reserve-30"].dawn
    assert (dawn["worst_soc_pct"], dawn["margin_points"], dawn["days_below"], dawn["days"]) \
        == ("6611/190", "-39/190", 4, 61)


# --- test 8: no vertical code and no design value -----------------------------------------------------------------

SIX_C = [PKG / "decisions" / n for n in ("study_input.py", "models.py", "evaluate.py", "run.py")] + \
        [PKG / "structure" / "difference.py"]


def _strings(path: Path) -> set[str]:
    return {n.value for n in ast.walk(ast.parse(path.read_text())) if isinstance(n, ast.Constant)
            and isinstance(n.value, str)}


def test_8_no_structure_key_and_no_factor_id_in_the_evaluator() -> None:
    ids = {r.factor_id for reg in REGISTRIES.values() for r in reg.rows} | set(REGISTRIES)
    for path in (PKG / "decisions" / "evaluate.py", PKG / "structure" / "difference.py"):
        found = (_strings(path) & ids) - {"contribution"}
        assert not found, (path.name, found)


def test_8_no_numeric_literal_but_the_allowed_ones() -> None:
    for path in SIX_C:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and type(node.value) in (int, float, complex):
                assert node.value in (0, 1), (path.name, node.value, node.lineno)
        text = path.read_text()
        assert not re.search(r"/\s*(study\.)?days\b", text), path.name


def test_8_no_design_figure_under_decisions() -> None:
    for path in (PKG / "decisions").rglob("*.py"):
        text = path.read_text()
        assert not re.search(r"\b(210|2,?916|68)\b", text), path
        assert not re.search(r"\b(20|150) ?L\b", text), path


# --- test 9: seams --------------------------------------------------------------------------------------------------

def _imports(path: Path) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            out |= {f"{node.module}.{a.name}" for a in node.names}
    return out


def test_9_only_the_four_modules_import_runs_and_only_public_names() -> None:
    import importlib
    allowed = {"study_input.py", "models.py", "evaluate.py", "run.py"}
    for path in (PKG / "decisions").rglob("*.py"):
        for name in _imports(path):
            if not name.startswith("assetops_backend.runs"):
                continue
            assert path.name in allowed and path.parent.name == "decisions", (path, name)
            module, _, attr = name.rpartition(".")
            assert module in ("assetops_backend.runs.admission", "assetops_backend.runs.replay_study"), name
            public = importlib.import_module(module).__all__
            assert attr in public or attr.isupper(), name


def test_9_nothing_loads_the_simulator_or_the_host() -> None:
    for path in (PKG / "decisions").rglob("*.py"):
        assert not [n for n in _imports(path) if n.split(".")[0] in ("simulator", "host")], path
    code = ("import sys, assetops_backend.decisions.run as r; "
            "bad = [m for m in sys.modules if m.split('.')[0].startswith(('simulator', 'host'))]; "
            "print(bad); sys.exit(1 if bad else 0)")
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr


# --- M1, L1, D-P6.34 to D-P6.38 and D-P6.40: planted and injected cases, literal outcomes --------------------------------

import dataclasses  # noqa: E402

from assetops_backend.decisions import evaluate as evaluate_module  # noqa: E402
from assetops_backend.structure.difference import Delta  # noqa: E402
from assetops_backend.structure.levers import Lever, SettingAxis  # noqa: E402
from option_fixtures import (ASSUMING, DIVISION, OUTCOME_LEAF, PRODUCT, assumed, change, leaves_for,  # noqa: E402
                             stated)


def _planted_row(registry, base, changes, amount="0.00", currency="USD"):
    decision, options = decision_of(None, registry.structure_key, current={}, keys=("plant",))
    inputs = (OptionInput(options[0], None, None, None, None),
              OptionInput(options[1], changes, None, None, one_off_of(options[1], amount, currency)))
    return evaluate_options(registry, base, decision, None, inputs)


def test_4_a_changed_leaf_with_a_missing_base_names_its_record() -> None:
    base = leaves_for(PRODUCT, {"a": stated(250)})
    outcome, (_, row) = _planted_row(PRODUCT, base, {"a": change(100), "b": change(5)})
    assert outcome == "RANKING_INCOMPLETE"
    assert (row.value, row.monthly_change, row.horizon_change) == (None, None, None)
    assert (row.disposition, row.reason_code) == ("DEFERRED", "VALUE_NOT_AVAILABLE")
    assert _missing(row) == [("b_record", "PLANT_FAMILY", "b")]
    assert _effects(row)[2] == ("prod", 2, None, "L", None, [("b_record", "PLANT_FAMILY", "b")])


def test_4_a_one_off_in_another_currency_leaves_the_value_missing() -> None:
    """F1b with one option's one-off stated in EUR: its value is not available and no option is ranked."""
    outcome, rows, options, _ = run_f1(amounts={"stop-60-reserve-30": "90.00"})
    decision, opts = decision_of(TEST_LEVER)
    study = read_study(FIXTURES / "study-f1.json")
    by_key, _ = match_cases(decision, opts, study)
    one_offs = {o.id: one_off_of(o, "90.00", "EUR" if o.option_key == "stop-60-reserve-30" else "USD")
                for o in opts if o.generator == "SETTING_GRID"}
    inputs = option_inputs(opts, TEST_LEVER, study, by_key, recompute_admission(study), one_offs, grid_changes=TEST_GRID)
    outcome, rows = evaluate_options(MG, f1_base(), decision, TEST_LEVER, inputs)
    row = dict(zip([o.option_key for o in opts], rows))["stop-60-reserve-30"]
    assert outcome == "RANKING_INCOMPLETE"
    assert _missing(row) == [("ONE_OFF_CURRENCY", "DECISION", None)]
    assert (row.value, row.disposition, row.reason_code, row.rank) == (None, "DEFERRED", "VALUE_NOT_AVAILABLE", None)
    assert (row.monthly_change, row.horizon_change, row.currency) == (D("182.50"), D("2190.00"), USD)


def _leaf_option(monthly, amount, origin="demo-simulated"):
    return {"contribution": change(monthly, origin)}, amount


def _ranked(lever, current, pairs, registry=OUTCOME_LEAF, extra=()):
    """`pairs`: option key -> (monthly change on the outcome, one-off amount[, origin]); no study, no admission."""
    decision, options = decision_of(lever, current=current)
    by_key = {o.option_key: o for o in options}
    inputs = [OptionInput(options[0], None, None, None, None)]
    for key, spec in pairs.items():
        monthly, amount, *origin = spec
        inputs.append(OptionInput(by_key[key], {"contribution": change(monthly, *origin)}, None, None,
                                  one_off_of(by_key[key], amount)))
    outcome, rows = evaluate_options(registry, leaves_for(registry, {"contribution": stated(0)}), decision, lever,
                                     tuple(inputs))
    return outcome, {r.option_id: r for r in rows}, by_key


def _axis_lever(values, template="stop-{stop_soc_pct}"):
    return Lever("plant_stop", "MINI_GRID", "candidate_l", "SETTING_GRID",
                 (SettingAxis("stop_soc_pct", tuple(D(v) for v in values), "%"),), template, ("candidate_l",))


def _rec(rows, by_key, key):
    r = rows[by_key[key].id]
    return r.disposition, r.rank, r.reason_code


def test_4_the_near_set_includes_a_value_at_exactly_the_tie_threshold() -> None:
    """stop-70 is worth 1200 - 200 = 1000.00, stop-80 is worth 1200 - 300 = 900.00 = 1000.00 x 0.9 and is nearer."""
    lever = _axis_lever((90, 80, 70))
    outcome, rows, by_key = _ranked(lever, {"stop_soc_pct": D(90)},
                                    {"stop-80": (100, "300.00"), "stop-70": (100, "200.00")})
    assert outcome == "RECOMMENDED"
    assert rows[by_key["stop-70"].id].value == D("1000.00") and rows[by_key["stop-80"].id].value == D("900.00")
    assert _rec(rows, by_key, "stop-80") == ("RECOMMENDED", 1, None)
    assert _rec(rows, by_key, "stop-70") == ("ACCEPTABLE", 2, None)


def test_4_a_distance_tie_goes_to_the_higher_value() -> None:
    """stop-100 and stop-80 are both 10 from 90; stop-100 is worth 1000.00, stop-80 950.00."""
    lever = _axis_lever((110, 100, 90, 80))
    outcome, rows, by_key = _ranked(lever, {"stop_soc_pct": D(90)},
                                    {"stop-100": (100, "200.00"), "stop-80": (100, "250.00")})
    assert outcome == "RECOMMENDED"
    assert rows[by_key["stop-100"].id].value == D("1000.00") and rows[by_key["stop-80"].id].value == D("950.00")
    assert _rec(rows, by_key, "stop-100") == ("RECOMMENDED", 1, None)
    assert _rec(rows, by_key, "stop-80") == ("ACCEPTABLE", 2, None)


def test_4_the_recommended_setting_above_today_at_the_grid_edge() -> None:
    lever = _axis_lever((100, 90, 80))
    outcome, rows, by_key = _ranked(lever, {"stop_soc_pct": D(90)}, {"stop-100": (100, "200.00")})
    assert outcome == "RECOMMENDED"
    assert _rec(rows, by_key, "stop-100") == ("RECOMMENDED", 1, "AT_GRID_EDGE")


def test_4_no_actions_source_class_is_the_weakest_across_options() -> None:
    lever = _axis_lever((100, 90, 80))
    _, rows, by_key = _ranked(lever, {"stop_soc_pct": D(90)},
                              {"stop-100": (100, "200.00", "observed-financial"), "stop-80": (100, "200.00", "source-emulated")})
    assert rows[by_key["stop-100"].id].source_class == "RECORDED"
    assert rows[by_key["stop-80"].id].source_class == "EMULATED"
    no_action = next(r for r in rows.values() if r.disposition == "COMPARISON")
    assert no_action.source_class == "EMULATED"


def test_4_an_assumption_under_a_used_node_is_listed() -> None:
    """contribution = a x s, s = w x 2 with w an assumption: a changes, so s is read; `assumed` names w."""
    base = leaves_for(ASSUMING, {"a": stated(10), "w": assumed(ASSUMING, "w", 3, "USD")})
    _, (_, row) = _planted_row(ASSUMING, base, {"a": change(4)})
    assert row.monthly_change == D(24) and row.assumed == ("w",) and _missing(row) == []


def test_4_a_zero_denominator_is_named_as_such() -> None:
    base = leaves_for(DIVISION, {"a": stated(250), "z": stated(5)})
    outcome, (_, row) = _planted_row(DIVISION, base, {"z": change(-5)})
    assert outcome == "RANKING_INCOMPLETE" and row.value is None
    assert _missing(row) == [("ZERO_DENOMINATOR", "STRUCTURE", "r")]
    assert _effects(row)[1] == ("r", 1, None, "L", None, [("ZERO_DENOMINATOR", "STRUCTURE", "r")])


def test_4_a_zero_denominator_in_the_no_action_side_is_named_as_such() -> None:
    base = leaves_for(DIVISION, {"a": stated(250), "z": stated(0)})
    _, (_, row) = _planted_row(DIVISION, base, {"a": change(4)})
    assert _missing(row) == [("ZERO_DENOMINATOR", "STRUCTURE", "r")]


def _with_missing_names(monkeypatch, registry, names):
    real = evaluate_module.difference

    def fake(reg, base, changes):
        out = dict(real(reg, base, changes))
        out["contribution"] = Delta("contribution", None, out["contribution"].unit, None, names, (), "MODELLED", ())
        return out
    monkeypatch.setattr(evaluate_module, "difference", fake)


def test_4_a_node_with_no_value_is_named_by_its_own_missing_leaves(monkeypatch) -> None:
    base = leaves_for(PRODUCT, {"a": stated(250)})  # prod has no value: b is missing
    _with_missing_names(monkeypatch, PRODUCT, ("prod",))
    _, (_, row) = _planted_row(PRODUCT, base, {"a": change(100)})
    assert _missing(row) == [("b_record", "PLANT_FAMILY", "b")]


def test_4_a_missing_name_outside_the_closed_list_raises(monkeypatch) -> None:
    base = leaves_for(PRODUCT, {"a": stated(250), "b": stated(2)})
    _with_missing_names(monkeypatch, PRODUCT, ("ghost",))
    with pytest.raises(RuntimeError, match="ghost"):
        _planted_row(PRODUCT, base, {"a": change(100)})


def test_4_a_node_that_names_no_leaf_raises(monkeypatch) -> None:
    base = leaves_for(PRODUCT, {"a": stated(250), "b": stated(2)})  # prod has a value, so no leaf is missing
    _with_missing_names(monkeypatch, PRODUCT, ("prod",))
    with pytest.raises(RuntimeError, match="prod"):
        _planted_row(PRODUCT, base, {"a": change(100)})


def test_4_the_horizon_change_is_computed_in_the_structures_context() -> None:
    from decimal import getcontext
    monthly = D("1.00000000000000000000000000001")  # 30 digits
    assert getcontext().prec == 28 and monthly * 12 == D("12.00000000000000000000000000")  # the default rounds it
    _, rows, by_key = _ranked(_axis_lever((100, 90, 80)), {"stop_soc_pct": D(90)}, {"stop-100": (monthly, "0.00")})
    assert rows[by_key["stop-100"].id].horizon_change == D("12.00000000000000000000000000012")
