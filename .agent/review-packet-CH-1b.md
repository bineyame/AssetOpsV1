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

## Fix round Part A (review REVISE; rulings DD0-R, CH1b-R2), head `ce14c45fe`

Code: `85551427a` (paged consume and the rest), `ce14c45fe` (M1 test set-up). Part B (CH-4 `None` sources, L3 rerun) waits for CH-4 to merge.

| Item | Status | Where |
|---|---|---|
| DD0-R / R2-1: paged, time-bounded consume | Met. Pages of `chain_consume_events` until the queue is empty or the consume deadline (stage start + `bound_seconds`/2, capped at the shared `deadline_at`). The drain gets its own `Deadline` on the full shared deadline, created after consume. `site_today` is read once per stage run and passed to every page. The stage reports `consume.{ms, select_ms, pages, stopped, deferred}` and `drain.{ms, deferred}` separately. | `chain/events.py` `consume`; `scheduling/stages.py` `chain_snapshots`; `tick.py` passes `bound_seconds` |
| R2-3: coalesced page write, one transaction | Met. `coalesce` gives one `Mark` per (tenant, Site, day, measure), with `first_event_id` = the page's first event in read order. `EventPort.mark_and_consume_page` writes the multi-row mark upserts and then every consumption row in one transaction, and refuses uncoalesced marks. The memory port implements it. Threads stay one event per transaction. | `events.py`; `postgres_event_store.py` `_values`, `mark_and_consume_page`; `test_ch1b_drain.py` `MemPort` |
| Review L2: lifecycle consumes exactly its pre-read ids | Met. The stage reads `unconsumed('lifecycle')` before `run_lifecycle` and then calls `consume_exactly`. | `stages.py` `chain_threads`; L0 `test_consume_exactly_records_only_the_events_read_before_the_run` |
| R2-2: typed index in 0044 | Met. `event_outbox_site_type_order (site_id, type, recorded_at, event_id)` **replaces** `event_outbox_site_order`: every outbox read filters on type, so a second index would only add write cost. No cursor, no pruning. | `0044_chain_events.py:124` |
| R2-3: guard shapes | Met. The `event_consumption insert` and `snapshot_dirty mark upsert` shapes accept a multi-row VALUES list of literal tuples only (`$valuesRows`). They stay insert-only with the same arbiter. The declared statements remain one-row templates; `_values` repeats the one VALUES tuple at run time. Self-test `test_event_page_writes_accept_multi_row_values_only`: a 2-row literal is accepted; `SELECT ... unnest`, `VALUES (:c, unnest(:ids))`, `INSERT ... SELECT` and a 3-column arbiter are refused. | `configuration-persistence.ps1:904-912`; `test_estate_guard.py` |
| M1 | Met. L2 (`test_ch1b_fix_postgres.py`): a selection is invisible at `selected_at - 1µs` and visible at `selected_at`; a dispatch job stays pending after a `cold-excursion` selection of its window and clears at its own `dispatch` selection (not 1 µs before it); a job with `available_at > k` is not pending at `k`; on a TUE-only calendar the Kobo Grain-mill measure writes one NOT_EXPECTED row per subject on Monday 12 Oct, the same subjects as Tuesday, and `grade_counts` with a missing second measure gives not_expected 1 and no_data 0. L0 `_counts` test in `test_ch1b_drain.py`. | |
| M2 | Met for Finding and Action. In `seeded` (real F01/F02 revisions, a real trial and a domain Action on F01), F01's trigger event is consumed out of the way first. The first stage run places only F02 and leaves the Actions PENDING_PLACEMENT (≥2), linking 0. A replayed `finding.revised` naming F01's revisions then places F01 and links 2 in that run. A rerun consumes 0 and writes 0. **No opportunity event is exercised**: the seeded set has none, so that path is covered by Part B's ineligible-opportunity stage test. | `test_m2_...` |
| Review L1 | Met. `inputs.<m> names no source, so no event ever marks it dirty`, with the mutation `charging_kwh: {}`. | `test_event_register.py` |

