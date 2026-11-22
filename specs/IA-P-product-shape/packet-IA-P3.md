# IA-P3 review packet (P4b, with D-IAP.35 and the existing-test migration)

Branch `task/IA-P3-sites-site-inbox`, worktree `/opt/assetecon/AssetOpsV1-iap3`. Head: see `git log -1` (stated in the hand-back).
Spec: `spec.md` rev 3 §6 P4b, §5.2, §5.3, §6 "Range pages"; `rulings.md` D-IAP.35 (merged from main `3cf6f893b`).
`USER_REVIEW_REQUIRED`: no (a build slice; the owner walkthrough is after the IA shape is built, `owner-review-at-product-shape`).
P5, P6 and P7 are not built (next runs).

## 1. What was built

- **P4b** (run 1, `IA-P3-handoff.md`): the Sites list and Outcomes on E1; `/sites` a range page; gate S1.
- **D-IAP.35, tests first** (`863eafec9`; both new tests failed first: Group "Not available yet" for "Cold-chain", and
  "Not shown: 1 Sites."):
  - Q1: a directory Site E1 lacks takes its Group from `DOMAIN_WORD[site_type]` ("Not available yet" when unmapped) and
    its waiting count from E0 (0 when absent from `waiting_by_site`); every other cell "Not available yet". `SiteItem`
    gained `group`, which also feeds search text and the domain scope (`estate/sitesList.tsx`).
  - Q5: `def.more` is "Not shown: 1 Site." for one hidden row, "Not shown: {h} Sites." otherwise.
- **(a) fix** (`19ea9374d`): `HomeList` gained `options.labelledBy`; `SitesListPage` passes `sites-heading`, so the
  `/sites` table's scroll region is a named, keyboard-reachable region again (`ui/HomeList.tsx`, `DataTable`).
- **Test infrastructure**: `test/sitesE1.ts` (`sitesE1(rows)`: the served mode-`none` E1 body with the given rows and no
  notes; `estateE0(waitingBySite)`: the default estate client with E0 from the World A fixture), `test/rangeHrefs.ts`
  (`pathsWithOneRange`: paths in order, asserting every link carries one `from`/`to` query), and `test/settled.ts`
  now waits on "Loading Sites…" (it did not, so a `/sites` test could read the page before E1 answered).

## 2. Test migration: the 41 existing frontend tests P4b broke (per file)

Rule (IA-P2 §2): (a) the slice broke real behaviour, fix the code; (b) the test pins the shape the spec replaced, migrate
it and cite the section. **(a) = 0 of the 41, (b) = 41.** No assertion was loosened to pass. Most route tests mounted
`/sites` with no E1 client, so E1 was refused and no row rendered; each now passes `sitesE1()` (and `estateE0`).
Making the list render exposed 3 more tests (passing vacuously at head before): one is **(a)**, the fix above
(`overflowContainment` "keeps the region reachable by keyboard, and named"); two are below (`operatorRouteFrames`).

