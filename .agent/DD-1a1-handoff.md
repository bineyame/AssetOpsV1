# DD-1a1 handoff (builder 11: R8 landed; STOPPED at the R8 probe, trial chain)

## Landed
- R8 in `tools/demo_story_days.py` `resolve`: one epoch per maximal run of consecutive built days of a Site (isolated days keep v1 `day-<n>`; a stream takes its first story run's number). Guards LATE_IN_STREAM and BUILT_DAY_AFTER_DEGRADED. `demo_combined_kobo._trial_chain(..., epoch)` takes the trial-before day's stream epoch for baseline and later.
- L0 `test_demo_story_days.py` 33 passed (stream epoch test, guard test; per-day-epoch mutation fails 3 tests). Deviation: mill-midday L0 fixture moved S-2d -> S-5d (S-2d joins the late S-3d day's stream, guard fires).
- `dd1a1_fullday_probe.py stream` (Kobo S-3d, S-1d, S, S+1d with complements) and `tools/dd1a1_r8_check.py <db> stream`. Helper scripts in `C:\Users\assef\dd1a1w\` (env.sh, d12.sh, mkdb.py).

## STOP: R8 probe, trial chain
- Run 1: trial "later" run aborted in `_publish_and_accept` (8 batches, 1067 of 1197 envelopes; one batch IN_PROGRESS 64/194; SSLEOFError from fake_central) - looked like a transport flake. Its data passed r8_check (shared epoch+gateway, sequence 1..N, late receipt, all windows SELECTED_UNIQUE, 0 AMBIGUOUS).
- Run 2 (rerun): delivery fine, but the trial evaluation fails: `BLOCKED:BASELINE_SELECTION_CHANGED:2026-11-04`. Cause (analytic_run_selection): the later run's first reading (source 11-05 03:00Z, same epoch day-1) triggers a new dispatch selection for the 11-04 window (seq 23, 11-05 12:06) after the plan froze the baseline on seq 22. On separate epochs (R5/R7b) no re-selection of 11-04 happened. So sharing the epoch with the trial later run changes the frozen baseline selection; R8 "trial runs take the shared epoch" conflicts with the verification plan. Not tuned. Architect must rule (e.g. later run on its own epoch, or plan freeze after the re-selection).
- Not run: full with/without acceptance builds, R6, R3 five, mill, Q8, Cold failure day, guards, packet. DB dropped, no processes.
