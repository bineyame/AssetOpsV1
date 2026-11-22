# IA-P3 handoff after run 1 (pre-flight and P4b code; PARTIAL: the existing-test migration is not done)

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

## Next (in order)

1. **Migrate the existing tests that P4b broke.** vitest `src/estate src/shell src/ui` at `01aaf02cd`: 2021 tests, 47
   failed in 18 files (log: scratch `vitest-branch.log`; re-run to list them). Compare with main's run of the same set,
   (main `4b648381c`, same set: 2000 tests, 5 failed: `s502` 2, `siteRangeMatrix` 2, `sr2` SR-6b 1; 69 s; the branch took
   202 s), so 43 of the branch's failures are new. Migrate per file with IA-P2's (a)/(b) rule (`packet-IA-P2.md` §2). The causes seen so far:
   - `sitesIndexRoute` (18), `operatorRouteFrames` (3), `simulatorLabGate` (4), `simulatorLabWorkspaceEntryPoint`,
     `siteDetailRoute`, `siteTemplateCatalog`, `siteTemplateLineage`, `overflowContainment` (3), `siteRangeCarry` (2),
     `operatorSiteTabs` "does not render on the Sites index": these pin the old directory table ("Site inventory", "In
     setup", lifecycle, the template-lineage note, the Sites crumb and its empty sentences). This is (b), §6 P4b.
     Re-point each to the list (rows, `Detail`, the gate's create action). The template-lineage note and "In setup" have no
     place in the list: record them as known deviations, or ask.
   - `operatorRailInventory`, `w301EstateShellRoutes`, `w302EstateEvidenceShellRoute`, `sharedVisualVocabulary` (3):
     the rail's Sites link now carries the range, because `/sites` fills its range on entry. This is (b), spec §6 "Range
     pages".
   - `estatePortfolio` (2): "Outcomes across the estate" is now inside the closed `Disclosure` (b, §6 P4b). Open it, or
     query hidden.
   - `sr2RequestUrls` (1: an extra `/api/sites/KOBO-001/…` request) and `siteRangeMatrix` (2): check them against main.
     IA-P2's packet lists `siteRangeMatrix` (2) and `sr2` SR-6b as failing on main too. `s502OverviewFindingList` is a
     known load flake.
2. Write the packet `packet-IA-P3.md` (P4b section; §5 counts branch against main), and set spec `Status` for IA-P3 P4b.
3. Then P5 (Q21 needs the Architect first), P6 and P7.

## Risks

- `.agent/mock-departure-register.md` R790+ and state index 206 may collide with 6f1 or DD rows: whoever merges second
  renumbers them.
- The Sites list on the demo build: `tools/demo_combined.py` does not prebuild `/api/portfolio/sites` (pre-flight Q11).
