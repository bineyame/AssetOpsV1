# v6.9 dependency registry pilot: Claims and Work

**Architect planning overlay · 2026-10-07; revised after dependency review.** The [registry](v69-dependency-registry-pilot.json) names dependency *kind*, *subject area* and *leverage inputs* separately. The [subject-area briefs](v69-subject-area-briefs.json) assign all 88 mock models and all 110 screens a primary home across 11 product areas, plus one cross-cutting simulation/edge enabler. It supplements the [screen ledger](v69-screen-ledger.json), [model homes](v69-model-homes.json) and [panel contracts](v69-panel-contracts.json). Only the seven Claims/Work pilot screens have complete panel-level node gates; all other panels remain governed by the ledger's unresolved gates and cannot be promoted from the area briefs alone. The S1 Foundation contract and the recorded S2 edge/scenario choices are resolved architecture nodes; no implementation or data node is resolved, no panel is claimed real, and no owner tier or priority is inferred. S1-01 remains the active implementation task.

## Contract for extending the registry

An **architecture** node records an accepted decision or projection/route contract with a decision link as evidence. An **implementation** node records a built capability only after its task has an approved independent review. A **data** node records a source-to-claim fixture or operational record only after normal ingestion, reload and lineage checks. A **product** node records the owner's tier, priority, core panels or Drop decision. Product nodes influence selection and weighting; they are never prerequisites that satisfy a technical gate.

Every implementation and data node has an architecture prerequisite. The thirteen S1–S7 task nodes record the current queue, but `requires` contains **technical prerequisites only**. `sequenced_after` records the chosen task order and is excluded from distance, reach and readiness. The checker validates both graphs and their combined acyclicity. Implementation layers distinguish product persistence, read projection, route/UI, edge acquisition, simulator producers and ingestion. Data depends directly on product persistence, so records can be seeded before a screen exists. A layered implementation node assigned to an S task and that task's closeout node must share the same status; a panel cannot appear ready halfway through the task's review. Every claim-bearing panel requires a read projection, UI and data node; a purely structural panel must explicitly declare `structural: true`. `real` requires all transitive technical prerequisites to be resolved and the rendered claim to be reviewed. `withheld` requires a visible reason and recorded owner approval. Otherwise it is `gap`. The ledger's `proposed_fidelity_tier` remains a proposal. `Real with honest gaps` requires all owner-designated core panels to be real. `Real` requires every panel to be real or owner-approved withheld, plus interaction and navigation acceptance. No empty `core_panels` list means approval while the product node is pending.

Keep model names in `satisfies_models` when useful for traceability, but do not require every architecture node to match a model. Actor identity, route contracts, currency/period comparability and domain role sets are first-class decisions. A subject-area brief is the Architect's decision unit; the Planner may then cut one or more reviewable vertical tasks. The registry stays a planning overlay until a task packet explicitly adopts its nodes and checks their evidence.

## Worked subject-area brief

| Area | Product question | Mock models and shared contracts | Decisions and evidence | Screens in this pilot | Owner choice |
| --- | --- | --- | --- | --- | --- |
| Claims | Which revisioned Finding is being shown, with what evidence and route? | `Finding`, `FindingRevision`, `FindingIndex`; Finding and evidence detail | Decide episode/revision/recurrence and full `FindingIndex` consumers; ingest a multi-revision episode, recurrence and missing/late variant | `finding`, `sitefindings`, `findings` | Global Findings tier, priority and core panels pending |
| Work and verification, Action detail | What Action was taken, and where does it lead? | `Action`, `ActionEvent`, `ActionIndex`; shared route and actor contract | Decide event authority, actor identity and Site/global index shape before first consumers; S6 still supplies bounded Action/verification records | `sitework`, `actions` | Global Actions breadth remains unapproved; S6 bounded portion stays in queue |
| Work and verification, cases | What Incident, request, performed maintenance or operational record exists, and who attested it? | `Incident`, `MaintenanceWorkRequest`, `MaintenanceRecord`, `MaintenancePlan`, `WorkEvent`, `OperationalRecord`, `MaintenanceIndex` | Decide identities/lifecycle/correction in one pass; prove attested records through reload and lineage | `incidents`, `maintenance` | Owner decides whether these roots merit implementation, deferment or Drop |

All 11 rendered panels of these seven screens are linked. Product choices are layered: `P-claims-area` and `P-work-area` supply area defaults; `P-finding`, `P-sitework` and `P-work-cases` are screen exceptions. `P-work-cases` deliberately spans mini-grid, cold-chain and EV Incident/Maintenance destinations, so one owner choice can defer or Drop that family without blocking each domain's assessment screens. An exception takes precedence over its area default. The checker requires exactly one effective choice per screen and rejects duplicate defaults or exceptions. A recorded `Real with honest gaps` choice must name at least one core panel for every screen it effectively governs. This is five pending owner choices for seven pilot screens; across the full inventory there are 11 area defaults and three exception choices. Add further exceptions only when a screen genuinely needs a different tier, priority or core-panel set. The sample is **not** the complete set of consumers. The manifest and panel inventory remain authoritative for other screens. In particular, no panel here is promotable merely by closing one index: `findings` and `actions` also require estate scope rules and a root implementation. The shared projection decisions must enumerate their cold-chain, EV and estate consumers before their contracts are frozen.

