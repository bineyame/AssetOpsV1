# SR-4 packet: Site pages follow the shared date range (lane G)

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

## Fix round (Revision 10d, D-SR.40-44): ready for review
Branch merged with main bbec56c26. Rulings applied as written; no design.
- **D-SR.40 (26 tests):** updated to positive tests, none deleted: `s404SiteFindingIndex` (4), `coldScenarios` (1), `coldFindingIndex` (1), `w1f4ChangesWorkStructure` (2), `siteWorkCases` (M1 and `work_subtab_counts`: 2), `evDepth` (availability crumbs, R347), `evEnergy`, `evHealthDepth` (R347 + spy now gets the shared range), `evScenarios` (R347), `evAssessmentRoutes` (3), `evSiteMoneyRoutes` (SLD link + R347), `miniDecisions` (spy gets the shared range; the address is no longer rewritten because it already names a range), `miniBackupRoutes`/`miniFuelRoutes` (two-hour address reads the 12:00 local hour; bar tag "Showing 6 Oct of the range"; refused frame stays pinned by the reversed case), `globalIncidents`/`globalMaintenance` (Site links carry the page's range). R347 tests assert both cases: a valid address range is carried exactly, a reversed or one-sided one carries none.
- **D-SR.41:** (a) `readSharedRange` compares the raw instants first: a `to` instant not after the `from` instant is invalid (`ui/sharedRange.ts`); unit cases added (reversed and equal instants invalid, an hour in one day valid); `evFoundation` E4 passes unchanged. (b) Cold and EV correction links read "Open with the default date range" (`ColdDepthRefusal.tsx`, `EvAvailability.tsx`); `evDepth` R244 now compares the exact href (`...availability?known_at=<KNOWN>`), and `coldDepth` pins the exact valid-range href plus a reversed case with none. (c) **Site Maintenance list read already sends the range**: the raw request is `/work/maintenance?from=<range.from>&to=<range.to>&limit=5` (and the Incidents read likewise). The old test failed only because it ran `rangeless()` on the received requests but not on the expectation. The test now compares raw requests against the entry range. No code change, nothing unwindowed.
- **D-SR.42 (d):** pinned in `ui/__tests__/rangeLink.test.tsx` (3 cases). Implementation reading: a target that names its own `from` or `to` is returned as written (the address's other bound is never mixed in; a half range is the link's own choice); an own `known_at` wins and is not added twice; with none named, from/to/known_at are all added.
- **D-SR.43:** `SiteAssetsFrame` and `SiteAssetFrame` declare "current settings"; pinned in `siteRangeTags.test.tsx` for mini, Cold and EV.
- **D-SR.44:** Backup/Fuel keep the day tag (tests above). EV evidence and analysis reads: `evSiteClient` `getEvidence` and `getAnalysis` (`ev/evidence`, `ev/evidence/analysis`) send `from`/`to`/`known_at` from the address through `coldWindowSearch`, so **no SR-9 card is needed**. Cold and EV financial assumptions declare "prices valid now" (`evSiteRoutes.tsx`, `SiteAnalyticsFrames.tsx` cold branch); pinned in `siteRangeTags.test.tsx`; their range-money pages still say "All pages".
- Checks: App-level Site vitest, 87 files in 11 batches of 8 (`grep -rl "<App\b" ... | xargs grep -l "/sites/"`): 0 failures (103+143+197+380+231+148+90+318+155+149+181 tests). `tsc --noEmit` clean. `check-all.ps1 -Python /opt/assetecon/AssetOpsV1/.venv/bin/python`: 19/19 PASS (the Estate self-test failure noted earlier is gone with the merged main). Commit 286dd3237.

## Fix round 2 (D-SR.57, D-SR.59; reviews SR-4ab REJECT, SR-4c ACCEPT WITH NOTES): ready for review
Branch merged with main (D-SR.57-59). Commits bd1670482..HEAD on `task/SR-4-site-range`.
- **H-1/L-4 (D-SR.59)** `sites/miniDepthClient.ts`: Renewable passes the address through only when it is exact Site-local midnights 1-5 days apart (instant form); otherwise a valid range of <=5 days sends `localDaysWindow(tz, range.from, n)` (date string itself), a longer range keeps the last-5-local-days rule, a named day/no range as before. Service/Backup/Fuel pass through only an exact one-local-clock-hour instant window; the one-day pass-through is gone ("Yesterday" -> 12:00 local); a reversed/unparseable pair that `readSharedRange` rejects still passes through. Ranges are measured only through `addressRange`/`pageDay`.
- **Contract:** `frontend/src/sites/__tests__/fixtures/mini-windows-contract.json` (16 cases: Addis +3 and Bogota -5 x Yesterday, 7d, 30d, custom 2/5 days, day-form, story hour, story 3 local days; expected values derived independently in Python/zoneinfo). `ui/__tests__/sharedRange.test.tsx` asserts the client equals it (and known_at carried); `backend/tests/test_sr4_mini_windows_contract.py` (no DB) feeds every window to `hour_windows` renewable/service/backup/fuel: 66 passed. Non-vacuous: old client -> vitest 12 failed/13 passed; old client's raw Yesterday windows in the fixture -> pytest 8 failed.
- **App pin** `shell/__tests__/sr2RequestUrls.test.tsx`: Kobo Renewable and Service under "Yesterday" send exactly the pinned Site-local URL (stub refuses any other mini URL with INVALID_WINDOW) and show none of the refusal copies. Old client: 2 failed.
- **L-1** `SharedRangeBar.tsx` safety net: per key the address's `from`/`to`/`known_at` wins; test in `siteRangeCarry.test.tsx` (fails on the old code).
- **D-SR.57 L3** `ui/sharedRange.ts` `withRange`: a link naming its own from/to and no known_at gets the address known_at; `rangeLink.test.tsx` re-pinned + own-known_at case (old code: 1 failed). **L2** `MiniScenarios.tsx` header rewritten, no behaviour change. **Two declarers:** `WindowSpan` removed from the Service/Backup/Fuel hour views (it renders nothing visible; the FocusPicker in `MiniHourBar` declares the same day); Renewable keeps it.
- **SR-4c L1:** MOCK DEVIATION R718/R719 at `SharedRangeBar.tsx` FOCUS_INSIDE docblock, `SiteHealthFrames.tsx` mini Health, `SiteEvidence.tsx` PANEL_ALL_DATES.
- **L-2** `tools/checks/site-links-carry-range.ps1`: single quotes, `export { Link } from` and namespace imports now fail; self-test extended (3 new fixtures; dropping one from the scanner fails the self-test). **L-3:** tests "previous range wins over day" and a Kisiwa fixture (own zone; capabilities read gives the Fuel subtab, its link and click keep the range). Not done: the Kisiwa `finding-windows/<day>` request pin.
- Process note: while restarting the batch run I ran `pkill -f "vitest run src/"`, which would also have stopped any other lane's vitest run at that moment (none was running right after).
- Observation (not changed, ruling says "as now"): the long-range Renewable rule and the Service default hour still take `localDateOf(tz, UTC day start)`, so in a negative-offset zone they land one local day before the range's last date (still a window `hour_windows` accepts). Architect to confirm.
- Checks: tsc clean; App-level Site vitest (`<App\b` files with `/sites/` + `sites/__tests__/mini*` + `ui/__tests__/sharedRange|rangeLink`), 96 files in 12 batches of 8: 0 failures, 2277 tests (first pass found 5 failures in 3 batches: the Renewable reversed pass-through, restored; two pins re-pinned to D-SR.59/D-SR.57 in `miniRenewableRoutes` and `shell/__tests__/sharedRange`; those 3 batches rerun 380+182+129 passed); pytest contract 66 passed; check-all: for coordinator (only `site-links-carry-range` run: 0 failures).

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
- D-SR.61: long-range Renewable and Service/Backup/Fuel default hour use the date string itself (range.to / pageDay), not localDateOf(UTC midnight); Bogota contract rows re-pinned, +3 rows unchanged.
