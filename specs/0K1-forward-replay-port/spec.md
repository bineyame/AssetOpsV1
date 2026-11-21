# 0K1: the forward replay port and its host adapter (implementer spec)

Status: in_review (built on `task/0K1-forward-replay`; packet `packet.md`). Rev 2 (handshake round 1 folded in: D-0K1.10 to D-0K1.18), Architect (Claude), 2026-11-21, written on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`;
pull order `specs/OWNER-AWAY/decisions-2026-11-21.md` row 4). Spike K, part 1 (`delivery-plan.md` §2 row `0K1`: "the
forward replay port method and its host adapter, proven by replaying a recorded run to the kernel's own trajectory";
lane C in `two-week-build-plan.md` §0.2, days 6 to 8). **3 units.** Discovery review (W5): a new port across a
protected seam (`.ai/RULES.md` §1; design A5). Non-screen. `USER_REVIEW_REQUIRED: false`.

- **What it is.** The product may not import the simulator (`tools/checks/dependency-direction.ps1`), yet valuing a
  generator setting needs the kernel (design `domain-and-decision-models.md` §4.2). 0K1 builds the seam: a neutral
  request and projection in `assetops_contracts`, a one-method port the product owns, and the adapter in `host/`
  that turns a frozen Kobo run plus a replay request into kernel inputs, executes them and projects the result. It is
  proven by exact equality with the kernel's own trajectory on five cases drawn from three shipped scenarios (prolonged, stop-60, reserve-trial; two cases edited by `document_edit`; the overcast scenario only pins a constant, T10).
- **Who uses it next.** `0K2` (Kobo's stop-threshold and reserve replays on the simulated series, the calibration
  rule, the 61-day window), `0M` (Mto's headroom replay "through the same adapter"), `6c` (the evaluator wired to the
  port). None of them may need a change to the port's types; that is what "done" protects.
- **Builds on (merged on `main` at `39e1682de`):** `host/execution_adapter.py` (`frozen_world_inputs(run)`,
  `model_for(run)`, `RunNotExecutable`, `FrozenRunNotReconstructible`), `simulator/assetops_simulator/kernel/execute.py`
  (`execute(inputs, model)`), `packs/mini_grid.py` (v5 `decide_v5`, `effective_start_threshold`; v2 stop-threshold
  override `_stop_threshold_at`, `STOP_THRESHOLD_OVERRIDE`), `packs/minigrid.py` (`_pv_available`, `_reserve_at`,
  `IRRADIANCE_ADDRESS`, `STANDARD_IRRADIANCE`), `contracts/assetops_contracts/trajectory.py` (`PrivateTrajectory`,
  `BoundaryState`, `DiscreteTransition`), `world_inputs.py` (`FrozenWorldInputs`, `ForcingInput`, `InitialValue`,
  `DiscreteInitialValue`, `DeclaredCause`), `backend/assetops_backend/runs/execution_ports.py` (`LabExecutionPort`,
  untouched), `host/tests/kobo.py` (`kobo_draft`).
- **Decisions:** `rulings.md` (D-0K1.1 to D-0K1.18). **Reviewer guide:** `reviewer-guide.md`. **Handshake:**
  `handshake.md`.

## 0. Before you start (gates; each is a hard stop)

- **Start:** the handshake has no open question. No other gate: 0K1 depends on nothing unmerged.
- **Branch** `task/0K1-forward-replay` off `main`; worktree `/opt/assetecon/AssetOpsV1-0k1`; symlink
  `frontend/node_modules` from the main checkout.
- **Pre-flight print (packet, first section).** Build `kobo_draft("kobo-mini-grid-prolonged", timestep_minutes=5,
  model_profile="mini-grid", model_profile_version=5, start_time="2026-09-22T03:00:00Z",
  end_time="2026-09-22T11:00:00Z")`, call `frozen_world_inputs(run)` and print every `forcings` row's `(event_id,
  address, state_key, canonical_unit, dimension, shape, requirement)`, every `initial_values` row's `(address,
  state_key, parameter_id, value)` and `discrete_initial_values`. Do the same for `kobo-mini-grid-stop-60` (v5) and
  for `kobo-daytime-overcast` (`daytime-mini-grid`, 15-minute, its own default interval): the stop-override row and
  the reserve-forcing row are what §2.3's constants are pinned to. Also print `[k for k, _ in B[1].interval_measurements]` of the prolonged v7 trajectory (the kernel keys are what the test reader reads: `pv-available-power@pv-inverter`, `load-requested-power@load-clinic|load-mill|load-res`, `generator-output-power@generator`; D-0K1.15). Record the output in the packet. If any address
  below differs from what is printed, stop and ask (a mid-build question).
- **Read:** `rulings.md`; design `domain-and-decision-models.md` §4.2 (in the pack); `runs/execution_ports.py`
  (whole header); `host/execution_adapter.py:1-141`, `:160-255`, `:404-524`, `:869-876`; `packs/mini_grid.py:1-35`,
  `:344-405`, `:949-1030`, `:1100-1160`; `packs/minigrid.py:1-90`, `:505-545`; `trajectory.py:239-500`;
  `host/tests/test_mini_grid_v5.py` (how a Kobo v5 run is built and read).
- **Databases:** none. Heavy tools through the slot pool only: host tests by `tools/heavy-slot.sh -- pwsh -NoProfile
  -File tools/run-host-tests.ps1 -- host/tests/test_0k1_forward_replay.py`; contract tests by the same wrapper on
  `contracts/tests/test_0k1_forward_replay_contract.py` (the wrapper puts `contracts/` on `PYTHONPATH` and takes any file path; no database is used by either new test file; the packet's first section records both commands and their exit lines, and if the wrapper cannot reach a file the interpreter command used instead, which is not a mid-build question; D-0K1.18). Never ports 5490 or 8990, the walkthrough DB or Docker.
- **Files.** New: `contracts/assetops_contracts/forward_replay.py`, `backend/assetops_backend/runs/replay_port.py`,
  `host/forward_replay.py`, `host/tests/test_0k1_forward_replay.py`, `contracts/tests/test_0k1_forward_replay_contract.py`,
  `backend/tests/test_0k1_replay_port_seam.py`. Edited: none. Nothing under `simulator/`, `runs/execution_ports.py`,
  `host/execution_adapter.py` or any guard changes (D-0K1.1, D-0K1.2).
- **No user-facing text** (D-0K1.8): nothing here is served or rendered; D-SC1.28 does not apply.

## 1. Outcome and why

Spike K exists because the stop-threshold change at Kobo is worth 2,916.00 over twelve months only as a *design
value* until "the adapter reproduces it from site series" (§4.2; decision D6). Before any replay can be trusted on
site series, the adapter itself must be shown to change nothing: replaying a run's own recorded series through the
port must give back exactly that run's trajectory, and replaying it under a changed setting must give exactly the
kernel's own run under that setting. 0K1 proves both, exactly (every value is a `Fraction`; there is no tolerance).
Calibration against *observed* series (±5% generator kWh, ±10% starts, 5 points SOC) is `0K2`'s (D-0K1.7).

Gate questions: does a replay of Kobo's prolonged morning, from its own recorded PV-available and per-load demand
series, reproduce every step's generator state, generator energy, unserved energy, battery charge and fuel? Does the
same series replayed at a 60% stop threshold equal the kernel's own stop-60 run, and at a 25% reserve equal the
kernel's own run on a 25% reserve? Does any simulator type cross into the product?

## 2. Design

### 2.1 The neutral contract (`contracts/assetops_contracts/forward_replay.py`; standard library only)

```python
REPLAY_GENERATOR_STATES = frozenset({"STOPPED", "FAILED"})        # start states a run may declare (mini_grid.py:9-12)
REPLAY_STATUSES = frozenset({"COMPLETED", "FAILED"})
FORWARD_REPLAY_REFUSALS = frozenset({
    "REPLAY_RUN_NOT_EXECUTABLE", "REPLAY_MODEL_UNSUPPORTED", "REPLAY_SERIES_MISALIGNED", "INPUT_GAP",
    "REPLAY_SERIES_INVALID", "REPLAY_ADDRESS_UNKNOWN", "POLICY_BAND_INVALID", "REPLAY_START_STATE_INVALID"})
