# Review packet CH-2: Finding threads, the Action-to-thread link, the backfill

- Build sheet: `AssetOpsV1-plan2/.agent/build-sheet-CH-2.md` (Architect, 2026-11-03). Lane 2.
- Branch `task/CH-2-threads`, worktree `AssetOpsV1-ch2`, cut from main `7fffc8358`, main (CH-0 `26f6edcea`) merged in at `ec600c9ac`.
- Migration `0042_chain_threads`, `down_revision = "0041_walk1_objective_min_days"` (R6: CH-1a's 0043 is not on main; whichever merges second re-points).
- USER_REVIEW_REQUIRED: no UI change (additive fields only). Merge on review ACCEPT.

## Pre-flight (P1-P5), answered from code before building

- **P1.** `mini_opportunity_scope_uk UNIQUE (tenant_id, site_id, id)` (`M/0030:152`). The occurrence FK uses it.
- **P2.** The cheapest board join is one thread lookup per board in `SiteOutcomeBoardService.board()` (`site_outcomes/read.py`), through a new `BoardServices.threads` port (`PostgresThreadSources.lookup`). It enriches `FindingFact.thread` and `ActionFact.thread_id` via `board.with_threads`. `work/domain_action_index.py`, `cold.py:198`, `linked_actions` and `refresh_chain` are untouched.
- **P3.** One extra query per request: `EstateSnapshot.threads` (tenant-wide `ANY(finding_ids)`/`ANY(action_ids)`, plus a `to_regclass` probe). It is not per Site. It is called once in `_portfolio`, once in `site_work_rows`, and once per window group in `site_work_rows_many`.
- **P4.** Stage children are registered in `stages.STAGES`. The head stage CHECK (`M/0030:231-233`) is **not changed**: `chain_threads` runs under the existing `S4` head stage, as cold/EV assess run under `S3`.
- **P5.** The full ids come from the L4 dry run and are in `tools/checks/fixtures/chain_coherence/expected-threads.json` and `.agent/CH-2-l4-dry-run.jsonl`.
- **Architect questions: none blocking.** The assumptions I took are listed under Deviations D-1 to D-5.

## What landed (file anchors)

- `backend/migrations/versions/0042_chain_threads.py` adds:
  - four tables with composite FKs;
  - `ledger_append_only` `_immutable` triggers;
  - the `chain_action_thread_target` BEFORE INSERT trigger, which also checks that `origin_finding_id` matches the target Action;
  - the `chain_action` view and three indexes;
  - a downgrade that refuses with rows, then drops view, triggers, indexes and tables.
- `backend/assetops_backend/chain/`:
  - `threads.py`: the pure core: `Source`, `key_of`, `thread_id_of` (uuid5), `effective_day`, `plan_place`, `MemoryThreads`, `ThreadRegistry`.
  - `lookup.py`: the shared lookup SQL and reducer, with no driver.
  - `adapters/postgres_thread_store.py`: insert-only. One transaction per source, with `pg_advisory_xact_lock` on the key (the guard forbids `ON CONFLICT`).
  - `adapters/postgres_thread_sources.py`: a `$pgReaders` module providing `sources`, `unlinked_actions`, `all_actions`, `lookup` and `opportunity_labels`.
  - `composition.py` and `backfill.py`: the CLI (`--tenant/--site/--steps/--dry-run`, refusal of a non-dry run on the polish/demo3 DBs, one JSON line per step) and `run_threads`.
- Tick:
  - `scheduling/stages.py` gains the `chain_threads` child.
  - `scheduling/tick.py` gains `TickLimits.chain_seconds = 60` (validated; in the lease and statement-timeout bounds), the stage after `s4` under head stage `S4`, a failure marker `CHAIN_THREADS`, and the CH-0 perf map `chain_threads -> chain_seconds`.
- Read path (exactly two joins):
  - `estate/portfolio.py`: `attach_threads` and `_action_for`. The `action_for` inherited by `mini.py:643` matches on thread OR the exact pair (fallback). The row gains `thread`.
  - `site_outcomes/board.py`: the in-hand loop adds a thread match for `is_domain` Actions only when the exact origin is not on the board. The FINDING `ref` gains `thread`.
  - `estate/adapters/postgres_estate_read.py` gains `threads`.
  - `site_outcomes/read.py` and `composition.py` wire the port.
- Frontend: optional `thread` on `EstatePortfolioRow` (`estate/estateClient.ts`) and a new `OutcomeFindingRef` in the `OutcomeIssue.ref` union (`sites/outcomeBoardClient.ts`).
- Coherence:
  - `tools/checks/chain_coherence.py` gains `coh10_thread_identity` and `coh11_actions_linked`. Both apply only to bundles whose Portfolio rows carry the `thread` key.
  - `expected-threads.json` is the COH-10 expectation; a fixture manifest may carry its own `expected_threads`.
  - New failing fixtures: `coh10_thread_occurrence` and `coh11_action_unlinked`.
  - `expected-today.json` drops the three resolved Kobo COH-2 entries.
- Guard: `configuration-persistence.ps1` gains:
  - the `chain` domain entry (shared with CH-1a);
  - `$threadWriter` with its four insert-only tables and anti-vacuity;
  - `postgres_thread_sources.py` in `$pgReaders`;
  - two self-tests in `test_estate_guard.py`.
- Head constants: 23 migration test files are moved to `0042_chain_threads`. In `test_walk1_objective_min_days_postgres.py`, `LATEST` is added and `HEAD` is kept as the migration under test. The stage-order expectations in `test_fix_cold_drain_tick_postgres.py` and `test_ch0_tick_timing.py` now include `chain_threads`. The `test_out_b1_board.py` ref gains `"thread": None`.

## Acceptance per sheet item

| Item | Status | Evidence |
|---|---|---|
| §0 Kobo 17/24/31 Oct are occurrences 1-3 of one thread | Met | L3 clone: `KOBO-001 GENERATOR_SUPPORT_CANDIDATE 3 occurrences (17 Oct, 24 Oct, 31 Oct)`; month Portfolio rows 4d121cdb 1/3, cbbc4916 2/3, 706d2f14 3/3 |
| §0 Cold start failure one thread, 2 occurrences | Met | f9ed0fec (28 Oct) 1/2, 2505d188 (31 Oct) 2/2, same subject asset c4b77b2d (R4: no differing asset ids) |
| §0 every Action and domain Action linked | Met | Clone `chain_action`: ACT-000001 MINI_TRIAL, ACT-000002 / ACT-000003 DOMAIN_INTENT all `thread_id IS NOT NULL`; COH-11 0 findings |
| §0 Portfolio shows ACT-001 on its Finding row (I-03) | Met | COH-2 Kobo resolved in week, S and month; all three Kobo occurrence rows carry ACT-001 through the thread |
| §0 Cold/EV boards list ACT-002/003 in hand when their Finding is on the board | Met, inactive on L3 | The thread match is in place (L0 `test_board_lists_a_domain_action_in_hand_by_thread`). On the clone, ACT-002/003 fall outside the board window (built at build time), so COH-3 does not fire and no in-hand line appears. That is DD-1, per §6 |
| §0 coherence gains thread rules, passes on L3 | Met | COH-10 0, COH-11 0; self-check 36 pass, 0 fail, 0 resolved with the updated expect file |
| §2 migration (tables, FKs, view, triggers, downgrade) | Met | L2 `test_0042_catalogue_and_head`; downgrade refused with rows; target trigger refuses a missing Action |
| §3 plan_place truth table, key_of, uuid5, effective_day | Met | L0: 25 tests |
| §3 writer insert-only, concurrent ticks make one thread | Met | L2 `test_concurrent_placements_of_one_key_make_one_thread` (two Findings of one key, one thread, one event, two occurrences) |
| §3 link_action PENDING_PLACEMENT / idempotent | Met | L0 |
| §4 backfill CLI, steps a/d/e reported skipped, dry-run SELECT only, refusal on protected DBs | Met | L4 run; L3 second run `written: 0` for b and c |
| §4 deterministic, idempotent | Met | L2 full dump compare after two runs; shuffled source order gives identical rows |
| §4 live stage `chain_threads` | Met | Tick tests (cold-drain order); perf map |
| §5.1 Portfolio thread join with fallback | Met | L0 `test_portfolio_join_matches_on_thread_with_exact_fallback`; W303 suites unchanged |
| §5.2 board in-hand thread match; `linked_actions` and `refresh_chain` untouched | Met | Diff touches only the in-hand loop and `_finding_issue` |
| §5.3 additive fields and frontend types | Met | tsc exit 0 |
| §6 COH-10/COH-11; Kobo COH-2 removed from expected-today | Met | See §0. Cold `ced674cb` and EV `b9f71cdd` COH-2 (month, I-09, owner DD-1) stay expected. No COH-3 entries existed, and none fire (the Actions are outside the board windows) |
| §8 guard registration | Met | Self-tests: removing the `finding_thread_event` INSERT fails as "found no INSERT INTO"; an UPDATE probe fails; a reader INSERT probe fails |

## Backfill on the L3 clone (`assetops_chainclone_ch2_test`, created, migrated, dropped)

| Site | Thread | Occurrences |
|---|---|---|
| KOBO-001 | GENERATOR_SUPPORT_CANDIDATE (gen 482da64d) | 3: 17 Oct, 24 Oct, 31 Oct |
| KOBO-001 | PRODUCTIVE_USE_HEADROOM (SITE) | 4: OPP-000001..000004 |
| COLD-LAB-001 | COLD_START_FAILURE | 2: 28 Oct, 31 Oct |
| COLD-LAB-001 | COLD_EXCURSION | 1: 31 Oct |
| EV-LAB-001 | EV_INTERRUPTION | 1: 27 Oct |

- Run 1 wrote 5 threads, 11 occurrences, 5 events and 3 links. The step (b) counts were NEW_THREAD 5, ADDED 6 and ALREADY_PLACED 4 (later revisions).
- Run 2 wrote 0 rows: b `ALREADY_PLACED 15`, c `{}`.
- L4 dry run on `assetops_polish_full_test` (SELECT only; the DB is at 0041, read through the base tables) planned the same rows.

## Checks run (all foreground, `run-host-tests.ps1`, Postgres `*_test` only)

- L0 `test_ch2_threads.py`: 25 passed.
- L2 `test_ch2_thread_store_postgres.py`: 3 passed (in the 58-pass group below).
- Scoped existing tests (unchanged except the expectation edits named above):
  - Pure group, 29 files: 439 passed. It covers `test_s4_finding_episode`, the W303 api/reduction/workflow labels, every pure file importing `estate.portfolio`/`site_outcomes.*`, and `test_ch0_tick_timing` (10 passed).
  - Postgres:
    - `test_out_b1_board`, `test_ch2_thread_store_postgres`, `test_s4_finding_index_postgres`, `test_w303_portfolio_fixture_postgres`, `test_out_b4_board_postgres`, `test_cov_partial_postgres`, `test_idx_gaps_postgres` and `test_qw2_many_postgres`: 58 passed, 552 s.
    - `test_s4_schedule_tick_postgres -m "not slow"`, `test_walk1_objective_min_days_postgres` and `test_s1_bindings_postgres`: passed (27 passed in a group).
    - `test_fix_cold_drain_tick_postgres`: passed after the order edit (13 passed with timing).
    - `test_s6_action_store_postgres`: 12 passed.
    - `test_w303_portfolio_scope_snapshot_postgres`: 10 passed, in three chunks.
    - `test_out_c4_ev_warnings_postgres`: 1 passed.
    - `test_out_d5_objectives_postgres` and `test_w303_portfolio_comparison_postgres`: 7 passed.
  - **`test_out_c3_repeat_visits_postgres`: 1 failed, the same on main `26f6edcea`** (`assert len(chosen) == 1` at :88, an empty summary-window match on today's wall-clock window). This is pre-existing and not caused by CH-2.
- Coherence unit tests `tools/checks/test_chain_coherence.py`: 55 passed.
- Frontend: 15 test files that import the two clients: 361 passed. `npx tsc --noEmit`: exit 0. `vitest related` itself aborts on a `.py` import-analysis error that is not from this diff, so the importing files were run directly.
- Guards (no policy override):
  - `check-architecture.ps1` passed; `check-agent-workflow.ps1` passed.
  - Estate guard self-tests: 9 tests. The thread pair plus `trial_comparison_writer_registered` passed after the pgWriters order fix; the 6 others passed earlier in the run.
  - All other guards are deferred, per the sheet.
- Not run (by the sheet): the full suites, the demo DB build and layout evidence (no UI).

## Deviations

- **D-1 No cutoff on threads.** The thread lookup reads occurrences as stored now. It ignores `known_at`, because backfilled `joined_at` is later than any historical cutoff. A historical read shows the current occurrence count. Board and Portfolio share the behaviour, so COH-10 agrees.
- **D-2 OPP threads are not in any body.** COH-10 checks Finding threads only. `kobo-headroom` is recorded in the fixture with all 4 OPPs: the polish DB has OPP-000001..4, while the sheet named OPP-3 and OPP-4. The backfill output is its proof; CH-4 adds the body field.
- **D-3 Not registered in `setup_cache` FUNCTION_OPS.** `setup_cache.py:73-75` records that `CaseRunner` cannot be cached. The L2 seed uses it, as the sheet asked.
- **D-4 Head stage.** `chain_threads` runs under `S4` (no CHECK change, P4).
- **D-5 The concurrency lock is an advisory xact lock**, not `FOR UPDATE` or `ON CONFLICT`. The guard refuses `ON CONFLICT` in an insert-only writer, and no key row exists before the first insert.
- The L2 domain Action row is a direct INSERT (the cold producer is out of scope). The FK and trigger checks are kept: no replica role.
- Step (a) reports `skipped: CH-1a not merged`. When CH-1a lands, `_step_a` needs its `build_range` call; that is a one-line wiring left to the second merger.

## DS-R1 items (§6b), checked against the diff

1. **Item 3, generator-shaped subject: fixed for threads.** `SUBJECT_COLUMN` is the only domain mapping, and the L0 test registers a fourth domain with one row.
2. **Item 2, exact-revision join: fixed** by the thread join, with the exact fallback.
3. **Item 4, Cold/EV Actions at build time: kept, owned by DD-1.** No window was widened.
4. **`board.py:50` "Verified on example data", the `reserve-trial-1` CHECK, dispatch constants: not touched.**

## Residual risk

- **The Portfolio thread join shows one Action on every occurrence row of a thread** (all three Kobo rows show ACT-001). Placement and confidence for the earlier rows change accordingly. This is the I-03 intent as I read it; the reviewer should confirm.
- **Second merger of 0042/0043:** re-point `down_revision`, update the 23 HEAD constants again, and merge the shared `chain` `$domains` entry.
- **The tick stage writes on every Site tick.** It reads all of the Site's sources each time (no `after` watermark used yet). This is bounded by `chain_seconds = 60`; CH-1b replaces it with outbox events.
- **The `vitest related` failure** (a `.py` import analysis) and the `test_out_c3_repeat_visits_postgres` failure are pre-existing on main.

## Fix round 1 (Part A, review REVISE)

Commit `318c416ae`. Part B (CH-1a integration) waits for the coordinator.

- **M1 (done), Architect rule added.** `opportunity_source` now reads `mini_opportunity.first_day/last_day` (`_OPPORTUNITY_SOURCES`) and sets the episode to the Site-local start of `first_day` through the start of the day after `last_day` (the end of `last_day`, exclusive). The OPEN event `effective_day`, `opened_at` and the occurrence episode follow from it. Migration 0042 gains `finding_thread_occurrence.time_basis` (`story_time` | `recorded_at`, default `story_time`); `plan_place` writes `recorded_at` only when a source has no stored story time (it falls back to `created_at`). Test: `test_opportunity_episode_is_the_study_window_in_site_time_not_build_time` (fails on the old code). Clone `fx2`: the headroom thread's OPEN event `effective_day` is 2026-10-25 and `opened_at` 2026-10-24T21:00Z (first study window starts 25 Oct, Addis); the four occurrences carry the windows 25-29 .. 28 Oct-1 Nov, all `time_basis = story_time` (11 of 11 occurrences).
- **Sweep of other `created_at` use:**

| Item | Time source | Verdict |
|---|---|---|
| Finding thread `opened_at`, OPEN `effective_day`, occurrence episode | `finding_revision.episode_start/end` | Story time. `created_at` only if a revision has no `episode_start` (labelled `recorded_at`; none on the clone). |
| OPP thread | study window `first_day/last_day` | Story time (M1). |
| Source ordering (R2) | `created_at, revision id` | Ordering only, no stored story time, ruled. |
| `finding_thread_occurrence.joined_at`, `chain_action_thread.linked_at` | `clock_timestamp()` | Build time by nature (audit of when the row was written), never shown as story time. |
| Action link / thread events | Actions carry no thread event in CH-2; no time written | none. |
| Domain Actions (Cold, EV) | no thread time is written for them | none. |

  Nothing else in the slice stores a build time as a story time. Items to list for SWEEP-DS: only the `recorded_at` fallback (currently unused on the clone) and the R2 ordering.
- **L2 (done).** The Portfolio row gains the additive `action_thread_id` (the matched Action's own `chain_action_thread` thread; frontend type optional). COH-11 now fails when the row selects an Action and `action_thread_id` is null or differs from the row's thread. Limit: an Action that no row selects (a later Action wins the row) is not observable in a body; the backfill SQL remains its proof. Fixture `coh11_action_link_missing`.
- **L3 (done).** `collect` stamps `manifest.threads = true`; the stamp, not the key, gates COH-10/COH-11. A stamped bundle whose rows lack `thread` or `action_thread_id` fails (COH-0 style); fixture `coh_thread_key_missing`. Unstamped (pre-CH-2) bundles are still skipped. Kobo board-agreement leg: Kobo identity is proven on the Portfolio leg only (no Kobo day board carries a FINDING ref); COH-10 0 therefore covers Cold and EV on the board leg.
- **L4 (done).** `test_ch2_backfill_cli.py`: refusal on both protected names before any read; `--dry-run` reads and never touches a tripping store; a, d, e skipped lines.
- **L7 (done).** The append-only test also runs UPDATE on every table.
- **Left as is.** L1: the thread join is correct. Caveat for CH-3: a new occurrence after a verified change would take ACT-001 through the same join and read "Change verified" instead of RECURRED; CH-3 must constrain the join by thread state or occurrence order. L5 (thread fields ignore `known_at`) is a CH-5a/ChainReader item. L6 (tick stage scans all sources; its failure backs off the whole Site) is a CH-1b item (anti-join placed sources).
- **Non-vacuity (mutate, watch fail, restore):** old `opportunity_source` fails the M1 test; `PROTECTED_DATABASES = ()` fails both refusal tests; dropping the Action-link condition in COH-11 fails `coh11_action_link_missing` and its test; gating `_threaded` on the key again fails the missing-key test. The UPDATE probe and the dry-run store test were not mutated (the UPDATE is refused by the existing trigger; the store fake raises on any access).
- **Checks.** Host: threads + backfill CLI + b1 + tick timing + coherence units, all passed (30 + 58 coherence, 126 earlier group); `test_ch2_thread_store_postgres` + `test_w303_portfolio_fixture_postgres` 5 passed (111 s); portfolio pure files 52 passed; estate guard self-tests (`thread or writer`) 3 passed; `check-architecture.ps1` and `check-agent-workflow.ps1` passed (guard Python set); clone `fx2`: migrate, backfill b 11 / c 3, rerun 0 / 0, collect 56 x 200, check without `--known-at`: COH-10 0, COH-11 0, self-check 36 pass 0 fail; clone dropped. Frontend: `tsc --noEmit` exit 0; the 15 importing files, 361 passed (node_modules junctioned from plan2).
