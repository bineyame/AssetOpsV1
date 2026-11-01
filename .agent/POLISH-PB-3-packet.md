# POLISH-PB-3 review packet: estate, cold/EV and work copy; P-07, P-09, P-10

- Task: `tasks/POLISH-PB-3-estate-work-copy.md`. Branch `task/POLISH-PB-3-estate-work-copy`, base `0ad27df7f`.
- Spec: `.agent/build-sheet-POLISH.md` §1.2, §1.4 (frontend half), §1.5, the §3.1 estate/cold/EV/work rows, §5 PB-3, and Addenda 4, 5, 6 Q4, 7, 8, 12.
- USER_REVIEW_REQUIRED: false. The copy joins the R655 plain-language row, which the owner approves at the walkthrough.

## Outcome

All PB-3 frontend hits from the PA-3 strict capture are now 0 on the polish build:
- portfolio "Finding COLD-LAB-001 · <uuid>" ×5 and "Scenario" ×2;
- cold-normal "Running";
- EV `REC <uuid>` ×3 and "Scenario details";
- preventive "running" and "draft" ×2.

Feature changes:
- **P-07:** the repeat-visit notice has four settled states and shows on `wr-overview`. R630 is closed.
- **P-09:** Preventive shows real due counts, a badge, row chips, and Site-zone due dates.
- **P-10:** the cold "What happened" panel names the window's incident.
- The out-of-capture UTC list from the PB-1 packet is done.

The work was built in four disjoint file groups (estate, cold/EV + P-10, UTC long tail, work + P-07/P-09). Each group was committed separately and checked here.

## Pre-flight (Addendum 12) and step 0

- **Q1-Q3:** the wire fields went to PA-3. The frontend treats them as optional.
- **Q4:** "Not yet approved"; "No preventive plans in this window."
- **P-07 step 0: PASS.**
  - Served demo3 (PID 25432) and called `GET /api/sites/COLD-LAB-001/outcome-board`.
  - `warnings[]` holds `REPEATED_MAINTENANCE_NO_RESULT`, href `/maintenance/requests/6d715387-39a8-436f-a52c-282e8350e558`, count 3.
  - Serve stopped by PID; port 8990 free.

## Wire shapes as served (polish build, PA-3 `84ab3ca3d`)

- **Board case item** (`in_hand`/`earlier`):
  - `{"text":"WR-007 · Starter battery replaced","href":"/maintenance/requests/53e4…","result_label":"Did not fix it","detail":null,"kind":"MAINTENANCE_REQUEST","occurred_at":"2026-10-06T16:20:00Z"}`.
  - The cold failure window `[2026-10-30T16:00Z, 17:05Z)` holds `kind:"INCIDENT"`, "INC-005 · Backup response failure", `occurred_at` `2026-10-30T16:11:00Z`, href `/sites/COLD-LAB-001/work/incidents`.
  - The kind for requests is `MAINTENANCE_REQUEST`; Addendum 12 says "WORK_REQUEST". The frontend tests only `INCIDENT`.
- **`/api/work/preventive`:**
  - `summary {"overdue_count":2,"due_soon_count":2,"not_assessed_count":1}`, `total_count` 5.
  - Row: `{trigger_kind:"CALENDAR", next_due_at:"2026-10-21T00:00:00Z", due_state:"OVERDUE", site_time_zone:"Etc/UTC", asset_label:"Connector c1", asset_type:"EV_CONNECTOR"}`.
- **Request detail `work_asset`:** `{"code":"generator-1","type":"GENERATOR","asset_label":"Backup generator"}`.

## Files materially changed

- **Estate:**
  - `estate/{EstatePortfolio,PortfolioOutcomes,findingIndex,actionIndex,EstateFinancials,EstateEvidence}.tsx`
  - `estate/{portfolioWords,estateFinancialsWords,estateEvidenceWords}.ts`
