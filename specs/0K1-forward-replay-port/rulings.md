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
