# 0K2: Kobo's stop-threshold and reserve replays on a simulated season (implementer spec)

Status: spec rev 1, handshake pending. Architect (Claude), 2026-11-21, on the owner's delegation
(`owner/owner-away-architect-decides-2026-11-21.md`; pull order `specs/OWNER-AWAY/decisions-2026-11-21.md` row 4).
Spike K, part 2 (`delivery-plan.md` §2 row `0K2`: "Kobo's stop-threshold and reserve replays on the simulated series,
through the port"; lane C, `two-week-build-plan.md` §0.2 days 8 to 10). **4 units.** Discovery review (W5): a new
mechanism whose litres feed a money figure (design §4.2). Non-screen. No migration. No database.
`USER_REVIEW_REQUIRED: false` (nothing served); the figures go to the owner beside the design values (D-0K2.13).

- **What it is.** The product-side replay study the evaluator (`6c`) will call: from a Site's 5-minute observed series
  and a frozen base run it replays the whole window through `ForwardReplayPort` at the baseline, checks the
  calibration rule, then replays each setting of the candidate grid and reports, per setting, the litres avoided (by
  month), the dawn bound, starts, running time, battery throughput, lowest charge and unserved energy. It is proven
  on a declared 61-day simulated Kobo season (D-0K2.1, D-0K2.2), the "simulated series" the slice row names.
- **Why next.** `6a` to `6e` need spike K's replay first (`two-week-build-plan.md` §0.3); design §4.2 makes the
  stop-threshold option a design value "until the adapter reproduces it from site series" (decision D6).
- **Builds on (on `main`):** 0K1's `contracts/assetops_contracts/forward_replay.py` (`ForwardReplayRequest`,
  `LoadSeries`, `ReplayStartState`, `ReplaySettings`, `ForwardReplayProjection`, `ReplayStep`,
  `ForwardReplayRefused`), `backend/assetops_backend/runs/replay_port.py` (`ForwardReplayPort`),
  `host/forward_replay.py` (`HostForwardReplay`); `host/execution_adapter.py` (`frozen_world_inputs`, `model_for`);
  `simulator/assetops_simulator/kernel/execute.py:1893` (`execute`); `host/tests/kobo.py` (`kobo_draft`,
  `set_property`); `contracts/assetops_contracts/world_inputs.py` (`FrozenWorldInputs`, `ForcingInput`,
  `FrozenInterval`). None of 0K1's types changes (0K1 spec, "Who uses it next").
- **Decisions:** `rulings.md` (D-0K2.1 to D-0K2.16). **Reviewer guide:** `reviewer-guide.md`. **Handshake:**
  `handshake.md`.

## 0. Before you start (gates; each is a hard stop)

- **Start:** the handshake has no open question. 0K1 is merged; no other gate.
- **Branch** `task/0K2-kobo-replay-study` off `main`; worktree `/opt/assetecon/AssetOpsV1-0k2`; symlink
  `frontend/node_modules` from the main checkout.
- **Pre-flight print (packet, first section).** Build the 8-day season of §3 (`base_run(8)`, `season_inputs`), run
  `execute(season_inputs(run, 8), model_for(run))` and print: `run.execution_status`; the frozen forcing addresses
  of the base run and of the season inputs (set, with counts); `len(step_starts)` (2,304); the site trajectory's
  generator kWh total, starts (§2.3 rule), running steps, min SOC, fuel used; and the SOC at the step starting
  02:00Z on each day. The Architect's probe on `main` (`a53a77a2e`) gave READY, 2,304 steps, 959.56 kWh, 7 starts,
  min SOC 30.0, fuel 287.87 L. A different status or address set is a mid-build question; different figures are not
  (figures are outputs).
- **Read:** `rulings.md`; design `domain-and-decision-models.md` §4.2 (in the pack); 0K1's `spec.md` §2 and
  `host/forward_replay.py` (whole); `host/tests/test_0k1_forward_replay.py:1-120` (how a Kobo run and a reader are
  built); `tools/derive_steady_scenarios.py:252-268` (`NIGHT_WINDOWS["late"]`); the four scenario files of §3.
- **Heavy tools** through the slot pool only (`tools/heavy-slot.sh -- ...`): host tests by `pwsh -NoProfile -File
  tools/run-host-tests.ps1 -- host/tests/test_0k2_kobo_season.py`; backend tests the same way on
  `backend/tests/test_0k2_replay_study.py` and `backend/tests/test_0k1_replay_port_seam.py` (no database; if the
  wrapper cannot reach a file, record the interpreter command used instead, as D-0K1.18). The 61-day run of §5 unit 3
  through the pool with `--label 0K2-season`, cap 25 minutes (twice the expected 12). Never ports 5490 or 8990, the
  walkthrough DB or Docker.
