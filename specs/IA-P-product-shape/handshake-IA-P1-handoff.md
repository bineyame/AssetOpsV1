# IA-P1 handoff (partial: P1 and P0 done; P2 not started)

Builder (Claude), 2026-11-22. Branch `task/IA-P1-frame-portfolio` (worktree `/opt/assetecon/AssetOpsV1-iap1`; the spec names
`task/IA-P1-frame-range-lists`, the dispatch named this one). Stopped near the context limit as the dispatch requires.

## Done (P1, the frame; committed)

- `shell/iaRoutes.ts` (new): `IA_LANDED` (`IA-P1`), `IA_HOMES` (one entry per §2.4 family), `railHomeOf`, `tabGroupOf`,
  `LEGACY_ROUTES` (`/` → `/portfolio`, `/operational-records` → `/evidence/records`, unit IA-P1), `liveLegacyRoutes`,
  `mergeLegacySearch`. `shell/LegacyRedirect.tsx` (new). App.tsx mounts one redirect per live alias before the routes.
- The rail is §2.1 (`OperatorShellLayout.tsx`), `activeLabel={railHomeOf(pathname)}`; `railActiveLabel` is gone.
  `RailIcon` gains `decide`.
- `ui/SectionTabs.tsx` (new): one tab row, range on every link. `/evidence` and `/evidence/records` show H1
  "Evidence & records" (subtitles kept) and the Coverage · Records row. `OperationalRecordsFrame` is mounted at
  `EVIDENCE_RECORDS_PATH`; its own links use `/evidence/records`.
- `OPERATIONAL_RECORDS_PATH` stays `/operational-records`: it is the target of the `ESTATE operational_records` Ref,
  pinned by the cross-language fixture `shell/__fixtures__/route-refs.json` that `backend/tests/test_ch5a2_refs.py` and
  `chain/refs.py` also read. Spec §11 allows no other backend change, so those links go through the alias (query kept).
  Known deviation for the packet.
- `sharedRange.ts`: `/evidence/records` joins `RANGE_PAGES`, `FILLED_PAGES` and `WORK_PAGES`; `/operational-records`
  leaves them.
- Guards: `navigation-truthfulness.ps1` pins the §2.1 list, `activeLabel={railHomeOf(pathname)}`, `export function
  railHomeOf(pathname: string): RailLabel | null` in `iaRoutes.ts`, and `/` as the `LEGACY_ROUTES` alias.
  `navigation-rail-fixtures.ps1` re-pinned (new cases: Decisions made live, Plan given a destination, activeLabel={null}).
- Tests: `shell/__tests__/iaRoutes.test.ts`, `shell/__tests__/iaRouteMap.test.ts` (both ways, R4/I2), and the existing
  rail, route and Operational records tests updated to §2.1.
- `tools/iap_gates.cjs` (new): R1 to R6 over `/portfolio`, `/evidence`, `/evidence/records` at 1440 and 390, light and
  dark, plus 390 with the menu open, and R2 over both aliases. Fixture base `frontend/src/estate/__tests__/fixtures/iap/`
  (`routes.json` maps an API path to a file; empty in P1, any other `/api/*` is 404).
- Register rows R771 (MD-IAP-1) and R772 (MD-IAP-14), counts updated.

Evidence (outside the repo): `/opt/assetecon/evidence/IA-P/P1/` (gate shots at 1440 and 390, light and dark, plus 390
with the menu open; `gates-clean.log`), plant logs in `plants/`.

P1 plants (each a one-line edit, shown failing, then reverted with `git checkout`):
- `rail` (Decisions made live): `iap_gates` R1 "rail is [... live|Decisions|WORK ...]", exit 1; `check-architecture`
  navigation truthfulness "declares the rail items [...] but the W1 rail is exactly [...]" and "points at '/decisions'
  ... not a route"; the rail fixtures case "IA-P1: Decisions made live (plant rail)" holds it.
- `alias` (`/operational-records` entry dropped): `iap_gates` R2 "/operational-records landed on /operational-records,
  expected /evidence/records", exit 1; `iaRouteMap` (b) fails (1 failed, 2 passed).
- `routemap` (`<Route path="/x">` added): `iaRouteMap` (a) fails (1 failed, 2 passed).
- `activeLabel={null}` (I16): rail fixtures case "IA-P1: activeLabel={null} (plant)" expects the call-form failure.
- In-page: `--plant wide` fails R4 ("page width 616 px at a 390 px viewport"), `--plant tiny` fails R6.

## Done (P0, the long range; commit "IA-P P0")

- `ui/sharedRange.ts`: `RANGE_MAX_DAYS` 731, `READ_WINDOW_DAYS` 31, `WHOLE_RANGE_PAGES`, `readWindow`, `capWindow` (the
  arithmetic for a range already read), `windowBound` (request bound in the address's own form), `linkBound` (the
  whole-range bound, for links and server links).
