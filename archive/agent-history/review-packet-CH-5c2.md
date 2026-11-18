# Review packet: CH-5c2 (store safety) - branch `task/CH-5c2-store-safety`

Spec: `AssetOpsV1-plan2\.agent\build-sheet-CH-5c.md` §8.6-§8.7; pre-flight `.agent/CH-5c2-preflight.md`;
handoff history `.agent/CH-5c2-handoff.md`. Lane 1. Migration: none new (CH-9 not on `main`; head stays 0048).

## A. Architect-ruling list (decisions the builders made that the sheet did not fix)

| # | Site | What was done and why | Pinning test |
|---|------|-----------------------|--------------|
| 1 | `analytics/cold_reads.py:65` | `read_scope.within(None, window_to, now)` keeps the "future window" note correct and registers `window_to` as a boundary (valid_until). Without it a stored body would keep the old note past `window_to`. | `test_ch5c2_real_composers_postgres.py::test_c4_sweep_over_every_stored_route` (0 violations over 569 seeded instants) |
| 2 | `actions/verification.py current_state` (`:965-966`, `:983`) | `now = at or self.clock()`; the PENDING reason `LATER_WINDOW_OPEN` vs `NOT_EVALUATED` flips at `later_end`, registered through `within`. The `:983` `covering_ids(..., self.clock())` reads Foundation at the request clock (a moved clock moves W through the F/foundation tables, not a boundary). | C4 sweep above; `test_ch5c2_clock_guard.py::test_composer_modules_have_no_unaccounted_clock_read` |
| 3 | `postgres_response_store._LOOKUP`: `valid_until > greatest(clock_timestamp(), :now)` | A live row is a miss once EITHER the DB clock or the app clock (`read_scope.clock()`) passes `valid_until`. The sheet gave only the app clock; the greatest() keeps a host with a lagging app clock from serving an expired body. | `test_ch5c2_store_safety_postgres.py::test_c2_valid_until_is_stored_and_a_moved_clock_misses`, `::test_c2_a_historical_request_never_expires` |
| 4 | Upsert of an EXPIRED row (`_INSERT ... DO UPDATE ... WHERE valid_until <= greatest(clock_timestamp(), :now)`) | Found by L3: an expired live row blocked its own re-warm (`DO NOTHING` made every request after expiry a `race` never stored again, breaking C5 prebuild). The DO UPDATE only fires for an expired row; a live row is never overwritten. The architecture guard (`configuration-persistence.ps1` rule 8) now pins the exact tail and was proven non-vacuous (a looser `WHERE true` fails it). | `test_ch5c2_store_safety_postgres.py::test_l1_an_insert_that_inserted_nothing_sends_no_etag`, `test_ch5c_response_store_postgres.py`, `check-architecture.ps1` |
| 5 | `valid_until` in the ETag (`response_store.etag(..., until)`) | Sheet defines ETag over route/key/W/version. Under #4 a re-warmed body under the same W would otherwise share the expired body's tag (a CH-5b 304 would then revalidate a stale body). | `test_c2_valid_until_is_stored_and_a_moved_clock_misses` |
| 6 | `PostgresConsequenceStore.site_history.work` allowlisted as "not in a stored compose" | Its `now()` predicate sits in a writer-side history read; W6 sees it in 0 composes. Reason recorded in the allowlist entry. | `test_ch5c2_clock_guard.py::test_allowlist_has_no_stale_entry`; W6 run `clock_predicates 0` |
| 7 | Dateless board day `site_overview/read.py db_today` | A dateless board/overview request reads its day from `PostgresScheduleStore.db_now` (DB clock, UTC date), previously unregistered. The midnight cap is Site-local, so a Site west of UTC would have been served yesterday's body after 00:00Z. Now a `read_scope.read_instant` capture that registers the next UTC midnight via `within`. `site_overview.read` and the scheduler store join the module list (124 modules); the schedule store's `db_now` is allowlisted as a capture, its 9 writers as writers. | `test_ch5c2_real_composers_postgres.py` PATHS (dateless board in every test); W6 CLI now requests each board Site dateless (section C) |

