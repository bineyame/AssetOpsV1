# Review packet OWN-G2 (automatic diesel-night check), u1 + u2 — PARTIAL (Postgres P1-P7 not proven)

Branch `task/OWN-G2-diesel-night-check`. Spec: `.agent/build-sheet-OWN-GAPS-2026-11-08.md` §2, Revision 1, Revision 2
R2-G2. Commits: `1eeabf66e` (u1), `06c09b95b` (u2 tools/KIS-11), this commit (Postgres file + packet).

## Files materially changed

- u1: `backend/assetops_backend/fuel_balance/{model.py, scheduled.py (new), adapters/postgres_fuel_balance_store.py,
  worker.py (docstring)}`, `scheduling/{stages.py, tick.py}`; tests `test_own_g2_fuel_night_{due,stage,tick}.py`
  (new), pin updates in `test_fix_cold_drain_stage.py`, `test_w402_mini_stage.py`, `test_w403_opportunity_stage.py`,
  `test_ch0_tick_timing.py`, `test_fix_cold_drain_tick_postgres.py`, `test_w402_mini_stage_postgres.py`.
- u2: `tools/demo_combined.py` (`Demo.tick` writes/removes `<work>/last-tick.json`, returns the report;
  `retry_until_visited`; `Demo.finish` closing-tick retry), `tools/demo_combined_rows.py` (`last_json_object`,
  `fuel_night_entry`, `kis11`), `tools/demo_combined_finish.py` (`@row("KIS-11")` right after KIS-9),
  `backend/tests/test_demo_combined_finish_rows.py` (+6 cases), `backend/tests/test_own_g2_fuel_night_tick_postgres.py`
  (new, NOT yet passing a run — see Deviations).

## Spec item -> evidence

| Item | Evidence |
|---|---|
| §2.4 due rule, R2 Q1/Q3/Q4/Q11/Q12 (no-DB) | `test_own_g2_fuel_night_due.py` |
| §2.3 stage child (REUSED/UNCHANGED, WINDOW_OPEN skip, CLOCK_BACKWARDS, deadline, `deadline_at`) | `test_own_g2_fuel_night_stage.py` |
| §2.2 tick wiring, limits, lease, `STAGE_LIMIT_FIELDS`, Q8 | `test_own_g2_fuel_night_tick.py`; stage-list pins in 4 updated files |
| R2 Q9 (a) `kis11` pure | `test_kis11_passes_...`, `test_kis11_fails_when_kisiwa_was_not_visited_and_on_each_break` (3 absent shapes + 6 breaks) |
| R2 Q9 (b) KIS-11 after KIS-9 | `test_kis11_is_wired_right_after_kis9` |
| R2 Q9 (c) `last-tick.json` written / stale removed / report returned | `test_last_json_object_...`, `test_demo_tick_writes_last_tick_json_and_removes_a_stale_one` |
| R2 Q9 addition: up to two more ticks 30 s apart | `test_closing_tick_retries_at_most_two_more_ticks_30_s_apart` |
| §2.7 P1-P7, R2 Q1/Q5/Q6/Q7/Q12 Postgres | file written; **not proven** (see below) |

No-DB run (10 files: the 3 G2 files, the 4 pin files, k3 rules, k4a rules, finish rows): **180 passed** in 13.7 s.

Postgres pin files rerun (`test_fix_cold_drain_tick_postgres.py`, `test_w402_mini_stage_postgres.py`, DB
`assetops_g2tick_test`, 277 s): **4 passed, 3 failed**. The 3 failures are `test_fix_cold_drain_tick_postgres.py`
p1/p2/p3, and each fails in its replay fixture **before the tick and before any G2-edited line**: p1 `assert jobs`
(no PENDING cold jobs, line ~101), p2 the EV replay run `FAILED` (`LabProjection status='FAILED'`), p3
`not enough values to unpack (expected 1, got 0)` in the cold fixture. These look like the known wall-clock fixture
drift (cf. branch `task/FIX-clock-dependent-power-fixture`). A baseline on the pre-G2 revision was not run: the
`git worktree add` into the scratchpad failed (path length), so "pre-existing" is unverified. `test_w402_mini_stage_postgres.py`
(the `:147` pin) passed.

## Known deviations / stops

1. **STOP: the ruled Postgres fixture cannot meet the 10-minute cap.** R2 Q5 requires K1's path (a real gateway and
   S2 ingestion). One Kisiwa 15:00-15:00 run stages 1828 batches / 3659 envelopes. The first attempt ran 750 s and was
   still inside the second run's acceptance. P1-P7 need at least 3 runs (N0/N1 in the base set, N9 outside it) and the
   ruling names 4, so the file needs about 15-25 min. A ruling is needed. Options: raise the cap for this one file
   (it is E2-explicit anyway, R1.3); shorten each run to the night (about 19 h, a small saving); or accept readings
   through `BatchIngestionService` without the gateway. The file has not completed a run.
