# AssetOps Feature Map

## Basis And Change Of Direction

Re-derived on 2026-09-24 from only
[simulator design v4](../Docs/simulator_design_v4.md) and the corrected
[mini-grid demo roadmap](../Docs/mini-grid-demo-architecture-and-roadmap.md).
v4 governs simulator mechanisms; the roadmap governs demo outcomes and order.
Built-state evidence is in `.ai/CODE_STATE.md` and `tasks/completed/`.

This replaces the previous Blocks A-J plan, its two-roadmap precedence claim,
and its fuel-first Finding decision. Earlier revamps and alignment reviews are
not direction for this plan. The former "(1)" roadmap is not a second authority.
See `D-2026-09-24-v4-roadmap-replan` for the supersession record.

Plan toward a coherent thing the owner can run and judge.
`D-2026-09-22-milestone-speed-over-purity` governs: protect expensive seams and
honest claims; carry cheap refinements in `.ai/MILESTONE_REVIEW_BACKLOG.md`.
Roadmap slices below are outcomes, not nine implementation tasks.

## What Is Already True

| Built | Canonical record |
| --- | --- |
| Gated Lab and operator shells; template catalog, create Site, Sites index, Site Details and read-only Foundation | T001-T013 |
| Configured topology, components, ratings, documentary controls, devices, signal mappings and SLD | T014-T016 |
| Shipped Fuel Loss scenario, scenario inspection and executable-document contract | T017-T018 |
| Frozen Draft run setup, profile resolution, Runs inventory and Draft detail | T019-T020 |

All are complete. The shipped Fuel Loss scenario still produces a `BLOCKED`
Draft; T020's `READY` proof uses a fixture. The simulator is a scaffold.
There is no execution, generated observation, gateway staging, Commit,
ingestion, accepted history, analytic, Finding, financial bridge or verification.
Configured PV/battery/load components are not functioning electrical models.

## Delivery Sequence

Letters match roadmap section 7. Every outcome includes the smallest backend,
simulator and UI path that makes it inspectable. Sources for screen content and
claim boundaries are roadmap sections 3-4; mechanism details stay in v4.

### A - A simulated mini-grid behaves credibly

**Demonstrable:** one Kobo-like mini-grid in Lab shows simulation time, PV,
residential/critical/productive demand, battery SOC/power, generator and named
energy flows. Change a forcing or policy and see a coherent physical change;
requested control and physically accepted output remain independently visible.

**Build from today:** complete the Foundation/property and addressed-binding
work, align the execution contract, then make the narrow Fuel Loss kernel and
Lab execution real. Extend that causal path to PV, load profiles, battery
SOC/limits, physical generator state, typed Site Controls, controller view,
`ControlIntent` and the deterministic resolver/`AcceptedFlowSet`.
Include a healthy baseline, service/unserved load and exact source/sink balance.
Use v4 sections 4-10 and 17; roadmap sections 3.1-3.3 and 7/A.

The inherited T020A-T023 queue is a starter path, not completion of A.
T021/T022 prove a fuel cause becomes private state and a reading. T023 can
prove initial staging while A is being completed; that is preparatory B work.
After this starter path, complete the electrical world before claiming A or
completing B. Do not proceed from the thin fuel runtime to a fuel Finding.

**Not yet a product claim:** Lab physics and traces are private. A does not
deliver an AssetOps Finding or financial result.

### B - The site crosses the real product boundary

**Depends on:** A's credible mini-grid and generated device observations.
**Demonstrable:** inspect truth versus reported readings, inspect staged
canonical envelopes, Commit, then open a basic Site Overview populated only
through normal ingestion. Turn the Lab off; the accepted Site history remains.
Rebuild that view from committed envelopes and referenced configuration without
private simulator objects. This is the **internal architecture demo**.

T023 starts the envelope/staging seam. Finish the gateway, immutable Commit
artifact, normal validation/normalization, acceptance/rejection, persisted
Evidence and selected-window Site read model. Carry the PV, BMS, generator,
meter and policy evidence C needs through this same path. A fuel-only allowlist
is an initial proof, not B's final evidence contract.

Source, gateway/publication and ingestion receipt times remain distinct.
Missing readings stay missing; duplicate content is idempotent and conflicting
message identity is explicit. Operator evidence inspection supplies provenance.
A full Replay UI and broad source-health dashboard are followers, not gates on
C. Replay remains accepted history, never re-simulation. v4 sections 3, 11, 21,
25; roadmap sections 3.2 and 7/B.

### C - First valuable AssetOps Finding

**Depends on:** B's ingested PV, BMS, generator, meter and time-valid policy
evidence, plus a cause-authored prolonged-runtime recipe and healthy reference.
**Demonstrable:** Site Overview -> Dispatch -> Finding Detail -> Evidence.
A practitioner can challenge a `DispatchInterval` classified as Necessary,
Candidate Avoidable or Indeterminate, inspect constraints, coverage, confidence,
alternatives and claim limits. Missing capability/override evidence limits the
claim rather than becoming an invented answer.