- **Files.** New: `backend/assetops_backend/runs/replay_study.py`, `backend/tests/test_0k2_replay_study.py`,
  `host/tests/kobo_season.py`, `host/tests/test_0k2_kobo_season.py`, `tools/kobo_replay_study.py`. Edited:
  `backend/tests/test_0k1_replay_port_seam.py` (the allow-list only, D-0K2.14). Nothing under `simulator/`,
  `contracts/`, `config/`, `host/forward_replay.py`, `runs/replay_port.py`, `runs/execution_ports.py` or any guard.
- **No user-facing text** (D-0K2.15): nothing is served or rendered; D-SC1.28 does not apply. `StudyRefused.detail`
  is a developer diagnostic.

## 1. Outcome and gate questions

Does the baseline replay of the season's published series reproduce the season's own generator energy within 5%,
its starts within 10% and its SOC path within 5 points, on at least 14 admissible days? When the site's controller
is not set as its Foundation says (it stops at 70% while the Foundation says 90%), does the study say
`NOT_CALIBRATED` and replay nothing else? For each setting of the grid, are the avoided litres (in total and per
local month), the dawn readings at 05:00 local, the starts, running steps, throughput, lowest charge and unserved
energy read from whole-window replays and nothing else? Is the dawn verdict given only on 61 or more replayed days?
Does every result say its input is SIMULATED and its figures MODELLED?

## 2. Design

### 2.1 Types (`backend/assetops_backend/runs/replay_study.py`)

Imports exactly: `__future__`, `dataclasses`, `datetime`, `fractions`, `zoneinfo`, `assetops_backend.runs.models`,
`assetops_backend.runs.replay_port`, `assetops_contracts.forward_replay` (the seam test pins the set, B12).

```python
STEP_MINUTES = 5
CALIBRATION_KWH = Fraction(5, 100)        # |replayed - observed| <= 5% of observed generator kWh
CALIBRATION_STARTS = Fraction(10, 100)    # |replayed - observed| <= 10% of observed starts
CALIBRATION_SOC_MAE = Fraction(5)         # mean absolute SOC error <= 5 points
MIN_LITRE_DAYS = 14                       # admissible days for any litre figure (design §4.2)
MIN_DAWN_DAYS = 61                        # replayed local days for a dawn verdict (rule of three, design §4.2)
STOP_GRID = tuple(Fraction(s) for s in (90, 85, 80, 75, 70, 65, 60))
RESERVE_GRID = (Fraction(30), Fraction(25))
KOBO_GRID = tuple(ReplaySettings(stop_soc_pct=s, reserve_soc_pct=r) for s in STOP_GRID for r in RESERVE_GRID)  # 14
INPUT_CLASSES = frozenset({"RECORDED", "EMULATED", "SIMULATED"})
STUDY_STATUSES = frozenset({"CALIBRATED", "NOT_CALIBRATED", "SAMPLE_TOO_SHORT"})
STUDY_REFUSALS = frozenset({"STUDY_WINDOW_INVALID", "STUDY_SERIES_MISALIGNED", "STUDY_START_UNKNOWN",
                            "REPLAY_FAILED", "TANK_BOUND_MET"})
DAWN_VERDICTS = frozenset({"PASS", "FAIL", "NOT_CLAIMED"})
RUNNING_STATES = frozenset({"STARTING", "RUNNING"})
CALIBRATION_MEASURES = ("generator_kwh", "starts", "soc")          # the order `failed` lists them in

@dataclass(frozen=True)
class ObservedSeries:                     # a Site's published 5-minute series over the study window, step-aligned
    interval_start: str                   # "YYYY-MM-DDTHH:MM:SSZ"; a local midnight of the frame's zone
    timestep_minutes: int
    pv_available_kw: tuple[Fraction | None, ...]       # average PV-available kW per step (after the inverter limit)
    loads: tuple[LoadSeries, ...]                      # 0K1's LoadSeries, by component id
    generator_kwh: tuple[Fraction | None, ...]         # observed generator energy in each step
    generator_state: tuple[str | None, ...]            # observed generator state for each step
    soc_pct: tuple[Fraction | None, ...]               # observed SOC at each step's start
    start_fuel_l: Fraction                             # the tank at the window start
    input_class: str                                   # INPUT_CLASSES
@dataclass(frozen=True)
class StudyFrame:
    timezone: str                         # the Site's IANA zone, e.g. "Africa/Addis_Ababa"
    battery_capacity_kwh: Fraction        # the Site's declared battery energy capacity (throughput only)
    dawn_local: time = time(5, 0)         # MG5: battery at or above the limit at 05:00 local
    dawn_min_soc_pct: Fraction = Fraction(35)
    min_litre_days: int = MIN_LITRE_DAYS
    min_dawn_days: int = MIN_DAWN_DAYS
@dataclass(frozen=True)
class Calibration:
    admissible_days: tuple[str, ...]      # local dates "YYYY-MM-DD", ascending
    generator_kwh_observed: Fraction; generator_kwh_replayed: Fraction
    starts_observed: int; starts_replayed: int
    soc_mae_points: Fraction
    failed: tuple[str, ...]               # subset of CALIBRATION_MEASURES, in that order; () when calibrated
@dataclass(frozen=True)
class MonthFigure:
    month: str; days: int; value: Fraction            # local month "YYYY-MM", local days of it in the window
@dataclass(frozen=True)
class DawnReading:
    local_date: str; soc_pct: Fraction
@dataclass(frozen=True)
class CaseOutcome:
    case_id: str                          # "baseline" or "stop-<s>-reserve-<r>"
    stop_soc_pct: Fraction; stop_source: str; reserve_soc_pct: Fraction; reserve_source: str
    fuel_l: Fraction                      # the projection's fuel_burned_l
    avoided_l: Fraction                   # baseline fuel_l - this fuel_l (0 for the baseline)
    avoided_l_by_month: tuple[MonthFigure, ...]
    generator_kwh: Fraction; running_steps: int; starts: int; unserved_kwh: Fraction
    added_starts: int; added_running_steps: int; added_throughput_kwh: Fraction
    throughput_kwh: Fraction; min_soc_pct: Fraction
    dawn: tuple[DawnReading, ...]; dawn_days_below: int; worst_dawn_soc_pct: Fraction; dawn_verdict: str
    clipped_steps: int
@dataclass(frozen=True)
class StudyResult:
    base_run_id: str; status: str; input_class: str
    window_start: str; days: int; clipped_days: tuple[str, ...]
    calibration: Calibration | None       # None only when SAMPLE_TOO_SHORT
    baseline: CaseOutcome | None          # set only when CALIBRATED
    cases: tuple[CaseOutcome, ...]        # grid order; () unless CALIBRATED
    projections: tuple[ForwardReplayProjection, ...]   # baseline first, then the grid; (baseline,) when NOT_CALIBRATED
    evidence_class: str = "MODELLED"
class StudyRefused(Exception):
    def __init__(self, code: str, subject: str, detail: str) -> None   # code in STUDY_REFUSALS, else ValueError

def replay_study(port: ForwardReplayPort, run: SimulationRun, observed: ObservedSeries, frame: StudyFrame,
                 grid: tuple[ReplaySettings, ...] = KOBO_GRID) -> StudyResult
def avoided_l_on(baseline: ForwardReplayProjection, case: ForwardReplayProjection,
                 offsets: frozenset[int]) -> Fraction      # for 6c: litres avoided on dispatch-3.2 CANDIDATE steps
```

