# PB-1c and finish (branch task/PB-1c-and-finish, worktree AssetOpsV1-pb1c)

Commits: `0df9a1f3f` (A), `46e1890eb` (C), then B ("SR finish").

## Part A: Analysed period line (done)
- `sites/AnalysedPeriodsLine.tsx` (MOCK DEVIATION header): `Analysed period: {from}–{to}`, `Analysed periods in this range: {n} · showing {x}` (the others as "· also" links), `No analysed period in this range` (periods empty, no shown period, read has no assessment: Cold `!isSelected`, EV `currentness UNKNOWN`). Shown only when the read carries `analysed_periods`.
- Links are built in the UI (PB-1a M1): the page's own path and address with `from`/`to` replaced by the period's instants (instant form of `ui/sharedRange.ts`); never `href`.
- PB-1b L2: `evSelectedWindow.shownWindow` makes `selectedWindowSearch` (tabs/links) and the Finding's session read use `shown_period`.
- Words in `ui/productWords.ts` (`analysedPeriodsLead`, `NO_ANALYSED_PERIOD`). Wired in Cold `SelectedWindowBar` and EV `WindowBar`.
- Tests: coldSiteViews 75/75 (0/1/n + link targets), evSiteMoneyRoutes 31/31 (0/1/n, link target, tabs carry shown period).
- "No event in ..." wording no longer exists in the source; the D-E5.31 literals cover it.

## Part B: SR finish (partly done)
- Done: one default. `defaultGlobalWorkWindow`, `defaultWorkWindow`, `siteSevenDayWindow` now give the last 7 full days ending yesterday (UTC / Site-local). Work preset `7dwork` "Last 7 days, including today" in `ui/sharedRange.ts`, offered by `SharedRangeBar` on Work pages only (`isWorkPage`).
- Request URLs: estate defaults (S17) unchanged, so `prebuilt_routes` (portfolio, findings, outcome-summary, site boards) are unaffected; Work pages are not pre-built. `sr2RequestUrls` 15/15.
- Tests updated: siteTime 17, coldWorkActions 43, evWorkActions 25, siteWorkCases 25, globalIncidents 31, sharedRange 23 (all pass, run one at a time).
- NOT done: "Open now" line (needs an unfiltered open-count read; global Work `state_counts` are window-filtered; no backend read exists, needs Architect/backend card). Register rows R338/S17: not located in the repo (no register file found); R338 is now "last 7 full days, Work offers 'including today'". Other Work pages' tests not all run (globalMaintenance, w1f4 etc.).

## Part C (done)
- `test_w303_selectors_postgres.py`: fake requests carry `known_at=None`; the mini fake Site gets `site_code`. 3 passed, 0 skipped, on assetops_pb1c_test (created and dropped).
- PARTIAL-MONEY: MOCK DEVIATION labels on the note and the "partial" row; no-amount wording is now `Kobo: amounts in more than one currency are not added · 6 of 7 days analysed · 4 Nov: no readings` (estateFinancials 14/14).
- `MiniRenewable` unused `pageHref` removed (and its caller prop).

## Checks
vitest files above; `tsc --noEmit` clean; check-architecture result below (see final report). No full suites, captures or layout evidence (the new lines are layout-sensitive: unmeasured).
