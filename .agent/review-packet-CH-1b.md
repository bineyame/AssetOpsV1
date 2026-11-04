# Review packet: CH-1b event register, outbox, dirty queue and drain

Branch `task/CH-1b-events` (worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch1b`); main `e207f328f` merged in.
Sheet: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-CH-1b.md`. Ruling: CH1b-R (Q1, Q2, D1 accepted;
`chain_consume_events = 500`; CH-3 first). Build history: `.agent/CH-1b-phase-0-handoff.md`. `B/` = `backend/assetops_backend/`.
USER_REVIEW_REQUIRED: no task file exists for CH-1b; per the W-lane rule the slice merges on review ACCEPT (no owner
walkthrough gate; backend only, no UI change).

## Outcome delivered

A new fact writes an outbox event in its own transaction (12 statement-level triggers on the producer tables plus the
`recompute_job` UPDATE trigger, migration `0044_chain_events`, down-revision `0045_thread_known_at`). The tick consumes
the events, marks Site-local days x measures dirty, and rebuilds only those snapshots (`chain_snapshots` stage); the
thread stage is event-driven (`chain_threads`). On the L3 clone a new productive price published through the product
CLI re-revisions only `productive_kwh` days from 30 Oct, with the new money; nothing else changes.

## Files materially changed

- `backend/migrations/versions/0044_chain_events.py` - `event_outbox`, `event_consumption`, `snapshot_dirty`; producers.
- `config/chain/event-register-v1.yaml`; `B/chain/events.py` (parse, resolve, consume); `B/chain/drain.py`.
- `B/chain/adapters/postgres_event_store.py` (EventPort + DirtyQueue; `record_backfill`; `pending()`/`site()` SELECTs);
  `file_chain_config.load_event_register`; `composition.build_event_store` and re-exports.
- `B/chain/builder.py` (L6), `postgres_chain_inputs.py` (L2 subject at day start, residuals 1 and 2), `reader.py` (L2),
  `measure_impls.py` (L3 `attributed`, `chain_asset`), `backfill.py` (step a records `backfill.site`).
- `B/scheduling/tick.py` (three `TickLimits`, `chain_snapshots` under CONSEQUENCE, `_deadline_at`), `stages.py`
  (`chain_snapshots`, event-driven `chain_threads`, lifecycle consume), `B/chain/adapters/postgres_thread_sources.py`.
- Guards: `tools/checks/configuration-persistence.ps1` (`$eventWriter`), `tools/checks/test_event_register.py` +
  `tools/check-all.ps1` line, `tools/checks/test_estate_guard.py` (+4 self-tests).
- Tests: `test_ch1b_register.py`, `test_ch1b_drain.py`, `test_ch1b_outbox_postgres.py`; `pg_harness`
  (`clear_event_history`, outbox as an empty-tables root); downgrade/catalogue tests below 0044; stage-order literals.

## Acceptance per sheet item

| Sheet item | Status |
|---|---|
| §0 observable result (event in the fact transaction; consume, mark, rebuild only dirty) | Met: L2 outbox tests (rollback leaves no event, one event per statement) + L3 below |
| §0 boundary: no broker, no pruning, no matcher/money/verification change | Met (no such code touched) |
| §1 migration: three tables, producers, `(source, idempotency_key) DO NOTHING`, immutability | Met; guard checks the 0044 text |
| §2 register (reviewed as code, read by `file_chain_config`) | Met; D1 analytic ids (deviation) |
| §3 consumers + drain, compare-and-delete on `marked_at`, cap defers never backs off | Met: `test_ch1b_drain` (cap hit defers, real error fails) |
| §4 L2 / L3 / L6 / residual 1 / residual 2, each with a test | Met: L0/L2 tests; L3 per Q1 + `chain_asset`; residual 2 by window and analytic |
| §4 CH-2 L6 thread stage incremental, cap defers | Met: `chain_threads` consumes `threads`, places named revisions only |
| §5 DS-R1 / OL-1 | See DS-R1 below; no outcome ids in register, events or drain |
| §6 test ladder L0, L2, scoped, L3 | Met (counts below) |
| §7 guard registration | Met; each new rule proven to fail on a mutation (phase 1b) |
| §9 fingerprint decides every skip | Met; see the L3 note on NO_DATA days |

## P5 trigger overhead (pre-flight, on a clone, production statement shape)

Single-row `INSERT` into `accepted_evidence`, 400 per transaction, 3 rounds per mode, rolled back: median 7.760 ms
with the trigger, 7.904 ms without (-1.8%, inside the +-7% round spread). PASS. Batch statements (one sample):
+2.8% (10 rows), +2.0% (100), +11.1% (500). Live ingestion inserts one reading per statement, so one event per reading.

## L3 clone proof (`assetops_chainclone_ch1b_test`, head `a2bfd73f8`, dropped at the end)

1. `chain_clone.py create ch1b --migrate`: created from `assetops_polish_full_test`, migrated to head.
2. Backfill `--steps a,b,c,d`: written a=139, b=11, c=3, d=6 (13 s). Rerun: a=0, b=0, c=0, d=0 (14 s).
3. `chain_clone.py settle ch1b`: S2 comparison permitted, tick COMPLETED (63 s), performance permitted. After it:
   outbox `backfill.site` 3, consumption 0, dirty 0 (no producer facts in a settled estate).
4. Snapshot before: 139 rows, every measure at revision 1.
5. `python -m assetops_backend.publish_assumption publish --site KOBO-001 --key productive_use_price_per_kwh
   --change-kind CORRECTION --value 0.30 --currency USD --valid-from 2026-10-30T00:00:00+03:00 --expected-prior
   94bb9036...` -> revision 2 `c3fc5ed9...` (prior 0.25 USD from 1 Jan). SUCCESSION was refused
   `SUCCESSION_NOT_FUTURE` (clone db_now is 4 Nov), so the product's backdated kind is CORRECTION. One
   `price.revised` event, occurred 29 Oct 21:00Z.
6. One tick (`scheduling.run tick --environment default --max-sites 5 --s3-jobs 10 --consequence-items 100`, 50 s):
   KOBO `chain_snapshots` `{code: OK, processed: 6, deferred: 0}`, 1908 ms of the 60 000 ms bound (3.2%);
   EV and COLD processed 0 (1374, 1390 ms). Second tick: all three `processed 0`, rows unchanged at 145.

Revisions before -> after (only rows that changed; every other row of every measure unchanged):

| Day (KOBO-001) | Measure | Rev | Grade | kWh | Money before (0.25) | Money after (0.30) |
|---|---|---|---|---|---|---|
| 2026-10-28 and earlier | productive_kwh | 1 -> 1 | - | - | unchanged | unchanged |
| 2026-10-30 | productive_kwh | 1 -> 2 | PARTIAL | 168.333 | 42.08 USD (rev 94bb...) | **50.50 USD** (rev c3fc...) |
| 2026-10-31 | productive_kwh | 1 -> 2 | PARTIAL | 0.000 | 0.00 USD (94bb) | 0.00 USD (c3fc) |
| 2026-11-01 | productive_kwh | 1 -> 2 | PARTIAL | 0.000 | 0.00 USD (94bb) | 0.00 USD (c3fc) |
| 2026-11-02 | productive_kwh | 1 -> 2 | NO_DATA | - | none | none |
| 2026-11-03 | productive_kwh | 1 -> 2 | NO_DATA | - | none | none |
| 2026-11-04 | productive_kwh | 1 -> 2 | NO_DATA | - | none | none |

No other measure (avoidable_gen_min, noon_headroom_kw, chamber_temp_c, backup_start_chain, charging_kwh) and no day
before 30 Oct gained a revision; 139 -> 145 rows. Note for review: the three NO_DATA days 2-4 Nov are inside the price's
validity, so their `input_fp` includes the new revision id and they re-revision with identical content. That is the
sheet's rule (§3 "skipping is decided only by `input_fp`"; §6 "only `productive_kwh` days >= 30 Oct"); a
stricter reading of "exactly the priced days" would exclude them. Not changed (no tuning of the fingerprint).

7. Collect (`chain_coherence.py collect --work <polC>\var\polish_full --database-url <clone>`, 129 s): 56 requests,
   all 200. Check vs `tools/checks/fixtures/chain_coherence/expected-today.json`: **0 new** in every rule (COH-1 12,
   COH-2 2, COH-5 6, COH-6 6, COH-7 10, COH-8 3 expected; others 0); self-check 39 pass, 0 fail. polC `git status`
   identical before and after (collect only reads `keys.json`).
8. Final counts: outbox `backfill.site` 3, `price.revised` 1; consumption `snapshots` 1; dirty 0; unconsumed 3 (the
   `backfill.site` events, which have no consumer in the register by design).
9. `chain_clone.py drop ch1b`: database dropped, the 2 files settle created under `var/` deleted;
   `pg_database LIKE 'assetops_chainclone%'` -> none; worktree `git status` clean.

Drain timing on the test estate (`test_s4_schedule_health_postgres` TICK_COST): first visit `chain_snapshots`
9522 ms (16% of 60 s), idle 1798 ms.

## Checks run (this phase on `a2bfd73f8` unless noted; earlier phases in the handoff)

Postgres via `tools/run-host-tests.ps1` (routed `assetops_pt*_test`), 1-2 files per call:
- `test_fix_cold_drain_tick_postgres` 4 passed (198 s); `test_s4_schedule_tick_postgres -m "not slow"` 6 passed,
  1 deselected (245 s) - both at `7dfc803e0`, no change needed.
- `test_w402_mini_stage_postgres`: 1 failed -> fixed -> 3 passed (153 s). Old expected stage list
  `[discover, s3, cold_assess, ev_assess, mini, opportunity, s4, consequence, cold_consequence, ev_consequence]` ->
  new `[..., s4, chain_threads, consequence, cold_consequence, ev_consequence, chain_snapshots]`.
- Producer tables: finding store + action store 18 passed (152 s); objectives `test_out_d2_objectives` +
  `test_out_d3_objective_store_postgres` 34 passed; financial assumptions `test_s4_assumptions_postgres` + foundation
  `test_s1_foundation_postgres` 33 passed; mini decisions `test_w403_opportunity_worker_postgres` +
  `test_out_d5_objectives_postgres` 8 passed (514 s). Earlier phases: evidence ledger (`test_s2_evidence_ledger`),
  analytic runs (s3/s4 files), mini depth (w402), verification (cc_schema, out_d1).
- Files importing `chain.builder`, `postgres_chain_inputs`, `scheduling.tick`, `scheduling.stages`: `test_ch1b_outbox`
  + `test_s4_schedule_health` 15 passed (553 s); `test_s4_deferred_match` + `test_s4_evidence_decided_at` 13 passed;
  `test_s5_overview` + `test_w403_opportunity_job_isolation` 7 passed; `test_ch1a_snapshot_postgres` 4 (phase 2);
  plus the tick files above.
- Pure: `test_ch1b_drain`, `test_w402_mini_stage` 29 passed; `test_event_register`, `test_ch1b_register`,
  `test_ch0_tick_timing`, `test_fix_cold_drain_stage` 66 passed; `test_w403_opportunity_stage`, `test_ch1a_*`,
  `test_ch2_threads`, `test_ch3_lifecycle`, `tools/checks/test_chain_coherence.py` 180 passed.
- Guards (PowerShell, `ASSETOPS_GUARD_PYTHON` set): `check-architecture.ps1` first FAILED ("Banned adapter import in
  stages.py:214/267: file_chain_config.load_event_register; only chain/composition.py may import chain/adapters") ->
  fixed in `a2bfd73f8` (import via composition) -> **passed**; `check-agent-workflow.ps1` passed.
  Estate guard self-tests not rerun: `configuration-persistence.ps1` and `test_estate_guard.py` unchanged since
  phase 1b (13 passed there); the two new SELECTs pass the guard (architecture check passed).
- No full backend suite (dispatch rule).

## Known deviations

- **D1 analytic ids** (accepted CH1b-R): the register names real analytic ids (`dispatch`, `cold-excursion`,
  `cold-start-response`, `ev-session/1`) instead of the sheet's job domains.
- **`backfill.site` writer** (Q2, accepted): `postgres_event_store.record_backfill` is the one Python INSERT into
  `event_outbox`, literal type `'backfill.site'`, `ON CONFLICT DO NOTHING`; every other runtime write refused by guard.
- **`chain_asset` attribution**: `cold_backup_chain` returns no `policy`, so a backup chain is attributed to the one
  subject asset its step evidence is on, else the single-subject rule (Q1).
- **Residual-2 fix**: a job is cleared by a later selection of the same exact window whose `analytic_id` is in the
  job's analytics (`JOB_ANALYTICS`); matching by window alone would let another analytic clear it.
- **`backup_start_chain` roles**: the register lists the four roles the measure reads (`BACKUP_ROLES`: grid, generator,
  transfer, bus), not the sheet's `backup_start_event`; that role reaches the measure through the
  `cold-start-response` selection (`assessment.revised`), not as a reading input.
- **Lifecycle consumer runs every stage run**: `run_lifecycle` runs once per `chain_threads` run (CH-3 §4 time-based
  causes INCONCLUSIVE_EXPIRED / CLEAN_DAYS need no event), then `consume('lifecycle')` records applied events.
- **Fake-runner literals on main**: CH-2's `chain_threads` was missing from 4 fake-runner tests on main (17 failures):
  `test_w402_mini_stage`, `test_fix_cold_drain_stage`, `test_w403_opportunity_stage`, `test_ch0_tick_timing`; plus the
  real-runner literal in `test_w402_mini_stage_postgres` (this phase). All fixed.
- L3 publish used CORRECTION, not the handoff's SUCCESSION (refused as backdated; the product rule).
- **R2-L3 carried to SWEEP-DS**: backfill step (a) builds snapshots up to today, past the story end; left as is. The
  drain resolves open-ended spans (a price with no `valid_to`, `foundation.revised`) to the Site-local today the same way.

## DS-R1

Item 4 (live re-assessment shown only as "not checked yet until the next tick"): fixed structurally - a new fact
re-assesses through the outbox and drain on the next tick; serve text untouched (DD-1). One-noon-hour solar period:
labelled keep -> CH-9. New `TickLimits` (60 s, 200 items, 500 events) are declared defaults, not fitted.

## Residual risk

- Outbox grows one row per live reading (P4; ~10 300 on the polish estate); no pruning (scale path S1).
- NO_DATA days inside a revised price window re-revision with identical content (above); harmless to values, adds rows.
- First-visit drain on a fresh estate took 16% of its bound; a much larger estate would defer (by design, no back-off).
- Overlap with CH-4 (`backfill.py` step b, `postgres_thread_sources.py`, `test_chain_coherence.py`,
  `test_ch2_thread_store_postgres.py`): the second to merge resolves.
- Residual 2 is still window-exact: a job whose window was re-split is not cleared by a differently-bounded selection.

## User-review focus

The NO_DATA-days reading of "exactly the priced days"; the lifecycle-every-run choice; the trigger-only outbox with
the single guarded Python writer.
