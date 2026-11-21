"""0K4b: the generator's fuel curve and the battery's charge taper, by hand.

Every expected value below is a literal or hand arithmetic from D-0K4.5 and
D-0K4.6, never a call to the function under test (W2).

Kobo's assumed curve (GENERIC_DEFAULT): SFC 0.3 L/kWh at full load, no-load
rate 3.3 L/h = 33/600 L/min, rated 40 kW.

    slope  s = 0.3 - 3.3 / 40 = 0.3 - 0.0825 = 0.2175 L/kWh = 2175/10000
    0 kWh   over 1 h:  3.3 L
    10 kWh  over 1 h:  3.3 + 2.175 = 5.475 L      (0.5475 L/kWh)
    20 kWh  over 1 h:  3.3 + 4.35  = 7.65 L       (0.3825 L/kWh)
    40 kWh  over 1 h:  3.3 + 8.7   = 12 L         (0.3 L/kWh = SFC)
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from assetops_contracts.execution_contract import (
    frozen_canonical_value,
    normalize_authored_float,
)
from assetops_simulator.packs import generator_curve as gc
from assetops_simulator.packs.errors import PhysicallyUnacceptable

F = Fraction
SFC = F(3, 10)
NO_LOAD = F(33, 600)
RATED = F(40)


def kobo():
    return gc.fuel_curve(SFC, NO_LOAD, RATED)


# --- F1-F3: the line through no load and full load ---------------------------


def test_f1_no_load_burns_the_declared_rate():
    assert gc.fuel_litres(kobo(), "RUNNING", F(60), F(0)) == F(33, 10)


def test_f2_full_load_burns_sfc_times_rating():
    assert gc.fuel_litres(kobo(), "RUNNING", F(60), F(40)) == F(12)
    assert F(12) == F(3, 10) * 40


def test_f3_part_load_is_the_straight_line():
    curve = kobo()
    assert curve.slope_l_per_kwh == F(2175, 10000)
    assert curve.no_load_l_per_min == F(33, 600)
    quarter = gc.fuel_litres(curve, "RUNNING", F(60), F(10))
    half = gc.fuel_litres(curve, "RUNNING", F(60), F(20))
    assert quarter == F(33, 10) + F(2175, 10000) * 10 == F(5475, 1000)
    assert half == F(765, 100)
    per_kwh = [F(5475, 1000) / 10, F(765, 100) / 20, F(12) / 40]
    assert per_kwh[0] > per_kwh[1] > per_kwh[2]  # strictly falling with load
    assert [quarter / 10, half / 20, gc.fuel_litres(curve, "RUNNING", F(60), F(40)) / 40] == per_kwh


# --- F4: states --------------------------------------------------------------


def test_f4_states():
    curve = kobo()
    assert gc.fuel_litres(curve, "STARTING", F(5), F(0)) == F(33, 600) * 5 == F(275, 1000)
    for state in ("STOPPED", "FAILED"):
        assert gc.fuel_litres(curve, state, F(5), F(0)) == 0
        assert gc.fuel_litres(curve, state, F(60), F(40)) == 0
    with pytest.raises(ValueError):
        gc.fuel_litres(curve, "STARTING", F(5), F(1, 100))


# --- F5: refusals, in order --------------------------------------------------


def _refusal(sfc, no_load, rated):
    with pytest.raises(gc.CurveRefused) as caught:
        gc.fuel_curve(sfc, no_load, rated)
    return caught.value.code


def test_f5_refusals_in_order():
    assert _refusal(SFC, F(0), RATED) == "NO_LOAD_NOT_POSITIVE"
    assert _refusal(F(9, 100), NO_LOAD, RATED) == "SFC_BELOW_DIESEL_ENERGY"
    # sfc 1/10, r = 5 L/h = 1/12 L/min: slope 1/10 - 60 x (1/12) / 40 = 1/10 - 1/8 < 0
    assert _refusal(F(1, 10), F(1, 12), RATED) == "NEGATIVE_SLOPE"
    # Overlaps decide the order: no-load first, then SFC, then slope.
    assert _refusal(F(9, 100), F(0), RATED) == "NO_LOAD_NOT_POSITIVE"
    # sfc 9/100 with r = 1/12: below diesel AND slope 9/100 - 1/8 < 0.
    assert _refusal(F(9, 100), F(1, 12), RATED) == "SFC_BELOW_DIESEL_ENERGY"
    # SFC exactly at the diesel bound is accepted.
    assert gc.fuel_curve(F(1, 10), F(1, 60), RATED).slope_l_per_kwh == F(1, 10) - F(1, 40)
    with pytest.raises(ValueError):
        gc.CurveRefused("NOPE", "")


# --- F6: the fuel cap --------------------------------------------------------


def test_f6_fuel_cap():
    curve = kobo()
    assert gc.output_cap_kw(curve, F(2, 10), F(5)) == 0
    assert gc.output_cap_kw(curve, F(1), F(5)) == (F(1) - F(275, 1000)) / (F(2175, 10000) * F(5, 60))
    # slope 0: sfc 0.3 with 3.3 L/h on an 11 kW set (3.3 / 11 = 0.3)
    flat = gc.fuel_curve(SFC, NO_LOAD, F(11))
    assert flat.slope_l_per_kwh == 0
    assert gc.output_cap_kw(flat, F(100), F(5)) is None
    assert gc.output_cap_kw(flat, F(1, 10), F(5)) == 0


# --- F7-F8: the taper --------------------------------------------------------


def test_f7_taper():
    limit, start = F(30), F(95)
    assert gc.charge_acceptance_kw(F(95), limit, start) == 30
    assert gc.charge_acceptance_kw(F(90), limit, start) == 30
    assert gc.charge_acceptance_kw(F(975, 10), limit, start) == 15
    assert gc.charge_acceptance_kw(F(999, 10), limit, start) == F(30, 20)
    assert gc.charge_acceptance_kw(F(100), limit, F(100)) == 30
    with pytest.raises(ValueError):
        gc.charge_acceptance_kw(F(1001, 10), limit, start)


def _steps(soc_from, soc_to, start, cap=500):
    """5-minute steps from one SOC to another on Kobo's 200 kWh, 95 % battery."""
    soc, steps = F(soc_from), 0
    while soc < soc_to:
        accepted = gc.charge_acceptance_kw(soc, F(30), start)
        soc += min(accepted * F(5, 60) * F(95, 100) / 200 * 100, F(100) - soc)
        steps += 1
        assert steps < cap, f"never reached {soc_to} % (stuck at {float(soc):.4f})"
    return steps


