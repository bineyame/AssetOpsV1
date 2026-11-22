# Review packet: IA-P1 (P0 the long range, P1 the frame, P2 the lists)

Task: `specs/IA-P-product-shape/spec.md` parts P0 to P2 (IA-P1). Branch `task/IA-P1-frame-portfolio` (the spec names
`task/IA-P1-frame-range-lists`). `USER_REVIEW_REQUIRED: true` (UI, direction); owner reviews at product shape, no piecemeal walkthrough.
Handoff with anchors and history: `specs/IA-P-product-shape/handshake-IA-P1-handoff.md`.

## Outcome
- P0: requests read the window, links keep the whole range (a 61-day range sends the last 31 days; rail and links keep the 61).
- P1: the 13-item rail in six groups (`IA_RAIL`), `iaRoutes.ts` aliases, Evidence & records with Coverage and Records tabs.
- P2: one list component for three pages. `/decisions` (new), `/findings`, `/actions` are `ui/HomeList.tsx` on `ui/homeListModel.ts`
  (cap 10, tiers, facets, sort, search, all in the address), defs in `estate/homeLists.tsx`, every page read once through
  `estate/estateReadCache.tsx` (I9 restart). Act first and the lens addresses are aliases to `/decisions` and `/findings`.

## Files (main groups)
`ui/HomeList.tsx|homeList.css|homeListModel.ts`, `ui/DataTable.tsx` (optional `tableClassName`), `estate/homeLists.tsx`,
`estate/estateReadCache.tsx`, `estate/EstatePortfolio.tsx` (ranked panel, rows, evidence aside removed), `findingIndex.tsx` and
`actionIndex.tsx` (cut to the reused words), `shell/EstateRootFrames.tsx`, `App.tsx`, `iaRoutes.ts`, `operatorSiteRoutes.ts`
(`DECISIONS_ROOT_PATH`), `OperatorShellLayout.tsx`, `ui/sharedRange.ts`, `tools/iap_gates.cjs`, `tools/checks/navigation-*.ps1`,
`tools/checks/missing-claim-scan.mjs`, fixtures under `estate/__tests__/fixtures/iap/`, register rows R782, R783.

## Acceptance (spec §6 P2)
- Tests first: `homeListModel.test` (22) and `homeLists.test` (25) pass. Tiles, tiers, one interactive element per row, a row
  without a ref shown as text, waiting = E0 `waiting_count`, address = control value, fresh mount = in-page result: covered.
- Plants shown failing then reverted (one-line edits): `cap` (3 homeListModel fail), `tile` (1), `restore` (2), `dropref` (1),
  `rowctl` (3 homeLists fail, and gate L2 fails 8 of 8 rows plus the Tab check). Rail plants: three new fixtures in
  `navigation-rail-fixtures.ps1` (Decisions to a missing route, route removed, demoted), 0 broken.
- Gates L1 L2 L3 in `iap_gates.cjs` with RAIL (Decisions live) and PAGES (`/decisions`, `/findings`, `/actions`):
  29 of 29 pass at 1440 and 390, light and dark; the 390 menu-open shot passes. Fixtures: `portfolio.json` (8 rows, so tier 1 and
  a set lens is a chip), `findings.json`, `actions.json`, mapped in `routes.json`.
- Gate R6 found a real defect: the browser's `small` made the row reason 10.8 px. Fixed (`--font-size-200`).

## Checks run (real output)
- `vitest run src/estate src/shell src/ui` at head: 3 failed, 1974 passed (99 files). The 3 are pre-existing on main (verified in a
  scratch worktree of main: 3 failed, 119 passed): `siteRangeMatrix.test.tsx` x2 ("each Site route ... matrix row": `/sites/:siteId/uploads`;
  "mini /health (R)") and `sr2RequestUrls.test.tsx` "SR-6b". Not fixed.
- `tsc --noEmit` clean. `tools/check-all.ps1` fast at head: all 42 guards passed, 167 s wall. `iap_gates.cjs` 29 of 29 pass (exit 0).
- Lean screenshots (outside the repo, scratch, deleted at hand-back): 25 pngs at 1440 and 390, light and dark, plus the 390 menu. Viewed `/decisions` at both widths: rows stack at 390 with labels. Seen: the first column cell keeps the table's white row-header fill beside transparent cells (cosmetic, P3b polish). `layout-evidence.mjs`: not run.

