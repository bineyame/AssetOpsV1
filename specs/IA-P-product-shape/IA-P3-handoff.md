# IA-P3 handoff after run 4 (P5 built to D-IAP.42-45 except the alias test migration and slice-end paperwork; P6, P7 not built)

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

1. Server parity test `backend/tests/test_iap_site_findings_parity_postgres.py` (committed; only its fail-first run
   happened, 4126 s wall, 74.5 s of tests, the rest a DB-slot wait). Results: MINI (Kobo `guardrail`, KOBO-001) FAILS
   the subset, SPEC_AMBIGUITY: the Site read is PARTIAL with 2 ids (month) and 3 (61-day), the estate is UNKNOWN with 0
   rows and `total_count` null (`estate/coverage.py` ~252 withholds heads touching an unchecked day on a PARTIAL mini
   Site; `estate/index.py` ~451 nulls the count unless COMPLETE). COLD (fx_cold_linked, COLD-LAB-001) passes parity, 2
   of 2 ids, both windows; EV (w504 positive, EV-LAB-001) passes, 1 of 1. No fuel Finding, no extra estate ids. Both
   then fail only on the missing fixtures. Fixtures cannot be byte-current as D-IAP.39 asks: Finding ids are `uuid4`
   (`analytics/finding_episode.py:669`) and the COLD world moves with the wall clock. Two Architect questions follow.
   No `known_at` is sent (the Site tab link carries none; a DB-now one is refused by EV with 422 `EV_TIME_INVALID`).
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

## Questions for the Architect (run 3)

- Q-P5-1 (SPEC_AMBIGUITY, MINI): the estate withholds a PARTIAL mini Site's Findings that the Site index shows. Is MINI
  MD-IAP-15 (index kept, lit under Evidence) and the alias COLD and EV only, or is the estate rule to change?
- Q-P5-2: the pinned bodies cannot be byte-current (uuid4 ids, clock-relative COLD world). Pin a normalised body (ids
  and dates replaced by stable tokens, the subset relation kept), or pin once and assert shape and the subset only?
- Coordinator Q1 and Q2 (packet §5) are still open; R795 is the candidate row; `sites/SitesIndex.tsx` kept.

## Run 4 (P5 on D-IAP.42 to D-IAP.45; PARTIAL, stopped at the context limit)

Merged main `12e618be3` (conflicts in spec Status and state index resolved: DD3a keeps 206, IA-P3 is 207). Commits
`2edb16d4b`..`188c5fee8`. Baseline worktree `/opt/assetecon/AssetOpsV1-iap3main` is now at main `12e618be3`.

