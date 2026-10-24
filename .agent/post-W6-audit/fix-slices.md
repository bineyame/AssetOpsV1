# Post-W6 D3 fix slices

Architect plan, 2026-10-24. Each card is a reviewable vertical correction on a fresh task branch from the frozen/rebased main. A D3 closes only after focused tests, independent review and current-SHA app/mock recapture. No product code was edited in classification. The owner walkthrough follows the demo sprint and story-based bootstrap context for **three** verticals: mini-grid, cold chain and EV charging.

## Sequencing and shared files

Run shell first. Then W1 mini, W2 cold, W2 EV, W3 estate, W4 mini, W5 cold, W5 EV, W6 global in that merge order. The `a` card precedes `b` within a seam. Parallel work is safe only for W3 estate with W5 cold while their listed files stay disjoint; W5 cold/EV both touch `siteWorkCases.tsx` and `domainActionClient.ts`, W1/W2 touch `App.tsx`, and shell touches all captures. Rebase and recapture after every merge that changes shared navigation. Each card has five build units: (1) correct structure/routing; (2) correct selected data and copy; (3) correct refusals and long content; (4) focused tests; (5) paired recaptures and cap proof. Split cards divide affected panels, with no shared-file parallelism within one seam.

## Cards

### shell-typography-copy — Shared shell, typography and copy

**Size:** 16 D3 IDs; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R115` (B1-02), `R119` (B1-06), `R120` (B1-07), `R125` (B1-14), `R127` (B1-16), `R129` (B1-21), `R130` (B1-22), `R133` (B1-25), `R140` (B1-43), `R141` (B1-55), `R149` (B1-66), `R151` (B1-53), `R152` (B1-54), `R170` (B2-21), `R203` (B4-03), `R319` (B13-01).

**Panels and order:** `asset`: Observed reserve and power exposure → Interpretation and next evidence → Condition evidence and claim boundary; `changes`: Change and effect → Decision path; `evidence-analysis`: Accepted records behind the conclusions → How a claim limit is set; `foundation`: Configured topology → Identity & operating obligations → Time-valid control configuration; `readiness`: Readiness and commissioning evidence → Gateway status · GW-MG-01 → Connected sources → Effect on readiness and confidence; `sites`: Site inventory → In setup; `sitework-incidents`: Incidents at this site; `sitework-maintenance`: Maintenance at this site; `sld`: Kobo Mini-grid · AC-coupled mini-grid → What each part does.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** all 87 baseline screens at 1440/390; every short refusal; singleton counts; UTC/EAT.

**Files:** frontend/src/App.tsx; frontend/src/shell/OperatorShellLayout.tsx; frontend/src/shell/WorkspaceShellLayout.tsx; frontend/src/sites/domainActionClient.ts; frontend/src/sites/siteWorkCases.tsx; frontend/src/sites/EvHealthDepth.tsx; frontend/src/work/globalWorkParts.tsx; frontend/src/work/WorkRequestOverview.tsx.

**Tests:** frontend/src/sites/__tests__/siteWorkCases.test.tsx; frontend/src/work/__tests__/globalWorkClient.test.ts; add focused routing, refusal, selected-row and access tests for each changed behavior.

**Paired recaptures:** all 87 baseline screens at 1440/390; every short refusal; singleton counts; UTC/EAT. Compare exact panel count/order/titles, links, typography, horizontal overflow, and closed-panel heights at 1440 and 390. Reuse the indexed producer and record the new SHA.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W1-mini-Action-a — W1 mini Site, Finding, Action and verification

**Size:** 18 D3 IDs; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R156` (B2-07), `R157` (B2-08), `R159` (B2-10), `R164` (B2-15), `R171` (B2-22), `R178` (B2-29), `R184` (B3-01), `R185` (B3-02), `R186` (B3-03), `R187` (B3-04), `R188` (B3-05), `R189` (B3-06), `R190` (B3-07), `R191` (B3-08), `R192` (B3-09), `R193` (B3-10), `R195` (B3-12), `R196` (B3-13).

**Panels and order:** `dispatch`: Sources and 15-minute blocks → Selected block · 14:20–14:35 → Accepted sample coverage; `evidence-analysis`: Accepted records behind the conclusions → How a claim limit is set; `finding`: What happened → What limits this conclusion → What to do next → Where to look next; `finding-evidence`: Evidence bundle · F-104 → Inspect source lineage; `finding-history`: Revision history; `mini`: What happened in the selected hour → Operating context → Needs attention → Bounded money consequence → Next step; `sitefindings`: Findings at this site.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B1–B5 representative, priced, held, failed, unknown, selected and refused at both widths.

