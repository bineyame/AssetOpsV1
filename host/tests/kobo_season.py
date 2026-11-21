"""0K2: a declared 61-day simulated Kobo season, run on the kernel as the site (spec §3; D-0K2.1 to D-0K2.3).

A test fixture, never a record: no Kobo series longer than a day exists in any store, and the season never enters a
database or the world. Each local day is built from the shipped Kobo day types, every value the shipped file's and
only re-based by the day's offset:

- 00:00-06:00 the four series of `kobo-night-early`;
- 06:00-18:00 the four series of `kobo-steady-day` (clear) or `kobo-daytime-overcast` (overcast, `overcast_v1`); the
  overcast file's `evening-reserve-override` is not a series and is left out (a declared simplification, D-0K2.22);
- 18:00-20:00 the `kobo-mini-grid-evening` events at offset 360;
- 20:00-24:00 `LATE_WINDOWS` (`tools/derive_steady_scenarios.py` `NIGHT_WINDOWS["late"]`), irradiance 0, mill 0.

One scenario document cannot hold a season (`document_bounds.py` refuses more than 4000 nodes at 8 days), so the
season's forcings are written straight into the base run's frozen inputs. This file shares no code with
`host/forward_replay.py` (W2).

`observed_series` publishes the site trajectory at the stated resolution (D-0K2.3): PV and load kW to 0.01, generator
kWh to 0.001, SOC to 0.1 point, fuel to 0.1 L, half-even (`round` on a `Fraction`). The input class it carries is
SIMULATED: a series made by the kernel, never shown as recorded.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from functools import cache
from typing import Callable

import yaml

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.replay_study import ObservedSeries
from assetops_contracts.forward_replay import LoadSeries
from assetops_contracts.world_inputs import ForcingInput, FrozenWorldInputs

from execution_adapter import frozen_world_inputs
from kobo import SCENARIOS, component, kobo_draft, set_property

SEASON_START = "2026-08-31T21:00:00Z"  # 1 Sep 2026 00:00 in Africa/Addis_Ababa (UTC+3, no clock change)
TIMEZONE = "Africa/Addis_Ababa"
SEASON_DAYS = 61  # 1 Sep - 31 Oct local
SEASON_START_SOC = Fraction(48)  # kobo-night-early's declared starting-state-of-charge (the measured handover)
SEASON_TANK_L = Fraction(20000)
SEASON_START_FUEL_L = Fraction(15000)
FOUNDATION_VALID_FROM = "2026-08-01T00:00:00Z"

#: (start minute of the local day, minutes, kW by load); pinned to NIGHT_WINDOWS["late"] by T8 (D-0K2.26).
LATE_WINDOWS = ((1200, 120, {"load-res": 9, "load-clinic": 4}),  # 20:00-22:00 local
                (1320, 120, {"load-res": 5, "load-clinic": 2}))  # 22:00-24:00 local

IRRADIANCE = "site:plane-of-array-irradiance"
RES, CLINIC, MILL = "load-demand@load-res", "load-demand@load-clinic", "load-demand@load-mill"
SERIES = (IRRADIANCE, RES, CLINIC, MILL)
LOAD_IDS = ("load-clinic", "load-mill", "load-res")
SOC = "battery-state-of-charge@battery"
TANK = "fuel-tank-volume@fuel-tank"
GEN = "generator-state@generator"
PV = "pv-available-power@pv-inverter"
GEN_OUT = "generator-output-power@generator"
STOP_ADDRESS = "generator-stop-soc-threshold@generator"
HOURS = Fraction(5, 60)
DAY = 1440


def overcast_v1(day_index: int) -> bool:
    return day_index % 4 == 3  # 15 of 61 days overcast


def season_site(document) -> None:
    document["foundation"]["valid_from"] = FOUNDATION_VALID_FROM
    set_property(document, "fuel-tank", "tank-capacity", int(SEASON_TANK_L))
    component(document, "fuel-tank")["rating"]["value"] = int(SEASON_TANK_L)


def _utc(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def base_run(days: int, *, start: str = SEASON_START, site_edit=season_site, version: int = 7) -> SimulationRun:
    run = kobo_draft("kobo-mini-grid-prolonged", timestep_minutes=5, model_profile="mini-grid",
                     model_profile_version=version, start_time=start,
                     end_time=_iso(_utc(start) + timedelta(days=days)), site_edit=site_edit)
    return run


@cache
def _series_events(name: str) -> tuple[tuple[str, int, int, Fraction], ...]:
    """(address, offset, duration, value) of the file's four series, in file order."""
    document = yaml.safe_load((SCENARIOS / f"{name}.yaml").read_text(encoding="utf-8"))
    return tuple(
        (event["state_key"], event["offset_minutes"], event["timing"]["duration_minutes"],
         Fraction(str(event["parameters"][0]["value"])))
        for event in document["timeline"] if event["state_key"] in SERIES
    )


