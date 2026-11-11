# PARTIAL-MONEY review packet

Task: build sheet `.agent/build-sheet-OWN-GAPS-2026-11-08.md` "Card PARTIAL-MONEY" (D-E5.45, owner "option 2 for
money"), label per D-E5.46. Branch `task/PARTIAL-MONEY` from main 626e3b94e. USER_REVIEW: owner walkthrough only
(story-visible money wording), per the W1/W6 walkthrough rules.

## Outcome
A PARTIAL mini-grid Site's money is the lines of its analysed Site-local days only. A Finding/line whose episode
overlaps any gap day (any reason: NO_READINGS, READINGS_CONFLICT, NOT_ENOUGH_READINGS, NOT_ANALYSED) is never a
money line and shows no current amount. Nothing is estimated, scaled or filled. Label:
`{amount} for {n} of {m} days analysed · {day list}: {short reason}` (more than 3 gaps: `{g} days without a usable
result`). PENDING / STALE / UNKNOWN / HISTORICAL keep today's withholding. No estate or cross-currency total.

## Files
- `backend/assetops_backend/estate/coverage.py`: `on_gap_day` (strict overlap with the gap day's Site-local bounds);
  PARTIAL rows carry `_on_gap_day`; `_mini_grid_money` withholds only those (was: every PARTIAL head, C6).
- `backend/assetops_backend/estate/financials.py`: `money_covered` (PARTIAL with >=1 analysed day is covered);
  `mini_grid_lines` skips `_on_gap_day` rows; `partial_money` (exact Decimal sum of the Site's ELIGIBLE lines, states
  SUMMED / CURRENCY_MIXED / OVERLAPPING / NO_ELIGIBLE_LINES, with `analysed_days`/`requested_days`/`gaps` copied from
  the Site's `days` block); `coverage_site_money` adds `money` to a PARTIAL Site's `coverage.sites[]` entry.
- `backend/assetops_backend/estate/portfolio.py`: Portfolio `coverage.sites[]` carries the same `money` block.
- `frontend/src/estate/portfolioWords.ts`: `analysedDaysMoney`, `partialMoneyText`, `PARTIAL_MONEY_NOT_ADDED`; gap words
  come from the one `DAY_GAP` table via the existing `gapReasonClause` (no new word table).
- `frontend/src/estate/EstatePortfolio.tsx`: `consequenceFirst` shows a PARTIAL Site's priced row as
  `analysedDaysMoney(amount, site.days)`; gap-day rows keep `partialConsequence`.
- `frontend/src/estate/EstateFinancials.tsx`: `PartialMoneyNotes`, one line per PARTIAL Site under the register.
- `frontend/src/estate/estateClient.ts`: `EstatePartialMoney`, `EstateCoverageSite.money?`.
- Tests: new `backend/tests/test_partial_money.py`; updated `test_cov_partial.py` T8 and
  `test_cov_partial_portfolio.py` X1 (both asserted the reversed C6 withholding); frontend
  `estatePortfolio.test.tsx` (+4), `estateFinancials.test.tsx` (+3).

## Pinned tests (each failed before the code: 8/8 backend failed on the pre-change run; frontend asserts text the
old code never produced)
1. `test_1_one_no_readings_day_amount_is_exactly_the_other_six_days_lines`: amount == exact sum of the 6 analysed
   lines; 6 of 7; gap NO_READINGS. Label: frontend `partialSiteShowsTheAnalysedDaysAmountWithItsLabel NO_READINGS`
   -> `$3.31–$3.97 for 6 of 7 days analysed · 4 Nov: no readings`.
2. `test_2_a_gap_days_own_line_is_never_included` (+ `test_2b_...` for conflict / not-enough: row shown UNKNOWN, no
   line; a head spanning into the gap day is excluded too).
3. `test_3_category_covered_only_for_partial_with_an_analysed_day`.
4. `test_4_a_pending_site_is_still_withheld`.
5. Frontend `estatePortfolio.test.tsx` (3 reasons + >3 gaps) and `estateFinancials.test.tsx` (3).
6. `test_6_no_total_across_currencies` (CURRENCY_MIXED, amount null) + frontend `neverAddsAcrossCurrencies`.
- Consistency: `test_a_data_gap_day_is_out_of_the_money_and_the_analysed_count_alike[READINGS_CONFLICT|NOT_ENOUGH]`
  (every day COMPLETE-graded by the chain; the conflict day is out of the lines, `analysed_days == days.checked == 6`,
  `money.gaps == days.gaps`); frontend asserts the money label's gap clause equals the coverage line's.

## Checks run (revision abe3d4bdd unless noted)
See "Check results" below.

## Known deviations
- Card file list names `evidence_money.py`; it holds no money for mini-grid (evidence rows only), so it is unchanged.
  The Portfolio "cards" in the UI are the outcome-summary chain cards (`site_outcomes/read.py`), whose money already
  reads checked-day claims ("At least"); unchanged. The estate `value_cards` follow `applicable` (now covered for
  PARTIAL) but are not rendered.
- The money block rides `coverage.sites[].money` (key present only for a PARTIAL mini-grid Site) rather than
  `summary`, so existing exact-equality summary tests and goldens are untouched.
- Label composed in the browser from codes (`portfolioWords.ts`, as `gapReasonClause` already is); no backend text.

## Residual risk
- The chain coverage line counts readings arrival: a conflict day still reads "complete readings on 7 of 7 days"
  in the server clause, followed by the estate gap clause "4 Nov: conflicting readings" (pre-existing GAP-REASONS
  behaviour, review note). Money and the "n of m analysed" count use the estate `days` block, the same set as that
  gap clause; the chain's "complete readings" count is a different fact and is not changed here.
- A head within the continuity tolerance of a NOT_ANALYSED or NO_READINGS day is withheld from rows by the existing
  D-E5.42 rule (`touched`), so it is also out of the sum: the amount can be below the analysed days' full total,
  never above it.
- Overlapping lines across partitions: summed only when no two eligible lines share an overlap group; same-partition
  overlaps are already demoted to CONFLICT by `compare`.

## User-review focus
The row wording "$3.31–$3.97 for 6 of 7 days analysed · 4 Nov: no readings" on a single Finding row (per card
literal) and the Financials Site line.
