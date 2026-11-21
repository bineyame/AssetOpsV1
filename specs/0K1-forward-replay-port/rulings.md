# 0K1 rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`).
D-0K1.1 to D-0K1.9 are applied by `spec.md` rev 1. None is an owner-level call (none is logged in
`specs/OWNER-AWAY/decisions-2026-11-21.md`); the owner may weigh in on D-0K1.4 on return.

## D-0K1.1 A separate one-method port; `LabExecutionPort` is not touched

- **Ruling.** `ForwardReplayPort` (`runs/replay_port.py`) holds one method, `forward_replay(run, request)`. The Lab
  port and every fake that implements it stay as they are.
- **Why.** Design A5 and `phase-plan-and-acceptance.md` PR 4c: "a **new** port method returning a neutral projection;
  `run_to_end` → `LabProjection` stays untouched (protected seam)". `LabExecutionPort` is `runtime_checkable`; a
  thirteenth method would make every existing implementation fail `isinstance` and every Lab fake grow a stub. A
  replay is not a Lab control (it advances no Draft, writes no artifact), so a separate port is also the more precise
  seam. The backend seam test pins the Lab port's twelve names.

## D-0K1.2 A replay is the base run's frozen world with the request's series, start and settings; nothing else changes

- **Ruling.** The adapter starts from `frozen_world_inputs(run)`, replaces the irradiance, load-demand,
  stop-override and reserve forcings and the three run-start values, and keeps every cause, bound, site control and
  other input. Settings are applied as the kernel's own overrides (`mini_grid.py:358-405` for the stop threshold,
  `minigrid.py:525-545` for the reserve) over the whole interval.
- **Why.** The design's whole argument for the replay is that "the avoidable litres are the difference of two model
  runs on identical inputs, so systematic model error largely cancels" (§4.2). Any arithmetic in the adapter beyond
  the one PV inversion would be a second model. Using the kernel's override mechanism means the shipped stop-60 run
  is an exact oracle for the setting path (T3), and a whole-interval window satisfies the kernel's step-alignment rule.

## D-0K1.3 Only mini-grid v5 to v7 replay

- **Ruling.** `REPLAY_MODELS = {("mini-grid", 5), ("mini-grid", 6), ("mini-grid", 7)}`; others are
  `REPLAY_MODEL_UNSUPPORTED`.
- **Why.** v5 is the reserve-aware start (`effective_start_threshold`) the design's reserve option depends on
  ("lowering the reserve ... lowers the effective start"); v4 added the per-load requested-power measurement the
  projection's unserved energy needs. A replay on v4 or earlier would value the reserve option on a start rule that
  ignores it.

## D-0K1.4 PV-available is inverted to irradiance exactly; a clipped step is flagged, not refused

- **Ruling.** `G = 1000 × kW / rated` (exact `Fraction`). A step whose PV-available equals the inverter limit is
  listed in `clipped_offsets` and replays normally. The irradiance is never in the projection.
- **Why.** The design left it open ("clipped slots are refused or flagged", §4.2; RR1). The kernel passes
  `min(potential, limit)` (`minigrid.py:546`); with `potential = kW ≤ limit` it passes exactly `kW`, so every flow,
  stock and decision is the same as with the true irradiance. Only the reconstructed irradiance (and the inverter's
  clipping measurement) differ, and neither is a decision quantity. Refusing would discard Kobo's sunniest middays
  (60 kW PV on 50 kW AC) and could fail the 14-day sample for no gain. T5 proves the equality on a clipped run.
  `0K2` keeps the flag visible on its calibration report.

## D-0K1.5 A gap is refused; no fill rule in 0K1

- **Ruling.** Any `None` in a series is `INPUT_GAP` with the earliest offset.
- **Why.** The kernel treats a forcing outside its window as unavailable, never zero (`minigrid.py:513-522`); a
  silent fill would be an invented series. The design's 20-minute rule is a property of real series and belongs to
  `0K2`, which reads them; it will be its own ruling with its own test.

## D-0K1.6 The projection is neutral and MODELLED; a kernel failure is a FAILED projection

