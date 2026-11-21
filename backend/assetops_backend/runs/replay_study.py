"""The replay study: a Site's 5-minute series replayed through `ForwardReplayPort` at the baseline and on a grid (0K2).

What it does (spec §2.2). From the Site's published 5-minute series and a frozen base run it replays the whole window
once at the baseline (no setting), checks the calibration rule on the admissible days, then replays the whole window
once per grid setting and reports, per setting, the litres avoided (in total and per local month), the dawn readings,
starts, running steps, battery throughput, lowest charge and unserved energy. Every figure is read from whole-window
replays and nothing else: no setting, dispatch rule, fuel law, price or gap fill lives here. Settings reach the kernel
only through `ReplaySettings` (D-0K1.2); the only arithmetic is sums, differences, the tolerance comparisons, the SOC
drop for throughput and local-time framing.

Labels (D-0K2.20). `ObservedSeries` is the seam's role, the Site's published series; what the series is (recorded,
emulated or simulated) travels in its `input_class`, and every `Calibration`, `CaseOutcome` and `StudyResult` carries
that class and the `MODELLED` evidence class. On SIMULATED input a CALIBRATED status means only that the replay path
follows the kernel run that made the series (adapter fidelity), not that the model matches a Site; a reader takes
`status` only together with `input_class`.

Dawn (D-0K2.8, D-0K2.17). The bound is applied as given by the frame, to every case, the baseline included; no reading
is excluded and the limit is never moved. A verdict is one case's absolute verdict; `new_dawn_days_below` and
`cleared_dawn_days_below` give the dates a case adds or clears against no action. Admissibility is the evaluator's.

Refusals raise `StudyRefused` before any later port call; a port refusal (`ForwardReplayRefused`) propagates
unchanged. Local days are whole days of 288 steps in a zone without a clock change (D-0K2.7).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from fractions import Fraction
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.replay_port import ForwardReplayPort
from assetops_contracts.forward_replay import (
    CASE_ID,
    ForwardReplayProjection,
    ForwardReplayRequest,
    LoadSeries,
    ReplaySettings,
    ReplayStartState,
)

STEP_MINUTES = 5
STEPS_PER_DAY = 288
CALIBRATION_KWH = Fraction(5, 100)  # |replayed - site| <= 5% of the site's generator kWh
CALIBRATION_STARTS = Fraction(10, 100)  # |replayed - site| <= 10% of the site's starts
CALIBRATION_SOC_MAE = Fraction(5)  # mean absolute SOC error <= 5 points
MIN_LITRE_DAYS = 14  # admissible days for any litre figure (design §4.2)
MIN_DAWN_DAYS = 61  # replayed local days for a dawn verdict (rule of three, design §4.2)
STOP_GRID = tuple(Fraction(s) for s in (90, 85, 80, 75, 70, 65, 60))
RESERVE_GRID = (Fraction(30), Fraction(25))
KOBO_GRID = tuple(ReplaySettings(stop_soc_pct=s, reserve_soc_pct=r) for s in STOP_GRID for r in RESERVE_GRID)
INPUT_CLASSES = frozenset({"RECORDED", "EMULATED", "SIMULATED"})
STUDY_STATUSES = frozenset({"CALIBRATED", "NOT_CALIBRATED", "SAMPLE_TOO_SHORT"})
STUDY_REFUSALS = frozenset({"STUDY_WINDOW_INVALID", "STUDY_SERIES_MISALIGNED", "STUDY_START_UNKNOWN",
                            "STUDY_GRID_INVALID", "REPLAY_FAILED", "TANK_BOUND_MET"})
EVIDENCE_CLASS = "MODELLED"
DAWN_VERDICTS = frozenset({"PASS", "FAIL", "NOT_CLAIMED"})
RUNNING_STATES = frozenset({"STARTING", "RUNNING"})
CALIBRATION_MEASURES = ("generator_kwh", "starts", "soc")
BASELINE = "baseline"
_INSTANT = "%Y-%m-%dT%H:%M:%SZ"


def _exact(value: object, name: str) -> None:
    if type(value) is not Fraction:
        raise TypeError(f"{name} must be a Fraction, not {type(value).__name__}")


def _series(values: object, name: str) -> None:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple, not {type(values).__name__}")
    for index, value in enumerate(values):
        if value is not None:
            _exact(value, f"{name}[{index}]")


def _whole(value: object, name: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be an int, not {type(value).__name__}")


def _labels(record: object) -> None:
    if record.input_class not in INPUT_CLASSES:
        raise ValueError(f"input_class {record.input_class!r} is not one of {sorted(INPUT_CLASSES)}")
    if record.evidence_class != EVIDENCE_CLASS:
        raise ValueError(f"a study figure is {EVIDENCE_CLASS} evidence")


@dataclass(frozen=True)
class ObservedSeries:
    """The seam's role: the Site's published 5-minute series, step-aligned. What it is (recorded, emulated or
    simulated) travels in `input_class` (D-0K2.20); the name never says the series was recorded."""

    interval_start: str  # "YYYY-MM-DDTHH:MM:SSZ"; a local midnight of the frame's zone
    timestep_minutes: int
    pv_available_kw: tuple[Fraction | None, ...]  # average PV-available kW per step (after the inverter limit)
    loads: tuple[LoadSeries, ...]  # 0K1's LoadSeries, by component id
    generator_kwh: tuple[Fraction | None, ...]  # the Site's generator energy in each step
    generator_state: tuple[str | None, ...]  # the Site's generator state for each step
    soc_pct: tuple[Fraction | None, ...]  # the Site's SOC at each step's start
    start_fuel_l: Fraction  # the tank at the window start
    input_class: str  # INPUT_CLASSES

    def __post_init__(self) -> None:
        if not isinstance(self.interval_start, str):
            raise TypeError("interval_start must be a str")
        _whole(self.timestep_minutes, "timestep_minutes")
        _series(self.pv_available_kw, "pv_available_kw")
        if not isinstance(self.loads, tuple) or not all(isinstance(x, LoadSeries) for x in self.loads):
            raise TypeError("loads must be a tuple of LoadSeries")
        _series(self.generator_kwh, "generator_kwh")
        if not isinstance(self.generator_state, tuple) or not all(
                s is None or isinstance(s, str) for s in self.generator_state):
            raise TypeError("generator_state must be a tuple of str or None")
        _series(self.soc_pct, "soc_pct")
        _exact(self.start_fuel_l, "start_fuel_l")
        if self.input_class not in INPUT_CLASSES:
            raise ValueError(f"input_class {self.input_class!r} is not one of {sorted(INPUT_CLASSES)}")


@dataclass(frozen=True)
class StudyFrame:
    timezone: str  # the Site's IANA zone, e.g. "Africa/Addis_Ababa"
    battery_capacity_kwh: Fraction  # the Site's declared battery energy capacity (throughput only)
    dawn_local: time = time(5, 0)  # MG5: battery at or above the limit at 05:00 local
    dawn_min_soc_pct: Fraction = Fraction(35)
    min_litre_days: int = MIN_LITRE_DAYS
    min_dawn_days: int = MIN_DAWN_DAYS

    def __post_init__(self) -> None:
        if not isinstance(self.timezone, str):
            raise TypeError("timezone must be a str")
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError) as unknown:
            raise ValueError(f"timezone {self.timezone!r} is not a known zone") from unknown
        _exact(self.battery_capacity_kwh, "battery_capacity_kwh")
        if not isinstance(self.dawn_local, time):
            raise TypeError("dawn_local must be a datetime.time")
        if self.dawn_local.minute % STEP_MINUTES or self.dawn_local.second or self.dawn_local.microsecond:
            raise ValueError("dawn_local must fall on a step start (a multiple of 5 minutes, no seconds)")
        _exact(self.dawn_min_soc_pct, "dawn_min_soc_pct")
        _whole(self.min_litre_days, "min_litre_days")
        _whole(self.min_dawn_days, "min_dawn_days")
        if self.min_litre_days < 1:
            raise ValueError("min_litre_days must be at least 1")


@dataclass(frozen=True)
class Calibration:
    admissible_days: tuple[str, ...]  # local dates "YYYY-MM-DD", ascending
    generator_kwh_site: Fraction
    generator_kwh_replayed: Fraction
    starts_site: int
    starts_replayed: int
    soc_mae_points: Fraction
    failed: tuple[str, ...]  # subset of CALIBRATION_MEASURES, in that order; () when calibrated
    input_class: str  # copied from the series
    evidence_class: str = EVIDENCE_CLASS

    def __post_init__(self) -> None:
        _labels(self)
        if tuple(m for m in CALIBRATION_MEASURES if m in self.failed) != self.failed:
            raise ValueError(f"failed lists measures of {CALIBRATION_MEASURES} in that order")


@dataclass(frozen=True)
class MonthFigure:
    month: str  # local month "YYYY-MM"
    days: int  # local days of that month in the window
    value: Fraction


@dataclass(frozen=True)
class DawnReading:
    local_date: str
    soc_pct: Fraction
    generator_state: str  # the projection's state at the dawn step (D-0K2.17)


@dataclass(frozen=True)
class CaseOutcome:
    case_id: str  # "baseline" or "stop-<s>-reserve-<r>"
    stop_soc_pct: Fraction
    stop_source: str
    reserve_soc_pct: Fraction
    reserve_source: str
    fuel_l: Fraction  # the projection's fuel_burned_l
    avoided_l: Fraction  # baseline fuel_l - this fuel_l (0 for the baseline)
    avoided_l_by_month: tuple[MonthFigure, ...]
    generator_kwh: Fraction
    running_steps: int
    starts: int
    unserved_kwh: Fraction
    added_starts: int
    added_running_steps: int
    added_throughput_kwh: Fraction
    added_starts_by_month: tuple[MonthFigure, ...]
    added_throughput_kwh_by_month: tuple[MonthFigure, ...]
    throughput_kwh: Fraction
    min_soc_pct: Fraction
    dawn: tuple[DawnReading, ...]
    dawn_days_below: int
    worst_dawn_soc_pct: Fraction
    dawn_verdict: str
    new_dawn_days_below: tuple[str, ...]  # local dates below the limit here and not in the baseline
    cleared_dawn_days_below: tuple[str, ...]  # below in the baseline and not here; both () for the baseline
    clipped_steps: int
    input_class: str  # copied from the series
    evidence_class: str = EVIDENCE_CLASS

    def __post_init__(self) -> None:
        _labels(self)
        if self.dawn_verdict not in DAWN_VERDICTS:
            raise ValueError(f"dawn_verdict {self.dawn_verdict!r} is not one of {sorted(DAWN_VERDICTS)}")


@dataclass(frozen=True)
class StudyResult:
    """CALIBRATED on SIMULATED input means the replay path follows the kernel run that made the series (adapter
    fidelity), not that the model matches a Site; a reader takes `status` only with `input_class` (D-0K2.20)."""

    base_run_id: str
    status: str
    input_class: str
    window_start: str
    days: int
    clipped_days: tuple[str, ...]
    calibration: Calibration | None  # None only when SAMPLE_TOO_SHORT
    baseline: CaseOutcome | None  # set only when CALIBRATED
    cases: tuple[CaseOutcome, ...]  # grid order; () unless CALIBRATED
    projections: tuple[ForwardReplayProjection, ...]  # baseline first, then the grid; (baseline,) when NOT_CALIBRATED
    evidence_class: str = EVIDENCE_CLASS

    def __post_init__(self) -> None:
        if self.status not in STUDY_STATUSES:
            raise ValueError(f"status {self.status!r} is not one of {sorted(STUDY_STATUSES)}")
        _labels(self)


class StudyRefused(Exception):
    """Nothing further ran: the series, the window, the grid or a projection was judged and refused."""

    def __init__(self, code: str, subject: str, detail: str) -> None:
        if code not in STUDY_REFUSALS:
            raise ValueError(f"{code!r} is not a study refusal")
        super().__init__(f"{code} ({subject}): {detail}")
        self.code = code
        self.subject = subject
        self.detail = detail


@dataclass(frozen=True)
class StudyDay:
    local_date: str
    first: int  # steps [first, end) of one local day
    end: int


# --- the steps, public so 0M reuses one rule of each (D-0K2.16) --------------------------------------------------


def _start_instant(observed: ObservedSeries) -> datetime:
    try:
        start = datetime.strptime(observed.interval_start, _INSTANT).replace(tzinfo=timezone.utc)
    except ValueError as malformed:
        raise StudyRefused("STUDY_WINDOW_INVALID", "start",
                           f"{observed.interval_start!r} is not a UTC instant {_INSTANT}") from malformed
    if start.strftime(_INSTANT) != observed.interval_start:
        raise StudyRefused("STUDY_WINDOW_INVALID", "start", f"{observed.interval_start!r} is not in {_INSTANT}")
    return start


def step_local_times(observed: ObservedSeries, frame: StudyFrame) -> tuple[datetime, ...]:
    """The local start of every step, aware, in the frame's zone."""
    start = _start_instant(observed)
    zone = ZoneInfo(frame.timezone)
    step = timedelta(minutes=STEP_MINUTES)
    return tuple((start + i * step).astimezone(zone) for i in range(len(observed.pv_available_kw)))