**Non-vacuity, each on the committed tree, then reverted with `git checkout`:**
- dropping `sel.selected_at <= :k` fails residual 1 (line 210);
- forcing `_subject_instant` to the period start leaves Monday with 0 subjects (line 256);
- dropping `x.analytic_id = ANY(:an)` lets the cold selection clear the dispatch job (line 220);
- passing `"f": []` in `unlinked_actions_for` fails the M2 link (line 323).

**DD0-R measurements** (L2, `w402` set-up; outbox rows in the 0044 reading subject shape, 9 s spans, one Site-day; bound 60 s, half 30 s):

| Case | stage ms | consume ms | drain ms | pages | per-page select ms | share of half bound |
|---|---|---|---|---|---|---|
| 4,400 events, empty history | 974 | 816 | 89 | 9 | 22-80 (median 25) | 3.2% |
| 4,400 events after 60,298 consumed | 3,314 | 2,972 | 81 | 9 | 228-359 (median 249) | 11% |

Per-page select cost grows roughly linearly with the consumed history: the anti-join still probes every earlier event of the type. That is 10x at 14 days. One Kobo day stays far below half the bound, so there is no DD-1 cursor item at this size. Extrapolating linearly, the 90-day demo outbox (about 390k events) would cost about 1.6 s per page, or about 15 s per Kobo day, which is still under 30 s. **This is an estimate, not measured.** It is a candidate DD-1 note.

**Checks (Part A, on `ce14c45fe` code):**
- `test_ch1b_drain.py`, `test_event_register.py`: 34 passed. Then `test_ch1b_drain.py`: 23 passed.
- `test_ch0_tick_timing`, `test_fix_cold_drain_stage`, `test_w402_mini_stage`, `test_w403_opportunity_stage`, `test_ch1b_register`: 74 passed.
- `run-host-tests.ps1`:
  - `test_ch1b_fix_postgres.py` + `test_ch3_lifecycle_postgres.py`: 10 passed (99 s);
  - `test_ch1b_outbox_postgres.py` + `test_w402_mini_stage_postgres.py`: 7 passed (141 s).
- Estate and register guard self-tests, in three `-k` runs because of the 10-minute call cap: 16 passed (event + register, 289 s), 7 passed (353 s), 3 passed (168 s). That is all 14 estate tests and all 12 register tests.
- `check-architecture.ps1` passed (135 s); `check-agent-workflow.ps1` passed.
- Not run: `test_ch2_thread_store_postgres.py` (its tests call `run_threads`, which is unchanged); the full backend suite.

## Fix round Part B (after CH-4 merged), head `4471cfe7b`

- **Merge.** `99cddced6` merges main at `d6bbe6f04` (CH-4). It merged cleanly, and migrations are unchanged.
- **Review M3 / R2-4.**
  - `sources_by_revision` now returns the placed Sources in `(created_at, id)` order, then one `None` per named ineligible opportunity revision, the same way `sources` returns them.
  - The `chain_threads` `on_event` drops the `None`s and counts them in step b's `skipped_ineligible`. The event is still consumed, never failed.
  - Stage test `test_threads_stage_consumes_an_ineligible_opportunity_event_as_skipped` uses CH-4's `seed_opportunities`, where study A is ineligible and study B has 2 revisions. It checks:
    - 3 `opportunity.revised` events, all consumed, with deferred 0 and `skipped_ineligible` 1;
    - one occurrence (study B);
    - A's event recorded in `event_consumption`;
    - a rerun consumes 0 and writes 0.
  - Non-vacuity: removing the stage filter fails with `AttributeError: 'NoneType' object has no attribute 'created_at'`, the crash the review predicted.
- **Index note (accepted by the coordinator).** In 0044, `event_outbox_site_type_order (site_id, type, recorded_at, event_id)` replaces `event_outbox_site_order`. Every outbox read filters on type, so keeping the old index would only add write cost. The L3 clone shows exactly `event_outbox_pkey`, `event_outbox_idem` and `event_outbox_site_type_order`.
- **DD-1 note: per-page select growth.**
  - The anti-join's per-page select grows about linearly with the consumed history: median 25 ms at 0 consumed, median 249 ms after 60,298.
  - Projected, **as an estimate and not measured**: about 1.6 s per page at the 90-day demo outbox (about 390k events), or about 15 s for one Kobo day's consume. That is still under the 30 s half bound.
  - If DD-1's 90-day data makes this real, a commit-safe cursor (or pruning) is the lever. Measure first.

