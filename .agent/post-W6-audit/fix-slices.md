# Post-W6 D3 fix slices

Architect plan, 2026-10-24. Each card is a reviewable vertical correction on a fresh task branch from the frozen/rebased main. A D3 closes only after focused tests, independent review and current-SHA app/mock recapture. No product code was edited in classification. The owner walkthrough follows the demo sprint and story-based bootstrap context for **three** verticals: mini-grid, cold chain and EV charging.

## Sequencing and shared files

Run shell first: its CSS/tokens, Action frame crumbs and Work count copy have shared reach. After it merges, W1-a then W1-b are serial. Serialize shared `SiteAnalyticsFrames.tsx`/tab edits in this order: shell → W1-a → W1-b → W2-EV → W2-cold → W4-mini. W2-EV creates the EV tab override and EV Findings branch; W2-cold consumes the override and adds the cold Findings branch. W3-estate may run after shell independently. W5-cold-Work and W5-EV-Work develop after their W2 predecessors; W5-EV-Work applies W2-EV's common R347 tab mechanism to its depth/work mounts. Serialize their edits to `DomainActionVerification.tsx`. W6-global-Work can run alongside W2/W3/W4/W5 after shell, but rebase and refresh affected cases before merge. W4 and W5 case pages use `siteWorkCases.tsx`; if either changes that shared file, serialize those edits and recapture mini/cold/EV case screens. R373 builds separately on `task/post-W6-R373-request-access`; rebase W6 after it lands and keep B19 403/200 recapture in W6. `App.tsx` is in scope for W2-EV/W2-cold Findings client props and, by W6 ruling Q13, W6's one unknown request-section route. Rebase and recapture shared route landings after the later merge. Each card has five build units: structure/routing; selected data/copy; refusals/long content; focused tests; paired recapture/cap proof. For each card recapture every indexed case of its listed screens at both widths, plus screens reached by any shared component it actually changes; use pure selected-DTO tests and record a capture gap where a producer cannot honestly create a state. Refresh affected representative cover cases after a shared-navigation merge.

## Cards

### shell-typography-copy — Shared shell, typography and copy

**Size:** 16 D3 IDs; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R115` (B1-02), `R119` (B1-06), `R120` (B1-07), `R125` (B1-14), `R127` (B1-16), `R129` (B1-21), `R130` (B1-22), `R133` (B1-25), `R140` (B1-43), `R141` (B1-55), `R149` (B1-66), `R151` (B1-53), `R152` (B1-54), `R170` (B2-21), `R203` (B4-03), `R319` (B13-01).

**Affected screens; panels in page order:** `sites`: breadcrumb/empty prose and provenance chip; `foundation`: Configured topology → Identity and operating obligations; `readiness`: closing notice and no-version heading; `sld`: diagram → unknown-part notice; `changes`: Change and effect → page-end notice, plus header crumb; `asset`: refusal prose; `evidence-analysis`: Accepted records behind the conclusions time column; `action-overview`, `action-plan`, `action-execution`, `action-evidence`, `action-history`: Action breadcrumb; `sitework-incidents`, `sitework-maintenance`, `cold-work-incidents`, `cold-work-maintenance`, `ev-work-incidents`, `ev-work-maintenance`: count strip. Other panels on those pages are regression-only.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** one case for each of 87 baseline screens, then every indexed case of the 18 affected screens: short refusal, singleton/zero/plural count, plan available/pending/failed, no-version, and Addis/UTC evidence time.

**Files:** `frontend/src/ui/primitives.css`, `ui/tokens.css`, `ui/Badge.tsx`, `ui/V69Layout.tsx`; `shell/SitesFrame.tsx`, `shell/SiteFoundationFrame.tsx`, `shell/SiteAnalyticsFrames.tsx`, `shell/SiteHealthFrames.tsx`, `shell/SiteEvidenceFrame.tsx`; `sites/SitesIndex.tsx`, `sites/StoredFoundationViews.tsx`, `sites/FoundationRevisionPanel.tsx`, `sites/SiteSingleLineDiagram.tsx`, `sites/SiteFoundationChange.tsx`, `sites/SiteBattery.tsx`, `sites/LedgerSiteEvidence.tsx`, `sites/siteWorkCases.tsx`; read `sites/verificationClient.ts` for the frozen plan. All paths after the first are under `frontend/src/`. Edit only where the ruling needs it.

**Tests:** `sites/__tests__/siteWorkCases.test.tsx`, `coldWorkCases.test.tsx`, `evWorkCases.test.tsx`, `siteAction.test.tsx`, `foundationScreen.test.tsx`; `shell/__tests__/v01bEvidenceVisual.test.tsx`, `siteFoundationRevision.test.tsx`; existing shell/SLD and shared vocabulary tests. Add plan loaded/pending/error, Site-timezone/UTC, no-version name, Action crumb, count grammar and CSS-row assertions.

**Paired recaptures:** 174 representative pairs across the 87 baseline screens plus all 230 indexed pairs of the 18 screens above (overlap allowed), from the frozen index's 21-producer cover. Record current SHA, panel order, time basis, overflow and closed heights; capture open UTC/technical disclosures as explicit viewer states.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W1-mini-Action-a — W1 mini Site, Finding, Action and verification

**Size:** 18 D3 IDs; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R156` (B2-07), `R157` (B2-08), `R159` (B2-10), `R164` (B2-15), `R171` (B2-22), `R178` (B2-29), `R184` (B3-01), `R185` (B3-02), `R186` (B3-03), `R187` (B3-04), `R188` (B3-05), `R189` (B3-06), `R190` (B3-07), `R191` (B3-08), `R192` (B3-09), `R193` (B3-10), `R195` (B3-12), `R196` (B3-13).