**Files:** frontend/src/sites/SiteFinding.tsx; frontend/src/sites/SiteFindingEvidence.tsx; frontend/src/sites/SiteFindingHistory.tsx; frontend/src/sites/SiteAction.tsx; frontend/src/sites/SiteActionVerification.tsx; frontend/src/sites/SiteWorkActions.tsx; frontend/src/sites/miniDepthClient.ts; frontend/src/App.tsx.

**Tests:** frontend/src/sites/__tests__/siteAction.test.tsx; frontend/src/sites/__tests__/siteActionVerification.test.tsx; frontend/src/sites/__tests__/siteWorkActions.test.tsx; add focused routing, refusal, selected-row and access tests for each changed behavior.

**Paired recaptures:** B1–B5 representative, priced, held, failed, unknown, selected and refused at both widths. Compare exact panel count/order/titles, links, typography, horizontal overflow, and closed-panel heights at 1440 and 390. Reuse the indexed producer and record the new SHA.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W1-mini-Action-b — W1 mini Site, Finding, Action and verification

**Size:** 18 D3 IDs; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R197` (B3-14), `R198` (B3-15), `R199` (B3-16), `R200` (B3-17), `R201` (B3-18), `R202` (B4-01), `R204` (B4-04), `R205` (B4-05), `R209` (B4-10), `R218` (B4-19), `R219` (B4-20), `R220` (B4-21), `R221` (B4-22), `R222` (B4-24), `R223` (B5-01), `R228` (B5-07), `R229` (B5-08), `R230` (B5-09).

**Panels and order:** `action-evidence`: Evidence requirements; `action-history`: Action history; `action-plan`: Success criteria; `assumptions`: Financial assumptions → Impact preview → Interpretation history; `financials`: What happened → what it means in money → Assumptions in use → Trade-offs and exclusions; `recommendation`: Proposed intervention → Declare success before evaluating → Evidence needed to verify; `sitefindings`: Findings at this site; `sitework`: Actions at this site; `verification`: Target and guardrails evaluated together → Activity evidence → Outcome evidence.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B1–B5 representative, priced, held, failed, unknown, selected and refused at both widths.

**Files:** frontend/src/sites/SiteFinding.tsx; frontend/src/sites/SiteFindingEvidence.tsx; frontend/src/sites/SiteFindingHistory.tsx; frontend/src/sites/SiteAction.tsx; frontend/src/sites/SiteActionVerification.tsx; frontend/src/sites/SiteWorkActions.tsx; frontend/src/sites/miniDepthClient.ts; frontend/src/App.tsx.

**Tests:** frontend/src/sites/__tests__/siteAction.test.tsx; frontend/src/sites/__tests__/siteActionVerification.test.tsx; frontend/src/sites/__tests__/siteWorkActions.test.tsx; add focused routing, refusal, selected-row and access tests for each changed behavior.

**Paired recaptures:** B1–B5 representative, priced, held, failed, unknown, selected and refused at both widths. Compare exact panel count/order/titles, links, typography, horizontal overflow, and closed-panel heights at 1440 and 390. Reuse the indexed producer and record the new SHA.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W2-cold — Cold Site and Findings routing

**Size:** 14 D3 IDs; five build units. **Severity:** High.

**Exact D3 IDs:** `R241` (B6-10), `R242` (B6-11), `R244` (B6-13), `R245` (B6-14), `R246` (B6-15), `R247` (B6-17), `R249` (B6-20), `R253` (B7-01), `R254` (B7-03), `R255` (B7-04), `R256` (B7-05), `R258` (B7-07), `R259` (B7-08), `R261` (B7-11).

**Panels and order:** `cold`: What happened · power → cooling → product conditions → Chamber temperature → Needs attention → Bounded money consequence → Next step; `cold-assumptions`: Financial assumptions; `cold-evidence`: What we can conclude now → Data sources · data quality, not equipment condition → Most useful next evidence; `cold-evidence-analysis`: Accepted records behind the conclusions → How a claim limit is set; `cold-financials`: What happened → what it means in money → Assumptions in use → Not included; `cold-finding`: Bounded conclusion → Operational context → Recommended next step; `cold-findings`: Findings at this site; `coldbackup`: What the chain shows → Reconstructed event chain → Backup event chains → Evidence by causal step; `temperature`: Temperature with operating context → Excursion context → Claim boundary.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B6–B7 plus cold-finding-excursion representative and false Findings reason; both widths.

**Files:** frontend/src/sites/coldSiteViews.tsx; frontend/src/sites/SiteFindingIndex.tsx; frontend/src/shell/coldSiteRoutes.tsx; frontend/src/App.tsx.

**Tests:** frontend/src/sites/__tests__/coldSiteViews.test.tsx; frontend/src/shell/__tests__/s404SiteFindingIndex.test.tsx; add focused routing, refusal, selected-row and access tests for each changed behavior.

**Paired recaptures:** B6–B7 plus cold-finding-excursion representative and false Findings reason; both widths. Compare exact panel count/order/titles, links, typography, horizontal overflow, and closed-panel heights at 1440 and 390. Reuse the indexed producer and record the new SHA.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W2-EV — EV Site, tabs and depth links

**Size:** 13 D3 IDs; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R265` (B8-06), `R267` (B8-08), `R268` (B8-12), `R270` (B8-14), `R271` (B8-15), `R275` (B8-19), `R276` (B8-20), `R280` (B8-24), `R281` (B8-27), `R283` (B9-03), `R284` (B9-05), `R285` (B9-08), `R286` (B9-09).

