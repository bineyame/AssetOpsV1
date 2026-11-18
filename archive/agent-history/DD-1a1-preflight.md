# DD-1a1 pre-flight (P1-P6 answered once; questions batched)

- Implementer (Claude Opus), 2026-11-06. Branch `task/DD-1a1-steady-fullday` from main `ce7a7853b`. Worktree `AssetOpsV1-dd1a1`.
- Inputs: `build-sheet-DD-1.md` (R2, R3, R11, §2, Build units DD-1a1, SCOPE-1, DD0c-R), `DD-0c-probe-results.md` §1, §2, §4, §5, `build-sheet-CH-9.md` §10 Q2/Q6/Q8 and §12 "Polish summary row".
- **Lane-1 overlap (CH-6a2/6a3: `chain/*`, `site_outcomes/*`, frontend):** none planned. DD-1a1 touches `host/gateway_publication.py`, `host/lab_execution.py` (one forwarded keyword), the replay helpers in `host/tests` and `backend/tests` (a default-off parameter), `tools/demo_story_days.py`, `tools/demo_combined_{kobo,cold}.py`, `backend/conversions/demo-story-days-v*.json`, new `config/scenarios/*-steady*.yaml`. `chain/*` is read only (operating calendar, `period_bounds`).

## P1. DD-0c applied (DD0c-R P1 answer, restated with anchors)