def day_windows(day_index: int, overcast: Callable[[int], bool] = overcast_v1):
    """Every (address, offset from the window start, duration, value) of one local day."""
    base = day_index * DAY
    rows = [(a, base + o, d, v) for a, o, d, v in _series_events("kobo-night-early")]
    day = "kobo-daytime-overcast" if overcast(day_index) else "kobo-steady-day"
    rows += [(a, base + 360 + o, d, v) for a, o, d, v in _series_events(day)]
    rows += [(a, base + 1080, d, v) for a, o, d, v in _series_events("kobo-mini-grid-evening") if o == 360]
    for start, minutes, loads in LATE_WINDOWS:
        rows += [(IRRADIANCE, base + start, minutes, Fraction(0)),
                 (RES, base + start, minutes, Fraction(loads["load-res"])),
                 (CLINIC, base + start, minutes, Fraction(loads["load-clinic"])),
                 (MILL, base + start, minutes, Fraction(0))]
    return rows


def season_inputs(run, days, *, overcast=overcast_v1, load_scale=Fraction(1), start_fuel_l=SEASON_START_FUEL_L,
                  site_stop_pct: Fraction | None = None) -> FrozenWorldInputs:
    inputs = frozen_world_inputs(run)
    templates = {}
    for forcing in inputs.forcings:
        templates.setdefault(forcing.address, forcing)
    assert set(SERIES) <= set(templates), sorted(set(SERIES) - set(templates))
    built = []
    for d in range(days):
        for address, offset, duration, value in day_windows(d, overcast):
            if address != IRRADIANCE:
                value = value * load_scale
            built.append(dataclasses.replace(templates[address], event_id=f"season:{address}:{offset}",
                                             parameter_id="season", value=value, shape="WINDOW",
                                             offset_minutes=offset, duration_minutes=duration))
    if site_stop_pct is not None:
        built.append(ForcingInput(event_id="season:stop", address=STOP_ADDRESS,
                                  state_key="generator-stop-soc-threshold", parameter_id="season",
                                  value=site_stop_pct, canonical_unit="%", dimension="FRACTION", shape="WINDOW",
                                  offset_minutes=0, duration_minutes=inputs.interval.duration_minutes,
                                  requirement="REQUIRED"))
    forcings = tuple(f for f in inputs.forcings if f.address not in SERIES) + tuple(built)

    def initial(row):
        if row.address == SOC:
            return dataclasses.replace(row, value=SEASON_START_SOC)
        if row.address == TANK:
            return dataclasses.replace(row, value=start_fuel_l)
        return row

    return dataclasses.replace(inputs, forcings=forcings,
                               initial_values=tuple(initial(row) for row in inputs.initial_values))


def _q(value: Fraction, quantum: Fraction) -> Fraction:
    return round(value / quantum) * quantum  # half-even on a Fraction


def observed_series(trajectory, n, *, input_class="SIMULATED", start: str = SEASON_START) -> ObservedSeries:
    B = trajectory.boundaries
    kw, kwh, pct, litre = Fraction(1, 100), Fraction(1, 1000), Fraction(1, 10), Fraction(1, 10)
    return ObservedSeries(
        interval_start=start,
        timestep_minutes=5,
        pv_available_kw=tuple(_q(B[i + 1].interval_measurement(PV) / HOURS, kw) for i in range(n)),
        loads=tuple(
            LoadSeries(load, tuple(_q(B[i + 1].interval_measurement(f"load-requested-power@{load}") / HOURS, kw)
                                   for i in range(n)))
            for load in sorted(LOAD_IDS, reverse=True)
        ),
        generator_kwh=tuple(_q(B[i + 1].interval_measurement(GEN_OUT), kwh) for i in range(n)),
        generator_state=tuple(B[i].discrete_state_for_step(GEN) for i in range(n)),
        soc_pct=tuple(_q(B[i].stock(SOC), pct) for i in range(n)),
        start_fuel_l=_q(B[0].stock(TANK), litre),
        input_class=input_class,
    )


__all__ = [
    "LATE_WINDOWS",
    "SEASON_DAYS",
    "SEASON_START",
    "SEASON_START_FUEL_L",
    "SEASON_START_SOC",
    "SEASON_TANK_L",
    "TIMEZONE",
    "base_run",
    "day_windows",
    "observed_series",
    "overcast_v1",
    "season_inputs",
    "season_site",
]
