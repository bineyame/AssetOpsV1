"""0M: the demand-on-headroom study on the kernel, over an 8-day declared simulated Mto season (spec §4 H1-H7).

The site is the Mto season run continuously on the kernel (`mto.py` on `kobo_season.py`); the study replays its
published series through `HostForwardReplay`. Every expected value comes from this file's own reader, which shares no
code with `runs/headroom_replay.py` or `runs/replay_study.py` (W2): customer steps by fixed offset (local = UTC + 3,
the weekday from the date), headroom from the published series by its own loop, extra litres from the projections'
`fuel_start_l` by its own loop, starts and dawn by their own loops. Each kernel run is built once; replays go through
one caching port, and a recording wrapper in front of it counts the calls each study makes.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from fractions import Fraction as F
from functools import cache

import yaml

from assetops_backend.runs.headroom_replay import MIN_DEMAND_DAYS, HeadroomRefused, ReducedCapacity, headroom_study
from assetops_simulator.kernel.execute import execute

from execution_adapter import model_for
from forward_replay import HostForwardReplay
from kobo import REPOSITORY_ROOT
from kobo_season import SEASON_START, SEASON_START_FUEL_L, SEASON_START_SOC, SEASON_TANK_L, observed_series
from mto import (
    HULLER,
    MTO_FACTS,
    MTO_FRAME,
    MTO_INVERTER_KW,
    MTO_LOAD_SCALE,
    MTO_RATINGS,
    MTO_REDUCED_INVERTER_KW,
    WELDER,
    mto_base_run,
    mto_season,
)

MANIFEST = REPOSITORY_ROOT / "Docs" / "demo-sprint" / "product-direction-layer4" / "demo-site-scenario-manifest.yaml"
DAYS = 8
DAY = 288
H = F(5, 60)
FIRST_DATE = date(2026, 9, 1)  # SEASON_START 21:00Z on 31 Aug is 00:00 local (UTC + 3)
DAWN_STEP = 60  # 05:00 local is 300 minutes after the local midnight
DAWN_LIMIT = F(35)


# --- kernel runs, each once -----------------------------------------------------------------------------------------


@cache
def full_run():
    return mto_base_run(DAYS)


@cache
def reduced_run():
    return mto_base_run(DAYS, inverter_limit_kw=F(25))


@cache
def published():
    run = full_run()
    trajectory = execute(mto_season(run, DAYS), model_for(run))
    assert trajectory.outcome == "COMPLETED", trajectory.failure
    return observed_series(trajectory, len(trajectory.boundaries) - 1)


class CachingPort:
    def __init__(self) -> None:
        self.inner = HostForwardReplay()
        self.done: dict = {}

    def forward_replay(self, run, request):
        key = (id(run), request)
        if key not in self.done:
            self.done[key] = self.inner.forward_replay(run, request)
        return self.done[key]


PORT = CachingPort()


class Recorder:
    def __init__(self, port=PORT) -> None:
        self.port = port
        self.requests = []

    def forward_replay(self, run, request):
        self.requests.append(request)
        return self.port.forward_replay(run, request)


@cache
def study():
    recorder = Recorder()
    result = headroom_study(recorder, full_run(), published(), (HULLER, WELDER), MTO_FRAME,
                            reduced=ReducedCapacity(reduced_run(), F(25)), min_days=DAYS)
    return result, recorder


# --- this file's own reader ------------------------------------------------------------------------------------------


def local_of(i: int) -> tuple[date, int]:
    """(local date, local minute of the day) of step i, by fixed offset from the local midnight start."""
    return FIRST_DATE + timedelta(days=i // DAY), (i % DAY) * 5


def reader_c(customer, n: int) -> list[F]:
    start = customer.local_start.hour * 60 + customer.local_start.minute
    end = customer.local_end.hour * 60 + customer.local_end.minute
    out = []
    for i in range(n):
        day, minute = local_of(i)
        out.append(customer.kw if day.weekday() < 5 and start <= minute < end else F(0))
    return out


def reader_months(values) -> list[tuple[str, int, F]]:
    totals: dict[str, F] = {}
    dates: dict[str, set] = {}
    for i, value in enumerate(values):
        day = local_of(i)[0]
        month = f"{day.year:04d}-{day.month:02d}"
        totals[month] = totals.get(month, F(0)) + value
        dates.setdefault(month, set()).add(day)
    return [(m, len(dates[m]), totals[m]) for m in sorted(totals)]


def as_rows(figures) -> list[tuple[str, int, F]]:
    return [(f.month, f.days, f.value) for f in figures]


def reader_burns(p) -> list[F]:
    out = []
    for i in range(len(p.steps)):
        after = p.steps[i + 1].fuel_start_l if i + 1 < len(p.steps) else p.fuel_end_l
        out.append(p.steps[i].fuel_start_l - after)
    return out


def reader_starts(p, first_previous: str) -> int:
    count, previous = 0, first_previous
    for step in p.steps:
        if step.generator_state in ("STARTING", "RUNNING") and previous == "STOPPED":
            count += 1
        previous = step.generator_state
    return count


def reader_dawn(p) -> tuple[int, F, set[str]]:
    readings = [(local_of(d * DAY)[0].isoformat(), p.steps[d * DAY + DAWN_STEP].soc_start_pct) for d in range(DAYS)]
    below = {d for d, soc in readings if soc < DAWN_LIMIT}
    return len(below), min(soc for _, soc in readings), below


def reader_demand(customer, capacity: str, p, q, pv, observed) -> dict:
    n = len(pv)
    c = reader_c(customer, n)
    loads = observed.loads
    h = []
    for i in range(n):
        total = F(0)
        for load in loads:
            total += load.kw[i]
        h.append(max(F(0), pv[i] - total))
    days, short, beyond, marks, seen = set(), set(), [], [], set()
    for i in range(n):
        day = local_of(i)[0].isoformat()
        if c[i] > 0:
            days.add(day)
            if h[i] < c[i]:
                short.add(day)
    for i in range(n):
        day = local_of(i)[0].isoformat()
        beyond.append((c[i] - h[i]) * H if c[i] > 0 and c[i] > h[i] else F(0))
        if c[i] > 0 and day in short and day not in seen:
            seen.add(day)
            marks.append(F(1))
        else:
            marks.append(F(0))
    kwh = sum((x * H for x in c), F(0))
    p_fuel = p.steps[0].fuel_start_l - p.fuel_end_l
    q_fuel = q.steps[0].fuel_start_l - q.fuel_end_l
    pb, qb = reader_burns(p), reader_burns(q)
    first = observed.generator_state[0]
    below, worst, p_below = reader_dawn(p)
    q_below = reader_dawn(q)[2]
    return {
        "case_id": customer.customer_id if capacity == "FULL" else f"reduced-{customer.customer_id}",
        "customer_id": customer.customer_id, "evidence": customer.evidence, "capacity": capacity,
        "customer_days": tuple(sorted(days)), "customer_kwh": kwh,
        "customer_kwh_by_month": reader_months([x * H for x in c]),
        "days_without_headroom": tuple(sorted(short)), "days_without_headroom_by_month": reader_months(marks),
        "kwh_beyond_headroom": sum(beyond, F(0)), "kwh_beyond_headroom_by_month": reader_months(beyond),
        "extra_fuel_l": p_fuel - q_fuel, "extra_fuel_l_by_month": reader_months([a - b for a, b in zip(pb, qb)]),
        "extra_generator_kwh": sum((s.generator_kwh for s in p.steps), F(0)) - sum((s.generator_kwh for s in q.steps),
                                                                                    F(0)),
        "extra_unserved_kwh": sum((s.unserved_kwh for s in p.steps), F(0)) - sum((s.unserved_kwh for s in q.steps),
                                                                                  F(0)),
        "extra_starts": reader_starts(p, first) - reader_starts(q, first),
        "extra_running_steps": p.running_steps - q.running_steps,
        "litres_per_customer_kwh": None if kwh == 0 else (p_fuel - q_fuel) / kwh,
        "dawn_days_below": below, "worst_dawn_soc_pct": worst, "dawn_verdict": "NOT_CLAIMED",  # 8 < 61 days
        "new_dawn_days_below": tuple(sorted(p_below - q_below)),
        "cleared_dawn_days_below": tuple(sorted(q_below - p_below)),
        "input_class": "SIMULATED", "evidence_class": "MODELLED",
    }


def got(outcome) -> dict:
    values = dict(vars(outcome))
    for key in ("customer_kwh_by_month", "days_without_headroom_by_month", "kwh_beyond_headroom_by_month",
                "extra_fuel_l_by_month"):
        values[key] = as_rows(values[key])
    return values


def projection(result, case_id: str):
    return next(p for p in result.projections if p.case_id == case_id)


def outcome(result, case_id: str):
    return next(d for d in result.demand if d.case_id == case_id)


# --- H1 calibrated ----------------------------------------------------------------------------------------------------


def test_h1_both_runs_ready_and_the_baseline_calibrated() -> None:
    for run in (full_run(), reduced_run()):
        assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
    result, recorder = study()
    assert result.status == "CALIBRATED"
    assert len(recorder.requests) == 2 + 2 * 2
    observed = published()
    baseline = projection(result, "baseline")
    n = DAYS * DAY
    cal = result.calibration
    assert len(cal.admissible_days) == DAYS
    assert cal.generator_kwh_site == sum(observed.generator_kwh, F(0))
    assert cal.generator_kwh_replayed == sum((s.generator_kwh for s in baseline.steps), F(0))
    first = observed.generator_state[0]
    site_starts, previous = 0, first
    for state in observed.generator_state:
        site_starts += state in ("STARTING", "RUNNING") and previous == "STOPPED"
        previous = state
    assert cal.starts_site == site_starts
    assert cal.starts_replayed == reader_starts(baseline, first)
    assert cal.soc_mae_points == sum((abs(baseline.steps[i].soc_start_pct - observed.soc_pct[i]) for i in range(n)),
                                     F(0)) / n
    assert cal.failed == ()
    assert result.baseline_fuel_l == baseline.steps[0].fuel_start_l - baseline.fuel_end_l


def test_h1_a_mislabelled_reduced_run_is_refused_before_any_call() -> None:
    for reduced in (ReducedCapacity(reduced_run(), F(30)), ReducedCapacity(full_run(), F(25))):
        recorder = Recorder()
        try:
            headroom_study(recorder, full_run(), published(), (HULLER, WELDER), MTO_FRAME, reduced=reduced,
                           min_days=DAYS)
        except HeadroomRefused as refused:
            assert (refused.code, refused.subject) == ("REDUCED_CAPACITY_INVALID", "reduced")
        else:
            raise AssertionError("a mislabelled reduced run was replayed")
        assert recorder.requests == []


# --- H2 huller, H3 welder ---------------------------------------------------------------------------------------------


def test_h2_the_huller_equals_the_reader() -> None:
    result, _ = study()
    observed = published()
    huller = outcome(result, "mto-huller")
    expected = reader_demand(HULLER, "FULL", projection(result, "mto-huller"), projection(result, "baseline"),
                             observed.pv_available_kw, observed)
    assert got(huller) == expected
    assert 0 < len(huller.days_without_headroom) < len(huller.customer_days)
    assert huller.extra_fuel_l != 0


def test_h3_the_welder_finds_no_headroom() -> None:
    result, _ = study()
    observed = published()
    welder = outcome(result, "mto-welder")
    assert got(welder) == reader_demand(WELDER, "FULL", projection(result, "mto-welder"),
                                        projection(result, "baseline"), observed.pv_available_kw, observed)
    assert welder.customer_kwh > 0
    assert welder.kwh_beyond_headroom == welder.customer_kwh
    assert welder.days_without_headroom == welder.customer_days
    assert welder.extra_fuel_l > 0


# --- H4 reduced -------------------------------------------------------------------------------------------------------


def test_h4_the_reduced_capacity_equals_the_reader() -> None:
    result, _ = study()
    observed = published()
    pv_r = [min(value, F(25)) for value in observed.pv_available_kw]
    r, b = projection(result, "reduced"), projection(result, "baseline")
    cap = result.capacity
    r_fuel = r.steps[0].fuel_start_l - r.fuel_end_l
    b_fuel = b.steps[0].fuel_start_l - b.fuel_end_l
    below, worst, r_below = reader_dawn(r)
    b_below = reader_dawn(b)[2]
    assert (cap.case_id, cap.inverter_limit_kw) == ("reduced", F(25))
    assert cap.extra_fuel_l == r_fuel - b_fuel
    assert cap.extra_fuel_l_per_day == (r_fuel - b_fuel) / DAYS
    assert as_rows(cap.extra_fuel_l_by_month) == reader_months([x - y for x, y in zip(reader_burns(r),
                                                                                       reader_burns(b))])
    assert cap.extra_generator_kwh == r.generator_kwh - b.generator_kwh
    assert cap.extra_unserved_kwh == r.unserved_kwh - b.unserved_kwh
    assert (cap.dawn_days_below, cap.worst_dawn_soc_pct, cap.dawn_verdict) == (below, worst, "NOT_CLAIMED")
    assert cap.new_dawn_days_below == tuple(sorted(r_below - b_below))
    assert cap.cleared_dawn_days_below == tuple(sorted(b_below - r_below))
    assert (cap.input_class, cap.evidence_class) == ("SIMULATED", "MODELLED")
    for customer in (HULLER, WELDER):
        full = outcome(result, customer.customer_id)
        low = outcome(result, f"reduced-{customer.customer_id}")
        assert got(low) == reader_demand(customer, "REDUCED", projection(result, low.case_id), r, pv_r, observed)
        assert set(full.days_without_headroom) <= set(low.days_without_headroom)
    assert outcome(result, "reduced-mto-huller").kwh_beyond_headroom > outcome(result, "mto-huller").kwh_beyond_headroom


# --- H5 the request ---------------------------------------------------------------------------------------------------


def test_h5_the_huller_request_adds_it_to_the_mill_only() -> None:
    _, recorder = study()
    observed = published()
    request = next(r for r in recorder.requests if r.case_id == "mto-huller")
    c = reader_c(HULLER, DAYS * DAY)
    sent = {load.load_id: load.kw for load in request.loads}
    base = {load.load_id: load.kw for load in observed.loads}
    assert set(sent) == set(base) == {"load-res", "load-mill", "load-clinic"}
    assert sum(1 for x in c if x) == 6 * 60  # Tue 1 - Fri 4 Sep and Mon 7 - Tue 8 Sep, 60 steps each
    for i in range(DAYS * DAY):
        assert sent["load-mill"][i] == base["load-mill"][i] + c[i], i
        assert sent["load-res"][i] == base["load-res"][i] and sent["load-clinic"][i] == base["load-clinic"][i], i
    assert request.pv_available_kw == observed.pv_available_kw


# --- H6 pins ----------------------------------------------------------------------------------------------------------


def _mto_block() -> dict:
    document = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    found = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("site") == "Mto" and "physical" in node:
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(document)
    assert len(found) == 1
    return found[0]


def test_h6_pins_against_the_manifest_and_the_calendar() -> None:
    block = _mto_block()
    physical = block["physical"]
    # manifest: `physical: {pv_kw: 50, inverters: [{id: INV-MT-01, kw: 25}, {id: INV-MT-02, kw: 25}],
    #            battery_kwh: 150, reserve_soc_pct: 30, genset_kw: 30, sfc_l_per_kwh: 0.33, ...}`
    assert MTO_FACTS == (("pv-array", "pv-rated-power", physical["pv_kw"]),
                         ("battery", "battery-energy-capacity", physical["battery_kwh"]),
                         ("battery", "reserve-state-of-charge", physical["reserve_soc_pct"]),
                         ("generator", "generator-rated-power", physical["genset_kw"]),
                         ("generator", "specific-fuel-consumption", physical["sfc_l_per_kwh"]))
    assert MTO_FACTS == (("pv-array", "pv-rated-power", 50), ("battery", "battery-energy-capacity", 150),
                         ("battery", "reserve-state-of-charge", 30), ("generator", "generator-rated-power", 30),
                         ("generator", "specific-fuel-consumption", 0.33))
    assert MTO_RATINGS == (("pv-array", 50), ("battery", 150), ("generator", 30))
    inverters = {i["id"]: F(i["kw"]) for i in physical["inverters"]}
    assert MTO_INVERTER_KW == sum(inverters.values()) == 50
    assert MTO_REDUCED_INVERTER_KW == inverters["INV-MT-01"] == 25  # INV-MT-02 failed
    options = {o["id"]: o for o in block["decision"]["options"]}
    # manifest: MTO-HULLER `load: {kw: 15, window: "10:00-15:00", days_per_month: 22, kwh_month: 1650}`
    # manifest: MTO-WELDING `load: {kw: 10, window: "18:00-21:00", days_per_month: 22, kwh_month: 660}`
    for customer, option in ((HULLER, "MTO-HULLER"), (WELDER, "MTO-WELDING")):
        load = options[option]["load"]
        window = f"{customer.local_start:%H:%M}-{customer.local_end:%H:%M}"
        assert (customer.kw, window) == (F(load["kw"]), load["window"])
        assert customer.weekdays == frozenset(range(5)) and customer.host_load_id == "load-mill"
    assert (HULLER.kw, f"{HULLER.local_start:%H:%M}-{HULLER.local_end:%H:%M}") == (15, "10:00-15:00")
    assert (WELDER.kw, f"{WELDER.local_start:%H:%M}-{WELDER.local_end:%H:%M}") == (10, "18:00-21:00")
    assert (HULLER.evidence, WELDER.evidence) == ("SIGNED", "VERBAL")
    assert MTO_LOAD_SCALE == F(1, 2)
    assert MIN_DEMAND_DAYS == 28
    assert (SEASON_TANK_L, SEASON_START_SOC, SEASON_START_FUEL_L) == (20000, 48, 15000)
    for month in (9, 10):  # a calendar pin: 22 weekdays each
        weeks = calendar.Calendar().itermonthdates(2026, month)
        assert sum(1 for d in weeks if d.month == month and d.weekday() < 5) == 22


def test_h6_the_frozen_runs_carry_mto_facts() -> None:
    needs = {}
    for label, run in (("full", full_run()), ("reduced", reduced_run())):
        needs[label] = {n.property_key: (F(str(n.value)), n.unit) for n in run.deterministic_identity.model_needs}
    for label, limit in (("full", 50), ("reduced", 25)):
        rows = needs[label]
        assert rows["inverter-ac-limit"] == (limit, "kW")
        assert rows["pv-rated-power"] == (50, "kW")
        assert rows["battery-energy-capacity"] == (150, "kWh")
        assert rows["reserve-state-of-charge"] == (30, "%")
        assert rows["generator-rated-power"] == (30, "kW")
        assert rows["specific-fuel-consumption"] == (F(33, 100), "L/kWh")
    assert published().interval_start == SEASON_START


# --- H7 sample --------------------------------------------------------------------------------------------------------


def test_h7_eight_days_is_too_short_at_the_default() -> None:
    recorder = Recorder()
    result = headroom_study(recorder, full_run(), published(), (HULLER, WELDER), MTO_FRAME,
                            reduced=ReducedCapacity(reduced_run(), F(25)))
    assert result.status == "SAMPLE_TOO_SHORT" and result.calibration is None
    assert recorder.requests == []