def study_days(observed: ObservedSeries, frame: StudyFrame) -> tuple[StudyDay, ...]:
    """§2.2 steps 1 and 2: the window's whole local days, or a refusal."""
    if observed.timestep_minutes != STEP_MINUTES:
        raise StudyRefused("STUDY_WINDOW_INVALID", "timestep",
                           f"a study steps at {STEP_MINUTES} minutes, not {observed.timestep_minutes}")
    start = _start_instant(observed)
    local_start = start.astimezone(ZoneInfo(frame.timezone))
    if local_start.time() != time(0, 0):
        raise StudyRefused("STUDY_WINDOW_INVALID", "start", f"{observed.interval_start} is not a local midnight")
    local = step_local_times(observed, frame)
    if not local:
        raise StudyRefused("STUDY_WINDOW_INVALID", f"day:{local_start.date().isoformat()}", "the window is empty")
    days: list[StudyDay] = []
    first = 0
    for i in range(1, len(local) + 1):
        if i == len(local) or local[i].date() != local[first].date():
            days.append(StudyDay(local[first].date().isoformat(), first, i))
            first = i
    for day in days:
        if day.end - day.first != STEPS_PER_DAY:
            raise StudyRefused("STUDY_WINDOW_INVALID", f"day:{day.local_date}",
                               f"{day.end - day.first} steps on a local day of {STEPS_PER_DAY}")
    n = len(observed.pv_available_kw)
    for name, values in (("generator_kwh", observed.generator_kwh), ("generator_state", observed.generator_state),
                         ("soc_pct", observed.soc_pct)):
        if len(values) != n:
            raise StudyRefused("STUDY_SERIES_MISALIGNED", name, f"{len(values)} values for {n} steps")
    for load in sorted(observed.loads, key=lambda item: item.load_id):
        if len(load.kw) != n:
            raise StudyRefused("STUDY_SERIES_MISALIGNED", f"load:{load.load_id}", f"{len(load.kw)} values for {n} steps")
    return tuple(days)