**Affected screens; panels in page order:** `mini`: breadcrumb → objective cards → Operating context and SLD link → failed-day rows; `evidence-analysis`: Accepted records behind the conclusions → How each limit is set; `dispatch`: selected-block refusal; `finding`: section tabs → header/strip → What happened → What limits this conclusion → What to do next → Where to look next; `finding-evidence`: section tabs/header → Evidence bundle; `finding-history`: section tabs/header → Revision history; `sitefindings`: lens chips → scope strip → Findings at this site. Adjacent panels are regression-only.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B1–B5 representative, priced, held, failed, unknown, selected and refused at both widths.

**Files:** `frontend/src/sites/SiteOverview.tsx`, `LedgerSiteEvidence.tsx`, `EvidenceClaimLimit.tsx`, `PerformanceDispatch.tsx`, `SiteFinding.tsx`, `SiteFindingEvidence.tsx`, `SiteFindingHistory.tsx`, `SiteFindingIndex.tsx`; `shell/SiteAnalyticsFrames.tsx` for existing route links. No Action or App edit in this card.

**Tests:** `sites/__tests__/siteFinding.test.tsx`, `siteFindingEvidence.test.tsx`, `siteFindingHistory.test.tsx`, `evidenceClaimLimit.test.tsx`, Overview/Dispatch tests and `shell/__tests__/s404SiteFindingIndex.test.tsx`; add failed-day key and wrong-revision refusal cases.

**Paired recaptures:** all 88 indexed pairs for `mini`, `evidence-analysis`, `dispatch`, `finding`, `finding-evidence`, `finding-history`, `sitefindings`; both widths, including failed, selected, unknown and refused. Record the current SHA and cap proof.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W1-mini-Action-b — W1 mini Site, Finding, Action and verification

**Size:** 18 D3 IDs; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R197` (B3-14), `R198` (B3-15), `R199` (B3-16), `R200` (B3-17), `R201` (B3-18), `R202` (B4-01), `R204` (B4-04), `R205` (B4-05), `R209` (B4-10), `R218` (B4-19), `R219` (B4-20), `R220` (B4-21), `R221` (B4-22), `R222` (B4-24), `R223` (B5-01), `R228` (B5-07), `R229` (B5-08), `R230` (B5-09).

**Affected screens; panels in page order:** `sitefindings`: Findings at this site table; `financials`: KPI/bridge → Assumptions in use → Trade-offs and exclusions; `assumptions`: Financial assumptions → Interpretation history; `recommendation`: Proposed intervention → Declare success before evaluating → Evidence needed to verify; `action-overview`: Action scope/refusal; `action-plan`: Success criteria; `action-execution`: Activity log; `action-evidence`: Evidence requirements; `action-history`: Action history; `verification`: Target and guardrails evaluated together → Activity evidence → Outcome evidence; `sitework`: Actions at this site. B4 “all six” includes Recommendation and five Action views; no unrelated panel is in scope.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B1–B5 representative, priced, held, failed, unknown, selected and refused at both widths.

**Files:** `frontend/src/sites/SiteFindingIndex.tsx`, `SiteFinancials.tsx`, `SiteAction.tsx`, `actionPresentation.tsx`, `SiteActionVerification.tsx`, `SiteWorkActions.tsx`; `shell/SiteAnalyticsFrames.tsx` for mounted route/section behavior. No Finding Evidence/History, mini depth client or App edit.

**Tests:** `sites/__tests__/siteAction.test.tsx`, `siteActionVerification.test.tsx`, `siteWorkActions.test.tsx`, Financials/assumption and Finding index tests; add unknown Action section, long history page, verification and work-link cases.

**Paired recaptures:** all 118 indexed pairs for `sitefindings`, `financials`, `assumptions`, `recommendation`, five `action-*`, `verification`, `sitework`; both widths, including unknown section, verified replay, historical and long-row states. Record current SHA and closed-height caps.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W2-cold — Cold Site and Findings routing

**Size:** 14 D3 IDs; five build units. **Severity:** High.

**Exact D3 IDs:** `R241` (B6-10), `R242` (B6-11), `R244` (B6-13), `R245` (B6-14), `R246` (B6-15), `R247` (B6-17), `R249` (B6-20), `R253` (B7-01), `R254` (B7-03), `R255` (B7-04), `R256` (B7-05), `R258` (B7-07), `R259` (B7-08), `R261` (B7-11).

**Affected screens; panels in page order:** `temperature`: Temperature with operating context → Excursion context → Claim boundary; `coldbackup`: What the chain shows → Reconstructed event chain → Backup event chains → Evidence by causal step; `cold-finding`: Bounded conclusion → Operational context → Recommended next step; `cold-findings`: Findings at this site; `cold`: event narrative/cards → Chamber temperature → Next step; `cold-evidence`: What we can conclude now → Most useful next evidence; `cold-evidence-analysis`: Accepted records behind the conclusions; `cold-financials`, `cold-assumptions`: Site tab/window state and respective selected panel. Other panels are regression-only.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B6–B7 plus cold-finding-excursion representative and false Findings reason; both widths.

**Files:** `frontend/src/sites/ColdAssessmentViews.tsx`, `coldSiteViews.tsx`, `SiteFindingIndex.tsx`; `shell/coldSiteRoutes.tsx`, `shell/SiteAnalyticsFrames.tsx` for the cold Findings branch, and `App.tsx` for its cold client prop. Consume W2-EV's `operatorSiteTabs.tsx` override for cold main tabs (B14-10). Read `ColdDepthClient.ts` to preserve selected-row semantics. Keep App routes unchanged.

**Tests:** `sites/__tests__/coldSiteViews.test.tsx`, `coldDepth.test.tsx`, `coldRoutes.test.tsx`; `shell/__tests__/s404SiteFindingIndex.test.tsx`; add event-chain order, Finding destination, selected-window and refusal assertions.

**Paired recaptures:** all 92 indexed pairs for the nine screens above, plus the absent-from-index `cold-finding-excursion` representative at 1440/390 and its false Findings reason. Include selected/refused/historical; record current SHA and cap proof.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W2-EV — EV Site, tabs and depth links

**Size:** 14 D3 IDs including R347; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R265` (B8-06), `R267` (B8-08), `R268` (B8-12), `R270` (B8-14), `R271` (B8-15), `R275` (B8-19), `R276` (B8-20), `R280` (B8-24), `R281` (B8-27), `R283` (B9-03), `R284` (B9-05), `R285` (B9-08), `R286` (B9-09), `R347` (B16-16 common EV tab mechanism). Also owns the EV branch of merged R253/B9-10 and EV copies of R254/R258/R259.

