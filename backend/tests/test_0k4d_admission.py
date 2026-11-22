"""0K4d: the admission rule and the four replay measures it reads (spec §2.1, §2.2, §3 AD1-AD8). No kernel, no database.

The rule (D-0K4.9) is proven on stub `CaseOutcome`s built here; the measures (D-0K4.16 as corrected by D-0K4.28) on
stub projections over 2 local days in Africa/Addis_Ababa, both through the public `admission_measures` and through
`replay_study` with a scripted port.
"""

from __future__ import annotations

import ast
import dataclasses
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace

import pytest

from assetops_backend.runs import admission as ad
from assetops_backend.runs import replay_study as rs
from assetops_backend.runs.admission import (
    ADMISSION_PARTS,
    JUDGED,
    Admission,
    AdmissionRule,
    admit,
)
from assetops_backend.runs.replay_study import (
    CaseOutcome,
    DawnReading,
    ObservedSeries,
    StudyFrame,
    admission_measures,
    replay_study,
    step_local_times,
)
from assetops_contracts.forward_replay import ForwardReplayProjection, LoadSeries, ReplaySettings, ReplayStep

BACKEND = Path(__file__).resolve().parents[1]
ADMISSION = BACKEND / "assetops_backend" / "runs" / "admission.py"
START = "2026-08-31T21:00:00Z"  # 1 Sep 00:00 local
DAY1, DAY2 = "2026-09-01", "2026-09-02"
DAY = 288
N = 2 * DAY
RUN = SimpleNamespace(run_id="run-k")
FRAME = StudyFrame(timezone="Africa/Addis_Ababa", battery_capacity_kwh=F(200), min_litre_days=1, min_dawn_days=2)


# --- stubs -------------------------------------------------------------------------------------------------------------


def outcome(case_id: str = "stop-70-reserve-30", *, unserved=F(0), breaches=0, max_starts=2, longest=0,
            dawn_socs=(F(50), F(50)), input_class="SIMULATED") -> CaseOutcome:
    """A study outcome with every field set; only the four admission measures and the dawn readings vary."""
    dawn = tuple(DawnReading(f"2026-09-{i + 1:02d}", soc, "STOPPED") for i, soc in enumerate(dawn_socs))
    below = tuple(r.local_date for r in dawn if r.soc_pct < 35)
    return CaseOutcome(
        case_id=case_id, stop_soc_pct=F(70), stop_source="SETTING", reserve_soc_pct=F(30), reserve_source="BASELINE",
        fuel_l=F(100), avoided_l=F(0), avoided_l_by_month=(), generator_kwh=F(0), running_steps=0, starts=0,
        unserved_kwh=unserved, added_starts=0, added_running_steps=0, added_throughput_kwh=F(0),
        added_starts_by_month=(), added_throughput_kwh_by_month=(), throughput_kwh=F(0), min_soc_pct=F(30),
        dawn=dawn, dawn_days_below=len(below), worst_dawn_soc_pct=min(dawn_socs), dawn_verdict="NOT_CLAIMED",
        new_dawn_days_below=(), cleared_dawn_days_below=(), clipped_steps=0,
        reserve_breach_steps=breaches, max_starts_in_a_day=max_starts, full_charge_dates=(),
        longest_days_without_full_charge=longest, input_class=input_class,
    )


def part(result: Admission, name: str):
    return next(p for p in result.parts if p.name == name)


def proj(case_id: str, *, states=None, soc=None, soc_end=F(50), reserve=(F(30), "BASELINE"),
         stop=(F(90), "BASELINE")) -> ForwardReplayProjection:
    states = tuple(states) if states is not None else ("STOPPED",) * N
    soc = tuple(soc) if soc is not None else (F(50),) * N
    steps = tuple(ReplayStep(5 * i, states[i], F(0), F(0), soc[i], F(1000), False) for i in range(N))
    return ForwardReplayProjection(
        base_run_id="run-k", case_id=case_id, status="COMPLETED", model_profile_id="mini-grid",
        model_profile_version=7, interval_start=START, timestep_minutes=5, stop_soc_pct=stop[0], stop_source=stop[1],
        reserve_soc_pct=reserve[0], reserve_source=reserve[1], steps=steps, soc_end_pct=soc_end, fuel_end_l=F(1000),
        min_soc_pct=min(soc), generator_kwh=F(0), unserved_kwh=F(0), starts=0,
        running_steps=sum(1 for s in states if s == "RUNNING"), fuel_burned_l=F(0), clipped_offsets=(),
        replay_identity="x")


