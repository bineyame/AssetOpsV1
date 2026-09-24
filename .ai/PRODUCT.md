# Product

## Purpose

AssetOps reconstructs site operation from ordinary evidence, explains bounded
operational and economic consequences, and verifies whether an intervention
improved the outcome. Initial users are mini-grid operators, asset managers and
technical reviewers.

## Planning Basis

The intended demo path is `Docs/mini-grid-demo-architecture-and-roadmap.md`;
simulator mechanisms come from `Docs/simulator_design_v4.md`. The feature map
translates those sources into buildable outcomes from the recorded code state.
UI references guide presentation when content exists; they no longer determine
the delivery sequence. `D-2026-09-24-v4-roadmap-replan` records this change.

## Demo Readiness Milestones

These names replace the previous M1C / Demo Ready v1 / v2 / v2.5 ladder.

| Milestone | Observable completion | Feature map |
| --- | --- | --- |
| Credible mini-grid runtime | Lab shows PV, loads, battery, generator, named flows and a coherent response to a forcing/policy change | A |
| Internal architecture demo | Inspect private truth, reported observations and staging; Commit; open Site history populated through normal ingestion | B |
| Domain-expert feedback | One Candidate Avoidable generator-runtime Finding with electrical context, inspectable evidence, claim boundary and indicative bounded fuel consequence | C |
| Economically legible Finding | Thin versioned BusinessContext translates the bounded quantity into fuel/maintenance consequence | D |
| Verified intervention demo | Accept a policy change from the Finding, ingest a later window, and report Verified, Ineffective or Inconclusive from target and guardrails together | H |
| Full portfolio client demo | Portfolio, dispatch and fuel Findings, bounded money, productive-use opportunity, battery trajectory, verified intervention and Lab proof | E-G and I complete the story |

The historical M0 / M1A / M1B labels describe completed configuration, topology
and scenario/setup work, not new work to repeat. T001-T020 are complete, but the
shipped scenario remains blocked and nothing executes.

**What moved:** the former Simulated Evidence Loop / Demo Ready v1 is now the
internal architecture finish line, not a client-ready promise. The first
Finding is dispatch, not fuel reconciliation. Fuel follows thin financial
translation. Cold-chain's former Demo Ready v2.5 slot is retired: cold-chain
and e-mobility test future reuse and are deferred from the mini-grid demo.
This supersedes the readiness naming in
`D-2026-09-17-client-demo-readiness`; its evidence-isolation rule remains.

**Four demo points, not one.** The internal architecture demo is B. The
domain-expert and early-prospect demo is C plus D: one site, one strong
Finding, its evidence and its money. The strong product demo is H, where the
Finding leads to an action and the action is verified from later evidence. The
full portfolio demo is I. Only the last of these requires six sites, and none
of the first three is a rehearsal. Customer conversations legitimately begin at
C-D; `tasks/README.md` holds the same table against task ids, and
`D-2026-09-24-queue-resequenced-for-demo` records the change.

Roadmap section 7/C permits feedback immediately after the dispatch Finding.
Its section 13.2 checklist also asks for an indicative fuel consequence:
include a bounded modelled quantity in C; priced Financials is D.
Do not wait for six Sites before seeking expert feedback. A prospective client
may be approached at C-D, but that does not claim the full I finish line.

## Product Walkthrough

Build in feature-map A, B, C, D, H order, then E, F, G and I; `tasks/README.md`
is authoritative and H no longer waits on fuel, opportunity or lifecycle work.

The final client presentation opens with Portfolio Value & Operations, then Kobo's dispatch context and Finding/Evidence,
bounded Financials, productive-use opportunity, battery trajectory and
intervention verification. Simulator Lab/private truth is the validation reveal
at the end. Roadmap sections 3-5 and 13 own the detailed story.

Use canonical product screens. Portfolio Value & Operations and productive-use
comparison are thin compositions over existing evidence, runs and assumptions,
not new truth stores. Broad maintenance, authoring and reporting suites are not
prerequisites.

## Product Principles And Claim Boundaries

- Every slice produces or directly unlocks a coherent UI-verifiable outcome.
  Demo speed governs under `D-2026-09-22-milestone-speed-over-purity`.
- Before accepted evidence, operator views cannot claim operational health,
  history, analytics or money. Lab may show clearly labelled private runtime
  truth; it cannot supply product conclusions.
- Dispatch distinguishes Necessary, Candidate Avoidable and Indeterminate.
  Missing capability or override evidence limits the conclusion.
- Fuel reconciliation establishes an unexplained residual with uncertainty;
  it does not establish theft.
- Renewable headroom establishes physical opportunity, not market demand or
  commercial viability. Battery trajectory does not imply an exact failure date.
- Versioned business assumptions translate the technical claim without making
  it stronger. Do not aggregate overlapping cost, revenue and asset exposure
  into fictitious total savings.
- Work completion is not resolution. Verification requires comparable
  post-action evidence with target and guardrails. The first verification story
  uses reserve discipline, critical-load service and unserved energy; battery
  stress is a later, richer guardrail and not a precondition for verifying.
- A simulated intervention comparison establishes a result in the model, not
  proven real-world causal impact.

## Current Milestone

Credible mini-grid runtime (A), followed by the internal architecture demo (B),
earliest domain-expert feedback (C) and its economic translation (D), then the
verified intervention (H). The queue was recreated, reviewed, and resequenced on
2026-09-24 from the user's own review; T020A is active.
`.ai/ACTIVE_CONTEXT.md` routes that work.
