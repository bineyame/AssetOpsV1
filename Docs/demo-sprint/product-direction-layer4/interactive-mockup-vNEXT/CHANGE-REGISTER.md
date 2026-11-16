# vNEXT change register

Old version: `frontend/mockups/v70/` (110 screens, v7.0 architecture screen review).
New version: `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/` (146 screens = 110 v7.0 + 36 added).
Unmodified v7.0 sources for diffing: `src-v70-baseline/`. Diff with `diff -u src-v70-baseline/screens.js screens.js` (likewise `portfolio.js`, `outcomes.js`, `build.mjs`).

**Status: Not approved: awaits owner inspection.**

Counts: Preserved 109 · Changed 1 · Removed 0 · Deferred 0 (v7.0 screens) · Added 36.

## 1. Shared-shell changes (affect every v7.0 screen; screens themselves unchanged)

| # | Change | File | Why |
|---|---|---|---|
| S1 | New **Decisions** group at the top of the left menu (Decision home, Why off plan, Plan and budget, Proof it worked, Pilot request) | `screens.js` `rail()` | Puts business results and choices first (brief Part V: "begin with a business result/decision rather than a technical landing page") while keeping every v7.0 route one click away. |
| S2 | Menu label "Portfolio" shown as **Operations view** (route `#/portfolio`, root name and breadcrumbs unchanged) | `screens.js` `rail()` | Distinguishes the v7.0 operations page from the new decision home without breaking links. |
| S3 | **Default route** (empty or unknown hash) opens `#/decide-lakeside` instead of `#/portfolio` | `decisions.js` (decision screens are registered first) | The demo opens on an operator's result against plan. |
| S4 | Decision screens use their own top bar (operator switch, "October 2026 · books closed 6 Nov") instead of the v7.0 range picker | `screens.js` `shell()` delegates to `decisionShell()` | Decision views are one accounting period; the v7.0 event-window picker does not apply to them. |
| S5 | Review bar: label "vNEXT DECISION REVIEW · not approved"; new **What changed in vNEXT** button; PDF link now points to the v7.0 PDF in `frontend/mockups/v70/` | `screens.js` `render()` | Reviewers see status and change list in context; the PDF is not copied. |
| S6 | Review notes stored under a new browser key (`assetops-vnext-review-notes`); export file `AssetOps-vNEXT-review-notes.json` now also contains the full screen inventory with vNEXT status | `screens.js` | Keeps v7.0 notes separate; the export is the extended manifest export the commission asked for. |
| S7 | Relative links re-pointed to their v7.0 locations (architecture spec link in Review notes; Portfolio "previous version" preview image) | `screens.js`, `portfolio.js` | The folder moved; links would otherwise break. No content change. |
| S8 | Initial `render()` moved from the end of `screens.js` to the end of `decisions.js` | `screens.js`, `decisions.js` | Decision screens must be registered before first render. |
| S9 | Book mode (`?book`) and the screen selector now include the 36 decision screens (listed first) | runtime | Same review tools cover the new screens. |

## 2. Changed v7.0 screen

