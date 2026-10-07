# v6.9 dependency registry pilot: Claims and Work

**Architect planning overlay · 2026-10-07; revised after dependency review.** The [pilot registry](v69-dependency-registry-pilot.json) names dependency *kind*, *subject area* and *leverage inputs* separately. It supplements the [110-screen ledger](v69-screen-ledger.json), [model homes](v69-model-homes.json) and [panel contracts](v69-panel-contracts.json). The accepted S1-01 Architect contract is the sole resolved node; no implementation or data node is resolved, no panel is claimed real, and no owner tier or priority is inferred. S1-01 remains the active implementation task.

## Contract for extending the registry

An **architecture** node records an accepted decision or projection/route contract with a decision link as evidence. An **implementation** node records a built capability only after its task has an approved independent review. A **data** node records a source-to-claim fixture or operational record only after normal ingestion, reload and lineage checks. A **product** node records the owner's tier, priority, core panels or Drop decision. Product nodes influence selection and weighting; they are never prerequisites that satisfy a technical gate.

Every implementation and data node has an architecture prerequisite. The eleven S1–S7 task nodes record the current queue, but `requires` contains **technical prerequisites only**. `sequenced_after` records the chosen task order and is excluded from distance, reach and readiness. The checker validates both graphs and their combined acyclicity. Finding, Action and work cases separate persistence, read projection/API and route/UI nodes. Data depends directly on persistence, so records can be seeded before a screen exists. A layered implementation node assigned to an S task and that task's closeout node must share the same status; a panel cannot appear ready halfway through the task's review. Every claim-bearing panel requires a read projection, UI and data node; a purely structural panel must explicitly declare `structural: true`. `real` requires all transitive technical prerequisites to be resolved and the rendered claim to be reviewed. `withheld` requires a visible reason and recorded owner approval. Otherwise it is `gap`. The ledger's `proposed_fidelity_tier` remains a proposal. `Real with honest gaps` requires all owner-designated core panels to be real. `Real` requires every panel to be real or owner-approved withheld, plus interaction and navigation acceptance. No empty `core_panels` list means approval while the product node is pending.

Keep model names in `satisfies_models` when useful for traceability, but do not require every architecture node to match a model. Actor identity, route contracts, currency/period comparability and domain role sets are first-class decisions. A subject-area brief is the Architect's decision unit; the Planner may then cut one or more reviewable vertical tasks. The registry stays a planning overlay until a task packet explicitly adopts its nodes and checks their evidence.

## Worked subject-area brief

| Area | Product question | Mock models and shared contracts | Decisions and evidence | Screens in this pilot | Owner choice |
| --- | --- | --- | --- | --- | --- |
| Claims | Which revisioned Finding is being shown, with what evidence and route? | `Finding`, `FindingRevision`, `FindingIndex`; Finding and evidence detail | Decide episode/revision/recurrence and full `FindingIndex` consumers; ingest a multi-revision episode, recurrence and missing/late variant | `finding`, `sitefindings`, `findings` | Global Findings tier, priority and core panels pending |
| Work and verification, Action detail | What Action was taken, and where does it lead? | `Action`, `ActionEvent`, `ActionIndex`; shared route and actor contract | Decide event authority, actor identity and Site/global index shape before first consumers; S6 still supplies bounded Action/verification records | `sitework`, `actions` | Global Actions breadth remains unapproved; S6 bounded portion stays in queue |
| Work and verification, cases | What Incident, request, performed maintenance or operational record exists, and who attested it? | `Incident`, `MaintenanceWorkRequest`, `MaintenanceRecord`, `MaintenancePlan`, `WorkEvent`, `OperationalRecord`, `MaintenanceIndex` | Decide identities/lifecycle/correction in one pass; prove attested records through reload and lineage | `incidents`, `maintenance` | Owner decides whether these roots merit implementation, deferment or Drop |