Construction (`__post_init__`): every numeric field of `ObservedSeries` and `StudyFrame` is a `Fraction` (`None`
allowed only inside a series; a `float`, `int` or `Decimal` is a `TypeError` naming the field, as D-0K1.9);
`timestep_minutes`, `min_litre_days`, `min_dawn_days` are `int`; `input_class` in `INPUT_CLASSES` (`ValueError`);
`dawn_local` a `datetime.time` whose minute is a multiple of 5 and second 0 (`ValueError`); `timezone` resolves by
`zoneinfo.ZoneInfo` (`ValueError` on `ZoneInfoNotFoundError`). `StudyResult.status` in `STUDY_STATUSES`;
`dawn_verdict` in `DAWN_VERDICTS` (`ValueError`).

### 2.2 `replay_study`, in this order (the first failure stops; a refusal raises before any later port call)

Let `n = len(observed.pv_available_kw)`, `zone = ZoneInfo(frame.timezone)`, `t_i = start + i × 5 min` (UTC), and the
local date and local time of step `i` be those of `t_i` in `zone`.

1. **Window.** `timestep_minutes != 5`: `STUDY_WINDOW_INVALID` subject `timestep`. `interval_start` not a UTC
   instant in the stated form, or not 00:00 local: subject `start`. `n == 0`, or any local date in the window with a
   step count other than 288: subject `day:<local date>` (the first such; a zone with a clock change is refused,
   D-0K2.7).
2. **Alignment.** `generator_kwh`, `generator_state`, `soc_pct` and every load's `kw` of length `n`, else
   `STUDY_SERIES_MISALIGNED`, subject the field name (`generator_kwh`, `generator_state`, `soc_pct`,
   `load:<id>`; in that order, loads by id).