This replaces fuel reconciliation as the first Finding. It requires A's
electrical/controller world; a generator fuel trace alone cannot establish
avoidability. Include an indicative bounded fuel quantity with its model basis
for roadmap section 13.2's feedback checklist; this does not require priced
Financials. C is the **earliest domain-expert feedback** checkpoint. Seek that
feedback before building the whole portfolio. Roadmap sections 3.3, 7/C, 13.2.

### D - Translate operations into business consequence

**Depends on:** C's bounded runtime/fuel quantities.
**Demonstrable:** the Finding, Site Financials and a compact Site Overview value
show fuel and maintenance consequence using versioned `BusinessContext`.
Inspect technical quantity, price/accrual assumption, measured/modelled/scenario
basis and confidence separately. Changing price changes money, not physics or
technical confidence. Show any extrapolation's basis and avoid double-counting.
This is a thin bridge, not a financial planning module.
v4 section 22; roadmap sections 3.3, 7/D, 12.1.

### E - Fuel reconciliation

**Depends on:** B's boundary, reusable C Finding/Evidence presentation and the
thin D financial bridge; add tank observations, consumption evidence/model and
separate delivery/operator-hand-dip records.
**Demonstrable:** Performance -> Fuel explains a `FuelBalanceWindow`, residual
and uncertainty, then links to its Finding, evidence and bounded consequence.
A physical delivery and its record can disagree; absent/delayed records reduce
claim capability. Private fuel removal yields only an unexplained residual in
AssetOps, never a theft assertion. The existing Fuel Loss recipe is reused here.
v4 sections 11-12, 17; roadmap sections 3.4 and 7/E.

### F - Productive-use opportunity

**Depends on:** A's dispatch/curtailment model and B-D's evidence, Findings and
assumptions. **Demonstrable:** Renewable/Productive-use shows recurring headroom
under demand, reserve, storage and service constraints. Evaluate a scheduled
productive load in a paired run and compare energy use/sales, curtailment and
diesel from new ingested evidence, with any tariff impact labelled scenario.

This is the first planned owner of load-addition intervention artifacts and
`PairedExperiment`. Freeze reconstructible intervention content and reject
undeclared differences in resolved effective inputs; comparing opaque version
identifiers is insufficient. Shared-window experiments must not overwrite or
double-count a Site's committed history: give the Planner an explicit comparison
history context before releasing both sides. The thin comparison composes
existing evidence/run views. Physical headroom does not establish market demand.
v4 sections 5.2, 13, 15; roadmap sections 3.5, 4 and 7/F.

### G - Asset lifecycle

**Depends on:** battery operation plus accepted SOC, power, temperature and
capability evidence. **Demonstrable:** Battery Health, Site Overview and
Financials show state, stress recurrence/trajectory, reference band and bounded
replacement exposure. Add a simple causal stress model and explicit run-start
stress basis; unknown aged-asset stress is not zero. Product analytics derives
its trajectory from accepted evidence, not the private accumulator.
Exact remaining-life dates are deferred. v4 sections 10, 14; roadmap 3.6, 7/G.

### H - Intervention verification

**Depends on:** C's dispatch Finding, D's consequences and the intervention
machinery introduced in F. **Demonstrable:** accept a policy/configuration
change, inspect its frozen world input, simulate and ingest the new world, then
judge a comparable post-action window with target and guardrails together.
Show Verified, Ineffective or Inconclusive, with reopening when later evidence
warrants it. Work completion alone leaves the Finding unresolved.

Use runtime/fuel improvement with reserve discipline, critical service and
battery stress guardrails. Paired simulation comparison and operational
verification are distinct claims; the latter needs post-action evidence.
This brings configuration change and narrow Action/Maintenance Verification
into the client path, without building a CMMS. v4 sections 5.2, 13, 15;
roadmap sections 3.7 and 7/H.

### I - Portfolio demonstration

**Depends on:** individually credible A-H stories.
**Demonstrable:** Portfolio Value & Operations prioritizes deliberately different
Sites by operational/economic attention, opportunity and evidence gaps. The
suggested recipes are Meki healthy, Kobo runtime, Genda fuel, Bahir service/
backup failure, Desta productive use and Arsi battery stress. Each has independent
Site/run history rolled up normally; recipes never assign Findings.

Walk from portfolio to a deep Finding, evidence, bounded consequence, opportunity
and verified intervention. Reveal Lab/private-truth validation last. This is the
**credible client demo** (roadmap sections 5, 7/I and 13.3).
Bahir's start-failure/service recipe and product assessment need explicit work;
the other five stories do not automatically supply them.