- Built, test-first:
  - D-IAP.42/43 server test (`test_iap_site_findings_parity_postgres.py`): MINI flipped (missing ids must sit on a
    Site whose estate coverage, keyed by `site_id` via `_site_uuid`, is not CURRENT/HISTORICAL; measured PARTIAL; a
    full subset fails "MINI parity holds: ship the MINI alias (D-IAP.42)"); COLD and EV normalised (`_normalise`),
    subset asserted before and after; pins written once (`IAP_WRITE_FIXTURES=1`, 267 s, 3 passed). COLD's month
    window is the 31 days ending on the data day (a calendar month is not stable under the shift; Known Deviation).
  - **SPEC_CONFLICT Q-P5-3 (Architect):** a second build (167 s) differs from the pins after D-IAP.43 normalising, in
    classes the ruling does not name: `run-<hex32>` ids, sha1/sha256 digests over ids, wall-clock record stamps
    (`as_of`, `decided_at`, `committed_watermark`), and arrays ordered by uuid value (so first-appearance tokens
    permute). Diff counts: cold-site 884 leaves, ev-site 1784; estate bodies not reported as drifting. The subset
    holds on both runs. The byte compare now `pytest.xfail`s with the drift named; a ruling (tokenise those classes
    and sort id-ordered arrays, or compare a projection) is needed before it can be a hard assert.
  - Client layer `estate/__tests__/siteFindingsParity.test.ts`: COLD and EV pass (2/2). Plant `parity` (`site_id`
    scope key in `findingsDef().site`): 2 failed, reverted.
  - D-IAP.42 alias: `SiteFindingsFrame` redirects COLD/EV to `/findings?{from,to,known_at}&scope=site:{id}`
    (`siteFindingsAlias`, `siteFindingsAliased` in `shell/siteSections.tsx`); the frame's cold/EV branches and its
    `coldAssessment`/`evAssessment` props are gone. MINI keeps its index, lit under Evidence, Evidence line
    "Records · Uploads · Findings" (also on MINI Evidence and Uploads). Test `shell/__tests__/siteFindingsAlias.test.tsx`
    (6 failed first, 6 pass solo). Register R796 (MD-IAP-15).
  - D-IAP.44: lifecycle word (`deriveSiteView` word, `<small data-lifecycle>`) on Sites rows and Outcomes L2 rows;
    Outcomes gets the directory through `EstatePortfolioFrame` → `OutcomesSites` (`useDirectorySites`,
    `lifecycleWords`); a refused directory read shows no word. 2 new `sitesList` tests (failed first); plant `nolife`
    failed 2, reverted. R795 now D2 (both homes named).
  - D-IAP.45: `sites/SitesIndex.tsx` and `sitesIndex.test.tsx` deleted (no export was imported elsewhere); the
    hard-wiring baseline entry, the `sharedVisualVocabulary` comment and the css header comment re-pointed.
  - Risks fixed: one Evidence line on cold/EV ("Records · Analysis · Uploads", drawn by `coldSiteViews`/`EvSiteViews`
    Subtabs through `ui/SiteSections`; `routes.uploads` added; shell no longer adds a second nav); Assets crumbs drop
    Health; Foundation row drops "Change & effect" (default `withChanges=false`; Changes pages draw no Foundation row,
    crumb "Changes"; R797). Tests migrated (b): `evSiteMoneyRoutes` (line), `operatorSiteTabs` (MINI line),
    `siteFoundationRevision` 3, `siteFoundationChange` 2, `foundationScreen` (passes `withChanges`).
  - Gates T1/T2 in `tools/iap_gates.cjs` (+ fixtures `fixtures/iap/site-{mini,cold,ev}.json` from
    `shell/__tests__/kobo-site-detail.json` with id/type/name replaced; `routes.json`). Fresh build, `vite preview`
    :5573: 62 of 62 pass. Plant `seventab`: T1 fails on all three, `operatorSiteTabs` 38 failed. Plant `crumb` (tab
    row on the mini Finding view): T2 mini fails. Shots and logs: `/opt/assetecon/evidence/IA-P/IA-P3/p5/` (132 files).
  - Layout evidence: not run (`tools/layout-evidence.mjs` needs the backend and a store; R4 at 390 in iap_gates passes).

## Next (P5 remainder, in order)

1. Migrate the alias fallout (branch run of estate+shell+ui+sites: 34 failed of 4144, 188 files, 192 s, at
   `188c5fee8`): `sites/__tests__/coldFindingIndex.test.tsx` (10) and `evFindingIndex.test.tsx` (9) mount the
   index at `/sites/:id/findings`, which now redirects; `siteRangeMatrix` "cold /findings (R)" and "ev /findings (R)"
   rows (now aliases); check `siteRangeMatrix` "each Site route" and `siteFindingsAlias` COLD (failed in-suite, passed
   solo: probably settle timing). The components `ColdFindingIndex`/`EvFindingIndex` are mounted by no route now:
   ask the Architect whether they go (D-IAP.45 logic) or their tests mount them directly. Compare the rest with the
   main run of the same scope (`vitest-main.log` from this run, see below); handoff run 3 lists the pre-existing ones.
2. Slice-end: move the per-file migration table into `packet-IA-P3.md` (§P5, with run 3's and run 4's rows),
   counts branch vs main, `test_iap_*` (branch run started this run; main once), guards, state entry 207, spec Status.

## Questions for the Architect (run 4)

- Q-P5-3 (SPEC_CONFLICT, D-IAP.43): the normalised bodies are not stable across builds (classes above). Which
  normalisation, or which projection, is the byte compare to run on?
- Q-P5-4: `ColdFindingIndex` and `EvFindingIndex` (and their tests) are unmounted by the alias: delete, or keep and
  re-mount their tests directly?