**Affected screens; panels in page order:** `ev-readiness`: Readiness and commissioning evidence → Gateway status; `sessions`: Session service records → How to read the denominator → Cause remains bounded; `ev-finding`: Bounded conclusion → Operational context → Recommended next step; `ev`: event/charging cards → Next step; `ev-evidence`, `ev-evidence-analysis`, `ev-financials`, `ev-assumptions`: Site tab/window state and the selected evidence/money panel. Connected sources and other adjacent panels are regression-only.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B8–B9, EV main-tab destinations, refused and missing-meter; both widths.

**Files:** `frontend/src/sites/EvFoundationViews.tsx`, `EvAssessmentViews.tsx`, `EvSiteViews.tsx`; `shell/evSiteRoutes.tsx`, `shell/SiteAnalyticsFrames.tsx` (EV mounts, EV Findings branch and shared unavailable copy), `shell/SiteFoundationFrame.tsx` (EV readiness links/tabs), `shell/operatorSiteTabs.tsx` (shared override), `shell/SiteDetailFrame.tsx` (bare EV home) and `App.tsx` (EV Findings client prop). Read `evDepthClient.ts` to preserve selected-row semantics. App route declarations stay unchanged.

**Tests:** `sites/__tests__/evFoundation.test.tsx`, `evAssessmentRoutes.test.tsx`, `evDepth.test.tsx`, `evSiteMoneyRoutes.test.tsx`; add session denominator, Finding link, tab-window and missing-meter assertions.

**Paired recaptures:** all 92 indexed pairs for the eight screens above, plus every indexed `ev-findings` case as an owned B9-10/R253 fix; refresh EV Foundation/SLD, Availability/Energy/Scenarios and mini/cold Finding child representative pairs reached by shared navigation. Include interrupted, refused and missing-meter at both widths. Record current SHA and cap proof.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W3-estate — Estate indices, evidence, money and Portfolio

**Size:** 9 D3 IDs; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R293` (B10-07), `R294` (B10-08), `R295` (B10-09), `R296` (B11-01), `R297` (B11-02), `R300` (B11-05), `R302` (B11-07), `R307` (B11-12), `R308` (B11-13).

**Affected screens; panels in page order:** `actions`: Managed actions title/criterion; `findings`: Findings across the estate rows/390 title; `findings-cost`, `findings-risks`, `findings-opportunities`: selected pending/partial lens rows; `globalevidence`: Capability coverage across sites → Recurring evidence gaps; `globalfinancials`: Consequence register → Aggregation rule; `portfolio`: Where management should act first → Objectives across the estate → scope disclosure and Site/Finding links. Other panels are regression-only.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B10–B11 clean, partial, pending, historical, page two and long-row; both widths.

**Files:** `frontend/src/estate/actionIndex.tsx`, `findingIndex.tsx`, `EstateEvidence.tsx`, `EstateFinancials.tsx`, `EstatePortfolio.tsx`; their existing estate styles if wrap/scroll is required. Demonstrated href/limit DTO omissions allow scoped backend estate edits in `evidence_money.py`, `portfolio.py`, `financials.py`, `index.py` and their tests; no schema change. W3 also fixes expired inert cold/EV Finding titles in the four estate Findings lenses under R297 destination proof.

**Tests:** `estate/__tests__/estateRoots.test.tsx`, `estateEvidence.test.tsx`, `estatePortfolio.test.tsx`, `estatePortfolioRoutes.test.tsx`; add pending/partial row, 390 unclamped title, real link and bounded scope-disclosure cases.

**Paired recaptures:** all 128 indexed pairs for `actions`, four Findings lenses, `globalevidence`, `globalfinancials`, `portfolio`; both widths, including pending, partial, page two, long text and refused. Add the KOBO-001 W1 landing proof for corrected links. Record current SHA/caps.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W4-mini — Mini depth, decisions and cases

**Size:** 15 D3 IDs; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R309` (B12-02), `R310` (B12-03), `R311` (B12-04), `R312` (B12-05), `R313` (B12-06), `R316` (B12-09), `R318` (B12-11), `R320` (B13-02), `R321` (B13-03), `R322` (B13-04), `R324` (B13-06), `R325` (B13-07), `R328` (B13-11), `R331` (B13-15), `R333` (B13-18).

