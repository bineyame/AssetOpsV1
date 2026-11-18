# OPS-01 phase 1 handoff

Branch `task/OPS-01-backend-test-speed`, from main `52189ec7`. Phase 1 is complete; the next step is phase 2 (xdist). Nothing is merged.

## What landed (commits 44984467, 8d2ff5cb, a DELETE-cleanup commit, 3581ad6e, and this closeout)

- `backend/tests/pg_harness.py` is the shared harness:
  - `route()` rewrites `ASSETOPS_TEST_DATABASE_URL` to `<stem>_pt<run>_<tag>_test` and keeps the base URL in `ASSETOPS_TEST_DATABASE_BASE_URL`. `<run>` is the pid in hex plus 4 random hex digits; `<tag>` is `main` serially and `tpl` for the template. The name length is checked against 63. A run that is already routed is left alone.
  - `fresh_database()` creates the template lazily and migrates it once. The template is then locked against connections (`ALLOW_CONNECTIONS false`). Each call then runs `DROP ... WITH (FORCE)` and `CREATE ... TEMPLATE`.
  - `assert_at_head()` checks the Alembic version.
  - `sweep_orphans()` handles killed runs. Every run holds a lease session whose `application_name` is `assetops-test-run:<run>`. Another run's databases are dropped only when that run has neither a lease session nor any session on those databases.
  - `cleanup()` drops only this run's databases. `empty_tables()` and `dispose()` are described below.
  - Escape hatches:
    - `ASSETOPS_TEST_TEMPLATE=0` restores the old in-place reset.
    - `ASSETOPS_TEST_CLEANUP=truncate` restores TRUNCATE.
    - The measurement knobs `ASSETOPS_TEST_CLONE_STRATEGY` and `ASSETOPS_TEST_SYNCHRONOUS_COMMIT` are off by default. When set, they apply only to run-owned databases, never to server settings.
- `backend/tests/conftest.py:79-86`: `pytest_configure` calls `pg_harness.route()` before the basetemp logic (moved into `_choose_basetemp`). `pytest_sessionfinish` calls `cleanup()`.
- `engine` fixtures, with names and imports unchanged:
  - Locations: `test_s1_foundation_postgres.py:~66` and `test_s1_bindings_postgres.py:~64`.
  - Each now calls `fresh_database()`, then `create_engine(URL)`, then `assert_at_head`.
  - The `store` fixtures yield and then call `pg_harness.dispose()`. They empty tables with `pg_harness.empty_tables(engine, ROOTS)` instead of TRUNCATE.
  - `runner` (`test_s4_finding_store_postgres.py`) and `rig` (`test_s2_gateway_access_postgres.py`) yield and dispose the engine they own.
  - `test_s3_demo_configuration.py::TestPostgres` uses `fresh_database()` and disposes its store.
- **DELETE cleanup (a change of mechanism; review it).**
  - What: `empty_tables()` deletes exactly the FK closure that `TRUNCATE <roots> CASCADE` reaches, under `SET LOCAL session_replication_role = replica`.
  - Why: TRUNCATE ends every index rebuild in a forced data-file sync on PG16 (`DataFileImmediateSync`). Measured per call: TRUNCATE took 1.4 s when the disk was quiet and 22-25 s under disk pressure; the DELETE took 0.14 s.
  - Why it is equivalent: the set of tables emptied is the same, neither resets sequences, and the migrations define no TRUNCATE triggers. TRUNCATE also skips row triggers.
  - Proof: `test_pg_harness.py::TestAgainstPostgres::test_delete_cleanup_empties_exactly_the_tables_truncate_cascade_reaches` compares the closure with the tables Postgres's own `truncate cascades to table` notices name, and asserts that the cascade set is non-empty.
- `tests/test_pg_harness.py`: 7 pure tests plus 2 Postgres tests.
- Documentation:
  - `backend/TESTING.md` is new: the guide contract, focused commands, the JUnit zero-skip check, the keep-awake step, the run cap, and timings.
  - `backend/README-db.md` Tests section now links it.
  - `tools/keep-awake-during-tests.ps1` is the coordinator's helper, committed as asked.

## Timings (serial full suite, private base DB, `--durations=30`)

| Run | Code | Wall | Peak client sessions | Result |
| --- | --- | --- | --- | --- |
| base1 | old `52189ec7` | 80.3 min | 90 (91 on `*_test`; max_connections 100) | 2114 passed, 2 failed (see below), 0 skipped |
| new1 | template, TRUNCATE | 41.4 min | 24 | 2123 passed, 0 skipped |
| base2 (stopped) | old | >4 h, reached 34% | – | the machine slept; invalid |
| new2 | template + DELETE | **30.8 min** | **22** | 2125 passed, 0 skipped |
| base2 | old, run from a worktree straight after new2 | **41.4 min** | 91 | 2115 passed, 1 failed (see below) |

