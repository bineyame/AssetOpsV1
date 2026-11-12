# SR-4 packet: Site pages follow the shared date range (lane G) — PARTIAL, resume on the VPS

Spec: architect rev 8 (`architect-sequence-client-scope-2026-11-11.md` top), D-SR.1-8 (`build-sheet-OWN-GAPS-2026-11-08.md`), register R718/R719. Branch `task/SR-4-site-range` (fast-forwarded to main a6d40513f before the build).

## Commits
- `59acd65c4` SR-4a: done.
- `59bccda4d` SR-4b: done.
- `77924b3ff` SR-4c WIP: partly done (see the resume points). tsc is clean at this commit.

Review plan: review 4a and 4b together. 4a alone makes Service/Renewable worse: the safety net adds 7 days to a `day=` story link, and only 4b's window rules fix that. Review 4c on its own once it is finished.

## Done
- **4a.**
  - `ui/RangeLink.tsx` and `carryRange`/`SITE_PATH`/`isSiteContentPage`/`weekEnding` in `ui/sharedRange.ts`.
  - Codemod of 93 non-test `.tsx` files (`RangeLink as Link`). It was done with a node script run from the scratchpad, not by hand; labelled reading of "Write/Edit only".
  - Safety net in `SharedRangeOutlet` (`shell/SharedRangeBar.tsx`): it takes the previous in-app range, else the 7 days ending on `day`, else `entryRange()`. It covers Site content pages only (Overview, Performance(/x), Findings, Evidence, Work(/incidents|/maintenance), Financials(/assumptions|/scenarios), Health, `/ev/...`). It does not cover Foundation, Prices, record pages or the Sites index.
  - Guard `tools/checks/site-links-carry-range.ps1`, registered with a self-test. Non-vacuous: it fails on main's `operatorSiteTabs.tsx`, and so does `siteRangeCarry.test.tsx` (4 of 10 fail).
  - Tests: `ui/__tests__/rangeLink.test.tsx` 8/8, `shell/__tests__/siteRangeCarry.test.tsx` 10/10.
- **4b.**
  - `pageDay` and `addressRange` in `ui/sharedRange.ts`.
  - `SiteOverview.selectionOf` now uses `pageDay` (date=<range.to>).
  - `PerformanceDispatch` uses `pageDay`, and `todayUtc` is deleted. The Kisiwa `finding-windows/<day>` read uses the same `day` (line ~566).
  - `miniDepthClient`, Service: the address window is used only when it is exactly 1 h or 1 day, or not a positive span (so a reversed window is still refused with its reason). Otherwise the 12:00 local hour of `pageDay`.
  - `miniDepthClient`, Renewable: the address window when it is at most 5 days (`MINI_RENEWABLE_DAYS`; the backend `mini_depth/read.py` takes 1-5 whole local days). Otherwise the last 5 local days when no `day` is named. **Labelled reading:** a named `day` reads that one local day, which keeps the story pins byte-identical.
  - Prev/Next edge text in `SiteWindowOverview` (`data-day-step-edge`).
  - Tests green, run one at a time:
    - new `ui/__tests__/sharedRange.test.tsx` 7
    - `sr2RequestUrls` 17 (new board pins `date=<range.to>`; the Dispatch pin is in `performanceDispatch.test` because the App path stops at /analytics)
    - `performanceDispatch` 45
    - `s5SiteWindowOverview` 69
    - `s502OverviewFindingList` 37
    - `miniRenewableRoutes` 19
    - `miniServiceRoutes` 16
    - `operatorRouteFrames` 22
  - Test helper `test/rangeless.ts` (it compares a path without from/to/known_at, as SR-2 did).
  - Replaced rows, not deleted: the Renewable "six days" refusal and the Service "two hours" refusal are now positive tests of the new rule. "Next day" story steps now use "Previous day", because a story day is the last day of its 7-day range.
- **4c (WIP).** `ui/rangeFocus.tsx` now has the span/now kinds, `useDeclareRangeSpan`, `useDeclareRangeNotUsed`, `RangeNotUsed`, `RangeSpan`, and uses layout effects. The `SharedRangeBar` tags follow the 8.2 table. Mini-grid Health declares "shows now".

## 4c done on the VPS (commits de0375733, e885670f4 and the next one)
- Declarations: "prices valid now" on mini-grid generic Financials (overview + assumptions) and `SitePricesFrame` (every Site type); "current settings" on `SiteFoundationFrame` (every view, every type), Foundation changes and change. Span (`WindowSpan` in `sites/MiniPerformance.tsx`): Renewable, Service, and also Backup and Fuel's hour view (same `serviceWindowFromParams` window; labelled extension), declared only when the read window is not the whole range.
- Spoken name for "now": "This page shows the present state / the current settings / the prices valid now" (labelled reading: "shows shows now" read badly).
- EV `/sites/<EV>/financials` (overview view only) → `<Navigate replace>` to `/ev/financials`, query kept.
- Evidence (D-SR.7): backend `/evidence/rejections` reads only `batch`, `/analytics` reads no query → line "All dates, not only the date range" (`data-panel-range="all-dates"`, `data-panel-range-for=rejections|analytics`) under Rejected records and in "How each limit is set" (only when a declaration loaded). `PANEL_ALL_DATES` in `sites/SiteEvidence.tsx`.
- Defect found and fixed (SR-4a): `withRange` added a second `known_at` to a target that named its own; now it keeps the target's. Test in `rangeLink.test.tsx`.
- Tests: new `shell/__tests__/siteRangeTags.test.tsx` 7/7 (tags + spoken name for mini/Cold/EV Health, Financials, Prices, Foundation, Performance, Service, Renewable; EV redirect); `siteEvidenceScreen` 16/16 (2 new); `sharedRange` (shell) 23/23 and `s5SiteWindowOverview` 69/69 updated; `rangeLink` 9/9. `test/rangeless.ts` now also takes arrays/nullables. tsc clean.
- Mini Overview/Dispatch tag needs a loaded board (FocusPicker): pinned in `s5SiteWindowOverview` only.