3. **Admissible days** (D-0K2.5): a local date is admissible when every one of its steps has `generator_kwh`,
   `generator_state` and `soc_pct` not `None`. Fewer than `frame.min_litre_days` admissible days: return
   `status="SAMPLE_TOO_SHORT"`, `calibration=None`, no projection; **the port is never called**.
4. **Start state.** `soc_pct[0]` or `generator_state[0]` is `None`: `STUDY_START_UNKNOWN` subject `soc` or
   `generator`. Start = `ReplayStartState(soc_pct[0], start_fuel_l, generator_state[0])`. A `RUNNING` start is the
   port's `REPLAY_START_STATE_INVALID`, propagated unchanged.
5. **Baseline.** `port.forward_replay(run, ForwardReplayRequest("baseline", pv_available_kw, loads, start))`, the
   whole window in one call (D-0K2.4). Any `ForwardReplayRefused` propagates unchanged (an input gap is the port's
   `INPUT_GAP`, D-0K2.6). Then, in order: `status == "FAILED"`: `REPLAY_FAILED` subject the case id;
   `interval_start != observed.interval_start`, `timestep_minutes != 5` or `len(steps) != n`:
   `STUDY_WINDOW_INVALID` subject `run`; any step's `fuel_start_l == 0` or `fuel_end_l == 0`: `TANK_BOUND_MET`
   subject the case id (D-0K2.10).
6. **Calibration** (§2.3) on the admissible days. Failed: return `status="NOT_CALIBRATED"`, the calibration,
   `baseline=None`, `cases=()`, `projections=(baseline,)`; **no further port call**.
7. **Grid.** For each settings in `grid` order, one whole-window call with `case_id = f"stop-{s}-reserve-{r}"`,
   where `s` and `r` are the effective values (the setting, else the baseline projection's `stop_soc_pct` /
   `reserve_soc_pct`) written as integers (a non-integral value is a `ValueError`: the grid is integral). Each
   projection is checked as in step 5 (`REPLAY_FAILED`, `TANK_BOUND_MET`).
8. **Outcomes** (§2.4) for the baseline and every case; return `status="CALIBRATED"`.

The port is called exactly `1 + len(grid)` times when calibrated, once when not, never on a short sample or a
refusal of steps 1 to 4. Nothing here applies a setting, a dispatch rule, a fuel law or a price: settings reach the
kernel only through `ReplaySettings` (D-0K1.2).

### 2.3 Calibration (exact `Fraction`s; D-0K2.5)

With `A` the admissible steps (every step of every admissible day) and `p` the baseline projection:
- **Generator energy:** `obs = Σ_{i∈A} generator_kwh[i]`, `rep = Σ_{i∈A} p.steps[i].generator_kwh`; fails when
  `|rep − obs| > CALIBRATION_KWH × obs` (so `obs == 0` requires `rep == 0`).
- **Starts**, one rule for both sides (`count_starts(states, first_previous, indices)`): step `i` is a start when
  `states[i] ∈ RUNNING_STATES` and the state before it is `"STOPPED"`; the state before step 0 is the start state's
  `generator_state`; a `None` before it is no start. Observed: over `observed.generator_state`; replayed: over
  `p.steps[*].generator_state`; both counted only at `i ∈ A`. Fails when `|rep − obs| > CALIBRATION_STARTS × obs`.
- **SOC:** `mae = Σ_{i∈A} |p.steps[i].soc_start_pct − soc_pct[i]| / |A|`; fails when `mae > CALIBRATION_SOC_MAE`.
- `failed` lists the failing measures in `CALIBRATION_MEASURES` order.

### 2.4 Outcomes (per projection `p`, with the baseline `b`)

- **Per-step burn:** `burn_i = p.steps[i].fuel_start_l − next_i`, `next_i = p.steps[i+1].fuel_start_l`, and
  `p.fuel_end_l` for the last step. A declared tank cause sits on both runs and cancels in every difference (D-0K2.10).
- `fuel_l = p.fuel_burned_l`; `avoided_l = b.fuel_burned_l − p.fuel_burned_l`.
- `avoided_l_by_month`: one `MonthFigure` per local month any step falls in, ascending; `value = Σ_{i in month}
  (burn_b,i − burn_p,i)`; `days` = local dates of that month in the window. Over a window, `Σ value == avoided_l`.
- `starts` by §2.3's rule over all steps; `running_steps = p.running_steps`; `generator_kwh`, `unserved_kwh`,
  `min_soc_pct` from `p`; `added_starts`, `added_running_steps` are this case's minus the baseline's.
- `throughput_kwh = Σ_i max(0, soc_i − soc_{i+1}) × frame.battery_capacity_kwh / 100`, with `soc_i =
  p.steps[i].soc_start_pct` and `soc_n = p.soc_end_pct` (discharge at the stock, D-0K2.11);
  `added_throughput_kwh = throughput_kwh − b`'s.
