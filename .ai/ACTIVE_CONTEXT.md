# Active Context

Routing only; hard cap 200 lines. Built history is in `.ai/CODE_STATE.md`,
durable rules in `.ai/ARCHITECTURE.md` and `.ai/DECISIONS.md`.

## Current Milestone

Credible mini-grid runtime (feature-map A), then internal architecture demo (B),
then a dispatch Finding for domain-expert feedback (C).

## Active Work

The Planner recreated the twenty-task queue; the Architect reviewed it on
2026-09-24, the first review by anything that did not write it. The queue is
accepted and its sequence is buildable in the order `tasks/README.md` gives.

**Active task: T020A**, `tasks/T020A-foundation-physical-properties.md`.
Then T020A1, T020B, T021, T021A, T022, T023 and T024 onward per that README.
T028 is the domain-expert feedback checkpoint; work after it may be redirected.

That review changed no sequence. It corrected one forward dependency - T026 now
introduces the first operational-record family, which T028 needs and T030
extends - and replaced the workflow's task-spec size bands with ceilings under
`D-2026-09-24-task-spec-size-ceilings`.

Direction comes only from:
- `Docs/simulator_design_v4.md` for simulator mechanisms;
- `Docs/mini-grid-demo-architecture-and-roadmap.md` for demo path and order.

The old two-roadmap precedence, fuel-first Finding and late electrical-world/
StateRef plan are superseded by `D-2026-09-24-v4-roadmap-replan`.
Earlier feature-map revamps, alignment reviews and v3 assessments do not direct
this work. Do not reconcile the new plan back to them.

## Read For The Active Task

1. `tasks/T020A-foundation-physical-properties.md` and `tasks/README.md`.
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
