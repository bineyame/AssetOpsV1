"""DIESEL-1 D0: the Kisiwa simulator trial. In memory; no database, no product code.

Kisiwa's physical assumptions, runs, cuts, lever, night window, metric, nights judged, pass mark, gates and stops are
DIESEL-1 §2 (`.agent/build-sheet-DIESEL-1.md` §2.2-§2.9, f755f085b), fixed before any run and never tuned. The Site
is the draft template `.agent/DIESEL-D0/kisiwa-diesel-hybrid-60kw.draft.yaml` built through the product's own create
path (`host/tests/fixtures.py` `site_from_template`), run on `mini-grid` v6 at 5 minutes with Lab publication profile
v3, as `tools/probe_kobo_nights.py` runs Kobo.

Nine day-runs, each 15:00 to 15:00 local (12:00Z to 12:00Z, 288 steps), from `2026-10-01T12:00:00Z`: runs 1-5 with
the generator stop setting 90 % (before), runs 6-9 with 60 % (after; a Site edit, source SITE). Run 1 starts at
100 %, 1000 L, STOPPED; every later run starts at the previous run's measured end. Night k is 18:00 to 12:00 local,
steps [36, 252) of run k. Nights 3-5 are judged against nights 6-8.

`python tools/probe_kisiwa_nights.py` prints the result JSON; `--write` writes `.agent/DIESEL-D0/probe-result.json`
and prints the verdict line; `--check` exits 1 if the committed JSON differs from a fresh run (gate G6).
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host" / "tests"))
sys.path.insert(0, str(ROOT / "host"))

import yaml  # noqa: E402

TEMPLATE = ROOT / ".agent" / "DIESEL-D0" / "kisiwa-diesel-hybrid-60kw.draft.yaml"
RESULT = ROOT / ".agent" / "DIESEL-D0" / "probe-result.json"

SOC, FUEL, GEN = "battery-state-of-charge@battery", "fuel-tank-volume@fuel-tank", "generator-state@generator"
COLD_STORE = "load-demand@load-clinic"
GENERATOR_FLOW = "generator_output"  # simulator/assetops_simulator/packs/mini_grid.py flow("generator_output", ...)
FUEL_LIMIT_NOTE = "fuel in tank"  # mini_grid.py resolve: the note a fuel-limited generator step carries (G5)

SITE_ID, TIMEZONE, FOUNDATION_VALID_FROM = "KISIWA-001", "Africa/Dar_es_Salaam", "2026-09-01T00:00:00Z"
PROFILE = {"model_profile": "mini-grid", "model_profile_version": 6, "timestep_minutes": 5,
           "publication_profile_version": 3}
RUN1_START = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)  # 15:00 local (UTC+3)
STEPS_PER_RUN = 288
NIGHT = (36, 252)  # 18:00 to 12:00 local, step indices of a 15:00-start run (DIESEL-1 §2.3, §2.4)
NIGHT_INFO_END = 180  # 06:00 local: the 18:00-06:00 figure, information only
RUNS_BEFORE, RUNS_AFTER = (1, 2, 3, 4, 5), (6, 7, 8, 9)
NIGHTS_BEFORE, NIGHTS_AFTER = (3, 4, 5), (6, 7, 8)

# DIESEL-1 §2.2, as data. Never tuned.
SFC = Fraction(355, 1000)  # L/kWh
NO_LOAD_RATE = Fraction(49, 10)  # L/h, GENERIC_DEFAULT
RESERVE = Fraction(30)  # %
CAPACITY = Fraction(60)  # kWh
PCS_LIMIT = Fraction(20)  # kW
EFFICIENCY = Fraction(95, 100)
STOP_BEFORE, STOP_AFTER = 90, 60
START_SOC, START_FUEL = 100, 1000
PRICE_USD_PER_L = Fraction(125, 100)
PASS_SHARE = Fraction(1, 5)
SOC_HEADROOM_POINTS = Fraction(10)  # B/analytics/dispatch.py:46, indicative avoidable minutes only
CAPABILITY_HEADROOM = Fraction(1, 10)  # B/analytics/dispatch.py:45

ASSUMPTIONS = {
    "source": "DIESEL-1 §2.2 (.agent/build-sheet-DIESEL-1.md, f755f085b); fixed before any run, never tuned",
    "site": {"display_name": "Kisiwa island mini-grid", "code": SITE_ID, "timezone": TIMEZONE},
    "pv_kwp": 20, "inverter_kw": 20, "battery_kwh": 60, "reserve_pct": 30, "pcs_charge_kw": 20,
    "pcs_discharge_kw": 20, "pcs_efficiency_pct": 95, "generator_kw": 60, "start_soc_pct": 35,
    "stop_soc_pct": {"before": STOP_BEFORE, "after": STOP_AFTER}, "minimum_runtime_min": 30, "start_delay_min": 5,
    "sfc_l_per_kwh": "0.355", "no_load_l_per_h": "4.9 (GENERIC_DEFAULT, 0.08145 x 60)", "tank_l": 1000,
    "start_fuel_l": START_FUEL, "diesel_price_usd_per_l": "1.25",
    "source_priority": ["pv-array", "generator", "battery"],
    "critical_load_priority": ["load-clinic", "load-res", "load-mill"],
    "loads_kw_local": {
        "load-res (Households)": {"06:00-18:00": 2, "18:00-23:00": 8, "23:00-06:00": 3},
        "load-clinic (Cold store)": {"00:00-24:00": 4},
        "load-mill (Water pump)": {"19:00-23:00": 6, "otherwise": 0}},
    "irradiance_w_m2_local": {"06:00-08:00": 150, "08:00-10:00": 550, "10:00-12:00": 900, "12:00-14:00": 950,
                              "14:00-16:00": 600, "16:00-18:00": 150, "18:00-06:00": 0},
}

# Windows of one 15:00-15:00 run, cut at 15, 16, 18, 19, 23, 06, 08, 10, 12, 14 local (DIESEL-1 §2.10):
# (offset minutes from 15:00, duration, irradiance W/m2, households kW, cold store kW, water pump kW, label)
WINDOWS = (
    (0, 60, 600, 2, 4, 0, "15:00 to 16:00"),
    (60, 120, 150, 2, 4, 0, "16:00 to 18:00"),
    (180, 60, 0, 8, 4, 0, "18:00 to 19:00"),
    (240, 240, 0, 8, 4, 6, "19:00 to 23:00"),
    (480, 420, 0, 3, 4, 0, "23:00 to 06:00"),
    (900, 120, 150, 2, 4, 0, "06:00 to 08:00"),
    (1020, 120, 550, 2, 4, 0, "08:00 to 10:00"),
    (1140, 120, 900, 2, 4, 0, "10:00 to 12:00"),
    (1260, 120, 950, 2, 4, 0, "12:00 to 14:00"),
    (1380, 60, 600, 2, 4, 0, "14:00 to 15:00"),
)

TIMINGS: list[float] = []  # seconds per 24-hour run_to_end (printed, never written: G6)


# --- the Site and the Draft ---------------------------------------------------------------------------------------


def stop_at(value: int) -> Callable[[dict[str, Any]], None]:
    """The lever as a Site edit: `stop-soc-threshold` on the generator (the `host/tests/kobo.py` `set_property`
    pattern; source becomes SITE)."""
    def edit(document: dict[str, Any]) -> None:
        from kobo import set_property

        set_property(document, "generator", "stop-soc-threshold", value)
    return edit


def kisiwa_site(site_edit: Callable[[dict[str, Any]], None] | None = None):
    from assetops_backend.sites.site_parsing import parse_site_document, render_site_document
    from fixtures import site_from_template

    site = site_from_template(TEMPLATE, site_id=SITE_ID, display_name="Kisiwa island mini-grid", timezone=TIMEZONE)
    document = copy.deepcopy(render_site_document(site))
    document["foundation"]["valid_from"] = FOUNDATION_VALID_FROM
    if site_edit is not None:
        site_edit(document)
    return parse_site_document(document, source="the Kisiwa draft site")


def kisiwa_draft(document: dict[str, Any], start: str, end: str, site_edit=None):
    """`host/tests/kobo.py` `kobo_draft`, on the Kisiwa Site: mini-grid v6, 5 min, Lab publication profile v3."""
    from assetops_backend.runs.profiles import (
        LAB_PUBLICATION_PROFILE, LAB_PUBLICATION_PROFILE_V4, LAB_PUBLICATION_PROFILE_V5, MINI_GRID_V6_MODEL)
    from assetops_backend.runs.service import RunSetupService
    from assetops_backend.scenarios.parsing import parse_scenario_document
    from fixtures import FakeRuns, FakeScenarios, FakeSites

    definition = parse_scenario_document(copy.deepcopy(document), source="a Kisiwa probe scenario", origin="SHIPPED")
    site = kisiwa_site(site_edit)
    setup = RunSetupService(
        FakeRuns(), FakeSites((site,)), FakeScenarios((definition,)), model_profiles=(MINI_GRID_V6_MODEL,),
        publication_profiles=(LAB_PUBLICATION_PROFILE, LAB_PUBLICATION_PROFILE_V4, LAB_PUBLICATION_PROFILE_V5),
        now=lambda: "2026-09-29T09:00:00Z")
    return setup.create_draft_run({
        "site_id": site.site_id, "foundation_version": site.foundation.version,
        "scenario_id": definition.scenario_id, "scenario_version": definition.version.scenario_version,
        "interval": {"start_time": start, "end_time": end}, "timestep_minutes": PROFILE["timestep_minutes"],
        "seed": 20260929,
        "model_profile": {"profile_id": MINI_GRID_V6_MODEL.model_profile_id,
                          "profile_version": MINI_GRID_V6_MODEL.model_profile_version},
        "publication_profile": {"profile_id": LAB_PUBLICATION_PROFILE.publication_profile_id,
                                "profile_version": PROFILE["publication_profile_version"]},
        "run_inputs": []})


# --- the scenario -------------------------------------------------------------------------------------------------


def _start_parameter(pid: str, name: str, value, unit: str, state_key: str) -> dict:
    return {"parameter_id": pid, "display_name": name, "value": value, "unit": unit,
            "execution_role": "CAUSAL_INPUT", "state_key": state_key, "execution_requirement": "REQUIRED",
            "ownership": {"owner": "SCENARIO_INPUT", "initializes": True}}


def _event(seq: int, event_id: str, offset: int, duration: int, category: str, state_key: str, name: str,
           value: int, unit: str, label: str) -> dict:
    return {"event_id": event_id, "sequence": seq, "offset_minutes": offset, "entry_kind": "EVENT",
            "category": category, "description": f"{name} from {label} local time.",
            "execution_role": "FORCING_INPUT", "state_key": state_key, "execution_requirement": "REQUIRED",
            "timing": {"shape": "WINDOW", "duration_minutes": duration},
            "parameters": [{"parameter_id": f"{event_id}-level", "display_name": name, "value": value, "unit": unit,
                            "execution_role": "FORCING_INPUT", "state_key": state_key,
                            "execution_requirement": "REQUIRED",
                            "ownership": {"owner": "SCENARIO_INPUT", "initializes": False}}]}


def _clock(offset: int) -> str:
    """Local HH:MM `offset` minutes after a 15:00 local run start (the day index is dropped)."""
    total = (15 * 60 + offset) % 1440
    return f"{total // 60:02d}:{total % 60:02d}"


def day_document(start_soc, start_fuel, days: int = 1) -> dict[str, Any]:
    """One 15:00-15:00 Kisiwa day (or `days` of them back to back) in memory. Event and parameter shapes copy
    `config/scenarios/kobo-s3-dispatch-necessary-run.yaml` and `config/scenarios/kobo-daytime.yaml`."""
    series = (("irradiance", "WEATHER", "site:plane-of-array-irradiance", "Plane-of-array irradiance", "W/m2", 2),
              ("households", "LOAD", "load-demand@load-res", "Households demand", "kW", 3),
              ("cold-store", "LOAD", "load-demand@load-clinic", "Cold store demand", "kW", 4),
              ("water-pump", "LOAD", "load-demand@load-mill", "Water pump demand", "kW", 5))
    timeline, seq = [], 0
    for prefix, category, state_key, name, unit, column in series:
        spans = [[day * 1440 + w[0], w[1], w[column], w[6]] for day in range(days) for w in WINDOWS]
        if days > 1:
            # G4's continuous 5-day document only: the scenario parser refuses a document over 4000 nodes, so
            # adjacent windows with the same level are joined. Every level at every minute is unchanged.
            joined = [spans[0]]
            for span in spans[1:]:
                if span[2] == joined[-1][2]:
                    joined[-1][1] += span[1]
                    joined[-1][3] = f"{_clock(joined[-1][0])} to {_clock(joined[-1][0] + joined[-1][1])}"
                else:
                    joined.append(span)
            spans = joined
        for n, (offset, duration, value, label) in enumerate(spans, start=1):
            seq += 1
            timeline.append(_event(seq, f"{prefix}-{n}", offset, duration, category, state_key, name, value, unit,
                                   label))
    return {
        "scenario_id": "kisiwa-probe-day",
        "display_name": "Kisiwa probe day (15:00 to 15:00 local, DIESEL-1 D0)",
        "purpose": "DIESEL-1 D0: one sunny Kisiwa day per run, the same every day, so before and after differ only "
                   "by the generator stop setting.",
        "version": {"scenario_version": 1, "version_valid_from": FOUNDATION_VALID_FROM},
        "site_contract": {"description": "A mini-grid created from the kisiwa-diesel-hybrid-60kw draft template, "
                                         "with Kobo's component ids."},
        "observation_sources": [],
        "public_parameters": [
            _start_parameter("starting-state-of-charge", "Battery state of charge at the start of the interval",
                             start_soc, "%", SOC),
            _start_parameter("starting-fuel", "Fuel in the tank at the start of the interval", start_fuel, "L",
                             FUEL),
            _start_parameter("starting-generator-state", "Generator state at the start of the interval", "STOPPED",
                             "state", GEN)],
        "timeline": timeline,
    }


# --- the metric (DIESEL-1 §2.5), one pure function -----------------------------------------------------------------


def _view_value(view, name: str):
    return next(entry.value for entry in view.entries if entry.name == name)


def _view_sum(view, name: str) -> Fraction:
    return sum((entry.value for entry in view.entries if entry.name == name), Fraction(0))


def measure_night(trajectory, lo: int = NIGHT[0], hi: int = NIGHT[1], info_hi: int = NIGHT_INFO_END,
                  step_minutes: int = 5) -> dict[str, Any]:
    """§2.5 over steps [lo, hi) of one run trajectory: litres per step from the generator state and the accepted
    generator energy, guardrails, and the reported fields. Exact Fractions throughout."""
    b = trajectory.boundaries
    step_h = Fraction(step_minutes, 60)
    idle_l = step_h * NO_LOAD_RATE
    loaded_l = idle = Fraction(0)
    info_l = gen_kwh = cold_unserved = all_unserved = Fraction(0)
    running = loaded = idles = starts = avoidable = 0
    below_reserve, socs = False, []
    reserves = []
    for i in range(lo, hi):
        cs = b[i].control_step
        state = dict(b[i].discrete_for_step).get(GEN)
        prev = dict(b[i - 1].discrete_for_step).get(GEN) if i > 0 else None
        energy = next(f.energy for f in cs.accepted.flows if f.flow_id == GENERATOR_FLOW)
        litres = Fraction(0)
        if state == "RUNNING":
            running += 1
            if prev != "RUNNING":
                starts += 1
            if energy > 0:
                loaded += 1
                litres = energy * SFC
                loaded_l += litres
            else:
                idles += 1
                litres = idle_l
                idle += litres
            soc, reserve = _view_value(cs.view, "state-of-charge"), _view_value(cs.view, "reserve-in-effect")
            support = min(PCS_LIMIT, (soc - reserve) / 100 * CAPACITY * EFFICIENCY / step_h)
            if soc >= reserve + SOC_HEADROOM_POINTS and _view_value(cs.view, "pv-available") + support >= (
                    1 + CAPABILITY_HEADROOM) * _view_sum(cs.view, "load-demand"):
                avoidable += 1
        if i < info_hi:
            info_l += litres
        gen_kwh += energy
        for load in cs.accepted.loads:
            all_unserved += load.unserved_energy
            if load.address == COLD_STORE:
                cold_unserved += load.unserved_energy
        reserves.append(_view_value(cs.view, "reserve-in-effect"))
    for i in range(lo, hi + 1):
        soc = dict(b[i].stocks)[SOC]
        socs.append(soc)
        if soc < reserves[min(i, hi - 1) - lo]:
            below_reserve = True
    stocks = lambda i: dict(b[i].stocks)  # noqa: E731
    night = loaded_l + idle
    return {
        "night_litres": night, "loaded_litres": loaded_l, "idle_litres": idle, "info_18_06_litres": info_l,
        "tank_drop_litres": stocks(lo)[FUEL] - stocks(hi)[FUEL], "generator_kwh": gen_kwh,
        "running_minutes": running * step_minutes, "loaded_minutes": loaded * step_minutes,
        "idle_minutes": idles * step_minutes, "starts": starts,
        "indicative_avoidable_minutes": avoidable * step_minutes,
        "cold_store_unserved_kwh": cold_unserved, "all_loads_unserved_kwh": all_unserved,
        "battery_min_pct": min(socs), "below_reserve": below_reserve, "reserve_in_effect": sorted(set(reserves)),
        "battery_at": {"start": stocks(lo)[SOC], "info_end": stocks(min(info_hi, hi))[SOC], "end": stocks(hi)[SOC]},
    }


# --- runs and gates -----------------------------------------------------------------------------------------------


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def run_once(document: dict, start: datetime, days: int, site_edit=None):
    from execution_adapter import model_for, run_to_end

    run = kisiwa_draft(document, _iso(start), _iso(start + timedelta(days=days)), site_edit)
    assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]  # G1
    began = time.perf_counter()
    trajectory = run_to_end(run, model_for(run)).trajectory
    TIMINGS.append((time.perf_counter() - began) / days)
    assert len(trajectory.boundaries) == days * STEPS_PER_RUN + 1, len(trajectory.boundaries)
    return run, trajectory


def _state(boundary) -> dict:
    stocks = dict(boundary.stocks)
    return {"soc": stocks[SOC], "fuel": stocks[FUEL], "generator": dict(boundary.discrete).get(GEN)}


def fuel_law_holds(trajectory) -> tuple[bool, int]:
    """G2: every step's accepted generator energy times the SFC equals the tank drop, exactly."""
    b, bad = trajectory.boundaries, 0
    for i in range(len(b) - 1):
        energy = next(f.energy for f in b[i].control_step.accepted.flows if f.flow_id == GENERATOR_FLOW)
        if energy * SFC != dict(b[i].stocks)[FUEL] - dict(b[i + 1].stocks)[FUEL]:
            bad += 1
    return bad == 0, bad


