# IA-P3 review packet (P4b, with D-IAP.35 and the existing-test migration)

Branch `task/IA-P3-sites-site-inbox`, worktree `/opt/assetecon/AssetOpsV1-iap3`. Head: see `git log -1` (stated in the hand-back).
Spec: `spec.md` rev 3 §6 P4b, §5.2, §5.3, §6 "Range pages"; `rulings.md` D-IAP.35 (merged from main `3cf6f893b`).
`USER_REVIEW_REQUIRED`: no (a build slice; the owner walkthrough is after the IA shape is built, `owner-review-at-product-shape`).
P5, P6 and P7 are built (§7, §8, §9); §10 lists every deviation. Ready for the one IA-P3 review.

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
- `test_iap_*` (4 files, one `--db-lane` call): 88 passed, 0 xfailed, 77 s (main: 85 in run 1, no parity file).
- `tsc` clean; `check-architecture` passed (clean, and the planted `SiteFindingIndex` outside `sites/` failed it).

## 8. P6 "Waiting for you" (spec §6 P6; D-IAP.37 Q12 to Q16)

### 8.1 What was built

- `shell/WaitingForYou.tsx` (new), mounted in `OperatorShellLayout`'s top bar after `SharedRangeBar`. The control is
  `<button type="button" class="ia-inbox" aria-haspopup="dialog" aria-controls="ia-inbox">`, the `action` icon, the label
  (visually hidden at <=640 px, `shell/waitingForYou.css`) and the badge (visible n, `aria-hidden`; hidden text
  ", {n} waiting"; absent at 0). `data-shell-control` marks it as shell chrome for tests that count a page's buttons.
- Q13: `waitingForAChoice(items, total)` and `waitingTotalOf(loaded)` in `estate/homeLists.tsx` are the one waiting total;
  the Decisions tile (`decisionsDef`, filtered: rows; whole: the truncated `waiting_count`) and the badge both call it.
  6f1 U2 re-sources this one function.
- Q12: the rows come only from `decisionItems(loaded.first, loaded.rows)` through `useEstateRead(…, "portfolio", …)`.
  The shell gets the app's estate client from the new `EstateClientProvider` (`estate/estateReadCache.tsx`, wrapped
  around `App`'s routes with `estateIndex`), so its cache key is the Decisions read's (`App` cannot pass the shell a prop:
  `navigation-truthfulness.ps1` pins `<Route element={<OperatorShellLayout />}>`). On `/findings` the page and the
  shell make one request (sr2RequestUrls row unchanged). `grep -rn "decisionItems(" frontend/src` (non-test) for 6f1's
  §4.4 sweep:
  - `estate/homeLists.tsx:77` (the definition), `:339` (`DecisionsListPage`), `:367` (Findings list join), `:430`
    (`DecisionsRows`);
  - `shell/WaitingForYou.tsx:53` (the inbox; `:6` is its doc comment).
- Q14: `Drawer`, `useDrawers`, `DrawerApi` moved unchanged to `ui/Drawer.tsx` (Close word as `DRAWER_CLOSE`), their rules
  to `ui/drawer.css` (the two `--dd-` tokens, `body.dd-locked`, `.dd-drawer*` and the <=600 px and reduced-motion rules).
  `DeepDiveMonth` and `PortfolioPeriod` import them; `DeepDiveMonth.test.tsx` passes unchanged. The Close button keeps
  `dd-button` (styled by `deepDiveMonth.css`, global in the one bundle).
- The drawer: "For you" "Not available yet" (MD-IAP-4); "In your portfolio" the `waiting` rows in server order, capped at
  10, `<a>{title} <small>{Site} · {placement word}</small></a>` (a row with no target is text), then "View all {n}" to
  `/decisions?state=waiting` with the range, shown only when n exceeds the rows shown; empty "Nothing else is waiting
  for a choice"; "Since you last looked" the first 3 `progress.rows` as "Action {code} · {outcome words}"
  (`displayCode`, `progressOutcomeWords`, Q15), then "See all in Results" to `/results` with the range; empty "No change
  recorded in this range". Loading: "Loading Decisions…"; a refusal: its copy. A link inside closes the drawer.

### 8.2 Tests first, plants

- `shell/__tests__/waitingForYou.test.tsx` (8 tests) failed first (module missing), then passed. It covers badge = tile
  (25 rows, 23 waiting, one read), truncated (1,010 rows, `waiting_count` 1,007), absent at 0, the shared function, the
  sections and caps, the empty states, and the focus cycle (focus to Close; Escape and scrim close; focus returns; Tab wraps).