**Affected screens; panels in page order:** `renewable`: tone/decision cards → From physical headroom to an opportunity → Productive-use evaluation → Eligible and excluded windows; `service`: tone/decision cards → Where the power went → Delivered power by addressed load → What is supported; `fuel`: tone/decision cards → Fuel balance at a glance → Balance bridge; `backup`: tone/decision cards → Backup event chains → Backup readiness evidence; `sitework-incidents`, `sitework-maintenance`: list/refusal strip → cases and unclamped text; `opportunity-finding`: Bounded opportunity → Next decision → Consequence basis; `scenarios`: Financial scenarios; `alternatives`: Alternatives to investigate and route/header. Adjacent panels are regression-only.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B12–B13 stocked, zero, DB-time 409, refused, page two and long-row; both widths.

**Files:** `frontend/src/sites/MiniPerformance.tsx`, `MiniOpportunity.tsx`, `MiniScenarios.tsx`, `MiniAlternatives.tsx`, `SiteWorkIncidents.tsx`, `SiteWorkMaintenance.tsx`, `siteWorkCases.tsx`; `shell/SiteAnalyticsFrames.tsx` for the mounted mini destination/header. Read `miniDepthClient.ts` for selected-state semantics.

**Tests:** `sites/__tests__/siteWorkCases.test.tsx`, `miniRenewableRoutes.test.tsx`, `miniServiceRoutes.test.tsx`, `miniFuelRoutes.test.tsx`, `miniBackupRoutes.test.tsx`; existing mini decision/scenario and opportunity Finding tests. Add long narrative, zero, bad-window and tab visibility cases.

**Paired recaptures:** all 96 indexed pairs for `renewable`, `service`, `fuel`, `backup`, `sitework-incidents`, `sitework-maintenance`, `opportunity-finding`, `scenarios`, `alternatives`; both widths, including zero, DB-time 409, refused and long text. If `siteWorkCases.tsx` changes, add cold/EV case-page regression pairs. Record SHA/caps.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W5-cold-Work — Cold depth and Work

**Size:** 6 D3 IDs; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R334` (B14-03), `R336` (B14-07), `R337` (B14-08), `R338` (B14-09), `R339` (B14-10), `R344` (B15-10).

**Affected screens; panels in page order:** `cold-work`: Actions at this site count/empty state and default window; `cooling`: selected/pending notice → Recovery curves → Context normalization; `cold-health`: selected/pending notice → Condition and evidence; `cold-scenarios`: Financial scenarios placeholder/notice; `cold-action`: Declared outcome criteria → Related activity linked-request copy. Window preservation applies across these five screens; other panels are regression-only.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B14–B15 positive, pending, unknown, zero, refused, forbidden and worst case; both widths.

**Files:** `frontend/src/sites/coldSiteViews.tsx`, `ColdCooling.tsx`, `ColdHealthDepth.tsx`, `ColdScenarios.tsx`, `SiteWorkActions.tsx`, `DomainActionVerification.tsx`; `shell/coldSiteRoutes.tsx` for URL window preservation. Read `domainActionClient.ts` for linked-state semantics.

**Tests:** `sites/__tests__/coldDepth.test.tsx`, `coldHealthDepth.test.tsx`, `coldScenarios.test.tsx`, `coldWorkActions.test.tsx`, `domainActionVerification.test.tsx`; add current-day default, invalid window, zero Action, and exact linked VERIFICATION_WINDOW/CANCELLED copy.

**Paired recaptures:** all 116 indexed pairs for `cold-work`, `cooling`, `cold-health`, `cold-scenarios`, `cold-action`; both widths, including pending, unknown, zero, refused and forbidden. A linked VERIFICATION_WINDOW/CANCELLED capture remains a declared producer gap until the story bootstrap exists; use selected-DTO tests now. Record SHA/caps.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W5-EV-Work — EV depth and Work

**Size:** 5 D3 IDs plus R347 application/recapture; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R345` (B16-06), `R346` (B16-07), `R348` (B17-04), `R349` (B17-06), `R350` (B17-08). R347's common tab mechanism moves to W2-EV; this card applies it to its depth/work mounts and retains B16-16 recapture.

**Affected screens; panels in page order:** `availability`: schedule count/units → Connector states over the service schedule → Full-schedule availability bound; `energy`: selected bridge row → Import power and configured limit → What can be concluded; `ev-health`: Condition and evidence window state; `ev-scenarios`: Financial scenarios window state; `ev-work`: Actions at this site window state; `ev-action`: Declared verification plan → non-loaded/invalid-window refusal. R350 also checks the existing Action `/overview` link destination; it does not authorize rewriting W1 Action chrome.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B16–B17 positive, unknown, pending, stale, refused, forbidden and worst case; both widths.

**Files:** `frontend/src/sites/EvAvailability.tsx`, `EvEnergy.tsx`, `EvHealthDepth.tsx`, `EvScenarios.tsx`, `EvSiteViews.tsx`, `DomainActionVerification.tsx`; `shell/evSiteRoutes.tsx` for window/link propagation. Read `evDepthClient.ts` and `domainActionClient.ts` for DTO semantics. Backend `test_w504_ev_intent_api.py` is a test, not a production edit file.

