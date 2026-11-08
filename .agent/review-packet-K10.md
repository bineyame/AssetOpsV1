# Review packet: DIESEL-K10 v2 (declared-absent productive use), phase 1 (code and tests)

- Ruling: `.agent/build-sheet-DIESEL-1.md` §9t (DIESEL-1-R3t), binding; owner answer "Build it (Recommended)" in
  `.agent/owner-kisiwa-measure-applicability-2026-11-08.md`.
- Branch `task/DIESEL-K10-declared-absent` (worktree `AssetOpsV1-k10`) from main `ae6d4cb71`. The dispatch named
  that branch; R3t §9t.3 wrote `task/DIESEL-K10-declared-none`. The dispatch wins.
- Commit: `56256bbc9` (code and tests). Phase 2 (clone proof, Postgres adapter run, served bodies) is not started.

## Outcome delivered

Implemented as R3t specifies:
- `productive_kwh` with no row, on a day whose site setup provably declares no productive-use load, is left out of
  that day's applicable measures. It is never graded, never COMPLETE and never a gap.
- The board states the zero in four places: the Grow line, the headline, the MG-1 earnings node and the gap note.
- Every other measure and every Site with no declaration keeps today's rule.

## Files materially changed

| File | Change |
|---|---|
| `backend/assetops_backend/chain/reader.py` | `DECLARED_SUBJECT_MEASURES`, `applicable_measures`. `_counts`/`counts` take `none_declared`. `grade_counts_of` passes `facts.none_declared`. `GradeCounts`, `SnapshotReader.grade_counts(_many)` unchanged. |
| `backend/assetops_backend/chain/read.py` | `_day_grades`, `readiness_of`, `day_grade`, `day_settled`, `day_gaps` take a keyword-only `none_declared`. `DayFacts.none_declared`. `ChainRequest.day` calls `_none_declared`: candidate set, lazy trigger, `getattr` port, `read_scope.memo("chain.none_declared", ...)`. `ChainReadPort` documents the optional method. |
| `backend/assetops_backend/chain/adapters/postgres_chain_read.py` | `_DECLARED_NONE` (one statement: site timezone LEFT JOIN Foundation revisions known at k overlapping the window). Pure `declared_none_of(tz, revisions, days)`: exactly one revision at the local start and at local end − 1 µs, each with `productive_loads == []`. `PostgresChainRead.declared_none_days`. |
| `backend/assetops_backend/mini_depth/read.py` | `productive_loads(content)` extracted. `productive_users` calls it. |
| `backend/assetops_backend/chain/outcomes.py`, `chain/vocabulary.py` | `NodeInputs.none_declared`. In `_earnings`, a non-FINDING record with the measure declared absent and no rows returns `money_claim(label, None, None, "NONE_DECLARED")`. `money.none_declared` literal. |
| `backend/assetops_backend/site_outcomes/mini.py` | Literals `SALES_NONE_DECLARED`, `GROW_NONE_HEADLINE`, `GAPS_NONE_DECLARED` (MD-K10-1, added to `COPY`). `decl` feeds `_productive_sales`. Headline falls back to the spare-solar headline. `node_in.none_declared`. `finding_gap_line` has its three forms. |
| `backend/tests/test_ch6_claims.py` | The pinned A4 node-text table gains the R3t `money.none_declared` row. This is a required update, not a loosened guard. |
| `backend/tests/test_k10_declared_none_{rule,board,adapter_postgres}.py` | New: R3t's three targeted files. |

## R3t items: status and evidence

| R3t item | Status | Evidence |
|---|---|---|
| 1 Shared rule in `reader.py`, used by `read.py`, `_counts`, `grade_counts_of` | done | rule tests 1–7. `read.py` imports `applicable_measures` and `DECLARED_SUBJECT_MEASURES` from `reader.py` (one rule). |
| 2 `read.py` keywords and `DayFacts`; `ChainRequest.day` steps 1–5; port error propagates | done | `test_chain_day_*`, `test_8_lazy_trigger_*`, `test_port_without_method_declares_nothing`, `test_port_error_propagates` |
| 3 Port, adapter, shared filter | code done; Postgres run deferred to phase 2 | pure coverage rule: `test_declared_none_of_needs_exactly_one_revision_at_both_bounds`. Postgres file has R3t's 6 cases (one/no-load, load, none, two overlapping, change inside the day, one statement). It skips without `ASSETOPS_TEST_DATABASE_URL` and was **not run** (rehearsal DB rule). |
| 4 Evaluator `NONE_DECLARED`, never summed | done | board test: earnings text is the literal and `value is None` |
| 5 Board lines, headline, node window, gap line | done | board tests: line/headline/earnings, spare solar leads, `SALES_NO_USERS` kept without `decl`, gap line three forms, `finding_gaps` on the board |
| Literals, exact | done, but see Stop K10-v1 | `test_literals_are_r3t_exactly` |

