# Final complete review: whole-diff findings (8b6ef3ed..5f71f6c9)

Independent reviewer, 2026-10-26, read-only (no tests run). Verdict: accept with three Medium to fix before the owner walkthrough; nothing High; no security regression, no backend contract break, no weakened or deleted tests.

## Medium

**M1. Default mini Work window shows wrong days in its own fields** (W5 R338 UTC-day default meets W4 R320 Site-local fields).
- `frontend/src/sites/workClient.ts:187-194` `defaultWorkWindow` returns `[today-6 00:00Z, tomorrow 00:00Z)`.
- `frontend/src/shell/SiteAnalyticsFrames.tsx:2337-2341` `workCasesScope` uses it for every Site type.
- `frontend/src/sites/siteWorkCases.tsx:315-331` `WindowForm` fills fields with `siteLocalDate` / `siteLocalLastDay`.
- Scenario: EAT mini Site, 26 Oct, `/sites/KOBO/work/incidents` bare. Read covers 20 Oct 00:00Z–27 Oct 00:00Z; "to (EAT, included)" shows 27 Oct (26 Oct 23:59:59Z = 27 Oct 02:59 EAT) so the form claims 8 days incl. tomorrow. Pressing Search unedited re-reads 19 Oct 21:00Z–27 Oct 21:00Z. Same on `/work/maintenance`. All demo Sites are EAT.
- Fix options: mini default = seven Site-local days (`siteLocalMidnightUtc(today-6)` to `siteLocalEndUtc(today)`), or rule which of R338/R320 wins for mini.

**M2. One shared Action shell shows different refusal controls on cold and EV.**
- `SiteAnalyticsFrames.tsx:1621-1645` `DomainActionShell`: cold 503 shows "Retry" (`COLD_WORK_RETRY`, no `reloadLabel`), no technical disclosure; EV shows "Reload" (`EV_WORK_RELOAD`) + "Technical detail" disclosure.
- Cold 409 → generic "The attempt was refused." with no button (`coldWorkPresentation.ts:127-131`); EV → "The Action changed while it was being read." + Reload (`evWorkPresentation.ts:97`). A cold Action that changes mid-read is a dead end. Makes backlog (h) more serious: 409 is a known code with a ruled EV sentence.
- App-wide label split: guide §5 "Reload"; cold depth "Retry" (`ColdCooling.tsx:157`, `ColdHealthDepth.tsx:67`, `ColdScenarios.tsx:109`, `coldSiteViews.tsx:339`); mini "Try again" (`MiniPerformance.tsx:302`), EV foundation same (`EvFoundationViews.tsx:235`); EV depth text says "Retry." while button says "Reload" (`EvAssessmentViews.tsx:105`).
- Fix: give cold `reloadLabel` and the same status map as `evActionRefusal` (409 → Reload); at minimum one word for the shell's button.

**M3. Phone-width rule caps the first column of every estate table, not just Findings.**
- `frontend/src/estate/estate.css:137-146`: inside `@media (max-width:640px)`, `.estate-page .data-table th/td/col:first-child { width:152px (!important) }` not limited by `:has(col.estate-findings-col)` (the 672px rule below is). Ruling Q8 (R295) covers Findings only.
- At 390px the Financials register (min 800px), Evidence, Actions and Portfolio tables get a 152px first column; long labels wrap into unmeasured tall rows.
- Fix: add the same `:has(...)` limit.

## Low

- **L1.** Refusals use `role="status"` in some places, `role="alert"` in others; guide §5 says one alert per refusal. Status: `MiniPerformance.tsx:295,402`, `ColdCooling.tsx:144`, `ColdHealthDepth.tsx:54`, `ColdScenarios.tsx:96`, `EvFoundationViews.tsx:219`, `SiteFinding.tsx:206`, `SiteFinancials.tsx:300`. Mostly predate this diff.
- **L2.** Same Action, two labels: global Work and request detail show stored `ACT-…` code (`global_index.py coded_actions`); Site Work shows `Action {first 8 chars}` (`backend/assetops_backend/work/site_index.py:208,215`). W6 Q10 excluded `site_index.py`; not a defect but unlogged.
- **L3.** Two sentences for the same EV tariff-estimate state: Site "No stored gross tariff estimate matches the current evidence." (`ev_site_reads.py:36`); estate pinned "Withheld · tariff basis has no stored consequence at this evidence cutoff" (`ev_site_reads.py:88`), system vocabulary.
- **L4.** Cold Financials > Scenarios tab row drops the selected window: `SiteAnalyticsFrames.tsx:1328` `<OperatorSiteTabs … current="Financials" />` without `search`, against cross-card ruling 3 (breadcrumb carries it). Fix: `search={coldTabSearch(site, params)}`.
- **L5.** `coldTabSearch` (`coldSiteRoutes.tsx:27-29`) passes a one-sided, reversed or >31-day window through; `evWorkTabSearch` (`evSiteRoutes.tsx:53-63`) drops it. A bad cold Work address sends every main tab into "Window cannot be read".
- **L6.** Zone-missing labels: mini bare "UTC" (`siteTime.ts:74`; `MiniScenarios.tsx:273`, `siteWorkCases.tsx:326`, `SiteFindingHistory.tsx:346`); cold/EV "UTC; Site time zone unavailable"; guide "UTC (Site time zone unavailable)". Mini Evidence records table labels zone only on "Measured"; cold/EV also on "Sent"/"Received".
- **L7.** Duplicated window controls/copy: three date-window forms with different rules (mini Work Site-local, end included, no reversed check; mini Scenarios Site-local, checks both; cold/EV `DomainWorkWindow` UTC, end exclusive). "Window cannot be read" defined 7 times; reversed/too-long sentences copied 3 times; selected-window reporting block copied 3 times (`SiteHealthFrames.tsx:40`, `EvAssessmentViews.tsx:697`, `EvSiteViews.tsx:438`).
- **L8.** Dead branch: 422 "Period cannot be read" at `MiniPerformance.tsx:288` unreachable (422 handled earlier by `MiniRefusedFrame`); non-standard title.
- **L9.** `evWorkPresentation.ts` R348 shows "needs both a start and an end, with the start before the end" for a correctly ordered non-UTC window.
- **L10.** `domainActionVerification.test.tsx` `it.each(["", "/plan", "/history"])` became `[""]`; covered by the new not-served test per R350 — coverage shift; confirm ruling cited.
- **L11.** `primitives.css` `.v69-key-values dd code` horizontal scroll box not keyboard reachable (no tabindex); 760px tab-row wrap written twice with different gap (`primitives.css` 0 vs `globalWork.css` 4px).

## Checked clean
- R373 `site_read_access` on Site Work, domain Work (reads+commands via `WorkGate`), four global lists, request detail (`main.py:577,582,592`); request detail via `gate.read_scope` (`global_work_api.py:58,110`); W6 links point to the same admitted Site. Estate roots still on `development_access` (backlog (d), R374).
- W3-estate links, W6 global Work basis/tokens/31-day limits consistent. Extra Action-code query per case row (performance note).
- Tests: none deleted; no skip/only/todo added beyond standard no-DB skip; removed assertions replaced by equal or stricter ruled ones.
- Not verified (no-run): test counts, suites, build, tsc, guards, 390px layout (M3/L11 from CSS reading).
