# AR-4 packet: Portfolio evidence on stored rows - `evidence.claim` DONE and proven; dispatch.day switch built; `money.lines` and MN-1 MOVED to `task/ANY-2-AR4b`; `evidence.provenance` backlog

**2026-11-12 review M1 closure (D-ANY.8 item 5):** commit `e265813b0` (MN-1 `mini.productive_energy@2` receipts, MN-2 `money.lines` kind/builder/register line/`_assumption_read`, MN-3 no-total guard, pin-test and `test_ch1a_snapshot_postgres.py` MN-1 edits) is reverted on this branch by a revert commit. All of that work stays on `task/ANY-2-AR4b`. Statements below about `money.lines`, MN-1/2/3, its tests and its resume items 1, 2, 4b describe AR4b, not this branch. Claim parity 61/0/0 stays valid: `money.lines` was never served and MN-1 changed no amount. With `ASSETOPS_PERIOD_READ_KINDS` unset the builders are the pre-e265813b0 set (`dispatch.day`, `evidence.claim`, four `mini_depth.*`).

Branch `task/ANY-2-AR4` (worktree `AssetOpsV1-ar4`). main `30a50b2cd` (ANY-1 + AR-2) merged at `6cbdfd5af`. Spec: architect
answer 2026-11-10 §4 AR-4; sequence rev 4; D-ANY.1-7, D-MONEY.1-5. USER_REVIEW_REQUIRED: no (review ACCEPT gates
the merge). Kill switch: `ASSETOPS_PERIOD_READ_KINDS` without `evidence.claim` = today's compose.

## Landed

| Item | Where |
|---|---|
| Phase 1 (`d5382056c`, `d530aa5a0`): kind `evidence.claim`, one row per (mini-grid Site, UTC claim day). It stores the selected window revision and its detail, plus the interval link rows per revision. The pure `project_claim_limit` serves it through `EvidenceMoneySnapshot` | `estate/period_rows.py`, `analytics/claim_limit_read.py`, `estate/adapters/postgres_evidence_money_read.py` |
| Merge with AR-2: both kind sets in `period_kind_builders`/`period_kind_versions`, register `kinds:`, pin tests | `chain/composition.py`, `config/chain/event-register-v1.yaml`, `test_any1_period_read.py`, `test_ch1b_register.py`, `test_ar2_mini_period_rows.py` |
| Rulings in code:<br>- D-ANY.5: a day with no selected revision is projected with no row and no compose (counted `no_revision_days()`).<br>- D-ANY.6a: a row that exists but is PENDING, has an older builder or names another revision is read as today.<br>- D-ANY.7: a selected revision with no row at k is read as today.<br>D-ANY.6a and D-ANY.7 days are logged `period_row_absent` and counted `row_misses()` | `period_rows.RequestRows.claim` |
| Speed fix, builder `estate-evidence-rows-2`. The stored detail was about 4.3 MB per day, because `run.evidence` held every reading of the window, and decoding it cost as much as the compose. It now keeps only ACCEPTED Evidence with the six fields the projection reads (`claim_inputs`). The tagged decode no longer recurses into scalars | `period_rows.claim_inputs`, `decode` |
| Seam fix: the Site lookup moved into the adapter (`EvidenceMoneySnapshot.site_ref`). Before, configuration-persistence failed on raw SQL in `estate/period_rows.py` | `postgres_evidence_money_read.py` |
| Parity adds `any.claim_rows.before_build` and `after_build`: a 7-day Portfolio known 1 s before the first `evidence.claim` row and 1 s after the last. Added when `--kinds` has `evidence.claim` | `tools/checks/period_read_parity.py` |
| The perf child reports `claim_row_misses` and `claim_no_revision` | `tools/checks/perf_budget.py` |

## Checks run (rev in brackets)

**No-DB**
- `test_ar4_evidence_period_rows.py`: 15 passed.
- Adjacent set (23 non-Postgres files: w302, w303, partial_money, pfc, cov_partial, qw2, ch1b, any1, ar2, ar4, dd1b2b_drain, fix_cold_drain): 492 passed, 5 skipped, 2 failed. Both failures are an environment ImportError: the venv's contracts point at the main checkout. With the worktree `contracts` on PYTHONPATH, `test_w302_evidence_api.py` gives 19 passed.
- Parity self-test: PASS. `test_period_read_parity.py` + `test_perf_budget.py`: 26 passed.