## Eleven subject-area briefs

The [machine-readable briefs](v69-subject-area-briefs.json) list each area's question, owned models, primary screens, decision and projection nodes, fixture gate and pending owner choice. Counts below are recalculated from that explicit ownership. **Screens touched overlap** because a screen can consume models from several areas; only primary screen and model assignments are one-to-one. Configuration, Evidence, Money, Mini-grid, Onboarding, Assets, Estate, Cold-chain and EV are now briefed at area level. Their panel gates remain to be refined in reviewable waves.

| Area | Models | Screens touched | Panels in primary screens | Decision focus |
| --- | ---: | ---: | ---: | --- |
| Work & verification | 17 | 37 | 24 | Action versus Incident/request/record identity; verification and attestation. |
| Evidence & source health | 12 | 28 | 9 | Accepted lineage, source freshness, readiness and shared projection consumers. |
| Claims | 7 | 23 | 16 | Finding episode, revision, index and exact drill-down. |
| Money | 5 | 17 | 9 | Assumption revisions, comparable currency/periods and scenario basis. |
| Mini-grid analytics | 10 | 12 | 25 | Dispatch plus service, renewable, fuel and backup rules. |
| Configuration | 8 | 12 | 9 | Time-valid Foundation, role sets and configured topology. |
| Onboarding & admin | 7 | 10 | 19 | Draft/import lifecycle, tenant authority and audited policy. |
| Assets & life | 5 | 8 | 34 | Registration, battery health, warranty and asset indexes. |
| Estate aggregation | 7 | 8 | 8 | Aligned windows, coverage, overlap and Portfolio projections. |
| Cold-chain analytics | 4 | 7 | 60 | Domain roles, excursion/cooling rules and optional work views. |
| EV analytics | 6 | 4 | 45 | Session/availability rules, power limits and optional work views. |

The cold-chain and EV *primary* screen counts are much larger than their model-touched counts because they reuse shared Evidence, Configuration, Claims, Money and Work models. Each has its own role, analytic and source-backed fixture gate. Work-case projections are optional branches, so a decision to defer Incidents or Maintenance does not block the domain assessment path.

### Simulation and edge enabling area

This twelfth brief owns no primary mock models, screens or product tier. Its nodes are technical/data prerequisites consumed by the 11 product areas. [The Architect decision](../../../.ai/DECISIONS.md) fixes three S2 cuts: `I-lab-registered-basis` in S2-01a, `I-edge-outbox` and `I-edge-simulated-adapter` in S2-01b, and `I-edge-diagnostics-publish`/`I-edge-fault-scenarios` in S2-01c. S2-02 owns central `I-accepted-evidence-store` and `I-edge-diagnostics-store`. `A-edge-diagnostics` now has a table and API contract in the technical design, with `D-edge-health-cases` required for S7. `A-edge-batch-signature` records a **defer** decision: signing and signature verification nodes stay open outside the queue; the pilot uses registered TLS credentials, canonical digest and exact-byte retry.

`A-demo-scenarios` feeds S3 complete/missing/contradictory/late cases and S6 two-run old/new-policy guardrail cases. S7 battery stress remains Unknown unless a causal simulator source exists; optional `I-sim-battery-cases` is outside the queue. S2 demo input is simulated only; `I-edge-physical-adapter` and first physical peer proof move to the first real pilot. Cold-chain and EV add separate world/device nodes and physical peers before their domain fixtures can close. These are architecture, implementation and data gates, not product choices. Queue-owned nodes are in `queue_baseline_nodes`; physical peers and domain worlds remain marginal beyond S1–S7. The [Site-first execution plan](site-first-execution-plan.md) and S2–S7 outlines name the corresponding review cuts.

## Leverage and readiness

Store four facts separately for each open node:

1. **Ready now:** panels whose only remaining open prerequisite is this node. **Closure unlock:** panels that become ready if this node *and its open upstream prerequisites* resolve. These are different facts; neither includes unrelated downstream work. Count a screen only when its approved core-panel and interaction gates are covered.
2. **Reach:** distinct subject areas and domain consumers reachable downstream, regardless of whether they are ready today. This makes shared contracts visible without promising immediate promotion.
3. **Distance:** number of unresolved transitive prerequisites. It is zero only when the node can be addressed now.
4. **Effort:** `S`, `M` or `L` estimate, revised by the Architect or Planner at task refinement.

Do not calculate a numerical priority rank until the owner has recorded tiers, priorities and core panels. Then weight each uniquely unlocked panel/screen by that choice; count a panel once even when multiple paths reach it. Publish the facts beside any score. A provisional ordering may use reach and distance to identify decisions to make next, but must be labelled unweighted. Recompute after each decision, reviewed task or fixture closes. Never interpret a `Dropped` product choice as resolving its technical nodes; exclude its screens from weighted unlock instead. The node report currently has zero ready-now and zero closure-unlock panels because each panel needs work on parallel read/UI and data branches. Reach still shows shared leverage: `A-claim-work-routes` reaches all 11 pilot panels with zero open technical prerequisites.