- **Back-to-back pair (new2, then base2): 30.8 vs 41.4 min, -26%.** Peak sessions fell from 91 to 22.
- Variance is very large, roughly 2x between runs of the same code (80 vs 41 min). It is concentrated in two single tests: `test_s4_finding_read_postgres::...pinned_lineage` (53-694 s) and `test_s4_finding_evidence_history_postgres::...stored_rows` (91-950 s).
- new1's tick module spent 1383 s in one test, `test_a_hung_stage...`. The same test takes 31 s focused, on both old and new code. That was a disk stall.
- Excluding those two S4 Finding modules, Postgres time was 18.8 min on base2 and 11.1 min on new2.
- The old-code failures were not caused by the harness:
  - base1: `test_s4_schedule_tick_postgres::TestClaimsCrashAndReplay::test_a_crashed_tick_resumes...` failed (`COMPLETED != SKIPPED_CLAIMED`), and so did `TestKillableStagesAndServerTimeouts::test_a_hung_stage...` (`PENDING != LEASED`). These are timing flakes under disk stall, recorded per carry M8.
  - base2: `test_runs_api::...propertyless_foundation` failed because the worktree lacks the untracked `var/sites/mg-001.yaml`.
- The new harness also failed `test_a_hung_stage...` once in a focused run during the stall window. The failure message was not captured; reruns passed in 31-182 s.
- Copy strategy (quiet moment): FILE_COPY re-clone took 0.5 s and WAL_LOG 0.4 s, so the default is kept.
- During the stall, one re-clone took 23 s and the template plus first clone 39 s; a DROP DATABASE waits on a checkpoint (`CheckpointDone`).
- `synchronous_commit=off` was **not measured**. The knob exists, and small commits measured 0.1-0.2 s even during the stall.

## Coverage (M4)

- I compared sorted `--collect-only -q` node IDs: baseline 2116, final 2125.
- Two node IDs in `test_s3_performance_cutover.py::TestRoutes::test_unknown_or_foreign_site_is_404[...]` are built from `uuid4()` at collection time, so they differ on every collection, even between two runs of the same code. With UUIDs normalised, **0 IDs are removed** and 9 are added, all in `tests/test_pg_harness.py`.
- JUnit outcome diff, base1 against new2: two baseline failures (the tick flakes) pass in new2; no test changed from passing to failing.
- Zero DB skips, taken from JUnit, not the summary line: new1 0 skipped, new2 0 skipped, base1 0, base2 0.

## Other proofs

- Non-vacuous guards, each committed first, then mutated and reverted with `git checkout`:
  - Replacing the closure recursion with an empty set makes the TRUNCATE-equivalence test fail.
  - Changing the expected head makes `assert_at_head` fail.
- Cleanup after failure: those failing mutation runs left no `_pt` databases behind.
- Killed run: `test_s1_foundation_postgres.py` was killed mid-module, leaving `..._pt5ad0a079_tpl_test` and `..._main_test`. The next run swept both and then removed its own.
- Laziness: `--collect-only` with the URL set created no database.
- No `_pt` or `assetops_ops01*` databases remain. The scratch worktree has been removed.
- `tools/check-all.ps1`: 9/9 passed on `8d2ff5cb`. It was rerun at closeout (see the commit).

## For phase 2 (anchors and risks)

- Routing for workers:
  - Today `route()` runs in every process and generates its own run id. Under xdist, the controller must pass the run id through `workerinput`, and each worker must call `route(tag=workerid)` with that id.
  - Change `route()` to accept `run`. Workers inherit the controller's environment, so the "already routed" short-circuit (`RUN_ENV` set) would otherwise send every worker to `main`. Have the controller skip routing, or clear `RUN_ENV` per worker.
  - The template: each worker currently builds its own. Building it once in the controller and sharing it is cheaper. Concurrent `CREATE DATABASE ... TEMPLATE` from the same template is fine as long as nothing connects to the template, which is already enforced with `ALLOW_CONNECTIONS false`.
  - `cleanup()` per worker drops the template too. With a shared template, only the controller may drop it.
- The `conftest` basetemp early return for workers (L1) is not done yet.
- Connections:
  - Peak is now about 22 serial, so 2-3 workers fit in `max_connections=100`.
  - Inline stores inside test bodies are still disposed only by GC: CaseRunner methods, the `make_tick` schedule store, S2 `ingestion()`, and S3 `worker()`. The `gc.collect()` fixtures are retained.
  - The real fix for the adapters is a public `dispose()` on the Foundation, Finding, Assessment and Ledger stores. That is production code and is not done.
- Timing-sensitive cases (M8):
  - Tick hung-stage and claims-replay tests (`test_s4_schedule_tick_postgres.py:~396-470`, `~337-374`).
  - Health skew and overlap race (`test_s4_schedule_health_postgres.py:280-317`, `427-503`).
  - Drain 30-second deadline with advisory-lock checks (`test_s4_evidence_drain_postgres.py:398-431`).
  - Work enqueue-lock poll (`test_s4_evidence_consequence_work_postgres.py:386-401`).
  - All of these flake under disk stalls even serially; expect worse under contention.
- The two large S4 Finding tests dominate the variance. Loadfile scheduling should start those modules first.
- Machine sleep invalidated one run. Start `tools/keep-awake-during-tests.ps1` and cap each run at 2x its expected time.
- `.ai/ACTIVE_CONTEXT.md`, `.ai/CODE_STATE.md` and the review packet are left for phase 2 closeout.
