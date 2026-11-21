"""0K3: the replay series reader on 0K2's simulated season published as readings (spec §3 S8, §4 T1-T2). Kernel.

S8 is 0K2's 8-day season (`test_0k2_kobo_season.site("8")`). This file's own writer publishes it as readings, with
its own addresses and quanta spelled here: for step `i`, PV and each load as a 5-minute mean `[t_i, t_{i+1})` in kW,
the generator's energy as a 5-minute mean of power (kWh x 12), SOC and generator state at `t_i`, the tank at `t_0`.
The expected value is `kobo_season.observed_series`, never the writer (W2).

Note (D-0K3.16): the season's loads are the kernel's requested power (`load-requested-power@<id>`), published here
as `feeder_demand`; T1 proves placement on the grid, not D-0K3.5's meaning (delivered power).
"""

from __future__ import annotations

import itertools
from datetime import datetime, timedelta, timezone
from fractions import Fraction as F
from uuid import UUID

from assetops_backend.analytics.assessment_inputs import AcceptedReading, Window
from assetops_backend.runs.replay_series import series_from_readings
from assetops_backend.runs.replay_study import replay_study

from forward_replay import HostForwardReplay
from kobo_season import observed_series
from test_0k2_kobo_season import frame, site

STEPS = 8 * 288  # 2304
START = datetime(2026, 8, 31, 21, 0, tzinfo=timezone.utc)  # 1 Sep 00:00 in Africa/Addis_Ababa
FIVE = timedelta(minutes=5)
HOURS = F(5, 60)
# the season's addresses, spelled here
PV_ADDR = "pv-available-power@pv-inverter"
GEN_OUT = "generator-output-power@generator"
SOC_ADDR = "battery-state-of-charge@battery"
TANK = "fuel-tank-volume@fuel-tank"
GEN = "generator-state@generator"
LOAD_CODES = ("load-clinic", "load-mill", "load-res")
ASSETS = {code: UUID(int=100 + i) for i, code in enumerate(("pv-inverter", "generator", "battery", "fuel-tank",
                                                             *LOAD_CODES))}
CODES = {v: k for k, v in ASSETS.items()}
BOUND = {"pv_available_power": (ASSETS["pv-inverter"],), "feeder_demand": tuple(ASSETS[c] for c in LOAD_CODES),
         "generator_power": (ASSETS["generator"],), "generator_state": (ASSETS["generator"],),
         "battery_soc": (ASSETS["battery"],), "fuel_level": (ASSETS["fuel-tank"],)}
_ids = itertools.count(1)


def quantum(value: F, step: F) -> F:
    return round(value / step) * step  # half-even on a Fraction


def decimal(value: F, places: int) -> str:
    scaled = value * 10 ** places
    assert scaled.denominator == 1, (value, places)
    n = scaled.numerator
    sign, n = ("-" if n < 0 else ""), abs(n)
    whole, frac = divmod(n, 10 ** places)
    return f"{sign}{whole}" + (f".{frac:0{places}d}" if places else "")


def reading(role, asset, value, unit, *, at=None, start=None, end=None) -> AcceptedReading:
    n = next(_ids)
    source_time = at if at is not None else end
    return AcceptedReading(
        evidence_id=UUID(int=10**6 + n), envelope_sha256="0" * 64, batch_id=UUID(int=7), gateway_id=UUID(int=1),
        source_id=UUID(int=2), sequence_epoch="season", sequence=n, role=role, asset_id=ASSETS[asset],
        source_time=source_time, interval_start=start, interval_end=end, published_at=source_time,
        received_at=source_time, accepted_at=source_time, quality="GOOD", value=value, unit=unit,
        foundation_revision_id=UUID(int=3), binding_set_revision_id=UUID(int=4), binding_revision_id=UUID(int=5),
        source_mode="SIMULATED")


def publish(trajectory) -> list[AcceptedReading]:
    """S8: the season as readings (this file's writer)."""
    B = trajectory.boundaries
    out = []
    for i in range(STEPS):
        t, t1 = START + i * FIVE, START + (i + 1) * FIVE
        pv = quantum(B[i + 1].interval_measurement(PV_ADDR) / HOURS, F(1, 100))
        out.append(reading("pv_available_power", "pv-inverter", decimal(pv, 2), "kW", start=t, end=t1))
        for code in LOAD_CODES:
            kw = quantum(B[i + 1].interval_measurement(f"load-requested-power@{code}") / HOURS, F(1, 100))
            out.append(reading("feeder_demand", code, decimal(kw, 2), "kW", start=t, end=t1))
        gen_kw = quantum(B[i + 1].interval_measurement(GEN_OUT), F(1, 1000)) * 12
        out.append(reading("generator_power", "generator", decimal(gen_kw, 3), "kW", start=t, end=t1))
        out.append(reading("battery_soc", "battery", decimal(quantum(B[i].stock(SOC_ADDR), F(1, 10)), 1), "%", at=t))
        state = B[i].discrete_state_for_step(GEN)
        if state is not None:
            out.append(reading("generator_state", "generator", state, "state", at=t))
    out.append(reading("fuel_level", "fuel-tank", decimal(quantum(B[0].stock(TANK), F(1, 10)), 1), "L", at=START))
    return out


def _season():
    run, trajectory = site("8")
    placed = series_from_readings(publish(trajectory), BOUND, CODES, Window(START, START + STEPS * FIVE))
    return run, trajectory, placed


def test_t1_the_published_season_reads_back_field_by_field() -> None:
    _, trajectory, placed = _season()
    got, want = placed.series, observed_series(trajectory, STEPS)
    assert got.interval_start == want.interval_start == "2026-08-31T21:00:00Z"
    assert got.timestep_minutes == want.timestep_minutes
    assert got.pv_available_kw == want.pv_available_kw
    assert {x.load_id: x.kw for x in got.loads} == {x.load_id: x.kw for x in want.loads}
    assert len(got.loads) == len(want.loads) == 3
    assert got.generator_kwh == want.generator_kwh
    assert got.generator_state == want.generator_state
    assert got.soc_pct == want.soc_pct
    assert got.start_fuel_l == want.start_fuel_l
    assert got.input_class == want.input_class == "SIMULATED"
    assert placed.off_grid == ()


def test_t2_the_study_on_the_read_equals_the_study_on_the_season() -> None:
    run, trajectory, placed = _season()
    f = frame(min_litre_days=8)
    got = replay_study(HostForwardReplay(), run, placed.series, f, grid=())
    want = replay_study(HostForwardReplay(), run, observed_series(trajectory, STEPS), f, grid=())
    assert got.status == want.status
    assert got.calibration == want.calibration and got.calibration is not None