**Tests:** `sites/__tests__/evDepth.test.tsx`, `evEnergy.test.tsx`, `evHealthDepth.test.tsx`, `evScenarios.test.tsx`, `evWorkActions.test.tsx`, `domainActionVerification.test.tsx`; `backend/tests/test_w504_ev_intent_api.py` for existing intent contract. Add invalid-window, non-loaded, unit and bridge-value cases.

**Paired recaptures:** all 124 indexed pairs for `availability`, `energy`, `ev-health`, `ev-scenarios`, `ev-work`, `ev-action`; both widths, plus the indexed R350 link-check landing. Include unknown, pending, stale, refused and forbidden; mark unproducible selected states as gaps with DTO tests. Record SHA/caps.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W6-global-Work — Global lists and exact request

**Size:** 15 D3 IDs here; R373 is a separate task. Five build units. **Severity:** High.

**Exact D3 IDs:** `R352` (B18-03), `R353` (B18-04), `R354` (B18-05), `R356` (B18-07), `R357` (B18-08), `R359` (B18-10), `R360` (B18-11), `R361` (B18-13), `R364` (B19-03), `R366` (B19-05), `R367` (B19-07), `R368` (B19-08), `R370` (B19-10), `R371` (B19-12), `R372` (B19-13). R373/B19-15 builds on `task/post-W6-R373-request-access`; this card retains its recapture gate.

**Affected screens; panels in page order:** `incidents`: crumb/window and paging → Incident cases links/rows; `maintenance`: window/paging → Corrective work requests; `maintenance-preventive`: window state → Preventive plan; `oprecords`: window/paging/refusal → Operational records; `wr-overview`: request tabs → Work done → Lifecycle; `wr-record`: request tabs → Maintenance record · activity; `wr-history`: request tabs → History. R371 also covers unknown-section `link-check` refusal. R373's granted/forbidden state is recapture-only here.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B18–B19 mini, cold, EV, 403, 404, 503, page two, historical, all-open and 160-char rows; both widths. The W6 default window includes today as `[today−6d, tomorrow)` UTC; W5-cold-Work owns Site Work's R338 counterpart. W5-EV-Work owns the EV Site Work positive case-detail 503 from the R373 packet.

**Files:** `frontend/src/work/GlobalIncidents.tsx`, `GlobalMaintenance.tsx`, `GlobalPreventive.tsx`, `OperationalRecords.tsx`, `globalWorkParts.tsx`, `globalWorkClient.ts`, `globalWork.css`, `workRequestShared.tsx`, `WorkRequestOverview.tsx`, `WorkRequestRecord.tsx`, `WorkRequestHistory.tsx`; `frontend/src/App.tsx` only for R371; `tools/navigation-truthfulness.ps1` and the route registry/guard test for R371. Authorized additive backend files: `backend/assetops_backend/work/{global_index,global_detail,operational_index}.py` and `work/adapters/postgres_global_read.py`; reuse `estate/evidence_money.py:site_home_href` without editing the estate helper. No `work/site_index.py`, schema, cursor format/order or page-membership change; newly displayed linked IDs or Action codes must enter the selected basis and digest. R373 owns backend `main.py`/`global_work_api.py`.

**Tests:** `work/__tests__/globalIncidents.test.tsx`, `globalMaintenance.test.tsx`, `globalPreventive.test.tsx`, `operationalRecords.test.tsx`, `globalWorkClient.test.ts`, `workRequestOverview.test.tsx`, `workRequestRecord.test.tsx`, `workRequestHistory.test.tsx`, plus App route/guard tests. Add three-domain Finding and Site links, linked WR hrefs, page-two caption, 390 overflow, historical seconds, unknown section and refused request cases; reuse R373's independent access tests. Run focused `backend/tests/test_w601{a,b,c,e}_*.py` and R373 tests, then one real-Postgres full backend suite at final SHA with keep-awake, a 2x cap and JUnit zero-skip proof.

**Paired recaptures:** all 380 indexed pairs for `incidents`, `maintenance`, `maintenance-preventive`, `oprecords`, `wr-overview`, `wr-record`, `wr-history`; include the 16 B18 and 10 B19 link landings, EV Site, linked WR, current/historical Incident and four R371 unknown-section landings, mini/cold/EV 403/200 after R373, 404/503, page two, historical, all-open and 160-character rows at both widths. Use W6 seed, W502/W504 walkthroughs with a fresh inherited `ASSETOPS_WORK_CURSOR_KEY_HEX`, and the reviewed mini 403 producer. Declare VERIFICATION_WINDOW, cold/EV preventive and operational rows, all-three-domain list, pending/stale global states and unproducible five-long-row states as gaps with selected-DTO tests or a capture-only DOM probe. Record current SHA, producer and cap proof.

**Caps:** apply the measured docket below and W6 ruling Q15 for missing panel/viewport rows: explicit W6-01 caps for Preventive plan (600/690), Operational records table (650/780) and 390 WR History (690); all other missing rows use the final-SHA five-row/160-character closed peak ×1.15 rounded up to 50 px, with numeric Architect ratification before merge. User-expanded all-disclosures-open is exempt from closed-height caps but must have zero clipping. An inner scroll is permitted only with every row reachable. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge. Reserve W6 register IDs from R396 (R396 is the Verification-tab D1); W1-b owns R383–R385 and W1-a R386–R395.

