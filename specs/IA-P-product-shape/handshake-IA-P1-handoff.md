# IA-P1 handoff (partial: P1, P0 done; P2 code built, tests and gates open)

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

## P2 state (code committed "IA-P P2 (partial)"; the dispatch stopped near the context limit)

Settled first: `siteRangeMatrix.test.tsx` (2 tests) and `sr2RequestUrls.test.tsx` "SR-6b" (1 test) FAIL ON MAIN TOO (run in a
scratch worktree of main: 3 failed, 119 passed). Name them in the packet as pre-existing; do not fix.

Built (all type-check; `npx tsc --noEmit` clean for non-test files):
- `ui/homeListModel.ts` + `ui/__tests__/homeListModel.test.ts` (22 pass), `ui/HomeList.tsx`, `ui/homeList.css`.
- `estate/homeLists.tsx` (decisions, findings, actions defs, item builders, `DecisionsListPage`, `FindingsListPage`,
  `ActionsListPage`) + `estate/__tests__/homeLists.test.tsx` (22 pass).
- `estate/estateReadCache.tsx` (`loadAllPages`, I9 restart, provider mounted in `OperatorShellLayout`, `useEstateRead`).
- `shell/EstateRootFrames.tsx` (`EstateDecisionsFrame`, lens prop gone), `App.tsx` (`/decisions`; lens routes gone),
  `iaRoutes.ts` (Decisions home; aliases `/portfolio/act-first`, `/findings/cost|risks|opportunities`, unit IA-P1),
  `OperatorShellLayout.tsx` (Decisions rail live), `sharedRange.ts` (`/decisions` range page; lens paths out),
  `portfolioWords.ts` (`act-first` out of tabs; `DECISIONS_PATH` lives here), `PortfolioTabs.tsx` (`decisionsHref`),
  `EstatePortfolio.tsx` (PriorityPanel, FindingRow, placementRows, EvidenceAside deleted; `consequenceFirst`, `barBody`
  exported), `findingIndex.tsx` and `actionIndex.tsx` cut to the reused words, `estateClient.ts` (`waiting_count?`,
  `waiting_by_site?` typed), `test/settled.ts` ("the decisions across the estate").

Deviations to record in the packet:
- Branch is `task/IA-P1-frame-portfolio` (spec names `task/IA-P1-frame-range-lists`); the 731 literal (P0 test fix, 2024-10-31
  to 2026-10-31 is 731 days); `OPERATIONAL_RECORDS_PATH` stays (the cross-language fixture).
- I8: the mini-grid set for `findingLinkLive` comes from the body's own rows (`domain === "MINIGRID"`) and coverage, not an
  extra `/api/sites` read (the handshake said the Site directory from the shared cache). Same set today's page used.
- The Findings opportunity table rows and `OpportunityList` (CH-4) left with the old Findings table; opportunities remain on
  the Portfolio Opportunity tab. The early-warning list under the Findings table is gone with it (the Overview keeps its pulse).
- The Portfolio page keeps its `lens` plumbing as the constant `"all"` (P3b rebuilds the Overview); `portfolioHref`'s lens
  argument is unused.
- E0 is P4a: `waiting_count` is read when present (typed optional) and the tile counts rows otherwise.

## Open in P2 (do these next, in order)

1. Test fallout (113 failures in the last `src/estate src/shell src/ui` run; 1m39s). Retire or rewrite, never weaken:
   - `estate/__tests__/estatePortfolio.test.tsx` (41): the Act-first tab, PL-1 lens tests, CC-R2 table groups and FindingRow
     cell tests test deleted UI. Delete the retired ones (list them in the packet); fix the ones that only used the tab row
     (`PF-T ... tab links`, counts, `every tab link carries from, to and known_at`).
   - `estateRoots.test.tsx` (23): the Findings lens tables, CH-4 opportunities, OUT-A pills, OUT-C warnings under the table,
     the Actions table. Replace the live ones by assertions on the list (homeLists.test covers the new shape).
   - `estatePortfolioRoutes.test.tsx` (2): old `/portfolio?lens=X` now goes to `/decisions?lens=X` (EstatePortfolioPage);
     `test_w303_global_route_precedence...`.
   - Rail: `operatorRailInventory` (22), `sitesIndexRoute`, `siteDetailRoute`, `siteFoundationRoute`, `sharedVisualVocabulary`,
     `operatorRouteFrames`, `operatorSiteTabs`, `simulatorLabWorkspaceEntryPoint`: the Decisions item is live, so the live list
     gains `Decisions` (`/decisions`) and the unavailable list loses it ("Decisions, Not available yet" gone).
   - `sharedRange.test.tsx` (4): `/portfolio/act-first` expectations become `/decisions`; `t028Screens`,
     `w301EstateShellRoutes`, `DeepDiveMonth` test 13 (tab row without Act first), `iaRouteMap` ("unresolvable route constant
     DECISIONS_PATH": teach the test's constant resolver `portfolioWords.ts`, or import the constant from
     `operatorSiteRoutes.ts` instead).
2. `navigation-truthfulness.ps1` and its fixtures (Decisions live, `/decisions` a route), `iap_gates.cjs` RAIL and PAGES plus
   L1 to L3, `routes.json` estate bodies (portfolio, findings, actions; the gate serves them from `fixtures/iap/`).
3. Plants `tile rowctl restore cap dropref`: each a one-line edit shown failing then reverted. `cap` fails
   `homeListModel.test` (HOME_LIST_CAP 11), `tile` and `dropref` and `restore` fail `homeLists.test`, `rowctl` fails
   `homeLists.test` and gate L2.
4. MD-IAP-2 and MD-IAP-6 rows in `.agent/mock-departure-register.md` (MD-IAP-2 note gains the third State word, D-IAP.29).
5. `iaRouteMap` growth check, `iap_gates` and the fast `check-all`, lean screenshots at 1440 and 390
   (`/opt/assetecon/tools/pw`: `source env.sh && export LD_LIBRARY_PATH=$AUDIT_LD_LIBRARY_PATH`), light and dark.
6. `specs/IA-P-product-shape/packet-IA-P1.md`, spec Status in_review, built-state entry + `index-*.md` line, `specs/INDEX.md`
   row (index under 8000 bytes). Delete the scratch folder.

## Risks

- The P0 sweep is wide (about 45 sites). The class rule is: requests read the window, links keep the whole range.
- The P1 plants `rail` and `alias` need a rebuild each; `routemap` is vitest only.
- `/evidence/records` now fills the range on entry (FILLED_PAGES, D-IAP.19), so a bare Records address opens on the
  7-day default instead of the Work page's own default; the request for an address that carries a range is unchanged.