## B. Delivered (commits on the branch, oldest first)

- `9e2315ae0` W6 CLI compose mode, F4 audit hook (`ComposeAudit`), Q5 module list capture, C3 listener; L4 trigger-only guard rule.
- `ee87d7385` M1 x3 ports, L1, C2, historical NULL, L4; docstrings; the expired-row upsert fix (#4, #5).
- `4e7240ce7` Q4 parity test (old objective-head SQL vs `current()`).
- `2e6399e3a` `config/chain/stored-composer-modules-v1.json` + C3 SQL allowlist (31 entries) + five composer Python clocks onto `read_scope.clock()`.
- `5d8342845`, `2186fda25` `db_today` fix (#7), real-composer L2 test (Kobo `guardrail` case), C4 sweep (`tools/chain_response_probe.py sweep`).
- `a3c578c0f` W6 CLI also requests each board Site dateless.
- next commit: architecture guard admits the expired-row re-warm (rule 8 regex).
- the packet commit (this file; task `Status: in_review`).

## C. Results

W6 (clone `assetops_chainclone_ch5c2_test`, head `a3c578c0f`, 93 s):
`requests 26 non-200 0 tables read 79 unresolved [] untracked [] event_consumption_read True clock_predicates 0 file_violations 0 modules 124 unlisted_modules []`.
The 26 = 23 prebuilt + 3 dateless boards (one per board Site); `site_overview.read` and `postgres_schedule_store` are both in the observed
module set, so `db_today` is exercised.

Plants through the W6 CLI (committed first, then planted in `site_overview/read.py db_today`, run, `git checkout --`):
- F4: planted `os.listdir(".")` -> `file_violations 1`, rc 1.
- C3: planted `SELECT 1 WHERE now() > now() - interval '1 day'` -> `clock_predicates 1`, rc 1.
Both reverted (`git status` clean).

C4 non-vacuity (clone, `chain_response_probe.py sweep --t0 2026-10-31T01:00:00+00:00 --only "estate/portfolio?from=2026-10-31" --limit 20`):
planted a body field `plant_label = clock().microsecond % 2` (an unregistered clock-dependent label) in `response_store._composed`;
the sweep reported violations (candidates at `03:09:59.999999Z`, `03:10:00.000001Z`, ... all before valid_until `20:59:59Z`), rc 1. Reverted.
Note: the earlier plant (dropping the `within` end registration) did not fail because on this seed no body changes at the placed
`later_end`; the registration is conservative there. A label flipping at an unregistered instant is the visible defect that proves the sweep can fail.
Sweep CLI note: the stored rows must be (re)built at the sweep t0 (the CLI uses the mocked clock), so the `chain_response` rows were deleted first.

Clean C4 sweep on the clone (t0 `2026-10-31T01:00:00Z`, `--limit 8` per path, 4 m 46 s): `paths 23 seeded 7732 candidates 43194 composed 184 violations []`, rc 0.
(The full, unlimited sweep is the L2 test `test_c4_sweep_over_every_stored_route`: 569 seeded instants, ~1720 candidates, 0 violations, 6 passed in 334 s at `2186fda25`.)

Earlier L3 results (head `2e6399e3a`, still apply: composer code unchanged since except `db_today`):
prebuild 23 requests (stored 20, hit 3, 42.5 s); `fresh` 23/23, all rows carry `valid_until`; idle two ticks -> `watermarks --compare` `moved {}`;
F median 3.1-3.3 ms per Site and 8.1 ms for all three (<= 20 ms; the first cold call reached 180 ms from the OS cache).
At the final head prebuild re-ran clean (stored 20, hit 3, `non_200 {}`, 40.5 s).

## D. Q1 table (every clock/`read_at` read near a stored compose, and its disposition)

| Site | Read | Disposition |
|------|------|-------------|
| `actions/verification.py:150` `freeze` | `self.clock()` | writer (plan freeze); not a stored compose |
| `:380` `bind_later_selection` | `self.clock()` | writer; not stored |
| `:548` `evidence` | `recorded_at or self.clock()` | writer-side `known_at`; not stored detail |
| `:785` `evaluate` | `self.clock()` | writer (evaluator); not stored |
| `:904` `_cost_check` | `self.clock()` | writer-side detail; not stored |
| `:965` / `:983` `current_state` | `at or self.clock()` / `covering_ids(.., self.clock())` | stored compose; registered via `within` (ruling #2); C4 sweep clean |
| `work/site_index.py:342-356` read_at refusals | `rx.read_at` vs `known_at` | `read_at` is constant for one live request; refusals never reach a body. `"read_at"` occurs in 0 of 23 stored bodies (SQL over `chain_response.body`); `actions.site_index` is in the module set; `fresh` masks only known_at/selection_token |
| `analytics/service.py:151` `_reconcile` | `self._clock()` | called only from `assess_site` (a writer: appends assessment revisions, `analytics/service.py:134-143`); not a composer path |
| `sites/cutover.py:209` `_current` | `service.now()` | used by `list_sites`; `service.now` is `foundation_service.utc_now`, now `read_scope.clock()` (converted in `2e6399e3a`); module is in the list, covered by F4/Q5 |
| `gateway_api.py:109` `read_gateway_health` | `clock()` | not a stored route; `gateway_api` is not in the module list |
| `site_overview/read.py db_today` | DB `clock_timestamp()` | fixed (ruling #7) |
| Allowlist (41 entries) | | by reference: `backend/tests/test_ch5c2_clock_guard.py` (each with a reason; `test_allowlist_has_no_stale_entry` fails a stale one) |

## E. Guards

- `tools/check-architecture.ps1`: first run FAILED (rule 8 vs the expired-row DO UPDATE, ruling #4); regex updated and the check re-run: passes. Non-vacuity: a planted `WHERE true` in the store SQL fails it with the two rule-8 errors; reverted.
- `tools/check-agent-workflow.ps1`: passed.
- Other check-all guards, one at a time (each exit 0): navigation truthfulness (16 s), dependency registry, delivery fixtures, mock-gap fixtures, missing-claim scan (42 tagged placements, 10 baselined) and its fixtures, evidence width, mock deviation labels, screen ledger (110 screens), chain coherence fixtures (103 passed), event register (12 passed).
- Estate guard self-tests split with per-test node ids (15 tests, 35-85 s each): see the result line at the end of section G.

## F. Known Deviations

1. Rulings #4 and #5 depart from the sheet's insert-only store and its ETag definition (reasons above).
2. Ruling #3 adds the DB clock to the C2 lookup.
3. `seeded_instants` reads only `timestamptz` columns of the change-logged tables; jsonb-embedded times are not read (named residual).
4. The C4 CLI sweep on the clone covers 8 earliest candidates per path (time cap); the full sweep is the L2 test.
5. The first cold F call (180 ms) is an OS-cache effect; the steady figure is 3-8 ms.
6. C4 non-vacuity uses an unregistered synthetic label; a naturally occurring body change at the registered boundary was not found on this seed.
7. The sweep CLI needs store rows built at its own t0 (see section C); documented here, not changed.

## G. End-game E4 check

E4 (at the end of the demo sprint, not now): re-run the W6 CLI and the full C4 sweep on a clone of the FINAL combined dataset, confirm
0 violations / 0 unlisted modules, and re-confirm `chain_response` rows all have `valid_until` after a prebuild; if CH-9 has merged,
re-point to migration 0050 on `0049_mini_service_v2` first and re-run W6 and `fresh` on a merged-tree clone. Lane-2 jobs
(`chain_clone.py`, collect, `mechanism_dataset.py`) must not overlap.
Not run here by owner rule: full suite, demo prepare, `test_demo_combined_postgres`.

Estate self-tests: 15 of 15 passed (each run alone, 35-123 s, none failed).
Focused re-run on the test DB at the final head: `test_ch5c2_clock_guard.py`, `test_ch5c2_store_safety_postgres.py`,
`test_ch5c_response_store_postgres.py`, `test_ch5c_w6_guard_postgres.py` -> 26 passed in 22 s.
Clone `assetops_chainclone_ch5c2_test` dropped (`chain_clone.py drop ch5c2`). No task file for CH-5c2 exists under `tasks/`, so there is no
`Status:` to set; ACTIVE_CONTEXT/CODE_STATE are left to the coordinator.

## Fix round 1 (review-CH-5c2.md, REVISE)

- **M-A** `response_store.valid_until(..., instants=)`: the liveness floor is `min(now, every read_scope.read_instant capture of the
  compose) - 1 s` (`ReadScope.instants`), not `now - 1 s`. L2 `test_ma_a_lagging_db_clock_keeps_its_registered_boundary` (read instant
  5 s behind the app clock) sets `valid_until = END - 1 s`. Non-vacuous: with the old floor planted it failed (`valid_until` fell to the
  23:59:59Z cap); reverted.
- **M-B** C4 sweep on real composers: `t0` fixed at 00:30Z tomorrow (plan `later_end` and outcome edge `t0 + 3 h` fall before every
  midnight cap whenever the test runs); added the current-week Portfolio and scope-ids (`to` after `t0`); asserts the placed boundaries are
  before the cap and that >= 1 path's `valid_until` is below the cap (6 of 8 paths, e.g. `2026-11-06T07:59:59Z` vs cap 20:59:59Z). 6 passed, 112 s.
- **L-1** `valid_until` is inside the M1 `try`; `test_l1_a_bad_site_timezone_serves_the_body_unstored` (`unstored`, no ETag, 200).
- **L-2** the two stale "store off" comments fixed.
- **L-3 residuals (recorded, not fixed):** F4 admits all of `host/` and `backend/migrations/` but `code_version` hashes only `host/**/*.py`
  and `migrations/versions/*.py` (non-`.py` files there pass F4 unhashed; no composer reads any). `os.stat`/`Path.exists`/`Path.resolve` are not
  audit events, so a stat-only read of an undeclared path escapes F4 (per spec F4 names open/listdir/scandir). A per-Site route reading another
  Site's file under a declared prefix passes F4.
- **L-5 residual:** the suite default is `ASSETOPS_RESPONSE_STORE=off` (conftest); route-level tests never exercise the stored path with real
  data writes between requests; closed by the stored-path files above and E4.
- **CH-9 merge** (main `8777bc0f8` merged): migration renamed `0050_chain_response_expiry` on `0049_mini_service_v2`
  (`test_exactly_one_alembic_head` passes); `configuration-persistence.ps1` path updated; `mini_depth.store.database_now` (`SELECT now()`,
  a projection's default knowledge cutoff, no stored composer calls it) allowlisted with that reason; `chain.grading` and `chain.policy`
  (new in stored composes after CH-9) added to `config/chain/stored-composer-modules-v1.json` (126 modules).
  Merged-tree clone (create --migrate, settle, W6, `fresh` store on, drop): W6 `requests 26 non-200 0 tables 79 unresolved [] untracked []
  clock_predicates 0 file_violations 0 modules 126 unlisted_modules []` rc 0; `fresh: 23/23 stored bodies equal a fresh compose`. No chain
  backfill step was run (the clone is a polish copy, already backfilled).
- Checks: clock guard + store_off + store_safety + response_store + w6_guard 45 passed; real_composers 6 passed; architecture and agent-workflow
  guards pass (`ASSETOPS_GUARD_PYTHON` = plan2 venv). No full suite, prepare or `test_demo_combined_postgres` (owner rule).
