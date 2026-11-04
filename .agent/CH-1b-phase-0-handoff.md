# CH-1b phase 0 handoff: pre-flight answered, Architect questions open (PARTIAL; build not started past the core)

Branch `task/CH-1b-events` (worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch1b`), from main `54d46479f`.
Sheet: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-CH-1b.md`. Paths: `B/` = `backend/assetops_backend/`.

## Landed (WIP commit, untested beyond a smoke run)

- `backend/migrations/versions/0044_chain_events.py`: the three tables, as the sheet's §1; 12 statement-level producer
  triggers `<table>_chain_event` (generated from `PRODUCERS`) plus `recompute_job_chain_event_update`. Upgrade applied
  cleanly on a clone of `assetops_polish_full_test` (head `0044_chain_events`, outbox empty after migrate).
- `B/chain/events.py`: register parse/validate (`parse_register`), `local_days`, `resolve`, `EventPort`, `consume`.
- `B/chain/drain.py`: `DirtyQueue`, `drain` (compare-and-delete via `queue.done`), `DrainReport`, `Deadline`.
- `config/chain/event-register-v1.yaml`. Smoke: a price valid from 29 Oct 21:00Z on Addis resolves to
  `productive_kwh` 30 Oct to 3 Nov; a span over local midnight marks both days.

## Pre-flight answers

- **P1.** All 12 sources carry `tenant_id` and `site_id` (NOT NULL; checked for assumptions, objectives and Foundation).
  The analytic ids in `analytic_run_selection` are `dispatch`, `cold-excursion`, `cold-start-response` and
  `ev-session/1`. The sheet's `analytics: [cold_chain]` and `[ev_charging]` are job domains, so the register uses the
  real analytic ids (deviation D1). Job domains are `dispatch`, `cold_chain`, `ev_charging`, `mini_*` and
  `mini_opportunity`. Of these sources, the CH-1a adapters read `accepted_evidence`, `analytic_run_selection`,
  `mini_depth_selection`, `recompute_job`, `financial_assumption_revision` and `foundation_revision`.
- **P2.** Every Cold reading carries `asset_id`, but it is not the subject asset:
  - `chamber_temperature` is on `probe-1` (TEMPERATURE_PROBE), while the measure's subject is `room-1` (COLD_ROOM);
  - the backup roles are on `grid-1`, `bus-1`, `transfer-1` and `generator-1`, and only `generator_state` and
    `backup_start_event` are on the GENERATOR subject.
  See **Q1**.
- **P3.** `recompute_job` is declared in `tools/checks/configuration-persistence.ps1`:
  - `$ledgerTables` (:674);
  - `$assessInserts` (:697);
  - the allowed-UPDATE list `$assessUpdates` (:703-706);
  - the check itself (:1119-1131).
  A writer entry follows the `$snapshotWriter` shape (:887-893) and touches `$pgWriters` :900, `$pgWritesSeen` :959,
  `$pgDriverSeen` :964, `$actionForbidden` :1050, the statement loop :1304-1319 and the vacuity loop :1569.
  Trigger-only tables have precedent: `cold_consequence_work` and `ev_consequence_work` are refused for any runtime
  statement (:1362-1372), and their migration text is checked (:1694, :1704). Use that precedent for `event_outbox`.
- **P4.** `enqueue_mini_depth` (0029:305) is a row-level `CONSTRAINT TRIGGER ... DEFERRABLE INITIALLY DEFERRED`. The new
  `accepted_evidence_chain_event` is a plain statement-level AFTER trigger, so it fires at statement end and the
  deferred trigger still fires at commit. Neither changes the other.
  - The production ledger (`postgres_evidence_ledger.py:541-575`) inserts **one reading per statement**, inside a
    per-ordinal savepoint. Live ingestion therefore writes one outbox event per reading. The statement aggregation
    only helps bulk inserts.
  - A savepoint rollback also removes its event.
  - The polish estate holds 10,300 readings, so the outbox will have a similar row count.
- **P5. PASS.** Measured on the clone with the production statement shape: single-row `INSERT` into
  `accepted_evidence`, 400 per transaction, 3 rounds per mode, rolled back.
  - Median with the trigger was 7.760 ms per insert; with it disabled, 7.904 ms. The delta of -1.8% is inside the
    noise (round-to-round spread about ±7%).
  - Batch statements, a single sample of the median of 40, showed +2.8% (10 rows), +2.0% (100) and +11.1% (500).
  - The first single-row probe read +40%, but that was 5 reps and noise; the 400-rep rerun replaces it.
  - Scripts: scratchpad `p5_bench.py` and `p5_bench2.py`; the deferred constraint triggers were not reached, because
    the transactions were rolled back.

## Questions for the Architect (batched; the build stops here)

- **Q1 (L3, semantics).** If readings are filtered literally by `asset_id = subject`, every chamber reading
  (probe-1 ≠ room-1) and most backup readings are dropped, and COLD-LAB `chamber_temp_c` and `backup_start_chain` go
  to NO_DATA.
  - Proposal: a reading counts for subject X when its `asset_id` is X. A reading whose `asset_id` is not a subject of
    that measure (or is null) is Site-wide, and is used only when the Site has exactly one subject of that kind.
  - On today's data this changes no value. The alternative is mapping probe to room through Foundation relations.
  - Chains: use the generator asset in the chain, if it has one, the same way.
- **Q2 (writer seam).** Sheet §3 has the backfill record a `backfill.site@1` event from Python, but §7 says
  `event_outbox` is written only by triggers.
  - Proposal: `chain/adapters/postgres_event_store.py` gets one INSERT into `event_outbox`, restricted by the guard to
    the literal type `'backfill.site'` with `ON CONFLICT DO NOTHING`. Every other runtime write to `event_outbox` stays
    refused.
- **Q3 (FYI, decided mechanically).** PostgreSQL refuses `UPDATE OF status` on a trigger with transition tables
  ("transition tables cannot be specified for triggers with column lists"). The UPDATE trigger instead compares old
  and new rows and emits `job.changed` when the status **or the window** changed. A widened PENDING window must dirty
  its new days; a coalescing `available_at` update emits nothing.
  - The key carries `pg_current_xact_id()` plus `sum(attempts)`, so a re-lease to the same status is a new event.
  - Duplicates are `ON CONFLICT (source, idempotency_key) DO NOTHING`.
- **Q4 (FYI).** R2-L3 (backfill step (a) builds snapshots up to today, past the story end) is not covered by the
  sheet. Step (a) is left as is; it goes to the packet as carried to SWEEP-DS. The drain resolves open-ended spans
  (a price with no `valid_to`, `foundation.revised`) up to the Site-local today in the same way.

## Remaining steps (anchors)

1. `B/chain/adapters/postgres_event_store.py`, implementing `EventPort` and `DirtyQueue`:
   - `unconsumed`: `NOT EXISTS event_consumption`, ordered by `recorded_at, event_id`, with a LIMIT;
   - `mark_and_consume`: a single transaction, upsert `ON CONFLICT DO UPDATE SET marked_at = clock_timestamp()`
     with `first_event_id` kept, then INSERT `event_consumption`;
   - `pop`, `queued`, `done`: `DELETE ... AND marked_at = :m`;
   - `site_today`.
   Wire it in `B/chain/composition.py` and add a register loader to `B/chain/adapters/file_chain_config.py`.
2. Tick:
   - Add `TickLimits.chain_snapshot_seconds = 60` and `chain_snapshot_items = 200` (`B/scheduling/tick.py:60-109`).
     Include them in the `>= 1` check, the positivity check, the statement-timeout `min(...)` and `site_lease_seconds`.
   - Add `STAGE_LIMIT_FIELDS` (:255) `"chain_snapshots"`.
   - Add the new stage in `_site` after the consequence drains (:479), under head stage `CONSEQUENCE`. A non-OK
     result is a failure; `{"code": "OK", "deferred": n}` is not.
   - Pass an absolute `deadline_at` (epoch time) so the child stops before the kill (`drain.Deadline`).
   - Update the CH-0 test `SITE_STAGES` (`backend/tests/test_ch0_tick_timing.py:37`).
3. `B/scheduling/stages.py`:
   - The `chain_snapshots` stage: consume `snapshots`, then drain.
   - Rewrite `chain_threads` (:194-206) to consume `threads` over `finding.revised`, `opportunity.revised` and
     `action.event`, placing only those ids.
   - Add reader methods to `postgres_thread_sources.py`: sources by revision id (filter `_FINDING_SOURCES` and
     `_OPPORTUNITY_SOURCES` with `r.id = ANY(:ids)`) and unlinked actions with `id = ANY(:action_ids)`.
   - Register the new stage in `STAGES` (:341).
4. Backfill step (a) (`B/chain/backfill.py:85-122`): after `build_range`, record `backfill.site@1` per Site (pending Q2).
5. Carried fixes in `B/chain/`:
   - L2: `foundation_assets` and `productive_assets` at day start when there is no period (`postgres_chain_inputs.py:148`,
     `:176`); in the reader, `_counts` (`reader.py:50-66`) counts a missing measure as NOT_EXPECTED on a day that has a
     NOT_EXPECTED row.
   - L3: `measure_impls.py:241`, `:267`, per Q1.
   - L6: `builder.py:86-87`, the skip returns `revision = latest[0]`.
   - Residual 1: `_WINDOWS` adds `sel.selected_at <= :k` (`postgres_chain_inputs.py:57`).
   - Residual 2: `_JOBS` adds `available_at <= :k`, and NOT EXISTS a later `analytic_run_selection` of the window
     visible at `:k` (`:63`, `:270`).
6. Guard:
   - `$eventWriter` in `configuration-persistence.ps1`, per P3;
   - `tools/checks/test_event_register.py`, plus a line for it in `tools/check-all.ps1:68`;
   - an estate guard self-test, also covering CH-2's missing CH-1a self-test Low.
7. Tests, per sheet §6:
   - `test_ch1b_register.py`, `test_ch1b_drain.py` and `test_ch1b_outbox_postgres.py`;
   - then the scoped existing files;
   - then L3: `tools/chain_clone.py create ch1b --migrate`, backfill, drain, publish the price, consume and drain,
     `drop`.

## Phase 1 update (after ruling CH1b-R): PARTIAL, resume here

Ruling CH1b-R:
- Q1, Q2 and D1 are accepted.
- Add `TickLimits.chain_consume_events = 500`. A cap hit defers and never backs off.
- **CH-3 merges first.** Do NOT touch `stages.py` or `tick.py` until the coordinator says CH-3 has merged. Then
  rebase on main and make CH-3's `PostgresThreadStore.append_events` and its step-d `chain_threads` call
  event-driven. Wire `consume('lifecycle')` to `run_lifecycle` (CH-3 sheet §4).

Landed in the phase-1 commit:
- `B/chain/adapters/postgres_event_store.py`:
  - implements `EventPort` and `DirtyQueue`;
  - `record_backfill` is the sole Python INSERT into `event_outbox`, with type `'backfill.site'`, source
    `'chain_backfill'` and `ON CONFLICT DO NOTHING`.
- `file_chain_config.load_event_register` (YAML).
- `composition.build_event_store`, and re-exports.
- L6: `builder.py` skip path returns `replace(row, revision=latest[0])`.
- Residual 1: `_WINDOWS` adds `sel.selected_at <= :k`.
- Residual 2: `_JOBS` adds `available_at <= :k`, and NOT EXISTS a later `analytic_run_selection` of the same exact
  window visible at `:k`.
  - It is matched by window, not by `analytic_id`. A selection of another analytic over the identical window would
    also clear the job; this is noted as a residual.
- L2:
  - `PostgresChainInputs._subject_instant`: when there is no period, subjects resolve at the Site-local day start.
    Used by `foundation_assets` and `productive_assets`.
  - `reader._counts`: on a day with any NOT_EXPECTED row, a missing measure counts NOT_EXPECTED.
- L3: `measure_impls.attributed(asset_id, subject, subjects)` per Q1.
  - Chamber raw readings and backup readings are filtered by it.
  - Backup chains are attributed by the window's `policy.generator_asset_id` (`b.get("policy")`). **Verify** that
    `cold_backup_chain` returns `policy`; if it doesn't, the single-subject rule applies.
- `test_ch1a_snapshot_postgres.py::test_downgrade...` now expects the 0044 refusal ("event history exists") first, then
  TRUNCATEs the three 0044 tables. It passes, and the other 3 tests in that file pass.
  - Other downgrade tests below 0044 (0042, 0030, 0029, ...) will need the same pattern. Find them with
    `grep -l "command.downgrade" backend/tests`.

Checks so far:
- `test_ch1a_grading`, `test_ch1a_reassessment` and `test_ch2_threads`: 62 passed.
- `test_ch1a_snapshot_postgres`: 4 passed, after the downgrade-test patch.

Still to do:
1. Guard:
   - `$eventWriter` in `configuration-persistence.ps1`, as in P3 above;
   - `snapshot_dirty` upsert and compare-and-delete;
   - `event_consumption` insert-only;
   - `event_outbox`: only the literal `backfill.site` INSERT from this module, and trigger-only otherwise (anti-vacuity
     by migration text).
   - Then the estate guard self-test, and `tools/checks/test_event_register.py` with its line in `tools/check-all.ps1`.
     Prove each new guard non-vacuous.
2. Tests:
   - `test_ch1b_register.py` and `test_ch1b_drain.py` (pure);
   - `test_ch1b_outbox_postgres.py`, per sheet §6 step 2 (catalogue, rollback leaves no event, one event per
     statement, idempotent consume, re-mark survives, PENDING then settled gives revision 2, drain twice gives 0
     writes, L2, L3, residuals).
3. Backfill step (a): `record_backfill` per Site after `build_range` (`B/chain/backfill.py:113-117`).
4. Scoped existing tests for every source table that gains a trigger (sheet §6 step 3).
5. After CH-3 merges: the tick and stage wiring:
   - `chain_snapshot_seconds`, `chain_snapshot_items` and `chain_consume_events`;
   - the `chain_snapshots` stage;
   - event-driven threads and lifecycle;
   - the CH-0 `SITE_STAGES` update.
   Then the L3 clone proof, the packet `.agent/review-packet-CH-1b.md`, and the commit.

## Phase 1b update (steps 1-4): resume at step 5 after CH-3 merges

Commits: `f6c8803ee` (guards, register guard, backfill event, residual 2, L3 chains, L0 tests), the estate-test
literal repair, the L2 outbox tests, then the downgrade-test harness change (see below).

- Guard (`configuration-persistence.ps1`): `$eventWriter` with four declared statement shapes (`$eventShapes`:
  consumption insert, dirty mark upsert, compare-and-delete on `marked_at`, `'backfill.site'` outbox insert); any
  other statement in the store fails; any other module writing an event table fails (outbox: "written only by the
  migration 0044 triggers"); each shape has anti-vacuity; the 0044 text check (producer INSERT present, exactly the
  `(source, idempotency_key) DO NOTHING` arbiter, no DO UPDATE, both `_immutable` triggers). Placed before
  `$trialComparisonWriter` in `$pgWriters`.
- Estate self-tests (`tools/checks/test_estate_guard.py`): 4 new (snapshot writer = the CH-2 Low, event statements,
  foreign event writes, 0044 arbiter); each mutation proven to fail. All 13 pass (new 4: 338 s; old 9: 500 s).
  They must run from the PowerShell tool (Git Bash subprocess hits the execution policy).
- `tools/checks/test_event_register.py` + check-all line: 11 tests, each rule has a failing mutation.
- Open assumption 1: `cold_backup_chain` does NOT return `policy` (`_backup` returns the envelope + chains). Fixed:
  chains are attributed by `measure_impls.chain_asset` (the one subject asset its step evidence is on), else the
  single-subject rule. Open assumption 2: residual 2 now also matches `x.analytic_id = ANY(:an)` via
  `postgres_chain_inputs.JOB_ANALYTICS` (dispatch / cold-excursion+cold-start-response / ev-session/1).
- Backfill (a): `ChainServices.events` (default None); `_step_a` calls `record_backfill` per Site, key
  `site|from|to`.
- Tests: `test_ch1b_register.py` (`EVENT_FIXTURES`), `test_ch1b_drain.py` (15), `test_ch1b_outbox_postgres.py` (3).
  NOT covered at L2: L2 subject-at-day-start, residual 1/2 SQL (only pure/L3 coverage) — add in step 5 if cheap.
- Downgrade tests: `pg_harness.empty_tables` now always adds `event_outbox` as a root (it has no Site FK, so it
  accumulated); `pg_harness.clear_event_history(engine)` before any downgrade below 0044. Applied to
  `test_ch2_thread_store_postgres`. Remaining downgrade files (`grep -l "command.downgrade" backend/tests`) need
  a run; add `clear_event_history` where they fail with "event history exists".
- Coordinator note for step 5: CH-3 adds `0045_thread_known_at` (down 0042); after rebase re-point 0044's
  `down_revision` to `0045_thread_known_at`. No 0044 producer is on a thread table, so the outbox logic is
  unaffected. Use `tools/chain_clone.py settle <name>` in the L3 proof.

### Step 4 status (downgrade/regression), resume here

- Passed with fixes: `test_ch2_thread_store_postgres` + `test_ch1a_snapshot_postgres` (7 passed, 102 s);
  `test_walk1_objective_min_days_postgres`, `test_walk1_productive_price_postgres` (`clear_event_history` before
  each downgrade), `test_out_d1_schema_postgres` (trigger pin now includes the 0044 statement trigger, tgtype 4),
  `test_cc_schema_postgres`: 31 passed (42 s).
- NOT yet run (a 6-file chunk passed 590 s and was killed by PID; run 1-2 files per call):
  w504, w503, w502, w501, w403, w402 migration, w401 migration, w207, w206, w205a, w204, w203, w201, w200,
  s4_evidence_consequence_work, s4_consequence_store, s405_publication, s2_evidence_ledger, s1_bindings,
  `mini_depth_probe.py` (helper). Fix pattern: `clear_event_history(engine)` before the downgrade; catalogue pins
  that list triggers on a producer table need the `<table>_chain_event` entry.
- Then the scoped producer-table tests (sheet §6 step 3): evidence ledger, analytic runs, mini depth, financial
  assumptions, foundation, finding store, mini decisions, action store, objectives.
- Note: a CH-3 agent runs Postgres tests concurrently on this machine; contention may slow runs.

## Phase 2 update (integration after CH-3; PARTIAL, resume at "Still to do")

Head `34c57f1aa` (main `e207f328f` merged; clean). Commits: `8410676ad` (merge `da5b18391`: T1 0044 down → 0045;
T3 config/composition keep both sides; T2 thread-store tests assert 0044 → 0045 → 0042 refusals in order),
`a99d5faf5` (step 5), `d0ef43f50` + `73b53ce9e` (step 4 downgrade fixes + stage L2 test).

Step 5 landed:
- `tick.py`: `chain_snapshot_seconds=60`, `chain_snapshot_items=200`, `chain_consume_events=500` (>=1, positivity,
  statement-timeout min, lease sum → 1080); `STAGE_LIMIT_FIELDS["chain_snapshots"]`; `_deadline_at(seconds)` =
  now + bound − min(5 s, bound/10); `chain_snapshots` runs after the consequence drains under CONSEQUENCE, failure
  marker `CHAIN_SNAPSHOTS` only on a non-OK code.
- `stages.py`: `chain_threads` = consume('threads') (each event places only its named revisions via
  `PostgresThreadSources.sources_by_revision`, then links `unlinked_actions_for(action_ids, placed finding ids)` so
  a PENDING_PLACEMENT action links when its Finding lands), then `run_lifecycle` once per stage run (CH-3 §4:
  event causes + time-based causes; skipped with `stopped: deadline` if the deadline passed), then
  consume('lifecycle') records the applied events. `deferred` = unconsumed threads+lifecycle events.
  `chain_snapshots` = consume('snapshots') then `drain`; `deferred` = queued rows + unconsumed events.
  No new thread-row writer (placements go through the existing `ThreadRegistry`/store, so T4 known-at holds).
- Event store: `pending()` count and `site()` lookup (SELECTs only).
- Tests: `test_ch1b_drain.py` +3 tick tests (limits, cap hit defers/never backs off, real error fails);
  `test_ch1b_outbox_postgres.py` +1 (real stage bodies: cap defers, consume+drain, rerun 0, threads rerun 0).
  Fake-runner literals updated in `test_w402_mini_stage.py`, `test_fix_cold_drain_stage.py`,
  `test_w403_opportunity_stage.py`, `test_ch0_tick_timing.py`, `test_fix_cold_drain_tick_postgres.py`
  (pre-existing on main: CH-2's `chain_threads` was missing from those fake-runner tests → 17 failures on main).

Checks (counts): pure `test_ch1b_drain/register`, `test_ch0_tick_timing`, `test_fix_cold_drain_stage`,
`test_w402_mini_stage`: 84 passed; `test_w403_opportunity_stage`, `test_ch1a_reassessment`, `test_ch1a_grading`,
`test_ch2_threads`, `test_ch3_lifecycle`: 98 passed. Postgres: ch2 thread store + ch1a snapshot 8 passed;
ch1b outbox 4 passed; ch3 lifecycle + w504 17+2 fixed; w503+w502 24+2 fixed; w501+w403 9 failing → fixed (9 passed
rerun); w402+w401 migration 10 + 6 fixed (10 passed rerun); w207+w206 16 + 5 fixed (12 passed rerun); w205a+w204
13 + 1 fixed; w203 (7 with w204 class) passed; w201+w200 30 + 2 fixed (4 passed rerun); s4 evidence work + s4
consequence store 26 passed; s405 + s2 ledger 54 passed; s1 bindings + w401 18 passed.
Earlier session: walk1 ×2, out_d1, cc_schema 31 passed.

Still to do:
1. Postgres tick tests: `test_fix_cold_drain_tick_postgres.py`, `test_s4_schedule_tick_postgres.py -m "not slow"`,
   `test_w402_mini_stage_postgres.py` (the real tick now runs `chain_snapshots`; check its stage-order literals).
2. Scoped producer-table tests (sheet §6 step 3) not yet named above: finding store, mini decisions, action store
   (`test_s6_action_store_postgres`), objectives (`test_out_d2_*`), financial assumptions, foundation.
3. Guards: `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1` (PowerShell tool; set
   `ASSETOPS_GUARD_PYTHON`); the event-store guard must still accept the two new SELECTs.
4. L3 on a clone: `tools/chain_clone.py create ch1b --migrate`; backfill `--steps a,b,c,d` then rerun (0);
   `chain_clone.py settle ch1b`; publish a productive price via `python -m assetops_backend.publish_assumption
   publish --site KOBO-001 --key productive_use_price_per_kwh --change-kind SUCCESSION ... --valid-from
   2026-10-30T00:00:00+03:00 --expected-prior <current rev>`; run the `chain_snapshots` stage (or a settle tick);
   compare `site_day_snapshot` revisions per measure before/after; collect
   (`tools/checks/chain_coherence.py collect --work C:\Users\assef\Bineyame\AssetOpsV1-polC\var\polish_full
   --database-url <clone url> --out <scratch>`; read-only on polC) and `check --expect
   tools/checks/fixtures/chain_coherence/expected-today.json`; report outbox/consumption counts and drain time vs
   60 s; `chain_clone.py drop ch1b`.
5. Packet `.agent/review-packet-CH-1b.md` (sections per the dispatch), task status, `git add -f`.
