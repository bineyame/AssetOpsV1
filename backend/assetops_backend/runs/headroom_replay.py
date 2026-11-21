"""The demand-on-headroom study: what a customer's load costs a Site, read from whole-window replays (0M).

What it does (spec §2.2). A customer's load profile (kW, a local window, week days) is added to one named Site load
and the whole window is replayed through `ForwardReplayPort` beside the same window without it. Each figure is the
customer's replay minus the no-customer replay at the same capacity (D-0M.7): extra litres (in total and per local
month), extra generator energy, unserved energy, starts and running steps, and the dawn readings. From the Site's
published series alone it also reports the days on which the PV headroom (PV available minus the Site's load, at 0
when negative) could not carry the customer, and the kWh beyond it (D-0M.6). With a reduced capacity it replays a
second base run, frozen with the lower inverter limit, fed `min(PV, limit)` (D-0M.8), with and without each customer.

One rule of each (D-0M.1): the window, the sample, the start state, the calibration, starts, burns, months and dawn
are 0K2's (`runs/replay_study.py`). Nothing here applies a price, tariff, fuel law, inverter law beyond that `min`, or
dispatch rule; the arithmetic is sums, differences, the headroom `max`, the reduced `min` and one ratio.

Labels (D-0M.14). Every `DemandOutcome`, `CapacityOutcome` and `HeadroomResult` carries the series' `input_class` and
the `MODELLED` evidence class. On SIMULATED input a CALIBRATED status means only that the replay path follows the
kernel run that made the series (adapter fidelity), not that the model matches a Site. A reduced run is a
counterfactual and is not calibrated (D-0M.10). A dawn verdict is one replay's absolute verdict; the dates a customer
adds or clears against its no-customer replay are `new_dawn_days_below` and `cleared_dawn_days_below` (D-0M.22).

Refusals raise `HeadroomRefused` before any port call (§2.2 step 1); a study refusal (`StudyRefused`) or a port
refusal (`ForwardReplayRefused`) propagates unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from fractions import Fraction

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.replay_port import ForwardReplayPort
from assetops_backend.runs.replay_study import (
    DAWN_VERDICTS,
    EVIDENCE_CLASS,
    INPUT_CLASSES,
    STEP_MINUTES,
    STUDY_STATUSES,
    Calibration,
    MonthFigure,
    ObservedSeries,
    StudyDay,
    StudyFrame,
    admissible_days,
    burns,
    by_month,
    calibrate,
    checked,
    count_starts,
    dates_below,
    dawn_outcome,
    start_state,
    step_local_times,
    study_days,
)
from assetops_contracts.forward_replay import (
    CASE_ID,
    ForwardReplayProjection,
    ForwardReplayRequest,
    LoadSeries,
)

MIN_DEMAND_DAYS = 28  # design §4.3: >= 28 admissible days covering the window (D-0M.13)
INVERTER_LIMIT_KEY = "inverter-ac-limit"  # the model need the reduced run is checked on (D-0M.19)
INVERTER_LIMIT_UNIT = "kW"
CUSTOMER_EVIDENCE = frozenset({"SIGNED", "VERBAL"})  # carried, never judged here (D-0M.9)
CAPACITIES = frozenset({"FULL", "REDUCED"})
HEADROOM_REFUSALS = frozenset({"CUSTOMER_ID_INVALID", "CUSTOMER_WINDOW_INVALID", "CUSTOMER_LOAD_UNKNOWN",
                               "REDUCED_CAPACITY_INVALID"})
BASELINE = "baseline"
REDUCED = "reduced"
REDUCED_PREFIX = "reduced-"
RESERVED_CASE_IDS = frozenset({BASELINE, REDUCED})
H = Fraction(STEP_MINUTES, 60)  # hours in one step


def _exact(value: object, name: str) -> None:
    if type(value) is not Fraction:
        raise TypeError(f"{name} must be a Fraction, not {type(value).__name__}")


def _labelled(record: object) -> None:
    if record.input_class not in INPUT_CLASSES:
        raise ValueError(f"input_class {record.input_class!r} is not one of {sorted(INPUT_CLASSES)}")
    if record.evidence_class != EVIDENCE_CLASS:
        raise ValueError(f"a headroom figure is {EVIDENCE_CLASS} evidence")


@dataclass(frozen=True)
class CustomerLoad:
    customer_id: str  # it and "reduced-<id>" fullmatch CASE_ID (<= 32 chars); not reserved (D-0M.18)
    kw: Fraction  # average kW while connected
    local_start: time  # [local_start, local_end) inside one local day
    local_end: time
    weekdays: frozenset[int]  # Monday = 0 (D-0M.5)
    host_load_id: str  # the Site load the customer joins (D-0M.4)
    evidence: str  # CUSTOMER_EVIDENCE

    def __post_init__(self) -> None:
        if not isinstance(self.customer_id, str):
            raise TypeError("customer_id must be a str")
        _exact(self.kw, "kw")
        for name in ("local_start", "local_end"):
            if not isinstance(getattr(self, name), time):
                raise TypeError(f"{name} must be a datetime.time")
        if not isinstance(self.weekdays, frozenset) or not all(type(d) is int for d in self.weekdays):
            raise TypeError("weekdays must be a frozenset of int")
        if not isinstance(self.host_load_id, str):
            raise TypeError("host_load_id must be a str")
        if self.evidence not in CUSTOMER_EVIDENCE:
            raise ValueError(f"evidence {self.evidence!r} is not one of {sorted(CUSTOMER_EVIDENCE)}")


@dataclass(frozen=True)
class ReducedCapacity:
    run: SimulationRun  # the base run frozen with the reduced inverter limit
    inverter_limit_kw: Fraction  # that run's inverter-ac-limit (the Site's Foundation, as the caller reads it)

    def __post_init__(self) -> None:
        _exact(self.inverter_limit_kw, "inverter_limit_kw")


@dataclass(frozen=True)
class DemandOutcome:
    case_id: str  # customer_id at FULL, "reduced-<customer_id>" at REDUCED
    customer_id: str
    evidence: str
    capacity: str
    customer_days: tuple[str, ...]  # local dates with at least one customer step, ascending
    customer_kwh: Fraction
    customer_kwh_by_month: tuple[MonthFigure, ...]  # D-0M.15
    days_without_headroom: tuple[str, ...]
    days_without_headroom_by_month: tuple[MonthFigure, ...]
    kwh_beyond_headroom: Fraction
    kwh_beyond_headroom_by_month: tuple[MonthFigure, ...]
    extra_fuel_l: Fraction
    extra_fuel_l_by_month: tuple[MonthFigure, ...]
    extra_generator_kwh: Fraction
    extra_unserved_kwh: Fraction
    extra_starts: int
    extra_running_steps: int
    litres_per_customer_kwh: Fraction | None  # None when customer_kwh == 0
    dawn_days_below: int
    worst_dawn_soc_pct: Fraction
    dawn_verdict: str
    new_dawn_days_below: tuple[str, ...]  # below here and not in the no-customer replay (D-0M.22)
    cleared_dawn_days_below: tuple[str, ...]  # below in the no-customer replay and not here
    input_class: str  # copied from the series (D-0M.14)
    evidence_class: str = EVIDENCE_CLASS

    def __post_init__(self) -> None:
        _labelled(self)
        if self.capacity not in CAPACITIES:
            raise ValueError(f"capacity {self.capacity!r} is not one of {sorted(CAPACITIES)}")
        if self.evidence not in CUSTOMER_EVIDENCE:
            raise ValueError(f"evidence {self.evidence!r} is not one of {sorted(CUSTOMER_EVIDENCE)}")
        if self.dawn_verdict not in DAWN_VERDICTS:
            raise ValueError(f"dawn_verdict {self.dawn_verdict!r} is not one of {sorted(DAWN_VERDICTS)}")


@dataclass(frozen=True)
class CapacityOutcome:
    """The reduced limit against full capacity, no customer."""

    case_id: str  # "reduced"
    inverter_limit_kw: Fraction
    extra_fuel_l: Fraction
    extra_fuel_l_per_day: Fraction
    extra_fuel_l_by_month: tuple[MonthFigure, ...]
    extra_generator_kwh: Fraction
    extra_unserved_kwh: Fraction
    dawn_days_below: int
    worst_dawn_soc_pct: Fraction
    dawn_verdict: str
    new_dawn_days_below: tuple[str, ...]  # against the baseline
    cleared_dawn_days_below: tuple[str, ...]
    input_class: str
    evidence_class: str = EVIDENCE_CLASS

    def __post_init__(self) -> None:
        _labelled(self)
        if self.dawn_verdict not in DAWN_VERDICTS:
            raise ValueError(f"dawn_verdict {self.dawn_verdict!r} is not one of {sorted(DAWN_VERDICTS)}")


@dataclass(frozen=True)
class HeadroomResult:
    """CALIBRATED on SIMULATED input means the replay path follows the kernel run that made the series (adapter
    fidelity), not that the model matches a Site; a reader takes `status` only with `input_class` (D-0M.14)."""

    base_run_id: str
    status: str  # STUDY_STATUSES
    input_class: str
    window_start: str
    days: int
    calibration: Calibration | None  # None only when SAMPLE_TOO_SHORT
    baseline_fuel_l: Fraction | None  # set only when CALIBRATED
    demand: tuple[DemandOutcome, ...]  # customers at FULL in given order, then at REDUCED; () unless CALIBRATED
    capacity: CapacityOutcome | None  # set when CALIBRATED and `reduced` given
    projections: tuple[ForwardReplayProjection, ...]  # baseline, customers, reduced, reduced customers
    evidence_class: str = EVIDENCE_CLASS

    def __post_init__(self) -> None:
        if self.status not in STUDY_STATUSES:
            raise ValueError(f"status {self.status!r} is not one of {sorted(STUDY_STATUSES)}")
        _labelled(self)


class HeadroomRefused(Exception):
    """Nothing was replayed: a customer or the reduced capacity was judged and refused (§2.2 step 1)."""

    def __init__(self, code: str, subject: str, detail: str) -> None:
        if code not in HEADROOM_REFUSALS:
            raise ValueError(f"{code!r} is not a headroom refusal")
        super().__init__(f"{code} ({subject}): {detail}")
        self.code = code
        self.subject = subject
        self.detail = detail


# --- step 1: every judgement before any port call ------------------------------------------------------------------


def _on_step(moment: time) -> bool:
    return moment.minute % STEP_MINUTES == 0 and moment.second == 0 and moment.microsecond == 0


def _check_customers(customers: tuple[CustomerLoad, ...], observed: ObservedSeries) -> None:
    load_ids = {load.load_id for load in observed.loads}
    seen: set[str] = set()
    for customer in customers:
        cid = customer.customer_id
        if (CASE_ID.fullmatch(cid) is None or CASE_ID.fullmatch(f"{REDUCED_PREFIX}{cid}") is None
                or cid in RESERVED_CASE_IDS or cid.startswith(REDUCED_PREFIX) or cid in seen):
            raise HeadroomRefused("CUSTOMER_ID_INVALID", cid,
                                  f"{cid!r} and {REDUCED_PREFIX}{cid!r} must be new case ids of at most 40 "
                                  f"characters, neither reserved nor repeated")
        seen.add(cid)
        if customer.kw <= 0:
            raise HeadroomRefused("CUSTOMER_WINDOW_INVALID", cid, f"kw {customer.kw} is not above 0")
        if not (_on_step(customer.local_start) and _on_step(customer.local_end)):
            raise HeadroomRefused("CUSTOMER_WINDOW_INVALID", cid,
                                  f"{customer.local_start}-{customer.local_end} does not fall on step starts")
        if customer.local_end <= customer.local_start:
            raise HeadroomRefused("CUSTOMER_WINDOW_INVALID", cid,
                                  f"the window ends at {customer.local_end}, not after {customer.local_start}")
        if not customer.weekdays or not customer.weekdays <= frozenset(range(7)):
            raise HeadroomRefused("CUSTOMER_WINDOW_INVALID", cid,
                                  f"weekdays {sorted(customer.weekdays)} must be a non-empty set of 0-6")
        if customer.host_load_id not in load_ids:
            raise HeadroomRefused("CUSTOMER_LOAD_UNKNOWN", cid,
                                  f"the Site has no load {customer.host_load_id!r} ({sorted(load_ids)})")


def _limit_need(run: SimulationRun, which: str):
    rows = [need for need in run.deterministic_identity.model_needs if need.property_key == INVERTER_LIMIT_KEY]
    if len(rows) != 1:
        raise HeadroomRefused("REDUCED_CAPACITY_INVALID", REDUCED,
                              f"the {which} run has {len(rows)} {INVERTER_LIMIT_KEY} needs, not 1")
    need = rows[0]
    if need.unit != INVERTER_LIMIT_UNIT or need.value is None:
        raise HeadroomRefused("REDUCED_CAPACITY_INVALID", REDUCED,
                              f"the {which} run's {INVERTER_LIMIT_KEY} is {need.value} {need.unit}, "
                              f"not a value in {INVERTER_LIMIT_UNIT}")
    return need


def _need_key(need) -> tuple:
    return (need.state_ref, need.property_key, need.canonical_value, need.canonical_unit)


def _check_reduced(run: SimulationRun, reduced: ReducedCapacity) -> None:
    if reduced.inverter_limit_kw <= 0:
        raise HeadroomRefused("REDUCED_CAPACITY_INVALID", REDUCED,
                              f"inverter_limit_kw {reduced.inverter_limit_kw} is not above 0")
    full_need = _limit_need(run, "full")
    reduced_need = _limit_need(reduced.run, "reduced")
    reduced_kw = Fraction(str(reduced_need.value))
    full_kw = Fraction(str(full_need.value))
    if reduced_kw != reduced.inverter_limit_kw:
        raise HeadroomRefused("REDUCED_CAPACITY_INVALID", REDUCED,
                              f"the reduced run is frozen at {INVERTER_LIMIT_KEY} {reduced_kw} kW, "
                              f"not the stated {reduced.inverter_limit_kw} kW")
    if not full_kw > reduced_kw:
        raise HeadroomRefused("REDUCED_CAPACITY_INVALID", REDUCED,
                              f"the full run's {INVERTER_LIMIT_KEY} {full_kw} kW is not above {reduced_kw} kW")
    full_rest = [_need_key(n) for n in run.deterministic_identity.model_needs if n.property_key != INVERTER_LIMIT_KEY]
    reduced_rest = [_need_key(n) for n in reduced.run.deterministic_identity.model_needs
                    if n.property_key != INVERTER_LIMIT_KEY]
    for index in range(max(len(full_rest), len(reduced_rest))):
        a = full_rest[index] if index < len(full_rest) else None
        b = reduced_rest[index] if index < len(reduced_rest) else None
        if a != b:
            raise HeadroomRefused("REDUCED_CAPACITY_INVALID", REDUCED,
                                  f"model need {index} differs: full {a}, reduced {b}")
    if run.deterministic_identity.interval != reduced.run.deterministic_identity.interval:
        raise HeadroomRefused("REDUCED_CAPACITY_INVALID", REDUCED,
                              f"the intervals differ: full {run.deterministic_identity.interval}, "
                              f"reduced {reduced.run.deterministic_identity.interval}")


# --- §2.3 rules ----------------------------------------------------------------------------------------------------


def customer_steps(customer: CustomerLoad, local_times: tuple[datetime, ...]) -> tuple[Fraction, ...]:
    """`c_i`: the customer's kW at a step whose local weekday and local start time fall in its window, else 0."""
    zero = Fraction(0)
    return tuple(
        customer.kw if moment.weekday() in customer.weekdays
        and customer.local_start <= moment.time().replace(tzinfo=None) < customer.local_end else zero
        for moment in local_times
    )