## Explicit Architect rulings

**B19-15 access:** High D3, production-reachable. `main.py` composes global request detail with `development_access`, which returns allow while Site Work can return 403 for the same principal. Gate detail with the same Site admission seam as Site Work; test a forbidden principal against both routes, including the linked request from all three verticals. Never expose the existence of a request across a denied Site. This is in W6 global Work.

**Capture-only click:** a client-only, non-mutating pager or disclosure click is allowed. It may change only viewer state; record the click and resulting case in the pair metadata. A click that sends a mutation, fabricates data, or bypasses a refusal remains outside capture-only. This permits B19 History Next and B11 Load more consistently.

**Live manual-reading form (B18-14):** mock-only Site options and values in an inert live form are false facts. Replace them with selected Sites or empty placeholders, keep submission visibly unavailable under R12, and show the D4 label next to the form until corrected.

**Inventory and spec:** `cold-finding-excursion` is mounted and produced by W2-03, so the target is 88 implemented IDs / 22 outside; its own two-width representative pair is required. B2-31 uses `/performance/dispatch?view=analysis`, not the spec path. B7 cold Findings must use cold Finding wiring. B12-13 mini depth uses W4-02, not `tools/s402*`. B14-15 cold depth producer is W5-01 and W502 only supplies Work. B18 W6 roots use `w601_seed.py` fixtures. The B7/B9/B11/B16/B18 EV and cold Site destination errors are product D3s, not spec excuses.

**Default window:** a seven-day default includes the current UTC day, with an exclusive end at next UTC midnight; state membership by each list’s documented event time. A read ending today 00:00Z excludes all events today and makes empty Work copy misleading (B14-09/B15-06/B16-04/B17-14/B18-12). Preserve explicit historical windows.

**Time basis:** Site-scoped reads and links show the Site timezone as primary, with UTC available in a disclosure; exact stored instants and URL parameters stay UTC. Estate roots may use UTC because they combine Sites, but say `UTC` in the header and show each Site-local time where a row is opened. R19 seconds precision stays; W6 historical date bar also shows seconds.

**Unregistered rulings:** B10-01 W3 estate departures, B12-01 W4 depth departures, B18-09 W6 cards, and the W1-F5b overage cases have canonical register rows in `mock-departure-register.md`. Existing Rxx claims are verified only where the classification says so; R40 is expired for built depth destinations but does not claim a cold or EV Recommendation exists.

**Carried Architect closeout:** K4 linked request copy: `VERIFICATION_WINDOW` with a performed record says “Work was recorded; verification is open and no outcome is established.” `CANCELLED` says “The linked request was cancelled; no completed work or verified outcome is established.” Use those only for exact linked states, with tests; this is W5 cold/EV Work. The registry-chain owner is W6 global Work (`A-cold-work-projections ← A-maintenance-index ← A-work-cases`, and the EV equivalent), with exact producer and consumer contracts in the review packet. W5-04c A1–A3: ratify the V4a test edit, retain strict EV result parsing until evaluator contracts widen, prove 409/missing-intent/in-panel 503 with component tests and explicit capture limit, read or remove `windowQuery`, and widen the no-write assertion to all five omitted tables and current-status equality. W5 EV Work owns these.

## Producer gap decisions

| Gap | Decision | Reason / immediate proof |
| --- | --- | --- |
| Cold/EV authored scenarios (B14-16/B16-09) | Later three-vertical story bootstrap | D3 copy and layout use pure selected DTO tests now. Do not create throwaway authored-scenario modes. Recapture populated state after owner supplies bootstrap context. |
| EV depth unknown/pending/stale (B16-10/B17-16) | Later story bootstrap | Existing focused DTO tests cover state rendering; producer cannot honestly yield these today. |
| Linked VERIFICATION_WINDOW/CANCELLED request (B15-10/B17-12) | Later story bootstrap for real capture; fix copy now | Exact linked-state pure tests verify the D3/copy rule; no throwaway lifecycle mode. `VERIFICATION_WINDOW` remains unavailable until writer exists. |
| Populated estate lenses (B10) | Later story bootstrap | Missing accepted lens predicates and selected cross-site examples; empty states stay honest now. |
| Populated Alternatives (B13-10) | Later story bootstrap | Current W4 producer yields DB-time 409; pure selected-row test proves layout now. |
| KOBO-001 W1 producer for mini landings (B11-03) | Needed now in W3 fix | Reuse the reviewed W1-F5b producer/mode, pin window and exact row target, then capture landing. |
| Stale ignored `var/sites` YAML (B18-18) | Later bootstrap cleanup | It is not a W6 API input or D3 verification source; do not use it for the demo. |
| `ASSETOPS_WORK_CURSOR_KEY_HEX` walkthrough env (B18-18) | Needed now in W6 fix | Set in existing W6 serve/recapture mode; without it the global list returns 503 and paging cannot be verified. |

## Closed-height cap docket

Caps below are per named panel and viewport. They use the largest captured closed state and a five-row, 160-character worst-case fixture wherever rows can lengthen. The mini records and Foundation Identity caps below are explicit shell pre-flight rulings, not mock one-row estimates. A cap is a readability/scroll budget, never permission to hide a row. Before building, use the selected worst-case producer or a pure render fixture of five 160-character rows. The all-disclosures-open viewer state is expressly exempt from these closed-height caps; no clipping is allowed. If a remeasure exceeds a cap, change wrapping, paging or inner scroll and recapture, or ask the Architect to revise the measured cap before merge.

