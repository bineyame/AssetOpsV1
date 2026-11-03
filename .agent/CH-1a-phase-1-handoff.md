# CH-1a phase 1 handoff (PARTIAL: stopped at the context budget)

- Branch `task/CH-1a-snapshots`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch1a`, head `59a813a93`.
- The authority is `AssetOpsV1-plan2\.agent\build-sheet-CH-1a.md`, including the §5c rulings. The pre-flight evidence is `.agent/CH-1a-preflight.md`.
- `B/` = `backend/assetops_backend/`.

## Landed (committed)

- `backend/migrations/versions/0043_chain_snapshots.py`:
  - `down_revision` = 0041;
  - the CHECKs, both indexes, and the trigger;
  - the downgrade refuses when rows exist.
  - It migrates to head cleanly: `test_out_b4_board_postgres` used a fresh database.
- `config/chain/coverage-policy-v1.json` and `operating-calendar-v1.json`, following the §2 ruling: Kobo and Cold 24 h, EV Tuesdays 08:00–16:00 with `source`.
- `B/chain/policy.py` holds the records and validation, with `CALENDAR_KINDS = ("OPERATING",)`, `PERIODS` and `MIDDAY_WINDOW_LOCAL` (the DS-R1 keep comment). The file read lives in `B/chain/adapters/file_chain_config.py` because guard rule 2 bans `pathlib`/`open(` above adapters; it is re-exported by `B/chain/composition.py`.
- `B/chain/grading.py` (pure): `period_bounds`, `covered_seconds`, `classify_day`, `coverage_pct`, `input_fp`.
- `B/chain/ports.py`:
  - `SiteRef`, `DayCtx`, `InputSet` (with an adapter-private `payload`), `SnapshotKey`, `SnapshotRow`;
  - the `SnapshotStore` Protocol;
  - the `ChainInputReader` Protocol, a method list proposal; adjust it to the rulings.
- `B/chain/measures.py`: `MeasureSpec`, `MEASURES` (6 entries, adapter keys) and `measures_for(site_type)`. There are no outcome literals.
- `B/chain/builder.py`: `SnapshotBuilder(store, adapters: {adapter_key: MeasureAdapter}, policy, calendar)`, with `.build(...)` and `.build_range(...)`, following the §4.2 steps. It skips on an equal fp.
- `B/chain/adapters/postgres_snapshot_store.py`: `latest`, `append` (INSERT only) and `read_latest` (one `DISTINCT ON` statement over many Sites).
- `B/chain/reader.py`: `GradeCounts`, `SnapshotReader.latest`, `.grade_counts` and `.grade_counts_many` (one store call). The day-level grade is the weakest grade across the listed measures and subjects; a missing row counts as NO_DATA.
- Ruling Q3c: `dispatch_minutes(dispatch)` was moved unchanged into `B/analytics/dispatch_read.py:49`.
  - `B/site_outcomes/mini.py:21` imports it, and `:617` keeps the alias `_dispatch_minutes = dispatch_minutes`, because `test_out_d5_objectives_postgres.py:98` reads `mini._dispatch_minutes` and tests must not change.
  - The signature still takes the dispatch dict, not `intervals`, because "unchanged" wins. Record this as a deviation.
- The guard registration in `tools/checks/configuration-persistence.ps1`:
  - the `chain` domain;
  - `$snapshotWriter` / `$snapshotTables`;
  - `$pgWriters`, `$pgWritesSeen` and `$pgDriverSeen`;
  - the `$actionForbidden` refusal;
  - the insert-only and owner checks;
  - anti-vacuity;
  - `$pgReaders` gains `chain/adapters/postgres_chain_inputs.py`, which does not exist yet.
  - The Architecture seams guard passed before the dispatch move. Rerun it.

## Checks so far

- `tools\run-host-tests.ps1 -- backend/tests/test_ch1a_grading.py backend/tests/test_out_b1_board.py backend/tests/test_out_b4_board_postgres.py`: **58 passed** (201 s), on `59a813a93`.
- Run every `.ps1` through the **PowerShell tool**, not `powershell -File` from Bash. Never pass a policy flag.

## Next (in order)

1. **`B/chain/adapters/postgres_chain_inputs.py`** (registered reader, SELECT only). It implements `ChainInputReader`, built from existing services:
   - `MiniDepthRead(engine, link_rows=None).productive_users` / `.productive_readings` (`B/mini_depth/read.py:358/382`);
   - `financials.composition.build_assumption_read_service(url).series(...)` with `selection`;
   - `DispatchReadService.window(t, s, utc_day)` for both UTC days, where the interval rows carry `evidence_ids` (the coverage evidence comes from the `accepted_evidence` interval_start/interval_end of those ids);
   - the stored selected `mini_depth_revision.result` (`hour.headroom_kw`, `hour.decision`, `coverage.gaps`), using `MiniDepthRead` `_HEAD` (`read.py:141`) or your own SELECT;
   - `ColdReadService.temperature` / `.backup_chain` (`B/analytics/adapters/postgres_assessment_store.py:2191/2240`), plus raw `chamber_temperature` readings and the backup-role readings (`grid_power_event`, `generator_state`, `transfer_result`, `backup_bus_state`) for coverage;
   - `EvSiteReads.overview` (`B/ev_site_reads.py:595`), which gives the sessions, `energy`, `consequence_summary` and the status intervals, for the §5c Q1 coverage;
   - `recompute_job` PENDING or LEASED for domains `dispatch`, `mini_renewable`, `cold_chain` and `ev_charging`.
   - Construction needs other domains' composition (not adapters) or SQL. Guard rule 1 forbids importing another domain's `adapters` outside its own composition. So build the services in `chain/composition.py` through `analytics`/`financials` composition functions, if they exist; check with grep.
2. **The measure adapters**, one per `MEASURES` adapter key, for example in `B/chain/measure_adapters.py`, following the §3 table and the §5c rulings:
   - productive: call `productive_energy`;
   - money: `quantize(0.01, HALF_UP)`, with `assumption_revision_id` = the selection's `revision_id`; 0 kWh gives "0.00"; the price revision id goes into the fp ids;
   - noon: LIMITED/CONFLICT give null values plus `result_state`;
   - backup: `starts: 0` on a covered night;
   - chamber: the max raw probe reading.
3. **`chain/composition.py`** `build_snapshot_builder(url)` / `build_snapshot_reader(url)`, and the CLI `B/chain/snapshots.py`, modelled on `B/declare_objective.py:67-110`.
4. **L2** `backend/tests/test_ch1a_snapshot_postgres.py`, following §6 step 2 and ruling Q8:
   - the catalogue, update/delete refusal and downgrade parts;
   - the stub reader with the real store for productive, idempotency and revision 2;
   - the real noon adapter on MG-W402 (`test_w402_reads_postgres._setup/_ingest/_reconcile`, already in `setup_cache.FUNCTION_OPS`);
   - `grade_counts_many` equals per-Site results, in one statement.
5. **The existing scoped tests** (§6 step 3), plus `test_w402_rules.py`, `test_w402_projection.py`, `test_w402_reads.py`, `test_w402_inputs_postgres.py`, `test_walk1_productive_sales.py` and `test_out_d5_objectives_postgres.py`.
6. **Guards:** Architecture seams, Agent workflow, and the estate guard self-tests (`tools/checks/test_estate_guard.py`). Prove the snapshot guard is not vacuous: commit, then add `DELETE FROM site_day_snapshot` to the store, watch the guard fail, and run `git checkout --`.
7. **L3**, once CH-0 merges: merge main, then `tools/chain_clone.py create ch1a --migrate`, build, show, time, rebuild (0 rows), drop. Compare against §5 as revised.
8. **The packet** `.agent/review-packet-CH-1a.md`.

## Open risks

- Kobo has no productive user before the WALK1 `configure_at` revision. The days before it give 0 subjects, so no rows, and `grade_counts` counts them NO_DATA.
- The EV status intervals for the Q1 coverage: check that `EvSiteReads` exposes the reported connector status intervals. If it does not, raise it with the Architect; do not invent a basis.
