# IA-P1 handoff (partial: P1 done; P0 started; P2 not started)

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

Evidence (outside the repo): `/opt/assetecon/evidence/IA-P/P1/` (gate shots), plant outputs listed in the commit.

## Next: P0 (the long range; spec-period.md P.9)

Written, not yet green: `p0-pending/readWindow.test.ts.pending` and `p0-pending/noRawRangeReads.test.ts.pending` (move them to `frontend/src/ui/__tests__/` as `.test.ts`; they fail until the
source lands). The plan, already surveyed:
- `sharedRange.ts`: `RANGE_MAX_DAYS = 731`; `WHOLE_RANGE_PAGES = /^\/(?:portfolio(?:\/outcomes)?|sites)\/?$/`;
  `readWindow(params, now?)` → `{from, to, known_at} | null` (DayRange plus `known_at`); `windowBound(params, key)` (the
  request bound in the address's own form: raw within 31 days, the window's `from` beyond); a link-side helper returning
  the raw whole-range bound (`linkBound`) so link builders keep the whole range (P.9 "Links").
- Raw `get("from")`/`get("to")` sites (request → `windowBound`, link → `linkBound`): `shell/SiteAnalyticsFrames.tsx`
  491, 1330, 1352, 1471, 1886, 2042, 2263, 2282, 2555 (requests); `estate/estateShared.tsx` 44 (request; give the query
  a whole-range `link` pair that `estateHref` prefers, so pager/state/lens links keep the whole range);
  `sites/MiniOpportunity.tsx` 174 (link from a server link); `sites/SiteEvidence.tsx` 105; `sites/coldAssessmentClient.ts`
  221; `sites/miniDepthClient.ts` 438, 491, 539, 548, 566; `sites/EvFoundationViews.tsx` 70 (link);
  `work/globalWorkParts.tsx` 337; `sites/SiteRangeOverview.tsx` 464 (rewrite on `rangeWindow(range)`);
  `sites/LedgerSiteEvidence.tsx` 1165. Also `work/globalWorkClient.ts:793` reads `getAll("from")` (the global Work
  window, capped at 31): window it too, and keep `globalWorkHref` links on the whole range.
- Helper callers that build requests (move to `readWindow`): `SiteHealthFrames.tsx:162`, `SiteFinancials.tsx:968`,
  `MiniPerformance.tsx:460,1705`, `SiteWindowOverview.tsx:302`, `SiteOverview.tsx:103`, `EvidenceClaimLimit.tsx:273`,
  `PerformanceDispatch.tsx:121`, `miniDepthClient.ts:444,498,542,571`. `FocusPicker` and the bar keep the whole range.
- `SharedRangeBar.tsx` (line ~31 `const focus = useRangeFocus()`): with no declared focus, a range over 31 days and a
  page outside `WHOLE_RANGE_PAGES`, treat the window as a declared span (`data-shared-range-focus="inside"`, "Showing
  {span} of the range"). Open point (mid-build question to raise): apply it only where `readsSharedRange` is true (a page
  that does not use the range keeps "Not used on this page"); default applied: yes.
- `ui/RangePartNote.tsx` (new), `sharedRangeBar.test` (61-day `/findings` inside, `/portfolio` All pages), one request
  test per read family, plants `rawread` and `nowindow`, gates R7 and R8 in `iap_gates.cjs`.

## Then: P2 (lists)

Not started. Read IA-2b rev 2 at `task/IA-2b1-lists` `b3102080c` (`git show b3102080c:specs/IA-1-shape-rebuild/spec-IA-2b.md`),
then spec §5.2 and the P2 card. P2 adds Decisions to `IA_HOMES` (recommendation and alternatives views light Decisions),
makes the rail item live (update `navigation-truthfulness.ps1`, its fixtures, `iap_gates.cjs` RAIL), adds the P2
aliases to `LEGACY_ROUTES`, `/decisions` to `RANGE_PAGES`/`FILLED_PAGES`, `act-first` out of `PORTFOLIO_TABS`, and the
estate list fixtures to `fixtures/iap/routes.json`. Register MD-IAP-2 and MD-IAP-6.

## Risks

- The P0 sweep is wide (about 45 sites). The class rule is: requests read the window, links keep the whole range.
- The P1 plants `rail` and `alias` need a rebuild each; `routemap` is vitest only.
- `/evidence/records` now fills the range on entry (FILLED_PAGES, D-IAP.19), so a bare Records address opens on the
  7-day default instead of the Work page's own default; the request for an address that carries a range is unchanged.
