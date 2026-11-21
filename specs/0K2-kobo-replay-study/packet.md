# 0K2 review packet: the Kobo replay study on a simulated season

Branch `task/0K2-kobo-replay` (base `15c5b07b6`; the spec names `task/0K2-kobo-replay-study`, the dispatch named this
one). Commits: unit 1 `959270aff`, unit 2 `aa7ec751e`, unit 3 `56bbefdf0`, closeout (this packet, state). Spec rev 2,
rulings D-0K2.1-29. No database, no migration, no served text. `USER_REVIEW_REQUIRED: false`; the figures go to the
owner beside the design values (D-0K2.13, rows 37 and 42). Evidence: `/opt/assetecon/evidence/0K2/`.

## Pre-flight (8 days, v7; `preflight/preflight.txt`)

READY; base-run forcing addresses = season addresses = {irradiance, load-res, load-clinic, load-mill} (base 4/2/1/3
forcings, season 104 each); 2,304 steps; start 48 %, 15,000 L, STOPPED. Site: 943.48 kWh, 7 starts, 1,023 running steps,
min SOC 30.0, fuel 283.04 L (the Architect's probe: 959.56 kWh, 287.87 L; status and address set agree, figures are
outputs). SOC at 02:00Z (05:00 local), days 0-7: 34.84 STARTING, 35.26 STOPPED ×3, 30.97 RUNNING (day 4, after the
overcast day 3), 35.26 STOPPED ×3.

## Files

New: `backend/assetops_backend/runs/replay_study.py`, `backend/tests/test_0k2_replay_study.py`,
`host/tests/kobo_season.py`, `host/tests/test_0k2_kobo_season.py`, `tools/kobo_replay_study.py`. Edited:
`backend/tests/test_0k1_replay_port_seam.py` (allow-list +2 names only). State: `.ai/state/data.md`, `index-2.md`.

## The 61-day study (`season-61/study.json`, `run.log`)

CALIBRATED on SIMULATED input = adapter fidelity (the replay path follows the kernel run that made the series), not a
model-to-Site match. Calibration, 61 admissible days: generator kWh site 7,418.143 / replayed 7,418.679; starts 46 / 46;
SOC MAE 0.0214 points; failed (). Clipped days 46 (kept). Timing: `--time-one` site 117.7 s, replay 80.3 s; cap
`max(25, ceil(2 × (117.7 + 15 × 80.3)/60))` = 45 min; full run 16 kernel runs of 17,568 steps, wall 23 m 43 s (site
119.7 s, 15 replays 1,302.7 s, about 87 s each), exit 0.

Season replay (SIMULATED, MODELLED); site (simulated) = the baseline row, which equals it within T11's bounds. Litres
and kWh: Sep (30 d) / Oct (31 d) / scaled to 30 days (window × 30/61). Added starts are 0 and unserved energy 0 in every
case; dawn below 35 % is 16 of 61 in every case.

| case | fuel L | avoided L Sep / Oct / 30 d | added throughput kWh Sep / Oct / 30 d | running steps | min SOC | worst dawn |
|---|---|---|---|---|---|---|
| baseline (site, simulated) | 2,225.6 | - | - (throughput 8,967.4) | 8,215 | 30.00 | 30.97 |
| 90-30 | 2,225.6 | 0 / 0 / 0 | 0 / 0 / 0 | 8,215 | 30.00 | 30.97 |
| 85-30 | 2,201.0 | 12.3 / 12.3 / 12.1 | 0 / 0 / 0 | 8,031 | 30.00 | 30.97 |
| 80-30 | 2,147.5 | 39.1 / 39.1 / 38.4 | 0 / 0 / 0 | 7,817 | 30.00 | 30.97 |
| 75-30 | 2,101.2 | 62.3 / 62.1 / 61.2 | 0 / 0 / 0 | 7,632 | 30.00 | 30.97 |
| 70-30 | 2,055.2 | 85.3 / 85.1 / 83.8 | 0 / 0 / 0 | 7,448 | 30.00 | 30.97 |
| 65-30 | 2,005.5 | 110.1 / 110.1 / 108.3 | 0 / 0 / 0 | 7,249 | 30.00 | 30.97 |
| 60-30 | 1,959.5 | 133.1 / 133.1 / 130.9 | 0 / 0 / 0 | 7,065 | 30.00 | 30.97 |
| 90-25 | 2,129.7 | 47.6 / 48.3 / 47.2 | 37.5 / 39.6 / 37.9 | 7,510 | 25.00 | 25.53 |
| 85-25 | 2,115.8 | 54.6 / 55.2 / 54.0 | 37.5 / 39.6 / 37.9 | 7,325 | 25.00 | 25.53 |
| 80-25 | 2,083.1 | 71.1 / 71.4 / 70.1 | 37.5 / 39.6 / 37.9 | 7,141 | 25.00 | 25.53 |
| 75-25 | 2,037.1 | 94.1 / 94.4 / 92.7 | 37.5 / 39.6 / 37.9 | 6,957 | 25.00 | 25.53 |
| 70-25 | 1,979.9 | 122.6 / 123.2 / 120.9 | 37.5 / 39.6 / 37.9 | 6,728 | 25.00 | 25.53 |
| 65-25 | 1,933.9 | 145.6 / 146.2 / 143.5 | 37.5 / 39.6 / 37.9 | 6,544 | 25.00 | 25.53 |
| 60-25 | 1,887.6 | 168.8 / 169.2 / 166.2 | 37.5 / 39.6 / 37.9 | 6,359 | 25.00 | 25.53 |