CASE_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
EVIDENCE_CLASS = "MODELLED"

@dataclass(frozen=True)
class LoadSeries:
    load_id: str                                # the component id after "load-demand@", e.g. "load-mill"
    kw: tuple[Fraction | None, ...]             # average requested kW over each step, in step order
@dataclass(frozen=True)
class ReplayStartState:
    soc_pct: Fraction; fuel_l: Fraction; generator_state: str
@dataclass(frozen=True)
class ReplaySettings:
    stop_soc_pct: Fraction | None = None        # None: the base run's frozen baseline
    reserve_soc_pct: Fraction | None = None
@dataclass(frozen=True)
class ForwardReplayRequest:
    case_id: str                                # CASE_ID fullmatch, e.g. "baseline", "stop-60"
    pv_available_kw: tuple[Fraction | None, ...]  # average PV-available kW (after the inverter limit) per step
    loads: tuple[LoadSeries, ...]
    start: ReplayStartState
    settings: ReplaySettings = ReplaySettings()

@dataclass(frozen=True)
class ReplayStep:
    offset_minutes: int; generator_state: str; generator_kwh: Fraction; unserved_kwh: Fraction
    soc_start_pct: Fraction; fuel_start_l: Fraction; pv_clipped: bool
@dataclass(frozen=True)
class ForwardReplayProjection:
    base_run_id: str; case_id: str; status: str                     # REPLAY_STATUSES
    model_profile_id: str; model_profile_version: int
    interval_start: str; timestep_minutes: int
    stop_soc_pct: Fraction; stop_source: str                        # "BASELINE" | "SETTING"
    reserve_soc_pct: Fraction; reserve_source: str
    steps: tuple[ReplayStep, ...]
    soc_end_pct: Fraction | None; fuel_end_l: Fraction | None; min_soc_pct: Fraction
    generator_kwh: Fraction; unserved_kwh: Fraction; starts: int; running_steps: int
    fuel_burned_l: Fraction | None
    clipped_offsets: tuple[int, ...]
    replay_identity: str                                            # the kernel's inputs_identity for the replay
    evidence_class: str = EVIDENCE_CLASS
    failure_kind: str | None = None; failure_subject: str | None = None

