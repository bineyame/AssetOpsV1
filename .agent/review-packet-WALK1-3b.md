# Review packet: WALK1-3b (Grow row: performance, KPI progress and potential apart; configurable minimum; 0041)

Task: build sheet `.agent/build-sheet-WALK1.md` (plan2) Addendum 2 §A2.1-§A2.5, and the two tests that fail on
main (`.agent/demo-sprint-lows-2026-10-31-pipeline.md`). Branch `task/WALK1-3b-target-progress` from main
`362dc4fe6`. Head `88cccaac5` (four commits). USER_REVIEW_REQUIRED: no walkthrough for this slice by itself. It
merges on review ACCEPT before G1, and the owner sees it at the G1 walkthrough.

## Outcome delivered

- **(a) Performance** stays the headline (`headline_money`, WALK1-3) and the "Productive-use sales" line. It never sets the state.
- **(b) KPI progress** now sets the state of a row that has a declared objective. MG-1 is judged month to date by
  `judge_month` (`outcomes/objectives.py`) over the Site-local calendar month through the board day
  (`site_outcomes/mini.py` `_productive_month`, `mg1_reading`). Mapping: Met / On pace → On track, Behind pace →
  Watch, Missed → Needs attention, Too early → Unknown (`OBJECTIVE_TOO_EARLY`).
- **(c) Potential**: in `outcome_state` (`outcomes/status.py`) an open opportunity now ranks below the objective
  verdicts. The row wire gains `potential: {label: "Opportunity", text}` when an opportunity is open and the state is
  not Opportunity. `OutcomeBoard.tsx` shows it as a second green chip after the state chip.
- Grow contributor order: Productive-use sales, Declared objective, Productive use (spare solar), Price per kWh, Cash
  collected, Site earnings. The board inserts the objective lines after the domain's `SiteFacts.objective_after`
  key (mini Grow: `productive_sales`). Every other row is unchanged.
- **Configurable minimum** (§A2.5):
  - migration `0041_walk1_objective_min_days`: nullable `min_checked_days`, CHECKs `..._min_checked_days_range`
    (1-28) and `..._min_checked_days_monthly` (productive_use_kwh only); the downgrade refuses while a value exists;
  - `Declaration.min_checked_days`: refused with 422 `OBJECTIVE_INVALID` when it is not an int (bool, 2.5, "3"),
    is outside 1-28, or is given for a non-monthly measure;
  - it is hashed only when present, the store inserts it, and the CLI takes `--min-checked-days` (the fixture
    passes its JSON value through);
  - `ObjectiveFact.min_checked_days` resolves NULL to `DEFAULT_MIN_CHECKED_DAYS = 3`, and `Measure.monthly` is set
    for productive_use_kwh only.
- **Main-failing tests fixed:**
  - the backend MERGED title now reads "Generator support review: joined into an earlier finding", matching
    `findingWords.ts`; the test is unchanged;
  - `test_out_b2_mini` now expects WALK1-1's `withheld: False` in `finding_gaps`.
- **Also fixed:**
  - the `test_out_d5_objectives_postgres` spy now passes the composer's extra `mini_readings` arguments. WALK1-3
    had already broken its two-argument signature.
  - `tools/demo_combined_finish.py` gains G1 row **WK-4** (§A2.4 finish check): Kobo S Grow is not Unknown, and
    its objective line contains "so far this month".

## Kobo on day S (10-29): actual, not tuned

A read-only probe against `assetops_polish_full_test` used SELECT only (`SET SESSION CHARACTERISTICS AS TRANSACTION
READ ONLY`) plus the reader's own read-only transactions. Polish is at `0039_merge_objectives_cc`, so it predates
WALK1-3: no Foundation declares a productive user there, and the probe used the `load-mill` asset in its place. The
Site zone is Africa/Addis_Ababa.

- `mtd` = **673.3333 kWh** (shown as "673.3"), **c = 6 checked days of e = 29**, m = 31. The checked days include
  10-16 and 10-23 at 0 kWh, measured.
- Verdict **MET**, so the Grow state is **On track**, provided no Finding, warning or limited-evidence rule outranks
  it on that day.
- Line: "Productive electricity sales: at least 300 kWh sold for productive use a month · 673.3 kWh so far this
  month, on 6 of 29 days checked", with chip "Met".
- The sheet expected 673.2 (4 × 168.3). The actual is 4 × 168.333… = 673.3. Nothing was tuned.
- No Opportunity chip on S: Kobo has no spare-solar read until WALK1-4/5.
- The full board on a 0041 database is checked at G1 (WK-4).

## Acceptance criteria