def admissible_days(observed: ObservedSeries, days: tuple[StudyDay, ...]) -> tuple[StudyDay, ...]:
    """§2.2 step 3: the days every step of which has the Site's generator energy, state and SOC (D-0K2.5)."""
    return tuple(
        day for day in days
        if all(observed.generator_kwh[i] is not None and observed.generator_state[i] is not None
               and observed.soc_pct[i] is not None for i in range(day.first, day.end))
    )


def start_state(observed: ObservedSeries) -> ReplayStartState:
    """§2.2 step 4: the run-start state, from the series' first step."""
    if observed.soc_pct[0] is None:
        raise StudyRefused("STUDY_START_UNKNOWN", "soc", "the series has no SOC at its first step")
    if observed.generator_state[0] is None:
        raise StudyRefused("STUDY_START_UNKNOWN", "generator", "the series has no generator state at its first step")
    return ReplayStartState(observed.soc_pct[0], observed.start_fuel_l, observed.generator_state[0])


def _id_part(value: Fraction | None, j: int) -> str:
    if value is None:
        return "site"
    if value.denominator != 1:
        raise StudyRefused("STUDY_GRID_INVALID", f"grid:{j}", f"{value} is not a whole percentage")
    return str(value.numerator)


def _case_ids(grid: tuple[ReplaySettings, ...]) -> tuple[str, ...]:
    """§2.2 step 4a (D-0K2.29): every case id, fixed before the first port call."""
    ids: list[str] = []
    for j, setting in enumerate(grid):
        case_id = f"stop-{_id_part(setting.stop_soc_pct, j)}-reserve-{_id_part(setting.reserve_soc_pct, j)}"
        if CASE_ID.fullmatch(case_id) is None or case_id in ids or case_id == BASELINE:
            raise StudyRefused("STUDY_GRID_INVALID", f"grid:{j}", f"case id {case_id!r} is not a new, valid id")
        ids.append(case_id)
    return tuple(ids)