def fuel_limited_steps(trajectory) -> int:
    """G5: steps whose accepted controls or notes carry the resolver's fuel-in-tank limit."""
    count = 0
    for boundary in trajectory.boundaries[:-1]:
        accepted = boundary.control_step.accepted
        texts = list(accepted.notes) + [why for c in accepted.controls for why in c.limited_by]
        count += any(FUEL_LIMIT_NOTE in text for text in texts)
    return count


# --- formatting -----------------------------------------------------------------------------------------------------


def dec(value: Fraction, places: int = 3) -> str:
    with localcontext() as ctx:
        ctx.prec = 60
        exact = Decimal(value.numerator) / Decimal(value.denominator)
        return str(exact.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN))


def _litres(value: Fraction) -> dict[str, str]:
    return {"exact": str(value), "dec3": dec(value)}


def _night_json(k: int, run_start: datetime, m: dict) -> dict[str, Any]:
    local = run_start + timedelta(hours=3)
    return {
        "night": k, "phase": "before" if k in RUNS_BEFORE else "after",
        "stop_soc_pct": STOP_BEFORE if k in RUNS_BEFORE else STOP_AFTER,
        "window_local": f"{local.date()} 18:00 to {(local + timedelta(days=1)).date()} 12:00",
        "night_litres": _litres(m["night_litres"]), "loaded_litres": _litres(m["loaded_litres"]),
        "idle_litres": _litres(m["idle_litres"]), "tank_drop_litres": _litres(m["tank_drop_litres"]),
        "tank_drop_equals_loaded": m["tank_drop_litres"] == m["loaded_litres"],
        "generator_kwh": dec(m["generator_kwh"]), "running_minutes": m["running_minutes"],
        "loaded_minutes": m["loaded_minutes"], "idle_minutes": m["idle_minutes"], "starts": m["starts"],
        "battery_pct": {"18:00": dec(m["battery_at"]["start"]), "06:00": dec(m["battery_at"]["info_end"]),
                        "12:00": dec(m["battery_at"]["end"]), "minimum": dec(m["battery_min_pct"])},
        "below_reserve": m["below_reserve"], "reserve_in_effect_pct": [str(r) for r in m["reserve_in_effect"]],
        "cold_store_unserved_kwh": dec(m["cold_store_unserved_kwh"]),
        "all_loads_unserved_kwh": dec(m["all_loads_unserved_kwh"]),
        "info_only_18_06_litres": _litres(m["info_18_06_litres"]),
        "info_only_indicative_avoidable_minutes": m["indicative_avoidable_minutes"],
    }