def test_f8_the_last_ten_points_are_slower():
    # At the 30 kW limit one step moves 30 x 5/60 x 0.95 / 200 x 100 = 1.1875 points.
    lower = _steps(80, 90, F(95))
    upper = _steps(90, 100, F(95))
    assert lower == 9  # 10 / 1.1875 = 8.42, so nine steps
    assert upper > lower
    flat_lower = _steps(80, 90, F(100))
    flat_upper = _steps(90, 100, F(100))
    assert abs(flat_upper - flat_lower) <= 1


# --- F9: exactness -----------------------------------------------------------


@pytest.mark.parametrize(
    "call, name",
    [
        (lambda: gc.fuel_curve(0.3, NO_LOAD, RATED), "sfc_l_per_kwh"),
        (lambda: gc.fuel_curve(SFC, 0.055, RATED), "no_load_l_per_min"),
        (lambda: gc.fuel_curve(SFC, NO_LOAD, 40), "rated_kw"),
        (lambda: gc.fuel_litres(kobo(), "RUNNING", 60.0, F(0)), "minutes"),
        (lambda: gc.fuel_litres(kobo(), "RUNNING", F(60), 1.5), "output_kwh"),
        (lambda: gc.output_cap_kw(kobo(), 1.0, F(5)), "fuel_l"),
        (lambda: gc.output_cap_kw(kobo(), F(1), 5), "minutes"),
        (lambda: gc.charge_acceptance_kw(95.0, F(30), F(95)), "soc_pct"),
        (lambda: gc.charge_acceptance_kw(F(95), 30.0, F(95)), "limit_kw"),
        (lambda: gc.charge_acceptance_kw(F(95), F(30), 95), "taper_start_pct"),
    ],
)
def test_f9_inexact_arguments_are_refused_by_name(call, name):
    with pytest.raises(TypeError, match=name):
        call()


# --- F10: the handlers -------------------------------------------------------


def _handler(key):
    return {h.state_key: h for h in gc.CURVE_HANDLERS}[key]


def test_f10_handlers():
    assert {h.state_key for h in gc.CURVE_HANDLERS} == {
        "generator-no-load-fuel-rate",
        "generator-minimum-load",
        "battery-charge-taper-start",
    }
    assert len(gc.CURVE_HANDLERS) == 3
    assert gc.CURVE_RELATIONS == ()
    rate = _handler("generator-no-load-fuel-rate")
    assert rate.dimension == "VOLUME_RATE"
    assert rate.consume(F(11, 200)) == F(11, 200)
    for bad in (F(0), F(-1)):
        with pytest.raises(PhysicallyUnacceptable, match="is not positive"):
            rate.consume(bad)
    minimum = _handler("generator-minimum-load")
    assert minimum.consume(F(0)) == 0 and minimum.consume(F(100)) == 100
    with pytest.raises(PhysicallyUnacceptable) as caught:
        minimum.consume(F(120))
    assert str(caught.value) == (
        "a minimum generator load of 120 % is not a share of the generator's rating"
    )
    with pytest.raises(PhysicallyUnacceptable):
        minimum.consume(F(-1))
    taper = _handler("battery-charge-taper-start")
    assert taper.consume(F(100)) == 100 and taper.consume(F(1, 10)) == F(1, 10)
    for bad in (F(0), F(1001, 10)):
        with pytest.raises(PhysicallyUnacceptable) as caught:
            taper.consume(bad)
        assert "is not a state of charge above 0 and at most 100" in str(caught.value)


# --- F11: the frozen path ----------------------------------------------------


def test_f11_frozen_l_per_h_burns_right_in_five_minutes():
    value, unit, _ = frozen_canonical_value(3.3, "L/h")
    rate = normalize_authored_float(value)
    assert unit == "L/min"
    assert rate == Fraction(11, 200)
    curve = gc.fuel_curve(Fraction(3, 10), rate, Fraction(40))
    assert gc.fuel_litres(curve, "STARTING", Fraction(5), Fraction(0)) == Fraction(11, 40)


# --- F12: the constants are v8's physics -------------------------------------


def test_f12_constants_are_pinned():
    assert gc.DIESEL_ENERGY_KWH_PER_L == Fraction(10)
    assert gc.MIN_SFC_L_PER_KWH == Fraction(1, 10)
    assert gc.TAPER_FLOOR_SHARE == Fraction(1, 20)
    assert gc.CURVE_REFUSALS == frozenset(
        {"NO_LOAD_NOT_POSITIVE", "SFC_BELOW_DIESEL_ENERGY", "NEGATIVE_SLOPE"}
    )
