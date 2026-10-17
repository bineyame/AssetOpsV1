"""W2-02 `cold-thermal/1` pack (build spec commit 2; technical design section 4)."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from fractions import Fraction

import pytest

from assetops_simulator.packs import fuel
from assetops_simulator.packs.cold import (
    DEFAULT_PROPERTY_VALUES, PROPERTY_FIELDS, ColdForcingRow, ColdPack, ColdParameters, ColdState,
    check_move, check_residual, run_window,
)
from assetops_simulator.packs.errors import PhysicallyUnacceptable

T0 = datetime(2026, 10, 6, 19, 0, tzinfo=timezone.utc)
END = T0 + timedelta(hours=1)


def _params(**overrides: str) -> ColdParameters:
    values = dict(DEFAULT_PROPERTY_VALUES, **overrides)
    return ColdParameters.from_properties({k: (values[k], PROPERTY_FIELDS[k][1]) for k in PROPERTY_FIELDS})


def _at(minute: int) -> datetime:
    return T0 + timedelta(minutes=minute)


def _f(minute: int, kind: str, asset: str, value: str) -> ColdForcingRow:
    return ColdForcingRow(_at(minute), kind, asset, value)


def _events(run, device: str):
    return [(r.source_time, r.record_kind, r.outcome) for r in run.records
            if r.device_id == device and r.measurement is None]


def _temps(run):
    return [r for r in run.records if r.device_id == "chamber-probe"]


def test_normal_thermal_balance():
    run = run_window(ColdPack(_params()), start=T0, end=END, initial_temperature=Fraction(3), ambient=Fraction(10),
                     forcings=(_f(5, "GRID_LOSS", "grid-1", "LOST"), _f(35, "GRID_RESTORE", "grid-1", "AVAILABLE")))
    starts = _events(run, "generator-controller")
    assert starts == [(_at(5), "START_REQUEST", "REQUESTED"), (_at(7), "START_RESULT", "SUCCEEDED")]
    assert _events(run, "transfer-controller") == [(_at(8), "TRANSFER_RESULT", "SUCCEEDED"),
                                                   (_at(35), "TRANSFER_RESULT", "SUCCEEDED")]
    temps = _temps(run)
    assert len(temps) == 13 and temps[-1].source_time == END
    assert all(r.value < Fraction(7, 2) for r in temps)
    final = run.transitions[-1].after
    assert final.generator == "STOPPED" and final.transfer == "GRID" and final.bus == "POWERED"
    # exact balance: the law, minute by minute, with no cooling (T never reaches 4)
    expected = Fraction(3)
    for _ in range(60):
        expected += Fraction(8, 100) * (10 - expected) / 60 / Fraction(12, 10)
    assert final.temperature == expected
    check_residual(_params(), final)
    # bus never dropped outside the 19:05-19:08 transfer gap
    unpowered = [tr.before.minute for tr in run.transitions if tr.after.bus == "UNPOWERED"]
    assert unpowered == [_at(5), _at(6), _at(7)]


def test_door_heat_exact_002():
    pack = ColdPack(_params())
    state = ColdState.initial(T0, Fraction(3), Fraction(3))  # ambient = T: no leak
    opened = pack.step(state, (_f(0, "DOOR_OPEN", "door-1", "OPEN"),))
    assert opened.heat_kwh == Fraction(2, 100)
    assert opened.after.temperature - Fraction(3) == Fraction(2, 100) / Fraction(12, 10)
    assert opened.after.temperature - Fraction(3) < Fraction(17, 1000)
    closed = pack.step(opened.after, (_f(1, "DOOR_CLOSE", "door-1", "CLOSED"),))
    assert closed.heat_kwh == Fraction(8, 100) * (3 - opened.after.temperature) / 60
    door = [(r.record_kind, r.correlation_key) for r in opened.records + closed.records if r.device_id == "door-sensor"]
    assert door == [("DOOR_OPEN", ("door-cycle", 1)), ("DOOR_CLOSE", ("door-cycle", 1))]


def test_hysteresis_and_delays():
    pack = ColdPack(_params())
    state = ColdState.initial(T0, Fraction(4), Fraction(20))
    s1 = pack.step(state).after  # T>=4: demand, compressor STARTING (1 min delay)
    assert s1.demand and s1.compressor == "STARTING"
    s2 = pack.step(s1).after
    assert s2.compressor == "RUNNING"
    # between the bounds demand holds (hysteresis); it drops only at T<=2
    mid = replace(s2, temperature=Fraction(3), initial_temperature=Fraction(3), heat_total=Fraction(0),
                  cool_total=Fraction(0))
    held = pack.step(mid).after
    assert held.demand and held.compressor == "RUNNING"
    low = replace(held, temperature=Fraction(2), initial_temperature=Fraction(2), heat_total=Fraction(0),
                  cool_total=Fraction(0))
    off = pack.step(low).after
    assert not off.demand and off.compressor == "OFF"
    # failed start: request at 19:00, FAILED result at the 5-minute timeout
    run = run_window(pack, start=T0, end=END, initial_temperature=Fraction(38, 10), ambient=Fraction(20),
                     forcings=(_f(0, "GENERATOR_FAILURE", "generator-1", "FAILED"), _f(0, "GRID_LOSS", "grid-1", "LOST")))
    assert _events(run, "generator-controller") == [(_at(0), "START_REQUEST", "REQUESTED"),
                                                    (_at(5), "START_RESULT", "FAILED")]
    assert _events(run, "transfer-controller") == []
    assert run.state_at(_at(15)).temperature > Fraction(406, 100)
    assert run.state_at(_at(20)).temperature > Fraction(415, 100)


def test_invalid_capacity_transition_residual_temperature():
    with pytest.raises(PhysicallyUnacceptable):
        _params(**{"cold-thermal-capacity": "0"})
    with pytest.raises(PhysicallyUnacceptable):
        _params(**{"cold-cooling-capacity": "-3"})
    with pytest.raises(PhysicallyUnacceptable):
        ColdParameters.from_properties({k: (DEFAULT_PROPERTY_VALUES[k], "degF") for k in PROPERTY_FIELDS})
    with pytest.raises(PhysicallyUnacceptable):
        check_move("generator", "STOPPED", "RUNNING")
    state = ColdState.initial(T0, Fraction(3), Fraction(10))
    with pytest.raises(PhysicallyUnacceptable):
        check_residual(_params(), replace(state, heat_total=Fraction(1, 1000)))
    with pytest.raises(PhysicallyUnacceptable):
        ColdState.initial(T0, Fraction(61), Fraction(10))
    hot = ColdState.initial(T0, Fraction(5999, 100), Fraction(10000))
    with pytest.raises(PhysicallyUnacceptable):
        ColdPack(_params()).step(hot)
    assert fuel.PhysicallyUnacceptable is PhysicallyUnacceptable


def test_probe_failure_emits_one_unavailable_then_nothing():
    run = run_window(ColdPack(_params()), start=T0, end=END, initial_temperature=Fraction(3), ambient=Fraction(10),
                     forcings=(_f(12, "PROBE_FAILURE", "probe-1", "FAILED"),))
    temps = _temps(run)
    assert [r.quality for r in temps] == ["GOOD"] * 3 + ["UNAVAILABLE"]
    assert temps[-1].unavailable_reason == "SENSOR_FAILURE" and temps[-1].value is None


def test_cold_observation_transform_drop_hold_add_and_quantization():
    from types import SimpleNamespace as O

    from assetops_simulator.observation.transform import cold_observations, cold_value_text

    assert cold_value_text(Fraction(405, 100), "degC") == "4"  # half-even: 4.05 -> 4.0
    assert cold_value_text(Fraction(415, 100), "degC") == "4.2"
    assert cold_value_text(Fraction(9, 5), "kW") == "1.8"
    forcings = (_f(0, "GENERATOR_FAILURE", "generator-1", "FAILED"), _f(0, "GRID_LOSS", "grid-1", "LOST"))
    run = run_window(ColdPack(_params()), start=T0, end=END, initial_temperature=Fraction(38, 10),
                     ambient=Fraction(20), forcings=forcings)
    drops = tuple(O(at=_at(m), kind="PROBE_REPORT", device_id="probe-1", action="DROP", outcome=None,
                    release_at=None) for m in (15, 20, 25, 30, 35, 40))
    probe = [o for o in cold_observations(run.records, drops) if o.record.device_id == "chamber-probe"]
    assert len(probe) == 7
    assert all(o.published_at == o.record.source_time + timedelta(seconds=3) for o in probe)
    hold = (O(at=_at(20), kind="PROBE_REPORT", device_id="probe-1", action="HOLD", outcome=None,
              release_at=_at(70)),)
    held = [o for o in cold_observations(run.records, hold) if o.held]
    assert len(held) == 1 and held[0].record.source_time == _at(20) and held[0].published_at == _at(70)
    add = (O(at=_at(5), kind="START_RESULT", device_id="generator-1", action="ADD", outcome="SUCCEEDED",
             release_at=None),)
    starts = [o for o in cold_observations(run.records, add) if o.record.device_id == "generator-controller"
              and o.record.signal_id == "start-event"]
    results = [(o.record.outcome, o.transition_ordinal, o.record.correlation_key) for o in starts
               if o.record.record_kind == "START_RESULT"]
    assert sorted(results) == [("FAILED", 2, ("outage", 1)), ("SUCCEEDED", 3, ("outage", 1))]