**Safeguards:**
1. Exactly one revision at both bounds. Pure coverage test plus mutations M4 and M5. The Postgres cases are written, not run.
2. Only `productive_kwh`: `test_only_productive_kwh_can_be_declared_absent` and M3. The adapter returns `frozenset()` for any other measure.
3. A row wins: test 4 and M1.
4. A day with no other row stays NO_DATA and unsettled: test 3 and M2.
5. The excluded measure is never COMPLETE, never in `enough_data_days` and never lifts readiness: `test_excluded_measure_is_never_complete_*` and test 1 (LIMITED with one PARTIAL).
6. No zero row and no money: no write path was added; the earnings value is None (board test).
7. MG-1 is never ON_TRACK or MET: `test_mg1_with_objective_and_declared_absent_is_never_on_track_or_met`. Not mutation-proven, because no code path could produce it.
8. Byte-identical without the port method, without a candidate measure, or with an empty trigger: tests 6 and 8, `test_kobo_shaped_composition_body_equal_to_before`, and M6.

## Mutations

Each mutation was applied after commit `56256bbc9`, run, then reverted with `git checkout -- <file>`. `git status` was clean after each revert.

| # | Mutation | Failed |
|---|---|---|
| M1 | Drop "no row of m" (row wins) | rule test 4 |
| M2 | Drop "row of another measure" | rule test 3 |
| M3 | Drop the `DECLARED_SUBJECT_MEASURES` filter | `test_only_productive_kwh_*` |
| M4 | Adapter `len(cover) == 1` → `>= 1` | coverage test (ambiguous) |
| M5 | Adapter checks the start bound only | coverage test (load at the D2 end) |
| M6 | Lazy trigger asks every day with rows | rule tests 6 and 8 |
| M7 | `grade_counts_of` drops `none_declared` | rule test 7, `test_chain_day_carries_*` |
| M8 | Remove the evaluator `NONE_DECLARED` branch | board earnings test |
| M9 | Board `decl` always True | `test_no_users_without_declaration_keeps_todays_wording` |
| M10 | Gap note omitted | `test_gap_line_three_forms` |

## Checks run (L0 only, no database, `ASSETOPS_TEST_DATABASE_URL` unset; free RAM 3.57 to 3.6 GB before each batch)

- K10 files: 26 passed, 6 skipped (the Postgres adapter file).
- Batch A, 70 pure files (`test_out_*`, `test_ch*`, `test_idx*`, `test_k10*`, `test_walk*`, `test_fuel*`, `test_diesel*`, `test_coh*`, `test_mini*`): 1199 passed, 5 failed.
  - Fixed after this run: the clock guard. My first SQL used `clock_timestamp()`; it now uses the file's `CAST(:k AS timestamptz) IS NULL OR ...` form (see deviation D2). The clock guard and `test_ch6_claims` then passed (42 passed).
  - Expected: `test_out_b2_vocabulary`. This is Stop K10-v1 below.
  - Not touched by this diff (grading, `board.py`, b1 fixtures): `test_ch1a_grading::test_period_bounds_addis_utc_tue_only_and_24h` ("unknown period 'midday'"), `test_out_b1_board::test_mini_protect_battery_outcome_measured_without_warning` (extra MG-8), `test_out_b1_board::test_board_imports_only_outcomes_and_stdlib` (board imports `chain.vocabulary` names). I did not re-run them on a clean main.
- Batch B, 39 pure files (`test_demo_*`, `test_w3*`, `test_w5*`, `test_w6*`, `test_estate*`, `test_portfolio*`, `test_site_*`, `test_execution_contract_alignment`): 653 passed, 85 skipped, 1 failed.
  - The failure is `test_demo_a0_assumption_clock_seam` at `objectives/adapters/postgres_objective_store.py:61,138`, a file this diff does not touch.
  - `test_w502_domain_intent_api.py` fails at collection (`NameError: COLD`). This diff does not touch it.
- Kobo, Cold and EV golden/contract tests among those runs all passed: `test_out_b3_cold_ev`, `test_ch5a1_board_contract`, `test_ch5a2_contract`, `test_ch6_contract`, `test_out_b2_mini`, `test_ch6b_estate_chain`, `test_ch6b2_portfolio_cards`.
- Not run, per the dispatch: Postgres tests, serves, check-all, guards ps1, the full suite.

## Stops

- **CLOSED by R3t2 (§9t2, main 766bfed78): Stop K10-v1 resolved with option (a). "load" is now "equipment" in the four literals, and `test_out_b2_vocabulary` passes. D2 is confirmed by the same ruling.** Tests after the reword: vocabulary, the K10 board and rule files, `test_ch6_claims` and the clock guard gave 46 passed, 6 skipped (the Postgres adapter file, no DB). The text below is the original stop, kept as history.
- **K10-v1 (was open, for the Architect): the R3t literals fail the product vocabulary scan.**
  - `frontend/src/test/productVocabulary.json:56` lists `"load"` as an unexplained abbreviation.
  - All four R3t literals say "productive-use load", so `test_out_b2_vocabulary::test_board_and_status_copy_pass_vocabulary` fails with 4 hits.
  - I kept the literals exactly as R3t gives them (binding). I did not add an exemption or change the guard.
  - Options:
    - (a) A wording ruling, for example "load" → "equipment", as the owner question itself put it ("productive-use equipment (like a mill)"). This keeps the "0 kWh" and "not assessed" clauses.
    - (b) An exact-text allowance. That is a guard change, and needs a ruling.
  - Until ruled, this branch has one red L0 test.
