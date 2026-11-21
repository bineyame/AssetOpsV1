"""0K4c (D-0K4.8, D-0K4.26): Kobo's declared season v2, beside an unchanged v1.

Season v2 is declared, not climatology, and SIMULATED: never a Kobo record. Every expected value here is this test's
own literal or arithmetic (W2). The day-type files are read with this test's own `yaml.safe_load` loop, never through
`_series_events` or `day_windows`. No kernel run.
"""

from __future__ import annotations

import dataclasses
import hashlib
from datetime import date, timedelta
from fractions import Fraction as F

import pytest
import yaml

from assetops_backend.sites.site_parsing import render_site_document
from execution_adapter import frozen_world_inputs
from kobo import SCENARIOS, kobo_site
from kobo_season import (
    base_run,
    inputs_digest,
    load_multiplier_v2,
    overcast_v2,
    season_inputs,
    season_site_v2,
    windows_digest,
)

IRR, RES, CLINIC, MILL = ("site:plane-of-array-irradiance", "load-demand@load-res", "load-demand@load-clinic",
                          "load-demand@load-mill")
SERIES = (IRR, RES, CLINIC, MILL)
DAY = 1440

# --- pre-flight literals (packet §Pre-flight; main 68a4ba6c0 + inputs_digest) --------------------------------------
V1_INPUTS_DIGEST = "59d6456b88ddbe0760866971cd919944ca3ca9491b92471ea6c6f9b4c20b1c38"
V1_WINDOWS_DIGEST = "f2f0088e743eade44dc96e428b749dac42d86d3388df9645b7ce8e21971cd3de"
V2_INPUTS_DIGEST = "465ab6e0818f3fbd6d15a3fbb2a30b6ab75ad1e3cfaa250d6c3b9807f4cdb1a8"

OVERCAST_LITERAL = [2, 3, 7, 8, 9, 13, 17, 18, 19, 20, 24, 25, 28, 33, 38, 39, 45, 50, 51, 52, 57]
MULTIPLIER_LITERAL = [F(37, 40), F(11, 10), F(19, 20), F(9, 8), F(39, 40), F(23, 20), F(1), F(17, 20), F(41, 40),
                      F(7, 8), F(21, 20), F(9, 10), F(43, 40)]
SUNDAYS_LITERAL = [5, 12, 19, 26, 33, 40, 47, 54]
# 20:00-22:00 and 22:00-24:00 local: res, clinic kW (irradiance and mill 0); the test's own literal.
LATE_LITERAL = ((1200, 120, F(9), F(4)), (1320, 120, F(5), F(2)))


# --- the test's own reader of the shipped day-type files --------------------------------------------------------------

def _file_rows(name: str):
    document = yaml.safe_load((SCENARIOS / f"{name}.yaml").read_text(encoding="utf-8"))
    rows = []
    for event in document["timeline"]:
        if event["state_key"] in SERIES:
            rows.append((event["state_key"], event["offset_minutes"], event["timing"]["duration_minutes"],
                         F(str(event["parameters"][0]["value"]))))
    return rows


def _file_day(day_index: int, overcast: bool):
    """The shipped files' rows of one local day, before any v2 shaping: (address, offset, duration, kW)."""
    base = day_index * DAY
    rows = [(a, base + o, m, v) for a, o, m, v in _file_rows("kobo-night-early")]
    daytime = "kobo-daytime-overcast" if overcast else "kobo-steady-day"
    rows += [(a, base + 360 + o, m, v) for a, o, m, v in _file_rows(daytime)]
    rows += [(a, base + 1080, m, v) for a, o, m, v in _file_rows("kobo-mini-grid-evening") if o == 360]
    for start, minutes, res, clinic in LATE_LITERAL:
        rows += [(IRR, base + start, minutes, F(0)), (RES, base + start, minutes, res),
                 (CLINIC, base + start, minutes, clinic), (MILL, base + start, minutes, F(0))]
    return rows


def _season_day(inputs, day_index: int):
    lo, hi = day_index * DAY, (day_index + 1) * DAY
    return sorted((f.address, f.offset_minutes, f.duration_minutes, f.value) for f in inputs.forcings
                  if f.address in SERIES and lo <= f.offset_minutes < hi)


# --- S1 calendar ------------------------------------------------------------------------------------------------------

def test_s1_the_declared_overcast_calendar():
    days = [d for d in range(61) if overcast_v2(d)]
    assert days == OVERCAST_LITERAL
    assert len(days) == 21
    assert sum(1 for d in days if d < 30) == 13 and sum(1 for d in days if d >= 30) == 8
    spells, run = [], 0
    for d in range(62):
        if d < 61 and overcast_v2(d):
            run += 1
        elif run:
            spells.append(run)
            run = 0
    assert spells == [2, 3, 1, 4, 2, 1, 1, 2, 1, 3, 1]


# --- S2 multiplier ----------------------------------------------------------------------------------------------------

def test_s2_the_declared_load_multiplier():
    assert [load_multiplier_v2(d) for d in range(13)] == MULTIPLIER_LITERAL
    assert all(load_multiplier_v2(d) == MULTIPLIER_LITERAL[d % 13] for d in range(61))  # period 13
    values = [load_multiplier_v2(d) for d in range(61)]
    assert min(values) == F(17, 20) and max(values) == F(23, 20)