def observed(soc=None) -> ObservedSeries:
    return ObservedSeries(
        interval_start=START, timestep_minutes=5, pv_available_kw=(F(1),) * N,
        loads=(LoadSeries("load-res", (F(2),) * N),), generator_kwh=(F(0),) * N, generator_state=("STOPPED",) * N,
        soc_pct=tuple(soc) if soc is not None else (F(50),) * N, start_fuel_l=F(1000), input_class="SIMULATED")


class Stub:
    def __init__(self, scripts: dict):
        self.scripts = scripts

    def forward_replay(self, run, request):
        return self.scripts.get(request.case_id, self.scripts.get("*"))


LOCAL = step_local_times(observed(), FRAME)


# --- AD1 each part on its own ------------------------------------------------------------------------------------------


def test_ad1_each_part_passes_and_fails_on_its_own() -> None:
    base = outcome("baseline", unserved=F(3), breaches=2, max_starts=4, longest=3)
    passing = dict(unserved=F(3), breaches=2, max_starts=6, longest=6)
    result = admit(base, outcome(**passing))
    assert tuple(p.name for p in result.parts) == ADMISSION_PARTS
    assert result.admitted and all(p.passed for p in result.parts)
    failing = {"energy_not_served": dict(unserved=F(3) + F(1, 1000)), "reserve_breaches": dict(breaches=3),
               "starts": dict(max_starts=7), "full_charge": dict(longest=7)}
    assert set(failing) == set(ADMISSION_PARTS)
    for name, change in failing.items():
        one = admit(base, outcome(**{**passing, **change}))
        assert [p.name for p in one.parts if not p.passed] == [name]
        assert one.admitted is False
    two = admit(base, outcome(**{**passing, **failing["starts"], **failing["reserve_breaches"]}))
    assert [p.name for p in two.parts if not p.passed] == ["reserve_breaches", "starts"] and not two.admitted
    energy, reserve = part(result, "energy_not_served"), part(result, "reserve_breaches")
    assert (energy.judged, energy.limit, energy.case_value, energy.baseline_value) == ("RELATIVE", None, F(3), F(3))
    assert (reserve.judged, reserve.limit, reserve.case_value, reserve.baseline_value) == ("RELATIVE", None, F(2), F(2))
    assert {p.judged for p in result.parts} <= JUDGED
    assert all(type(v) is F for p in result.parts for v in (p.case_value, p.baseline_value))
    assert result.case_id == "stop-70-reserve-30" and result.rule == AdmissionRule()


# --- AD2 starts --------------------------------------------------------------------------------------------------------


def test_ad2_starts_absolute_then_relative() -> None:
    def starts(baseline: int, case: int):
        return part(admit(outcome("baseline", max_starts=baseline), outcome(max_starts=case)), "starts")

    assert (starts(4, 6).judged, starts(4, 6).passed, starts(4, 6).limit) == ("ABSOLUTE", True, F(6))
    assert (starts(4, 7).judged, starts(4, 7).passed) == ("ABSOLUTE", False)
    assert (starts(8, 7).judged, starts(8, 7).passed, starts(8, 7).limit) == ("RELATIVE_BASELINE_FAILS", True, F(6))
    assert (starts(8, 9).judged, starts(8, 9).passed) == ("RELATIVE_BASELINE_FAILS", False)
    assert (starts(6, 6).judged, starts(6, 6).passed) == ("ABSOLUTE", True)
    rule = AdmissionRule(max_starts_per_day=3)
    assert part(admit(outcome("baseline", max_starts=1), outcome(max_starts=4), rule), "starts").passed is False


# --- AD3 full charge ---------------------------------------------------------------------------------------------------


def test_ad3_full_charge_limit_is_every_days_less_one() -> None:
    def full(baseline: int, case: int):
        return part(admit(outcome("baseline", longest=baseline), outcome(longest=case)), "full_charge")

    assert full(0, 6).limit == F(6)
    assert (full(0, 6).judged, full(0, 6).passed) == ("ABSOLUTE", True)
    assert (full(0, 7).judged, full(0, 7).passed) == ("ABSOLUTE", False)
    assert (full(9, 8).judged, full(9, 8).passed) == ("RELATIVE_BASELINE_FAILS", True)
    assert (full(9, 10).judged, full(9, 10).passed) == ("RELATIVE_BASELINE_FAILS", False)
    assert (full(7, 7).judged, full(7, 7).passed) == ("RELATIVE_BASELINE_FAILS", True)