def _with_customer(loads: tuple[LoadSeries, ...], host_load_id: str, c: tuple[Fraction, ...]) -> tuple[LoadSeries, ...]:
    return tuple(
        LoadSeries(load.load_id, tuple(None if kw is None else kw + ci for kw, ci in zip(load.kw, c, strict=True)))
        if load.load_id == host_load_id else load
        for load in loads
    )


def _headroom(pv: tuple[Fraction, ...], loads: tuple[LoadSeries, ...]) -> tuple[Fraction, ...]:
    """`h_i = max(0, pv_i - Σ load kw_i)` over the Site's own loads (D-0M.6)."""
    return tuple(max(Fraction(0), pv[i] - sum((load.kw[i] for load in loads), Fraction(0))) for i in range(len(pv)))


def _dawn(p: ForwardReplayProjection, q: ForwardReplayProjection, days: tuple[StudyDay, ...],
          local: tuple[datetime, ...], frame: StudyFrame):
    readings, below, worst, verdict = dawn_outcome(p, days, local, frame)
    here = set(dates_below(readings, frame))
    there = set(dates_below(dawn_outcome(q, days, local, frame)[0], frame))
    return below, worst, verdict, tuple(sorted(here - there)), tuple(sorted(there - here))


def _extra_fuel_by_month(p: ForwardReplayProjection, q: ForwardReplayProjection,
                         local: tuple[datetime, ...]) -> tuple[MonthFigure, ...]:
    return by_month(tuple(a - b for a, b in zip(burns(p), burns(q), strict=True)), local)