# --- S3 applied to res and clinic only --------------------------------------------------------------------------------

def _shaped(rows, *, load, mill):
    out = []
    for a, o, m, v in rows:
        if a in (RES, CLINIC):
            v = v * load
        elif a == MILL:
            v = v * mill
        out.append((a, o, m, v))
    return sorted(out)


@pytest.mark.parametrize("scale", [F(1), F(1, 2)], ids=["load_scale=1", "load_scale=1/2"])
def test_s3_the_multiplier_scales_res_and_clinic_over_the_whole_day(scale):
    inputs = season_inputs(base_run(10, version=7), 10, season="v2", load_scale=scale)
    got = _season_day(inputs, 9)
    want = _shaped(_file_day(9, overcast=True), load=scale * F(7, 8), mill=scale)  # load_multiplier_v2(9) = 7/8
    assert got == want
    nights = {(a, v) for a, o, m, v in got if o < 9 * DAY + 300 and a in (RES, CLINIC)}  # 00:00-05:00 local
    assert nights == {(RES, scale * F(21, 8)), (CLINIC, scale * F(7, 4))}
    assert any(a == MILL and v > 0 for a, o, m, v in got)  # day 9's mill rows are not all zero


# --- S4 Sundays -------------------------------------------------------------------------------------------------------

def test_s4_the_mill_is_off_on_local_sundays():
    assert date(2026, 9, 6).weekday() == 6
    sundays = [d for d in range(61) if (date(2026, 9, 1) + timedelta(days=d)).weekday() == 6]
    assert sundays == SUNDAYS_LITERAL
    inputs = season_inputs(base_run(13, version=7), 13, season="v2")
    for d in (5, 12):
        mill = [v for a, o, m, v in _season_day(inputs, d) if a == MILL]
        assert len(mill) == 13 and set(mill) == {F(0)}
    for d in (4, 6):
        mill = sorted((o, m, v) for a, o, m, v in _season_day(inputs, d) if a == MILL)
        assert mill == sorted((o, m, v) for a, o, m, v in _file_day(d, overcast=False) if a == MILL)
        assert any(v > 0 for o, m, v in mill)


# --- S5 coverage ------------------------------------------------------------------------------------------------------

def test_s5_every_series_covers_every_step_once_and_no_address_is_new():
    days = 8
    run = base_run(days, version=7)
    inputs = season_inputs(run, days, season="v2")
    steps = days * DAY // 5
    counts = {}
    for address in SERIES:
        covered = [0] * steps
        rows = [f for f in inputs.forcings if f.address == address]
        for f in rows:
            for step in range(f.offset_minutes // 5, (f.offset_minutes + f.duration_minutes) // 5):
                covered[step] += 1
        assert covered == [1] * steps, address
        counts[address] = (len(rows), sum(covered))
    assert counts == {a: (days * 13, steps) for a in SERIES}
    assert {f.address for f in inputs.forcings} == {f.address for f in frozen_world_inputs(run).forcings}


# --- S6 v1 inputs unchanged -------------------------------------------------------------------------------------------

def _own_digest(inputs) -> str:
    lines = []
    for forcing in inputs.forcings:
        lines.append("|".join(f"{field.name}={getattr(forcing, field.name)}"
                              for field in dataclasses.fields(forcing)))
    lines.sort()
    for row in inputs.initial_values:
        lines.append(f"initial|{row.address}|{row.value}|{row.canonical_unit}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def test_s6_v1_inputs_unchanged():
    inputs = season_inputs(base_run(61), 61)
    assert inputs_digest(inputs) == V1_INPUTS_DIGEST
    assert _own_digest(inputs) == V1_INPUTS_DIGEST
    assert windows_digest() == V1_WINDOWS_DIGEST


def test_s6_an_unknown_season_is_refused():
    with pytest.raises(ValueError):
        season_inputs(base_run(1), 1, season="v3")


# --- S7 Foundation (document half; the frozen half is 0K4d's V0, D-0K4.26) -------------------------------------------

def test_s7_the_v2_foundation_carries_the_assumed_equipment_with_its_basis():
    document = render_site_document(kobo_site(season_site_v2))
    components = {c["component_id"]: c for c in document["foundation"]["components"]}

    def prop(component_id, key):
        [value] = [p["value"] for p in components[component_id].get("properties") or [] if p["property_key"] == key]
        return value

    for component_id, key in (("generator", "generator-no-load-fuel-rate"), ("generator", "generator-minimum-load"),
                              ("battery", "battery-charge-taper-start")):
        assert prop(component_id, f"{key}-basis") == "GENERIC_DEFAULT"
    assert (prop("generator", "generator-no-load-fuel-rate"), prop("generator", "generator-minimum-load"),
            prop("battery", "battery-charge-taper-start")) == (3.3, 30, 95)
    assert prop("fuel-tank", "tank-capacity") == 20000
    assert components["fuel-tank"]["rating"]["value"] == 20000


# --- S9 v2 pinned as a whole ------------------------------------------------------------------------------------------

def test_s9_v2_is_pinned_as_a_whole():
    """A change here is a new season, never an edit (D-0K4.26). 0K4d's `study.json` records the same digest."""
    inputs = season_inputs(base_run(61), 61, season="v2")
    assert inputs_digest(inputs) == V2_INPUTS_DIGEST
    assert _own_digest(inputs) == V2_INPUTS_DIGEST
