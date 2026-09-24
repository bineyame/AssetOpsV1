# Active Context

Routing only; hard cap 200 lines. Built history is in `.ai/CODE_STATE.md`,
durable rules in `.ai/ARCHITECTURE.md` and `.ai/DECISIONS.md`.

## Current Milestone

Credible mini-grid runtime (feature-map A), then internal architecture demo (B),
a dispatch Finding for domain-expert feedback (C), its economic translation (D)
and the verified intervention (H). E, F, G and I follow.

## Active Work

The Planner recreated the queue, the Architect reviewed it on 2026-09-24, and
the user's own review then resequenced it under
`D-2026-09-24-queue-resequenced-for-demo`. `tasks/README.md` is authoritative.

**T020A is built, reviewed twice, corrected twice, and back with the Reviewer.**
`tasks/T020A-foundation-physical-properties.md`. The first independent Codex
review returned three reproduced correctness defects and one test weakness; the
second closed those and returned three bounded corrections - an unrepresentable
integer that threw instead of refusing, a comment promising a guard the run
record does not have, and a frontend test claiming to prove bound rendering it
never showed. All are fixed and the packet's stale claims are corrected. A
fourth round closed the same unrepresentable-integer hole one domain along in
the scenario parser, which had been flagged rather than fixed and which the
user approved closing.
It still needs user review (`USER_REVIEW_REQUIRED: true`) and independent
re-review. Packet `.agent/T020A-review-packet.md`; reviews
`.agent/T020A-independent-review.md` and
`.agent/T020A-second-pass-review.md` with their probes beside them.
**Next task: T020A1**, then T020B, T021, T021A, T022, T023 and T024 onward per
that README. None of the resequencing touches the starter path.

What the resequencing changed, from position 10 onward: T026 is thinned to
dispatch-essential evidence and the gateway-failure work moved to T026A; a new
T029A extracts the minimal immutable policy-intervention mechanism so T034
verification runs right after T029 instead of behind T030-T033; T033 no longer
gates verification and adds battery stress to T034's guardrail rule set
afterwards. Delivery order is now A, B, C, D, H, then E, F, G, I. Feature-map
letters are outcomes, not order.

Two ordering facts the queue states deliberately. T026A is unscheduled and a
prerequisite of nothing, including T036; run it whenever feedback and time
justify it. T033 and T035 are an interchangeable pair, because neither consumes
the other's artifacts and the choice is a product-priority call from T028/T029
feedback. Every other position in `tasks/README.md` is load-bearing.

There are four demo points, not one: T027 internal architecture, T028/T029
domain-expert and early prospect, T034 strong product, T036 full portfolio.
Seek expert feedback at T028/T029 and reassess T030-T036 from what is said.

The earlier Architect review corrected one forward dependency - T026 introduces
the first operational-record family, which T028 needs and T030 extends, and the
thinning preserved it - and replaced the workflow's task-spec size bands with
ceilings under `D-2026-09-24-task-spec-size-ceilings`.

Direction comes only from:
- `Docs/simulator_design_v4.md` for simulator mechanisms;
- `Docs/mini-grid-demo-architecture-and-roadmap.md` for demo path and order.

The old two-roadmap precedence, fuel-first Finding and late electrical-world/
StateRef plan are superseded by `D-2026-09-24-v4-roadmap-replan`.
Earlier feature-map revamps, alignment reviews and v3 assessments do not direct
this work. Do not reconcile the new plan back to them.

## Read For The Active Task

1. `tasks/T020A1-addressed-foundation-bindings.md` and `tasks/README.md`.
   T020A's own file and packet are the built state its successor extends.
2. `.ai/PLANNING_HANDOFF_T020A_T023.md`: Properties and frozen answers;
   Existing property transition; Contract Versions And Retirements.
3. v4 sections 4.1, 5.2, 10, 24 and 27.2, plus the decisions T020A names.
4. `.ai/CODE_STATE.md`: T014, T018-T020 for existing carriers and frozen setup.
   Completed tasks are regression/history evidence, not future direction.
5. `.ai/ARCHITECTURE.md`; `.ai/WORKFLOW.md` for seams, sizing and review shape.
6. `.ai/ROLE_CONFIG.md` for role bindings, including the temporary Architect one.

Site-scoped Controls land with the first controller (T024), not with T020A's
carrier. The narrow fuel runtime and initial staging do not complete A or B:
A completes at T025, B at T027 and the first Finding is T028.

## What Is Built

T001-T020 are complete and merged in the base: Site creation/readback,
Foundation topology/devices/mappings/SLD, Fuel Loss scenario inspection, frozen
Draft setup and Runs inventory/detail. No product-path `READY` for the shipped
scenario; T020 used a fixture. No execution, generated observations, staging,
ingestion, accepted history, analytics or Findings.

T020A adds typed component properties to a Foundation and moves two machine
physics numbers out of the shipped scenario into it. A Foundation-owned
scenario parameter now states no value; run setup resolves it through the model
profile's binding, which names the component type, the property and the unit,
and freezes it. `EXECUTION_CONTRACT_VERSION` is 3,
`INITIAL_VALUE_ANSWERS_DISAGREE` is retired, and every Foundation-value failure
blocks. The shipped scenario still cannot reach `READY`: three forcing states
the profile does not model remain, and that is T020B's.

The shipped scenario lives in `config/scenarios/fuel-loss-event.yaml`.
Shipped and writable stores have disjoint identities; the scenario store ships
nonempty because there is no authoring UI.

## Local Data To Preserve

The working checkout's gitignored `var/sites/` holds mg-001, mg-002 (cold room)
and mg-003 (two AC buses), which the user asked to preserve. Do not clear,
replace or delete that directory. Updated templates do not mutate existing
Sites: use a new explicit fixture for new property/schema demonstrations and
leave existing fixtures intact. An isolated checkout does not contain them.

T020A added **mg-004**, instantiated from template version 2 through the
product's create path, and `var/scenarios/fuel-loss-event-mg004.yaml`, a local
copy of the shipped scenario pointed at it. A run is bound to the site the
scenario declares and run setup will not retarget one, so the resolved case
needs a scenario that names the new fixture; the shipped definition still
targets MG-001, whose Foundation declares no properties, and the Draft it
produces is the BLOCKED case the same review looks at. mg-001, mg-002 and
mg-003 were not touched.

`var/scenarios/` is the writable scenario store; `var/runs/` contains local
Drafts and may include T020's fixture-only READY run. Neither is shipped proof
of a reachable execution path.

## Standing Direction And Checks

`D-2026-09-22-milestone-speed-over-purity` binds every slice and review.
Stop for expensive-to-reverse defects, misleading claims or user-only decisions.
Carry cheap refinements in `.ai/MILESTONE_REVIEW_BACKLOG.md`; do not turn each
v4 concept into an independent task.

Run `tools/check-agent-workflow.ps1`, `tools/check-architecture.ps1` and checks
appropriate to the changed behavior. Layout-sensitive implementation requires
the workflow's browser evidence. `node tools/layout-evidence.mjs` now takes the
Site to measure as its second argument, or `ASSETOPS_LAYOUT_SITE`: a Foundation
section a site declares nothing for renders as a stated absence and not as a
table, so measuring containment against such a site measures an empty set.
