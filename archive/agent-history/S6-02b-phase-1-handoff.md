# S6-02b phase 1 handoff (reserve-aware model + public VERIFIED replay)

Branch `task/S6-02b-verification-ui`, worktree `AssetOpsV1-review5`. Commits `87dba01b` (v5 model, reserve-trial
scenario, manifest v2 with windows predeclared and committed before the first replay), `2ab56ce0` (expected block
from the replay, v5 model tests, catalog tests). Not merged.

## What landed

- `mini-grid` v5: `simulator/assetops_simulator/packs/mini_grid.py` end of file - `START_HEADROOM_OVER_RESERVE = 5`,
  `effective_start_threshold`, `decide_v5` (start at min(Site start threshold, reserve in effect + 5); stop, minimum
  runtime, start delay, battery request are v4's), `MINI_GRID_V5_COUPLING/MODEL` (resolve_v4 unchanged). v1-v4
  objects untouched. Registered in `backend/assetops_backend/runs/profiles.py` (`MINI_GRID_V5_MODEL`, `MODEL_PROFILES`),
  `host/execution_adapter.py` `EXECUTABLE_MODELS`, `host/tests/kobo.py` profiles (V4 + V5 added).
- Scenario `config/scenarios/kobo-mini-grid-reserve-trial.yaml` v1: SOC 42.5 %, 0 W/m2 first hour then 800 W/m2,
  residential 10 kW + clinic 5 kW, mill 0. Fingerprint pinned (`test_scenario_fingerprints.py`); listed as never
  shipped as v1 in `test_run_binds_scenario_to_site.py`.
- Manifest `backend/conversions/d-verification-window-v2.json`: windows 2026-10-13T06:00Z / 2026-10-15T06:00Z, same
  action/run timing as v1; `expected.why_verified` explains the physics. `host/tests/test_s6_verification_replay.py`
  is parametrized over v1 (v4, INCONCLUSIVE, unchanged) and v2.
- Replay v2 result (real Postgres, gateway, S2): VERIFIED `TARGET_AND_GUARDRAILS_PASS`; Candidate seconds baseline 3600,
  later 0; both windows 12/12 complete, 121 evidence IDs, 74 publication IDs, REGISTERED_SIMULATION with distinct run
  digests; feeder 15 kWh, PV-available 48 kWh, initial SOC 63.105263 = 63.105263, terminal 77.355263 = 77.355263,
  unserved 0, below-reserve 0; events ACCEPTED, APPLIED, RESOLVED. Baseline generator ON 04:05-07:55; later none.
  Why it is honest: the generator delivers no energy in either run (PV surplus saturates the 30 kW PCS charge
  limit), so SOC is identical; the reserve changes only whether the dawn dip (34.6 %) reaches the start threshold.
- `host/tests/test_mini_grid_v5.py` (9): v5 == v4 decisions on the template reserve (both scenarios), lower reserve
  lowers the start and v4 ignores it, unloaded generator leaves SOC unchanged.

## Checks (at `2ab56ce0`)

v2 replay 1 passed (222 s); v5 + v2 model tests 49 passed; profile/catalog/publication/replay-manifest adjacent files
255 passed; `tools/check-all.ps1` all 9 guards passed.

## Next (phase 2)

UI per the packet; walkthrough `prepare` should replay manifest v2 (reuse the replay test's helpers: `_draft`,
`_publish_and_accept`, `LabRunner`) so the served Action is the real VERIFIED one; other cases test-scoped and labelled.
Registry nodes `I-sim-verification-cases`, `D-verification-window` stay `open` until review.

## Open risks

- The baseline generator runs unloaded (0 kW) - physically the "avoidable" runtime, but the walkthrough copy should say
  so plainly rather than imply fuel was burned.
- Replay test costs ~4 min per manifest (two in the full suite).