| File | n | a/b | What changed, and why |
| --- | --- | --- | --- |
| `shell/__tests__/sitesIndexRoute.test.tsx` | 18 | (b) | The directory table ("Site inventory") is replaced by the Sites list (§6 P4b). Row: the name links to `/sites/MG-002`, Group "Mini-grid", waiting "0" (D-IAP.35 Q1); the ID, source, origin, lifecycle and template cells left with the table. One target per row (D-IAP.6): the `View` link is gone, hrefs compared by path (list links carry the range). The digit rule now counts E0 as a record (`{MG-002: 7}`), `length > 0` kept. Empty sentences: "No Sites in this scope." (the list's `none`). W1-F1's v69 panels (3) replaced by "the one list in every directory state", which pins D-IAP.35's "a refused directory read renders E1's rows alone". R127/R120 root crumb: §5.3 list header, no crumb (asserted absent). |
| `shell/__tests__/operatorRouteFrames.test.tsx` | 3 (+2) | (b) | Empty sentence as above; "unreadable store" now means a refused E1 (its served text and Try again, pre-flight Q8), not the directory. +1 digit rule: on `/sites` the one digit is the Sites tile's count "0" (§5.2 tiles); other routes keep zero digits. +1 navigation test needed only `estateE0` to keep the default client's other reads (no assertion changed). |
| `shell/__tests__/simulatorLabGate.test.tsx` | 2 | (b) | Empty sentence. The `/sites` "no controls" test now passes with E1 answering (the refused E1's Try again button was the control). The `/` variant fails on main too (below). |
| `shell/__tests__/operatorSiteTabs.test.tsx`, `siteDetailRoute.test.tsx`, `siteTemplateCatalog.test.tsx` | 1 each | (b) | Wait on the list, not "Site inventory"; the empty sentence. |
| `shell/__tests__/simulatorLabWorkspaceEntryPoint.test.tsx` | 1 | (b) | No root crumb on the list page (§5.3): the rail is the only navigation, and the crumb is asserted absent. |
| `shell/__tests__/siteTemplateLineage.test.tsx` | 1 | (b) | The note sat in the directory table's row; the list has no template column. Retired, with the replacement "no note on the Sites list" (the row is there, the note is not); the Site page tests for the note are unchanged. Question 1. |
| `shell/__tests__/siteRangeCarry.test.tsx` | 2 | (b) | "Sites index not filled" becomes "filled" (§6 "Range pages", D-IAP.19; the Foundation still not filled). The rail-to-cards test passes with E1 answering. |
| `shell/__tests__/operatorRailInventory.test.tsx`, `w301EstateShellRoutes.test.tsx`, `w302EstateEvidenceShellRoute.test.tsx` | 1 each | (b) | Mounted at `/sites`, which now fills its range, and the rail keeps it (SR-1): labels and paths pinned as before, plus every link carries the one range. |
| `ui/__tests__/sharedVisualVocabulary.test.tsx` | 3 | (b) | Rail as above (1). The two badge tests pinned the directory row's mode, lifecycle and origin badges; the list's cells are text-only (D-IAP.6). Replaced by "the list row draws no badge, from a template or not" with Group "Mini-grid". |
| `ui/__tests__/overflowContainment.test.tsx` | 3 (+1) | (b) (+1 (a)) | With E1 answering, the list table sits in the scroll region with its semantics; the column set is the list's (§4.3 E1 `columns`). +1 (a): the named keyboard region (fix in §1). |
| `estate/__tests__/estatePortfolio.test.tsx` | 2 | (b) | "Outcomes across the estate" is inside the closed Disclosure "Each Site's objectives" (§6 P4b): the tests first assert it hidden and closed, then open it. "Nothing before panel 1" on Outcomes becomes §6 P4b's order (L1/L2 before L3; L3 holds only the range note, the cards and, last, the Disclosure). |

**Not migrated (fail on main too, same assertion and line).** `sr2RequestUrls` SR-6b "the range page and its one-day
drill-in": the extra request is `/api/sites/KOBO-001/reading-uploads`, identical on main `3cf6f893b` (line 255), so it is
not P4b's. `siteRangeMatrix` (2: "each Site route in App.tsx has a matrix row", "mini /health (R)"), `simulatorLabGate`
"offers no way to create a site from the operator route /" (line 387, one button), same on main.
`s502OverviewFindingList`: a load flake on both trees (alone at head, 1 then 2 failures, different tests; on main 1).

## 3. Checks (head `590cfce9a` plus the docs commit)

| Check | Head | Main `3cf6f893b` (`/opt/assetecon/AssetOpsV1-iap3main`) |
| --- | --- | --- |
| vitest `src/estate src/shell src/ui` | 103 files, 2022 tests: 6 failed, 2016 passed; 74 s | 101 files, 2000 tests: 4 failed, 1996 passed; 96 s |
| Head's 6 failures | `siteRangeMatrix` 3 (the 2 above plus "cold /health (R)", passing alone), `sr2` 1, `simulatorLabGate` `/` 1, `s502` 1 | `siteRangeMatrix` 2, `sr2` 1, `simulatorLabGate` `/` 1 |
| backend `test_iap_portfolio_period/_sites/_waiting_counts.py` (host runner, `--db`) | 85 passed | 85 passed |
| `tsc --noEmit` | clean | |
| `npm run build` (fresh `dist`) | built | |
| `tools/iap_gates.cjs` on `vite preview :5573` | 56 of 56 pass (S1 at Oct: −$852.00 = −$852.00; Sep–Oct: −$1,704.00 = −$1,704.00) | |
| `check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON`), `check-agent-workflow.ps1` | passed, passed | |
| `tools/checks/statement_catalogue.py` | exit 0 | |

Before the migration, head was 47 failed of 2022 in 207 s (the refused-E1 path made the suite slow); 41 were P4b's.
Gate log and shots: `/opt/assetecon/evidence/IA-P/IA-P3/p4b-migration/`. Layout evidence: the gates' page checks at 1440,
768 and 390, light and dark; `layout-evidence.mjs` not run (the only layout change is a `role=region` and `tabindex`).

## 4. Known deviations

- The template-lineage note ("Created from v1; current template is v2") and the v69 "In setup" panel have no place on the
  Sites list (spec §6 P4b removes the directory table; §5.2 has no such column). The note stays on the Site's own page.
- `sites/SitesIndex.tsx` (the directory table) is mounted by no route now; its substrate test still runs. Left in place.

## 5. Questions

1. Is losing the template-lineage note and "In setup" from `/sites` accepted (deviation, register row), or does either
   need a home on the list?
2. May `sites/SitesIndex.tsx` and its test be deleted in P5, or kept?

## 6. Review focus

`estate/sitesList.tsx` `siteItems` (directory rows), `ui/HomeList.tsx` `labelledBy`, and §2's (b) calls, above all the
retirements (`siteTemplateLineage`, the two badge tests, W1-F1, R127 crumb).

## 7. P5 (D-IAP.38 to D-IAP.47): per-file test migration

Rule as §2: (a) the slice broke real behaviour, fix the code; (b) the test pins what the spec replaced, migrate it and
cite the section. Nothing was loosened to pass; a deleted test names the content it covered.

### 7.1 Run 3 (`1607351ac`, `bbb707964`): six tabs, object pages (spec §2.3, §6 P5, D-IAP.38)

| Files | Tests | Class | Why |
| --- | --- | --- | --- |
| `siteAction` 16, `miniDecisions` 3, `evAssessmentRoutes` 3, `domainActionVerification` 2, `coldWorkActions` 1, `w1f4ActionStructure` 1, `siteFuelFinding` 1 | 27 | (b) | object pages draw no tab row; the crumb has three parts (§2.3) |
| `operatorSiteTabsOverride`, `siteDetailRoute`, `siteFoundationRevision`, `siteFoundationRoute`, `t028Screens`, `coldDepth`, `coldHealthDepth`, `evFoundation`, `evSiteMoneyRoutes`, `mini{Backup,Fuel,Renewable,Service}Routes`, `siteFoundationChange`, `siteHealthBoundary`, `siteWorkActions`, `mockDeviationStyle`, `overflowContainment` (19 files, count by `git show --stat bbb707964`) | 27 | (b) | the tab row is six labels with the section line under it (§2.3, `SITE_TAB_OF`) |
| `SiteAnalyticsFrames.tsx` stale `mock-deviation.css` import | 1 | (a) | fixed in code |

### 7.2 Run 4 (alias, Evidence line, Foundation row)

| File | Class | Why |
| --- | --- | --- |
| `evSiteMoneyRoutes` (line), `operatorSiteTabs` (MINI Evidence line "Records · Uploads · Findings") | (b) | one Evidence line (D-IAP.38, D-IAP.42) |
| `siteFoundationRevision` 3, `siteFoundationChange` 2, `foundationScreen` | (b) | the Foundation row no longer carries "Change & effect" (R797) |
| `coldFindingIndex` 10, `evFindingIndex` 9 | (b), see 7.3 | D-IAP.42 alias; D-IAP.47 deletes the screens |
| `siteRangeMatrix` "cold /findings (R)", "ev /findings (R)" | (b) | rows are now alias rows (7.4) |
| `siteFindingsAlias` COLD (failed only in the full run) | no defect | passes alone and on the 143-test run of three files; a load timing failure under a full run (see 7.5) |
| `simulatorLabGate` "operator route /" | not this slice | fails alone on main `12e618be3` too: "/" draws the Overview's "Try again" button when its unstubbed period read is refused (`PortfolioOverview.tsx`); listed on main in §3 |
| `coldWorkCases` | no defect | passes alone (142 of 143 in that run, the one being `simulatorLabGate`) |

### 7.3 D-IAP.47: the 19 tests sorted (`ColdFindingIndex`, `EvFindingIndex` deleted)

Moved (b) to a test of the Findings list at `scope=site:{id}` or of the alias:
- range kept through the redirect (`from`, `to`, **and** `known_at`): `siteFindingsAlias` COLD and EV (known_at added) and
  `siteRangeMatrix` alias rows; the main tabs carry `known_at` on the kept MINI index: `siteFindingsAlias` MINI (was
  `coldFindingIndex` "mini keeps the mini index"; the EV file's "leaves a mini Site on the mini index" is the same test);
- the Site's rows only, and the empty state in the def's words: `homeLists` "Findings list at scope=site:{id}" (2 new);
- a refused window says the shared sentence: already `homeLists` "refused window ... each list says the shared sentence"
  (covers `r253_refusal 0`, the EV "refuses a window" test).

Deleted with the component, content named (it is not on the Findings list; for the walkthrough):

| Test(s) | Content only the old index drew |
| --- | --- |
| `r253_selected_rows_columns_and_windowed_links`, EV "lists the selected EV Findings", EV Q23 | the 7-column table (Domain, Priority, Confidence, State, Main consequence, Lens), "Not assessed" cells, the Domain link to Performance temperature or backup, "Began ... ended" period, the cold read's own window/cutoff when the address has none, MOCK DEVIATION R435 and R436 labels |
| `r253_no_selected_assessment` | "No cold assessment for this window" (the list has no selected-assessment state) |
| `r253_cursor_note`, EV "states empty and cursor", EV "keeps paging honesty" | the first-N paging note (the list reads every page, I9) |
| `r253_refusal 1`, `r253_refusal 2`, EV "does not call a 503 a window error" | "Source permission refused" and "Assessment unavailable" strips and their references panel (the list says one sentence per refusal) |
| `OUT-A A4` cold and EV (2) | the Affects / Also checked pills on the Site index rows (the list rows carry category labels, projected in the parity pin) |
| `OUT-C U5` cold and EV (4) | the Site's early warnings under the Site Findings list (`EarlyWarnings`, still used by other pages); **not on the Findings list: named as missing** |

Code removed: `sites/EvFindingIndex.tsx`, `ColdFindingIndex` and its props, `COLD_FINDINGS_*`, `coldFindingsCursorNote`,
`episodePeriod`, `mainConsequence` (all in `ColdAssessmentViews.tsx`), unused imports there, and `ROADMAP_WORDS`
`coldFindingsNotGlobal`, `evFindingsNotGlobal`, `manageFindings` (the owner-example assertion in `roadmapWords.test.ts`
now keeps `reviewRecommendation` only).

### 7.4 `siteRangeMatrix`

`RangeMatrixEntry.alias` (new): cold and EV `/findings` rows are `R` with `alias: true`; the R-row test skips them and a
new "alias rows" describe asserts the redirect to `/findings` with `scope=site:{code}` and `from`, `to`, `known_at` kept
(plus a non-empty-set guard). The two failures left (`each Site route`: `/sites/:siteId/uploads` has no row; `mini
/health (R)`) fail identically on main `12e618be3` (run alone there).

### 7.5 D-IAP.46 and the guards

- Parity pin: `_projection` compares the envelope and the named row fields (tokens by episode_start then title, Site body
  first), hard assert, no xfail. Plants `estatedrift` and `sitedrop`: see 7.6.
- `check-architecture` (site-substrate pattern widened in run 4 to `SiteFindingIndex` and `SiteControlsTable`): planted
  `export function SiteFindingIndex()` in `frontend/src/shell/PlantSubstrate.tsx`; it failed with "Site presentation
  component declared outside the shared substrate in frontend/src/shell/PlantSubstrate.tsx:1"; file removed, guard clean.

### 7.6 Counts and plants at head

- Parity (`--db-lane`, whole file): 3 passed in 78 s, hard projection assert, no xfail. Plants: `estatedrift` (`estate/index.py`
  row `site_name` = site code): cold and ev failed ("`$.estate[0].site_name: 'Cold replay lab' != 'COLD-LAB-001'`");
  `sitedrop` (cold Site findings read minus its last item): cold failed on `$.site` while the subset held; both reverted.
- vitest `src/estate src/shell src/ui src/sites` at head: 186 files, 11 failed / 4115 passed (4126), 126 s. Main
  `12e618be3`: 12 failed / 4081 passed (4093), 184 files, 213 s. Failures at head are main's set (s502 2, siteRangeMatrix 2,
  sr2RequestUrls, domainActionVerification, evActionFixRound, evSiteMoneyRoutes 2, siteWorkCases) plus `evScenarios` R347
  (fails only in the full run: the Site tabs read the window before the read settled; passes alone on head and on main, 4 of
  4). Not failing at head: `linkRefOnly` (main flake), `siteFindingsAlias` COLD, `coldWorkCases`, `simulatorLabGate` (it fails
  alone on main and head, passes in the full run: order/timing, not this slice).
- `tsc` clean; `check-architecture` passed (clean, and the planted `SiteFindingIndex` outside `sites/` failed it).
