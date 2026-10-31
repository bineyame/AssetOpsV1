"""SCN-kobo-reserve-matters U2 (design D2): the kernel design check for `kobo-mini-grid-reserve-matters` v1.

In process, no gateway, no database. Mini-grid v5 runs once on the template Foundation (reserve 30, start 35) and
once with reserve 25. The test asserts the scenario's design properties only, never money
(`build-sheet-SCN-kobo-reserve.md` Addendum 1, which replaces the first U2 properties):

1. baseline: the generator delivers > 0 kWh in at least one whole UTC hour lying before offset 240; H is the first
   such hour;
2. reserve 25: generator energy in H is 0 kWh (its start is allowed);
3. neither run goes below its own reserve;
4. baseline: the generator is still requested after the clearing (offset >= 240) while PV covers every load;
5. every generator transition lies >= 20 min from 00:00 UTC.

The trial changes generator energy, not starts: before the baseline generator carries load both runs share one
state-of-charge path, and the baseline's reserve (30 %) is the reserve-25 run's own v5 start.
"""

from __future__ import annotations

from fractions import Fraction

from test_mini_grid_v5 import GEN, SOC, _steps

NAME = "kobo-mini-grid-reserve-matters"
START_MINUTE_UTC = 3 * 60  # the run starts 03:00 UTC (06:00 local)
CLEARING = 240  # irradiance-2 offset


def _flows(boundary) -> dict[str, Fraction]:
    return {f.flow_id: f.energy for f in boundary.control_step.accepted.flows}


def _offset(boundary) -> int:
    return boundary.control_step.intent.from_offset


def _hour(boundary) -> int:
    return (START_MINUTE_UTC + _offset(boundary)) // 60


def _energy_in(steps, hour: int) -> Fraction:
    return sum((_flows(b)["generator_output"] for b in steps if _hour(b) == hour), Fraction(0))


def _first_loaded_hour(steps) -> int | None:
    """The first whole UTC hour, lying wholly before the clearing, whose generator energy is > 0 kWh."""
    for hour in sorted({_hour(b) for b in steps}):
        if (hour + 1) * 60 - START_MINUTE_UTC > CLEARING:
            return None
        if _energy_in(steps, hour) > 0:
            return hour
    return None


def test_baseline_generator_carries_load_for_a_whole_hour_before_the_clearing() -> None:
    _, base = _steps(NAME, 5)
    hour = _first_loaded_hour(base)
    assert hour is not None, "no whole hour before the clearing with the baseline generator loaded"
    # Recorded U3 window (the first loaded clock hour in the kernel run), not a design target: 04:00-05:00 UTC.
    assert hour == 4, hour
    assert _energy_in(base, hour) > 0


def test_reserve_25_generator_delivers_nothing_in_that_hour() -> None:
    _, base = _steps(NAME, 5)
    _, later = _steps(NAME, 5, reserve=25)
    hour = _first_loaded_hour(base)
    assert hour is not None
    assert _energy_in(later, hour) == 0, (hour, float(_energy_in(later, hour)))


def test_neither_run_goes_below_its_own_reserve() -> None:
    for reserve, value in ((None, Fraction(30)), (25, Fraction(25))):
        _, steps = _steps(NAME, 5, reserve)
        lowest = min(dict(b.stocks)[SOC] for b in steps)
        assert lowest >= value, (reserve, lowest)


def test_baseline_morning_runtime_is_unloaded_while_pv_covers_every_load() -> None:
    _, base = _steps(NAME, 5)
    unloaded = [
        b for b in base
        if _offset(b) >= CLEARING and dict(b.discrete_for_step)[GEN] == "RUNNING"
        and _flows(b)["generator_output"] == 0 and _flows(b)["load_demand"] > 0
        and _flows(b)["pv_to_load"] == _flows(b)["load_demand"]
    ]
    assert unloaded, "no unloaded generator step after the clearing with PV covering every load"


def test_every_generator_transition_is_at_least_20_minutes_from_midnight() -> None:
    for reserve in (None, 25):
        _, steps = _steps(NAME, 5, reserve)
        states = [(_offset(b), dict(b.discrete_for_step)[GEN]) for b in steps]
        # Prepend the scenario's starting generator state so the transition into step 0 is checked.
        states.insert(0, (0, 'STOPPED'))
        transitions = [offset for (offset, s), (_, prev) in zip(states[1:], states) if s != prev]
        assert transitions or reserve == 25, "vacuous: the baseline generator never changed state"
        for offset in transitions:
            minute = (START_MINUTE_UTC + offset) % 1440
            assert min(minute, 1440 - minute) >= 20, (reserve, offset)
