# Post-W6 structural app-versus-v69 audit specification

Architect plan, 2026-10-24. Baseline: merged W1-W6 on `main`; this document authorizes an audit and subsequent separately reviewed corrections, not a product change. The v69 `screen-manifest.json` has 110 IDs. The audit target below is **87 implemented IDs**, including the 26 W1 IDs in `.agent/W1-F5b-evidence/audit.json` and the 22 W2 IDs in `.agent/W2-structural-audit.md`. The other 23 IDs are named below. Reconcile this inventory against the mounted `App.tsx` routes before capture; a missing mounted target is a finding, not a silent reduction of the denominator.

## Scope and capture source

Routes below are patterns. `:siteId` is the registered mini, cold or EV Site as appropriate; `:findingId`, `:actionId`, `:caseId`, `:assetId`, `:opportunityId` and `:changeId` are exact IDs from the selected producer. Carry the producer's `from`, `to`, `known_at`, `at`, revision or selected-record query where relevant. Never substitute a mock-only ID for a missing record. The producer code names in the last column are the start points for the audit harness; each run records the actual command, fixture ID and selected URL in the index.

| v69 ID | Mounted route / view | Owning slice | Real-data producer or walkthrough mode |
| --- | --- | --- | --- |
| `sites` | `/sites` | W1-UX-02 / S1 | W1-F5b Sites stocked/empty |
| `mini` | `/sites/:siteId` | W1-UX-02 / S5-01 | W1-F5b mini priced/held/failed/unassessed |
| `foundation` | `/sites/:siteId/foundation` | W1-UX-05 / S1-03 | W1-F5b Foundation current/no-version |
| `readiness` | `/sites/:siteId/foundation/readiness` | W1-UX-05 / S1-03 | W1-F5b readiness current/no-version |
| `sld` | `/sites/:siteId/foundation/sld` | W1-UX-05 / S1-03 | W1-F5b SLD current/battery |
| `evidence` | `/sites/:siteId/evidence` | W1-UX-03 / S2-02 | W1-F5b accepted-record evidence |
| `evidence-analysis` | `/sites/:siteId/evidence?view=analysis` | W1-UX-03 / S3-02b | W1-F5b selected assessment/claim-limit |
| `dispatch` | `/sites/:siteId/performance/dispatch` | W1-UX-03 / S3-01 | W1-F5b dispatch supported/limited/refused |
| `analysis` | `/sites/:siteId/performance/analysis` | W1-UX-03 / S3-01 | W1-F5b analysis selected dispatch |
| `finding` | `/sites/:siteId/findings/:findingId` | W1-UX-02 / S4-01 | W1-F5b Finding open/stale |
| `finding-evidence` | `/sites/:siteId/findings/:findingId/evidence` | W1-UX-02 / S4-03 | W1-F5b Finding evidence |
| `finding-history` | `/sites/:siteId/findings/:findingId/history` | W1-UX-02 / S4-03 | W1-F5b Finding history |
| `sitefindings` | `/sites/:siteId/findings` | W1-UX-02 / S4-04 | W1-F5b Site Findings selected/empty |
| `financials` | `/sites/:siteId/financials` | W1-UX-02 / S4-02b | W1-F5b priced/unpriced/held |
| `assumptions` | `/sites/:siteId/financials/assumptions` | W1-UX-02 / S4-08 | W1-F5b selected price/history |
| `recommendation` | `/sites/:siteId/findings/:findingId/recommendation` | W1-UX-04 / S6-01b | W1-F5b accepted/held/unavailable |
| `changes` | `/sites/:siteId/foundation/changes/:changeId` (also bare no-selection state) | W1-UX-04 / S6-01b | W1-F5b change applied/no selection |
| `action-overview` | `/sites/:siteId/actions/:actionId` | W1-UX-04 / S6-01b | W1-F5b recorded Action |
| `action-execution` | `/sites/:siteId/actions/:actionId/execution` | W1-UX-04 / S6-01b | W1-F5b applied/failed execution |
| `action-history` | `/sites/:siteId/actions/:actionId/history` | W1-UX-04 / S6-01b | W1-F5b Action events |
| `action-plan` | `/sites/:siteId/actions/:actionId/plan` | W1-UX-04 / S6-02b | W1-F5b pass/guardrail verification |
| `action-evidence` | `/sites/:siteId/actions/:actionId/evidence` | W1-UX-04 / S6-02b | W1-F5b pass/guardrail verification |
| `verification` | `/sites/:siteId/actions/:actionId/verification` | W1-UX-04 / S6-02b | W1-F5b verified/historical/guardrail |
| `sitework` | `/sites/:siteId/work` | W1-UX-04 / S6-03 | W1-F5b selected Action list |
| `health` | `/sites/:siteId/health` | W1-UX-05 / S7-01b | W1-F5b source-health selected |
| `asset` | `/sites/:siteId/assets/:assetId` | W1-UX-05 / S7-01b | W1-F5b Kobo battery Unknown |
| `cold-foundation` | `/sites/:siteId/foundation` | W2-01 | W2-01 cold Foundation replay |
| `cold-readiness` | `/sites/:siteId/foundation/readiness` | W2-01 | W2-01 cold readiness replay |
| `cold-sld` | `/sites/:siteId/foundation/sld` | W2-01 | W2-01 cold topology replay |
| `temperature` | `/sites/:siteId/performance/temperature` | W2-03 | W2-02 cold excursion/normal; W2-03 selected assessment |
| `coldbackup` | `/sites/:siteId/performance/backup` | W2-03 | W2-02 cold start chain; W2-03 assessment |
| `cold-finding` | `/sites/:siteId/findings/:findingId` | W2-03 | W2-03 selected backup Finding |
| `cold-findings` | `/sites/:siteId/findings` | W2-03 | W2-03 selected/empty cold index |
| `cold` | `/sites/:siteId` | W2-04 | W2-04 selected cold Overview |
| `cold-evidence` | `/sites/:siteId/evidence` | W2-04 | W2-04 selected accepted evidence |
| `cold-evidence-analysis` | `/sites/:siteId/evidence?view=analysis` | W2-04 | W2-04 selected record/limit read |
| `cold-financials` | `/sites/:siteId/financials` | W2-04 | W2-04 unpriced consequence |
| `cold-assumptions` | `/sites/:siteId/financials/assumptions` | W2-04 | W2-04 selected cold assumptions |
| `ev-foundation` | `/sites/:siteId/foundation` | W2-05a | W2-05a EV topology replay |
| `ev-readiness` | `/sites/:siteId/foundation/readiness` | W2-05a | W2-05a EV readiness replay |
| `ev-sld` | `/sites/:siteId/foundation/sld` | W2-05a | W2-05a EV topology replay |
| `sessions` | `/sites/:siteId/performance/sessions` | W2-06 | W2-05b EV session producer; W2-06 selected assessment |
| `ev-finding` | `/sites/:siteId/findings/:findingId` | W2-06 | W2-06 interrupted-session Finding |
| `ev` | `/sites/:siteId/ev` | W2-07 | W2-07 selected EV Overview |
| `ev-evidence` | `/sites/:siteId/ev/evidence` | W2-07 | W2-07 selected accepted EV evidence |
| `ev-evidence-analysis` | `/sites/:siteId/ev/evidence/analysis` | W2-07 | W2-07 selected record/limit read |
| `ev-financials` | `/sites/:siteId/ev/financials` | W2-07 | W2-07 selected gross-tariff scenario |
| `ev-assumptions` | `/sites/:siteId/ev/financial-assumptions` | W2-07 | W2-07 selected EV assumptions |
| `findings` | `/findings` | W3-01 | W3-01 estate Finding/Action root fixture |
| `findings-cost` | `/findings/cost` | W3-01 | W3-01 cost lens |
| `findings-risks` | `/findings/risks` | W3-01 | W3-01 risk lens |
| `findings-opportunities` | `/findings/opportunities` | W3-01 | W3-01 opportunity lens |
| `actions` | `/actions` | W3-01 | W3-01 estate Action fixture |
| `globalevidence` | `/evidence` | W3-02 | W3-02 exact selected estate evidence |
| `globalfinancials` | `/financials` | W3-02 | W3-02 exact selected estate money |
| `portfolio` | `/portfolio` | W3-03 | W3-03 same-cutoff portfolio producer |
| `sitework-incidents` | `/sites/:siteId/work/incidents` | W4-01 | W4 case producer, selected Site cases |
| `sitework-maintenance` | `/sites/:siteId/work/maintenance` | W4-01 | W4 case producer, selected Site cases |
| `renewable` | `/sites/:siteId/performance/renewable` | W4-02 | `tools/s402*` mini-depth cases |
| `service` | `/sites/:siteId/performance/service` | W4-02 | `tools/s402*` mini-depth cases |
| `fuel` | `/sites/:siteId/performance/fuel` | W4-02 | `tools/s402*` mini-depth cases |
| `backup` | `/sites/:siteId/performance/backup` | W4-02 | `tools/s402*` mini-depth cases |
| `scenarios` | `/sites/:siteId/financials/scenarios` | W4-03 | `tools/w403_mini_decisions_walkthrough.py` |
| `alternatives` | `/sites/:siteId/findings/:findingId/alternatives` | W4-03 | W4-03 mini decisions walkthrough |
| `opportunity-finding` | `/sites/:siteId/opportunities/:opportunityId` | W4-03 | W4-03 renewable opportunity producer |
| `cooling` | `/sites/:siteId/performance/cooling` | W5-01a | W5-01 cold selected-depth replay |
| `cold-health` | `/sites/:siteId/health` | W5-01a | W5-01 cold health replay |
| `cold-scenarios` | `/sites/:siteId/financials/scenarios` | W5-01b | W5-01 authored scenario producer |
| `cold-work` | `/sites/:siteId/work` | W5-02a | `tools/w502_cold_work_walkthrough.py` Action mode |
| `cold-work-incidents` | `/sites/:siteId/work/incidents` | W5-02b | W502 selected incident cases |
| `cold-work-maintenance` | `/sites/:siteId/work/maintenance` | W5-02b | W502 selected maintenance cases |
| `cold-action` | `/sites/:siteId/actions/:actionId/verification` | W5-02c | W502 declared-criteria Action mode |
| `availability` | `/sites/:siteId/performance/availability` | W5-03a | W5-03 selected EV depth producer |
| `energy` | `/sites/:siteId/performance/energy` | W5-03a | W5-03 selected meter-sample producer |
| `ev-health` | `/sites/:siteId/health` | W5-03b | W5-03 selected EV health producer |
| `ev-scenarios` | `/sites/:siteId/ev/financials/scenarios` | W5-03b | W5-03 authored EV scenario producer |
| `ev-work` | `/sites/:siteId/work` | W5-04a | `tools/w504_ev_work_walkthrough.py` Action mode |
| `ev-work-incidents` | `/sites/:siteId/work/incidents` | W5-04b | W504 selected incident cases |
| `ev-work-maintenance` | `/sites/:siteId/work/maintenance` | W5-04b | W504 selected maintenance cases |
| `ev-action` | `/sites/:siteId/actions/:actionId/verification` | W5-04c | W504 declared-criteria Action mode |
| `incidents` | `/incidents` | W6-01a | W6-01a selected global case fixture |
| `maintenance` | `/maintenance` | W6-01b | W6-01b corrective fixture |
| `maintenance-preventive` | `/maintenance/preventive` | W6-01b | W6-01b authored preventive fixture |
| `wr-overview` | `/maintenance/requests/:caseId?site_id=:siteId` | W6-01c | W6-01c exact work-request fixture |
| `wr-record` | `/maintenance/requests/:caseId/record?site_id=:siteId` | W6-01c | W6-01c performed-record fixture |
| `wr-history` | `/maintenance/requests/:caseId/history?site_id=:siteId` | W6-01d | W6-01d event-history fixture |
| `oprecords` | `/operational-records` | W6-01e | W6-01e selected operational-record fixture |