| Screen | Panel | Width | Peak observed closed px | Cap px |
| --- | --- | ---: | ---: | ---: |
| `action-evidence` | Evidence requirements | 1440 | 373 | 450 |
| `action-evidence` | Evidence requirements | 390 | 615 | 800 |
| `action-execution` | Activity log | 1440 | 364 | 450 |
| `action-execution` | Activity log | 390 | 676 | 800 |
| `action-history` | Action history | 1440 | 362 | 450 |
| `action-history` | Action history | 390 | 589 | 800 |
| `action-overview` | Action scope | 1440 | 384 | 450 |
| `action-overview` | Action scope | 390 | 644 | 750 |
| `action-plan` | Success criteria | 1440 | 392 | 450 |
| `action-plan` | Success criteria | 390 | 573 | 800 |
| `asset` | Interpretation and next evidence | 390 | 415 | 500 |
| `assumptions` | Financial assumptions | 1440 | 567 | 650 |
| `assumptions` | Financial assumptions | 390 | 923 | 1050 |
| `assumptions` | Interpretation history | 1440 | 1823 | 800 |
| `assumptions` | Interpretation history | 390 | 4572 | 1400 |
| `changes` | Change and effect | 390 | 552 | 800 |
| `cold` | Bounded money consequence | 390 | 288 | 350 |
| `cold-action` | Related activity | 390 | 278 | 350 |
| `cold-evidence` | What we can conclude now | 390 | 615 | 800 |
| `cold-evidence-analysis` | Accepted records behind the conclusions | 1440 | 391 | 450 |
| `cold-evidence-analysis` | Accepted records behind the conclusions | 390 | 485 | 800 |
| `cold-financials` | Not included | 390 | 266 | 300 |
| `cold-finding` | Bounded conclusion | 390 | 353 | 400 |
| `cold-findings` | Findings at this site | 1440 | not captured: five long rows | 550 |
| `cold-findings` | Findings at this site | 390 | 441 (zero-row gap) | 850 |
| `cold-foundation` | Operating interpretation | 390 | 399 | 450 |
| `cold-health` | Condition and evidence | 1440 | 285 | 400 |
| `cold-readiness` | Readiness and commissioning evidence | 1440 | 672 | 800 |
| `cold-readiness` | Readiness and commissioning evidence | 390 | 654 | 800 |
| `cold-sld` | Cold replay lab | 390 | 528 | 600 |
| `cold-sld` | What each part does | 1440 | 514 | 600 |
| `cold-work` | Actions at this site | 1440 | 457 | 550 |
| `cold-work` | Actions at this site | 390 | 457 | 800 |
| `cold-work-incidents` | Incidents at this site | 1440 | 486 | 550 |
| `cold-work-incidents` | Incidents at this site | 390 | 599 | 800 |
| `cold-work-maintenance` | Maintenance at this site | 1440 | 486 | 550 |
| `cold-work-maintenance` | Maintenance at this site | 390 | 430 | 800 |
| `coldbackup` | Evidence by causal step | 1440 | 581 | 700 |
| `coldbackup` | Evidence by causal step | 390 | 915 | 1050 |
| `cooling` | Recovery curves | 390 | 412 | 800 |
| `dispatch` | Accepted sample coverage | 1440 | 345 | 400 |
| `dispatch` | Selected block · 04:00–04:15 UTC | 390 | 640 | 750 |
| `dispatch` | Sources and 15-minute blocks | 390 | 870 | 1000 |
| `ev-evidence-analysis` | Accepted records behind the conclusions | 1440 | 399 (short rows) | 700 |
| `ev-evidence-analysis` | Accepted records behind the conclusions | 390 | not captured: five long rows | 1000 |
| `ev-finding` | Bounded conclusion | 1440 | not captured with link | 600 |
| `ev-finding` | Bounded conclusion | 390 | not captured with link | 850 |
| `ev-findings` | Findings at this site | 1440 | not captured: five long rows | 550 |
| `ev-findings` | Findings at this site | 390 | 430 (gap) | 850 |
| `sessions` | Session service records table | 1440 | not captured: five long rows | 900 |
| `sessions` | Session service records table | 390 | not captured: five long rows | 1400 |
| `findings`, `findings-cost`, `findings-risks`, `findings-opportunities` | Findings across the estate / lens panel | 1440 | not captured: five long rows | 1000 |
| `findings`, `findings-cost`, `findings-risks`, `findings-opportunities` | Findings across the estate / lens panel | 390 | not captured: five long rows | 1500 |
| `actions` | Managed actions | 1440 | not captured: five long rows | 750 |
| `actions` | Managed actions | 390 | not captured: five long rows | 1100 |
| `globalfinancials` | Consequence register | 1440 | not captured: five long rows | 800 |
| `globalfinancials` | Consequence register | 390 | not captured: five long rows | 1200 |
| `portfolio` | Objectives across the estate | 1440 | not captured: five long rows | 600 |
| `portfolio` | Objectives across the estate | 390 | not captured: five long rows | 800 |
| `ev-foundation` | Operating interpretation | 390 | 348 | 400 |
| `ev-foundation` | Physical site | 390 | 360 | 450 |
| `ev-health` | Condition and evidence | 1440 | 324 | 400 |
| `ev-health` | Condition and evidence | 390 | 455 | 800 |
| `ev-readiness` | Gateway status · edge-ev-lab-001 | 390 | 1669 | 1900 |
| `ev-work` | Actions at this site | 1440 | 480 | 550 |
| `ev-work` | Actions at this site | 390 | 480 | 800 |
| `ev-work-incidents` | Incidents at this site | 1440 | 502 | 600 |
| `ev-work-incidents` | Incidents at this site | 390 | 445 | 800 |
| `ev-work-maintenance` | Maintenance at this site | 1440 | 502 | 600 |
| `ev-work-maintenance` | Maintenance at this site | 390 | 445 | 800 |
| `evidence` | Data sources · data quality, not equipment condition | 390 | 774 | 900 |
| `evidence-analysis` | Accepted records behind the conclusions | 1440 | 910 | 1200 |
| `evidence-analysis` | Accepted records behind the conclusions | 390 | 1235 | 1800 |
| `evidence-analysis` | How each limit is set | 1440 | 311 | 400 |
| `evidence-analysis` | How each limit is set | 390 | 542 | 800 |
| `financials` | Trade-offs and exclusions | 390 | 387 | 450 |
| `financials` | What happened → what it means in money | 1440 | 609 | 700 |
| `financials` | What happened → what it means in money | 390 | 1152 | 1300 |
| `finding` | What happened | 390 | 534 | 600 |
| `finding` | What limits this conclusion | 1440 | 318 | 400 |
| `finding` | What limits this conclusion | 390 | 467 | 550 |
| `finding` | Where to look next | 390 | 628 | 750 |
| `finding-evidence` | Evidence bundle · Generator support merits review | 1440 | 411 | 500 |
| `finding-evidence` | Evidence bundle · Generator support merits review | 390 | 728 | 850 |
| `finding-evidence` | Inspect source lineage | 390 | 218 | 250 |
| `finding-history` | Revision history | 1440 | 635 | 750 |
| `finding-history` | Revision history | 390 | 1329 | 1500 |
| `foundation` | Configured topology | 1440 | 595 | 700 |
| `foundation` | Identity and operating obligations | 1440 | 595 | 850 |
| `foundation` | Identity and operating obligations | 390 | 678 | 1050 |
| `foundation` | Time-valid control configuration | 1440 | 759 | 900 |
| `foundation` | Time-valid control configuration | 390 | 1152 | 1300 |
| `health` | Data sources · data quality, not equipment condition | 1440 | 766 | 900 |
| `health` | Data sources · data quality, not equipment condition | 390 | 867 | 1000 |
| `incidents` | Incident cases | 1440 | 599 | 700 |
| `incidents` | Incident cases | 390 | 690 | 800 |
| `maintenance` | Corrective work requests | 1440 | 609 | 700 |
| `maintenance` | Corrective work requests | 390 | 690 | 800 |
| `mini` | Bounded money consequence | 390 | 334 | 400 |
| `mini` | Needs attention | 1440 | 595 | 700 |
| `mini` | Operating context | 1440 | 595 | 700 |
| `mini` | Operating context | 390 | 792 | 900 |
| `mini` | What happened in the selected hour | 1440 | 333 | 400 |
| `readiness` | Gateway status · edge-kobo-001 | 1440 | 822 | 950 |
| `readiness` | Gateway status · edge-kobo-001 | 390 | 1919 | 2150 |
| `readiness` | Readiness and commissioning evidence | 1440 | 592 | 700 |
| `readiness` | Readiness and commissioning evidence | 390 | 1009 | 1150 |
| `recommendation` | Declare success before evaluating | 1440 | 513 | 600 |
| `recommendation` | Evidence needed to verify | 390 | 352 | 400 |
| `recommendation` | Proposed intervention | 1440 | 513 | 600 |
| `recommendation` | Proposed intervention | 390 | 710 | 800 |
| `sitefindings` | Findings at this site | 1440 | 507 | 600 |
| `sitefindings` | Findings at this site | 390 | 763 | 900 |
| `sitework` | Actions at this site | 1440 | 319 | 400 |
| `sitework` | Actions at this site | 390 | 598 | 800 |
| `sitework-incidents` | Incidents at this site | 1440 | 443 | 500 |
| `sld` | Kobo mini-grid | 1440 | 1097 | 1250 |
| `sld` | Kobo mini-grid | 390 | 1435 | 1650 |
| `sld` | What each part does | 1440 | 640 | 750 |
| `sld` | What each part does | 390 | 940 | 1100 |
| `verification` | Activity evidence | 1440 | 361 | 450 |
| `verification` | Activity evidence | 390 | 347 | 400 |
| `verification` | Outcome evidence | 1440 | 361 | 450 |
| `verification` | Outcome evidence | 390 | 377 | 450 |
| `verification` | Target and guardrails evaluated together | 390 | 751 | 850 |
| `wr-history` | History | 1440 | 467 | 550 |
| `wr-overview` | Lifecycle | 1440 | 422 | 500 |
| `wr-overview` | Work done | 1440 | 422 | 500 |
| `wr-record` | Maintenance record · activity | 1440 | 603 | 700 |

**B3-17 specific ruling:** The 8.6x/17x Interpretation history is D3. Show at most three compact history rows per default page, retain an accessible Next/Previous history control and the full selected record on demand. Closed cap: 800 px at 1440 and 1400 px at 390. The current 1823/4572 px default fails; do not grandfather it. A user who opens every disclosure is exempt from these heights but must retain all text, focus order and navigation.