| First unweighted sample | Pilot panels reached | Open upstream | Interpretation |
| --- | ---: | ---: | --- |
| `A-claim-work-routes` | 11 | 0 | Shared decision can be made now; it does not by itself promote a panel. |
| `I-S1-01` | 11 | 0 | Active task supplies Site/Asset identity needed by evidence, Action and work records. |
| `A-actor-identity` | 6 | 0 | Shared actor/author decision reaches Action and the S4-02 path. |
| `D-finding-revisions` | 5 | 20 | Fixture is downstream of Foundation, registered Lab/gateway delivery, evidence, dispatch and Finding persistence. |

These counts cover only the seven fully mapped pilot screens. Reach in the full 110-screen product will be larger once the remaining panel gates are linked.

The **screen and panel report** unions open technical nodes across each panel, then across each screen, and sums rough effort points (`S=1`, `M=3`, `L=5`) once per unique node. The full total includes the current queue. The marginal column excludes [nodes the planned S1–S7 queue is expected to close](v69-dependency-registry-pilot.json), including its decisions and demo fixtures. S2–S7 remain outlines until refined, so this is a planning baseline, not a claim that those nodes are already approved or built. The checker validates that the baseline contains every queue-owned implementation and its open technical prerequisites. It excludes queue-only links and resolved nodes from both columns. The points are a sizing aid, not elapsed time; shared work must not be summed again across screens.

| Pilot screen | Panels | Full open nodes / points | Marginal beyond queue nodes / points |
| --- | ---: | ---: | ---: |
| `finding` | 4 | 30 / 98 | 0 / 0 |
| `sitefindings` | 1 | 25 / 83 | 3 / 7 |
| `findings` | 1 | 26 / 88 | 4 / 12 |
| `sitework` | 1 | 28 / 92 | 0 / 0 |
| `actions` | 1 | 29 / 95 | 2 / 6 |
| `incidents` | 2 | 9 / 29 | 6 / 20 |
| `maintenance` | 1 | 9 / 31 | 6 / 22 |

Use the checker's `--details` option for each panel's and screen's exact full and marginal open sets. `sitefindings` needs only the FindingIndex contract, projection and Site UI beyond the queue: seven points. `sitework` now includes Site/Asset identity, the evidence-backed Finding path, Action persistence and the accepted baseline fixture. Its bounded panel is queue-owned, so its marginal figure is zero despite 92 points of total unfinished work, including the newly explicit Lab/gateway path. `D-action-records` stops at the applied change; `D-verification-window` separately covers the later accepted window for S6-02 and future verification panels. The current queue still puts S7 after S6, but Health's technical `requires` points to Foundation bindings, accepted evidence and central diagnostics, so its architecture can be decided independently of verification.

## Ledger convergence and area-level coverage

Each pilot screen's ledger row has `registry_dependencies` with its **effective** product node ID and the exact union of its panels' required node IDs. For registered screens, these IDs are the authoritative promotion gates; the older model-name lists in `promotion_dependencies` remain traceability until the full ledger migrates. Both validators reject drift between the two representations. No other screen may claim a registry link without mapped panels. The nine added area briefs record product question, primary models and screens, architecture and projection nodes, fixture gate and pending owner choice. They are a decision inventory, **not** a 247-panel readiness assessment. The checker enforces complete 88-model and 110-screen primary coverage, resolves an effective owner choice for every screen from 11 area defaults and three exception choices, and keeps the 11 mapped pilot panels separate. The first-cut counts from the owner's review can change because this version explicitly assigns every model once; touched-screen counts still overlap across areas. The S1–S7 nodes remain prerequisites, not completed implementation in the added areas.

## Architect sequence

The S1–S7 Site spine remains the implementation path. At the pre-S3 planning review, settle actor identity and Finding/Action route contracts to the extent their first consumers need them, and specify `FindingIndex`, `CapabilityReadiness` and `SourceHealth` with all known consumers visible. `A-S4-financial` explicitly depends on actor identity because S4-02's `financial_assumption_revision.author_id` needs an author/actor contract; dispatch does not technically depend on it. This is contract design, not implementation of estate or other-domain screens. After S7, use the Claims/Action detail brief for the multi-revision Finding and contextual roots. Take the work-case identity pass only after the owner chooses the Incidents and Maintenance product tier. Mini-grid breadth, cold-chain/EV and estate aggregation retain their own domain and fixture gates.

Run `node frontend/docs/architecture/check_v69_dependency_registry.cjs` from the repository root for area coverage and the pilot readiness report, or add `--details` for exact open sets. The existing `check_v69_ledger.py` remains the full manifest/ledger validator. When an S2–S7 outline is refined, the Planner checks `queue_baseline_nodes` against the packet before relying on marginal effort; a moved or deferred contract/fixture must leave the baseline.
