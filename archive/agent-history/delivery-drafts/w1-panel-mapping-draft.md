# W1 panel-to-gate mapping draft — 58 of 58

Planning only, for the 21 proposed W1 manifest IDs in the owner strategy. Keys are `screen_id:panel_index` in `v69-panel-contracts.json`; title is a check against that file. **All listed gates are AND dependencies**, including transitive `requires`. A task closeout does not make a panel real without the named read, UI, persisted/accepted data, lineage, rendered-claim review and applicable V-01 interaction acceptance. Product tier and core choices remain pending owner. `B` means a bounded supported path exists in the merged S1/S2-01 code, subject to contract/review reconciliation; `G` means a necessary gate or claim is still missing. `B` is not registry `real`.

Existing registry nodes retain their IDs. Proposed new nodes below need Architect contract and registry/schema review before addition; they are **not** accepted technical decisions. Every proposed data node requires its named architecture contract and persistence node. `UI-*`/`R-*`/`D-*` are compact draft IDs, not current registry IDs. Where the panel contains both a supported slice and a mock-only section, the status is `G`; a narrower core claim can be chosen explicitly later.

## Proposed gates used in the table

| Code | Exact AND set; proposed IDs explained here |
| --- | --- |
| F | `A-S1-foundation + I-S1-01 + R-foundation + UI-foundation + D-foundation-version` (new read/UI/data gates; source is persisted Foundation revision) |
| BIND | `F + A-S1-bindings + I-S1-02 + R-bindings + UI-readiness + D-bindings` |
| TOPO | `BIND + R-topology + UI-sld` |
| LAB | `A-lab-registered-basis + I-S2-01a + I-lab-registered-basis + R-lab + UI-lab + D-lab-run` |
| EDGE | `LAB + A-S2-evidence + I-S2-01b + I-edge-outbox + I-S2-01c + I-edge-diagnostics-publish + R-gateway-local + UI-lab-gateway + D-gateway-local` |
| ACCEPT | `EDGE + I-S2-02 + I-accepted-evidence-store + R-evidence + UI-evidence + D-accepted-envelope` (exact accepted batch/decision IDs, not Lab truth) |
| HEALTH | `ACCEPT + I-edge-diagnostics-store + A-evidence-shared-projections + R-source-health + UI-source-health + D-central-diagnostics` (ordinary central diagnostics; S7's `D-edge-health-cases` adds outage/pressure variants, not a prerequisite for S2 Evidence) |
| CAP | `ACCEPT + A-evidence-shared-projections + R-capability + UI-capability + D-coverage-window` |
| DIS | `ACCEPT + A-S3-dispatch + I-S3-01 + I-sim-dispatch-cases + R-dispatch + UI-dispatch + D-dispatch-window` |
| FIND | `DIS + A-finding-episode + A-claim-work-routes + I-S4-01 + I-finding-store + I-finding-read + I-finding-ui + D-finding-revisions` |
| MONEY | `FIND + A-S4-financial + A-actor-identity + I-S4-02 + R-financial + UI-financial + D-financial-revision + D-assumption-revision` |
| OVER | `DIS + FIND + MONEY + A-S5-overview + I-S5-01 + R-site-overview + UI-site-overview + D-overview-window` |
| WORK | `FIND + A-action-lifecycle + A-actor-identity + A-claim-work-routes + I-S6-01 + I-action-store + I-action-read + I-action-ui + D-action-records` |
| VERIFY | `WORK + A-S6-verification + I-S6-02 + I-sim-verification-cases + D-verification-window + R-verification + UI-verification` |
| ASSET | `HEALTH + A-S7-health + I-S7-01 + R-asset-health + UI-asset-health`; a physical battery claim additionally needs `D-battery-observation` and its accepted-envelope lineage, while explicit Unknown is supported without it |

New `R-*` nodes are reviewed read projections, `UI-*` nodes are reviewed routes/panels, and `D-*` nodes are persisted or accepted fixtures with lineage. Their architecture prerequisites must be made explicit when they enter the registry. The current pilot lacks these non-Claims/Work nodes, so this is a proposed mapping, not a claim the checker already accepts it. For all claim panels `V-01` and exact owner core approval are separate product/visual gates, not technical `requires` nodes. A structural panel may omit data only after an explicit `structural: true` ruling; none is silently designated structural here.

## Complete mapping

| Panel | Panel contract title | Status | AND gates beyond the code above / claim limit |
| --- | --- | --- | --- |
| `sites:1` | Site inventory | B | F + `R-site-directory + UI-sites`; Site identity and registered status only, no estate claims. |
| `sites:2` | In setup | G | `A-onboarding-identity + I-onboarding-store + D-onboarding-records + R-site-directory + UI-sites`; setup event not S1 scope. |
| `foundation:1` | Configured topology | B | TOPO; selected version and bound components only. |
| `foundation:2` | Identity & operating obligations | B | F; time-valid registered facts only. |
| `foundation:3` | Time-valid control configuration | B | F; effective revision and explicit missing properties. |
| `readiness:1` | Readiness and commissioning evidence | B | BIND; configuration readiness, no source health inference. |
| `readiness:2` | Gateway status · GW-MG-01 | G | BIND + HEALTH; centrally received status needed for Site claim. |
| `readiness:3` | Connected sources | G | BIND + HEALTH; central freshness/cadence, not only bindings. |
| `readiness:4` | Effect on readiness and confidence | G | BIND + CAP; accepted evidence and rule-specific coverage. |
| `sld:1` | Kobo Mini-grid · AC-coupled mini-grid | B | TOPO; registered topology only. |
| `sld:2` | What each part does | B | TOPO; configured role descriptions only, no dynamic performance. |
| `lab:1` | Selected canonical envelope | B | EDGE; local V3 bytes and staged state; central acceptance via ACCEPT if shown. |
| `lab:2` | Truth versus observed | B | LAB + `R-lab-truth-compare + UI-lab`; comparison stays in Lab, never product Evidence. |
| `lab:3` | Release and ingestion | G | EDGE + ACCEPT + `R-batch-progress + UI-lab`; ingestion receipt/reload awaits S2-02. |
| `lab:4` | What never crosses | B | LAB + EDGE + `R-lab-truth-compare + UI-lab`; explicit boundary/explanation, no product truth store. |
| `evidence:1` | What we can conclude now | G | CAP; evidence quality/claim ceiling, not unbuilt dispatch conclusion. |
| `evidence:2` | Data sources · data quality, not equipment condition | G | HEALTH; central diagnostic and accepted report times. |
| `evidence:3` | Most useful next evidence | G | CAP + `R-next-evidence`; only rule-backed missing role, no invented recommendation. |
| `evidence-analysis:1` | Accepted records behind the conclusions | G | ACCEPT + `R-evidence-index + UI-evidence-analysis`; exact decision/envelope IDs and duplicate/conflict states. |
| `evidence-analysis:2` | How a claim limit is set | G | CAP + `R-claim-lineage + UI-evidence-analysis`; rule, missingness and accepted sources. |
| `dispatch:1` | Sources and 15-minute blocks | G | DIS; selected-window classified intervals plus gaps. |
| `dispatch:2` | Selected block · 14:20–14:35 | G | DIS + `R-dispatch-interval`; exact selected interval/revision. |
| `dispatch:3` | Accepted sample coverage | G | DIS + CAP; source and role coverage, conflicting samples visible. |
| `analysis:1` | Constraint comparison | G | DIS + `R-dispatch-interval + UI-dispatch-analysis`; bounded analytic only. |
| `analysis:2` | Bounded fuel calculation | G | DIS + MONEY + `R-fuel-calculation`; cannot show money before S4 assumptions. |
| `analysis:3` | Coverage, confidence and alternatives | G | DIS + CAP + `R-claim-lineage + UI-dispatch-analysis`; alternatives require explicit rule contract. |
| `finding:1` | What happened | G | FIND; existing pilot gate `I-finding-read + I-finding-ui + D-finding-revisions`. |
| `finding:2` | What limits this conclusion | G | FIND + CAP; pilot gate plus explicit missing/late source limit. |
| `finding:3` | What to do next | G | WORK; pilot gate `I-finding-ui + I-action-read + D-action-records`; before S6 show honest no-Action state. |
| `finding:4` | Where to look next | G | FIND + `R-claim-lineage`; pilot gate plus exact assessment/evidence navigation. |
| `finding-evidence:1` | Evidence bundle · F-104 | G | FIND + ACCEPT + `R-finding-evidence + UI-finding-evidence`; selected revision and bundle membership. |
| `finding-evidence:2` | Inspect source lineage | G | FIND + ACCEPT + `R-claim-lineage + UI-finding-evidence`; exact source envelopes. |
| `financials:1` | What happened → what it means in money | G | MONEY; bounded quantity × versioned assumption, with exclusions. |
| `financials:2` | Assumptions in use | G | MONEY; author/provenance and effective revision. |
| `financials:3` | Trade-offs and exclusions | G | MONEY + `R-money-exclusions`; unsupported comparison stays Unknown. |
| `assumptions:1` | Financial assumptions | G | MONEY + `UI-assumptions`; actor/versioned edits. |
| `assumptions:2` | Impact preview | G | MONEY + `R-assumption-preview + UI-assumptions`; hypothetical preview labelled, not observed money. |
| `assumptions:3` | Interpretation history | G | MONEY + `R-assumption-history + UI-assumptions`; immutable revisions. |
| `mini:1` | What happened in the selected hour | G | OVER + `R-operational-timeline`; accepted selected-window events. |
| `mini:2` | Operating context | G | OVER; scope and period stated. |
| `mini:3` | Needs attention | G | OVER + `I-finding-index + A-finding-index + D-finding-revisions`; Site-scoped Finding list or honest empty state. |
| `mini:4` | Bounded money consequence | G | OVER + MONEY; same revision/assumption as detail. |
| `mini:5` | Next step | G | OVER + WORK; Action/recommendation only when persisted, otherwise no-action state. |
| `changes:1` | Change and effect | G | WORK + VERIFY + `R-configuration-change + UI-changes`; applied revision and later outcome kept distinct. |
| `changes:2` | Decision path | G | WORK + VERIFY + `R-verification-plan + UI-changes`; plan fixed before outcome. |
| `recommendation:1` | Proposed intervention | G | FIND + WORK + `R-recommendation + UI-recommendation`; proposal grounded in Finding. |
| `recommendation:2` | Declare success before evaluating | G | WORK + `R-verification-plan + UI-recommendation`; target/guardrails versioned before later run. |
| `recommendation:3` | Evidence needed to verify | G | WORK + CAP + `R-verification-plan + UI-recommendation`; missing inputs explicit. |
| `verification:1` | Target and guardrails evaluated together | G | VERIFY; failed guardrail is a failed outcome, even if target improves. |
| `verification:2` | Activity evidence | G | VERIFY + `R-action-events`; actor, change artifact, event provenance. |
| `verification:3` | Outcome evidence | G | VERIFY + ACCEPT + `R-claim-lineage`; later window and accepted envelopes. |
| `sitework:1` | Actions at this site | G | WORK; existing pilot gate `I-action-read + I-action-ui + D-action-records`. |
| `action-overview:1` | Action scope | G | WORK + `R-action-detail + UI-action-overview`; stable route, selected baseline and actor. |
| `health:1` | Physical asset condition | G | ASSET + `D-edge-health-cases` for the S7 demo; only supported battery observation, otherwise Unknown; no remaining-life claim. |
| `health:2` | Data sources · data quality, not equipment condition | G | HEALTH + `D-edge-health-cases + UI-site-health`; central diagnostic provenance. |
| `asset:1` | Observed reserve and power exposure | G | ASSET + `D-battery-observation` for a positive claim; otherwise explicit Unknown. |
| `asset:2` | Interpretation and next evidence | G | ASSET + CAP; capacity inference withheld absent contract/input. |
| `asset:3` | Condition evidence and claim boundary | G | ASSET + `R-asset-health`; no unsupported replacement exposure. |

## Mapping gaps to resolve before owner core choice

The table has a proposed gate path for every panel, but most paths contain new, unreviewed node IDs. The **unmappable claim portions today** are `sites:2` (onboarding outside W1), `analysis:3` alternatives (no bounded alternative contract), `financials:3` cross-option trade-offs (no comparability contract), and `asset:1-3` physical battery condition if no causal accepted battery report exists. These cannot be selected as real W1 core panels on the current graph. `mini:3` also needs a Site FindingIndex contract beyond the S5 packet; `mini:5` needs S6 Action and may lag S5. `readiness:2-4` need a ruling on where configuration readiness ends and central source/capability health begins. Owner core-panel selection must name the supported *slice* or wait for those gates; a screen-level `Real with honest gaps` cannot quietly promote its other panels.

Before implementing this draft, the Architect must validate each proposed ID, area, scope and AND branch against actual S1/S2-02 accepted reads and the panel contract. The checker should fail closed for any owner-approved core key missing a reviewed mapping. It should publish unresolved ancestors and distinct panel paths; `delivery_plan.enables` can carry planning benefit for adjacent work without making a technical gate pass.