def checked(projection: ForwardReplayProjection, observed: ObservedSeries, case_id: str) -> ForwardReplayProjection:
    """Step 5's three checks in order: REPLAY_FAILED, STUDY_WINDOW_INVALID "run", TANK_BOUND_MET (D-0K2.25)."""
    if projection.status == "FAILED":
        raise StudyRefused("REPLAY_FAILED", case_id,
                           f"the kernel failed: {projection.failure_kind} ({projection.failure_subject})")
    n = len(observed.pv_available_kw)
    if (projection.interval_start != observed.interval_start or projection.timestep_minutes != STEP_MINUTES
            or len(projection.steps) != n):
        raise StudyRefused("STUDY_WINDOW_INVALID", "run",
                           f"the projection covers {projection.interval_start}, {projection.timestep_minutes} "
                           f"minutes, {len(projection.steps)} steps; the series {observed.interval_start}, {n} steps")
    if any(step.fuel_start_l == 0 for step in projection.steps) or projection.fuel_end_l == 0:
        raise StudyRefused("TANK_BOUND_MET", case_id, "the tank empties; the litre difference is no longer the case's")
    return projection


def start_steps(states: tuple[str | None, ...], first_previous: str | None) -> tuple[int, ...]:
    """1 at a step in STARTING or RUNNING whose previous state is STOPPED, else 0 (§2.3)."""
    marks = []
    previous = first_previous
    for state in states:
        marks.append(1 if state in RUNNING_STATES and previous == "STOPPED" else 0)
        previous = state
    return tuple(marks)