**Outside W1-W6:** `lab` is a separate Simulator Lab surface, not an operator W1-W6 screen. The remaining 22 manifest IDs have no W1-W6 product implementation: `incident`, `workverification`, `assets`, `cold-recommendation`, `ev-findings`, `ev-recommendation`, `cold-finding-excursion`, `assets-warranty`, `asset-register`, `asset-overview`, `site-create-form`, `site-create-template`, `site-batch-upload`, `site-setup-history`, `asset-performance`, `asset-config`, `asset-edit`, `asset-work`, `asset-evidence`, `asset-warranty`, `settings-policies`, `settings-tenant`. **Inventory gate:** the auditor must prove `87 + 23 = 110` against the manifest before running. Any screen found mounted or represented by a W1-W6 producer moves into the audit target. An unavailable tab inside an implemented page stays in scope as a state of that page. Do not capture a fake destination.

## Method and evidence contract

1. Freeze main SHA, manifest hash, selected fixture IDs, clock/cutoff, API and frontend URLs, capture tool revisions and viewport configuration. Use the v69 `index.html` render at **1440 and 390 CSS pixels** as the visual authority; `browser-review.json` is a baseline smoke report, not proof of app parity. `render-reference.ps1` renders an existing PDF page when that format is used. Use `tools/measure-mock-panels.mjs` or the existing rendered-panel measurements for panel budgets.
2. Run existing W1 and W2 producers and capture tools, W3 estate, W4 mini, W502, W504 and W6 fixtures by their existing modes. Extend a capture wrapper only to drive URLs, wait for stable content, take screenshots and measure DOM; keep it **capture-only**. It may not mutate product state, fabricate API data, seed special display text, or bypass a refusal. Seed/replay remains in the already reviewed producer/walkthrough mode. Serialize shared Vite/cache use, allocate separate ports and DBs, stop only spawned PIDs, and drop only audit-owned DBs.
3. For every screen, compare exact panel count, order and titles; within each panel compare rows, columns, chips, links and disclosure order. Compare grid/stack layout, spacing and measured heights, font family/size/weight/line-height, `.prose`, colours against named tokens, borders, status tones, sticky headers and overflow. Check populated, empty, pending/historical and refused states that the producer can actually yield. At 1440 and 390 verify no page horizontal overflow, no clipped material text, readable table scrolling, stable focus order and short-page header height. A mock value is illustrative; compare the structure while confirming app values come from selected real records.
4. Write one machine-readable and one human-readable index. A **pair** is `(screen ID, case, width)` with app and mock images; at least one populated/representative case at each width for every in-scope ID: **174 minimum pairs**. Further states add pairs, never replace the representative pair. Each pair records route, producer command/mode, selected IDs/window, panel titles/order, per-panel app/mock heights and ratio, colour/font measurements, overflow, screenshot paths, findings and reviewer verdict. The HTML index presents app beside mock at each width. Reuse `.agent/W1-F5b-evidence/index.html`/`audit.json` and its 168 pairs as the format precedent, and W2-F's 22-screen re-audit as the structural precedent; all old screenshots are historical until recaptured at the frozen SHA. A panel over approximately 1.3x the mock needs a measured reason and a reviewed ruling, never an automatic pass.