**Panels and order:** `ev`: What happened on the service day → Charging activity and site power → Needs attention → Bounded money consequence → Next step; `ev-assumptions`: Financial assumptions; `ev-evidence`: What we can conclude now → Data sources · data quality, not equipment condition → Most useful next evidence; `ev-evidence-analysis`: Accepted records behind the conclusions → How a claim limit is set; `ev-financials`: What happened → what it means in money → Assumptions in use → Not included; `ev-finding`: Bounded conclusion → Operational context → Recommended next step; `ev-readiness`: Readiness and commissioning evidence → Gateway status · GW-EV-01 → Connected sources → Effect on readiness and confidence; `sessions`: Session service records → How to read the denominator → Cause remains bounded.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B8–B9, EV main-tab destinations, refused and missing-meter; both widths.

**Files:** frontend/src/sites/EvSiteViews.tsx; frontend/src/sites/evDepthClient.ts; frontend/src/shell/evSiteRoutes.tsx; frontend/src/App.tsx.

**Tests:** frontend/src/sites/__tests__/evDepth.test.tsx; frontend/src/sites/__tests__/evSiteMoneyRoutes.test.tsx; add focused routing, refusal, selected-row and access tests for each changed behavior.

**Paired recaptures:** B8–B9, EV main-tab destinations, refused and missing-meter; both widths. Compare exact panel count/order/titles, links, typography, horizontal overflow, and closed-panel heights at 1440 and 390. Reuse the indexed producer and record the new SHA.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W3-estate — Estate indices, evidence, money and Portfolio

**Size:** 9 D3 IDs; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R293` (B10-07), `R294` (B10-08), `R295` (B10-09), `R296` (B11-01), `R297` (B11-02), `R300` (B11-05), `R302` (B11-07), `R307` (B11-12), `R308` (B11-13).

**Panels and order:** `actions`: Managed actions; `findings`: Findings across the estate; `findings-cost`: Cost lens; `findings-opportunities`: Opportunities lens; `findings-risks`: Risks lens; `globalevidence`: Capability coverage across sites → Recurring evidence gaps; `globalfinancials`: Consequence register → Aggregation rule; `portfolio`: Where management should act first → Objectives across the estate → An opportunity beyond reducing cost → What changed in this review.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B10–B11 clean, partial, pending, historical, page two and long-row; both widths.

**Files:** frontend/src/estate/findingIndex.tsx; frontend/src/estate/actionIndex.tsx; frontend/src/estate/EstateEvidence.tsx; frontend/src/estate/EstateFinancials.tsx; frontend/src/estate/EstatePortfolio.tsx; backend/assetops_backend/estate/index.py; backend/assetops_backend/estate/evidence_money.py; backend/assetops_backend/estate/financials.py; backend/assetops_backend/estate/portfolio.py.

**Tests:** frontend/src/estate/__tests__/estateRoots.test.tsx; frontend/src/estate/__tests__/estateEvidence.test.tsx; frontend/src/estate/__tests__/estatePortfolio.test.tsx; add focused routing, refusal, selected-row and access tests for each changed behavior.

**Paired recaptures:** B10–B11 clean, partial, pending, historical, page two and long-row; both widths. Compare exact panel count/order/titles, links, typography, horizontal overflow, and closed-panel heights at 1440 and 390. Reuse the indexed producer and record the new SHA.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W4-mini — Mini depth, decisions and cases

**Size:** 15 D3 IDs; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R309` (B12-02), `R310` (B12-03), `R311` (B12-04), `R312` (B12-05), `R313` (B12-06), `R316` (B12-09), `R318` (B12-11), `R320` (B13-02), `R321` (B13-03), `R322` (B13-04), `R324` (B13-06), `R325` (B13-07), `R328` (B13-11), `R331` (B13-15), `R333` (B13-18).