- **Ruling.** `ForwardReplayProjection` carries only `Fraction`, `int`, `str`, `bool`, `None` and `ReplayStep`; it is
  `MODELLED`; fuel burned is the tank identity (start − end ± declared causes). A failure inside the kernel returns
  `status="FAILED"` with its kind; only a judged request is a refusal.
- **Why.** `execution_ports.py`: "Nothing simulator-shaped appears in either direction". The same separation the Lab
  port keeps between a refusal ("nothing was executed") and an execution that started and stopped. Fuel from the tank
  stock rather than kWh × SFC keeps the adapter free of physics (the kernel's linear law is checked by T1's anchor,
  not re-implemented).

## D-0K1.7 The proof is exact equality with the kernel's own trajectory; calibration is 0K2's

- **Ruling.** T1 to T5 assert equality of `Fraction`s, step by step. The ±5% / ±10% / 5-point calibration, the 61-day
  window and `SAMPLE_TOO_SHORT` are `0K2`'s.
- **Why.** `delivery-plan.md` defines 0K1's proof as "replaying a recorded run to the kernel's own trajectory"; the
  reuse matrix row: "replay of the Kobo trial day equals the kernel's own trajectory; then 210 L / 20 L design
  values" (the second half is 0K2). Exact inputs give an exact answer; tolerance is for observed (quantized,
  published) series only.

## D-0K1.8 No user-facing text

- **Ruling.** 0K1 serves and renders nothing. `ForwardReplayRefused.detail` is a developer diagnostic. Any later
  figure from a replay is composed through SC-1 and carries the design-value label until 0K2 passes (decision D6).
- **Why.** D-SC1.28 governs served text; there is none here, so 0K1 neither waits for SC-1a nor adds legacy text.

## D-0K1.9 Exact numbers only at the port

- **Ruling.** Every numeric field of a request is a `Fraction`; a `float`, `int` or `Decimal` is a `TypeError`.
- **Why.** The kernel is exact ("there is no tolerance anywhere", `minigrid.py:38-39`); accepting a float would put
  an unstated rounding at the seam that T1's equality could not see. The caller (`0K2`) converts its stored decimal
  text with `Fraction(text)`.

## Handshake answers (round 1)

Architect (Claude), 2026-11-21, on the owner's delegation. Each question answered once; applied by `spec.md` rev 2 and
`reviewer-guide.md` rev 2. Checked against `main` (`f04648a3d`) by running the kernel on the shipped Kobo scenarios.
No owner-level call arises (nothing is logged in `specs/OWNER-AWAY/decisions-2026-11-21.md`; no authorisation widened).
The handshake has no open question after this.

## D-0K1.10 (R1) The test reader emits loads in reverse sorted order, so a positional match fails

