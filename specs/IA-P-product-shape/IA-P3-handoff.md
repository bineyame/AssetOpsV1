# IA-P3 handoff after run 2 (P4b with D-IAP.35 and its test migration done; P5 to P7 not built)

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