# --- AD4 the dawn never decides ----------------------------------------------------------------------------------------


def test_ad4_the_dawn_is_information_and_never_decides() -> None:
    base = outcome("baseline")
    low = admit(base, outcome(dawn_socs=(F(20),) * 20))
    assert low.dawn.days_below == 20 and low.admitted is True
    assert low.dawn.worst_soc_pct == F(20) and low.dawn.margin_points == F(20) - 35 == F(-15)
    assert len(low.dawn.dates_below) == 20
    high = admit(base, outcome(dawn_socs=(F(80), F(41), F(60)), max_starts=7))
    assert high.dawn.days_below == 0 and high.dawn.dates_below == () and high.admitted is False
    assert high.dawn.margin_points == F(41) - 35 == F(6)
    mixed = admit(base, outcome(dawn_socs=(F(50), F(34), F(36), F(10))))
    assert mixed.dawn.dates_below == ("2026-09-02", "2026-09-04") and mixed.dawn.days_below == 2
    other = admit(base, outcome(dawn_socs=(F(50), F(34), F(36), F(10))), dawn_limit_pct=F(40))
    assert other.dawn.days_below == 3 and other.dawn.margin_points == F(-30) and other.admitted
    assert not any("dawn" in p.name for p in low.parts)


# --- AD5 no action is never rejected -----------------------------------------------------------------------------------


def test_ad5_the_baseline_against_itself_is_admitted() -> None:
    base = outcome("baseline", unserved=F(5), breaches=4, max_starts=9, longest=12, dawn_socs=(F(10), F(20)))
    result = admit(base, base)
    assert result.admitted is True
    assert part(result, "starts").judged == "RELATIVE_BASELINE_FAILS"
    assert part(result, "full_charge").judged == "RELATIVE_BASELINE_FAILS"
    quiet = outcome("baseline")
    assert admit(quiet, quiet).admitted is True


# --- AD6 labels --------------------------------------------------------------------------------------------------------


def test_ad6_labels_and_a_mismatched_input_class() -> None:
    with pytest.raises(ValueError):
        admit(outcome("baseline", input_class="SIMULATED"), outcome(input_class="EMULATED"))
    result = admit(outcome("baseline", input_class="EMULATED"), outcome(input_class="EMULATED"))
    assert result.evidence_class == "MODELLED" and result.input_class == "EMULATED"
    with pytest.raises(ValueError):
        dataclasses.replace(result, evidence_class="OBSERVED")
    with pytest.raises(ValueError):
        dataclasses.replace(result.parts[0], judged="MAYBE")
    rule = AdmissionRule()
    assert (rule.max_starts_per_day, rule.full_charge_every_days, rule.basis) == (6, 7, "GENERIC_DEFAULT")


# --- AD7 the four measures ---------------------------------------------------------------------------------------------


def _states() -> list[str]:
    states = ["STOPPED"] * N
    for i in (10, 11, 12, 30, 31):  # day 1: two STOPPED to RUNNING/STARTING transitions
        states[i] = "RUNNING"
    states[30] = "STARTING"
    states[DAY + 10] = "RUNNING"  # day 2: one start
    for i in (DAY + 50, DAY + 70):  # day 2: FAILED then RUNNING twice, never a start (D-0K4.28, 0K2's B6)
        states[i], states[i + 1] = "FAILED", "RUNNING"
    return states


def test_ad7_reserve_breaches_read_the_case_reserve() -> None:
    soc = [F(50)] * N
    soc[100] = F(27)
    assert admission_measures(proj("baseline", soc=soc), LOCAL, "STOPPED")[0] == 1
    assert admission_measures(proj("stop-90-reserve-25", soc=soc, reserve=(F(25), "SETTING")), LOCAL, "STOPPED")[0] == 0
    soc[101] = F(30)  # at the reserve is not below it
    assert admission_measures(proj("baseline", soc=soc), LOCAL, "STOPPED")[0] == 1