- **Dawn:** for each local date, the step whose local start time equals `frame.dawn_local`; `DawnReading(date,
  p.steps[i].soc_start_pct)`; `dawn_days_below` counts `soc_pct < frame.dawn_min_soc_pct`; `worst_dawn_soc_pct`
  the least; `dawn_verdict` is `NOT_CLAIMED` when `days < frame.min_dawn_days`, else `FAIL` if `dawn_days_below > 0`,
  else `PASS` (D-0K2.8; the baseline gets a verdict too).
- `clipped_steps = len(p.clipped_offsets)`; `StudyResult.clipped_days` = local dates holding a clipped offset of the
  baseline (counted, never excluded; D-0K1.4).
- `avoided_l_on(b, p, offsets) = Σ_{i: p.steps[i].offset_minutes ∈ offsets} (burn_b,i − burn_p,i)`; `ValueError`
  if the two projections' `interval_start` or step offsets differ.

### 2.5 Public helpers (`0M` calls them; D-0K2.16)

`replay_study` is composed of these, each public and in `__all__`, so `0M` reuses one rule rather than writing a
second:

```python
@dataclass(frozen=True)
class StudyDay:
    local_date: str; first: int; end: int              # steps [first, end) of one local day
def study_days(observed: ObservedSeries, frame: StudyFrame) -> tuple[StudyDay, ...]      # §2.2 steps 1-2 (refusals)
def admissible_days(observed: ObservedSeries, days: tuple[StudyDay, ...]) -> tuple[StudyDay, ...]   # step 3
def start_state(observed: ObservedSeries) -> ReplayStartState                            # step 4 (refusals)
def checked(projection: ForwardReplayProjection, observed: ObservedSeries, case_id: str) -> ForwardReplayProjection
    # step 5's three checks in order (REPLAY_FAILED, STUDY_WINDOW_INVALID "run", TANK_BOUND_MET); returns it
def calibrate(observed, baseline: ForwardReplayProjection, admissible: tuple[StudyDay, ...]) -> Calibration  # §2.3
def count_starts(states: tuple[str | None, ...], first_previous: str, indices: frozenset[int] | None = None) -> int
def burns(projection: ForwardReplayProjection) -> tuple[Fraction, ...]                   # §2.4 per-step burn
def step_local_times(observed: ObservedSeries, frame: StudyFrame) -> tuple[datetime, ...]  # aware, the frame's zone
def by_month(values: tuple[Fraction, ...], local_times: tuple[datetime, ...]) -> tuple[MonthFigure, ...]
def dawn_outcome(projection, days, local_times, frame) -> tuple[tuple[DawnReading, ...], int, Fraction, str]
    # (readings, days below, worst, verdict), §2.4
```

## 3. The simulated season (`host/tests/kobo_season.py`; a declared test fixture, D-0K2.1 to D-0K2.3)

No Kobo series longer than a day exists in any store (DS3 loads two Kobo days; DS2's generated telemetry is next
fortnight). The season is therefore declared here from the shipped Kobo day types and run continuously on the kernel
as the site. It is simulated input, never shown as observed.

```python
SEASON_START = "2026-08-31T21:00:00Z"     # 1 Sep 2026 00:00 in Africa/Addis_Ababa (UTC+3, no clock change)
TIMEZONE = "Africa/Addis_Ababa"
SEASON_DAYS = 61                          # 1 Sep - 31 Oct local
def overcast_v1(day_index: int) -> bool: return day_index % 4 == 3     # 15 of 61 days overcast
LATE_WINDOWS = ((1200, 120, {"load-res": 9, "load-clinic": 4}),       # 20:00-22:00 local; pinned to
                (1320, 120, {"load-res": 5, "load-clinic": 2}))       # tools/derive_steady_scenarios.py NIGHT_WINDOWS["late"]
SEASON_START_SOC = Fraction(48)           # kobo-night-early's declared starting-state-of-charge (the measured handover)
SEASON_TANK_L = Fraction(20000); SEASON_START_FUEL_L = Fraction(15000)
def season_site(document) -> None         # Foundation valid_from "2026-08-01T00:00:00Z"; fuel-tank tank-capacity and
                                          #   its rating 20000 (set_property and the component's rating)
def base_run(days: int, *, site_edit=season_site, version: int = 7) -> SimulationRun
    # kobo_draft("kobo-mini-grid-prolonged", timestep_minutes=5, model_profile="mini-grid",
    #   model_profile_version=version, start_time=SEASON_START, end_time=SEASON_START + days, site_edit=site_edit)
def season_inputs(run, days, *, overcast=overcast_v1, load_scale=Fraction(1), start_fuel_l=SEASON_START_FUEL_L,
                  site_stop_pct: Fraction | None = None) -> FrozenWorldInputs
def observed_series(trajectory, n, *, input_class="SIMULATED") -> ObservedSeries
```

