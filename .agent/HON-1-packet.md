# HON-1 packet: complete-readings honesty

Branch `task/HON-1-complete-readings` from main 8a4b4fe4d. Card: `.agent/architect-sequence-client-scope-2026-11-11.md`
lines 29-34. Build commit 7e99b8e48.

## Delivered
- **One rule**: `chain/claims.py` `without_data_gap_days(counts, grades, gaps)`. If a mini-grid day has a D-E5.46
  data-gap reason (READINGS_CONFLICT / NOT_ENOUGH_READINGS) and the chain graded it COMPLETE, it is taken out of
  `complete` and does not join any other bucket. A gap day already graded below COMPLETE is not taken out twice.
- **Source of the gap days**: the injected `claims.data_gap_provider` (wired in `main.py`) points to the new
  `EstateEvidenceService.site_data_gap_days_many`. That reads `snap.dispatch_days` and applies
  `coverage.data_gap_days` (renamed from `_data_gap_reasons`, unchanged), so these are the same days the estate gap
  clause names. It is read once per request and memoised as `chain.data_gaps`. It only covers mini-grid Sites. If it
  fails, the failure is noted and the counts fall back to readings arrival.
- **`estate_count_claims`** applies the rule, so all four callers (outcome summary, `/estate/chain`, the estate
  Portfolio, the estate Findings index) see the same days:
  - the coverage line reads "complete readings on 5 of 7 days";
  - the Site is `complete: False` and the lead reads incomplete;
  - the count-claim basis is CHECKED_DAYS;
  - `days_text` matches the line.
- **"Why?" days** (`_own_days`): `EstateCounts.arrived` keeps the arrival counts before a day is taken out. A card
  whose claim days equal those arrival days counts as the line's day set, so it never shows "7 of 7" next to the
  line's "6 of 7".
- **Site Overview day line**: `site_overview/read.py` adds `freshness.data_gap_reason`, computed by
  `finding_index.data_gap_reason(detail)` (the Finding index's rule). On a gap day, `SiteWindowOverview`
  `DayStateLine` shows the `DAY_GAP` label from the one word table (`productWords.ts`) in place of "Latest complete
  readings". No new words were added.

## Tests (each new test failed before the code)
- New `backend/tests/test_hon1_complete_readings.py`, 13 tests:
  - the rule, for each reason;
  - a gap day not taken twice;
  - the coverage line, lead and `days_text` for each reason ("5 of 7");
  - the count claims for each reason;
  - mini-grid only;
  - an all-good week: the line and cards equal the baseline;
  - a provider failure changes nothing;
  - Site Overview `data_gap_reason` for each reason, and None on an analysed day.
  - Before the code: 13 failed. After: 13 passed.
- Frontend `s5SiteWindowOverview.test.tsx` gets 3 tests (one per reason, plus an analysed day). With the component
  change stashed, the 2 reason tests failed; with it, they pass.
- Non-Postgres files, run one at a time with no DB URL, all with 0 skipped:
  - `test_hon1_complete_readings` 13
  - `test_pfc_coverage_line` 123
  - `test_ch6b_estate_chain` 20
  - `test_s5_overview_read` 39
  - `test_gap_reasons` 12
  - `test_partial_money` 10
  - `test_estate_coverage_local_days` 12
  - `test_cov_partial` 20
  - `test_ch5b_why` 49
  - `test_ch5a2_contract` 26
  - `test_ch5a2b_claims` 31
  - `test_ch6b2_portfolio_cards` 55
  - `test_k8_estate_fuel` 21
  - `test_mb1_opportunity_board` 28
  - `test_out_w2_summary_window` 9
  - `test_qw2_reuse` 4
  - `test_idx_gaps_index` 22
- vitest on `s5SiteWindowOverview` and `s502OverviewFindingList`: 104 passed. `tsc --noEmit`: clean.
- Architecture check (`tools/check-architecture.ps1`, ASSETOPS_GUARD_PYTHON set to the plan2 venv), run on
  7e99b8e48: "Architecture check passed."

## Golden changes
None. No fixture has a data-gap day, so `estate_week_2026-10-25.json` and every exact-equality test are unchanged.

## Not run: Postgres (coordinator D-ANY.6, DB reserved). Run these when the DB is free
Use `ASSETOPS_TEST_DATABASE_URL=...assetops_hon1_test`, one file at a time, and check that connections are under 150:
- `test_cov_partial_portfolio`
- `test_w303_portfolio_api`
- `test_w303_portfolio_scope_snapshot_postgres`
- `test_w302_money_api`
- `test_qw2_many_postgres`
- `test_out_c3_repeat_visits_postgres`
- `test_mb1_site_actions_postgres`
- `test_w303_selectors_postgres` (2 failures already exist on main, see the PARTIAL-MONEY packet)
- `test_s4_finding_index_postgres`

These exercise `site_data_gap_days_many` on a real estate snapshot, and the extra snapshot read in the summary
(statement-count or ledger budgets).

## Known deviations / residual risk
- The demotion uses the Site day grade. If a conflict day is graded PARTIAL for the Site but COMPLETE for the
  measure a claim reads, that claim still counts it. The coverage line and cards are not affected.
- The Site board's own node `days_line` (OutcomeBoard parts, from evaluator rows) is not demoted. For a mini Site it
  is a one-day board, and the Site Overview day line now names the gap. A card's own days line is still read from
  claim days when its day set differs from the line's (for example a separate study).
- The estate Portfolio and Index call `count_claims` inside their own estate snapshot. The provider then opens a
  second, nested estate snapshot (a second pooled connection). It reads consistently, but it is not the same
  snapshot.
- The outcome summary now makes one extra estate snapshot read per request when there is a mini-grid Site.
- Not checked on live client data (Kisiwa boundary-duplicate day): that is for the rehearsal.