## Classification and carried checks

For **every** observed difference, the Architect records exactly one disposition: (a) existing register ruling with its `Rxx` ID and current built/resolved status verified; (b) new genuine departure, assigned D1, D2, D4, D5 or D6 with a new row in `.agent/mock-departure-register.md`, visible `MOCK DEVIATION Dn` label and owner note; or (c) D3 structural defect with a register row and a fix slice, then recapture. D3 is never an accepted exception. Existing D3 rows R22/R23/R24/R37/R38/R60 must be checked for closure or withdrawn status. D1 is an honest unavailable capability, D2 a proposed improvement needing owner approval/reversal, D4 replacement of false placeholder facts, D5 a named build-order expiry, and D6 a rare documented constraint with alternatives considered. Unlabelled differences fail review. The register header's old count is stale; derive counts from distinct rows and report open/resolved/withdrawn separately.

Mandatory carried UI-pass checks from `.ai/MILESTONE_REVIEW_BACKLOG.md`: `.prose` sentences now 14 px against mock 12 px; tall dark shell header (~275-335 px) on short 390 pages including refused and cold Action; `1 incidents` / `1 maintenance` plural grammar; raw `c1 · EV_CONNECTOR` asset label; and one generic window error for distinct invalid inputs in `domainActionClient.ts`. Treat each as a finding on every affected screen/state, classify by the observed mismatch, and assign a shared fix owner. Include W6-01a 390 refused, W5-01a cold refused, W5-02c K4 and W5-04b/c captures. Check whether the 390 Window control's extra height is an existing R88/R112 departure before inventing a new row. Review the other carried UI Lows in the same backlog for observable structure, copy and clipping; do not turn non-UI test/environment Lows into visual departures.