def _demand(customer: CustomerLoad, capacity: str, p: ForwardReplayProjection, q: ForwardReplayProjection,
            pv: tuple[Fraction, ...], observed: ObservedSeries, days: tuple[StudyDay, ...],
            local: tuple[datetime, ...], frame: StudyFrame, first_previous: str) -> DemandOutcome:
    c = customer_steps(customer, local)
    h = _headroom(pv, observed.loads)
    zero = Fraction(0)
    dates = [moment.date().isoformat() for moment in local]
    customer_days = tuple(sorted({dates[i] for i in range(len(c)) if c[i] > 0}))
    short_days = {dates[i] for i in range(len(c)) if c[i] > 0 and h[i] < c[i]}
    beyond = tuple(max(zero, c[i] - h[i]) * H if c[i] > 0 else zero for i in range(len(c)))
    first_marks = []
    marked: set[str] = set()
    for i in range(len(c)):
        if c[i] > 0 and dates[i] in short_days and dates[i] not in marked:
            marked.add(dates[i])
            first_marks.append(Fraction(1))
        else:
            first_marks.append(zero)
    customer_kwh = sum((ci * H for ci in c), zero)
    extra_fuel = p.fuel_burned_l - q.fuel_burned_l
    p_states = tuple(s.generator_state for s in p.steps)
    q_states = tuple(s.generator_state for s in q.steps)
    below, worst, verdict, new, cleared = _dawn(p, q, days, local, frame)
    return DemandOutcome(
        case_id=customer.customer_id if capacity == "FULL" else f"{REDUCED_PREFIX}{customer.customer_id}",
        customer_id=customer.customer_id, evidence=customer.evidence, capacity=capacity,
        customer_days=customer_days,
        customer_kwh=customer_kwh,
        customer_kwh_by_month=by_month(tuple(ci * H for ci in c), local),
        days_without_headroom=tuple(sorted(short_days)),
        days_without_headroom_by_month=by_month(tuple(first_marks), local),
        kwh_beyond_headroom=sum(beyond, zero),
        kwh_beyond_headroom_by_month=by_month(beyond, local),
        extra_fuel_l=extra_fuel,
        extra_fuel_l_by_month=_extra_fuel_by_month(p, q, local),
        extra_generator_kwh=p.generator_kwh - q.generator_kwh,
        extra_unserved_kwh=p.unserved_kwh - q.unserved_kwh,
        extra_starts=count_starts(p_states, first_previous) - count_starts(q_states, first_previous),
        extra_running_steps=p.running_steps - q.running_steps,
        litres_per_customer_kwh=None if customer_kwh == 0 else extra_fuel / customer_kwh,
        dawn_days_below=below, worst_dawn_soc_pct=worst, dawn_verdict=verdict,
        new_dawn_days_below=new, cleared_dawn_days_below=cleared,
        input_class=observed.input_class,
    )