2. That first attempt also failed on a fixture bug, now fixed but not re-run: `_publish_and_accept` counts batches
   by `received_at`, so each run now gets `received + k s`, which keeps the time at about DB now - 10 min.
3. Fixture shape choices (R2 Q5): `probe_kisiwa_nights.day_document` is a fixed 15:00-15:00 local day. So the runs
   end at the latest local 15:00 at or before DB now - 15 min, and 1, 2 and 9 days earlier (not exactly at the night
   ends), and each run holds exactly one night. P5's old night is 9 nights back, not 10, so its run starts after the
   Site's install at now - 12 d. The tick's other stages run in process (`InProcessRunner`), and only `fuel_night`
   is a real `StageRunner` child, to keep the runtime down.
4. Q1 Postgres edges use the real 5-minute readings at 17:25/17:30/12:25/12:30 local, not 17:29/12:29. The
   behaviour proved at each edge is the same, and the edge set is asserted non-empty. Q12's "Cold-like Site" uses a
   Site id that has no FUEL_TANK or GENERATOR rows.
5. The `CAST(:a AS uuid)` risk is resolved by schema: `accepted_evidence.asset_id` is `uuid`
   (`migrations/versions/0005_evidence_ledger.py:174`), so the cast is correct. It has not yet been exercised by a
   completed Postgres run.
6. §2.6 lists `test_ch1b_drain.py` among the pin files. u1 did not touch it, and it was not run here.

## Residual risk

- P1-P7 are unproven on Postgres. `schedule_inputs` and the stage child have only been exercised through fakes.
- KIS-11 was not run on a real build: no demo prepare, as instructed.

## Phase 3 (R3 proof run, 2026-11-08) — Postgres file: 4 passed, 1 FAILED (Q1)

- Main merged (G3a in), clean. Marker `pytest.mark.slow` added (commit `60ab27462`).
- No-DB set after the merge: 160 passed (3 G2 files, ch0 tick timing, `test_ch1b_drain.py` run, passed, no edit needed;
  cold_drain_stage, w402/w403 stage, finish rows) + 43 passed (k3, k4a rules).
- `test_own_g2_fuel_night_tick_postgres.py`, one process, file order, `-s`, own DB: run 1 = 4 failed, 1 passed, 1133 s;
  after two test-code fixes, run 2 = **1 failed, 4 passed, 1172 s (19.5 min)**.
- Test-code fixes (no change to what is proved): (a) FUEL_DELIVERY records now carry a ticket digest
  (`WORK_RECORD_TICKET_REQUIRED` in P4b/P4c/P5); (b) `record_ids` is returned as a list of lists, flattened by `_ids()`
  (P4a/P5).
- Passing: P1/P2/P3/P6/P7 (`test_p1_p2_p3_p6_p7_two_ticks`), P4a, P4b/c, P5. G2 print lines: tick 1 fuel_night
  `eligible True, processed 3, appended 2, reused 1, raised NO_FINDING 3`; P3 Kobo `eligible True, nights [], processed 0`;
  P4a `APPENDED rev 2 WITHIN_MARGIN, limitation DIP_SENSOR_CONFLICT`; P4b `85 L, APPENDED OPENED, UNEXPLAINED`; P4c
  `APPENDED WITHDRAWN rev 3 WITHIN_MARGIN`; P5 `records 3, night 2026-10-29 APPENDED rev 2`.
- **FAILING: `test_q1_bucket_edges_and_q12_a_site_without_fuel_assets`** at `:216`. The Kisiwa fuel_level readings
  (376 over 4 runs, about 94 a day, so a 15-minute cadence) are at 17:30 and 12:30 but NOT at 17:25 / 12:25
  (`G2 Q1 edge readings 376 ['12:30', '17:30']`). R3.3 item 4 assumed real 5-minute readings and says to keep the
  assert that all four edge times are present; the data cannot satisfy it. Not edited: it changes what is proved.
  Ruling needed (e.g. assert the real edge readings 17:30 in / 12:30 out, and use 17:15 / 12:15 or night_of on
  synthetic 17:25 / 12:25 for the outside neighbours).
- `test_w402_mini_stage_postgres.py` + `test_fix_cold_drain_tick_postgres.py::test_p4_...unchanged_apart_from_four_zero_count_keys`:
  4 passed, 201.9 s.
- Module docstring runtime not yet added (run is not a clean pass).

## User review

Not required by itself. The cap/fixture ruling in Deviation 1 is needed before review can close G2.
