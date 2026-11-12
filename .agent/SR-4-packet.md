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

## Resume points (4c), in order
1. Declarations still to add:
   - "prices valid now": the mini-grid Financials branch of `SiteFinancialsFrame` (`shell/SiteAnalyticsFrames.tsx:1404`, overview and assumptions views, `site_type === "MINIGRID"`) and `SitePricesFrame` (`shell/SitePricesFrame.tsx:145`).
   - "current settings": `SiteFoundationFrame` (`shell/SiteFoundationFrame.tsx:64`), `SiteFoundationChangesFrame` and `SiteFoundationChangeFrame` (`SiteAnalyticsFrames.tsx` ~2127/2166).
   - Span: Renewable over 5 days and the Service day. Use `<RangeSpan>` in `sites/MiniPerformance.tsx` near the window use (~451/878); the span is the local days or the service day.
2. EV `/sites/<EV>/financials`: `<Navigate replace>` to `siteEvFinancialsHref`, keeping the query, in `SiteFinancialsFrame` when `site_type === "EV_CHARGING"`.
3. Evidence panels (D-SR.7), the pre-flight item (c) still to check:
   - Do `/evidence/rejections` and `/analytics` accept from/to? Check the backend routes.
   - If not, add the panel line "All dates, not only the date range" (`data-panel-range="all-dates"`) in `SiteEvidenceFrame`.
4. Tests:
   - Update `shell/__tests__/sharedRange.test.tsx` "the label is true per route class". It currently FAILS: `/sites/MG-002` is now filled, so assert "Showing <yesterday> of the range" instead of "This page's own dates".
   - Update `s5SiteWindowOverview` "SR-2: a one-day board ..." (expects "Day shown: 24 Oct", which is now "Showing 24 Oct of the range").
   - Add tag/spoken-name cases per 8.2 row (Overview, Performance, Health, Financials, Prices, Foundation for each type), the EV redirect, and the Evidence panels.
5. **Not yet run:** the 86 App-level test files that render `/sites/...` (`grep -rl "<App\b" --include=*.test.tsx src | xargs grep -l "/sites/"`). Expect href-exactness failures; fix them with `rangeless(...)`. Also expect Next-day failures on story `day=` links (now the edge). Run them one file at a time, or as a normal suite now that the demo app is stopped.
6. `tools/check-architecture.ps1`: every check except two passes. Those two need `ASSETOPS_GUARD_PYTHON=C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe` (no .venv in this worktree); on the VPS, use its venv.

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
- (f) Cold/EV on a range with no event: not yet checked.
