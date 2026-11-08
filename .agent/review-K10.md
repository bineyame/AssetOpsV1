# Review: DIESEL-K10 v2 phase 1 (declared-absent productive use)

- Reviewer: fresh Claude reviewer (independent of the builder). Read-only on code; no DB, no check-all.
- Branch `task/DIESEL-K10-declared-absent`, HEAD `baf266a46`; main `766bfed78` is an ancestor (main has not moved past it).
- Diff read: `git diff main...HEAD` (7 product files, 4 test files, packet).
- Spec: build sheet §9t (R3t) and §9t2 (R3t2); owner text `.agent/owner-kisiwa-measure-applicability-2026-11-08.md`.

## Verdict: FIX (phase 1)

One Medium finding: a gap in the per-day coverage rule lets a part-day setup (including a failed builder setup read)
become "declared absent". The fix is small, pure, and conservative. Everything else holds; the remaining findings are Low.

## Findings

### M1 (Medium): only the two day bounds are checked, so a part-day setup can be declared absent

`backend/assetops_backend/chain/adapters/postgres_chain_read.py:183-201` (`declared_none_of`).

**What is wrong.**
- A day is declared absent when exactly one revision with no productive load covers the local start, and exactly one covers local end − 1 µs.
- Nothing checks what lies between those two instants.
- The SQL already returns every revision that overlaps the window, so the data needed to check it is already there.

**Failure scenarios.** I ran both against the real function, on the D2 Dar es Salaam day:
1. **Load mid-day.** Revisions: A (no load) to 08:00 local, C (mill declared) 08:00–14:00, B (no load) from 14:00.
   - `declared_none_of` returns `{D2}`.
   - The builder resolves `productive_kwh` subjects at the operating-hours period start (`postgres_chain_inputs.py:150-154`). If that start falls in A, the builder writes no row.
   - The board then reads "0 kWh · no productive-use equipment declared", and the day settles even though a mill was declared for six hours.
2. **Validity gap mid-day.** This is the case the dispatch asked about. Revisions: A (no load) to 08:00, nothing in force 08:00–14:00, B (no load) from 14:00.
   - `declared_none_of` returns `{D2}`.
   - If the builder's subject instant falls in the gap, `productive_users` raises `MiniReadUnavailable`. `productive_assets` swallows it into `[]` (`postgres_chain_inputs.py:209-214`), and no row is written.
   - So a failed Foundation read does become declared absent here. That is the R3t §9t.1 hole that v2 exists to close.
   - The owner's rule says "the component contributor being non existent doesn't mean it is checked". The dispatch says "a part-day declaration stays unsettled". Both are broken in this edge case.

**Why it is only Medium.**
- Current (non-superseded) revisions cannot overlap (the `foundation_revision_no_current_overlap` exclusion constraint).
- Both scenarios need a mid-day revision boundary in the Site's setup history. Kisiwa's demo data most likely has none.
- But no constraint forbids validity gaps or mid-day changes. The rule should hold on any data, not only on the demo's.

**Fix (pure; tightening only, so every change can only stop a day being declared absent).** In `declared_none_of`, also require:
- every revision overlapping `[local start, local end)` has `productive_loads(content) == []`;
- the overlapping revisions cover the day with no gap.

A simpler alternative: require exactly one revision overlapping the whole day. That would change the builder's own `(t0, mid, none), (mid, None, none)` expectation in `test_declared_none_of_needs_exactly_one_revision_at_both_bounds` from `{D1, D2, D3}` to `{D1, D3}`. Either way:
- add the two scenarios above as pure cases in that test;
- mirror them in the Postgres adapter file for phase 2.

**Ruling needed.** R3t §9t.3 item 3 specifies the bounds only, so this goes to the Architect as a spec tightening. It is not a builder deviation. It sits within safeguard 1's intent ("a missing or ambiguous revision means missing data").

### L1 (Low): the safeguard 7 test is not mutation-sensitive, but the safeguard holds by construction

`backend/tests/test_k10_declared_none_board.py` (`test_mg1_with_objective_and_declared_absent_is_never_on_track_or_met`).

**Mutations I tried on a scratch copy** (`chain/outcomes.py:_month_reading`):
- (D) a declared-absent month reads `value = 0` instead of None;
- (E) also forces `complete = True`.

**Result.**
- Both pass all 26 K10 tests.
- MG-1 still reads UNKNOWN ("no fully checked day counted yet this month") with target 300 and with target 0.

