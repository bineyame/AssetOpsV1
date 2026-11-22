"""cold-thermal 2 (DD4.1, spec DD section 4.4, D-DD.22, D-DD.65): occupancy, COP, auxiliary load, f_m."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from fractions import Fraction

import pytest

from assetops_simulator.packs.cold import (
    DEFAULT_PROPERTY_VALUES, DD_LOAD_PARAMETERS, MODEL_PROFILE, MODEL_PROFILE_V2, PROPERTY_FIELDS, ColdForcingRow,
    ColdLoadParameters, ColdPack, ColdParameters, check_residual, run_window,
)
from assetops_simulator.packs.errors import PhysicallyUnacceptable

T0 = datetime(2026, 10, 6, 5, 0, tzinfo=timezone.utc)


def _params(**overrides: str) -> ColdParameters:
    values = dict(DEFAULT_PROPERTY_VALUES, **{"cold-cooling-capacity": "6"}, **overrides)
    return ColdParameters.from_properties({k: (values[k], PROPERTY_FIELDS[k][1]) for k in PROPERTY_FIELDS})


def _at(minute: int) -> datetime:
    return T0 + timedelta(minutes=minute)


def _f(minute: int, kind: str, asset: str, value: str) -> ColdForcingRow:
    return ColdForcingRow(_at(minute), kind, asset, value)


def _digest(run) -> str:
    rows = [repr((r.device_id, r.signal_id, r.source_time.isoformat(), r.measurement, str(r.value), r.unit,
                  r.quality, r.record_kind, r.outcome, r.transition_ordinal)) for r in run.records]
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


V1_FORCINGS = (
    _f(10, "DOOR_OPEN", "door-1", "OPEN"), _f(15, "DOOR_CLOSE", "door-1", "CLOSED"),
    _f(60, "GRID_LOSS", "grid-1", "LOST"), _f(60, "GENERATOR_FAILURE", "generator-1", "FAILED"),
    _f(200, "GRID_RESTORE", "grid-1", "AVAILABLE"),
)


def test_zero_load_terms_reproduce_v1_bytes():
    """C-DD19 (cold part): v2 with zero load terms, COP 1, f 1 and no crates is byte-identical to v1."""
    zero = ColdLoadParameters(respiration_kw_per_crate=Fraction(0), field_heat_kwh_per_crate_degc=Fraction(0),
                              cop=Fraction(1), auxiliary_kw=Fraction(0))
    kwargs = dict(start=T0, end=_at(6 * 60), initial_temperature=Fraction(3), ambient=Fraction(26),
                  forcings=V1_FORCINGS)
    v1 = run_window(ColdPack(_params()), **kwargs)
    v2 = run_window(ColdPack(_params(), load=zero), **kwargs)
    assert ColdPack(_params()).profile == MODEL_PROFILE == ("cold-thermal", 1)
    assert ColdPack(_params(), load=zero).profile == MODEL_PROFILE_V2 == ("cold-thermal", 2)
    assert len(v1.records) > 100
    assert _digest(v1) == _digest(v2)


def test_dd_load_parameters_are_the_spec_table():
    p = DD_LOAD_PARAMETERS
    assert p.respiration_kw_per_crate == Fraction(15, 10000)
    assert p.field_heat_kwh_per_crate_degc == Fraction(37, 1800)
    assert p.field_heat_minutes == 360 and p.field_heat_target_degc == 4
    assert p.cop == 2 and p.auxiliary_kw == 1


def test_crates_respiration_field_heat_and_meter_are_exact():
    """Heat = leak + door + crates x respiration + active field-heat pulses; meter = cooling x f / cop + aux."""
    pack = ColdPack(_params(), load=DD_LOAD_PARAMETERS)
    forcings = (_f(0, "CRATES_IN", "room-1", "40"), _f(0, "DOOR_OPEN", "door-1", "OPEN"),
                _f(5, "DOOR_CLOSE", "door-1", "CLOSED"), _f(0, "EFFICIENCY", "compressor-1", "500/403"))
    run = run_window(pack, start=T0, end=_at(400), initial_temperature=Fraction(3), ambient=Fraction(24),
                     forcings=forcings)
    first = run.transitions[0]
    pulse = 40 * Fraction(37, 1800) * (24 - 4) / 360
    leak = (Fraction(8, 100) * (24 - 3) + Fraction(2, 100) * 60) / 60
    assert first.heat_kwh == leak + 40 * Fraction(15, 10000) / 60 + pulse
    assert first.after.crates == 40
    # the pulse ends after 360 minutes
    late = run.transitions[365]
    assert late.heat_kwh == (Fraction(8, 100) * (24 - late.before.temperature)) / 60 + 40 * Fraction(15, 10000) / 60
    # meter: every 5-minute mean equals the slot's (cooling x f / cop + aux) mean, exactly
    meter = [r for r in run.records if r.device_id == "compressor-meter"]
    assert meter and all(r.unit == "kW" for r in meter)
    slot0 = run.transitions[0:5]
    expected = sum((Fraction(6) * Fraction(500, 403) / 2 if tr.before.compressor == "RUNNING" else 0) + 1
                   for tr in slot0) / 5
    powered = [tr for tr in slot0 if tr.before.bus == "POWERED"]
    assert len(powered) == 5
    assert meter[0].value == expected
    check_residual(pack.p, run.transitions[-1].after)


def test_crates_below_zero_raise_and_out_reduces():
    pack = ColdPack(_params(), load=DD_LOAD_PARAMETERS)
    with pytest.raises(PhysicallyUnacceptable):
        run_window(pack, start=T0, end=_at(10), initial_temperature=Fraction(3), ambient=Fraction(24),
                   forcings=(_f(1, "CRATES_OUT", "room-1", "1"),))
    run = run_window(pack, start=T0, end=_at(10), initial_temperature=Fraction(3), ambient=Fraction(24),
                     forcings=(_f(1, "CRATES_IN", "room-1", "7"), _f(3, "CRATES_OUT", "room-1", "5")))
    assert run.transitions[-1].after.crates == 2


def test_v1_refuses_v2_forcings():
    with pytest.raises(PhysicallyUnacceptable):
        run_window(ColdPack(_params()), start=T0, end=_at(5), initial_temperature=Fraction(3),
                   ambient=Fraction(24), forcings=(_f(1, "CRATES_IN", "room-1", "7"),))


def test_generator_reset_restarts_by_hand():
    """GENERATOR_RESET: FAILED -> STOPPED; the controller's start request then runs as usual (a start by hand)."""
    pack = ColdPack(_params(), load=DD_LOAD_PARAMETERS)
    forcings = (_f(0, "GRID_LOSS", "grid-1", "LOST"), _f(0, "GENERATOR_FAILURE", "generator-1", "FAILED"),
                _f(7, "GENERATOR_RESET", "generator-1", "STOPPED"), _f(169, "GRID_RESTORE", "grid-1", "AVAILABLE"))
    run = run_window(pack, start=T0, end=_at(180), initial_temperature=Fraction(3), ambient=Fraction(24),
                     forcings=forcings)
    gen = [(int((r.source_time - T0).total_seconds() // 60), r.record_kind, r.outcome) for r in run.records
           if r.device_id == "generator-controller" and r.measurement is None]
    assert gen == [(0, "START_REQUEST", "REQUESTED"), (5, "START_RESULT", "FAILED"),
                   (7, "START_REQUEST", "REQUESTED"), (9, "START_RESULT", "SUCCEEDED")]
    assert run.transitions[11].before.bus == "POWERED"


def test_generator_reset_of_a_generator_not_failed_raises():
    pack = ColdPack(_params(), load=DD_LOAD_PARAMETERS)
    with pytest.raises(PhysicallyUnacceptable):
        run_window(pack, start=T0, end=_at(10), initial_temperature=Fraction(3), ambient=Fraction(24),
                   forcings=(_f(0, "GRID_LOSS", "grid-1", "LOST"), _f(0, "GENERATOR_FAILURE", "generator-1", "FAILED"),
                             _f(3, "GENERATOR_RESET", "generator-1", "STOPPED")))


def test_full_room_at_capacity_runs_unclipped():
    """D-DD.65: a room at occupancy = capacity (400 crates, cooled) turns one 40-crate batch over at 28 degC ambient
    for a day: no clipping, an exact balance and the band held once the admitted batch's field heat is pulled down."""
    from dataclasses import replace
    from assetops_simulator.packs.cold import ColdState
    pack = ColdPack(_params(), load=DD_LOAD_PARAMETERS)
    state = replace(ColdState.initial(T0, Fraction(3), Fraction(28)), crates=400)
    forcings = {_at(180): (_f(180, "CRATES_OUT", "room-1", "40"), _f(180, "DOOR_OPEN", "door-1", "OPEN")),
                _at(185): (_f(185, "DOOR_CLOSE", "door-1", "CLOSED"),),
                _at(190): (_f(190, "CRATES_IN", "room-1", "40"), _f(190, "DOOR_OPEN", "door-1", "OPEN")),
                _at(195): (_f(195, "DOOR_CLOSE", "door-1", "CLOSED"),)}
    temps, meter, peak = [], [], 400
    for minute in range(24 * 60):
        tr = pack.step(state, forcings.get(_at(minute), ()), start=T0)
        state = tr.after
        peak = max(peak, state.crates)
        temps.extend(r.value for r in tr.records if r.device_id == "chamber-probe")
        meter.extend(r.value for r in tr.records if r.device_id == "compressor-meter")
    assert state.crates == 400 and peak == 400
    check_residual(pack.p, state)
    # 6 kW cooling exceeds leak + 400 x respiration + one batch's field heat at 28 degC: the band holds
    assert max(temps) < 5 and min(temps) > Fraction(3, 2)
    assert all(v >= 1 for v in meter)  # auxiliary always on a powered bus; no value clipped to a cap


# -- D-DD.87: the 10^-6 degC grid, the rounding booked in the energy ledger -------------------------------------

def _crates_run(load: ColdLoadParameters, minutes: int):
    forcings = (_f(0, "CRATES_IN", "room-1", "40"), _f(0, "DOOR_OPEN", "door-1", "OPEN"),
                _f(5, "DOOR_CLOSE", "door-1", "CLOSED"), _f(0, "EFFICIENCY", "compressor-1", "21/20"))
    return run_window(ColdPack(_params(), load=load), start=T0, end=_at(minutes), initial_temperature=Fraction(3),
                      ambient=Fraction(24), forcings=forcings)


def test_dd_load_parameters_declare_the_micro_degree_grid():
    assert DD_LOAD_PARAMETERS.temperature_quantum == Fraction(1, 1000000)


def test_every_step_temperature_is_on_the_grid_and_the_residual_holds():
    from dataclasses import replace
    run = _crates_run(DD_LOAD_PARAMETERS, 6 * 60)
    for tr in run.transitions:
        assert 1000000 % tr.after.temperature.denominator == 0
    last = run.transitions[-1].after
    assert last.rounding_total != 0
    pack = ColdPack(_params(), load=DD_LOAD_PARAMETERS)
    check_residual(pack.p, last)
    # the ledger is exact: dropping the booked rounding breaks it
    with pytest.raises(PhysicallyUnacceptable):
        check_residual(pack.p, replace(last, rounding_total=Fraction(0)))


def test_quantised_six_hours_match_exact_probe_readings_to_the_thousandth():
    from dataclasses import replace
    exact = _crates_run(replace(DD_LOAD_PARAMETERS, temperature_quantum=None), 6 * 60)
    grid = _crates_run(DD_LOAD_PARAMETERS, 6 * 60)
    assert exact.transitions[-1].after.rounding_total == 0

    def probe(run):
        return [(r.source_time, r.value) for r in run.records if r.device_id == "chamber-probe"]

    pe, pg = probe(exact), probe(grid)
    assert len(pe) == 6 * 60 // 5 + 1 and [t for t, _v in pe] == [t for t, _v in pg]
    # Known deviation (packet): rounding both to 0.001 differs at one reading that sits 1.7e-6 degC from a
    # half-thousandth; the readings themselves agree well inside a thousandth (measured max 2.9e-6 degC).
    assert max(abs(a - b) for (_t, a), (_u, b) in zip(pe, pg)) < Fraction(1, 100000)
