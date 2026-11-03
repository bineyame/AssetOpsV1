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
