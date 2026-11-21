# 0K1 reviewer guide

Architect (Claude), 2026-11-21, rev 2 (handshake round 1, D-0K1.10 to D-0K1.18). Discovery review (W5): a new port across the product/simulator seam. Read
`spec.md`, `rulings.md`, then the diff. Done means every question of spec §6 answers yes with evidence and every plant
below fails its named test.

## What to check, and how

1. **Independent expected values (W2).** T1 to T5 compare the adapter's projection with values the test reads from
   the kernel's own trajectory with its own reader (`recorded_request` and the step reader in the test file). A test
   that builds its expected values by calling `project`, `replay_inputs` or any adapter helper is High.
2. **Nothing computed beyond the inversion.** Read `host/forward_replay.py`: the only arithmetic on physical values
   is `1000 × kW / rated`, the tank identity and sums for the totals. A start threshold, reserve rule, SFC or
   dispatch rule in the adapter is High (D-0K1.2).
3. **Settings by the kernel's mechanism.** T10 shows one whole-interval override per setting and none without;
   T3 and T4 equal the kernel's own changed-setting runs.
4. **The order of checks.** `replay_inputs` against spec §2.4 step by step; T6's two-fault case; the stub
   `execute_fn` never called on a refusal.
5. **Seam.** `git diff main...HEAD --stat` lists only spec §0's six new files; `execution_ports.py`,
   `execution_adapter.py`, `simulator/` and every guard unchanged; T9 and the backend seam test pass; the packet shows
   the dependency-direction guard failing twice on scratch copies.
6. **Exactness.** No `float(` and no `round(` in the three new modules; the contract test refuses each non-`Fraction`.
7. **Pre-flight print.** The packet's print matches the addresses and state keys the adapter uses.

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Fails |
|---|---|---|
| P1 | irradiance from the inverter limit instead of the rated power | T1 (steps with PV below the limit) |
| P2 | load series matched by position, not `load_id` (the test reader emits loads in reverse sorted order and K-BASE's three load series are pairwise unequal, D-0K1.10) | T10 (per-load forcing by id) and T1 (per-load served power, D-0K1.19, D-0K1.21) |
| P3 | the stop setting ignored | T3 |
| P4 | the reserve setting applied to the start threshold instead of the reserve forcing | T4 (K-RES at 32, D-0K1.20) and T10 |
| P20 | `RESERVE_OVERRIDE_FIELDS.dimension` changed | T10 (drift guard only; T4 is the acceptance proof, D-0K1.16) |
| P21 | `generator_state` validated in `ReplayStartState.__post_init__` | contract test (`"RUNNING"` constructs) and T6 (a refusal code is expected) |
| P5 | the base run's start SOC kept | T2 |
| P6 | the base run's own stop-override forcing kept beside the setting (a stop-60 base replayed at 70) | T10 (one forcing at the stop address) |
| P7 | a `None` read as 0 | T6 (`INPUT_GAP`) |
| P8 | a clipped step refused | T5 |
| P9 | `clipped_offsets` empty on K-CLIP | T5 |
| P10 | a FAILED trajectory raised as `ForwardReplayRefused` | T7 |
| P11 | the projection carries the `PrivateTrajectory` (an extra field) | T9 |
| P12 | `forward_replay` added to `LabExecutionPort` | backend seam test |
| P13 | `runs/replay_port.py` imports `host.forward_replay` | dependency-direction guard; backend seam test |
| P14 | a `float` accepted in `pv_available_kw` | contract test |
| P15 | `REPLAY_MODELS` gains mini-grid v4 | T6 (v4 run accepted) |
| P16 | the series-length check after the settings check | T6 two-fault case |
| P17 | `starts` counted as RUNNING steps | T1 (`starts` against the trajectory's transitions) |
| P18 | `fuel_burned_l` as kWh × 0.3 in the adapter | T1 passes but review item 2 is High; T7 (`fuel_burned_l` must be `None` on FAILED) |
| P19 | `replay_identity` built from `case_id` | T8 |

7b. **Tank bound.** `fuel_burned_l`'s docstring carries the capacity/empty-bound note (D-0K1.14); missing is Low.

## Not findings


No calibration rule, no 61-day window, no dawn bound, no gap fill, no money (spec §7, `0K2`). No caller composes the
port (D-0K1.1). A tank refill or cause (D-0K1.14) and a non-5-minute replay (D-0K1.17) are unproven by design. Clipped steps replay (D-0K1.4). K-RES's `reserve_source` is asserted from the request, not compared with the kernel (D-0K1.11). No served text (D-0K1.8).