def count_starts(states: tuple[str | None, ...], first_previous: str | None,
                 indices: frozenset[int] | None = None) -> int:
    marks = start_steps(states, first_previous)
    if indices is None:
        return sum(marks)
    return sum(marks[i] for i in indices)


def calibrate(observed: ObservedSeries, baseline: ForwardReplayProjection,
              admissible: tuple[StudyDay, ...]) -> Calibration:
    """§2.3, exact, on the admissible steps."""
    steps = [i for day in admissible for i in range(day.first, day.end)]
    replayed = baseline.steps
    site_kwh = sum((observed.generator_kwh[i] for i in steps), Fraction(0))
    replayed_kwh = sum((replayed[i].generator_kwh for i in steps), Fraction(0))
    first_previous = observed.generator_state[0] if observed.generator_state else None
    indices = frozenset(steps)
    site_starts = count_starts(observed.generator_state, first_previous, indices)
    replayed_starts = count_starts(tuple(s.generator_state for s in replayed), first_previous, indices)
    mae = (sum((abs(replayed[i].soc_start_pct - observed.soc_pct[i]) for i in steps), Fraction(0)) / len(steps)
           if steps else Fraction(0))
    failed = []
    if abs(replayed_kwh - site_kwh) > CALIBRATION_KWH * site_kwh:
        failed.append("generator_kwh")
    if abs(replayed_starts - site_starts) > CALIBRATION_STARTS * site_starts:
        failed.append("starts")
    if mae > CALIBRATION_SOC_MAE:
        failed.append("soc")
    return Calibration(
        admissible_days=tuple(day.local_date for day in admissible),
        generator_kwh_site=site_kwh, generator_kwh_replayed=replayed_kwh,
        starts_site=site_starts, starts_replayed=replayed_starts,
        soc_mae_points=mae, failed=tuple(failed), input_class=observed.input_class,
    )


def burns(projection: ForwardReplayProjection) -> tuple[Fraction, ...]:
    """Litres from the tank in each step: this step's start stock less the next one's (the end stock last)."""
    stocks = [s.fuel_start_l for s in projection.steps] + [projection.fuel_end_l]
    return tuple(stocks[i] - stocks[i + 1] for i in range(len(projection.steps)))