| Item | Status |
|---|---|
| A2.1 opportunity below objective steps; no-objective order unchanged; MISSED and Findings above | Done; `test_opportunity_no_longer_outranks_a_declared_objective`, updated `test_out_d2` rule-7 tests |
| A2.1 `potential` wire field and second chip (R690) | Done; compose tests and vitest `rendersTheOpportunityAsASecondChipAfterTheStateChip` / `rendersOneChipWhenNoPotentialOrOnAnOlderBody` |
| A2.2 `judge_month` rules 1-5, rates compared exactly (`value*m >= target*c`), no projection | Done; truth table with c = 2/3 and avg = need boundaries |
| A2.2 verdict chips On pace / Behind pace / Too early to judge; actual texts | Done; compose tests pin Met, Behind pace, On pace, Too early, Missed texts |
| A2.2 conflicting day not checked (Addendum 3 M1) | Done; `test_conflicting_day_is_not_checked` |
| A2.3 headline unchanged; contributor order | Done; `test_kobo_month_to_date_met_is_on_track_without_an_opportunity_chip` |
| A2.4 EV Grow unchanged; Portfolio dots follow row state | EV pinned (`test_ev_grow_rows_are_unchanged`); Portfolio has no code change (reads row state) |
| A2.5 migration up/down/refusal and both CHECKs | Done; `test_walk1_objective_min_days_postgres.py` (3 tests) |
| A2.5 validation 0/29/2.5/"3" (and True) refused, non-monthly refused, 1/28/absent accepted, NULL stored | Done (pure and Postgres) |
| A2.5 existing hash unchanged when absent | Done; `test_existing_declaration_keeps_its_hash` pins the pre-3b body |
| A2.5 minimum 1 and 5, default NULL → 3, TOO_EARLY text with `{k}` | Done |
| Vocabulary scan | Done; new strings in `mini.COPY`, scanned in pytest and vitest (`w1` set) |
| Head literals 0041 | Done; 22 test modules plus `mini_depth_probe.py`; the 0040 test now separates `HEAD` (0041) from `THIS` (0040) |
| Register R690-R693, R678 resolved | Done (`.agent/mock-departure-register.md`) |

## Checks run (head `88cccaac5`, foreground, each run under 600 s)

- Scoped backend unit group: every non-Postgres `test_out_*`, `test_idx_gaps_*`, `test_link_lineage`, `test_walk1_*`
  module, including the new `test_walk1_3b_target_progress.py` (22 tests). Result: **431 passed**.
- Postgres on `assetops_walk1d_test`, all passed:
  - `test_walk1_objective_min_days_postgres`, `test_out_d1_schema_postgres` and `test_walk1_productive_price_postgres`: 28 passed;
  - `test_out_d3_objective_store_postgres`, `test_out_d3_declare`, `test_cc_schema_postgres`, `test_w204_cold_migration` and `test_w205a_ev_migration`: 35 passed;
  - `test_out_d5_objectives_postgres` and `test_walk1_productive_producer_postgres`: 5 passed, 151 s.
- `tools/check-all.ps1`: **All 12 guards passed**. That includes architecture seams, agent workflow, mock deviation
  labels and client vocabulary, and the screen ledger.
- Frontend: `tsc --noEmit` clean. `vitest run src/sites src/estate`: **67 files, 1955 tests passed**.
- Not run:
  - the full backend suite; the coordinator runs it after merge. Because of the migration this slice is on the full
    tier, and the other 16 head-literal Postgres modules changed only their literal;
  - the full frontend suite and the production build;
  - layout evidence: one extra chip in a wrapping `ob-sum` flex row, judged not layout-sensitive. Layout evidence:
    not run.

## Known deviations

- The `outcome-status/2` policy version was not bumped, although the precedence changed. The sheet does not ask for
  it. Architect call.
- The mini Assure "Actual against plan" count ("{met} of {n} declared objectives met · {u} not checked yet") still
  counts On pace, Behind pace and Too early as "not checked yet". The sheet does not say otherwise. Kobo on S is Met,
  so this is not visible on the walkthrough path.
- The potential's issue text is carried as the chip's `title` (tooltip). The chip itself reads "Opportunity", as
  §A2.1 says.
- The board day's money uses the UTC day (WALK1-3, unchanged). The month window uses Site-local days, as §A2.2
  says. For a UTC+3 Site the last checked day can differ by those three hours from the day figure.

## Residual risk

- The month read fetches the whole month of `feeder_demand` rows for the Site and filters them by asset in Python,
  using the WALK1-3 reader query. The cost is about 30 times one day per board read. It is fine for the demo data;
  watch it at G1.
- Polish predates WALK1-3, so the S figure above comes from the mill asset. It is not the full board read.

## User-review focus

- Kobo Grow on S reads "On track", with "673.3 kWh so far this month, on 6 of 29 days checked" and the chip "Met".
- On S+1, once WALK1-5 adds spare solar, the second "Opportunity" chip appears beside the state.