def test_ad7_starts_by_local_day() -> None:
    measures = admission_measures(proj("baseline", states=_states()), LOCAL, "STOPPED")
    assert measures[1] == 2
    late = _states()
    late[DAY - 1] = "RUNNING"  # 23:55 on day 1: a third start, counted on day 1 (its start's local date)
    assert admission_measures(proj("baseline", states=late), LOCAL, "STOPPED")[1] == 3
    first = ["RUNNING"] + ["STOPPED"] * (N - 1)
    assert admission_measures(proj("baseline", states=first), LOCAL, "STOPPED")[1] == 1
    assert admission_measures(proj("baseline", states=first), LOCAL, "RUNNING")[1] == 0
    assert admission_measures(proj("baseline"), LOCAL, "STOPPED")[1] == 0


def test_ad7_full_charge_dates_and_longest_gap() -> None:
    soc = [F(50)] * N
    soc[200] = F(100)  # day 1 only
    assert admission_measures(proj("baseline", soc=soc, soc_end=F(100)), LOCAL, "STOPPED")[2:] == ((DAY1, DAY2), 0)
    assert admission_measures(proj("baseline", soc=soc, soc_end=F(99)), LOCAL, "STOPPED")[2:] == ((DAY1,), 1)
    assert admission_measures(proj("baseline"), LOCAL, "STOPPED")[2:] == ((), 2)
    assert admission_measures(proj("baseline", soc_end=F(100)), LOCAL, "STOPPED")[2:] == ((DAY2,), 1)
    second = [F(50)] * N
    second[DAY + 5] = F(100)
    assert admission_measures(proj("baseline", soc=second), LOCAL, "STOPPED")[2:] == ((DAY2,), 1)
    with pytest.raises(ValueError):
        admission_measures(proj("baseline"), LOCAL[:-1], "STOPPED")


def test_ad7_the_study_carries_the_four_measures() -> None:
    soc = [F(50)] * N
    soc[100] = F(27)
    soc[200] = F(100)
    series = observed(soc)
    case = proj("stop-90-reserve-25", soc=soc, states=_states(), soc_end=F(100), reserve=(F(25), "SETTING"))
    stub = Stub({"baseline": proj("baseline", soc=soc), "stop-90-reserve-25": case})
    frame = dataclasses.replace(FRAME, assumptions=("a 1 x (assumed, GENERIC_DEFAULT: d)",))
    result = replay_study(stub, RUN, series, frame, grid=(ReplaySettings(F(90), F(25)),))
    assert result.status == "CALIBRATED"
    assert result.assumptions == frame.assumptions
    b, c = result.baseline, result.cases[0]
    assert (b.reserve_breach_steps, b.max_starts_in_a_day, b.full_charge_dates, b.longest_days_without_full_charge) == (
        1, 0, (DAY1,), 1)
    assert (c.reserve_breach_steps, c.max_starts_in_a_day, c.full_charge_dates, c.longest_days_without_full_charge) == (
        0, 2, (DAY1, DAY2), 0)
    short = replay_study(stub, RUN, series, dataclasses.replace(frame, min_litre_days=3))
    assert short.status == "SAMPLE_TOO_SHORT" and short.assumptions == frame.assumptions
    assert replay_study(stub, RUN, series, FRAME, grid=(ReplaySettings(F(90), F(25)),)).assumptions == ()
    with pytest.raises(TypeError):
        dataclasses.replace(FRAME, assumptions=["x"])
    assert "admission_measures" in rs.__all__


# --- AD8 imports and words ---------------------------------------------------------------------------------------------

ADOPTING = ("reproduc", "confirm", "validat", "replace", "agree")  # D-0K2.20's scan, as 0K2's B13


def _string_constants(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings]


def test_ad8_admission_imports_exactly_its_modules_and_no_adopting_word() -> None:
    assert Path(ad.__file__).resolve() == ADMISSION.resolve()
    modules = set()
    for node in ast.walk(ast.parse(ADMISSION.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module)
    assert modules == {"__future__", "dataclasses", "fractions", "assetops_backend.runs.replay_study"}
    strings = _string_constants(ADMISSION)
    assert len(strings) > 10, "vacuous: almost no string constants"
    assert [s for s in strings if any(word in s.lower() for word in ADOPTING)] == []