def throughput_steps(projection: ForwardReplayProjection, frame: StudyFrame) -> tuple[Fraction, ...]:
    """Battery discharge in each step at the stock, kWh: the SOC drop times the capacity (D-0K2.11)."""
    socs = [s.soc_start_pct for s in projection.steps] + [projection.soc_end_pct]
    return tuple(max(Fraction(0), socs[i] - socs[i + 1]) * frame.battery_capacity_kwh / 100
                 for i in range(len(projection.steps)))


def by_month(values: tuple[Fraction, ...], local_times: tuple[datetime, ...]) -> tuple[MonthFigure, ...]:
    """One figure per local month any step falls in, ascending; `days` is that month's local dates in the window."""
    totals: dict[str, Fraction] = {}
    dates: dict[str, set] = {}
    for value, moment in zip(values, local_times, strict=True):
        month = moment.strftime("%Y-%m")
        totals[month] = totals.get(month, Fraction(0)) + value
        dates.setdefault(month, set()).add(moment.date())
    return tuple(MonthFigure(month, len(dates[month]), totals[month]) for month in sorted(totals))


def dawn_outcome(projection: ForwardReplayProjection, days: tuple[StudyDay, ...], local_times: tuple[datetime, ...],
                 frame: StudyFrame) -> tuple[tuple[DawnReading, ...], int, Fraction, str]:
    """(readings, days below, worst, verdict): the step starting at the frame's dawn, every local day (§2.4)."""
    readings = []
    for day in days:
        for i in range(day.first, day.end):
            if local_times[i].time() == frame.dawn_local:
                step = projection.steps[i]
                readings.append(DawnReading(day.local_date, step.soc_start_pct, step.generator_state))
                break
    below = len(dates_below(tuple(readings), frame))
    worst = min(r.soc_pct for r in readings)
    if len(days) < frame.min_dawn_days:
        verdict = "NOT_CLAIMED"
    else:
        verdict = "FAIL" if below > 0 else "PASS"
    return tuple(readings), below, worst, verdict


def dates_below(readings: tuple[DawnReading, ...], frame: StudyFrame) -> tuple[str, ...]:
    return tuple(sorted(r.local_date for r in readings if r.soc_pct < frame.dawn_min_soc_pct))


def _differences(case: tuple, base: tuple) -> tuple[Fraction, ...]:
    return tuple(Fraction(c) - Fraction(b) for c, b in zip(case, base, strict=True))


def _outcome(case_id: str, p: ForwardReplayProjection, b: ForwardReplayProjection, observed: ObservedSeries,
             days: tuple[StudyDay, ...], local: tuple[datetime, ...], frame: StudyFrame,
             first_previous: str) -> CaseOutcome:
    p_states = tuple(s.generator_state for s in p.steps)
    b_states = tuple(s.generator_state for s in b.steps)
    p_marks, b_marks = start_steps(p_states, first_previous), start_steps(b_states, first_previous)
    p_through, b_through = throughput_steps(p, frame), throughput_steps(b, frame)
    readings, below, worst, verdict = dawn_outcome(p, days, local, frame)
    base_readings = dawn_outcome(b, days, local, frame)[0]
    here, there = set(dates_below(readings, frame)), set(dates_below(base_readings, frame))
    throughput = sum(p_through, Fraction(0))
    return CaseOutcome(
        case_id=case_id,
        stop_soc_pct=p.stop_soc_pct, stop_source=p.stop_source,
        reserve_soc_pct=p.reserve_soc_pct, reserve_source=p.reserve_source,
        fuel_l=p.fuel_burned_l,
        avoided_l=b.fuel_burned_l - p.fuel_burned_l,
        avoided_l_by_month=by_month(_differences(burns(b), burns(p)), local),
        generator_kwh=p.generator_kwh, running_steps=p.running_steps, starts=sum(p_marks),
        unserved_kwh=p.unserved_kwh,
        added_starts=sum(p_marks) - sum(b_marks),
        added_running_steps=p.running_steps - b.running_steps,
        added_throughput_kwh=throughput - sum(b_through, Fraction(0)),
        added_starts_by_month=by_month(_differences(p_marks, b_marks), local),
        added_throughput_kwh_by_month=by_month(_differences(p_through, b_through), local),
        throughput_kwh=throughput, min_soc_pct=p.min_soc_pct,
        dawn=readings, dawn_days_below=below, worst_dawn_soc_pct=worst, dawn_verdict=verdict,
        new_dawn_days_below=tuple(sorted(here - there)),
        cleared_dawn_days_below=tuple(sorted(there - here)),
        clipped_steps=len(p.clipped_offsets),
        input_class=observed.input_class,
    )