- L1 knob: `host/gateway_publication.py:128-153` `publish_in_boundary_order`, seal at `:149` after each group. Sole product caller `host/lab_execution.py:2990` (`self._gateway`, set at `:2086`). Fakes with the 4-arg signature: `host/tests/test_ev_publication.py:337`, `test_ev_lab_execution.py:133,421`, `test_cold_lab_execution.py:99,210`.
- Plan: `publish_in_boundary_order(..., *, seal_once=False)`; `HostLabExecution(..., seal_once=False)` stores it and passes `seal_once=True` **only when set** (so the fakes' signatures stay valid). The producer helpers gain a default-off parameter, set True only by the demo children: Kobo `test_s6_verification_replay.py:194` `_publish_and_accept` -> `test_s6_verification_publication.py:126` `_host`; Cold `test_w502_cold_scenario_producer.py:100` (ShiftedChain host; the cold child already subclasses the chain at `tools/demo_combined_cold.py:77`); EV `test_w205b_ev_replay_postgres.py:268`. Kobo `degraded` (`demo_combined_kobo.py:263`) also passes it.
- Parity accepted under DD0c-R Q2 (compare rule recorded there). Cold 24 h run not built (Q3). B-22 sequential 1.81 h central / 2.46 h upper; 2.26 / 2.91 h with drain: under 3 h, no stop.

## P2. Installs against S-20d

- `backend/conversions/demo-combined-story-v1.json:12` Kobo `install_at` S-29d 11:00; `:29` Cold S-26d 06:00; `:35` EV S-26d 06:30. All precede S-20d, so B-22 hits no `DAY_BEFORE_INSTALL` (`tools/demo_story_days.py:179-185`). With Kobo local UTC+3 (`backend/tests/fixtures/s1/kobo-001.yaml:7`, Africa/Addis_Ababa) the Kobo local day S-20d starts S-21d 21:00Z, still after install + 1 h.
- EV Tuesdays: `weekday_offset` (`demo_story_days.py:40-44`) moves to the Tuesday on or before; in `[S-20d, S+1d]` there are 3 Tuesdays (3 or 4 depending on S's weekday). The exact list is DD-1a2's (R1), computed from E3's S.

## P3. Prepare and add-day paths

- Prepare: `tools/demo_combined.py:332` `prepare`; busy marker `:341-342` refuses, written `:356`, removed `:683`; children run at `:405` (`demo_combined_<site>.py build`). Day list resolved at `:129` via `sd.resolve` (`demo_story_days.py:131`).
- add-day: `demo_combined.py:495`; busy check `:504`; `sd.plan_add_day` `:515` (`demo_story_days.py:200-237`, the five refusals); `delivered_days` `:478`; child at `:526`.
- Kind dispatch: Kobo `demo_combined_kobo.py:353-371` (`trial-*` through `_trial_chain` `:400`; others `run_day` `:309`); Cold `demo_combined_cold.py:155-164` -> `run_day` `:106`.
- Kobo run interval must contain the whole scenario timeline: `backend/assetops_backend/runs/service.py:1041-1063` refuses `INTERVAL_INVALID` for an entry at or past the interval end. A scenario cannot be run as a slice.

## P4. R7 seams (DD-1b1; facts only)

- Ledger insert `postgres_evidence_ledger.py:429` (`evidence_publication`); existing override pattern `test_decision_clock_override` `:141-146`, `:526-527`. Objective `recorded_at` columns `objectives/adapters/postgres_objective_store.py:35`. No guard in `tools/checks/*.py` names `clock_override` today, so DD-1b1 registers none it must extend.

## P5. Tick output (R9 is backlogged, BL-11)

- `backend/assetops_backend/scheduling/tick.py:187` builds the JSON; `:280` `tick_perf_line`; `:308` logs it. Consumers by grep: `tools/checks/chain_coherence.py`, `tools/checks/test_chain_coherence.py`, `tools/checks/test_perf_budget.py`, `tools/writer_guard_probes.py`, `tools/demo_combined_finish.py`.

## P6. Memory

- DD-0c §2: python WS peak 576 MB (Kobo A prepare), PG container 1,047 MiB, minimum free 2,508 MB (Kobo B ticks): above the 2 GB floor. The full-day extension adds runs, not concurrency (children are sequential), so the per-run peak is unchanged; the rehearsal (DD-1b2) measures it.

## Facts that shape the questions

- Kobo FORCING_INPUT entries are the whole story (irradiance, three load demands); the healthy references carry no fault forcing. Values (2 h windows): `kobo-daytime` v2 (06-18 local, 12 h; irr 150/550/900/950/600/150; res 8/6/5/6/8/14; clinic 5/6/7/7/6/5; mill 0/15/18/10/12/0; SoC 55). `kobo-mini-grid-evening` v2 (12-20 local, 8 h; irr 500/300/100/0; res 6/8/14/14; clinic 7/6/5/5; mill 15/18/3/0; SoC 42, fuel 300, generator STOPPED).
- Neither parent covers 20:00-06:00 local. Kobo study day = local 00:00-24:00 (`config/chain/operating-calendar-v1.json`, `mini_depth/store.py:366-396`); every hour must be covered by `pv_available_power`.
- Kobo story runs: 03:00-11:00Z = 06-14 local (normal, overcast, overuse, degraded, late, trial-*); `mill-midday` 03:00-15:00Z = 06-18 local. Complements: 00-06 local plus 14-24 (or 18-24 for mill-midday).
- `cold-normal` v1: 60 min of scenario, forcings GRID_LOSS 19:05 / GRID_RESTORE 19:35; the replay window is fixed at 65 min (`tools/w502_cold_work_cases.py:56,144`).

## Questions (batched; each has a default)

1. **What "forcings removed" means for Kobo.** Removing every FORCING_INPUT leaves no irradiance and no load. **Default:** for Kobo, nothing is removed. Both parents are already the "healthy" references (no fault forcing), so `kobo-steady*` copy the parent windows verbatim; only `scenario_id`, `display_name`, `purpose`, `label` and source lines change. For Cold, GRID_LOSS/GRID_RESTORE are removed (R2 as written).
2. **Night hours (20:00-06:00 local) have no parent window.** **Default:** reuse `kobo-mini-grid-evening` `*-4` (18-20 local: irr 0, res 14, clinic 5, mill 0) unchanged, repeated as 2 h windows across the night. These are parent values with no value changed, but the structure is new: windows are repeated. Each repeated window names its source line. Alternative: the Architect names another source.
3. **Slicing.** A run cannot play part of a scenario (`service.py:1041-1063`). **Default:** separate steady files per complement segment, each a contiguous local-hour slice: `kobo-steady-night` (00-06), `kobo-steady-afternoon` (14-24, for the 8 h story days), `kobo-steady-evening` (18-24, for `mill-midday`), and `kobo-steady` (00-24, for DD-1a2's pure steady days). Model: the Kobo manifest's (`d-verification-window-v3`, mini-grid v5, generator-capable). Starting state per segment: the parent's declared SoC/fuel/generator at that parent's start (55 % for segments from daytime, 42 % / 300 L / STOPPED from evening); state is not carried across runs. The night segment may therefore start the generator; that is reported, never tuned.
4. **Which Sites get full-day story days in DD-1a1.** **Default:** Kobo and Cold (both declared 24 h). EV is not changed: R2 rules no `ev-steady`, and EV's declared 08-16Z is outside CH9-R2. Cold story day = the story run in its hour plus `cold-steady` runs tiling the other 23 local hours. Alternative: Kobo only, with Cold full days left to DD-1a2's steady baseline.
5. **Cold tiling.** Runs carry 60 min of scenario and a fixed 65-min assessment window. **Default:** hourly starts, so the 60-min scenario intervals tile the local day with no overlap and no gap; the L0 check runs on scenario intervals, not on the 65-min windows. That is 24 runs per steady day, not the ~22 of DD-0b §7: at 5.2 s per run, +23 runs (about 2 min) per Cold story day. The cost is reported.
6. **Delivery of complement runs.** **Default:** each complement run is its own registered run with its own epoch and a distinct `received_at` = its end + 1 h (as the story kinds do), except a `late` story day, whose complements share its lateness offset +minutes so `DUPLICATE_RECEIVED_AT` holds. The trial pair keeps `_trial_chain` unchanged; its complements are plain `run_day` runs, and the trial verification windows (06:00 hour) are untouched. L2 checks that the verification metrics are equal with and without the complements.
7. **Day-list shape.** **Default:** a new file `demo-story-days-v2.json` (v1 kept for history and its tests). Each Kobo/Cold kind gains `"complement": [<steady kind>, ...]`; `resolve` expands one entry into its story run plus complement `DayRun`s on the same day. L0 asserts that the local-day union is exactly [00:00, 24:00) with no overlap and no gap. The duplicate-day check stays per entry. DD-1a2 then builds the B-22 list on v2.
8. **Cost gate.** **Default:** report the measured extra per full Kobo day from one L2 run on a `*_test` DB (2 complement runs at L1 speed), projected against the +50 % prepare budget. No owner stop unless the projection is over it.

Stop here for rulings.