- **Cold/EV:**
  - `sites/{coldSiteViews,ColdAssessmentViews,ColdScenarios,ColdCooling,coldDepthGraphics}.tsx`
  - `sites/{coldAssessmentWords,coldFormat,coldWorkPresentation}.ts`
  - `sites/{EvSiteViews,EvAssessmentViews,EvAvailability,EvEnergy,evDepthGraphics}.tsx`, `sites/evWorkPresentation.ts`
  - `sites/OutcomeBoard.tsx` (`onRead`), `sites/outcomeBoardClient.ts` (optional `kind`/`occurred_at`)
- **Work:** `work/{GlobalPreventive,WorkRequestOverview,workRequestShared,globalWorkParts,GlobalMaintenance}.tsx`, `work/globalWorkClient.ts` (types), `sites/siteWorkCases.tsx`.
- **UTC tail:**
  - `sites/{PerformanceDispatch,SiteFinding,LedgerSiteEvidence,SiteFindingIndex,SiteFindingEvidence,SiteWorkActions}.tsx`
  - `sites/{findingPresentation,EvidenceClaimLimit,SiteFindingHistory,MiniPerformance,SitePerformance,MiniScenarios}.tsx`
  - `sites/{SiteAction,SiteHealth,FoundationRevisionPanel,FoundationBindingsPanel}.tsx`, `sites/domainActionClient.ts`
- **Shared:** `ui/TechnicalDetails.tsx` (`TechnicalReferences`), `test/v69PanelTitles.ts` (`cold:4`/`ev:4` "Possible cost").
- **Tests:** about 30 test files under `estate/`, `work/`, `sites/` and `shell/`, updated for the new copy, plus the new tests listed below.
- **Records:**
  - `.agent/mock-departure-register.md`: R660-R662 added, R630 closed, PB-3 note on R655.
  - `.ai/CODE_STATE.md`: "POLISH PB-3".

## Acceptance criteria

| Criterion | Status |
|---|---|
| Estate §3.1 rows | Met. Lane A halves are listed under Residual risk. |
| Addendum 8 Q4: "What-if" / "No reviewed what-if yet" (R655) | Met |
| Cold/EV §3.1 rows; Addendum 8 Q3 "Possible cost" | Met |
| Addendum 8 Q5 / Addendum 5: cold/EV id leaks into Technical details; `ColdAssessmentViews:237` | Met (`TechnicalReferences`). Foundation `ExactReferences` outside cold/EV files: not touched (not on capture screens). |
| P-10, three texts, no new fetch | Met. 3 tests (incident in window with WR and out-of-window distractors and a single-fetch check; loaded with none; board unavailable), plus an `onRead` test. Seen on `cold-board-failure`. |
| P-07, 4 states with `data-repeat-check` | Met. 4-state test. The notice shows on `wr-overview`. |
| P-09: cards, badge, chips, Site-zone dates, two-part note | Met. Tests cover counts 2/3/1, 0 overdue → "None overdue", the plural line, the chips, and Addis Ababa 22:30Z → 29 Oct. Seen on `maintenance-preventive`. |
| Addendum 6 Q4 / 12 Q3: parsers replaced; `work_asset.asset_label` with `assetWords` fallback; no "EV connector" | Met |
| Addendum 7 Q1/Q6: out-of-capture UTC list; two-part note on Preventive, Maintenance and request pages | Met. Exceptions are under Residual risk. |
| Strict captures `portfolio-week`, `findings-*`, `cold-board-*`, `ev-board-fault`, `maintenance-preventive`, `wr-overview` | Met: 0 counted hits |
| check-all 12/12, tsc, scoped and full vitest | Met. See Checks. |

## Checks

