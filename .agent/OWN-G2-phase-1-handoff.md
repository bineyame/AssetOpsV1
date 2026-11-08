# OWN-G2 handoff after u1 (PARTIAL: stopped at the context budget)

Branch `task/OWN-G2-diesel-night-check`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-g2`, main merged at `76083070d`
(includes the R2 rulings, build sheet `.agent/build-sheet-OWN-GAPS-2026-11-08.md` "R2-G2"). u1 commit `1eeabf66e`.

## Landed (u1)

- `backend/assetops_backend/fuel_balance/model.py`: `ScheduleInputs`, `DuePlan`; `schedule_inputs` on `FuelBalanceReadPort`.
- `fuel_balance/scheduled.py` (new): `BASE_NIGHTS`, `RECORD_LOOKBACK`, `QUIET`, `EDGE`, `bucket_bounds()`, `night_of()`,
  `latest_closed_night()`, `due_nights()`, `run_site(store, findings, t, s, limit, deadline)` (R2 Q4, Q11).
- `fuel_balance/adapters/postgres_fuel_balance_store.py`: module `_windows_on(c, ...)` shared by `windows()` and the new
  `schedule_inputs(t, s, record_lookback)` (one REPEATABLE READ READ ONLY snapshot; honours `test_db_clock_override`;
  bucket SQL binds `bucket_bounds()`; `e.asset_id = CAST(:a AS uuid)` — **unverified on Postgres**: if
  `accepted_evidence.asset_id` is text, drop the cast).
- `scheduling/stages.py` `fuel_night` + `STAGES` + docstrings; `scheduling/tick.py` limits, `__post_init__`, lease,
  `STAGE_LIMIT_FIELDS`, `as_json` `"eligible"`, `_site` wiring under `stage("MINI")`, docstring; `fuel_balance/worker.py`
  docstring.
- Tests (no DB): new `test_own_g2_fuel_night_due.py`, `_stage.py`, `_tick.py`; updated stage-list/lease pins in
  `test_fix_cold_drain_stage.py`, `test_w402_mini_stage.py` (incl. the S4 lost-claim param), `test_w403_opportunity_stage.py`
  (incl. `test_lost_claim_stops_before_the_opportunity_stage`), `test_ch0_tick_timing.py`; Postgres pins in
  `test_fix_cold_drain_tick_postgres.py:106,199`, `test_w402_mini_stage_postgres.py:147` (edited, not yet run).
- Run: those 8 no-DB files + `test_k3_fuel_balance_rules.py` + `test_k4a_fuel_finding_rules.py`: 114 + 43 passed
  (PYTHONPATH must include `tools` for the k3 rules file).

## Next (u2), in order

1. `tools/demo_combined.py` `Demo.tick` (623-629): parse the last stdout line that is a JSON object per tick, write
   `<work>/last-tick.json`, remove a stale file when none parses, return the parsed report (R2 Q9 c). `Demo.finish`
   (592): when "kisiwa" is in the story and the closing tick's report has no `fuel_night` stage for KISIWA-001, run up
   to two more ticks 30 s apart (R2 Q9 addition); keep the retry count testable (a small pure helper).
2. `tools/demo_combined_rows.py` `kis11(...)` pure (+2-3 cases in `backend/tests/test_demo_combined_finish_rows.py`,
   plus one retry-count case); `tools/demo_combined_finish.py` `@row("KIS-11")` right after KIS-9 (`:1468`): last-tick
   entry for KISIWA-001 `code OK`, `eligible true`; story nights' latest window revision = 1 (reuse `_kisiwa` cache
   windows at `:1379-1395`); Kisiwa exactly one fuel Finding; KOBO-001 zero `fuel_balance_window` rows; fail with
   "KISIWA-001 was not visited by the last tick" when absent.
3. Postgres `backend/tests/test_own_g2_fuel_night_tick_postgres.py` per §2.7 as amended by R2 Q1, Q5, Q6, Q7, Q12
   (K1 path: `test_k1_kisiwa_site_postgres.py:42-110`; decision clock override
   `evidence/adapters/postgres_evidence_ledger.py:525`). Own `*_test` DB name; check >= 2.5 GB free RAM; foreground,
   < 10 min; slow-tier marker if > 120 s. Then rerun the two edited Postgres pin files.
4. `.agent/review-packet-G2.md`; commit with `git add -f .agent`.

## Open risks

- The `CAST(:a AS uuid)` above; the Postgres file is the first real run of `schedule_inputs`.
- `stages.fuel_night` builds two fuel stores (one inside the finding service); both dispose.
