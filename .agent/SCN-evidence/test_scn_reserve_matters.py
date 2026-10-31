"""SCN-kobo-reserve-matters U2: the kernel design check for `kobo-mini-grid-reserve-matters` v1 (no gateway, no DB).

Mini-grid v5 runs once on the template Foundation (reserve 30, start 35) and once with reserve 25. The test asserts
the scenario's design properties only, never money (`build-sheet-SCN-kobo-reserve.md` U2):

1. baseline: the generator starts at a step where SOC is in (30, 35] %, before offset 150;
2. baseline: generator energy > 0 in the whole UTC hour holding that start;
3. reserve 25: no generator start in the whole run, minimum SOC > 30 % and > the 25 % reserve;
4. baseline: the generator is still requested at offset >= 180 while PV covers every load;
5. every generator transition lies >= 20 min from 00:00 UTC.
"""

from __future__ import annotations

from fractions import Fraction

from test_mini_grid_v5 import GEN, SOC, _steps

NAME = "kobo-mini-grid-reserve-matters"
START_MINUTE_UTC = 3 * 60  # the run starts 03:00 UTC (06:00 local)


def _flows(boundary) -> dict[str, Fraction]:
    return {f.flow_id: f.energy for f in boundary.control_step.accepted.flows}


def _offset(boundary) -> int:
    return boundary.control_step.intent.from_offset


def _start(steps):
    """The first step whose generator state leaves STOPPED."""
    return next((b for b in steps if dict(b.discrete_for_step)[GEN] != "STOPPED"), None)


def test_baseline_starts_inside_the_band_the_trial_removes() -> None:
    _, base = _steps(NAME, 5)
    start = _start(base)
    assert start is not None, "the baseline generator never starts"
    assert _offset(start) < 150, _offset(start)
    assert Fraction(30) < dict(start.stocks)[SOC] <= Fraction(35), dict(start.stocks)[SOC]


def test_baseline_generator_delivers_energy_in_the_start_hour() -> None:
    _, base = _steps(NAME, 5)
    start = _start(base)
    assert start is not None
    hour = (START_MINUTE_UTC + _offset(start)) // 60
    in_hour = [b for b in base if (START_MINUTE_UTC + _offset(b)) // 60 == hour]
    energy = sum((_flows(b)["generator_output"] for b in in_hour), Fraction(0))
    assert energy > 0, f"generator energy {float(energy)} kWh in {hour:02d}:00-{hour + 1:02d}:00 UTC"


def test_reserve_25_never_starts_and_stays_above_30() -> None:
    _, later = _steps(NAME, 5, reserve=25)
    assert _start(later) is None
    lowest = min(dict(b.stocks)[SOC] for b in later)
    assert lowest > Fraction(30) and lowest > Fraction(25), lowest


def test_baseline_morning_runtime_is_unloaded_while_pv_covers_every_load() -> None:
    _, base = _steps(NAME, 5)
    unloaded = [
        b for b in base
        if _offset(b) >= 180 and dict(b.discrete_for_step)[GEN] == "RUNNING"
        and _flows(b)["generator_output"] == 0 and _flows(b)["load_demand"] > 0
        and _flows(b)["pv_to_load"] == _flows(b)["load_demand"]
    ]
    assert unloaded, "no unloaded generator step at offset >= 180 with PV covering every load"


def test_every_generator_transition_is_at_least_20_minutes_from_midnight() -> None:
    for reserve in (None, 25):
        _, steps = _steps(NAME, 5, reserve)
        states = [(_offset(b), dict(b.discrete_for_step)[GEN]) for b in steps]
        transitions = [offset for (offset, s), (_, prev) in zip(states[1:], states) if s != prev]
        for offset in transitions:
            minute = (START_MINUTE_UTC + offset) % 1440
            assert min(minute, 1440 - minute) >= 20, (reserve, offset)