- The sweep: every raw `get("from")`/`get("to")` now goes through `windowBound` or `linkBound` (`noRawRangeReads`
  scans the tree). Range-state callers window with `capWindow`/`readWindow`: `useRangeOverview`, `SiteHealthFrames`,
  `EvidenceClaimLimit`, `MiniPerformance` fuel nights, `miniDepthClient` (two builders). Estate: `EstateQuery.link` and
  `GlobalWorkQuery.link` hold the whole range when windowed; `estateHref` and `globalWorkHref` prefer it, so pager, state
  and lens links keep the whole range. `globalWorkPageQuery` windows a 32 to 731 day range (it refused before).
- The bar (`SharedRangeBar.tsx`): with no declared focus, a range over 31 days, a non-whole page that `readsSharedRange`
  (the open point's handoff default: range pages only), it declares `capWindow(range)` as a span: tag "inside", "Showing
  1-31 Oct of the range". `focusSpanLabel` and `FOCUS_INSIDE` moved to `ui/rangeFocus.tsx` (re-exported from the bar).
- `ui/RangePartNote.tsx` (new, tested; no page uses it yet: its blocks are P3 and P4).
- Tests: `readWindow.test.ts`, `noRawRangeReads.test.ts` (parked tests, one literal corrected: 2024-10-31 to 2026-10-31
  is 731 days, 2024-10-30 is 732), `rangePartNote.test.tsx`, a bar test and an R7/R8 request test in
  `shell/__tests__/sharedRange.test.tsx`, a four-family request test in `sr2RequestUrls.test.tsx` (health, mini depth,
  cold, EV). Old "longer than 31 days" refusal tests moved to a 2024 start (they now refuse at 731).
- Plants shown failing, then reverted: `rawread` (`SiteEvidence.tsx` back to `params.get("from")`) fails
  `noRawRangeReads` ("../../sites/SiteEvidence.tsx:106"); `nowindow` (the bar's auto-span returns `null`) fails the new
  bar test.
- Gates R7 and R8 in `tools/iap_gates.cjs` (`checkLongRange`).
- P1 test fallout fixed (rail labels, `/` alias, Evidence & records label) in operatorSiteTabs, sitesIndexRoute,
  simulatorLabWorkspaceEntryPoint, estatePortfolioRoutes.

Known, not mine (fail on the unchanged P1 head too): `siteRangeMatrix.test.tsx` (`/sites/:siteId/uploads` has no matrix
row; mini `/health` has an extra read) and `sr2RequestUrls.test.tsx` "SR-6b mini-grid Health" (an extra uploads read).
Links inside Site pages that rebuild from the raw window (SiteAnalyticsFrames action `window=`) were windowed with their
requests, not split; a Site-side `link` pair is not added (the spec names only the estate and Work links).

## Next: P2 (lists; not started)

Read in this order: spec.md §5.2 (the React transcription, the four defs table), §6 "P2" (files, tests, plants, gates
L1 to L3), and IA-2b rev 2 (`git show b3102080c:specs/IA-1-shape-rebuild/spec-IA-2b.md`): §3.1 model steps 1 to 7 (tier,
facets, search, sort, cap 10, keep-first, groups) and `iaListHref`'s order; §3.2 markup and chips; §3.3 write and
restore; §3.4 format; §7 copy; §8 Block A (the `homeListModel.test.ts` cases: tiers at 2, 3, 10, 11, 25). The model is
pure, so write `ui/__tests__/homeListModel.test.ts` first with literals.

Build order: `ui/homeListModel.ts` + test, `ui/HomeList.tsx` + `homeList.css`, `estate/homeLists.tsx` (decisions,
findings, actions defs) + test, `estate/estateReadCache.tsx` (mount in `OperatorShellLayout`), rewire `findingIndex.tsx`
and `actionIndex.tsx` and add `EstateDecisionsFrame` in `shell/EstateRootFrames.tsx`, App.tsx `/decisions` and the
aliases, `portfolioWords.ts` (`act-first` out of `PORTFOLIO_TABS`), `iaRoutes.ts` (Decisions in `IA_HOMES`, P2 aliases
in `LEGACY_ROUTES`, Decisions rail item live in `OperatorShellLayout`, `navigation-truthfulness.ps1` and its fixtures,
`iap_gates.cjs` RAIL and PAGES, `routes.json` estate bodies), `sharedRange.ts` (`/decisions` in `RANGE_PAGES`,
`FILLED_PAGES`), gates L1 to L3, plants `tile rowctl restore cap dropref`, MD-IAP-2 and MD-IAP-6 register rows,
`iaRouteMap` growth, then the packet.

## Risks

- The P0 sweep is wide (about 45 sites). The class rule is: requests read the window, links keep the whole range.
- The P1 plants `rail` and `alias` need a rebuild each; `routemap` is vitest only.
- `/evidence/records` now fills the range on entry (FILLED_PAGES, D-IAP.19), so a bare Records address opens on the
  7-day default instead of the Work page's own default; the request for an address that carries a range is unchanged.
