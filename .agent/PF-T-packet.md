# PF-T packet: Portfolio section tabs (card B1)

Branch `task/PF-T-portfolio-tabs` (wt `AssetOpsV1-pft`, from main `22d877b1d`). Build commit `ecaf8fc01`.
Spec: `.agent/architect-sequence-client-scope-2026-11-11.md` C.6 B1; proposal 2026-11-10 §6, §11; layout `frontend/mockups/v71/portfolio-tabs.html`.

## What changed
- `frontend/src/App.tsx`: one route `/portfolio/:tab?` (page stays mounted across tabs).
- `frontend/src/estate/portfolioWords.ts`: `PORTFOLIO_TABS` (owner-approved labels), `portfolioTabFrom`, `portfolioTabPath`, top-3 words.
- `frontend/src/estate/EstatePortfolio.tsx`:
  - `EstatePortfolioPage` redirects (before any read): unknown tab -> Overview; `/portfolio?lens=X` -> `/portfolio/act-first?lens=X`. Both keep the window.
  - `PortfolioTabs`: `<nav aria-label="Portfolio sections">` of `site-tabs` links with `aria-current`. Each link carries `from`/`to`/`known_at`. `lens` is on Act first only. Counts come from `total_count` (Act first), `summary.opportunity_count` and `summary.accepted_action_count`. An unknown count shows no badge.
  - Panels:
    - Overview: the four cards, the counts strip (each count links to its tab) and `TopThree` with "See all {n} findings →".
    - Act first: ranked table, lenses, load more, warnings, with the evidence prompt beside it.
    - Outcomes by site: the matrix.
    - Opportunity and What changed: their panels.
    - Scope & coverage: the existing scope drawer and the business-context footer.
  - On a tab change, focus moves to the panel's h2. The lens is read on Act first only; other tabs read `all`.
  - The date bar sits above the title (sticky).
- `estatePortfolio.css`: `.pf-tabs` (count badge; deep tab right-aligned; wraps at ≤760 px), `.pf-top3`, `.pf-pulse`, sticky `.pf-datebar`.

## Mock deviations (header comment in EstatePortfolio.tsx)
- PF-T-1: the product shell has no top bar. The date bar sits at the top of the page, sticky, not in a shell top bar. The shared top-bar picker is card SR.
- PF-T-2: the coverage line and the "Readings per site" table are PF-C. The context row keeps today's per-Site partial notes, and the Scope tab holds today's drawer.
- PF-T-3: the top-3 badge shows the placement group, not High/Medium priority (CC-R2-Q3).
- PF-T-4: the Act first count is the lens read's `total_count`.

## Tests (vitest, named files only)
- `estatePortfolio.test.tsx`: 83/83 pass, including 9 new PF-T tests:
  - nav and `aria-current`
  - tab links carry `from`/`to`/`known_at`
  - lens on Act first only
  - unknown count shows no badge
  - known counts
  - no refetch on a tab change, and focus to the panel heading
  - Overview cards, links and top 3
  - the date bar on top
  - the 760 px wrap, checked on the CSS
- `estatePortfolioRoutes.test.tsx`: 4/4 pass, including 3 new tests: one mounted route with no refetch (App level), the lens redirect, and the unknown-tab redirect.
- 30 pre-PF-T tests were re-pointed to the tab that now holds their panel: a `showTab` helper, `ACT`/`tabEntry` entries, and `panel()` opens the panel's tab.
- `expectV69Panels("portfolio")` and `expectPlantedPanelRejected("portfolio")` are replaced by per-tab `renderedPanelTitles` assertions, because v71 supersedes the v69 one-page composition.
- Non-vacuity: breaking the wrap rule and the badge rule each failed its test (2 failed). Both were reverted with `git checkout`.
- `npm run typecheck` (tsc --noEmit): clean.

## Not done / risks
- No other test files, full suite, layout evidence or captures were run, per the brief. Other tests that render `/portfolio`:
  - `evidenceTrace`, `w301EstateShellRoutes`, `sharedVisualVocabulary`, `operatorRail*` and `siteDetail`/`siteFoundation` route tests.
  - A grep found no selectors that moved to another tab, but these tests were not run.
- Layout at 390/760/1440 has not been checked. The sticky date bar and the tab wrap are verified on CSS only.
- An `act(...)` warning appears in stderr for a few older tests. It does not fail any test.
- PF-C (coverage line) is not touched.
