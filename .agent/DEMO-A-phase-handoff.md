# DEMO-A phase handoff

Sources: `AssetOpsV1-plan2\.agent\build-sheet-DEMO-SPARSE.md` (wins where it differs) over
`build-sheet-DEMO-COMBINED.md` (rev 1 + Addendum 1). Branch `task/DEMO-A-combined-dataset`.

## State (2026-10-31, DEMO-SPARSE)

- Pre-flight + Q1 ruling (demo configurations re-timed to Kobo commissioning): `.agent/DEMO-SPARSE-preflight.md`.
- **U1 probe: done**, `.agent/DEMO-SPARSE-trial-probe.md`. normal = necessary-run; overcast = necessary-run
  (daytime-overcast refused the 8 h interval); overuse = reserve-trial; Kobo degraded = first-half delivery
  (degraded-evidence refused under v4). Trial hour (a) 06:00, cost check `MODELLED_NO_IMPROVEMENT` 0 USD. Reported.
- **U2: built** `tools/demo_story_days.py` (`load`, `resolve`, `DayRun` + `known_at`, `plan_add_day`),
  `backend/conversions/demo-story-days-v1.json`, `prepare --days`, `<work>/days.json` (`days` + `doc`), story v2
  (install S-29d 11:00, import -1 h, price +1 h), Kobo cap 80 s/run + 60. Tests `backend/tests/test_demo_story_days.py`.
- **U3: built** `tools/demo_combined_kobo.py`: `configure_at` (Q1), `run_day`, `publish_first_half`, `_trial_chain`,
  `kobo.json` `days[]` + `configuration`. Dev prepare `--sites kobo` on `assetops_demo3_dev_test` / `var/demo3_dev`.
- **U4: in progress**: `add-day` command (`demo_combined.py`, `.busy` lock, delivered-days query), Kobo child
  `add-day`; `links` lists story days + boards S/S-7/S-28; `serve` prints next-day `add-day` commands.
- U5 (cold, EV on the day list), U6 (self-check child `tools/demo_combined_finish.py`, slow build test, register
  R615/R616/R618, carry-over R535/R552/R569/R595): not started.

## Resume notes for U5 (from DEMO-A Explore)

- Cold: `test_w502_cold_scenario_producer.ShiftedChain.open` (:73-108) reads DB now (:79), calls
  `producer.shifted_case` (:80); install = start - 4 h, setup = start - 1 h (:82). Thread `story_day`/`install_at`/
  `scenario_path` through `target_delta` (`tools/w502_cold_work_cases.py:69`), `shifted_case` and `ShiftedChain.open`.
- EV: `Chain.open`'s `now=lambda: "2026-10-06T07:00:00Z"` (test_w205b :258-263) -> swap `registered.RunSetupService`
  (w601 swap pattern `tools/w601_seed.py:529-545`); shifted scenario via `open(scenarios=..., scenario_id=...)`;
  `native_replay` guard `tools/w504_ev_work_walkthrough.py:122-124` needs `window=`.
