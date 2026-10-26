# post-W6 W2-cold: build handoff (phase 1, partial: not started)

The pre-flight agent stopped at the context cap before writing product code. Branch `task/post-W6-W2-cold` at `077e15a9` (main merged in). Build exactly `.agent/post-W6-W2-cold-rulings.md`; the cross-card section binds. Use `.agent/post-W6-W2-cold-preflight.md` for anchors and literals. This file adds only the build plan and the dependency state.

## Dependency state (2026-10-24)

- **W2-EV has not built yet** (its branch has only its pre-flight). Two ruled interfaces are W2-EV's:
  - The `OperatorSiteTabs` optional window-aware href override (`shell/operatorSiteTabs.tsx:103`, currently `{siteId, current}` only).
  - The shared Site-timezone formatter (`eatTime` in `sites/coldSiteViews.tsx:168`, hard-coded +3 h, imported by `EvSiteViews.tsx:26`).
- **Do not edit either.** The cold main-tab window preservation (B14-10 consumer) waits for W2-EV and a rebase. For R259, write the cold calls through one local helper, e.g. `coldSiteClock(value, timeZone, measuredDay)` returning `{ text, utc }`, next to `utcClock` (:1061). After the rebase, delegate it to W2-EV's signature.
- **Quiet machine:** until the coordinator clears it, run only focused vitest files, typecheck, check-all and the guards. No Postgres tests, captures, full vitest or builds.

## Units (commit each, with focused tests)

1. **Refusal and performance screens** (`sites/ColdAssessmentViews.tsx`; export `RefusedStrip`/`RefusedTiles` from `coldSiteViews.tsx` :407-428).
   - `refusalText` :129: classify by `code` (`COLD_TIME_INVALID`, `COLD_WINDOW_INVALID`, `COLD_WINDOW_TOO_LONG`, other 422 → "The selected window is invalid."). Keep key `invalid-window`, title "Window cannot be read"; non-window refusals keep their titles.
   - `ColdPerformanceFrame` :806-813: drop `PageRefusal`, add RequestedWindowBar + RefusedStrip (chip = refusal title) + RefusedTiles + the technical references.
   - Hide the duration notice (:422) unless temperature loaded.
   - R241: StatusBar `action` "Inspect temperature claim" → `props.routes.evidence` + `?view=analysis` + the read's window. This needs the `routes` prop passed into the panels/status.
   - R242: `<small>` units and no `word` on the 8 cards (:267-297, :601-606).
   - R245: copy at :255 and at the limit row.
   - R246: :534.
   - R247: prose :592 and `establishes()` :493 override.
   - R249: :1096 → `Unknown · {site} · Confidence: Unknown`.
   - Tests: `sites/__tests__/coldRoutes.test.tsx` (pins at :284-292 and :793 change on purpose).
2. **Cold Overview** (`coldSiteViews.tsx` `OverviewCards` :471-521, `stripEvents` :525, OverviewScreen :540-690; `shell/coldSiteRoutes.tsx`).
   - Add `sld` (`siteFoundationViewHref(id,'sld')`) and `workMaintenance` (`siteWorkMaintenanceHref`) to `ColdSiteRoutes` (interface near `coldSiteViews.tsx:74`). Update the fixtures.
   - Five cards: plain labels plus MetricCard `link` "View detail →". Maintenance shows "Not summarised here" / "Maintenance cases are listed under Work".
   - The Overview reads `p.assessment.getBackupChain`; join by `evidence_id`; use `ADVERSE`/`RUNNING`/`outcomeText`, exported from ColdAssessmentViews :478-484.
   - "steps above" copy; SLD panel action; dedupe limitations (:629).
   - Tests: `coldSiteViews.test.tsx`. Overview fixtures need a `getBackupChain` stub.
3. **Evidence and Analysis.**
   - Strip action "Portfolio evidence" → `EVIDENCE_PATH` (:816).
   - Cooling row and cooling next-evidence items → "Review cooling →" (`routes.cooling` + window, :858/:1008).
   - Normal gap copy (:997), per Q10.
   - R259: pass `site.timezone` via `coldSiteScreen` (`coldSiteRoutes.tsx`) → ColdSiteFrame → Analysis. Format Measured/Sent/Received (:1135-1137) in the Site zone with seconds; show the date when the local day differs from Measured; exact UTC in `title`; UTC fallback when the zone is missing. Header names follow shell Q18.
   - Tests: Addis, UTC, midnight crossing, missing zone.
4. **Cold Findings index.**
   - New `ColdFindingIndex` in `ColdAssessmentViews.tsx`, per Q3 literals.
   - Export `LensChips` from `sites/SiteFindingIndex.tsx:78`; adding new chip literals would break the `navigation-truthfulness.ps1` multiset.
   - Add the cold branch in `SiteFindingsFrame` (`shell/SiteAnalyticsFrames.tsx:451`; edit only that hunk; pattern as :675) and the `coldAssessment` prop on `App.tsx:435`.
   - Tests: a new cold index test, plus `shell/__tests__/s404SiteFindingIndex.test.tsx` for mini/EV discrimination.
5. **After the coordinator clears the machine:** full vitest, typecheck, build, guards; recapture per ruling Q15. Allow 92 + 2 + representative regressions + URL-only invalid/too-long cold cases at both widths. Caps: cold Findings 550/850.

## Guards to keep

The `navigation-truthfulness` chip multiset, `missing-claim-scan` (no new "not available yet" text), and `shell-overflow`. Run `tools/check-architecture.ps1` and `tools/check-agent-workflow.ps1`.