def _capacity(reduced: ReducedCapacity, r: ForwardReplayProjection, baseline: ForwardReplayProjection,
              observed: ObservedSeries, days: tuple[StudyDay, ...], local: tuple[datetime, ...],
              frame: StudyFrame) -> CapacityOutcome:
    extra_fuel = r.fuel_burned_l - baseline.fuel_burned_l
    below, worst, verdict, new, cleared = _dawn(r, baseline, days, local, frame)
    return CapacityOutcome(
        case_id=REDUCED, inverter_limit_kw=reduced.inverter_limit_kw,
        extra_fuel_l=extra_fuel, extra_fuel_l_per_day=extra_fuel / len(days),
        extra_fuel_l_by_month=_extra_fuel_by_month(r, baseline, local),
        extra_generator_kwh=r.generator_kwh - baseline.generator_kwh,
        extra_unserved_kwh=r.unserved_kwh - baseline.unserved_kwh,
        dawn_days_below=below, worst_dawn_soc_pct=worst, dawn_verdict=verdict,
        new_dawn_days_below=new, cleared_dawn_days_below=cleared,
        input_class=observed.input_class,
    )


# --- §2.2 ------------------------------------------------------------------------------------------------------------


def headroom_study(port: ForwardReplayPort, run: SimulationRun, observed: ObservedSeries,
                   customers: tuple[CustomerLoad, ...], frame: StudyFrame, *,
                   reduced: ReducedCapacity | None = None, min_days: int = MIN_DEMAND_DAYS) -> HeadroomResult:
    """§2.2, in order; the first failure stops, and nothing later runs."""
    _check_customers(customers, observed)  # step 1
    if reduced is not None:
        _check_reduced(run, reduced)
    days = study_days(observed, frame)  # step 2 (0K2's window, sample and start)
    ok = admissible_days(observed, days)

    def result(status: str, **fields) -> HeadroomResult:
        values = dict(calibration=None, baseline_fuel_l=None, demand=(), capacity=None, projections=())
        values.update(fields)
        return HeadroomResult(base_run_id=run.run_id, status=status, input_class=observed.input_class,
                              window_start=observed.interval_start, days=len(days), **values)

    if len(ok) < min_days:
        return result("SAMPLE_TOO_SHORT")
    start = start_state(observed)
    pv = observed.pv_available_kw
    baseline = checked(port.forward_replay(run, ForwardReplayRequest(BASELINE, pv, observed.loads, start)),
                       observed, BASELINE)  # step 3
    calibration = calibrate(observed, baseline, ok)
    if calibration.failed:
        return result("NOT_CALIBRATED", calibration=calibration, projections=(baseline,))
    local = step_local_times(observed, frame)
    steps = {c.customer_id: customer_steps(c, local) for c in customers}

    def replay(on: SimulationRun, case_id: str, pv_series, customer: CustomerLoad | None):
        loads = observed.loads if customer is None else _with_customer(
            observed.loads, customer.host_load_id, steps[customer.customer_id])
        return checked(port.forward_replay(on, ForwardReplayRequest(case_id, pv_series, loads, start)),
                       observed, case_id)

    full = [replay(run, c.customer_id, pv, c) for c in customers]  # step 4
    projections = [baseline, *full]
    reduced_base = None
    reduced_cases: list[ForwardReplayProjection] = []
    pv_r: tuple = ()
    if reduced is not None:  # step 5 (D-0M.8)
        limit = reduced.inverter_limit_kw
        pv_r = tuple(None if value is None else min(value, limit) for value in pv)
        reduced_base = replay(reduced.run, REDUCED, pv_r, None)
        reduced_cases = [replay(reduced.run, f"{REDUCED_PREFIX}{c.customer_id}", pv_r, c) for c in customers]
        projections += [reduced_base, *reduced_cases]
    first_previous = start.generator_state  # step 6
    demand = [_demand(c, "FULL", p, baseline, pv, observed, days, local, frame, first_previous)
              for c, p in zip(customers, full, strict=True)]
    capacity = None
    if reduced is not None:
        demand += [_demand(c, "REDUCED", p, reduced_base, pv_r, observed, days, local, frame, first_previous)
                   for c, p in zip(customers, reduced_cases, strict=True)]
        capacity = _capacity(reduced, reduced_base, baseline, observed, days, local, frame)
    return result("CALIBRATED", calibration=calibration, baseline_fuel_l=baseline.fuel_burned_l,
                  demand=tuple(demand), capacity=capacity, projections=tuple(projections))


__all__ = [
    "CAPACITIES",
    "CUSTOMER_EVIDENCE",
    "HEADROOM_REFUSALS",
    "INVERTER_LIMIT_KEY",
    "MIN_DEMAND_DAYS",
    "RESERVED_CASE_IDS",
    "CapacityOutcome",
    "CustomerLoad",
    "DemandOutcome",
    "HeadroomRefused",
    "HeadroomResult",
    "ReducedCapacity",
    "customer_steps",
    "headroom_study",
]