class ForwardReplayRefused(Exception):
    def __init__(self, code: str, subject: str, detail: str) -> None   # code in FORWARD_REPLAY_REFUSALS, else ValueError
```

Construction rules (`__post_init__`, D-0K1.9): every numeric field of the request is a `Fraction` (a `float`,
`int` or `Decimal` raises `TypeError` naming the field; `None` is allowed only inside a series); `case_id` must
fullmatch `CASE_ID` (`ValueError`); `generator_state` must be in `REPLAY_GENERATOR_STATES` is **not** checked here
(it is a refusal, §2.4 step 9, so the reason reaches the caller as a code). `ForwardReplayProjection.status` must be
in `REPLAY_STATUSES`; `failure_kind` is set if and only if `status == "FAILED"` (`ValueError`). Nothing in this module
imports anything outside the standard library.

### 2.2 The port (`backend/assetops_backend/runs/replay_port.py`)

```python
@runtime_checkable
class ForwardReplayPort(Protocol):
    def forward_replay(self, run: SimulationRun, request: ForwardReplayRequest) -> ForwardReplayProjection:
        """Replay a frozen mini-grid run's world under a request; raises ForwardReplayRefused when nothing ran."""
```
Imports: `__future__`, `typing`, `assetops_backend.runs.models.SimulationRun`, `assetops_contracts.forward_replay`.
Nothing composes it in the product in this unit (no route, no command); `0K2` and `6c` receive it by injection, as
`LabExecutionPort` is received (`execution_ports.py` "Why the product cannot build an implementation of it").
`LabExecutionPort` is not edited (D-0K1.1).

### 2.3 The adapter (`host/forward_replay.py`)

```python
REPLAY_MODELS = frozenset({("mini-grid", 5), ("mini-grid", 6), ("mini-grid", 7)})   # D-0K1.3; each proven by T1 (D-0K1.12)
STEP_HOURS = lambda minutes: Fraction(minutes, 60)

class HostForwardReplay:                       # satisfies ForwardReplayPort
    def __init__(self, *, execute_fn=execute) -> None          # tests inject a stub (§4 T7); default the kernel's
    def forward_replay(self, run, request) -> ForwardReplayProjection

def replay_inputs(run: SimulationRun, request: ForwardReplayRequest) -> ReplayPlan     # pure; §2.4 steps 1-10
@dataclass(frozen=True)
class ReplayPlan:
    inputs: FrozenWorldInputs; model: ModelSpec; plant: ReplayPlant
    stop: tuple[Fraction, str]; reserve: tuple[Fraction, str]; clipped_offsets: tuple[int, ...]