**Why the safeguard still holds.**
- `none_declared` is never read by `_kpi`, `_reading` or `_month_reading`. It is read only in `_earnings`.
- `judge_month` needs checked (COMPLETE) days, and a declared-absent day never contributes one.

So the safeguard is real, but this test would not catch a regression that grades a declared absence. That is the packet's own caveat, and I confirm it.

**Optional:** add a direct `OutcomeEvaluator` assertion that MG-1's reading value is None on a declared-absent window with no rows. Non-blocking.

### L2 (Low, nit): stray whitespace on an untouched line

`backend/assetops_backend/chain/adapters/postgres_chain_read.py:250`: `params ={` (was `params = {`). This is unrelated churn inside `finding_heads`. Revert it.

## Checks against the dispatch

1. **Owner rule.**
   - **Never graded, completed, counted, priced or summed.**
     - `applicable_measures` (`chain/reader.py`) removes the measure before the per-day grades are built. So it cannot be COMPLETE, cannot enter `enough_data_days`, and cannot lift readiness.
     - `_earnings` returns `money_claim(..., None, None, "NONE_DECLARED")`, so the value is None and it is never summed.
     - No write path was added.
   - **Missing data stays a gap.**
     - Declared absent needs no `productive_kwh` row AND a row of another measure AND the port's proof. Rule tests 2–5 cover this.
     - Port errors propagate; `declared_none_days` has no try/except, so the board reads PARTIAL.
     - If the port lacks the method, nothing is declared.
     - A "more than one revision" bound is rejected (the coverage test; mutation A, see below).
     - A "load declared but no data" day is rejected (no day is returned).
     - Part-day: see M1.
   - **Builder path (`postgres_chain_inputs.py:209-214`).**
     - The swallowed `RuntimeError` only means "no `productive_kwh` row". It is never an input to K10.
     - K10 asks an independent setup read at board time. That read must find exactly one no-load revision at each bound, and its errors propagate.
     - So a failed builder read becomes declared absent only when the setup is readable and none-declaring at both bounds but unreadable at the builder's instant. That is M1 scenario 2.
     - A transient DB failure in the builder, where the setup actually declares a load, gives no declared day. The adapter sees the load, and the day stays a gap.
2. **One shared rule.**
   - `chain/read.py` imports `applicable_measures` and `DECLARED_SUBJECT_MEASURES` from `chain/reader.py`.
   - `_counts`, `counts` and `grade_counts_of` pass the same `none_declared`.
   - `DayFacts` carries it, so `claims.py` estate counts and the board agree.
   - Rule test 7 asserts `grade_counts_of == counts(..., nd)`.
   - Other `day_grade` callers without the keyword:
     - `why.py:138` (`day_grades`/`days_line`) has no caller.
     - `why.py:208` builds a `measure_day` node only when the measure has subject rows, so a declared-absent `productive_kwh` gets no node.
     - `site_chain.days_of` has no caller.
   - Neither diverges in practice.
3. **Adapter SQL** (`_DECLARED_NONE`), read against `migrations/versions/0001_foundation_identity.py`.
   - **Columns.**
     - `site.timezone` is `text NOT NULL`. `site.(tenant_id, id)` is the FK target.
     - `foundation_revision` has `tenant_id`, `site_id`, `valid_from`, `valid_to`, `recorded_at`, `superseded_at` and `content jsonb`, all present with the expected types.
   - **LEFT JOIN.** The revision predicates sit in `ON`, so a Site with no revision still returns one row (timezone, NULLs). Python drops a `valid_from` of None and returns nothing. A Site that does not exist returns no rows and an empty set.
   - **Site timezone.** `CAST(:lo|:hi AS timestamp) AT TIME ZONE s.timezone` turns a naive local midnight into the correct timestamptz. Python recomputes both bounds with `ZoneInfo(tz)` from the same column. Half-open overlap is correct.
   - **D2 form.**
     - k given: `recorded_at <= k AND (superseded_at IS NULL OR superseded_at > k)`. This is identical to `MiniDepthRead.productive_users`.
     - k null: `superseded_at IS NULL`. This differs from the live clock form only for future-dated rows. It is conservative, and R3t2 confirmed it.
   - **Exactly one revision at each bound.** Local start and local end − 1 µs are each checked with `valid_from <= at < valid_to` and `len(cover) == 1`. Correct, subject to M1.
   - **Statements.** One statement per call; params bind like the file's other statements.
   - **Not executed.** This is my reading, not a run. Phase 2 must run it.