- K10-s1 to K10-s4 belong to the phase-2 proof and were not evaluated.

## Known deviations

- **D1.** The branch name follows the dispatch, not §9t.3.
- **D2 (confirmed by R3t2).** R3t wrote `k = COALESCE(:known_at, clock_timestamp())`. I implemented the file's existing live form instead: `CAST(:k AS timestamptz) IS NULL OR recorded_at <= k`, and when k is null, `superseded_at IS NULL`.
  - Why: a SQL clock read in `postgres_chain_read.py` fails the CH-5c2 C3 clock guard (`test_ch5c2_clock_guard`). Allowlisting it would loosen that guard.
  - The two forms are equivalent for rows already stored (no future `recorded_at` or `superseded_at`).
- **D3.** `none_declared` defaults to `None` rather than `{}` in the signatures. The behaviour is identical.
- **D4.** `DayFacts.none_declared` is stored frozen (`read_scope.freeze`). It equals `{}` when empty.

## Residual risk and phase-2 focus

- The Postgres adapter SQL has not been executed: the `AT TIME ZONE` bound casts, the LEFT JOIN with no revision, and the jsonb content. Phase 2 must run `test_k10_declared_none_adapter_postgres.py` on an authorized `*_test` DB before the clone proof.
- Kisiwa's statement count rises by one per board/day read (only when the trigger fires). Kobo, Cold and EV make no extra call by construction (test 8).
- `code_version` makes every stored prebuilt body stale under this code. Serve only a clone (R3t §9t.4).

## Fix round (R3t3)

Ruling §9t3 of `build-sheet-DIESEL-1.md`; review `.agent/review-K10.md` (M1, L1, L2). Code commit d56a9dbfc.

- **M1.** `declared_none_day(revisions, lo, hi)` added to `chain/reader.py` (R3t3 cursor algorithm; `(valid_from, valid_to, has_productive)` tuples). `declared_none_of` in `postgres_chain_read.py` computes `[lo, hi)` per Site-local day and calls it once per day. The SQL already filtered on the whole requested span with D2's known-at form, so it is unchanged: still one statement. Pure tests: `test_r3t3_declared_none_day_eleven_cases` holds all 11 cases (plus two extra: revisions ending at `lo` or starting at `hi` are ignored). Two older assertions changed to match R3t3: duplicate no-mill revisions now give all days (overlap allowed), and a duplicate with a mill gives none. Adapter cases 6 (mid-day mill) and 7 (mid-day gap) added to `test_k10_declared_none_adapter_postgres.py`; they return `{}` for D2 through `declared_none_days` and skip until the DB phase. `test_two_overlapping_revisions_*` updated the same way. Neither adapter test has run on a DB.
- **L1.** `test_mg1_evaluator_reads_none_never_zero_on_a_declared_absent_window`: on a declared-absent window with an MG-1 objective, `_month_reading` value is None, `complete` is False, and `judge_month` is neither MET nor ON_PACE. The same through `readings()`.
- **L2.** `params = {` restored at `postgres_chain_read.py:250`.

**Mutations** (committed first, then `git checkout`; tree clean after each):

| Mutation | Result |
|---|---|
| Drop the gap check in `declared_none_day` | fails `test_r3t3_declared_none_day_eleven_cases` (case 7 returned True) |
| Drop the productive veto | fails the eleven-cases test and `test_declared_none_of_needs_exactly_one_revision_at_both_bounds` |
| `_month_reading` value 0 for a declared-absent month (L1 D) | fails the new evaluator test |
| `_month_reading` `complete` forced True (L1 E) | fails the new evaluator test |

**Tests (pure, no DB):** the three K10 files, `test_out_b2_vocabulary`, `test_ch6_claims`, `test_ch5c2_clock_guard`, `test_out_b3_cold_ev`, `test_ch5a1_board_contract`, `test_ch5a2_contract`, `test_ch6_contract`, `test_out_b2_mini`, `test_ch6b_estate_chain`, `test_ch6b2_portfolio_cards`: 234 passed, 8 skipped (the Postgres adapter file). No DB, no check-all run (rehearsal in progress).

**Phase-2 duty (R3t3):** record Kobo's `declared_none_of` result over the S-5d, S, d1 board windows and the one-, three- and four-Site Portfolio windows. Any non-empty Kobo set is stop K10-s1.

## User review

R3t needs no separate owner walkthrough for this slice: the owner already answered §9t.6. The reviewer should check the
literals against §9t.1 and resolve Stop K10-v1 with the Architect before merge.
