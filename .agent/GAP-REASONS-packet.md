# GAP-REASONS packet (D-E5.46) + currentness wording follow-up

Branch `task/GAP-REASONS` from main 44bab5d50. Card: `.agent/build-sheet-OWN-GAPS-2026-11-08.md` ~4093.

## Delivered
- `estate/coverage.py`: `_data_gap_reasons(days)` reuses `finding_index.data_gap_reason` (the one rule the Finding index uses: claim INDETERMINATE + `AMBIGUOUS_COHORT`/`GENERATOR_SERIES_AMBIGUOUS` -> READINGS_CONFLICT; `NO_COHORT`/`NO_GENERATOR_STATE` -> NOT_ENOUGH_READINGS; cohort AMBIGUOUS/EMPTY likewise). In the `day_grades` path a selected, CURRENT, no-open-work day with such a reason becomes a gap carrying it; the Site is PARTIAL; `_days_block` already emits `gaps[].reason`. Data-fact gaps withhold no Findings (as the index does).
- Precedence: NO_DATA grade (NO_READINGS) > PENDING grade/open jobs (system) > unselected day (NOT_ANALYSED) > data reason. UTC rule (no `day_grades`) unchanged.
- `postgres_assessment_store._dispatch_day_on`: selected days now carry `window_claim_level`, `window_limitations`, `cohort_status`.
- Words: reused `DAY_GAP` / backend vocabulary; nothing duplicated.
- Wording: no "checked" left on currentness/findings-list words. `productWords.ts` CURRENT "Complete readings, analysed"; PARTIAL "Some days are incomplete"; PENDING "Not analysed yet"; FAILED "The latest analysis could not be completed"; UNASSESSED/NOT_ASSESSED "This period has not been analysed"; proved-empty "Analysed: nothing to report"; next/sentence lines say "analysed". `SiteFindingIndex.tsx` (gap sentence "not analysed yet", PARTIAL_WITHHELD "incomplete days", step "Analysed, and Findings matched"), `OverviewFindingList.tsx`, `FindingConsequence.tsx` (STALE next; "latest complete readings").
- Tests updated: idxGaps, s404, s502, s5SiteWindowOverview, pb4, performanceDispatch, siteFinding, siteWorkActions, siteFinancials, productStatus.

## Tests
- New `backend/tests/test_gap_reasons.py` (12): failed 6 before the code, 12 pass after; with test_estate_coverage_local_days, test_cov_partial, test_idx_gaps_index: 66 passed.
- Vitest 11 touched files: 447 passed. `tsc --noEmit` clean.
- Postgres (assetops_gaprs_test): see coordinator line below.

## Not done / deviations
- NOT verified on client6 Kisiwa (demo DB frozen): the boundary-duplicate day reading READINGS_CONFLICT is for Saturday's rehearsal build.
- Left "Checked:" in `SiteWindowOverview` day-reading line (Kobo generator line, not a findings list), work actions ("being checked again"), CapabilityReadiness, MiniOpportunity; backend `DAYS_CHECKED`/`DAYS_WITHHELD` portfolio text ("assessed", "not available yet") untouched (PF-W area).
