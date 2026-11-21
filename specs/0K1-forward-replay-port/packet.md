# 0K1 review packet

Branch `task/0K1-forward-replay` off main `3bdf3c81d`; commits `4d7606a9d` (unit 1), `e5f8c239c` (unit 2), `ea2a1d7ad`
(T10 load check, Q1-Q2), and the bookkeeping commit. `USER_REVIEW_REQUIRED: false`. Discovery review (W5).

## 1. Pre-flight and commands

- Print (spec §0), on this branch: prolonged v5 and stop-60 v5 are READY, 96 steps, `causes 0`. Plant rows:
  `pv-rated-power@pv-array` 60, `inverter-ac-limit@pv-inverter` 50, `fuel-tank-capacity@fuel-tank` 400, start 35,
  stop 90, reserve `battery-reserve-state-of-charge@battery` 30, SOC `battery-state-of-charge@battery` 40, tank
  `fuel-tank-volume@fuel-tank` 300, `generator-state@generator` STOPPED. Forcings: `site:plane-of-array-irradiance`
  (W/m2, IRRADIANCE, WINDOW, REQUIRED; 0/150/450/550 at 0/60/120/240), `load-demand@load-res|load-clinic|load-mill`
  (kW, POWER, WINDOW, REQUIRED). Stop-60 row: `('stop-threshold-override', 'generator-stop-soc-threshold@generator',
  'generator-stop-soc-threshold', '%', 'FRACTION', 'WINDOW', 'REQUIRED')` at 0 for 480, value 60. Overcast
  (daytime-mini-grid/1, 15 min, 48 steps) reserve row: `('evening-reserve-override', 'battery-reserve-state-of-charge@battery',
  'battery-reserve-state-of-charge', '%', 'FRACTION', 'WINDOW', 'REQUIRED')` at 600 for 120. B[1] keys (prolonged v7)
  include `generator-output-power@generator`, `load-requested-power@load-clinic|load-mill|load-res`,
  `load-served-power@...`, `pv-available-power@pv-inverter`. Every address matches the spec.
- Host: `tools/heavy-slot.sh -- pwsh -NoProfile -File tools/run-host-tests.ps1 -- host/tests/test_0k1_forward_replay.py`:
  34 passed. Contracts: the same wrapper on `contracts/tests/test_0k1_forward_replay_contract.py` (with the other two
  contracts files, since the wrapper refuses a directory): included in the run below.

## 2. Acceptance (spec §6)

1. Yes. T1 replays K-BASE under v5, v6 and v7: every step equal. Observed (all three): generator 134 kWh, unserved
   5 kWh, fuel burned 201/5 L (= 0.3 x 134), starts 1, running 66, SOC end 98.875, min 30.
2. Yes. K-STOP (T3): 277/3 kWh, running 41, equal to the stop-60 run. K-RES (T4): running 0 at a 25 setting, equal to
   the kernel's 25-baseline run; the no-setting anchor equals the 30 run (running 46, 0 kWh delivered).
3. Yes. K-START (T2) starts at 55 and equals its kernel run; K-CLIP (T5) equals its run with 48 clipped offsets
   (240 to 475).
4. Yes. T6: 19 refusals with code and subject, the stub `execute_fn` never called; T7 FAILED projection, 40 steps.
5. Yes. T9 (types, disjoint vocabularies), backend seam test (four imports, Lab port's twelve names, no other
   backend file names `forward_replay`).
6. Every plant fails, two in a different test than the guide names (§4). Mid-build count 2.

## 3. Checks (real output)

- Focused + contracts + seam + regression (`test_mini_grid_v5`, `test_lab_execution`, `test_run_execution_api`),
  one wrapper run: `249 passed, 1 warning in 41.44s`, exit 0.
- Kernel executions: 20 (8 expected, 8 replays, 1 in T7, 3 in T8; T6 and T10 none), cached per module.
- `check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` set): passed. `check-agent-workflow.ps1`: passed.
  `check-all.ps1` (fast): `All 40 guards passed`, 1m19s, exit 0.
- `select-tests.py --base main`: selects `backend/tests/test_0k1_replay_port_seam.py` (run on the host here; the
  container tier was not run: no Docker by dispatch).
- Guard shown failing on scratch copies (`git archive HEAD`), `Invoke-DependencyDirectionCheck`, exit 1 each:
  `Banned import of the composition leaf in ./backend/assetops_backend/runs/replay_port.py:21: from host.forward_replay import HostForwardReplay.`
  and `Banned import in the neutral contracts at ./contracts/assetops_contracts/forward_replay.py:26: from assetops_simulator.kernel.execute import execute.`
  The branch itself: exit 0.
- No `float(` or `round(` in the three new modules.

## 4. Plants (reviewer guide), each in the committed tree, reverted after

All 23 runs fail as expected except the two first found: P2 passed T1 and P4 passed T4. P2 now fails T10's new
per-load plan check (re-run: caught); P4 fails T10. Q1 and Q2 in `mid-build-questions.md`: a projection that depends
on loads only through their sum cannot see a positional swap, and the reserve-trial dip never reaches 30 %, so the
two P4 trajectories are identical. Defaults applied (T10 is the catching test); an Architect call is asked.

## 5. Deviations and residual risk

- Unit 1's commit holds the adapter without `project`/`HostForwardReplay`; T6/T10 landed with unit 2 (they call
  `HostForwardReplay`).
- `ForwardReplayRequest` also requires tuples for the series and `LoadSeries.load_id` non-empty (beyond §2.1).
- `ForwardReplayProjection` also validates `stop_source`/`reserve_source` and `evidence_class`.
- Risk: the backend seam test was not run in the container tier.

Review focus: `host/forward_replay.py` `replay_inputs` against §2.4; T10's load check (Q1).