**Panels and order:** `alternatives`: Alternatives to investigate; `backup`: Backup event chains → Backup readiness evidence → Operating evidence → Next evidence; `fuel`: Fuel balance at a glance → Balance bridge → Inspect existing generator fuel interpretation; `opportunity-finding`: Bounded opportunity → Next decision → Consequence basis; `renewable`: From physical headroom to an opportunity → Productive-use evaluation → Eligible and excluded windows; `scenarios`: Financial scenarios; `service`: Where the power went → Delivered power by addressed load → What is supported → What unlocks a service conclusion; `sitework-incidents`: Incidents at this site; `sitework-maintenance`: Maintenance at this site.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B12–B13 stocked, zero, DB-time 409, refused, page two and long-row; both widths.

**Files:** frontend/src/sites/SiteWorkIncidents.tsx; frontend/src/sites/SiteWorkMaintenance.tsx; frontend/src/sites/siteWorkCases.tsx; frontend/src/sites/miniDepthClient.ts; frontend/src/sites/MiniPerformance.tsx; frontend/src/sites/MiniScenarios.tsx.

**Tests:** frontend/src/sites/__tests__/siteWorkCases.test.tsx; frontend/src/sites/__tests__/miniDecisions.test.tsx; frontend/src/sites/__tests__/miniRenewableRoutes.test.tsx; add focused routing, refusal, selected-row and access tests for each changed behavior.

**Paired recaptures:** B12–B13 stocked, zero, DB-time 409, refused, page two and long-row; both widths. Compare exact panel count/order/titles, links, typography, horizontal overflow, and closed-panel heights at 1440 and 390. Reuse the indexed producer and record the new SHA.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W5-cold-Work — Cold depth and Work