All 11 rendered panels of these seven screens are linked. Product choices are layered: `P-claims-area` and `P-work-area` supply area defaults; `P-finding`, `P-sitework` and `P-work-cases` are screen exceptions. The exceptions separate the S4/S6 bounded screens and the optional work cases from their area's deferred breadth. An exception takes precedence over its area default. The checker requires exactly one effective choice for each pilot screen and rejects duplicate defaults or exceptions. A recorded `Real with honest gaps` choice must name at least one core panel for every screen it effectively governs. This is five pending owner choices for seven screens; later briefs should add exceptions only when a screen genuinely needs a different tier, priority or core-panel set. The sample is **not** the complete set of consumers. The manifest and panel inventory remain authoritative for other screens. In particular, no panel here is promotable merely by closing one index: `findings` and `actions` also require estate scope rules and a root implementation. A later complete brief must enumerate all consumers, including cold-chain and EV Site panels, before freezing a shared projection contract.

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
| `D-finding-revisions` | 5 | 10 | Fixture is downstream of Foundation, evidence, dispatch and Finding persistence. |

These counts cover only the seven fully mapped pilot screens. Reach in the full 110-screen product will be larger once the remaining briefs are linked.

The **screen and panel report** unions open technical nodes across each panel, then across each screen, and sums rough effort points (`S=1`, `M=3`, `L=5`) once per unique node. The full total includes the current queue. The marginal column excludes [nodes the planned S1–S7 queue is expected to close](v69-dependency-registry-pilot.json), including its decisions and demo fixtures. S2–S7 remain outlines until refined, so this is a planning baseline, not a claim that those nodes are already approved or built. The checker validates that the baseline contains every queue-owned implementation and its open technical prerequisites. It excludes queue-only links and resolved nodes from both columns. The points are a sizing aid, not elapsed time; shared work must not be summed again across screens.

| Pilot screen | Panels | Full open nodes / points | Marginal beyond queue nodes / points |
| --- | ---: | ---: | ---: |
| `finding` | 4 | 20 / 64 | 0 / 0 |
| `sitefindings` | 1 | 15 / 49 | 3 / 7 |
| `findings` | 1 | 16 / 54 | 4 / 12 |
| `sitework` | 1 | 18 / 58 | 0 / 0 |
| `actions` | 1 | 19 / 61 | 2 / 6 |
| `incidents` | 2 | 9 / 29 | 6 / 20 |
| `maintenance` | 1 | 9 / 31 | 6 / 22 |

Use the checker's `--details` option for each panel's and screen's exact full and marginal open sets. `sitefindings` needs only the FindingIndex contract, projection and Site UI beyond the queue: seven points. `sitework` now includes Site/Asset identity, the evidence-backed Finding path, Action persistence and the accepted baseline fixture. Its bounded panel is queue-owned, so its marginal figure is zero despite 58 points of total unfinished work. `D-action-records` stops at the applied change; `D-verification-window` separately covers the later accepted window for S6-02 and future verification panels. The current queue still puts S7 after S6, but Health's technical `requires` points to Foundation bindings and accepted evidence, so its architecture can be decided independently of verification.

## Ledger convergence and remaining areas

Each pilot screen's ledger row has `registry_dependencies` with its **effective** product node ID and the exact union of its panels' required node IDs. For registered screens, these IDs are the authoritative promotion gates; the older model-name lists in `promotion_dependencies` remain traceability until the full ledger migrates. Both validators reject drift between the two representations. No nonpilot screen may claim a registry link without mapped panels. The remaining subject-area briefs—configuration breadth, evidence/source health, money breadth, mini-grid breadth, onboarding/admin, assets/life, estate aggregation, cold-chain and EV—are pending. The S1–S7 nodes here are prerequisites, not completed briefs for those areas.

## Architect sequence

The S1–S7 Site spine remains the implementation path. Before S4, settle actor identity and Finding/Action route contracts to the extent their first consumers need them, and specify `FindingIndex`, `CapabilityReadiness` and `SourceHealth` with all known consumers visible. `A-S4-financial` explicitly depends on actor identity because S4-02's `financial_assumption_revision.author_id` needs an author/actor contract. This is contract design, not implementation of estate or other-domain screens. After S7, use the Claims/Action detail brief for the multi-revision Finding and contextual roots. Take the work-case identity pass only after the owner chooses the Incidents and Maintenance product tier. Mini-grid breadth, cold-chain/EV and estate aggregation retain their own domain and fixture gates.

Run `node frontend/docs/architecture/check_v69_dependency_registry.cjs` from the repository root for the concise report, or add `--details` for the exact open sets. The existing `check_v69_ledger.py` remains the full manifest/ledger validator.