4. **Wording.**
   - The four literals match R3t2 byte for byte: `SALES_NONE_DECLARED`, `GROW_NONE_HEADLINE`, `GAPS_NONE_DECLARED`, and `money.none_declared`.
   - The gap-line forms match §9t.3:
     - with gaps: the gap text, then `" · " + GAPS_NONE_DECLARED`;
     - no gaps with a note: the note alone, with `days: []`;
     - neither: None.
   - The headline falls back only when there is no spare-solar headline, and carries no money.
   - The node window is `(day, day)`, so `.get(day)` equals R3t's "all window days".
5. **Kobo, Cold and EV.**
   - **By construction.**
     - Cold and EV have no candidate measure, so the result is `{}` before any port call.
     - Kobo's days with a `productive_kwh` row are never asked about, and a row always wins.
     - With `nd == {}`, every rule function is the identity, and `DayFacts`/`NodeInputs` gain only defaulted fields.
   - **Goldens and contracts passed:** `test_out_b3_cold_ev`, `test_ch5a1_board_contract`, `test_ch5a2_contract`, `test_ch6_contract`, `test_out_b2_mini`, `test_ch6b_estate_chain`, `test_ch6b2_portfolio_cards`.
6. **Mutations.** I re-ran four of the packet's mutations plus three new ones, on a `git archive HEAD` scratch copy. No repo file was edited. Each was run against the two pure K10 files.

   | Mutation | Result |
   |---|---|
   | A: adapter `len(cover) == 1` → `>= 1` (packet M4) | fails the coverage test |
   | B: `ChainRequest.day` drops `none_declared` from `day_settled` (new) | fails `test_chain_day_carries_*` |
   | C: drop "no row of m" (row wins; packet M1) | fails `test_4_*` |
   | F: gap note dropped when there are gaps (packet M10 variant) | fails `test_gap_line_three_forms` |
   | D, E: safeguard 7 (new) | survive; see L1 |
7. **Pre-existing failures.** I ran them on `git archive main` and `git archive HEAD` copies, with `config/` included. The failure sets are identical, so K10 does not cause them:
   - `test_ch1a_grading::test_period_bounds_addis_utc_tue_only_and_24h` (`ValueError: unknown period 'midday'`);
   - `test_out_b1_board::test_mini_protect_battery_outcome_measured_without_warning` (extra `('MG-8','NO_OBJECTIVE')`);
   - `test_out_b1_board::test_board_imports_only_outcomes_and_stdlib`;
   - `test_demo_a0_assumption_clock_seam::test_no_product_module_passes_the_recorded_clock_override`;
   - `test_w502_domain_intent_api.py` collection: `NameError: name 'COLD' is not defined` on main as well.

## Checks run (pure only)

Interpreter `AssetOpsV1-plan2\.venv`, worktree PYTHONPATH, `ASSETOPS_TEST_DATABASE_URL` unset:
- **K10 and adjacent tests.** The three K10 files, `test_out_b2_vocabulary`, `test_ch6_claims`, `test_ch5c2_clock_guard` and the seven Kobo/Cold/EV contract and golden files above: **232 passed, 6 skipped** (the Postgres adapter file, no DB).
- **Mutations and the main-vs-HEAD comparison:** see items 6 and 7.
- **Not run:**
  - Postgres tests (the adapter SQL is unexecuted);
  - check-all, guards and the full suite;
  - the frontend.

## Residual risk (phase 2)

- **Unexecuted SQL.** The adapter SQL has never run. Check binding of the naive `:lo`/`:hi` and of a None `:k` under the project driver. Run `test_k10_declared_none_adapter_postgres.py` on a `*_test` DB first.
- **Kobo statement count.** The lazy trigger fires on any Kobo day that holds other measures' rows but no `productive_kwh` row, for example a stage built before the productive stage. The output stays unchanged (the adapter finds the mill), but the statement count rises by one.
  - Check this against any statement-budget guard during the K10-s1 comparison.
  - If Kobo's Foundation history has an earlier no-mill revision covering a day with rows, that day becomes declared absent and Kobo's body changes. Treat that as K10-s1, not as a pass.
- **Stale prebuilt bodies.** `code_version` makes every stored prebuilt body stale, so serve only a clone (R3t §9t.4). This was already named.