- Plant `badge` (the badge counts every row, `items.length`): 4 failed (both badge = tile tests, absent at 0, the cap
  test's "View all 23"); reverted.
- Plant `focus` (no focus return: `opener.current?.focus()` removed in `ui/Drawer.tsx`): both focus-cycle tests failed;
  reverted.

### 8.3 Existing tests migrated (the shell now reads the Decisions read on every operator page)

- Shell buttons: `simulatorLabGate`, `sitesIndexRoute`, `siteFoundationChange` exclude `[data-shell-control]` beside
  `[data-shared-range-button]`.
- A page's own requests: `test/shellReads.ts` (`isShellInboxRead`, `pageRequests`); `miniServiceRoutes`,
  `miniBackupRoutes`, `siteWorkCases` drop the shell's read from their request lists.
- Estate reads pinned on purpose: `sr2RequestUrls` `/portfolio/outcomes` now expects the portfolio URL twice (the Outcomes
  tab reads page 1 outside the shared cache, the shell through it) and `/maintenance` adds the shell's read;
  `estatePortfolioRoutes` counts 2 on a bare `/portfolio` (the default window on mount, then the completed address) and 2
  on the tab switch test (unchanged across the switch); `sharedRange` compares distinct requests.

### 8.4 Known deviations and risks

- On `/portfolio/outcomes` the portfolio page-1 URL is requested twice (the Outcomes tab's own read and the shell's cached
  read). On a page whose address has no range yet, the shell reads the default window once before the address is
  completed. Neither is a second Decisions read; both are left for P7 or the coordinator.

### 8.5 Checks at head

See `IA-P3-handoff.md` run 6 for the counts and shots. `iap_gates.cjs`: 63 of 63 pass (W1: badge "6" = tile "6"; the
top bar one row at 1280, 45 px high for a 32 px control).

## 9. P7 scope and search (spec §6 P7; D-IAP.40, D-IAP.41)

### 9.1 What was built

- `shell/ScopeSwitch.tsx` (new). The button reads "All sites ▾", "{domain word} ▾" or "{Site name} ▾" from the
  address's `scope`. The menu (`role=menu`, arrow keys, Escape returns focus, a click outside closes) lists "All sites",
  one entry per domain present (the directory's `site_type` through `DOMAIN_WORD`, in its order, no quoted literal; Q24),
  then the Sites in directory order. On a list (`/decisions`, `/findings`, `/actions`, `/sites`) an entry writes
  `scope=` and keeps every other parameter (facets, sort, `q`, the range); `show` goes, as `homeListHref` drops it.
  On a Site page or a hub, a Site entry opens `/sites/{code}` with the range, and a group or all writes `scope=` (all
  removes it) on the same address (Q23). The directory is read only when the menu opens or a Site is the scope.
- `EverySiteChip` (same file), placed in `OperatorShellLayout` above the page: "This page shows every Site" on the
  Overview, Demand & capacity, Outcomes (so above L1), Results and Evidence & records (and its Records tab) while the
  scope is not all (D-IAP.40, MD-IAP-5, register R798). Site pages and lists show none.
- Every `HomeList` surface already applied `scope` through `homeListModel` (Decisions, Findings, Actions, Sites, the
  Overview's Decisions rows, Outcomes L2, whose "Show all" carries it through `homeListHref`); P7 adds the test that
  Outcomes L2 follows a group scope.
- `shell/SearchPalette.tsx` (new). The button (accessible name "Search Sites, decisions and Findings"; visible text the
  full label above 1360 px, "Search" below, plus the "Ctrl K" hint above 640 px) and Ctrl K / ⌘ K open and close a
  `role=dialog` with one `role=combobox` input and a `listbox`. Entries: Sites (`display_name`, "Site",
  `/sites/{site_id}`), Decisions (`title`, "Decision · {Site}", `decisionsDef().target`), Findings (`title`,
  "Finding · {Site}", `findingsDef().target`), Actions (`action_title`, "Action · {owner or Site}",
  `link_refs.action`), then each live rail item (label, "Go to"); an entry with no target is not indexed (Q25). Words
  ANDed, case-blind, over the label and its kind; the first 20 in that kind order. Arrow keys move
  (`aria-activedescendant`), Enter opens with the range, Escape closes; focus returns to the element focused before.
  The reads are the lists' cached reads (`useEstateRead`, same keys) and the directory, made only while it is open.
  `decisionItems(` is called by that name (`shell/SearchPalette.tsx`) for 6f1 U2's §4.4 sweep.
- `OperatorShellLayout`: the top bar is Scope · Search · range bar · Waiting for you; Scope and Search sit at the start,
  and the bar wraps at <=640 px (`shell/scopeSearch.css`, tokens only; the panel and menu use P6's `--dd-` scrim and
  shadow tokens).
- `EstateClientProvider` (P6, kept: D-IAP.37 did not name it) gained an optional `directory` (`App` passes
  `siteDirectory`), read by `useProvidedSiteDirectory()`.
- §8.4's double read: the Outcomes and Demand & capacity tabs (`PortfolioTabsPage`, `estate/EstatePortfolio.tsx`) now
  take page 1 from `useEstateRead(reads, "portfolio", window)`. The shared key `(client, "portfolio", range)` already
  allowed it: the cache's first page is the tab's former query (`lens=all`, `limit=50` = `ALL_PAGES_LIMIT`,
  `cursor=null`). No design choice was needed. The tab's own per-key `Map` and the PL-1 held read (a lens change; the
  lens is always `all` on these tabs) are gone.
- Walk (Q26): `backend/conversions/walk-layer4-v1.json` `pages` adds `/decisions`, `/results`, `/portfolio/outcomes`,
  `/portfolio/demand-and-capacity`; `test_t11_smoke_pages`'s literal and `test_t8_smoke_node_env_is_exactly_six`'s page
  count (10 -> 14) in the same commit (`backend/tests/test_wk_walk_world.py`; red first: 1 failed, then 103 passed).
- Gate K1 in `tools/iap_gates.cjs` (`checkSearch`): on `/decisions` at 1280, Ctrl K opens the dialog with the input
  focused, Ctrl K closes it with focus back on the Search button, Escape does the same; with `--shots`, the scope menu
  and the palette at 1440, 1280 and 390, light and dark (a `/api/sites` directory of the E1 Sites served for K1 only).

### 9.2 Tests first, plants

- Red first (`2fa9f30b3`, tests only): 14 failed of 18. `shell/__tests__/scopeSwitch.test.tsx` 12 failed (no
  `[data-scope-switch]`, no chip; its Outcomes L2 test and the three "does not" chip rows passed, since `HomeList`
  already scoped L2); `shell/__tests__/searchPalette.test.tsx` failed to load (module missing);
  `estate/__tests__/outcomesOneRead.test.tsx` 2 failed ("expected [ {…}, {…} ] to have a length of 1 but got 2" on
  `/portfolio/outcomes` and `/portfolio/demand-and-capacity`). After `fb0aee8cd`: 24 of 24 pass.
- Plant `scopedrop` (`scopeTarget` keeps only the range): `scopeSwitch` 2 failed (the two "on a list" tests); reverted.
- Plant `deadlink` (`searchEntries` indexes every rail item, `to ?? "/"`): `searchPalette` 2 failed (the entries test and
  the in-shell "plan" query); reverted.
- Plant for K1 (no focus return: the `focus()` in `SearchPalette`'s close effect removed, rebuilt): `iap_gates.cjs` 1
  failed of 64, K1 only ("Ctrl K did not close it with focus returned", "Escape did not close it with focus returned");
  reverted and rebuilt.

### 9.3 Existing tests migrated

- `shell/__tests__/sr2RequestUrls.test.tsx` "SR-2 the demo's API requests are byte-identical", `/portfolio/outcomes` row:
  back to one `/api/estate/portfolio?…&limit=50` (P6 had pinned it twice, §8.3); (b), §8.4's double read is fixed.
- `estate/__tests__/estatePortfolioRoutes.test.tsx` "a tab switch stays on the one mounted route and does not read
  again": `portfolioCalls` 2 -> 1 (the tab and the shell share the read; the switch still adds none); (b), same cause.

### 9.4 Known deviations and risks (P7)

- **`EstateClientProvider` kept** (P6; D-IAP.37 did not name it) and widened: it now also carries the Site directory
  (`directory`, `useProvidedSiteDirectory`) so the shell's scope menu and search reach `App`'s `siteDirectory` (the shell
  takes no props: `navigation-truthfulness.ps1` pins `<Route element={<OperatorShellLayout />}>`). For the reviewer.
- **A group scope on Findings and Actions shows no rows.** `findingsDef` and `actionsDef` have `site` but no `domain`
  (their rows carry no domain), and `homeListModel`'s `inScope` refuses a `group:` scope on a def without `domain`.
  Before P7 no control offered a group scope on those lists; the switch now does. Resolving it needs a domain source
  for those rows (the directory by `site_code`, or a served field): a design choice, not made (question 1 below).
- **Search button text**: the accessible name is the spec's "Search Sites, decisions and Findings"; the full label is
  visible only above 1360 px, "Search" below (the 1280 top bar stays one line, gate W1), and the "Ctrl K" hint is shown
  above 640 px on every platform (⌘ K works but is not drawn).
- **The palette's panel and the scope menu use `--surface-raised`**, as P6's drawer does: in dark mode they draw light
  (the dark shots show it), the same as the month's drawers today.
- **The Outcomes and Demand tabs now wait for every page of the shared read** (up to 20 × 50 rows) instead of page 1
  alone, and a later page's refusal (not a first-page code) shows as the tab's refusal. The shell already made those
  pages on every operator page since P6, so no request is added.
- **`/results` still reads page 1 outside the cache** (`estate/Results.tsx:30`, the same URL as the shell's first page),
  so it is requested twice there; a range-less address reads the default window once before `SharedRangeOutlet`
  completes it (P6). Neither was in P7's brief; left for the coordinator.
- **Scope on a Site page** (`/sites/{code}?scope=…`): the button reads the scope, the page is unchanged (D-IAP.40); the
  rail and in-page links carry only the range, so leaving a list drops `scope=` (as before P7).
- Register: R798 (MD-IAP-5, D5, open until scoped reads) and R799 (MD-IAP-9's scope-menu part, D4) appended after R797.

### 9.5 Questions (P7)

1. A group scope on `/findings` and `/actions`: should their defs take a domain (from the directory by `site_code`, which
   adds the directory read to those lists, or from a served field), or should a `group:` scope be ignored on a def without
   `domain` (`homeListModel`, as a def without `site` ignores every scope)?
2. `/results` reads page 1 outside the shared cache (twice with the shell): fold it into the cache as P7 did for the
   Portfolio tabs?

### 9.6 Checks at head `6dbfb3a34` (evidence `/opt/assetecon/evidence/IA-P/IA-P3/p7/`)

| Check | Head `6dbfb3a34` | Main `12e618be3` |
| --- | --- | --- |
| vitest `src/estate src/shell src/ui src/sites` (run from `frontend/`) | 190 files, 4158 tests: 10 failed, 4148 passed; 124 s | 184 files, 4093 tests: 12 failed, 4081 passed (run 4) |
| Head's 10 failures, all in main's set | `s502OverviewFindingList` 2 (the load flake; names vary by run), `siteRangeMatrix` 2, `sr2RequestUrls` SR-6b, `domainActionVerification` R348, `evActionFixRound` L5, `evSiteMoneyRoutes` 2, `siteWorkCases` R322 | |
| backend `test_iap_*` (4 files, one `--db-lane` call) | 88 passed, 75 s | |
| `tsc --noEmit` (in the fresh `npm run build`) | clean; built | |
| `check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON`), `check-agent-workflow.ps1` | passed, passed (at head with this packet) | |
| `tools/checks/statement_catalogue.py` | exit 0 | |
| `backend/tests/test_wk_walk_world.py` | 103 passed | |
| `tools/iap_gates.cjs` on `vite preview :5573` | 64 of 64 pass (fresh build; 301 s): T1 and T2 on the three verticals, W1 badge "6" = tile "6" with four top-bar children at top 6 (bar 45 px, control 32 px), K1 open, Ctrl K close and Escape close with focus returned; 12 P7 shots | |

An earlier head run (`de2528004`) had 12 failed: the `estatePortfolioRoutes` pin migrated above, and `simulatorLabGate`
"operator route /" (fails on main too, §7 table), which passed in the final run. A first run from the repo root read CSS
by relative path and failed 38 with ENOENT; it is not counted.
Layout evidence: the gates' page checks (1440, 768, 390, light and dark), W1 at 1280, and the P7 shots
(`shots/p7-scope-*`, `shots/p7-search-*` at 1440, 1280, 390, light and dark); `layout-evidence.mjs` not run (the top
bar is measured by W1).

## 10. IA-P3 slice end: every deviation, in one list

- §4: the template-lineage note and "In setup" left the Sites list (R795 re-housed them, D-IAP.44).
- §7: MINI keeps its Site Findings index (MD-IAP-15, R796); the cold index's columns and the Site's early warnings have
  no home on the Findings list (§7.3); one Changes name (R797); the Q-P5-3 byte compare rests on D-IAP.46's projection.
- §8.4: a range-less address reads the default window once before it is completed.
- §9.4: `EstateClientProvider` kept and widened with `directory`; a group scope on Findings and Actions shows no rows;
  the Search button's visible text below 1360 px; the panel and menu light in dark mode (as the drawer); the Portfolio
  tabs wait for every page of the shared read; `/results` still reads page 1 twice; `scope=` is not carried by links.
- Register rows of IA-P3: R790 to R799.
- `USER_REVIEW_REQUIRED`: no. IA-P3 (P4b to P7) is ready for its one review.

## 11. Fix round 1 (review-IA-P3.md; D-IAP.48 to D-IAP.51)

Merged main (D-IAP.48 to D-IAP.51) first; the only conflict was the spec's Status line. Tests first: the new and flipped
tests failed before the fix (9 failed / 64 passed across `homeLists`, `sitesList`, `scopeSwitch`;
`/opt/assetecon/evidence/IA-P/IA-P3/fix1/red1.log`).

- **D-IAP.48 (H1)**: `estate/siteDomains.ts` (`useSiteDomains`) reads the Site directory only while the scope is a group and
  joins on `site_code`, case-blind. `findingsDef` and `actionsDef` take `domainOf` and gain `domain`; their `scopeWord` is
  `scopeChipWord` (`DOMAIN_WORD`). `FindingsListPage` and `ActionsListPage` take an optional `directory` (else the
  provider's). Loading shows "Loading Findings…" / "Loading Actions…"; a refused directory shows
  "The Site list cannot be read right now, so this group cannot be applied." with "Try again". A row with no
  directory entry is in no group. Sweep: `grep -n "site: (" frontend/src/estate/*.tsx` finds four defs, all now with `domain`.
- **D-IAP.49**: `Results.tsx` reads `useEstateRead(reads, "portfolio", window)`. The `sr2RequestUrls` pin is reported below.
- **D-IAP.50 (M1)**: `EverySiteChip` shows on every path that is neither `LIST_PATHS` nor `/sites/{code}…`. `scopeSwitch`
  case for `/incidents`. R798 and the file header widened (MD-IAP-5 in the spec was widened by the ruling).
- **D-IAP.51 (M2)**: `OutcomesSites` passes the directory rows to `siteItems`; the builder's test is flipped and the parity
  case holds a directory-only Site.
- **Lows**: R800 added (COLD/EV "Records · Analysis · Uploads"); R328 restated against the object-page trail (D-IAP.38 Q20);
  Site scope matching is case-blind in `homeListModel.inScope` and `scopeWord` (test: `scope=site:cold-lab-001`).
- Plants (each run, watched fail, reverted): see section 11.1.

### 11.1 Fix round 1: plants and checks (evidence in `/opt/assetecon/evidence/IA-P/IA-P3/fix1/`)

- Plant `nodomain` (both `domain` lines dropped): 4 of the 6 new `homeLists` cases fail (rows, rows, refusal-retry, no-entry
  row). Plant `chiplist` (the five-page list restored): the `/incidents` case fails. Both reverted (`plants.log`).
- vitest `src/estate src/shell src/ui src/sites` at fix head: 190 files, 14 failed / 4151 passed (4165) before the three
  test-wording fixes; after them the three `homeLists` cases pass. Remaining failures are main's `12e618be3` set (12 failed /
  4081 passed): s502 (flaky within the file: 2 on main, 1 or 2 here), siteRangeMatrix 2, sr2RequestUrls, domainActionVerification,
  evActionFixRound, evSiteMoneyRoutes 2, siteWorkCases. `coldWorkCases` and `outcomeBoard` failed once in the full run and pass
  on rerun with `homeLists` (`rerun.log`). `sr2RequestUrls` does not count `/results`, so no row is re-pinned.
- `test_iap_*` 88 passed (84 s). `tsc` clean. Fresh `npm run build` clean. `iap_gates.cjs`: 64/64 (`gates.log`).
  `check-architecture`, `check-agent-workflow`, `statement_catalogue.py`: pass. No server or job left running.
- `USER_REVIEW_REQUIRED`: no.