- **tsc:** `npx tsc --noEmit -p .` gives 0 errors.
- **check-all:** `tools\check-all.ps1 -Python <plan2 venv>` on `a5e514ecf`: **All 12 guards passed**.
  - The first run, on `ca6f5d6bd`, failed 3 guards, all fixed in code or copy, with no guard changed:
    - Architecture seams: a `variant` prop in the shared Site substrate (`TechnicalReferences` in `ColdAssessmentViews`). It moved to `ui/TechnicalDetails.tsx`.
    - Missing-claim scan and its fixtures: 8 untagged "not available yet" strings. These were reworded; see D1.
- **Scoped vitest per group:**
  - estate 87/87;
  - work 223, plus cold/site work 60/60;
  - UTC tail 1105/1110, where the 5 failures were other groups' pins, fixed;
  - cold/EV 651/659, where the 7 panel-title failures were fixed in `v69PanelTitles` and the 1 timeout passed alone;
  - re-run after the fixes: 11 files 354/354, and 2 files 97/97.
- **Full `npx vitest run`:** on `a5e514ecf`: **Test Files 150 passed (150); Tests 3590 passed (3590)**, wall 344 s.
- **Strict capture.** Served polA3 against `assetops_polish_full_test` (serve PID 5436, Vite PID 30632 from polB3, `ASSETOPS_API_PORT=8990`), frontend `ca6f5d6bd`, `DEMOB_STRICT=1`, 10 keys × 1440/390.
  - **0 counted hits in all 20 captures.**
  - `exempt` 1 each (the time-zone note).
  - `overflow=false` everywhere.
  - Both processes stopped by PID; ports 8990 and 5490 free.
  - Output: scratchpad `pb3cap/`.
  - The copy-only commit `a5e514ecf` came after the capture. On the captured screens it changes only the Portfolio cell "Cost basis not available yet" → "No cost basis recorded yet" (no vocabulary effect).
- **Hits per owner (per width, 10 keys):** PB-3 0; Lane A 0; PA-3 0.
- **Layout evidence:** not run (`tools/layout-evidence.mjs`). The capture tool's overflow measurement at 1440 and 390 is the layout evidence.

## Builder copy outside §3.1 (old → new)

**Estate:**
- "{n} surviving VERIFIED outcomes in 30 days" → "{n} verified outcomes kept in the last 30 days"
- "Origin Finding revision not selected" → "The version of the finding it came from is not the one selected"
- Actions index "Finding {id8}" → "Source finding" (id in `title`)
- Financials exclusion raw `line_key` → "Consequence line"
- Progress rows "Action {code} · {outcome}" with the outcome words "no result yet / fix confirmed / fix did not work / result not clear / result recorded"; ids in Technical details
- "Gross scenario value unavailable" → "No what-if value worked out yet"
- "{amount} gross tariff scenario." → "{amount} at the recorded tariff, before costs (a what-if)."
- OPPORTUNITY_NOTE "A scenario needs …" → "A what-if needs reviewed physical headroom, demand and an agreed cost assumption."
- "Gross tariff scenario" → "Gross tariff estimate"
- "Coverage incomplete" also → "Some data missing" in `findingIndex` `count()`

**Cold/EV:**
- "Product exposure not established" → "Stock risk not known yet"
- "Compressor running" / "Cooling running" / "Running" → "Compressor on" / "Cooling on" / "On"
- "; no running record" → "; no record of cooling on"
- "Does not show the compressor running" → "…working"
- "From a registered test run; …" → "Generated for a test; not readings from physical equipment."
- "…is not a UTC time." → "…is not a valid time."
- `EV_WINDOW_NOT_UTC_TEXT` → "The selected window start and end must be times without a local offset."
- Cold `REC <uuid>` → "Source report"
- `SES <uuid>` → "Charging session"
- "Scenario details" → "What-if details" (technical)
- "No gross tariff scenario assessed" → "No gross tariff estimate yet"
- "Historical scenario" → "Earlier what-if"
- Missing chain steps → "No record of {step}"
- `ColdAssessmentViews:237` "Assessment <uuid>" → "Analysis view not available for this cold record"
- EV source reasons (inside Technical details) lose "run/bound/fixture"