@dataclass(frozen=True)
class ReplayPlant:                             # every value read from the base run's frozen inputs
    battery: str; generator: str; tank: str; loads: tuple[str, ...]      # component ids, loads sorted
    pv_rated_kw: Fraction; inverter_ac_limit_kw: Fraction; tank_capacity_l: Fraction
    start_threshold_pct: Fraction; stop_baseline_pct: Fraction; reserve_baseline_pct: Fraction
def project(plan: ReplayPlan, trajectory: PrivateTrajectory, run: SimulationRun,
            request: ForwardReplayRequest) -> ForwardReplayProjection                  # §2.5
```

**Addresses** (all exact strings, components read from the frozen inputs, never assumed): battery `b` from the one
`initial_values` row whose address starts `battery-state-of-charge@`; generator `g` from the one
`discrete_initial_values` row whose address starts `generator-state@`; tank `k` from the one `initial_values` row whose
address starts `fuel-tank-volume@`; loads from every `forcings` row whose address starts `load-demand@`. Plant numbers
from `initial_values` by `state_key`: `pv-rated-power`, `inverter-ac-limit`, `fuel-tank-capacity`,
`generator-start-soc-threshold`, `generator-stop-soc-threshold`, `battery-reserve-state-of-charge` (one row each;
zero or two is `REPLAY_RUN_NOT_EXECUTABLE`, subject the state key). The pre-flight print confirms them.

**Forcings built** (one `ForcingInput` per run of equal consecutive values, shape `WINDOW`, `requirement` as the
base run's row for that address):
- irradiance at `site:plane-of-array-irradiance`: value `STANDARD_IRRADIANCE * kw / pv_rated_kw` (exact; D-0K1.4);
  `event_id` `replay:pv:<offset>`; other fields copied from the base run's first forcing at that address;
- each load at `load-demand@<load>`: value `kw`; `event_id` `replay:load:<load>:<offset>`; fields copied likewise;
- a stop setting, if given: one window `[0, duration)` at `generator-stop-soc-threshold@<g>`, `event_id` `replay:stop`, `state_key`, `canonical_unit`, `dimension` and `requirement` equal to the stop-60 run's own row
  (constants `STOP_OVERRIDE_FIELDS`, pinned by T10). A whole-interval window is aligned to every step, which is what
  `_stop_threshold_at` requires; it is the shipped stop-60 row's own form (offset 0, duration 480 at 5-minute steps;
  D-0K1.17);
- a reserve setting, if given: one window `[0, duration)` at `battery-reserve-state-of-charge@<b>`, `event_id`
  `replay:reserve`, fields `RESERVE_OVERRIDE_FIELDS`, pinned by T10 to the overcast run's reserve row (a drift guard only; that the
  mini-grid models accept the row is proved by T4; D-0K1.16).
Every base-run forcing at the irradiance address, a load-demand address, the stop address or the reserve address is
removed; every other forcing, every cause, bound, site control, bus attachment and unmodelled input is kept unchanged
(D-0K1.2). `parameter_id` of a built forcing is `replay:<field>` (`pv`, `load`, `stop`, `reserve`).

**Start states:** the `initial_values` rows at `battery-state-of-charge@<b>` and `fuel-tank-volume@<k>` and the
`discrete_initial_values` row at `generator-state@<g>` are replaced with `dataclasses.replace(row, value=...)`.
`run_id` of the inputs becomes `f"{run.run_id}:replay:{case_id}"`. Nothing else in the inputs changes.

### 2.4 The order of checks in `replay_inputs` (the first that fails refuses; nothing executes)

1. `model_for(run)` raises, or `frozen_world_inputs(run)` raises `RunNotExecutable` or `FrozenRunNotReconstructible`:
   `REPLAY_RUN_NOT_EXECUTABLE` (subject `run.run_id`). A run whose `execution_status` is not `READY` is this code.
2. `(model.model_profile_id, model.model_profile_version)` not in `REPLAY_MODELS`: `REPLAY_MODEL_UNSUPPORTED`
   (subject `"<id>/<version>"`).
3. The plant (§2.3): a missing or doubled address or number: `REPLAY_RUN_NOT_EXECUTABLE`.
4. `len(pv_available_kw)` or any load's `len(kw)` differs from `len(inputs.interval.step_starts)`:
   `REPLAY_SERIES_MISALIGNED` (subject `pv` or `load:<id>`).
5. The set of `load_id`s differs from the plant's loads, or a `load_id` repeats: `REPLAY_ADDRESS_UNKNOWN` (subject the
   first offending id in sorted order, missing ones before extra ones).
6. Any `None` in a series: `INPUT_GAP`, subject `pv@<offset>` or `load:<id>@<offset>` for the earliest offset (PV
   before loads at the same offset, loads by id) (D-0K1.5).
7. Any value `< 0`, or a PV value `> inverter_ac_limit_kw`: `REPLAY_SERIES_INVALID` (subject as step 6).
8. Settings: a stop setting not in `(start_threshold_pct, 100]`, or a reserve setting not in `[0, 100]`:
   `POLICY_BAND_INVALID` (subject `stop` or `reserve`). The kernel's own check (`mini_grid.py:390-397`) is the same
   band; checking first means a bad setting never becomes a FAILED run.
9. Start: `soc_pct` not in `[0, 100]`, `fuel_l` not in `[0, tank_capacity_l]`, or `generator_state` not in
   `REPLAY_GENERATOR_STATES`: `REPLAY_START_STATE_INVALID` (subject `soc`, `fuel` or `generator`).
10. Build the inputs (§2.3); `clipped_offsets` are the step offsets whose PV value equals `inverter_ac_limit_kw`.

`forward_replay`: `plan = replay_inputs(run, request)`; `trajectory = self._execute(plan.inputs, plan.model)`
(`execute(inputs, model)`, `execute.py:1893`, `raise_on_failure` left false, so a
failure comes back as a FAILED trajectory); `return project(plan, trajectory, run, request)`. A kernel
failure is a FAILED projection, never a refusal (D-0K1.6, as `LabExecutionPort`'s docstring separates them).

### 2.5 The projection (`project`)

With `B = trajectory.boundaries`, `dt = inputs.interval.timestep_minutes`, `n = len(step_starts)`:
- `steps[i]` for each `i` with both `B[i]` and `B[i+1]` recorded: `offset_minutes = B[i].offset_minutes`;
  `generator_state = B[i].discrete_state_for_step("generator-state@<g>")`; `generator_kwh =
  B[i+1].interval_measurement("generator-output-power@<g>")` (always measured from v2, `mini_grid.py:988-991`; a
  missing value is a `RuntimeError`, a defect, not a refusal); `unserved_kwh = Σ_load
  (B[i+1].interval_measurement("load-requested-power@<l>") − B[i+1].interval_measurement("load-served-power@<l>"))`;
  `soc_start_pct = B[i].stock("battery-state-of-charge@<b>")`; `fuel_start_l = B[i].stock("fuel-tank-volume@<k>")`;
  `pv_clipped = offset in clipped_offsets`.
- `soc_end_pct`, `fuel_end_l`: the stocks at `B[n]` when `status == "COMPLETED"`, else `None`.
- `min_soc_pct`: the least SOC stock over every recorded boundary.
- `generator_kwh`, `unserved_kwh`: sums over `steps`; `running_steps`: steps with `generator_state == "RUNNING"`;
  `starts`: `trajectory.discrete_transitions` with `address == "generator-state@<g>"`, `previous == "STOPPED"` and
  `next == "STARTING"`.
- `fuel_burned_l` (COMPLETED only, else `None`): `fuel_start − fuel_end + Σ` over `inputs.causes` at the tank
  address of `quantity` (`INCREASE`) or `−quantity` (`DECREASE`). Its docstring says: "exact only while the tank never
  meets its capacity or empty bound; a run whose tank causes could clip is outside 0K1's proof (0K2)" (D-0K1.14).
- `stop_soc_pct`, `stop_source`: the setting and `"SETTING"`, else the baseline and `"BASELINE"`; reserve likewise.
- `replay_identity = trajectory.inputs_identity`; `status = trajectory.outcome`; on FAILED, `failure_kind` and
  `failure_subject` from `trajectory.failure`.
- Nothing else: no `BoundaryState`, `PrivateTrajectory`, `ModelSpec`, irradiance value or event list crosses.

## 3. Fixtures (shipped scenarios; no new file under `config/`)

Every run: `kobo_draft(name, timestep_minutes=5, model_profile="mini-grid", model_profile_version=V,
start_time="2026-09-22T03:00:00Z", end_time="2026-09-22T11:00:00Z", ...)` (96 steps), `V` is 7 for K-START to K-CLIP; K-BASE runs at
5, 6 and 7 (D-0K1.12). The test's own reader (`recorded_request(trajectory, case_id)`, written in the test file, sharing no
code with the adapter, W2) builds a request from a kernel trajectory, **loads in reverse sorted `load_id` order** (the kernel's and the plant's order is sorted, so any positional match would pass otherwise; D-0K1.10): for step `i`, `pv = B[i+1].interval_measurement(
"pv-available-power@pv-inverter") / Fraction(5, 60)`, each load's `kw = B[i+1].interval_measurement(
"load-requested-power@<load>") / Fraction(5, 60)`; start from `B[0]` (SOC and tank stocks, `B[0].discrete_state(
"generator-state@generator")`). Each case's expected values are read from its own kernel run, executed by the test
with `execute(frozen_world_inputs(run), model_for(run))`.. Component ids as printed on `main` (D-0K1.15): `pv-array`, `pv-inverter` (the inverter; read as `pv-available-power@pv-inverter`),
`battery-pcs`, `battery`, `generator`, `fuel-tank`, `load-res`, `load-clinic`, `load-mill`; the reader's keys are those
printed keys, and a key missing from the boundary is a `KeyError` that fails the test.

| Case | Kernel run (the expected trajectory) | Replay request |
|---|---|---|
| **K-BASE** | `kobo-mini-grid-prolonged` | `recorded_request(K-BASE)`, settings none |
| **K-START** | `kobo-mini-grid-prolonged` with `document_edit` setting `starting-state-of-charge` to 55 | K-BASE's series, start SOC 55 |
| **K-STOP** | `kobo-mini-grid-stop-60` | K-BASE's series, `stop_soc_pct=Fraction(60)` |
| **K-RES** | `kobo-mini-grid-reserve-trial` with `site_edit` reserve 25 (`test_mini_grid_v5.py` `_reserve`) | `recorded_request` of the same scenario unedited (reserve 30), `reserve_soc_pct=Fraction(25)`; also that request with no setting (the baseline-30 anchor) |
| **K-CLIP** | `kobo-mini-grid-prolonged` with `document_edit` setting the 240-minute irradiance window's value from 550 to 900 (54 kW potential on a 50 kW inverter) | `recorded_request(K-CLIP)` |

Hand anchors (independent of both the kernel and the adapter): Kobo's template 0.3 L/kWh, so K-BASE's
`fuel_burned_l == Fraction(3, 10) * generator_kwh`; K-BASE `starts == 1` and `running_steps == 66` (so `starts` and `running_steps` differ; printed on `main` for v5, v6 and v7) and `unserved_kwh > 0`; the three load series of K-BASE are pairwise unequal (so a mix-up changes the result) (the scenario's
purpose: "part of the load goes unserved for that hour"); K-STOP's `generator_kwh` and `running_steps` are strictly
less than K-BASE's ("it runs for less time, delivers less energy"); K-RES `running_steps == 0` and the replay of the
same series with **no setting** (baseline 30, not `Fraction(30)`) has `running_steps > 0` (`test_mini_grid_v5.py` docstring: the dawn dip to 34.6% never
reaches v5's 30% start); K-CLIP `clipped_offsets == tuple(range(240, 480, 5))`; K-BASE `clipped_offsets == ()`.

## 4. Tests (written first)

`host/tests/test_0k1_forward_replay.py` (no database):
- **T1 parity, K-BASE (V = 5, 6 and 7):** `HostForwardReplay().forward_replay(run, request)`; for every step `i`, each
  `ReplayStep` field equals the value read from the kernel trajectory by the test's own reader (state, generator kWh,
  unserved kWh, SOC, fuel); `starts`, `running_steps`, `soc_end_pct`, `fuel_end_l`, `min_soc_pct` equal the
  trajectory's; status COMPLETED; the hand anchors.
- **T2 parity, K-START; T3 parity, K-STOP; T4 parity, K-RES; T5 parity and clipping, K-CLIP:** as T1 against each
  case's own kernel trajectory; T3 also `stop_source == "SETTING"`, `stop_soc_pct == 60`; T4 `reserve_source ==
  "SETTING"` and `reserve_soc_pct == 25` asserted from the request, and only the step fields, `starts`, `running_steps`, SOC and fuel
  compared with the kernel run (whose reserve is a baseline, so `reserve_source` cannot match it; D-0K1.11); the anchors of §3.
- **T6 refusals**, each its own case on K-BASE's run and request with one change, asserting `code` and `subject`:
  95 PV values (`REPLAY_SERIES_MISALIGNED`, `pv`); `load-mill` left out (`REPLAY_ADDRESS_UNKNOWN`, `load-mill`); an
  extra `load-pump` (`REPLAY_ADDRESS_UNKNOWN`, `load-pump`); `load-res` twice (`REPLAY_ADDRESS_UNKNOWN`, `load-res`);
  PV `None` at offset 50 (`INPUT_GAP`, `pv@50`); `load-mill` `None` at 50 and PV `None` at 55 (`INPUT_GAP`,
  `load:load-mill@50`); PV −1 at 0 (`REPLAY_SERIES_INVALID`, `pv@0`); PV 51 kW at 0 (`REPLAY_SERIES_INVALID`); stop 35
  and stop 101 (`POLICY_BAND_INVALID`, `stop`); stop 36 accepted; reserve −1 and 101 (`POLICY_BAND_INVALID`,
  `reserve`); SOC 101, fuel 401, generator `RUNNING` (`REPLAY_START_STATE_INVALID`, `soc`, `fuel`, `generator`; the `generator` case constructs its request, so the contract does not refuse it, D-0K1.18); a
  `daytime-mini-grid` run and a `mini-grid` v4 run (`REPLAY_MODEL_UNSUPPORTED`); a BLOCKED Draft (prolonged with a
  required parameter removed by `document_edit`, the way `kobo.py`'s callers make one; `REPLAY_RUN_NOT_EXECUTABLE`);
  95 PV values and stop 35 together (`REPLAY_SERIES_MISALIGNED`: step 4 before step 8). Each asserts the stub
  `execute_fn` was never called.
- **T7 failure:** `HostForwardReplay(execute_fn=stub)` where the stub runs the kernel then returns
  `dataclasses.replace(t, outcome="FAILED", failure=ExecutionFailure("PHYSICAL_RESOLUTION_FAILURE", "x", "y"),
  boundaries=t.boundaries[:41])`: no exception; status FAILED; `failure_kind` set; 40 steps; `soc_end_pct`,
  `fuel_end_l`, `fuel_burned_l` `None`.
- **T8 determinism:** the same request twice gives equal projections; two requests differing only in `case_id`
  give the same `replay_identity` (the run ID is outside the identity, `trajectory.py:21-24`); a stop setting
  changes it.
- **T9 seam:** `isinstance(HostForwardReplay(), ForwardReplayPort)`; `FORWARD_REPLAY_REFUSALS` is disjoint from
  `LAB_CONTROL_REFUSALS` and `EXECUTION_FAILURE_KINDS`; every value reachable from a projection (recursing into
  tuples and `ReplayStep`) is a `Fraction`, `int`, `str`, `bool` or `None`, and no value's type has a `__module__`
  starting `assetops_simulator`.
- **T10 pins:** `STOP_OVERRIDE_FIELDS` equals the stop-60 run's frozen stop-override row on `(state_key,
  canonical_unit, dimension, shape, requirement)`; `RESERVE_OVERRIDE_FIELDS` equals the overcast run's reserve row on
  the same fields; a built plan for K-STOP holds exactly one forcing at the stop address, `[0, 480)`; `RESERVE_OVERRIDE_FIELDS` is T10's drift guard only (D-0K1.16); a plan on the stop-60
  run itself with `stop_soc_pct=Fraction(70)` holds exactly one forcing there, value 70; a plan with no
  settings holds none at the stop or reserve address; every non-replaced forcing, cause and initial value of the base
  run is in the plan unchanged; K-BASE's plan has fewer irradiance forcings than steps (run-length merge).

`contracts/tests/test_0k1_forward_replay_contract.py`: a `float`, an `int` and a `Decimal` in each numeric request
field raise `TypeError`; `case_id` `"Bad Id"`, `""` and a 41-character id raise `ValueError`; a projection with
status `FAILED` and no `failure_kind`, or `COMPLETED` with one, raises `ValueError`; `ForwardReplayRefused("NOPE",
"", "")` raises `ValueError`; `ReplayStartState(Fraction(40), Fraction(300), "RUNNING")` constructs (the refusal is T6's, D-0K1.18); the module imports only the standard library (an `ast` scan).

`backend/tests/test_0k1_replay_port_seam.py`: `runs/replay_port.py` imports exactly the four modules of §2.2 (an
`ast` scan); `LabExecutionPort`'s public method names equal `{"projection", "start", "step", "run_to_end",
"registered_stage", "staged_envelopes", "history", "advance_publication", "publication_schedule",
"gateway_diagnostics", "release_registered", "registered_delivery"}` (unchanged, D-0K1.1); no file under `backend/`
names `forward_replay` outside `runs/replay_port.py` and this test.

**Run count (packet records it; D-0K1.13):** about 20 kernel executions of 96 steps: 8 kernel runs for the expected values (K-BASE x3, K-START, K-STOP, K-RES at 25 and at 30, K-CLIP), 8 replays, 1 in T7, 3 in T8; T6 and T10 execute none.

**Regression:** `host/tests/test_mini_grid_v5.py`, `host/tests/test_lab_execution.py`, `backend/tests/test_run_execution_api.py`;
the dependency-direction guard; check-all (fast) once at the end; `python tools/select-tests.py --base main` before
review.

**Guard shown failing** (packet, exit code and message each): a scratch copy with `from host.forward_replay import
HostForwardReplay` added to `runs/replay_port.py` fails `tools/checks/dependency-direction.ps1`; a scratch copy with
`from assetops_simulator.kernel.execute import execute` in `contracts/assetops_contracts/forward_replay.py` fails it.

## 5. Units

| Unit | Content | Commits |
|---|---|---|
| 1 (1.0) | §2.1 contract, §2.2 port, §2.3-§2.4 `replay_inputs` and the plant; contract tests; T6, T9 (static parts), T10; backend seam test | 1 |
| 2 (1.5) | `HostForwardReplay`, §2.5 `project`; T1 to T5, T7, T8 | 1 |
| 3 (0.5) | the guard's two failing runs; regression; check-all; packet | 0 to 1 |

Total 3.0. Packet: `specs/0K1-forward-replay-port/packet.md` (pre-flight print, the K-BASE totals observed, the two
guard runs, the mid-build count).

## 6. Done (questions; each can fail)

1. Does a replay of K-BASE's own recorded series reproduce every step of the kernel's trajectory exactly, under v5
   and v7?
2. Do K-STOP and K-RES equal the kernel's own runs under the changed setting, so a setting is applied by the kernel's
   own override mechanism and by nothing the adapter computes?
3. Does K-START prove the start state is the request's, and K-CLIP that a clipped step changes no dispatch and is
   listed?
4. Is every refusal of T6 given with its code and subject before anything executes, and a kernel failure returned as
   a FAILED projection?
5. Does no simulator type, irradiance value or event list cross the port, and is `LabExecutionPort` unchanged?
6. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 7. Out of scope

The calibration rule (±5% generator kWh, ±10% starts, 5 points SOC MAE; `REPLAY_NOT_CALIBRATED`), the 61-day window,
`SAMPLE_TOO_SHORT`, the dawn bound at 05:00 local, the candidate grid, litres to money, and reading series from
product readings (all `0K2`); a gap-fill rule (D-0K1.5); a demand-on-headroom replay (`0M`); composing the port in a
process (`0K2`, `6c`); any screen or served text; the start threshold as a setting (not on the design's grid); a replay on a step other than 5 minutes (the window form is whole-interval, so it holds, but no test runs it, D-0K1.17); a tank refill or any tank cause that could clip at capacity (D-0K1.14).

## 8. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 | A clipped step: refuse or flag? | Flag (D-0K1.4): dispatch is identical under the inversion; the irradiance itself never leaves the adapter |
| Q2 | Short gaps (≤ 20 minutes) in a series | Refused in 0K1 (D-0K1.5); `0K2` rules a fill, if any, on real series |
| Q3 | Should the port extend `LabExecutionPort`? | No: a separate one-method port (D-0K1.1) |
| Q4 | Which model versions replay | mini-grid v5 to v7 (D-0K1.3); a later version joins by one line and T1 |
