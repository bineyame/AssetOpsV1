"""S6-02b phase 1: `mini-grid` v5, the reserve-aware generator-start policy (`D-2026-10-16-s602a-replay`).

v5 requests the generator at or below min(start threshold, reserve in effect + 5). These tests run the kernel in
process (no gateway, no database) and read the recorded trajectory:

- on the template Foundation (reserve 30, start 35) v5 decides exactly what v4 decides, step by step;
- under a 25 % reserve the reserve-trial scenario's dawn dip (to 34.6 %) never reaches v5's 30 % start, while v4
  still starts at 35 % - the reserve is what v5 reads;
- the generator delivers no energy in the reserve-trial run (PV saturates the PCS charge limit), so the state of
  charge is identical with and without it - the physical basis of the v2 replay's comparability;
- v4's decision function is unchanged (its earlier versions stay reproducible).
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from assetops_backend.runs.profiles import MINI_GRID_V4_MODEL as V4_PROFILE
from assetops_backend.runs.profiles import MINI_GRID_V5_MODEL as V5_PROFILE
from assetops_simulator.packs import mini_grid

from execution_adapter import model_for, run_to_end
from kobo import kobo_draft

START = "2026-09-22T03:00:00Z"  # 06:00 in Africa/Addis_Ababa
END = "2026-09-22T11:00:00Z"
GEN = "generator-state@generator"
SOC = "battery-state-of-charge@battery"
TRIAL = "kobo-mini-grid-reserve-trial"
PROLONGED = "kobo-mini-grid-prolonged"


def _reserve(value: float):
    def edit(document):
        for item in document["foundation"]["components"]:
            for prop in item.get("properties") or []:
                if prop["property_key"] == "reserve-state-of-charge":
                    prop["value"], prop["source"] = value, "SITE"
                    return
        raise KeyError("reserve-state-of-charge")
    return edit


def _steps(name: str, version: int, reserve: float | None = None):
    run = kobo_draft(name, site_edit=None if reserve is None else _reserve(reserve), timestep_minutes=5,
                     model_profile="mini-grid", model_profile_version=version, start_time=START, end_time=END)
    assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
    trajectory = run_to_end(run, model_for(run)).trajectory
    steps = [b for b in trajectory.boundaries if b.control_step is not None]
    assert steps, "no control step was recorded"
    return trajectory, steps


def _row(boundary):
    requests = {r.quantity: r.requested for r in boundary.control_step.intent.requests}
    return (boundary.control_step.intent.from_offset, dict(boundary.stocks)[SOC], dict(boundary.discrete_for_step)[GEN],
            requests["generator-run"], requests["battery-power"])


def _running(steps) -> list[int]:
    return [b.control_step.intent.from_offset for b in steps if dict(b.discrete_for_step)[GEN] == "RUNNING"]


def test_profiles_are_a_new_version_beside_v4() -> None:
    assert (V5_PROFILE.model_profile_id, V5_PROFILE.model_profile_version) == ("mini-grid", 5)
    assert (mini_grid.MINI_GRID_V5_MODEL.model_profile_id, mini_grid.MINI_GRID_V5_MODEL.model_profile_version) == (
        "mini-grid", 5)
    assert mini_grid.MINI_GRID_V4_MODEL.coupling.decide is mini_grid.decide
    assert mini_grid.MINI_GRID_V5_MODEL.coupling.decide is mini_grid.decide_v5
    assert mini_grid.MINI_GRID_V5_MODEL.coupling.resolve is mini_grid.resolve_v4
    assert "reserve" in V5_PROFILE.statement and V4_PROFILE.statement in V5_PROFILE.statement


@pytest.mark.parametrize(("start", "reserve", "effective"), [(35, 30, 35), (35, 25, 30), (35, 40, 35), (20, 25, 20)])
def test_effective_start_threshold_is_never_above_the_site_start(start, reserve, effective) -> None:
    assert mini_grid.effective_start_threshold(Fraction(start), Fraction(reserve)) == effective


@pytest.mark.parametrize("name", [PROLONGED, TRIAL])
def test_on_the_template_reserve_v5_decides_exactly_as_v4(name: str) -> None:
    _, v4 = _steps(name, 4)
    _, v5 = _steps(name, 5)
    assert [_row(b) for b in v5] == [_row(b) for b in v4]
    assert _running(v5), "vacuous: the generator never ran"


def test_a_lower_reserve_lowers_the_v5_start_and_v4_ignores_it() -> None:
    _, base = _steps(TRIAL, 5)
    _, later = _steps(TRIAL, 5, reserve=25)
    _, v4_later = _steps(TRIAL, 4, reserve=25)
    lowest = min(dict(b.stocks)[SOC] for b in later)
    assert Fraction(30) < lowest <= Fraction(35), lowest  # the dip crosses 35 % but never reaches 30 %
    assert _running(base) and not _running(later)
    assert _running(v4_later) == _running(base)  # v4 reads only the start threshold
    reason = next(r.reason for b in later for r in b.control_step.intent.requests if r.quantity == "generator-run")
    assert "v5 start threshold 30" in reason and "reserve in effect 25" in reason, reason


def test_the_unloaded_generator_leaves_the_state_of_charge_unchanged() -> None:
    base_t, base = _steps(TRIAL, 5)
    _, later = _steps(TRIAL, 5, reserve=25)
    generator_energy = [f for b in base for f in b.control_step.accepted.flows
                        if "generator" in f.flow_id and f.energy]
    assert generator_energy == []
    assert [dict(b.stocks)[SOC] for b in base] == [dict(b.stocks)[SOC] for b in later]
    assert len(_running(base)) * 5 >= 120  # the baseline generator runs through the predeclared 06:00 window