**Size:** 6 D3 IDs; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R334` (B14-03), `R336` (B14-07), `R337` (B14-08), `R338` (B14-09), `R339` (B14-10), `R344` (B15-10).

**Panels and order:** `cold-action`: Declared outcome criteria → Related activity; `cold-health`: Condition and evidence; `cold-scenarios`: Financial scenarios; `cold-work`: Actions at this site; `cooling`: Recovery curves → Context normalization → Next best evidence.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B14–B15 positive, pending, unknown, zero, refused, forbidden and worst case; both widths.

**Files:** frontend/src/sites/coldSiteViews.tsx; frontend/src/sites/DomainActionVerification.tsx; frontend/src/sites/siteWorkCases.tsx; frontend/src/sites/domainActionClient.ts.

**Tests:** frontend/src/sites/__tests__/coldDepth.test.tsx; frontend/src/sites/__tests__/coldWorkActions.test.tsx; frontend/src/sites/__tests__/domainActionVerification.test.tsx; add focused routing, refusal, selected-row and access tests for each changed behavior.

**Paired recaptures:** B14–B15 positive, pending, unknown, zero, refused, forbidden and worst case; both widths. Compare exact panel count/order/titles, links, typography, horizontal overflow, and closed-panel heights at 1440 and 390. Reuse the indexed producer and record the new SHA.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W5-EV-Work — EV depth and Work

**Size:** 6 D3 IDs; five build units. **Severity:** Medium/Low.

**Exact D3 IDs:** `R345` (B16-06), `R346` (B16-07), `R347` (B16-16), `R348` (B17-04), `R349` (B17-06), `R350` (B17-08).

**Panels and order:** `availability`: Connector states over the service schedule → Full-schedule availability bound → Most useful next evidence; `energy`: Import power and configured limit → What can be concluded → Technical-to-financial bridge; `ev-action`: Declared verification plan; `ev-health`: Condition and evidence; `ev-scenarios`: Financial scenarios; `ev-work`: Actions at this site.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B16–B17 positive, unknown, pending, stale, refused, forbidden and worst case; both widths.

**Files:** frontend/src/sites/evDepthClient.ts; frontend/src/sites/DomainActionVerification.tsx; frontend/src/sites/siteWorkCases.tsx; frontend/src/sites/domainActionClient.ts; backend/tests/test_w504_ev_intent_api.py.

**Tests:** frontend/src/sites/__tests__/evDepth.test.tsx; frontend/src/sites/__tests__/evWorkActions.test.tsx; frontend/src/sites/__tests__/domainActionVerification.test.tsx; backend/tests/test_w504_ev_intent_api.py; add focused routing, refusal, selected-row and access tests for each changed behavior.

**Paired recaptures:** B16–B17 positive, unknown, pending, stale, refused, forbidden and worst case; both widths. Compare exact panel count/order/titles, links, typography, horizontal overflow, and closed-panel heights at 1440 and 390. Reuse the indexed producer and record the new SHA.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

### W6-global-Work — Global lists and exact request

**Size:** 16 D3 IDs; five build units. **Severity:** High.

**Exact D3 IDs:** `R352` (B18-03), `R353` (B18-04), `R354` (B18-05), `R356` (B18-07), `R357` (B18-08), `R359` (B18-10), `R360` (B18-11), `R361` (B18-13), `R364` (B19-03), `R366` (B19-05), `R367` (B19-07), `R368` (B19-08), `R370` (B19-10), `R371` (B19-12), `R372` (B19-13), `R373` (B19-15).

**Panels and order:** `incidents`: Incident cases → Case boundaries; `maintenance`: Corrective work requests; `maintenance-preventive`: Preventive plan; `oprecords`: Operational records → Record a manual reading → How records are used; `wr-history`: History; `wr-overview`: Work done → Lifecycle; `wr-record`: Maintenance record · activity.

**Data source:** selected stored Site/Foundation/evidence/Action/Work records at the captured window and cutoff; use the existing reviewed walkthrough named in each batch. Never insert mock literals as live facts.

**States:** B18–B19 mini, cold, EV, 403, 404, 503, page two, historical, all-open and 160-char rows; both widths.

**Files:** frontend/src/work/globalWorkParts.tsx; frontend/src/work/WorkRequestOverview.tsx; frontend/src/work/WorkRequestRecord.tsx; frontend/src/work/WorkRequestHistory.tsx; backend/assetops_backend/main.py; backend/assetops_backend/global_work_api.py; backend/assetops_backend/work/global_index.py.

**Tests:** frontend/src/work/__tests__/globalWorkClient.test.ts; backend/tests/test_w601a_global_incidents.py; backend/tests/test_w601b_global_maintenance.py; backend/tests/test_w601c_request_detail.py; backend/tests/test_w601e_operational_index.py; add focused routing, refusal, selected-row and access tests for each changed behavior.

**Paired recaptures:** B18–B19 mini, cold, EV, 403, 404, 503, page two, historical, all-open and 160-char rows; both widths. Compare exact panel count/order/titles, links, typography, horizontal overflow, and closed-panel heights at 1440 and 390. Reuse the indexed producer and record the new SHA.

**Caps:** apply the measured docket below. User-expanded all-disclosures-open is exempt from closed-height caps; it must remain readable without page or panel clipping. If a remeasure exceeds a cap, adjust layout or internal scrolling and recapture; if that cannot preserve the content, return to Architect for a revised cap based on the worst-case fixture before merge.

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

Caps below are per named panel and viewport. Each is based on the largest captured closed state, with a five-row, 160-character allowance where a panel has table rows. A cap is a readability/scroll budget, never permission to hide a row. Before building, use the selected worst-case producer or a pure render fixture of five 160-character rows. The all-disclosures-open viewer state is expressly exempt from these closed-height caps; no clipping is allowed. If a remeasure exceeds a cap, change wrapping, paging or inner scroll and recapture, or ask the Architect to revise the measured cap before merge.

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
| `cold-findings` | Findings at this site | 390 | 441 | 500 |
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
| `ev-evidence-analysis` | Accepted records behind the conclusions | 1440 | 399 | 450 |
| `ev-findings` | Findings at this site | 390 | 430 | 500 |
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
| `evidence-analysis` | Accepted records behind the conclusions | 1440 | 910 | 1050 |
| `evidence-analysis` | Accepted records behind the conclusions | 390 | 1235 | 1400 |
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
| `foundation` | Identity and operating obligations | 1440 | 595 | 700 |
| `foundation` | Identity and operating obligations | 390 | 678 | 800 |
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