**Postgres** (own `assetops_ar4_test`, one file at a time, all through `tools/run-host-tests.ps1`, so the worktree's `gateway`/`field` are used; parity ran with them on PYTHONPATH)
- `test_ar4_evidence_period_rows_postgres.py` (new) [`e42c5a354`]: 1 passed, wall 64 s, JUnit tests 1 / failures 0 / errors 0 / skipped 0.
  - F02 rows vs compose of `/api/estate/evidence`, JSON byte-equal: live, historical k, k before revision 1, and a 1-day sub-range.
  - A late assessment then gives 2 misses while PENDING. It still gives 2 after its events are consumed (the revision check alone does that), and 0 after the rebuild.
  - Non-vacuity: dropping the revision check makes the test fail at :107 (stale ceiling served). Reverted with `git checkout`.
- `test_w302_w1_claim_limit_on_postgres.py`: 7 passed (157 s). `test_w302_evidence_scope_snapshot_postgres.py`: 3 passed (117 s) [`cc7c55148`].
- The evidence API refuses an unaligned window (422 INVALID_WINDOW). Unaligned windows are covered on the Portfolio by parity instead.

**client4 build** (`python -m assetops_backend.chain.period_backfill build --site <S> --kind evidence.claim --quiet`)
- v1: KOBO 34 of 66 written, 257 s. KISIWA 15 of 28 written, 51 s.
- v2: KOBO 34 written, 126 s. KISIWA 15 written, 29 s.

**client4 parity** (`--kinds evidence.claim --seed 20261111 --random 16`; e3c polish_client4 `--work`/`--story`; prebuilt routes)
- v1 rows [`1d01db95e`], wall 2379 s (other lanes were running): **`PASS (61 cases, 0 mismatch, 0 unstable)`**. This includes `any.claim_rows.before_build` / `after_build` and `any.between_revisions.site_day_snapshot`.
- v2 rows [`e42c5a354`], start 04:37, wall 1527 s: **`PASS (61 cases, 0 mismatch, 0 unstable)`**, exit 0. This includes both `claim_rows` cases.
- The covered sets are non-empty. The perf child on `before_build` (rows on) shows `misses=7` (D-ANY.7) and `norev=7` (D-ANY.5); the 22-day range shows `norev=21`.

**Timing on client4** (cold, fresh process, response store off; other lanes were running tests, so noise is about ±15%)

| Request | rows off | `evidence.claim` v1 | `evidence.claim` v2 |
|---|---|---|---|
| unlisted week 10-19..10-26 | 17.6-19.4 s (5 runs) | 18.3-19.3 s (3) | **11.7, 14.5 s** |
| 22 days 10-14..11-05 | 44.2-45.1 s (3) | 43.7 s | **37.0, 39.1 s** |

**Where the rest goes** (cProfile, week, rows on)
- `estate/coverage.py _mini_grid_basis`: 17.6 s. About 13 s of that is `dispatch_days` → `assessment._window`, which is the per-day dispatch selection that AR-3's `dispatch.day` owns. `estate/coverage` is AR-3's file and was not touched.
- Next: `coverage._mini_grid_money` 4.1 s and `consequence_provenance` 3.3 s.
- **AR-4 alone cannot reach the board-like target. AR-3's `dispatch.day` is the dominant term.**

**check-all** (19 guards) [`8b2c4f24b`]: 15 PASS, 4 FAIL.
- Architecture seams: my raw SQL. Fixed in `1d01db95e`; `check-architecture.ps1` then reports "Architecture check passed."
- Estate guard self-tests: 3 failures with the same cause. Not rerun (41 min under load).
- Missing-claim scan and its fixtures: `Cannot find module 'typescript'`. The worktree has no `frontend/node_modules`, so this is environment; it passes on the main checkout.

## Session 2026-11-12 (D-ANY.8 steps 1 and 3, code + no-DB only)

| Commit | What |
|---|---|
| `714650582` | Merge main `4099e40fb` (one import conflict in `evidence_money.py`) |
| `e265813b0` | **MN-1**: `productive_kwh` day money gains `basis` + `receipt{v, formula, qty (unrounded), unit, rate, rate_unit, rate_ref, rounding, segments, fx}`; amount unchanged; adapter `mini.productive_energy@2` (new input_fp, so a rebuild appends). **MN-2**: kind `money.lines` (`estate/money_rows.py`), per (mini-grid Site, local day) the potential line (study headroom x 1 h x the productive price valid at the day start, receipt shape, byte-equal to `PricedEnergy._potential`), body names the `study` and `price` it used. **MN-3**: `financials/money_lines.refuse_totals` enforced at build + AST no-`sum` scan of the money writers. **Rev-5 contract**: register `money.lines` inputs `assumption_keys: [productive_use_price_per_kwh]` (+ the renewable inputs); `price.revised@1` (0044 trigger, the event PR-3's `SITE_ADMIN_ENTRY` insert raises) with an open `valid` dirties every day from its applies-from date to today; the drain rebuilds them |
| `e37294b73` | Merge main `ef02bd649` (AR-3 + AR-6). Conflicts in `chain/composition.py` and 3 pin tests resolved: all kinds built side by side. `evidence.claim` (an `s3_day` kind) now takes AR-3's UTC-day rule for Foundation events (pinned in `test_ch1b_register`) |
| `36d15fd70` | **Step 3 switch**: `evidence_money.mini_grid_rows` reads `coverage.dispatch_days` (AR-3 rows when served, else compose) and notes those days for the claim rows (`EvidenceMoneySnapshot.note_page_days`). Non-vacuity: reverting to `snap.dispatch_days` fails the new test (1 failed), reverted with `git checkout` |

Checks: `test_ar4_money_lines.py` 15 passed; `test_ar4_evidence_period_rows.py` 17 passed; adjacent no-DB set after both merges and the switch (any1, ar2, ar3, ar4, ar6, ch1b, ch6, cov_partial, dd1b2b, fix_cold_drain, hon1, out_c, partial_money, pfc, qw2, w302, w303, walk1_productive; 41 files) `805 passed, 5 skipped` [`36d15fd70`]; ch5a1/ch5b/ch6_contract/ch6b/k10/pb3/demo_combined_finish_rows 188 passed, 1 skipped [`e265813b0`]; `check-architecture.ps1` "Architecture check passed." (needs `ASSETOPS_GUARD_PYTHON`). `tools/checks/test_estate_guard.py` from Git Bash: 16 failed, all `_common.ps1 cannot be loaded because running scripts is disabled` (execution policy, environment); launched from PowerShell (tree as of `714650582`/`e265813b0`): **16 passed in 2038 s** - the earlier 3 failures are closed.

## Session 2026-11-12 06:00 (D-ANY.8 17 Nov minimum evidence, client4 `assetops_polish_client4_test`, head `ba227df16`)

- `tools/checks/test_estate_guard.py` from PowerShell (plan2 venv, `ASSETOPS_GUARD_PYTHON` set): **16 passed**, 1980 s.
- client4 rows already current, nothing rebuilt: `evidence.claim` `estate-evidence-rows-2` (33 SELECTED + 16 UNASSESSED), `dispatch.day` `dispatch-day-rows-1` (33 CURRENT + 29 UNASSESSED, 10-10..11-09, built 2026-11-12 00:03).
- **Parity** `--kinds evidence.claim,dispatch.day --seed 20261111 --random 16`, e3c polish_client4 work/story, prebuilt routes, wall 1815 s: **FAIL (61 cases, 1 mismatch, 0 unstable)**. Every case passes except `any.claim_rows.before_build` (known_at 2026-11-11T23:35Z): oracle has `selection_id`, candidate has `selection_id null / match_state MISSING` (byte 1118). `any.claim_rows.after_build` and `any.between_revisions.*` PASS.
  - Cause (read from `dispatch_day_rows.py`, not yet proven by a mutation): the dispatch.day rows were built at 00:03 on 11-12, AFTER that known_at, so the explicit-k read finds no row and `absent_day` renders "nothing stored" (D-ANY.5, no fallback compose by AR-3's design), while compose sees the assessment that existed at k. The case's known_at is tied to the claim build (23:40); dispatch rows were built later, so no known_at exists between the two builds. Architect options: (a) set the case k after the dispatch build and document "k before any row" as a backfill-age effect; (b) give the dispatch.day read a compose fallback for no-row-at-explicit-k when a revision is selected (as D-ANY.7 does for claims).
  - Step-3 deviation (D-ANY.9): `note_page_days` (`36d15fd70`) accepted. The Portfolio cases whose claim days follow AR-3 rows (the `any.portfolio.*` cases and `any.claim_rows.after_build`) exercise it and PASS byte-equal; the 22-day perf child shows `claim_no_revision=21`, `period_row_absent=16`.
- **Timings** (cold, fresh process, store off, `/api/estate/portfolio?...&lens=all`, aligned UTC windows, one run each, about +-15% noise):

| Request | rows off | claim + dispatch.day rows on |
|---|---|---|
| week 10-19..10-26 | 10.9 s | 9.3 s |
| 22 days 10-14..11-05 | 27.0 s | 24.8 s |
| 31 days 10-10..11-10 | 33.0 s | 29.0 s |

  Gain is 1.7-4 s, not the ~13 s the earlier profile promised.
- **Why (cProfile, week, rows on, 41 s under profile):** `claims._data_gaps` -> `data_gap_provider` -> `evidence_money.py:577` `data_gap_days(snap.dispatch_days(...))` composes the dispatch days again, 16.1 s cumulative. It is a second caller `36d15fd70` did not switch (it switched only `mini_grid_rows`). Next: `_mini_grid_basis` 8.7 s (3 calls), `_mini_grid_money` 6.2 s, `consequence_provenance` 0.5 s (profile). **The ~4 s in `_mini_grid_money`/`consequence_provenance` stays unstored for 17 Nov (backlog `evidence.consequence_money`, D-ANY.9).** Likely fix, not done here: point `evidence_money.py:577` at `coverage.dispatch_days`, then re-measure.

## Session 2026-11-12 (D-ANY.10 item 4: `_data_gaps` through `coverage.dispatch_days`)

- `estate/evidence_money.py` `site_data_gap_days_many` now calls `coverage.dispatch_days(snap, ...)` (was `snap.dispatch_days`). New no-DB test `test_data_gaps_read_through_the_coverage_dispatch_days` (`test_ar4_evidence_period_rows.py`); non-vacuity: temporarily reverted with Edit -> 1 failed, restored.
- No-DB: AR-4 files 33 passed; with adjacent estate/claims/gap files (15 files) 257 passed.
- Profile (client4 read-only, no DB writes, cold process, store off, `evidence.claim,dispatch.day` rows on, unlisted week 10-19..10-26 portfolio lens=all): **8.1 s total (8.6 s under cProfile)** vs 9.3 s before. `claims._data_gaps` 0.094 s cumulative (was 16.1 s under profile); `snapshot.dispatch_days` no longer under it (`select_dispatch_days_on` 4 calls 2.2 s, all from `_mini_grid_basis`/`mini_grid_rows`). Probe script: scratchpad `prof_week.py`, not committed.

## Resume points (first = next)

0. DONE 07:25: main merged, parity 0/61, timings and the `select_dispatch_days_on` cause recorded above. Next is the D-ANY.9 `evidence.consequence_money` decision (the `for_finding_on` calls).

## Session 2026-11-12 07:00-07:25 (after merging main `eedd2659f`, AR-3 absent-compose; client4, read-only)

- No-DB after merge: 75 passed (ar4 x2, ar3_dispatch_day_rows, estate_coverage_local_days, w301_estate_coverage).
- **Parity** `--kinds evidence.claim,dispatch.day --seed 20261111 --random 16`, e3c polish_client4 work/story, prebuilt routes, ~21 min: **PASS (61 cases, 0 mismatch, 0 unstable)**; `any.claim_rows.before_build` now PASS.
- **Timings** (cold fresh process, store off, rows `evidence.claim,dispatch.day` on, `/api/estate/portfolio?...&lens=all`, wall under cProfile; one run, +-15%):

| Request | 917a90724 (rows on, no item 4) | now |
|---|---|---|
| week 10-19..10-26 | 9.3 s | 8.7 s (8.1, 9.5 on two other runs) |
| 22 days 10-14..11-05 | 24.8 s | 22.2 s |
| 31 days 10-10..11-10 | 29.0 s | 27.1 s |

  `claims._data_gaps` is 0.10 / 0.13 / 0.16 s (was 16.1 s in the week profile). Probe: scratchpad `prof_win.py` (not committed).
- **The four `select_dispatch_days_on` calls (week 1.7-2.3 s; 12 calls 6.5 s at 22 days; 16 calls 6.8 s at 31 days):** `print_callers` shows ALL come from `financials/money_eligibility.py:192 for_finding_on` (W3-01 per-bracketed-UTC-day money-eligibility selector), reached through the money path. None come from `_mini_grid_basis` or `mini_grid_rows` (those go through `coverage.dispatch_days`). `for_finding_on` is outside AR-4's files and calls the store directly through its own `days` port. The fix is the D-ANY.9 backlog `evidence.consequence_money` (read stored `dispatch.day` rows there). Not fixed on AR-4: above 0.3 units and not AR-4's files.

## Not built (resume here, D-ANY.8 order)

1. **money.lines read side (MN-2 rest):** `site_outcomes/mini.py` -> `NodeInputs` gains the stored day line; `OutcomeEvaluator._potential` uses it only when the row is current at k (not PENDING) and its `study`/`price` equal the page's item and `sales["price"]`, else today's compose (D-ANY.6a). Kill switch: `money.lines` in `ASSETOPS_PERIOD_READ_KINDS`.
2. **Postgres (one file at a time, own `assetops_ar4_test`):** `test_ar4_money_lines_postgres.py` - rows equal to compose for a priced and an unpriced day; a PR-3-style `SITE_ADMIN_ENTRY` revision mid-range -> `price.revised` -> drain -> rows from the valid date to today are new revisions with the new `rate_ref`, still equal to compose before and after. Rerun `test_ch1a_snapshot_postgres.py` (its money asserts were updated for MN-1, not run).
3. (D-ANY.8 4a) Parity on client4 with `--kinds evidence.claim,dispatch.day` over the switch, keeping the D-ANY.5/7 cases; timings (week, 22 days, 31 days) cold, store off, with profiles.
4. (4b) money.lines parity incl. the price-save case; build `money.lines` rows on client4 (`period_backfill build --kind money.lines`). If not passing by Sat 12:00, move commits `e265813b0` (and the read side) to `task/ANY-2-AR4b`.
5. Rerun `test_estate_guard.py` from PowerShell (not Git Bash).
6. PR-3's Postgres flow test is rerun by whichever of AR-4 / PR-3 merges second.
7. Backlog: `evidence.provenance` (cold/EV pinned windows); the Portfolio consequence money (`_mini_grid_money` / `consequence_provenance`, ~4 s on client4) is NOT covered by `money.lines` as built - needs an Architect call (store the per-(consequence, Finding) revision provenance like `revision_provenance`?).
8. To serve on a demo DB: build rows, then add the kinds to `ASSETOPS_PERIOD_READ_KINDS`.

## Known deviations

0. (D-ANY.10 item 4) `site_data_gap_days_many` calls `coverage.dispatch_days` rather than `snap.dispatch_days`; `period_rows.fragment` is a row builder and keeps composing.

1. The dispatch-day selection is not stored. It is the page's own `select_dispatch_days_on` (AR-3's `dispatch.day`), and it stays the dominant cost.
2. Link rows are stored as of build time (same as AR-2 deviation 4).
3. Rows are read once per Site: one reader read plus one provenance statement.
4. The stored detail is pruned to the Evidence fields the projection reads (`claim_inputs`). A future reader of any other stored field must bump the builder version.
5. MN-1 says old rows "read PENDING until the backfill". `site_day_snapshot` has no adapter-version PENDING rule, so old productive rows keep serving their (unchanged) amount without a receipt until rebuilt. Readers use only `amount`/`currency`/`assumption_revision_id`, so values are equal.
6. `money.lines` holds the potential line only. The spec's "per (Site, day) money lines" for the Portfolio consequence path is not stored (Not built 7).
7. An opportunity study revision raises no day event (`opportunity.revised@1` is `days: none`), so the read side must compare the stored `study` with the page's (Not built 1).
8. The `money.lines` price is read at the local day start (`valid_at`), as the board's `productive_price(start)` does.
9. The step-3 mutation proof used `sed -i` on a committed file and was reverted with `git checkout` (lane rules prefer Edit).