Design value (unchanged, still labelled design; §4.2): stop 70 avoided 210 L a month, 0 of 61 dawn days, 150 kWh added
throughput a month; reserve 25 avoided 20 L a month, 4 of 61 dawn days. Season, same bases: stop-70-reserve-30 85.3 /
85.1 / 83.8 L, 16 of 61, 0 / 0 / 0 kWh; reserve 25 at stop 90 47.6 / 48.3 / 47.2 L, 16 of 61. Throughput excludes PCS
losses (D-0K2.11). The overcast day's evening reserve override (15 % from 16:00) is left out of the season, its effect
not estimated (D-0K2.22): it bears on the reserve-25 figures and the after-overcast dawns.

## Dawn (D-0K2.17)

Cause, the shipped dispatch law (`packs/mini_grid.py` docstring): sources serve load in the Site's order PV, battery,
generator, and the generator charges the battery only while the battery is not discharging. Once a night's charge falls
to the effective start, min(35, 30 + 5) = 35 %, the generator starts but the battery keeps serving first, down to the
reserve, and dwells just above it until PV returns. The stop threshold is never reached at night. The dawn limit equals
the effective start, 5 points above the reserve. This is the model as written on the Site's settings, not a claim about
Kobo's real controller.

Every case, the baseline included, fails the absolute bound: the same 16 dates in each, so `new_dawn_days_below` and
`cleared_dawn_days_below` are () for all 14 cases. Failing dawns: 1 Sep 34.84 (`window-start`, the declared 48 %
crossing 35 % at 04:55; STARTING in reserve-30 cases, STOPPED in reserve-25) and 5, 9, 13, 17, 21, 25, 29 Sep, 3, 7,
11, 15, 19, 23, 27, 31 Oct (`after-overcast`, RUNNING; 30.97 at reserve 30, 25.53 at reserve 25). No `other`. Least
reading at or above the limit: 35.263 (2 Sep and 44 other dawns), margin 0.263 points; the design's "worst day 2 points
above the limit" is met by no case. Nothing was moved: bound 35 %, reserve, start charge 48 %, calendar and frame as
declared. Row 42 stands: no reserve-30 case can pass under this law.

## Checks

Revision `79434e411`; logs in `regression/`, all through the slot pool and `run-host-tests.ps1`:
- Host `test_0k2_kobo_season.py` + `test_0k1_forward_replay.py`: 47 passed in 77.6 s (0K2 alone first run: 13 passed,
  72.6 s). Backend `test_0k2_replay_study.py` + `test_0k1_replay_port_seam.py`: 29 passed, 2.2 s. Contracts
  `contracts/tests` (`-AllowHostFull`): 190 passed, 66.6 s.
- T11 passed unshifted, with the self-shift precondition (both directions break all three bounds) asserted in the test.
- Seam scan: `scanned > 100` holds; allow-list +2 names. Guard shown failing: a scratch copy of `replay_study.py` with
  `from host.forward_replay import HostForwardReplay` fails `check-architecture.ps1` exit 1, "Banned import of the
  composition leaf in ./backend/assetops_backend/runs/replay_study_scratch.py:33" (`plants/guard-failing.log`).
- `check-architecture.ps1` passed (with `ASSETOPS_GUARD_PYTHON`; without it the chain guard refuses, by design);
  `check-agent-workflow.ps1` passed; check-all (fast): CHECKALL. `select-tests.py --base main`: "full (568 of 568)
  because tools/kobo_replay_study.py"; the full suite is the coordinator's to schedule.
- Plants (`plants/run.log`, throwaway worktree, removed): P1-P31 each fail a named test, except P24, which fails B3
  but not T3 (no case on the 8-day kernel season adds or clears a dawn date, so a swap is invisible there), and P27,
  which first passed B5 (scripted baseline had no throughput or start); B5 now gives the baseline both and fails under
  P27 (`p27-b5-rerun.log`, commit `79434e411`). P32 is a review item (T11's precondition is in the test).

## Known deviations

- `observed_series` takes `start=SEASON_START` (keyword): the trajectory carries no window start; T13 passes its own.
- `StudyFrame` refuses `min_litre_days < 1` (ValueError): a calibration over no step would be vacuous.
- An empty window refuses with subject `day:<local date of the start>` (spec gives no date for `n == 0`).
- Units 1 and 2's backend halves share commit `959270aff` (one module); unit 2's commit carries the fixture and T1-T13.
- Pre-flight figures differ from the Architect's probe (see above); status and addresses agree.

## Review focus

The dawn section; T11's self-shift precondition (asserted in the test); W2 independence of the host reader; the
reserve-30 cases showing zero added throughput (the stop setting changes generator running, not the battery's discharge
in this law). Mid-build questions: 0.