## Next Work And Unowned Requirements

**Next actor: Planner.** Recreate the unimplemented task files from this map and
`.ai/PLANNING_HANDOFF_T020A_T023.md`; do not activate their existing wording.
This Architect pass leaves task files untouched. v4 sections 2.1 and 24 retain
T020A -> T020B -> T021 -> T021A -> T022 -> T023 as the starter dependency order,
with a sizing/split checkpoint around T020A. T021A is not a kernel prerequisite.

Existing starter owners need recreation, not duplication: T020A covers the
property carrier, T020B contract alignment, T021 the narrow kernel/neutral
contracts/test placement, T021A parser narrowing, T022 Lab wiring/observation,
and T023 the first envelope schema/staging. They do not own the broader demo.

The following have no complete implementation-task owner today. Rows name the
outcome that must own them; they are not a request for one task per noun.

| Gap to assign | First outcome / Planner responsibility |
| --- | --- |
| Addressed bindings through scenario/profile/frozen initialization; component control properties using the carrier | A starter: current T020A explicitly excludes StateRef; assign the immediate follow-on cut and control-property coverage |
| PV/load/battery/generator models, discrete-state contract, Site Controls, controller and accepted flows | A completion: no current task covers the credible electrical world; require repeated-load addressing and healthy/policy-change demonstrations |
| Dispatch-capable publication profile, mappings and evidence types; gateway fault/recovery, Commit and ingestion; Site Overview | B completion beyond initial T023 staging; prove reconstruction and timestamp semantics |
| Dispatch reconstruction/classification, confidence/claim ceilings, indicative fuel quantity, Finding and Evidence | C; include missing-capability and degraded-evidence cases, not only the successful recipe |
| Versioned business assumptions and bounded consequence | D; retain separate technical and economic bases |
| Operational delivery/dip records and fuel balance uncertainty | E; distinguish record failure from physical movement |
| Immutable intervention artifacts, load addition, effective-input pairing and comparison history context | F, reused in H; no arbitrary mutable intervention references |
| Battery stress initialization, evidence-derived trajectory and replacement exposure | G |
| Configuration change, Action/Maintenance link, target/guardrail verification and Finding history | H |
| Independent portfolio recipes, service/start-failure assessment and Lab truth-versus-inference validation | I; v4 sections 17, 20, 25 |

## Decisions At Their Point Of Use

The roadmap's live product choices (section 12) are financial assumptions before
D's external exposure; recognizable productive load before F demo recording;
and lifecycle monetization before G's external exposure. Recommended defaults
are already in that source; do not reopen cheap implementation choices.

Carry the canonical unresolved items to the work that consumes them: Fuel Loss
authored-number corrections follow the independent kernel result; fuel-model
expectation basis and uncertainty belong to E; reset/intervention-history
behavior belongs to the first injection control. The model declaring its own
Foundation needs (Option C) is triggered by the first law needing a value the
scenario does not request; see `D-2026-09-22-foundation-value-declaration`.
None requires a new general planning phase before the starter work.

## What Moved, What Was Cut, And Where It Lives

- Electrical behavior moved from old Block I to A, before the dispatch Finding.
  Component addressing moved from that late block into the immediate T020A
  sizing/split. Site-scoped controls still wait for the actual controller.
- Candidate Avoidable runtime replaces fuel residual as the first Finding (C).
  Thin economics follows (D), fuel follows (E); opportunity (F) and lifecycle
  (G) are separate outcomes before verification (H) and portfolio (I).
- Old `Demo Ready v1` is an internal architecture demo, not the client finish
  line. C supports early expert feedback; I completes the client story.
  `.ai/PRODUCT.md` replaces the old v1/v2/v2.5 naming.
- Cold-chain/e-mobility are deferred architecture tests, not scheduled milestones
  in this mini-grid sequence. Generic pack plugins, full authoring UI, broad
  inventory/CMMS, rich reports, precise RUL and advanced solvers remain deferred
  under roadmap section 8. A scheduled cold-room electrical load in F is not
  a cold-chain domain implementation.
- The duplicated eight-area capability catalog, seam table and UI inventory
  were cut. Built contracts remain in `.ai/CODE_STATE.md`, shell/persistence
  and truth rules in `.ai/ARCHITECTURE.md`, status vocabulary in
  `D-2026-09-13-provenance-status-vocabulary`, and mechanics in v4.
  Screen-to-input mapping lives in roadmap section 4.
- Fixed speculative T024-T038 ranges and absolute future contract-version
  numbers were removed. The Planner owns new task cuts; version-move guidance
  remains in the scoped handoff and `D-2026-09-22-contract-version-scope`.
  Full Replay/source-health breadth moves to evidence-history follow-up after
  the first Finding, without dropping its accepted-history semantics.