- **Ruling.** The kernel keys its load measurements in sorted order (`mini_grid.py:1058` sorts `interval_energies`), the
  plant's loads are sorted, so a request in the reader's natural order would pass a positional match. The reader in the
  test file returns `loads` in reverse sorted `load_id` order for every case (T1 to T5, T6's base request). K-BASE's
  three load series are asserted pairwise unequal (printed on `main`: 3 distinct), so a mix-up changes the result.
  P2 fails T1 and the guide's P2 row says so.
- **Why.** A plant that cannot fail is no check (W2). Both preconditions are asserted in the test, not assumed.

## D-0K1.11 (R2) K-RES: no setting is the baseline anchor; `reserve_source` is asserted from the request

- **Ruling.** "The replay at reserve 30" is the replay of the unedited reserve-trial request with **no** setting
  (baseline 30), not `Fraction(30)`. K-RES's own replay (setting 25) is compared with the kernel run on a 25 baseline
  only on step fields, `starts`, `running_steps`, SOC and fuel; `reserve_soc_pct == 25` and `reserve_source ==
  "SETTING"` are asserted from the request, since the kernel run's source is a baseline.
- **Why.** The two paths (baseline, setting) are different code; each is exercised once, and no field is compared with
  a value that differs by design.

## D-0K1.12 (R3) v6 stays admitted; T1 runs v5, v6 and v7

- **Ruling.** `REPLAY_MODELS` keeps v6. T1 replays K-BASE under v5, v6 and v7. T2 to T5 run at v7 (the shipped one).
- **Why.** v6 replaces only `resolve` (adds the `battery-charge-requested-power@battery` measurement, `mini_grid.py:1211-1243`),
  so nothing replay-affecting is expected, but "expected" is not proved; on `main` K-BASE gives `starts 1, running_steps
  66` under all three, and T1 makes that a test (three runs of 96 steps, cheap). Dropping v6 would refuse a shipped
  version for no gain.

## D-0K1.13 (R4) Five cases on three scenarios; the run count

- **Ruling.** The summary reads "five cases drawn from three shipped scenarios" (overcast only pins T10's constant). The
  packet records the count: about 20 kernel executions of 96 steps (8 kernel runs for expected values, 8 replays, 1 in T7,
  3 in T8; T6 and T10 execute none).
- **Why.** The review counts the right thing; the count lets the reviewer see no run is skipped.

## D-0K1.14 (R5) A tank cause is out of 0K1's proof

- **Ruling.** `fuel_burned_l`'s identity is exact only while the tank meets neither bound. A run with a tank refill that
  could clip is outside 0K1 (`0K2`'s concern, where Kobo refills appear). The adapter's docstring says so in one line; no
  test; spec §7 and the guide's "Not findings" say so; the guide's item 7b has the reviewer check the line.
- **Why.** No 0K1 case has a cause (printed: `causes 0` for all three scenarios); a test would invent a case. The hand
  anchor `fuel_burned_l == 3/10 x generator_kwh` cross-checks the identity on the no-cause runs.

## D-0K1.15 (I1) Component ids are the printed ones

- **Ruling.** `pv-array`, `pv-inverter`, `battery-pcs`, `battery`, `generator`, `fuel-tank`, `load-res`, `load-clinic`,
  `load-mill`. Printed boundary keys on `main`: `pv-available-power@pv-inverter`, `generator-output-power@generator`,
  `load-requested-power@<load>`, `load-served-power@<load>`; stocks `battery-state-of-charge@battery`,
  `fuel-tank-volume@fuel-tank`. The reader uses those keys (a missing key is a `KeyError` that fails the test); the
  pre-flight prints B[1]'s measurement keys.
- **Why.** The kernel keys PV-available by the inverter (`mini_grid.py:1063`).

## D-0K1.16 (I2) T4 is the acceptance proof of the reserve row; T10's pin is a drift guard

- **Ruling.** `RESERVE_OVERRIDE_FIELDS` stays pinned to the overcast run's reserve row (the only shipped one; the
  reserve-trial run has no reserve forcing, printed). T4 proves the mini-grid models accept it; T10 only catches drift,
  and the spec says so. A plant that changes the constant's dimension fails T10 (P20).
- **Why.** Honest naming of what each test proves; no new shipped fixture for a pin.

## D-0K1.17 (I3) A whole-interval window is aligned at any step size

- **Ruling.** Confirmed: the stop-60 run's row is offset 0, duration 480 at 5-minute steps (printed); the replay window
  is `[0, duration)` with `duration` the interval, so it starts and ends on every step boundary and
  `_stop_threshold_at`'s alignment refusal cannot fire. A replay on a 15-minute step is untested and out of scope
  (spec §7). T10 keeps the stop-60 anchor; T3 proves acceptance.
- **Why.** The check in the kernel is per step; the window is the whole interval, so it is a property of the form.

## D-0K1.18 (I4, I5) Test commands and the generator-state split

- **Ruling.** (I4) The wrapper puts `contracts/` and `backend/` on `PYTHONPATH` and takes any file path; the backend
  conftest routes Postgres tests by file name only, and neither new file is one. The packet's first section records both
  commands and exit lines; if a file is out of the wrapper's reach it records the interpreter command and carries on
  (not a mid-build question). (I5) The contract test asserts `ReplayStartState(Fraction(40), Fraction(300), "RUNNING")`
  constructs; T6's `generator` case asserts the refusal. A plant that validates it at construction fails the contract
  test (P21).
- **Why.** Both halves of the split are pinned, so neither can move without a test failing.