## Audit batches and order

Each batch owns **at most six IDs** and its own evidence subdirectory. The list is exhaustive over the 87-ID inventory above. Two agents maximum at once, only on disjoint read/capture work; shared shell, register, index and any subsequent shared-code edits are serialized. No agent edits product code during the audit. One Architect reconciles overlapping findings and assigns register IDs.

| Order | Batch / shared component | IDs |
| --- | --- | --- |
| 1 | W1 shell/Foundation | `sites`, `foundation`, `readiness`, `sld`, `changes`, `asset` |
| 2 | W1 Overview/Evidence | `mini`, `evidence`, `evidence-analysis`, `dispatch`, `analysis`, `health` |
| 3 | W1 Finding/money | `finding`, `finding-evidence`, `finding-history`, `sitefindings`, `financials`, `assumptions` |
| 4 | W1 Action/work | `recommendation`, `action-overview`, `action-execution`, `action-history`, `action-plan`, `action-evidence` |
| 5 | W1 verification | `verification`, `sitework` |
| 6 | W2 cold Foundation/assessment | `cold-foundation`, `cold-readiness`, `cold-sld`, `temperature`, `coldbackup`, `cold-finding` |
| 7 | W2 cold Site | `cold-findings`, `cold`, `cold-evidence`, `cold-evidence-analysis`, `cold-financials`, `cold-assumptions` |
| 8 | W2 EV Foundation/assessment | `ev-foundation`, `ev-readiness`, `ev-sld`, `sessions`, `ev-finding` |
| 9 | W2 EV Site | `ev`, `ev-evidence`, `ev-evidence-analysis`, `ev-financials`, `ev-assumptions` |
| 10 | W3 estate indices | `findings`, `findings-cost`, `findings-risks`, `findings-opportunities`, `actions` |
| 11 | W3 estate composition | `globalevidence`, `globalfinancials`, `portfolio` |
| 12 | W4 mini depth | `renewable`, `service`, `fuel`, `backup` |
| 13 | W4 decisions/cases | `scenarios`, `alternatives`, `opportunity-finding`, `sitework-incidents`, `sitework-maintenance` |
| 14 | W5 cold depth/work | `cooling`, `cold-health`, `cold-scenarios`, `cold-work` |
| 15 | W5 cold cases/Action | `cold-work-incidents`, `cold-work-maintenance`, `cold-action` |
| 16 | W5 EV depth/work | `availability`, `energy`, `ev-health`, `ev-scenarios`, `ev-work` |
| 17 | W5 EV cases/Action | `ev-work-incidents`, `ev-work-maintenance`, `ev-action` |
| 18 | W6 global lists | `incidents`, `maintenance`, `maintenance-preventive`, `oprecords` |
| 19 | W6 work request | `wr-overview`, `wr-record`, `wr-history` |

