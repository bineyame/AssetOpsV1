# IA-P3 handoff after run 3 (P5 partial: tabs, section lines, object pages built; parity proof and alias pending; P6, P7 not built)

Branch `task/IA-P3-sites-site-inbox`, worktree `/opt/assetecon/AssetOpsV1-iap3`, from `main` `8f8b3ad16`.
Main baseline worktree `/opt/assetecon/AssetOpsV1-iap3main` (detached at `main` `4b648381c`, `npm ci` done; delete with
`git worktree remove` when the baseline is no longer needed). No server or background job is left running.

## Done

- Pre-flight: `IA-P3-preflight.md` (28 questions with defaults; Q21 blocks only P5's alias; the 6f1 meeting point).
- P4b, test-first (new tests failed first: `sitesList` failed to resolve `../portfolioSitesClient`; `siteTypeMatrix` 5 of 6
  failed; `sharedRange` 2 failed on `/sites` not being a range page):
  - `estate/portfolioSitesClient.ts` (schema `portfolio-sites-1`), `estate/sitesList.tsx` (`sitesDef`, `siteItems`,
    `SitesListPage`, `OutcomesSites`), `shell/SitesFrame.tsx` (the list; the directory table is gone; the gated create
    action stays in the header), `estate/EstatePortfolio.tsx` (Outcomes L1/L2 from E1, L3 `RangePartNote` + cards +
    `Disclosure` "Each Site's objectives"; E0 for Outcomes comes from the tab's own estate read, with no second read),
    `ui/HomeList.tsx` (`def.more`, column `note`), `ui/RangePartNote.tsx` (`rangePartWords`), `ui/sharedRange.ts`
    (`/sites` in FILLED and RANGE pages), `shell/iaRoutes.ts` (`IA-P3` landed), `App.tsx` (`portfolioSites` prop).
  - The backend test 9 writes `sites-g-2026-10.json` and `sites-g-2026-09-10.json` (World G, Thika).
  - Plants: `scopetile` (the tile shows `total.gap` under a filter) fails 2 `sitesList` tests; `browsersort` (gap compare
    on the default sort) fails 6. Both were reverted.
  - Gates: `tools/iap_gates.cjs` S1 and `/sites` as a list page: 56 of 56 pass. Shots and log are in
    `/opt/assetecon/evidence/IA-P/IA-P3/p4b/`.
  - Register R790 to R793 (MD-IAP-7, -9, -12 P4 parts; MD-IAP-13). State entry 206 (`shell.md`).
  - Guards: `check-architecture` passed (with `ASSETOPS_GUARD_PYTHON`), `check-agent-workflow` passed,
    `statement_catalogue.py` exit 0, `tsc --noEmit` clean.
  - Backend, `test_iap_portfolio_sites.py`, `_period.py` and `_waiting_counts.py`: 85 passed on the branch and 85 on main.

## Run 2 (D-IAP.35 and the test migration; done)

- D-IAP.35 Q1 and Q5 built test-first; the 41 broken tests migrated, 41 (b), plus one (a) fix (`HomeList`
  `labelledBy`). Per-file table, counts against main and gates: `packet-IA-P3.md`. Spec `Status` says P4b in_review.
- Baseline worktree `/opt/assetecon/AssetOpsV1-iap3main` is at main `3cf6f893b` (detached).

## Next (in order)

1. The coordinator's answer to `packet-IA-P3.md` §5 (lineage note, "In setup", `SitesIndex.tsx`).
2. P5 (D-IAP.38, D-IAP.39), P6 (D-IAP.37), P7 (D-IAP.40). Route tests that mount `/sites` pass `sitesE1()` and
   `estateE0()` from `frontend/src/test/sitesE1.ts`; rail tests at `/sites` use `test/rangeHrefs.ts`.

## Risks

- `.agent/mock-departure-register.md` R790+ and state index 206 may collide with 6f1 or DD rows: whoever merges second
  renumbers them.
- The Sites list on the demo build: `tools/demo_combined.py` does not prebuild `/api/portfolio/sites` (pre-flight Q11).

## Run 3 (P5, PARTIAL; stopped near the context limit)

Commits `1607351ac` (P5 build) and `bbb707964` (test migration), on `7e3c92e99`.

- Built, test-first: six tabs and `SITE_TAB_OF` (`shell/operatorSiteTabs.tsx`; frames keep old labels, mapped in the
  component); `ui/SiteSections.tsx` + `shell/siteSections.tsx` (Setup: Foundation · Changes · Assets; Evidence: Records ·
  Uploads; Performance: the four existing "Performance sections" navs gain "In Performance:" and a trailing Health, and
  the Health page shows Performance · Health); Assets lights Setup; Uploads gains the row, lights Evidence, crumb
  Sites › {Site} › Upload readings; object pages (every Finding view, fuel Finding, Actions, verifications) draw no tab
  row and use `ui/Breadcrumbs` with three parts (`siteObjectPages.test.tsx`); R383 closed, R794 (MD-IAP-8) and R795
  (candidate: lineage note and "In setup", coordinator Q1) added.
- Fail-first: `operatorSiteTabs` 56 failed of 95; `siteObjectPages` 10 of 10. Now 95/95 and 10/10.
- Migration: object pages 27 tests in 7 files (b) (subagent table: siteAction 16, miniDecisions 3, evAssessmentRoutes 3,
  domainActionVerification 2, coldWorkActions 1, w1f4ActionStructure 1, siteFuelFinding 1); tabs and lines 27 tests in
  19 files (b) plus one (a) (stale `mock-deviation.css` import in `SiteAnalyticsFrames.tsx`). Per-file rows go in the
  packet. Pre-existing on main `759759598` too (not P5): s502OverviewFindingList (flaky), siteRangeMatrix 2,
  sr2RequestUrls, domainActionVerification "32 days", evActionFixRound, evSiteMoneyRoutes outcome board 2, outcomeBoard
  (flaky), siteWorkCases "36-day".
- Baseline worktree `/opt/assetecon/AssetOpsV1-iap3main` is at main `759759598`.

## Next (P5 remainder, in order)

1. Server parity test `backend/tests/test_iap_site_findings_parity_postgres.py` (written by a subagent, UNCOMMITTED and
   unverified if still uncommitted: check `git status`; its result per vertical decides the alias). Fixtures
   `frontend/src/estate/__tests__/fixtures/iap/parity-{mini,cold,ev}-{site,estate}.json`.
2. Client layer `estate/__tests__/siteFindingsParity.test.ts` (D-IAP.39 layer 2: `loadAllPages` → `findingItems` →
   `homeListModel(findingsDef(), items, {show:"all"}, "site:{code}")` ⊇ Site ids); plant `parity` (`site:` keyed on
   `row.site_id` in `estate/homeLists.tsx` `findingsDef().site`).
3. The alias per passing vertical: a `LEGACY_ROUTES` entry `/sites/:siteId/findings` → `/findings?scope=site:{id}`
   (unit IA-P3) only if all three pass; else a type-aware redirect inside `SiteFindingsFrame` for passing verticals and
   MD-IAP-15 (index lit under Evidence, "Findings" in its section line) for failing ones.
4. Plants `seventab` (Findings back in the row: fails operatorSiteTabs and T1), `crumb` (a Finding page keeps the row:
   T2), `parity`. Gates T1 and T2 in `tools/iap_gates.cjs`; shots per spec P5.
5. Full scope runs on branch and main (estate, shell, ui vitest; backend `test_iap_*` + parity), tsc, fresh build,
   `iap_gates.cjs`, check-architecture, check-agent-workflow, `statement_catalogue.py`; packet §P5; state entry; spec Status.

## Risks (run 3)

- Cold and EV Evidence pages now carry two navs named "Evidence sections" (their own Overview | Analysis row and the
  new Records · Uploads line). Merge them into one line next run.
- Foundation pages show "Change & effect" in the Foundation sub-tabs and "Changes" in the Setup line (both by spec).
- Assets/Asset crumbs still read Sites › {Site} › Health › Battery although the page lights Setup.
- Mini Finding views whose h1 is "Finding" carry "Finding" as the crumb title.