**Work:**
- Subtitle and strip → "…calendar or hours of use" / "· due dates as set in each plan"
- "Running hours" → "Hours of use"; "Every N hours of use"; "At N hours of use"
- Notice → "These plans are not yet approved, and none is linked to an incident or a cause."
- "Due in 14 days" → "Due in the next 14 days"
- "No linked Finding or Action" → lower case
- Earlier plan version, stored action id and `siteWorkCases` "UTC and IDs" → Technical details
- `siteWorkCases` times → `formatDayTime`

**UTC tail:** "(UTC)" dropped from about 20 labels; "Times are UTC." sentences deleted; "whole UTC days" → "whole days"; Ledger "server clock, UTC" → "server clock"; "…sent and received times stay UTC." → "…are not converted."

## Known deviations

- **D1. Missing-claim guard and ruled "not available yet" wording.** The guard reserves "not available yet" for a registered `MissingClaim` gap. Following the PB-2 precedent, I reworded instead of adding an exemption or registering gaps (the guard is unchanged):
  - "Time not available yet" → "No time recorded yet" (§3.1)
  - "Cost basis not available yet" → "No cost basis recorded yet" (§3.1, Portfolio and EV)
  - "Repeat visits: not available yet (…)" → "Repeat visits could not be checked (the site summary could not be read)" (§1.2)
  - builder strings: "No what-if value worked out yet"; Preventive without a summary: "Not shown" / "This list did not include the due counts" / badge "Due status not sent with this list"

  If the Architect wants the exact ruled wording, the route is a mock_gaps registration or a reviewed exemption.
- **D2. P-10 link.** "Open incident →" uses the board href as sent (`/sites/COLD-LAB-001/work/incidents`). `coldUiHref` returns null for non-cold-API links. "Open Finding →" stays beside it.
- **D3.** Id-holding cold/EV disclosures are tagged `technical` but keep their own names (Record details, Basis details, …), to avoid several identically named "Technical details" on one page. Cold/EV uses one-level `TechnicalReferences`, not the nested `WorkedOut`, because the existing tests allow one disclosure per panel.
- **D4.** Not done:
  - "Updating/Historical · Value withheld" (the row covers only the partly-checked case);
  - "Supported findings" card label;
  - `MiniScenarios.tsx:216` "Scenarios created through" (banned word; off the capture screens);
  - the Site-local `YYYY-MM-DD` day in MiniPerformance;
  - `coldDueText` `YYYY-MM-DD` (pinned by SiteWorkActions tests);
  - the foundation `ExactReferences` in `ColdFoundationViews`.
- **D5.** Kept: `.ai/ACTIVE_CONTEXT.md` (lanes run in parallel; the coordinator owns routing, as in PB-0 to PB-2).

## Residual risk

- **Lane A server text still visible as stored** (not capture hits): `placement.py:56,60` "Supported Finding · Generated test data source"; `portfolio.py:297-299` `display_value` "Not comparable…"/"Not established" (the Assure card has a frontend override); `portfolio.py:146`; `placement.py:26`; `evidence_money.py:43`.
- **Pages without a time-zone note:** `readableTime`/`readablePeriod` now drop "UTC" on `assessmentAnalysis`, `assessmentGraphics`, `FindingDetail` and `SiteEvidence`, and those pages may have no note. `SiteEvidence.tsx:293` renders `EvidenceClaimLimit` without one.
- SiteFinding overview and History show Site-local times (for example "EAT") beside the plain "Times in UTC" note.
- `coldWorkCases` K3b long-text test failed once under load and passed on re-run (code untouched).

## User-review focus

None required. The reviewer should check D1 (wording against the guard), the builder copy list, and `wr-overview-1440.png`, `cold-board-failure-1440.png` and `maintenance-preventive-1440.png` in `pb3cap/`.