def replay_study(port: ForwardReplayPort, run: SimulationRun, observed: ObservedSeries, frame: StudyFrame,
                 grid: tuple[ReplaySettings, ...] = KOBO_GRID) -> StudyResult:
    """§2.2, in order; the first failure stops, and a refusal raises before any later port call."""
    days = study_days(observed, frame)  # steps 1-2
    admissible = admissible_days(observed, days)  # step 3

    def result(status: str, **fields) -> StudyResult:
        values = dict(calibration=None, baseline=None, cases=(), projections=(), clipped_days=())
        values.update(fields)
        return StudyResult(base_run_id=run.run_id, status=status, input_class=observed.input_class,
                           window_start=observed.interval_start, days=len(days), **values)

    if len(admissible) < frame.min_litre_days:
        return result("SAMPLE_TOO_SHORT")
    start = start_state(observed)  # step 4
    case_ids = _case_ids(grid)  # step 4a
    baseline = port.forward_replay(run, ForwardReplayRequest(BASELINE, observed.pv_available_kw, observed.loads,
                                                             start))  # step 5
    checked(baseline, observed, BASELINE)
    local = step_local_times(observed, frame)
    by_offset = {i * STEP_MINUTES: local[i].date().isoformat() for i in range(len(local))}
    clipped_days = tuple(sorted({by_offset[offset] for offset in baseline.clipped_offsets}))
    calibration = calibrate(observed, baseline, admissible)  # step 6
    if calibration.failed:
        return result("NOT_CALIBRATED", calibration=calibration, projections=(baseline,), clipped_days=clipped_days)
    projections = [baseline]
    for case_id, setting in zip(case_ids, grid, strict=True):  # step 7
        projection = port.forward_replay(run, ForwardReplayRequest(case_id, observed.pv_available_kw, observed.loads,
                                                                   start, setting))
        projections.append(checked(projection, observed, case_id))
    first_previous = start.generator_state  # step 8
    base_outcome = _outcome(BASELINE, baseline, baseline, observed, days, local, frame, first_previous)
    cases = tuple(_outcome(case_id, p, baseline, observed, days, local, frame, first_previous)
                  for case_id, p in zip(case_ids, projections[1:], strict=True))
    return result("CALIBRATED", calibration=calibration, baseline=base_outcome, cases=cases,
                  projections=tuple(projections), clipped_days=clipped_days)


def avoided_l_on(baseline: ForwardReplayProjection, case: ForwardReplayProjection,
                 offsets: frozenset[int]) -> Fraction:
    """Litres avoided on the given step offsets (for 6c: dispatch-3.2 CANDIDATE steps)."""
    if baseline.interval_start != case.interval_start or [s.offset_minutes for s in baseline.steps] != [
            s.offset_minutes for s in case.steps]:
        raise ValueError("the two projections do not cover the same steps")
    b, p = burns(baseline), burns(case)
    return sum((b[i] - p[i] for i, step in enumerate(case.steps) if step.offset_minutes in offsets), Fraction(0))


__all__ = [
    "BASELINE",
    "CALIBRATION_KWH",
    "CALIBRATION_MEASURES",
    "CALIBRATION_SOC_MAE",
    "CALIBRATION_STARTS",
    "DAWN_VERDICTS",
    "EVIDENCE_CLASS",
    "INPUT_CLASSES",
    "KOBO_GRID",
    "MIN_DAWN_DAYS",
    "MIN_LITRE_DAYS",
    "RESERVE_GRID",
    "RUNNING_STATES",
    "STEP_MINUTES",
    "STOP_GRID",
    "STUDY_REFUSALS",
    "STUDY_STATUSES",
    "Calibration",
    "CaseOutcome",
    "DawnReading",
    "MonthFigure",
    "ObservedSeries",
    "StudyDay",
    "StudyFrame",
    "StudyRefused",
    "StudyResult",
    "admissible_days",
    "avoided_l_on",
    "burns",
    "by_month",
    "calibrate",
    "checked",
    "count_starts",
    "dates_below",
    "dawn_outcome",
    "start_state",
    "start_steps",
    "step_local_times",
    "study_days",
    "throughput_steps",
]
