"""The generator's fuel curve and the battery's charge taper (0K4b; D-0K4.5, D-0K4.6).

These are `mini-grid` v8's physics: changing one is a new model version, never an edit.

**Fuel curve (D-0K4.5).** The straight line through the declared no-load rate
and the declared full-load consumption. While STARTING or RUNNING a generator
burns its no-load rate for every minute on, plus a slope per kWh delivered:

    litres = r x minutes_on + s x kWh       s = SFC - 60 x r / rated

with `r` the no-load rate in L/min (the frozen record's canonical unit for a
declared L/h; `CANONICAL_UNITS["L/h"]` divides by 60 once, at freezing), `SFC`
the declared full-load consumption in L/kWh and `rated` the rating in kW. At
full load the burn is `SFC x rated` an hour; at no load it is `r` a minute.
STOPPED and FAILED burn nothing.

A curve is refused when the no-load rate is not positive, when the full-load
consumption is below the energy content of diesel (a generator would make
energy from nothing), or when the slope is negative (part load would burn less
per kWh than nothing at all); checked in that order.

**Charge taper (D-0K4.6).** The battery accepts its PCS limit up to the taper
start; above it acceptance falls linearly to zero at 100 % state of charge,
never below a floor of one twentieth of the limit.

Every argument is a `Fraction`, so the kernel's exact balance checks stay
exact. The module holds no state and reads no context; 0K4a's resolver calls
it per segment.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from assetops_simulator.kernel.model import ComponentRelation, StateHandler
from assetops_simulator.packs import minigrid as daytime
from assetops_simulator.packs.fuel import PhysicallyUnacceptable

NO_LOAD_FUEL_RATE = "generator-no-load-fuel-rate"  # frozen in L/min (CANONICAL_UNITS "L/h" -> "L/min", /60)
MINIMUM_LOAD = "generator-minimum-load"  # % of the generator's rating
TAPER_START = "battery-charge-taper-start"  # % state of charge

#: Declared model constant: diesel holds about 9.9-10 kWh a litre.
DIESEL_ENERGY_KWH_PER_L = Fraction(10)
#: Below this a generator would make energy from nothing.
MIN_SFC_L_PER_KWH = 1 / DIESEL_ENERGY_KWH_PER_L
#: Acceptance never falls below 1/20 of the limit.
TAPER_FLOOR_SHARE = Fraction(1, 20)
HUNDRED = Fraction(100)
#: Minutes in an hour: the slope's `60 x r / rated` and the fuel cap's kWh in a step.
MINUTES_PER_HOUR = Fraction(60)
ON_STATES = frozenset({"STARTING", "RUNNING"})

CURVE_REFUSALS = frozenset({"NO_LOAD_NOT_POSITIVE", "SFC_BELOW_DIESEL_ENERGY", "NEGATIVE_SLOPE"})


class CurveRefused(Exception):
    """A declared fuel curve no generator can have; `code` is in `CURVE_REFUSALS`."""

    def __init__(self, code: str, detail: str) -> None:
        if code not in CURVE_REFUSALS:
            raise ValueError(f"{code!r} is not a fuel-curve refusal code")
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _exact(**arguments: object) -> None:
    for name, value in arguments.items():
        if not isinstance(value, Fraction):
            raise TypeError(f"{name} must be a Fraction, not {type(value).__name__}")


@dataclass(frozen=True)
class FuelCurve:
    no_load_l_per_min: Fraction  # r, already in L/min
    slope_l_per_kwh: Fraction  # s = sfc - 60 x no_load_l_per_min / rated


def fuel_curve(sfc_l_per_kwh: Fraction, no_load_l_per_min: Fraction, rated_kw: Fraction) -> FuelCurve:
    _exact(sfc_l_per_kwh=sfc_l_per_kwh, no_load_l_per_min=no_load_l_per_min, rated_kw=rated_kw)
    if no_load_l_per_min <= 0:
        raise CurveRefused(
            "NO_LOAD_NOT_POSITIVE", f"a no-load fuel rate of {no_load_l_per_min} L/min is not positive"
        )
    if sfc_l_per_kwh < MIN_SFC_L_PER_KWH:
        raise CurveRefused(
            "SFC_BELOW_DIESEL_ENERGY",
            f"a full-load consumption of {sfc_l_per_kwh} L/kWh is below {MIN_SFC_L_PER_KWH} L/kWh, "
            "the least diesel can give",
        )
    slope = sfc_l_per_kwh - MINUTES_PER_HOUR * no_load_l_per_min / rated_kw
    if slope < 0:
        raise CurveRefused(
            "NEGATIVE_SLOPE",
            f"a no-load rate of {no_load_l_per_min} L/min on a {rated_kw} kW generator burns more than "
            f"its full-load consumption of {sfc_l_per_kwh} L/kWh allows",
        )
    return FuelCurve(no_load_l_per_min=no_load_l_per_min, slope_l_per_kwh=slope)


def fuel_litres(curve: FuelCurve, state: str, minutes: Fraction, output_kwh: Fraction) -> Fraction:
    """Litres burned over `minutes` in `state` while delivering `output_kwh`."""
    _exact(minutes=minutes, output_kwh=output_kwh)
    if state not in ON_STATES:
        return Fraction(0)
    if state == "STARTING" and output_kwh != 0:
        raise ValueError(f"a STARTING generator delivers nothing, not {output_kwh} kWh")
    return curve.no_load_l_per_min * minutes + curve.slope_l_per_kwh * output_kwh


def output_cap_kw(curve: FuelCurve, fuel_l: Fraction, minutes: Fraction) -> Fraction | None:
    """The most kW `fuel_l` litres allow over `minutes` while RUNNING; `None` when fuel sets no bound."""
    _exact(fuel_l=fuel_l, minutes=minutes)
    idle = curve.no_load_l_per_min * minutes
    if fuel_l < idle:
        return Fraction(0)
    if curve.slope_l_per_kwh == 0:
        return None
    return (fuel_l - idle) / (curve.slope_l_per_kwh * minutes / MINUTES_PER_HOUR)


def charge_acceptance_kw(soc_pct: Fraction, limit_kw: Fraction, taper_start_pct: Fraction) -> Fraction:
    """The most kW the battery accepts at `soc_pct`: the limit, tapered above the start."""
    _exact(soc_pct=soc_pct, limit_kw=limit_kw, taper_start_pct=taper_start_pct)
    if soc_pct > HUNDRED:
        raise ValueError(f"a state of charge of {soc_pct} % is above full")
    if soc_pct <= taper_start_pct or taper_start_pct == HUNDRED:
        return limit_kw
    return limit_kw * max(TAPER_FLOOR_SHARE, (HUNDRED - soc_pct) / (HUNDRED - taper_start_pct))


# --- Handlers ----------------------------------------------------------------


def _positive_rate(value: Fraction, *_: object) -> Fraction:
    if value <= 0:
        raise PhysicallyUnacceptable(f"a no-load fuel rate of {value} L/min is not positive")
    return value


def _share_of_rating(value: Fraction, *_: object) -> Fraction:
    if not 0 <= value <= HUNDRED:
        raise PhysicallyUnacceptable(
            f"a minimum generator load of {value} % is not a share of the generator's rating"
        )
    return value


def _taper_start(value: Fraction, *_: object) -> Fraction:
    if not 0 < value <= HUNDRED:
        raise PhysicallyUnacceptable(
            f"a taper start of {value} % is not a state of charge above 0 and at most 100"
        )
    return value


CURVE_HANDLERS: tuple[StateHandler, ...] = (
    daytime._coefficient(
        NO_LOAD_FUEL_RATE,
        "generator-no-load-fuel-rate-coefficient",
        "VOLUME_RATE",
        _positive_rate,
        "Litres an hour the generator burns while STARTING or RUNNING at no output.",
    ),
    daytime._coefficient(
        MINIMUM_LOAD,
        "generator-minimum-load-coefficient",
        "FRACTION",
        _share_of_rating,
        "Site policy: the least share of its rating a running generator is held at.",
    ),
    daytime._coefficient(
        TAPER_START,
        "battery-charge-taper-start-coefficient",
        "FRACTION",
        _taper_start,
        "The state of charge above which the battery accepts less than its limit.",
    ),
)

#: None new: 0K4a adds the two generator keys to the v8 "generator" relation and
#: the taper key to the battery's (assembled there).
CURVE_RELATIONS: tuple[ComponentRelation, ...] = ()
