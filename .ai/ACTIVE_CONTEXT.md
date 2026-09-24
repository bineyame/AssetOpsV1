# Active Context

Routing only; hard cap 200 lines. Built history is in `.ai/CODE_STATE.md`,
durable rules in `.ai/ARCHITECTURE.md` and `.ai/DECISIONS.md`.

## Current Milestone

Credible mini-grid runtime (feature-map A), then internal architecture demo (B),
then a dispatch Finding for domain-expert feedback (C).

## Active Work

Architect replan from the corrected sources is complete in this branch.
**Next: Planner recreates the unimplemented task files. No implementation task
is active through this routing.** The previous instruction to activate T020A
as written is withdrawn. Task files were deliberately not edited in this pass;
they are pending recreation, not acceptance of their current scope.

Direction comes only from:
- `Docs/simulator_design_v4.md` for simulator mechanisms;
- `Docs/mini-grid-demo-architecture-and-roadmap.md` for demo path and order.

The old two-roadmap precedence, fuel-first Finding and late electrical-world/
StateRef plan are superseded by `D-2026-09-24-v4-roadmap-replan`.
Earlier feature-map revamps, alignment reviews and v3 assessments do not direct
this work. Do not reconcile the new plan back to them.

## Read For The Planner

1. `.ai/FEATURE_MAP.md`: Delivery Sequence; Next Work And Unowned Requirements.
2. `.ai/PLANNING_HANDOFF_T020A_T023.md`: immediate sizing, boundaries and proofs.
3. v4 sections 2-11, 24-25; roadmap sections 7-10 and 13.
4. `.ai/CODE_STATE.md`: T014-T020 as needed for carriers and frozen setup.
   Completed tasks are regression/history evidence, not future direction.
5. `.ai/ARCHITECTURE.md`; `.ai/WORKFLOW.md` for task/review shape.
6. `.ai/ROLE_CONFIG.md` for the unchanged role bindings.

Retain the starter dependency order T020A -> T020B -> T021 -> T021A -> T022 ->
T023, with an immediate carrier/addressed-binding split as needed.
Site-scoped Controls land with the first controller. The narrow fuel runtime
and initial staging do not complete A or B; the Planner must assign electrical
runtime completion, then dispatch-capable ingestion and the first Finding.

## What Is Built

T001-T020 are complete and merged in the base: Site creation/readback,
Foundation topology/devices/mappings/SLD, Fuel Loss scenario inspection, frozen
Draft setup and Runs inventory/detail. No product-path `READY` for the shipped
scenario; T020 used a fixture. No execution, generated observations, staging,
ingestion, accepted history, analytics or Findings.

The shipped scenario lives in `config/scenarios/fuel-loss-event.yaml`.
Shipped and writable stores have disjoint identities; the scenario store ships
nonempty because there is no authoring UI.

## Local Data To Preserve

The working checkout's gitignored `var/sites/` holds mg-001, mg-002 (cold room)
and mg-003 (two AC buses), which the user asked to preserve. Do not clear,
replace or delete that directory. Updated templates do not mutate existing
Sites: use a new explicit fixture for new property/schema demonstrations and
leave existing fixtures intact. An isolated checkout does not contain them.

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
the workflow's browser evidence. This replan changes documentation only.