**Day types (local hours; every value is the shipped file's, only re-based by the day's offset `d × 1440`):**
00:00-06:00 the four series of `kobo-night-early` (its offsets); 06:00-18:00 the four series of `kobo-steady-day`
(clear) or of `kobo-daytime-overcast` (overcast; its `evening-reserve-override` event is not a series and is not
taken), offset + 360; 18:00-20:00 the events of `kobo-mini-grid-evening` whose `offset_minutes == 360`, re-based to
1080; 20:00-24:00 `LATE_WINDOWS` (irradiance 0, `load-mill` 0). The four series are the events whose `state_key` is
`site:plane-of-array-irradiance`, `load-demand@load-res`, `load-demand@load-clinic`, `load-demand@load-mill`; value
`parameters[0].value`, duration `timing.duration_minutes`.

**`season_inputs`:** `frozen_world_inputs(run)` with every forcing at those four addresses removed and one
`ForcingInput` per day-type window added, `dataclasses.replace` of the base run's first forcing at that address with
`event_id=f"season:{address}:{offset}"`, `parameter_id="season"`, `value` (loads × `load_scale`), `shape="WINDOW"`,
the offset and duration; the `battery-state-of-charge@battery` and `fuel-tank-volume@fuel-tank` initial values set
to `SEASON_START_SOC` and `start_fuel_l`; the generator start `STOPPED` (the base run's). `site_stop_pct`, if given,
adds one window `[0, duration)` at `generator-stop-soc-threshold@generator`, `event_id="season:stop"`, with the
stop-60 run's own row fields (`generator-stop-soc-threshold`, `%`, `FRACTION`, `WINDOW`, `REQUIRED`): the site whose
controller is not set as its Foundation says. Written here, sharing no code with `host/forward_replay.py` (W2); the
scenario document path cannot hold a season (`document_bounds.py`: "more than 4000 nodes" at 8 days, probed).

**`observed_series` (the publication, D-0K2.3):** with `B = trajectory.boundaries`, `H = Fraction(5, 60)`, half-even
rounding to the stated quantum (`round(x / q) × q`, Python's `round` on a `Fraction` is half-even): PV
`B[i+1].interval_measurement("pv-available-power@pv-inverter") / H` to 0.01 kW; each load
`B[i+1].interval_measurement("load-requested-power@<id>") / H` to 0.01 kW, emitted in **reverse sorted** `load_id`
order (D-0K1.10); `generator_kwh` `B[i+1].interval_measurement("generator-output-power@generator")` to 0.001 kWh;
`generator_state` `B[i].discrete_state_for_step("generator-state@generator")`; `soc_pct`
`B[i].stock("battery-state-of-charge@battery")` to 0.1 point; `start_fuel_l` `B[0].stock("fuel-tank-volume@fuel-tank")`
to 0.1 L; `interval_start = SEASON_START`.

**Frame:** `StudyFrame(timezone=TIMEZONE, battery_capacity_kwh=Fraction(200))` (the template's
`battery-energy-capacity`); tests override `min_litre_days` and `min_dawn_days` where a test says so.

## 4. Tests (written first)

`backend/tests/test_0k2_replay_study.py` (no kernel, no database; about a second): a stub port returns projections built in the
test from per-case scripts (2- or 15-day windows at 5 minutes, `Africa/Addis_Ababa`, start `2026-08-31T21:00:00Z`)
and records every request.
- **B1 thresholds:** generator obs 100, rep 105 passes, rep `105 + 1/1000` fails, rep 95 passes (5 of observed, not
  of replayed); starts obs 10: rep 11 passes, 12 fails; obs 0: rep 0 passes, rep 1 fails; SOC MAE exactly 5 passes,
  `5 + 1/1000` fails; `failed` order when all three fail.
- **B2 admissibility:** one `None` in a day's observed `soc_pct` excludes that whole day; the replay differs by 50
  points on that day only; calibrated; `admissible_days` omits it.
- **B3 dawn is local:** each step's SOC distinct; the dawn reading of 1 Sep is the step at 02:00Z; `worst`,
  `dawn_days_below`, verdict with `min_dawn_days` equal to and above the window's days.
- **B4 months are local:** the three hours from 21:00Z on 31 Aug count in `2026-09`; a 15-day window from
  `2026-09-23T21:00:00Z` gives `2026-09` (7 days) and `2026-10` (8 days); `Σ value == avoided_l`.
- **B5 throughput:** SOC 50, 40, 45, 30 with capacity 200 gives 50 kWh (charge not counted).
- **B6 starts:** states STOPPED, STARTING, RUNNING, RUNNING, STOPPED, RUNNING after a STOPPED start gives 2; a FAILED
  then RUNNING gives 0; with a STOPPED start state, a first step STARTING counts.
- **B7 refusals and order:** timestep 15, a start at 22:00Z, 287 steps (each `STUDY_WINDOW_INVALID` with its
  subject); `soc_pct` one short (`STUDY_SERIES_MISALIGNED`, `soc_pct`); `soc_pct[0] None`
  (`STUDY_START_UNKNOWN`, `soc`); a short sample returns `SAMPLE_TOO_SHORT` with **zero** port calls; a misaligned
  series with a short sample refuses (step 2 before step 3).
- **B8 propagation:** the stub raises `ForwardReplayRefused("INPUT_GAP", "pv@50", "x")`: the same exception reaches
  the caller; a FAILED baseline is `REPLAY_FAILED` subject `baseline`; a FAILED grid case is `REPLAY_FAILED`
  subject its case id; a projection with 287 steps is `STUDY_WINDOW_INVALID` subject `run`.
- **B9 tank:** a step with `fuel_start_l == 0` in a grid case is `TANK_BOUND_MET` subject that case id.
- **B10** `avoided_l_on` over an offset subset; mismatched offsets raise `ValueError`.
- **B11 construction:** a `float` in `soc_pct`, an `int` `start_fuel_l`, `input_class="OBSERVED"`, `dawn_local`
  05:02, an unknown zone, `StudyRefused("NOPE", "", "")` each raise; `KOBO_GRID` has 14 settings, stop-major.
- **B12 seam:** `replay_study.py` imports exactly §2.1's set (an `ast` scan); a NOT_CALIBRATED stub run calls the
  port once; a calibrated one `1 + len(grid)` times, every request of `n` steps.

`host/tests/test_0k2_kobo_season.py` (the kernel; no database; an 8-day season unless stated, v7; about 1 minute).
Expected values come from the test's own reader of the site trajectory and of the projections (it shares no code
with `replay_study.py`, W2): dawn by fixed offset `d × 1440 + 300` from `SEASON_START`, months by offset, starts by
its own loop, throughput by its own loop.
- **T1 calibrated:** `replay_study(HostForwardReplay(), run, observed, frame(min_litre_days=8, min_dawn_days=8),
  grid=(S(90, 30), S(70, 30), S(90, 25)))` (`S(a, b)` is `ReplaySettings(Fraction(a), Fraction(b))`) is `CALIBRATED`; the calibration's five figures equal the reader's;
  preconditions asserted: the observed series differs from the kernel's exact values on at least one step
  (quantization is live); `clipped_days` is not empty and every day is admissible (clipped days are kept).
- **T2 anchor:** case `stop-90-reserve-30` (settings) has steps equal to the baseline's on every field, `avoided_l
  == 0`, `stop_source == "SETTING"`; the baseline's sources are `BASELINE`.
- **T3 outcomes:** for each case every `CaseOutcome` figure equals the reader's; `Σ avoided_l_by_month ==
  avoided_l`; preconditions: some case has `dawn_days_below >= 1` and some reading is `>= 35`; `stop-70-reserve-30`
  has `avoided_l != 0`.
- **T4 not calibrated (14-day season):** the site at `site_stop_pct=Fraction(70)`, `min_litre_days=14`:
  `NOT_CALIBRATED`, `failed == ("generator_kwh",)` (probe on `main`: 9.1% over, SOC MAE 0.36, starts equal),
  `cases == ()`, one port call.
- **T5 short sample:** `min_litre_days=14` on 8 days: `SAMPLE_TOO_SHORT`, zero port calls.
- **T6 verdict:** default `min_dawn_days` (61): every case `NOT_CLAIMED`; with 8: `FAIL` exactly where
  `dawn_days_below > 0`.
- **T7 whole window:** a recording port wrapper sees `1 + len(grid)` calls, each with 2,304 PV values.
- **T8 pins:** `STOP_GRID`, `RESERVE_GRID`, the three tolerances, `MIN_LITRE_DAYS == 14`, `MIN_DAWN_DAYS == 61`;
  `LATE_WINDOWS` equals `NIGHT_WINDOWS["late"]` of `tools/derive_steady_scenarios.py` (loaded by `importlib` from its
  path); `overcast_v1` gives 15 of 61.
- **T9 tank:** `season_inputs(..., start_fuel_l=Fraction(50))` and the observed start 50 L: `TANK_BOUND_MET`.
- **T10 gap:** observed PV `None` at offset 600: `ForwardReplayRefused` `INPUT_GAP` `pv@600` reaches the caller.

**Edited** `backend/tests/test_0k1_replay_port_seam.py`: `allowed` gains `runs/replay_study.py` and
`backend/tests/test_0k2_replay_study.py`; nothing else changes.

**The 61-day study** (`tools/kobo_replay_study.py --days 61 --out <file>`; inserts `host`, `host/tests`, `backend`,
`contracts`, `simulator` on `sys.path` as `tools/probe_kobo_nights.py` does): the season, its site run, the observed
series, `replay_study` with the default frame and `KOBO_GRID`; writes one JSON (every `Fraction` as `"p/q"` and a
3-decimal reading) to `/opt/assetecon/evidence/0K2/<run>/study.json`; prints one line per case. Expected about 16
kernel runs of 17,568 steps, about 12 minutes. Exit 0 done, 2 refused (`<CODE> <subject>` on stderr).

**Regression:** `host/tests/test_0k1_forward_replay.py`, `backend/tests/test_0k1_replay_port_seam.py`, the
dependency-direction guard, check-all (fast) once at the end, `python tools/select-tests.py --base main`.
**Guard shown failing:** a scratch copy of `runs/replay_study.py` with `from host.forward_replay import
HostForwardReplay` fails `tools/checks/dependency-direction.ps1` (packet: exit code and message).

## 5. Units

| Unit | Content | Commits |
|---|---|---|
| 1 (1.5) | §2.1 types, §2.2 steps 1-6, §2.3, the §2.5 helpers they use; B1, B2, B6, B7, B8 (baseline half), B11, B12; the seam-test edit | 1 |
| 2 (1.5) | §2.2 steps 7-8, §2.4, `avoided_l_on`; B3-B5, B8 (grid half), B9, B10; §3 fixture; T1-T10 | 1 |
| 3 (1.0) | the tool and the 61-day run; regression; guard failing; check-all; packet | 0 to 1 |

Total 4.0. Packet: `specs/0K2-kobo-replay-study/packet.md`: the pre-flight print; the 61-day result per case (fuel,
avoided by month, dawn days below and worst, starts, running steps, added throughput, min SOC, unserved); beside
them the design values (§4.2: stop 70 avoided 210 L a month, 0 of 61 dawn days, 150 kWh added throughput; reserve 25
avoided 20 L a month, 4 of 61 dawn days); the calibration figures; run count and wall time; the guard run; the
mid-build count.

## 6. Done (questions; each can fail)

1. Does the baseline replay of the season's published series calibrate, with each measure equal to an independent
   reader's, and does a site stopping at 70% fail on generator energy with nothing else replayed?
2. Is every replay a whole-window call, settings reaching the kernel only through `ReplaySettings`, and does the
   (90, 30) setting reproduce the baseline exactly?
3. Are the avoided litres by local month, the dawn readings at 05:00 local, starts, throughput and the verdict rule
   (61 days) each equal to the independent reader's, on a season where the bound both holds and fails?
4. Is every refusal given with its code and subject before the port is called, a short sample never replayed, an
   input gap the port's own refusal, and a tank that empties refused?
5. Is no money, price or physical law in `replay_study.py`, and does every result carry SIMULATED and MODELLED?
6. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 7. Out of scope

Money (litres × price, wear cost, one-off, value: the evaluator `6c`, D-0K2.12); the dispatch-3.2 CANDIDATE share
of the avoided litres (`avoided_l_on` is the hook; `6c` supplies the offsets); choosing a setting (design's "highest
value ... 2 points above the dawn limit" rule: `6c`); reading the series from accepted readings (queued `0K3`,
D-0K2.1); a gap-fill rule (D-0K2.6); a zone with a clock change (D-0K2.7); replacing the pack's design values or any
label (held for the owner, D-0K2.13); any screen or served text; Kisiwa's negative control (`6c`, on its own series).

## 8. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 | Where do "the simulated series" come from? | A declared 61-day season of shipped Kobo day types, run on the kernel as the site (D-0K2.1, D-0K2.2) |
| Q2 | Replay day by day or the whole window? | Whole window (D-0K2.4): the dawn bound depends on the evening before |
| Q3 | A dawn bound that fails under no action too | Reported for every case, baseline included, by the design's absolute rule; option admissibility relative to no action is `6c`'s, for the owner then (D-0K2.8) |
| Q4 | Do the season's figures replace the design values? | Held for the owner (owner-away row 31); recorded beside them in the packet (D-0K2.13) |
| Q5 | Money in the spike? | No: the evaluator's (D-0K2.12) |
| Q6 | Short input gaps | Refused, as D-0K1.5; a fill rule waits for real series (D-0K2.6) |