## Fix slices, walkthrough index and gates

After the audit ledger is reviewed, create task branches from the frozen/rebased main, with one fix slice per shared component seam: shell and shared typography/copy; W1 mini/Action; W2 cold; W2 EV; W3 estate; W4 mini; W5 cold Work; W5 EV Work; W6 global Work. Merge only reviewed slices and recapture impacted screens at the merged SHA. Do not split one shared file between concurrent builders. Each D3 fix card names exact panels/order, data source, states, files, test and paired captures. The Architect rules layout caps **once** from worst-case fixtures (five 160-character rows where applicable), declares an explicit all-disclosures-open exemption, and states the fallback if remeasurement exceeds a cap: adjust layout/scroll or return to Architect for a revised measured cap before merge. A short mock row alone cannot set a production cap (lesson 15). Run focused tests for touched behavior; one quiet full suite for a behavior round if required, after the line-ending check in lesson 14. Reviewers verify the exact register row and current captures; D3 remains open until corrected.

The final owner index has a screen-order table linking each implemented ID to its route, representative 1440/390 pairs, producer state and pass status. Below it, six category sections D1-D6 list each **still visible** departure by register ID, screen, plain-language “mock shows / app shows / why” text, screenshot links, status and owner decision needed. D3 lists corrected defects with before/after proof and says none remain open; D5 names its resolving unit and whether expired; D6 gives alternatives. Include a per-screen departure flag/link beside each pair so the owner can walk screen by screen while the category sections remain the decision index. Historical/withdrawn register rows are linked as history, not presented as live differences.

**Call the owner only when:** manifest coverage is reconciled to 110 IDs; all 87 implemented IDs have current-SHA app/mock pairs at both widths plus relevant missing states; panel order/title and 1440/390 layout checks have a reviewed verdict; every difference is classified and registered or fixed; every open D3 is closed with a reviewed fix and recapture; shared UI-pass checks are resolved or have a justified non-D3 ruling; producer/capture tools remain capture-only; affected focused checks and required guards pass; the merged final SHA is recorded; and the owner index is navigable with plain-language D1-D6 flags. Owner approval of D2/reversal and prioritisation of D1 occur during that walkthrough, not as a reason to leave the audit incomplete.
