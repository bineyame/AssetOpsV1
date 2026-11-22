# 0K4a packet: `mini-grid` v8, the generator takes the load

Implementer (Claude), 2026-11-21. Branch `task/0K4a-dispatch-v8` (base `main` `b96d5e978`, `main` merged at
`68a4ba6c0` with 0K4b before commit 3). Spec `spec.md` rev 2; rulings D-0K4.2-6, D-0K4.19, D-0K4.20, D-0K4.22.
Evidence: `/opt/assetecon/evidence/0K4a/commit3/` (plants, data, regression logs). `USER_REVIEW_REQUIRED: false`.

## Pre-flight print (on `main` `b96d5e978` plus only `host/tests/trajectory_digest.py`)

- v7 8-day Kobo season: COMPLETED, 2305 boundaries, digest `8eb9c44c38f31a77a8faf6e7e9f90fd2c62112dbe0d01c6a3243b7dae783f280`
  (N9's literal).
- Day 4 05:00 local (offset 6060): SOC `28243/912` (30.97 %), generator RUNNING (D-0K2.17's fault reproduced).
- Addresses: `battery-ac-power@battery-pcs`, `pv-ac-power@pv-inverter`, `pv-available-power@pv-inverter`,
  `generator-output-power@generator`, `battery-charge-requested-power@battery`, `battery-discharge-capability@battery-pcs`,
  `load-requested-power@load-{clinic,mill,res}`, `load-served-power@load-{clinic,mill,res}`.

## Commits

1. `819c922e0`: §2.1 extraction, §2.2 `cycle_charge_split`, `trajectory_digest.py`, S1-S10, N9.
2. `d85e42c97`: §2.3 `decide_v8`, `simulator/tests/test_decide_v8.py`.
3. `55ac62647` to head: §2.4 `_resolve_cycle` / `resolve_v8` / `prepare_v8`, §2.5 the version (simulator,
   backend `MODEL_PROFILES`, `EXECUTABLE_MODELS`, `REPLAY_MODELS` with its N11 comment, `kobo.py` tuple entry), §2.7
   the SC-1 statements, cases and the `run_profile_summary` seam; N1-N8, N10-N13, W1-W2, G1-G2 (`55ac62647`); N7's 37 %
   run (`2a8e20cb8`); N13 window and T8 (`1c15e98b4`); N13b (head).

## Files (commit 3)

`simulator/assetops_simulator/packs/mini_grid.py` (v8 section after `decide_v8`), `backend/assetops_backend/runs/
profiles.py` (`ModelProfile.statement: str | Message`, `MINI_GRID_V8_MODEL`, row after v7),
`backend/assetops_backend/simulator_lab_api.py` (`served_text` on the two statement reads),
`backend/assetops_backend/i18n/statements/en/model_profile.py`, `backend/tests/statement_cases/model_profile.py`,
`host/execution_adapter.py`, `host/forward_replay.py`, `host/tests/kobo.py` (import plus one tuple entry),
`host/tests/test_0k4a_dispatch_v8.py`, `backend/tests/test_0k4a_profile_words.py` (new),
`simulator/tests/test_cycle_charge_split.py` (G1-G2 appended), `backend/tests/test_sc1_statements.py` (T8 keys),
`backend/tests/test_0k4b_properties.py` (P4: see
deviations). Nothing under `config/`, `contracts/`, `runs/replay_study.py`, `tools/checks/`; no baseline or allow entry.

## 0K4b review notes, handled

- `fuel_curve` and a rating at or below 0: v8 calls it only through `_checked_curve`, which refuses `rated <= 0` with
  `PHYSICAL_RESOLUTION_FAILURE` at `generator-rated-power@generator` (the Foundation handler already refuses it; this is
  the second wall). Test G1; plant (guard removed) fails G1 with the division.
- `output_cap_kw` and `minutes == 0`: called only through `_fuel_cap_kw`, which refuses a segment of no length.
  (`_segments` never makes one: its cuts are a sorted set.) Test G2; plant fails G2.

## N1's night (overcast day 0; `run8(2)`; full table in `data.log`)

| local | state | SOC % | gen kWh | battery AC kWh | PV curtailed |
|---|---|---|---|---|---|
| d0 18:20 | STARTING | 34.78 | 0 | +1.583 | 0 |
| d0 18:25 | RUNNING | 33.94 | 3.333 | -1.750 | 0 |
| ... 50 steps, SOC rising every step ... | | | | | |
| d0 23:00 | RUNNING | 89.64 | 3.083 | -2.500 | 0 |
| d0 23:05 | STOPPED | 90.83 | 0 | +0.583 | 0 |

The generator starts at 34.78 % (the effective start 35), carries the load at 40 kW and charges the battery at up to
the PCS limit (2.5 kWh a step), never discharges beside it, and stops at 90.83 % after 4 h 40 min.

## Model-change reconciliation (both SIMULATED; D-0K4.11)

Day 1, 05:00 local, the dawn after the overcast day, same inputs: **v7 30.53 % (`9281/304`)**, **v8 74.29 %
(`677533/9120`)**. v7 serves the night from the battery beside a running generator; v8 charges it. No design value.

## N5 and N8

- N5 (`site_stop_pct=100`): one exact step, d0 10:55, SOC 99.997 %: generator `1` kWh (12 kW), PV AC 1.506 below
  available 1.55 kWh (curtailment). Every other RUNNING step delivers at least 1 kWh or notes "below minimum load".
- N8 (N1's run): 108 STARTING or RUNNING steps, 1042/3 kWh; tank fall `21049/200` L = `33/600 x 5 x 108 + 2175/10000 x
  1042/3` exactly; COMPLETED; every step notes `CURVE_FUEL_NOTE` and never `LINEAR_FUEL_NOTE`.

## Digests

- N9 (v7, 8 days): `8eb9c44c38f31a77a8faf6e7e9f90fd2c62112dbe0d01c6a3243b7dae783f280`, unchanged.
- **N12 (v8, 8 days):** `d6add2a3a4ee4f802c2820a772717718c8ca381d0e02d1269d2ea68df5371f11`.
- N11: replay of v8 on N1's observed series: 576 steps, `generator_kwh` within 1 % of the site run's 347.33 kWh.

## Done (spec §5)

1. Yes: N1, N2. 2. Yes: N4 (10/3, +5/2, 5/12 kWh per step), N13. 3. Yes: N5. 4. Yes: N6, N6b, N7. 5. Yes: N8.
6. Yes: N9, N12, N11, regression below. 6b. Yes: W1, W2; `git diff main -- tools/checks/` empty; no baseline entry.
7. Plants below, each failing; mid-build count 7 (2 dispatched, 5 found), see deviations.

## Plants (each reverted; `plants.log`)

| # | Fails | # | Fails |
|---|---|---|---|
| P1 | N3 and commit 2's four reorder cases; **not N2** (finding) | P10 | N11 |
| P2 | S4, S10, S8 (commit 1) | P11 | N7 (with the 37 % run, deviation 3) |
| P3 | S1 (commit 1), N4 | P12 | S10, S8 (commit 1) |
| P4 | S4, S5, S10, S8 (commit 1), N5 | P13 | N13b (passes N13, deviation 5) |
| P5 | S5, S8 (commit 1) | P14 | N8 |
| P6 | N6b | P15 | N12 |
| P7 | N8 | P16 | W1 |
| P8 | N8 | G1, G2 | G1, G2 |
| P9 | as worded, behaviour-neutral (`_add_v3_measures` sorts); as a value swap, N9 (commit 1) | | |

## Checks

All logs are in `/opt/assetecon/evidence/0K4a/commit3/`. Host tests ran through `run-host-tests.ps1`, and every job
went through `heavy-slot`.

- `pytest simulator/tests` (whole) at `2a8e20cb8`: **565 passed** in 12.9 s (`sim.log`). Later commits touch only host
  and backend tests.
- Host regression at `2a8e20cb8` (`test_0k4a_dispatch_v8`, `test_0k1_forward_replay`, `test_0k2_kobo_season`,
  `test_registered_kobo_execution`, `test_mini_grid_v7`, `test_s6_verification_replay`, `test_0k4b_kobo_assumed`):
  1 failed, 80 passed in 255 s. The failure was N13, deviation 4 (`host.log`). After the fix, at head,
  `test_0k4a_dispatch_v8.py` gives **15 passed** (N1-N13b; `host-0k4a-rerun.log` plus `n13b.log`).
- Backend, no database (`test_0k4a_profile_words`, `test_0k4b_properties`, `test_sc1_statements`,
  `test_component_properties`, `test_addressed_bindings`, `test_k1_kisiwa_fixtures`): 1 failed (T8, deviation 7) and
  610 passed. After the fix, `test_sc1_statements` plus `test_0k4a_profile_words` give **393 passed**
  (`backend-rerun.log`).
- `check-all` (fast) at `1c15e98b4`+N13b: **All 42 guards passed** (blocking; 0 advisory, 0 warned), 144 s (`check-all.log`).
- `tools/select-tests.py --base main` selects 300 of 588 backend files for the container suite. This was **not run**:
  that suite needs the database and Docker, which this dispatch does not allow. It is for the coordinator to schedule
  (`select-tests.log`).
- `git diff main -- tools/checks/ config/ contracts/ backend/assetops_backend/runs/replay_study.py`: empty.

## Known deviations and mid-build count (2 dispatched + 5 found = 7)

Dispatched with commit 3:
1. **Commit 2's generator-only reorder.** `decide_v8` on `battery, pv, generator` gives `generator, battery, pv`: only
   the generator moves, as §2.3 words it. Kobo's order is unaffected.
2. **The extra file `simulator/tests/test_decide_v8.py`** (commit 2's "own pure test", not in §0's list).

Found in commit 3 (each a question for the Architect; the build took the reading named):
3. **N7 gains a 37 % stop run.** In N1's and N5's runs the charge from 35 % to the stop takes hours, the 30-minute
   runtime never binds, and P11 passed N7. With a 37 % stop the generator reaches it within two running steps, and the
   runtime holds it on: P11 now fails N7. N1 and N5 are unchanged.
4. **N13's "all night" read as [60, 90).** With res 25 and clinic 10 kW forced over [0, 360), the battery charges at
   only 5 kW before 01:00. It reaches its reserve inside the window (01:20: battery AC `3019/1600` kWh, the reserve
   limit acting correctly), so "N4's per-step figures hold on [65, 90)" cannot be true. The build forces res and
   clinic over [60, 90) (N4's SOC history), so the view at 60 sees 35 kW and the mill joins at 62.
5. **N13b added.** On N13's fixture, P13 passes, because v7's end-of-step rule adds the same "differed" note whenever
   nothing else limits. N13b (res 5 kW from 60: a 35 kW charge request against the 30 kW PCS limit, then the mill from
   62) has another limit on the step, so only v8's note can carry it. P13 fails N13b. Figures: unserved `1/4` kWh,
   battery AC `-1` kWh.
6. **`backend/tests/test_0k4b_properties.py` P4** asserted the curve needs are "on no profile yet" and that every
   `model_profile` case is a need. It now excludes `mini-grid` v8 and filters the cases by key.
7. **`backend/tests/test_sc1_statements.py` T8** pins the shipped statement keys. It gains `model_profile.description`
   and `model_profile.state` (0K4b made the same adopter edit).

Finding, not a change: **P1 does not fail N2.** While RUNNING, the resolver's split discharges only in branch 1
(`D > A + R`), whatever the view requested, so N2 holds by the physics. P1 fails N3 and commit 2's four reorder cases.

## Residual risk

- N5's exact set has one step on this fixture (d0 10:55). The precondition holds and nothing was tuned.
- v8 is on no world yet (0K4f), and calibration is 0K4d's.

## Review focus

`_resolve_cycle` against `resolve` (the eight marked `0K4a §2.4 (n)` changes, the `allocate` closure, the fuel rerun);
the two guards; `MINI_GRID_V8_MODEL` relations and handlers; W2's main digest.