def _reduction(before: list[Fraction], after: list[Fraction]) -> tuple[Fraction, Fraction, Fraction]:
    mean_b, mean_a = sum(before, Fraction(0)) / len(before), sum(after, Fraction(0)) / len(after)
    return mean_b, mean_a, (mean_b - mean_a) / mean_b


# --- build ----------------------------------------------------------------------------------------------------------


def build() -> dict[str, Any]:
    TIMINGS.clear()
    runs, nights, measures, chained = [], [], {}, []
    soc, fuel = START_SOC, START_FUEL
    g2_bad = g5_steps = 0
    g3 = []
    cold_all_runs = Fraction(0)
    for k in range(1, 10):
        start = RUN1_START + timedelta(days=k - 1)
        edit = stop_at(STOP_AFTER) if k in RUNS_AFTER else None
        run, trajectory = run_once(day_document(soc, fuel), start, 1, edit)
        begin, end = _state(trajectory.boundaries[0]), _state(trajectory.boundaries[-1])
        _, bad = fuel_law_holds(trajectory)
        g2_bad += bad
        g5_steps += fuel_limited_steps(trajectory)
        g3.append({"run": k, "generator_at_15_00": end["generator"]})
        cold_all_runs += sum((load.unserved_energy for bnd in trajectory.boundaries[:-1]
                              for load in bnd.control_step.accepted.loads if load.address == COLD_STORE), Fraction(0))
        m = measure_night(trajectory)
        measures[k] = m
        if k in RUNS_BEFORE:
            chained.append(trajectory)
        runs.append({"run": k, "interval": [_iso(start), _iso(start + timedelta(days=1))],
                     "stop_soc_pct": STOP_AFTER if k in RUNS_AFTER else STOP_BEFORE,
                     "scenario_sha256": run.deterministic_identity.scenario.scenario_sha256,
                     "start_parameters": {"soc": repr(soc), "fuel": repr(fuel), "generator": "STOPPED"},
                     "start": {"soc": str(begin["soc"]), "fuel": str(begin["fuel"]), "generator": begin["generator"]},
                     "end": {"soc": str(end["soc"]), "fuel": str(end["fuel"]), "generator": end["generator"]},
                     "battery_at_15_00_pct": dec(end["soc"])})
        nights.append(_night_json(k, start, m))
        # The next run starts at this run's measured end, carried as the scenario's numbers (no rounding).
        soc, fuel = float(end["soc"]), float(end["fuel"])

    # G4: chained runs 1-5 equal one continuous 5-day run at every boundary.
    _, continuous = run_once(day_document(START_SOC, START_FUEL, days=5), RUN1_START, 5)
    TIMINGS.pop()
    g4_diffs = []
    for k, trajectory in enumerate(chained):
        for j, boundary in enumerate(trajectory.boundaries):
            if _state(boundary) != _state(continuous.boundaries[k * STEPS_PER_RUN + j]):
                g4_diffs.append(f"run {k + 1} boundary {j}")
    _, g2_cont = fuel_law_holds(continuous)

    seams_exact = all(runs[k]["start"]["soc"] == runs[k - 1]["end"]["soc"]
                      and runs[k]["start"]["fuel"] == runs[k - 1]["end"]["fuel"] for k in range(1, 9))
    gates = {
        "G1": {"pass": True, "detail": "every run READY at setup and run_to_end completed (asserted)"},
        "G2": {"pass": g2_bad == 0 and g2_cont == 0, "steps_failing": g2_bad + g2_cont,
               "detail": "accepted generator energy x 0.355 equals the tank drop at every step, exactly"},
        "G3": {"pass": all(item["generator_at_15_00"] == "STOPPED" for item in g3), "runs": g3},
        "G4": {"pass": not g4_diffs and seams_exact, "boundaries_differing": g4_diffs[:20],
               "seams_carry_exact": seams_exact,
               "detail": "chained runs 1-5 against one continuous run 2026-10-01T12:00Z to 2026-10-06T12:00Z "
                         "(stop 90): battery, fuel and generator state at every boundary, exactly"},
        "G5": {"pass": g5_steps == 0, "fuel_limited_steps": g5_steps},
        "G6": {"pass": None, "detail": "checked by --check: a fresh run is byte-equal to the committed file"},
    }

    lb = [measures[k]["night_litres"] for k in NIGHTS_BEFORE]
    la = [measures[k]["night_litres"] for k in NIGHTS_AFTER]
    mean_b, mean_a, share = _reduction(lb, la)
    _, _, share_all = _reduction([measures[k]["night_litres"] for k in RUNS_BEFORE],
                                 [measures[k]["night_litres"] for k in RUNS_AFTER])
    ib = [measures[k]["info_18_06_litres"] for k in NIGHTS_BEFORE]
    ia = [measures[k]["info_18_06_litres"] for k in NIGHTS_AFTER]
    info_b, info_a, info_share = _reduction(ib, ia) if sum(ib) else (Fraction(0), Fraction(0), Fraction(0))
    judged = NIGHTS_BEFORE + NIGHTS_AFTER
    cold_ok = all(measures[k]["cold_store_unserved_kwh"] == 0 for k in judged)
    battery_ok = not any(measures[k]["below_reserve"] for k in judged)
    diesel_ok = share >= PASS_SHARE
    result = "FAIL" if not (cold_ok and battery_ok) else ("PASS" if diesel_ok else "NOT MET")
    fragile = result == "PASS" and share_all < PASS_SHARE
    no_evidence = all(measures[k]["indicative_avoidable_minutes"] == 0 for k in NIGHTS_BEFORE)

    return {
        "schema": {"id": "assetops.kisiwa-night-probe", "version": 1},
        "ruling": "DIESEL-1 §2 (.agent/build-sheet-DIESEL-1.md, f755f085b)",
        "assumptions": {**ASSUMPTIONS, "template": str(TEMPLATE.relative_to(ROOT)).replace("\\", "/"),
                        "template_sha256_lf": hashlib.sha256(
                            TEMPLATE.read_text(encoding="utf-8").encode("utf-8")).hexdigest()},
        "profile": {**PROFILE, "run_length": "15:00 to 15:00 local, 288 steps",
                    "night": "18:00 to 12:00 local, steps [36, 252)",
                    "info_only_night": "18:00 to 06:00 local, steps [36, 180)"},
        "runs": runs,
        "nights": nights,
        "cold_store_unserved_kwh_all_steps_all_runs": dec(cold_all_runs),
        "gates": gates,
        "verdict": {
            "nights_before": list(NIGHTS_BEFORE), "nights_after": list(NIGHTS_AFTER),
            "mean_before": _litres(mean_b), "mean_after": _litres(mean_a),
            "reduction": str(share), "reduction_pct": dec(share * 100, 1),
            "pass_mark": "at least 20 % less diesel per night (owner 2026-11-07)",
            "guardrails": {"cold_store_unserved_zero_nights_3_8": cold_ok,
                           "battery_never_below_reserve_nights_3_8": battery_ok},
            "result": result, "fragile": fragile,
            "all_nights_reduction_pct": dec(share_all * 100, 1),
            "info_only_18_06": {"mean_before": _litres(info_b), "mean_after": _litres(info_a),
                                "reduction_pct": dec(info_share * 100, 1)},
            "s7_no_avoidable_minutes_nights_3_5": no_evidence,
        },
        "money_info": {"usd_per_night": dec((mean_b - mean_a) * PRICE_USD_PER_L, 2),
                       "basis": "(mean_before - mean_after) x 1.25 USD/L; modelled from a generic fuel curve, not "
                                "measured by a fuel meter; information only, never a target; not annualised"},
    }


def verdict_line(result: dict) -> str:
    v = result["verdict"]
    return (f"{v['result']}{' (FRAGILE)' if v['fragile'] else ''}: {dec(Fraction(v['mean_before']['exact']), 1)} L -> "
            f"{dec(Fraction(v['mean_after']['exact']), 1)} L per night (6 pm to noon), {v['reduction_pct']} % less; "
            f"gates {'all pass' if all(g['pass'] is not False for g in result['gates'].values()) else 'FAILING'}")


def main(argv: list[str]) -> int:
    result = build()
    text = json.dumps(result, indent=1) + "\n"
    gates_ok = all(g["pass"] is not False for g in result["gates"].values())
    if "--check" in argv:
        same = RESULT.exists() and RESULT.read_text(encoding="utf-8") == text
        print("probe result current (G6 pass)" if same else "probe result stale (G6 FAIL)")
        return 0 if same else 1
    if "--write" in argv:
        RESULT.write_text(text, encoding="utf-8", newline="\n")
        print(verdict_line(result))
        print("seconds per 24-hour run (in memory): " + ", ".join(f"{t:.2f}" for t in TIMINGS), file=sys.stderr)
        return 0 if gates_ok else 2
    print(text)
    return 0 if gates_ok else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