## Known deviations
1. Branch name (above). The 731 literal in a P0 test (2024-10-31 to 2026-10-31 is 731 days).
2. I8: the mini-grid set comes from the body's coverage (`match_state`, as the Findings page always did), not an extra `/api/sites` read.
3. The Findings opportunity table, `OpportunityList` (CH-4), the early-warning list under the table, OUT-A pills and the Finding
   row's money cell left with the old tables; opportunities stay on the Portfolio Opportunity tab. The partial-money labels
   (`consequenceFirst`) now show in the Decisions "At stake" cell.
4. The Portfolio page keeps `lens` as the constant "all" (P3b rebuilds the Overview); its card links still go to the alias paths.
5. E0 is P4a: `waiting_count` is read when present; the tile counts rows otherwise.
6. `OPERATIONAL_RECORDS_PATH` stays (the cross-language fixture).
7. `/findings` now reads findings plus portfolio (50 per page) and no scope or outcome-summary; `sr2RequestUrls` expectation changed to that.
8. MD rows R782 (MD-IAP-2, three State words, D-IAP.29) and R783 (MD-IAP-6; renumbered from R773-R774 at merge).
9. Guard changes needing review: `missing-claim-scan.mjs` gains two reviewed exemptions (`NOT_AVAILABLE_YET` in `homeLists.tsx`,
   `DETAIL_NOT_AVAILABLE` in `HomeList.tsx`); the hard-wiring baseline shrank by `--shrink` (findingIndex href 4 to 0);
   `DataTable` gained `tableClassName`.
10. The Records tab on `/evidence/records` fills the range on entry (D-IAP.19): a bare address opens on the 7-day default.

## Tests removed or moved (retired UI; none weakened)
- `estateRoots.test.tsx` deleted whole (23 tests on the old Findings and Actions tables, lens tabs, CH-4, OUT-A, OUT-C). Kept:
  refused-window sentences, real-client classification, Action title rule, now in `homeLists.test.tsx` (3 tests). Dropped with the UI:
  the "No success criterion recorded" line, five-long-rows render, 152 px column.
- `estatePortfolio.test.tsx`, removed: rendersEveryFindingColumnAndFourLensStates, rendersTypedEvidencePromptAndExactDestinations,
  "PB-3 review M1" (episode text), rendersIncompleteAndNoGapPromptWithoutSite, clearsPrivilegedRowsOn401And503, appendsOnlyFindingRowsOnLoadMore,
  coldAndEvFindingTitlesAreLiveOnlyWithAServerWindowedLink, rowWithoutLinkRefsRendersNoLink..., the six CC-R2 placement-group tests and
  CC-R2-Q1 words test, "PF-T lens travels on the Act first link only", "moving from Act first lens=cost ...", the whole PL-1 describe (6).
  Rewritten to the live shape: Overview, cards, unpriced, change disclosure, status bodies, window links, panel structure, the three
  partial-money tests (now on `consequenceFirst`), the pulse warnings test, PF-T tab names, counts and See-all (to `/decisions`).
- `fixtures/portfolioTabsOverview.before.html`: the Act first tab removed. Rail lists gained Decisions in 11 test files.
- `estatePortfolioRoutes`, `w301`, `sharedRange`, `t028Screens`, `iaRouteMap`: lens paths became aliases; `/decisions` joined the range pages.

## Residual risk and review focus
- Coverage lost with the old tables: the Finding row's evidence prompt and per-row placement reasons have no new home (P3b/P4).
- Review the two scan exemptions and `DataTable.tableClassName` (shared primitive).
- Check `/decisions?lens=cost` chip and the Tab order on a real browser; the 8-row fixture draws no tools (tier 1).