### L3 on a fresh clone `assetops_chainclone_ch1bb_test` (code `4471cfe7b`, no serve running), dropped at the end

1. `create --migrate`: head `0044_chain_events`, the three outbox indexes listed above.
2. Backfill `a,b,c,d`:
   - first run: a=139 (Cold 24, EV 16, Kobo 99), b=9 (`skipped_ineligible` 2, CH-4's 0-eligible studies), c=3 LINKED, d=6;
   - rerun: a=0, b=0 (13 ALREADY_PLACED, `skipped_ineligible` 2), c=0, d=0.
3. `settle`: S2 permitted, tick COMPLETED (58 s), performance permitted. Afterwards: 139 rows all at revision 1; outbox `backfill.site` 3; consumption 0; dirty 0.
4. An idle tick before the publish (the first publish attempt was refused for missing arguments, so nothing was published): every Site `chain_snapshots` OK with processed 0, and `chain_threads` processed 0.
5. Publish:
   - command: `publish_assumption publish --site KOBO-001 --key productive_use_price_per_kwh --change-kind CORRECTION --value 0.30 --valid-from 2026-10-30T00:00+03:00 --expected-prior 94bb9036...`;
   - result: revision 2 `df2c1e94...`;
   - one `price.revised` event, occurred `2026-10-29T21:00Z`, valid `[that, null]`.
6. One tick (`--max-sites 5 --s3-jobs 10 --consequence-items 100`, 55 s), all three Sites COMPLETED:
   - KOBO `chain_snapshots`: OK, processed 6, deferred 0, in 1,905 ms (3.2% of 60 s);
   - EV and COLD: processed 0;
   - only `productive_kwh` gained revision 2, on 30 Oct (42.08 to **50.50** USD), 31 Oct and 1 Nov (0.00, now on the new revision), and 2-4 Nov (NO_DATA);
   - rows went from 139 to 145. Consumption `snapshots` 1; dirty 0.
   - The tick's per-stage record keeps only code, processed and deferred, so the consume/drain split for L3 is not in its output. That split is measured at L2 (Part A table).
7. Collect into a scratch work dir holding a copy of polC's `keys.json` (polC itself was not written): 56 requests, all 200.
8. Check against the merged `expected-today.json`: **0 new** in every rule (COH-1 12, COH-2 2, COH-5 6, COH-7 10, COH-8 3, all expected; COH-6, COH-10 and COH-16 0). Self-check: 33 pass, 0 fail.
9. `drop ch1bb`: the database was dropped and the 2 settle files were deleted. No `assetops_chainclone%` database remains. `git status` is clean.

### Checks (Part B, on `4471cfe7b`)

- **Pure:** `test_ch1b_drain`, `test_ch1b_register`, `tools/checks/test_chain_coherence.py`, `test_ch0_tick_timing`, `test_fix_cold_drain_stage`, `test_w402_mini_stage`, `test_w403_opportunity_stage`: 181 passed.
- **Postgres, via `run-host-tests.ps1`:**
  - `test_ch1b_fix_postgres` + `test_ch2_thread_store_postgres`: 11 passed (191 s);
  - `test_ch1b_outbox_postgres` + `test_w402_mini_stage_postgres`: 7 passed (104 s);
  - `test_ch3_lifecycle_postgres` + `test_ch4_opportunity_postgres`: 7 passed (34 s).
- **Guards:**
  - Estate event tests + register guard tests: 16 passed (202 s). The guard and the guard tests are unchanged since Part A, where all 14 estate tests passed.
  - `check-architecture.ps1` passed (123 s); `check-agent-workflow.ps1` passed.
- **Not run:** the full backend suite (dispatch rule).