| Screen | Before (v7.0) | After (vNEXT) | Why it improves executive decision comprehension |
|---|---|---|---|
| `portfolio` (Operations view) | No route to a decision view. Optimize card basis line: "Modelled + scenario · one-hour window · reliability checked as a safeguard". | Blue banner with a link to the decision home. Optimize card basis line adds: "Period note: this is one generator finding's exposure on the last day of the selected window, not a total for the period." | Removes the presentation risk recorded in the decision-intelligence baseline doc §5.2 (a 7- or 30-day reader would take the figure as the period's avoidable fuel cost). The banner tells the reader this page shows the earlier three-site estate. |

## 3. v7.0 screen inventory (all 110 ids)

| Screen id | Title | Status | Note |
|---|---|---|---|
| `portfolio` | Portfolio · Portfolio Value & Operations | Changed | Changed: decision-home banner; Optimize card basis gains the period note (one finding’s exposure on the window’s last day, not a period total). |
| `sites` | Sites · Sites | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `mini` | Sites · Kobo Mini-grid / Overview | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `foundation` | Sites · Kobo Mini-grid / Foundation | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `readiness` | Sites · Kobo Mini-grid / Foundation | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `changes` | Sites · Kobo Mini-grid / Foundation | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `dispatch` | Sites · Kobo Mini-grid / Performance | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `renewable` | Sites · Kobo Mini-grid / Performance | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `evidence` | Sites · Kobo Mini-grid / Evidence | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `finding` | Findings · Generator support merits review / Overview | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `analysis` | Findings · Generator support merits review / Analysis | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `financials` | Sites · Kobo Mini-grid / Financials | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `assumptions` | Sites · Kobo Mini-grid / Financials | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `recommendation` | Findings · Generator support merits review / Recommendation | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `verification` | Actions · Reduce extended generator support / Verification | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `asset` | Assets · Kobo battery / Health | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `health` | Sites · Kobo Mini-grid / Health | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `lab` | Simulator Lab · Kobo · Gateway & Ingestion / Gateway & Ingestion | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold` | Sites · GreenHarvest Cold Room / Overview | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `temperature` | Sites · GreenHarvest Cold Room / Performance | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cooling` | Sites · GreenHarvest Cold Room / Performance | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `coldbackup` | Sites · GreenHarvest Cold Room / Performance | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev` | Sites · Depot Charging Hub / Overview | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `sessions` | Sites · Depot Charging Hub / Performance | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `availability` | Sites · Depot Charging Hub / Performance | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `energy` | Sites · Depot Charging Hub / Performance | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `incident` | Incidents · Backup failure and temperature excursion / Timeline | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `workverification` | Maintenance · Starter and control-circuit inspection / Verification | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `service` | Sites · Kobo Mini-grid / Performance | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `fuel` | Sites · Kobo Mini-grid / Performance | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `backup` | Sites · Kobo Mini-grid / Performance | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `sitefindings` | Sites · Kobo Mini-grid / Findings | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `sitework` | Sites · Kobo Mini-grid / Work | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `sitework-incidents` | Sites · Kobo Mini-grid / Work | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `sitework-maintenance` | Sites · Kobo Mini-grid / Work | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `evidence-analysis` | Sites · Kobo Mini-grid / Evidence | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `assets` | Assets · Assets | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `findings` | Findings · Findings | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `actions` | Actions · Actions | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `incidents` | Incidents · Incidents | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `maintenance` | Maintenance · Maintenance | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `globalevidence` | Evidence · Portfolio evidence | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `globalfinancials` | Financials · Portfolio financials | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-foundation` | Sites · GreenHarvest Cold Room / Foundation | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-health` | Sites · GreenHarvest Cold Room / Health | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-evidence` | Sites · GreenHarvest Cold Room / Evidence | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-evidence-analysis` | Sites · GreenHarvest Cold Room / Evidence | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-financials` | Sites · GreenHarvest Cold Room / Financials | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-assumptions` | Sites · GreenHarvest Cold Room / Financials | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-findings` | Sites · GreenHarvest Cold Room / Findings | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-work` | Sites · GreenHarvest Cold Room / Work | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-work-incidents` | Sites · GreenHarvest Cold Room / Work | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-work-maintenance` | Sites · GreenHarvest Cold Room / Work | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-finding` | Findings · Backup response failed during grid interruption / Overview | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-recommendation` | Findings · Backup response failed during grid interruption / Recommendation | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-foundation` | Sites · Depot Charging Hub / Foundation | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-health` | Sites · Depot Charging Hub / Health | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-evidence` | Sites · Depot Charging Hub / Evidence | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-evidence-analysis` | Sites · Depot Charging Hub / Evidence | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-financials` | Sites · Depot Charging Hub / Financials | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-assumptions` | Sites · Depot Charging Hub / Financials | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-findings` | Sites · Depot Charging Hub / Findings | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-work` | Sites · Depot Charging Hub / Work | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-work-incidents` | Sites · Depot Charging Hub / Work | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-work-maintenance` | Sites · Depot Charging Hub / Work | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-finding` | Findings · Connector 2 charging session interrupted / Overview | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-recommendation` | Findings · Connector 2 charging session interrupted / Recommendation | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-action` | Actions · ACT-061 · Investigate connector 2 / Verification | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `finding-evidence` | Findings · Generator support review / Evidence | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `alternatives` | Findings · Generator support review / Alternatives | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `finding-history` | Findings · Generator support review / History | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `action-overview` | Actions · ACT-048 · Generator policy review / Overview | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `action-plan` | Actions · ACT-048 · Generator policy review / Plan | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `action-execution` | Actions · ACT-048 · Generator policy review / Execution | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `action-evidence` | Actions · ACT-048 · Generator policy review / Evidence | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `action-history` | Actions · ACT-048 · Generator policy review / History | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `opportunity-finding` | Findings · Productive-use headroom at Kobo / Overview | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-finding-excursion` | Findings · Chamber temperature went above policy / Overview | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-action` | Actions · ACT-051 · Witness automatic-start test / Verification | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `scenarios` | Sites · Kobo Mini-grid / Financials | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-scenarios` | Sites · GreenHarvest Cold Room / Financials | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-scenarios` | Sites · Depot Charging Hub / Financials | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-readiness` | Sites · GreenHarvest Cold Room / Foundation | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-readiness` | Sites · Depot Charging Hub / Foundation | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `sld` | Sites · Kobo Mini-grid / Foundation | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `cold-sld` | Sites · GreenHarvest Cold Room / Foundation | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `ev-sld` | Sites · Depot Charging Hub / Foundation | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `assets-warranty` | Assets · Assets / Warranty & vendors | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `asset-register` | Assets · Assets / Register asset | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `asset-overview` | Assets · Kobo battery / Overview | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `site-create-form` | Sites · Sites / Add site · form | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `site-create-template` | Sites · Sites / From template | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `site-batch-upload` | Sites · Sites / Batch upload | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `site-setup-history` | Sites · Sites / Setup history | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `asset-performance` | Assets · Kobo battery / Performance | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `asset-config` | Assets · Kobo battery / Configuration | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `asset-edit` | Assets · Kobo battery / Configuration | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `asset-work` | Assets · Kobo battery / Work | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `asset-evidence` | Assets · Kobo battery / Evidence | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `asset-warranty` | Assets · Kobo battery / Warranty | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `findings-cost` | Findings · Findings / Cost | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `findings-risks` | Findings · Findings / Risks | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `findings-opportunities` | Findings · Findings / Opportunities | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `maintenance-preventive` | Maintenance · Maintenance / Preventive · scheduled | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `wr-overview` | Maintenance · Starter and control-circuit inspection / Overview | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `wr-record` | Maintenance · Starter and control-circuit inspection / Maintenance record | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `wr-history` | Maintenance · Starter and control-circuit inspection / History | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `oprecords` | Operational records · Operational records | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `settings-policies` | Settings · Settings / Operational policies | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |
| `settings-tenant` | Settings · Settings / Tenant configuration | Preserved | Reachable unchanged; shared shell changes only (menu group, menu label, review bar). |

## 4. Added screens (36)

All are data-driven templates in `decisions.js` over `MANIFEST` (`fixtures.js`, generated from `../demo-site-scenario-manifest.yaml`). Operators: `lakeside` = Lakeside Power (mini-grid), `harvest` = Harvest Cold Network (cold rooms), `metro` = Metro Bus Depots (captive EV fleet).

| Route | Title | Operator | Why it improves executive decision comprehension |
|---|---|---|---|
| `#/decide-lakeside` | Decision home | lakeside | Leads with the October result against plan, coverage and a counter-intuitive contrast, then a ranked plan; role toggle reorders without changing numbers (L1.3, Part V opening). |
| `#/bridge-lakeside` | Why we are off plan | lakeside | Shows plan-to-actual by site and driver with the unexplained part visible, so a CFO sees cause and evidence type in one view. |
| `#/decide-harvest` | Decision home | harvest | Leads with the October result against plan, coverage and a counter-intuitive contrast, then a ranked plan; role toggle reorders without changing numbers (L1.3, Part V opening). |
| `#/bridge-harvest` | Why we are off plan | harvest | Shows plan-to-actual by site and driver with the unexplained part visible, so a CFO sees cause and evidence type in one view. |
| `#/decide-metro` | Decision home | metro | Leads with the October result against plan, coverage and a counter-intuitive contrast, then a ranked plan; role toggle reorders without changing numbers (L1.3, Part V opening). |
| `#/bridge-metro` | Why we are off plan | metro | Shows plan-to-actual by site and driver with the unexplained part visible, so a CFO sees cause and evidence type in one view. |
| `#/econ-kobo` | Kobo · site economics | lakeside | One template for nine sites: P&L against plan with source badges and the vertical chain (energy-to-cash, occupancy-normalised energy, departures and tariff) that explains the money. |
| `#/econ-kisiwa` | Kisiwa · site economics | lakeside | One template for nine sites: P&L against plan with source badges and the vertical chain (energy-to-cash, occupancy-normalised energy, departures and tariff) that explains the money. |
| `#/econ-mto` | Mto · site economics | lakeside | One template for nine sites: P&L against plan with source badges and the vertical chain (energy-to-cash, occupancy-normalised energy, departures and tariff) that explains the money. |
| `#/econ-mwea` | Room A · Mwea · site economics | harvest | One template for nine sites: P&L against plan with source badges and the vertical chain (energy-to-cash, occupancy-normalised energy, departures and tariff) that explains the money. |
| `#/econ-thika` | Room B · Thika · site economics | harvest | One template for nine sites: P&L against plan with source badges and the vertical chain (energy-to-cash, occupancy-normalised energy, departures and tariff) that explains the money. |
| `#/econ-kirinyaga` | Room C · Kirinyaga · site economics | harvest | One template for nine sites: P&L against plan with source badges and the vertical chain (energy-to-cash, occupancy-normalised energy, departures and tariff) that explains the money. |
| `#/econ-embakasi` | Embakasi · site economics | metro | One template for nine sites: P&L against plan with source badges and the vertical chain (energy-to-cash, occupancy-normalised energy, departures and tariff) that explains the money. |
| `#/econ-kasarani` | Kasarani · site economics | metro | One template for nine sites: P&L against plan with source badges and the vertical chain (energy-to-cash, occupancy-normalised energy, departures and tariff) that explains the money. |
| `#/econ-ruiru` | Ruiru · site economics | metro | One template for nine sites: P&L against plan with source badges and the vertical chain (energy-to-cash, occupancy-normalised energy, departures and tariff) that explains the money. |
| `#/choice-kobo-generator` | Change when Kobo’s generator stops | lakeside | Answers the experience invariant (L3.6) for one decision: all options incl. do nothing, costs, effects, evidence type, safeguards, rejected options with why-not, sensitivity, proof and records needed; contract rights where decision-relevant. |
| `#/choice-kobo-battery` | Protect Kobo’s battery warranty | lakeside | Answers the experience invariant (L3.6) for one decision: all options incl. do nothing, costs, effects, evidence type, safeguards, rejected options with why-not, sensitivity, proof and records needed; contract rights where decision-relevant. |
| `#/choice-kisiwa-generator` | Restore Kisiwa’s backup generator | lakeside | Answers the experience invariant (L3.6) for one decision: all options incl. do nothing, costs, effects, evidence type, safeguards, rejected options with why-not, sensitivity, proof and records needed; contract rights where decision-relevant. |
| `#/choice-mto-inverter` | Restore Mto’s failed inverter | lakeside | Answers the experience invariant (L3.6) for one decision: all options incl. do nothing, costs, effects, evidence type, safeguards, rejected options with why-not, sensitivity, proof and records needed; contract rights where decision-relevant. |
| `#/choice-mto-demand` | Sell Mto’s spare daytime solar | lakeside | Answers the experience invariant (L3.6) for one decision: all options incl. do nothing, costs, effects, evidence type, safeguards, rejected options with why-not, sensitivity, proof and records needed; contract rights where decision-relevant. |
| `#/choice-mto-billing` | Bill the Mto customers missed after the meter swap | lakeside | Answers the experience invariant (L3.6) for one decision: all options incl. do nothing, costs, effects, evidence type, safeguards, rejected options with why-not, sensitivity, proof and records needed; contract rights where decision-relevant. |
| `#/choice-mwea-demand` | Fill Mwea’s empty space | harvest | Answers the experience invariant (L3.6) for one decision: all options incl. do nothing, costs, effects, evidence type, safeguards, rejected options with why-not, sensitivity, proof and records needed; contract rights where decision-relevant. |
| `#/choice-thika-backup` | Protect Thika’s stock until the switch is fixed | harvest | Answers the experience invariant (L3.6) for one decision: all options incl. do nothing, costs, effects, evidence type, safeguards, rejected options with why-not, sensitivity, proof and records needed; contract rights where decision-relevant. |
| `#/choice-kirinyaga-energy` | Bring Kirinyaga’s energy use back to normal | harvest | Answers the experience invariant (L3.6) for one decision: all options incl. do nothing, costs, effects, evidence type, safeguards, rejected options with why-not, sensitivity, proof and records needed; contract rights where decision-relevant. |
| `#/choice-embakasi-schedule` | Charge Embakasi’s buses outside peak hours | metro | Answers the experience invariant (L3.6) for one decision: all options incl. do nothing, costs, effects, evidence type, safeguards, rejected options with why-not, sensitivity, proof and records needed; contract rights where decision-relevant. |
| `#/choice-kasarani-charger` | Keep Kasarani’s buses running while charger 2 is repaired | metro | Answers the experience invariant (L3.6) for one decision: all options incl. do nothing, costs, effects, evidence type, safeguards, rejected options with why-not, sensitivity, proof and records needed; contract rights where decision-relevant. |
| `#/choice-ruiru-expansion` | Can Ruiru take the city’s extra buses? | metro | Answers the experience invariant (L3.6) for one decision: all options incl. do nothing, costs, effects, evidence type, safeguards, rejected options with why-not, sensitivity, proof and records needed; contract rights where decision-relevant. |
| `#/plan-lakeside` | Plan and budget | lakeside | Makes allocation transparent: budget and crew limits, recommended set, excluded options with reasons, modelled-not-realized totals; budget switch shows the ranking change. |
| `#/verify-lakeside` | Proof it worked | lakeside | Separates the three proofs (operation, money in the books, attribution) so a completed job is never read as realized money. |
| `#/pilot-lakeside` | Pilot request | lakeside | Converts the demo into a bounded paid diagnostic with the source categories and deliverables (Part V convert step). |
| `#/plan-harvest` | Plan and budget | harvest | Makes allocation transparent: budget and crew limits, recommended set, excluded options with reasons, modelled-not-realized totals; budget switch shows the ranking change. |
| `#/verify-harvest` | Proof it worked | harvest | Separates the three proofs (operation, money in the books, attribution) so a completed job is never read as realized money. |
| `#/pilot-harvest` | Pilot request | harvest | Converts the demo into a bounded paid diagnostic with the source categories and deliverables (Part V convert step). |
| `#/plan-metro` | Plan and budget | metro | Makes allocation transparent: budget and crew limits, recommended set, excluded options with reasons, modelled-not-realized totals; budget switch shows the ranking change. |
| `#/verify-metro` | Proof it worked | metro | Separates the three proofs (operation, money in the books, attribution) so a completed job is never read as realized money. |
| `#/pilot-metro` | Pilot request | metro | Converts the demo into a bounded paid diagnostic with the source categories and deliverables (Part V convert step). |

Components added (used across the screens above): role emphasis toggle (CEO/COO/CFO/CCO; reorders and highlights panels and changes the headline question, never the numbers: audit-verified); evidence drawer from every money figure; plan-vs-actual bar chart; waterfall bridge with pattern-coded money classes (recorded, modelled, not explained yet); energy-to-cash flow; occupancy-normalised energy chart; contract-rights panel with 8-stage claim timeline, deadline countdown, cost per path and the fixed legal line; budget and crew meters; three-verdict proof view; example-only pilot form.

## 5. Changed or cut legacy behaviour needing owner approval

1. **Default landing page** is now the decision home (`#/decide-lakeside`), not the v7.0 Portfolio (S3). Alternative: keep `#/portfolio` as default and put the decision home second.
2. **Menu label "Portfolio" → "Operations view"** (S2). The page title stays "Portfolio Value & Operations".
3. **Review notes written in v7.0 are not shown in vNEXT** (separate browser key, S6). Owner may prefer to share one key.
4. **The evidence-state selector** ("Illustrative scenario / Evidence-limited / No evidence") has no effect on decision screens; decision screens show their own "not available yet" states instead. Deferred: limited/no-evidence variants for decision screens.
5. **Optimize card wording** on the Operations view (section 2): owner decides whether the period note is the right fix or whether the figure should be removed for multi-day windows.
6. **Two demo estates side by side**: the v7.0 screens use the earlier estate (Kobo / GreenHarvest / Depot, 6 Oct windows); decision screens use the Layer 4 operators (Oct 2026). Site economics pages link to the v7.0 site view as "Operations detail" with a notice. Owner decides whether the v7.0 screens should be re-skinned onto the Layer 4 operators in a later revision.
7. **Plain-language rewrites of manifest reason strings** (table below). Meaning unchanged; codes, `>=`, "LOI", "P1" etc. removed from screen text.

| Manifest text | On screen |
|---|---|
| `6,430 needed with everything else; budget 5,000` | Needs $6,430 with everything else; the budget is $5,000 |
| `wins if budget >= 6,430 and the cooperative will not extend its letter of intent` | Only if the budget is at least $6,430 and the cooperative will not extend its letter of intent |
| `fails the evening service obligation (P1 hard constraint) on a single genset` | Fails the evening supply obligation: one generator cannot be relied on alone |
| `LOI converts to supply contract; inverter INV-MT-02 restored first` | The letter of intent becomes a supply contract, and inverter 2 is restored first |
| `flat tariff: no schedule saving exists (EV-L1 immaterial here)` | Flat tariff: changing the schedule saves nothing here |
| `every evening kWh is diesel; margin negative at 0.40 and no demand evidence` | Every evening kWh is diesel: the margin is negative at $0.40/kWh and there is no demand evidence |
| `fails dawn adequacy safeguard` | Fails the safeguard: battery below 35% at 5 am on some replayed days |
| `not needed for +6; insufficient alone for +10 (grid upgrade ~45,000 [assumption])` | Not needed for 6 more buses; not enough alone for 10 (a grid upgrade of about $45,000 would also be needed, an assumption) |
| Bridge bases, e.g. `210 L x 1.25 (forward-feasible share of Candidate fuel)`, `120 L x 1.25 consumed minus modelled; investigate (MG-L5)` | 210 L × 1.25 (the share a forward replay shows is avoidable); … being investigated |
| Kobo verification plan (`Candidate generator minutes down >= 50% …; MG-5 dawn SOC >= 35% every day`) | Generator time beyond need down by at least half on comparable days; battery at least 35% at 5 am every day |

## 6. Deferred (not built in this revision)

- Decision screens are English-only, light theme only (v7.0 has no dark theme either).
- No "evidence-limited" variants of decision screens (see 5.4).
- Harvest and Metro have one budget case each in the manifest, so their budget control is shown disabled with that statement.
- Verification plans for Harvest (Kirinyaga repair) and Metro (Embakasi schedule) are not in the manifest; their tests are marked "Proposed in this mock-up" on screen.

## 7. Rev 2: Architect fix round on the review (16 Nov 2026)

Source: `../REVIEW.md` findings (owner: "let the architect address review findings"). Screen inventory unchanged (146 screens; statuses as above). Changes are within `decisions.js`, `decisions.css`, `tools/`, and this pack.

| Item | Screens | Change | Why it improves executive decision comprehension |
|---|---|---|---|
| L11 | none (bundle) | `tools/gen_fixtures.py` strips the private `oracle:` block; fixtures regenerated from the corrected manifest | The expected answers never ship with the demo |
| M1 | `choice-embakasi-schedule`, `econ-embakasi`, Metro home and plan | Super-off-peak tier shown; cheapest schedule shows its bill ($12,975 a month, the lowest) and is rejected with "Cheapest bill, but 3 buses leave short every night"; recommended bill $13,356, $381 more, +$103,965.60 over 12 months | The rejection now visibly trades money against service instead of hiding the cheaper price |
| L2 | `decide-harvest`, `decide-metro`, coverage drawers, site economics | Coverage line and panel for all operators (97.8%, 99.3%) with the estimated lines named | CFO sees recorded vs estimated for every operator |
| L10 | Metro home, bridge, site economics (all three depots) | Depot maintenance in every EV cost; plan $38,520.80, actual $41,705.12, $32.03 per departure; Ruiru on an older tariff | Cost per departure is complete |
| L5 | `choice-kasarani-charger`, Metro home and plan | "Charge one bus at Ruiru on each of the 3 nights until the repair", $90 in total, against about $240 and 2 broken departures | Removes the per-night ambiguity |
| M3 | `plan-lakeside`, `choice-mto-inverter` | New "Will the cooperative extend its letter of intent?" control beside the budget; both inverter paths side by side under the chosen assumption; table of all four cases; "More budget never lowers the result; the letter-of-intent assumption is what changes it." Default $5,000 + Yes | Shows the real driver of the ranking change instead of implying that more budget changes the answer |
| L1 | all decision screens | Plain allocation method and meter-check sentences; "fixture", "manifest" removed from client text; audit vocabulary scan extended and applied to drawers | No internal language in front of a client |
| L7 | `choice-embakasi-schedule`, `choice-mto-inverter`, checklist | Do-nothing rows always state a reason; Mto do-nothing path reads "$0 now; cover lost after 27 Nov 2026"; checklist B9 says the budget control is Lakeside-only | Do nothing is never shown as free when it is not |
| L8 | home (Lakeside), `choice-kobo-generator`, `choice-mto-demand`, `bridge-lakeside` | "Design value: to be reproduced from your data" at first use of 210 L, 20 L and 68 L | Replay figures are not presented as measured results |
| M2 | pack text | "evidence class" wording replaced by money class / plain words | Consistent vocabulary |

Owner approval added by rev 2: the letter-of-intent control and its default (Yes) on Plan and budget.


## 8. Rev 3 (re-review N2–N9, 16 Nov 2026)

| Item | Screen | Change | Why |
|---|---|---|---|
| N2 | `#/choice-embakasi-schedule`, `#/econ-embakasi` | The 00:00–05:00 rate is a contract term from 1 Nov; October non-peak energy is billed at 0.12 | the previous "charging ended by 23:10" reason could not hold for October's volumes |
| N3 | walkthrough (Metro) | "lowest bill only because it buys 9,300 kWh less; dearer per kWh delivered" | the negative control is honest about why the bill is low |
| N5 | `#/verify-metro` | target is near-zero peak-price charging and ~62,000 kWh a month at the 00:00–05:00 rate | matches the modelled saving |
| N6 | `#/choice-kasarani-charger` rights panel | "wait" path shows "$0 now; about $240 in likely penalties and 2 broken departures" | same treatment as the Mto inverter |
| N7 | `#/plan-lakeside` | note under the crew meter when the huller is lost: the Mto visit is still needed for the inverter, so 3 of 3 stays | explains a correct figure instead of changing it |
| N8 | `#/econ-thika`, `#/econ-embakasi`, cold economics pages | Thika verdict "Within the occupancy model" when occupancy is at plan; driver amounts use one sign convention (negative = worse) on cost operators; the energy-model formula is replaced by plain words | pre-existing presentation issues |
| N9 | `tools/run-audit.sh`, README | wrapper reads CHROME, PW and optional AUDIT_LD_LIBRARY_PATH / FONTCONFIG_FILE from the environment; setup documented | the audit can be re-run on any machine |