## App-level Site vitest (87 files, batches of 8)
- First pass: 11 batches, 45 failing tests in 26 files. Fixed so far: all of batches 0-3 (t028Screens, siteOverviewScreen, siteFoundationRoute, operatorSiteTabs, siteDetailRoute, siteDetailScreen) and the href-exactness lines elsewhere.
- **Still failing: 31 tests in 18 files** (list: rerun `grep -rl "<App\b" --include=*.test.tsx src | xargs grep -l "/sites/"`, or the files below). They are not href exactness; each tests behaviour the SR-4a safety net or 4b defaults superseded, and needs a per-test ruling, not a mechanical rewrite:
  - "no range / no window chosen / bare address" cases now get the 7-day range: `s404SiteFindingIndex` (4), `coldScenarios` (1), `w1f4ChangesWorkStructure` (2), `siteWorkCases` (3), `coldFindingIndex` (1), `evSiteMoneyRoutes` (2).
  - "a refused read carries no window on the tabs" (R347/Q14): tabs now carry the address range: `evDepth` (4), `evEnergy`, `evHealthDepth` (2), `evScenarios`, `evAssessmentRoutes` (3).
  - Mini refused window "two hours" (R313) now replaced by the 4b hour rule: `miniBackupRoutes`, `miniFuelRoutes` (same as the Service row already replaced in 4b).
  - `coldDepth` 422 invalid window, `miniDecisions` scenario time bounds (spy args), `evFoundation` source control "only a valid window", `globalIncidents`/`globalMaintenance` (global Work links to `/incidents`/`/maintenance` expected the range; check whether RangeLink should carry on non-Site Work paths — it does not today).

## Resume point
1. Fix the 31 above one file at a time (replace superseded assertions with positive tests of the new rule; never delete).
2. Guards: check-all result below.
## Pre-flight answers (8.5)
- (a) Route classes, every route under `/sites` in `App.tsx` (no operator `/performance/...` routes exist):
  - R: Findings, Work, Evidence, Scenarios, Cold/EV pages, Renewable ≤5 days.
  - D: the mini-grid Overview, Dispatch, Service, Renewable >5 days.
  - N: mini-grid Health/Financials, Prices, Foundation (+changes), the Sites index.
- (b) Today defaults:
  - `PerformanceDispatch` `todayUtc`: fixed.
  - `miniDepthClient` :341/:365: fixed.
  - `SiteAnalyticsFrames.tsx` `todayWindow`: Findings index with no from/to. Unreachable in-app now that the safety net fills `/findings`; left as the no-range fallback.
  - `workClient.ts:192`: the R338 Work default. Superseded on Site Work by the safety net; global Work is unchanged.
  - The other `toISOString().slice(0,10)` hits format instants; they are not page days.
- (c) Rejections/analytics range params: open (resume point 3).
- (d) The Renewable server limit is 1-5 whole Site-local days (`backend/assetops_backend/mini_depth/read.py:7`).
- (e) Codemod file list: `git show --stat 59acd65c4`.
- (f) Cold/EV on a range with no event, and EV `/ev/financials` same fingerprint: NOT checked (needs the DB/demo serve; this lane ran without a DB). Pending.
- (f, rev 10 10.5 "Assets list, battery page"): `/sites/:id/assets` (`SiteAssetsFrame`) and `/sites/:id/assets/:assetId` (`SiteAssetFrame`) are generic for every Site type; they read `/api/sites/{code}/battery` and `/assets/{id}/battery` (`asset_boundary_api.py`), which take no query and return Foundation configuration with condition always UNKNOWN (no SOC/readings, `battery_boundary.py`). So for Cold and EV too: **N (configuration), no readings, no SR-9 card needed.** Cold/EV have no other asset routes (their unit/charger detail lives inside windowed Health). Open: the asset pages declare nothing to the bar.
- Routes under `/sites` not in the rev 10 10.5 table (Architect question, D-SR.17): Performance Backup and Fuel (mini; same hour window as Service, now declared as a span), Fuel finding (`SITE_FUEL_FINDING_ROUTE_PATH`), Mill/Fuel verification, Opportunity detail (five-day, from the Renewable CTA), Action pages, EV evidence/analysis, EV and Cold financial assumptions, EV/Cold scenarios.