## Fix round 1 (review-IA-P1.md M1-M3, L1-L5)
- M1: `HomeList` passes the filtered `model.rows` to `def.tiles` with a `whole` flag; Decisions uses the server `waiting_count` only when `whole`. Tests: parts under a State facet on Decisions and Actions.
- M2: Findings "Its decision" column and tile read `Loading…` while the Decisions read is in flight and `Not available yet` when it is refused; never "No decision open" or 0. Two tests.
- M3: `globalWorkPageQuery` takes its window from `readSharedRange`/`capWindow`/`rangeWindow` (both forms; the second day arithmetic and `validMidnight` are gone); `known_at` is checked first so its refusal code is kept. `noRawRangeReads` now matches `getAll` too (and its sharedRange exemption path was fixed). Deviation: an instant with hours (01:00Z) is now accepted and rounded to its day, as the bar does; the old "not a UTC midnight" incidents case became "not a date". Gate: any `[data-page-refusal]` on a list page, or an `INVALID_*` refusal on any page, fails R3 (proved: the old client fails it on `/evidence/records`).
- Gate fixtures (class fix): portfolio and findings gained a cold windowed, cold no-window, EV windowed, watched (MONITOR), under-way and no-link row; actions a no-link row. Gate L2 accepts a text row only if it says "Detail not available yet" and fails if a list has no text row.
- L1 (th row fill transparent), L2 (copy "Loading Decisions…" etc.; added to `settled.ts`), L4 (crumb "Evidence & records") fixed.
- Deferred: L2 tile labels while loading; L3 (First page nonce in `useEstateRead`/cache); L5 (second exemption const needs a missing-claim-scan config change); L4 "See all 8 findings" wording (P3b rebuilds the panel).
- Checks: tsc clean; vitest on ui, estate, work and two shell files 648 passed, 1 failed (SR-6b, pre-existing on main); architecture, agent-workflow, missing-claim (44 tagged, 10 baselined), hard-wiring (12/20/69/50/3), navigation x2 pass; fresh build, `iap_gates.cjs` 29 of 29, exit 0.

## Fix round 2 (full `src/shell` run: 21 failed in 7 files on the branch, 3 in 2 on main)
One cause for 18 of the 21: the Site Overview range view's loading sentence ("Loading the site's overview for this date range.",
`RANGE_OVERVIEW_LOADING`, `sites/SiteRangeOverview.tsx`) was not in the `settledScreen` list (`test/settled.ts`). On the branch the
range read (windowed through `capWindow`, P0) is still in flight when `settledScreen` first checks, so the tests asserted against the
loading screen. Verified: the same test passes after a 300 ms wait, and the page shows 5 cards. No product behaviour changed; the
sentence is a real loading state that the helper's contract says must be listed. Class (c): test-helper gap, fixed in the helper (neither a nor b).

| Test (file) | Cause | a/b | Change |
|---|---|---|---|
| overviewDispatchAssessment x3 | range-loading sentence unlisted, asserts on loading screen | helper | `settled.ts` lists the sentence |
| s502OverviewFindingList x2 (request scope, refused read) | same | helper | same |
| s5SiteWindowOverview x2 (default day to address, SR-4b fallback) | same | helper | same |
| siteDetailScreen x1 (quick actions click) | same: markup changed when the read landed | helper | same |
| siteOverviewScreen x10 | same | helper | same |
| siteRangeMatrix x2, sr2RequestUrls SR-6b | pre-existing on main, out of scope | n/a | none |

Counts: a = 0, b = 0, helper = 18 (all 18 branch-only failures). Spec/packet behaviour changes did not touch any of these tests.
Run: `src/shell` 65 files passed, 3 failed files; 5 failed, 1598 passed (3 are main's; `s502` refused-read and `ev / (R)` failed once under
full-suite load and passed on a rerun of those two files: 2 failed = main's two matrix tests). `src/ui src/estate src/work`: 585 passed.
tsc clean; fresh build; `iap_gates.cjs` 29 of 29, exit 0; architecture (needs `ASSETOPS_GUARD_PYTHON`, the worktree has no `.venv`),
agent-workflow, missing-claim (44 tagged, 10 baselined), hard-wiring (12/20/69/50/3), navigation x2 pass.
Investigated (c): `siteOverviewScreen` "renders one card per profile domain" makes the same client calls in the same order on the branch and on main
(getSite x2, then one getRangeOverview per range, no waterfall), so the later landing is render timing only; nothing changed.
