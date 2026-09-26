# Start Here

AssetOps turns mini-grid evidence into bounded operational/economic conclusions
and verifies whether interventions helped. This file routes work; built state
lives in `.ai/CODE_STATE.md` and current routing in `.ai/ACTIVE_CONTEXT.md`.

## Current Focus

Current milestone:

Credible mini-grid runtime (feature-map A), then internal architecture demo (B),
a dispatch Finding for domain-expert feedback (C), its economic translation (D)
and the verified intervention (H). E, F, G and I follow.

Planning status:

T001-T020 are complete. Sites, Foundation, scenario inspection and frozen Draft
setup/readback exist. Nothing executes and the shipped scenario is still blocked.

The Planner recreated the task queue, the Architect reviewed it, and the user's
queue review resequenced it on 2026-09-24 under
`D-2026-09-24-queue-resequenced-for-demo`: verification moved ahead of analytic
breadth, T026 was thinned, and T036 is the last of four demo points rather than
the first client-facing one. **T020A1 is built and in review**, unaffected by
that resequencing, followed by the order in `tasks/README.md`.

Read `.ai/ACTIVE_CONTEXT.md`, then the task file, `.ai/FEATURE_MAP.md` and
`.ai/PLANNING_HANDOFF_T020A_T023.md`.

This replaces the former "recreate the queue first" routing.
`D-2026-09-24-v4-roadmap-replan` records the new source basis and sequence.
The only direction sources are `Docs/simulator_design_v4.md` (mechanisms) and
`Docs/mini-grid-demo-architecture-and-roadmap.md` (demo path). Earlier planning
reviews and the former second roadmap are not additional authorities.

## Current Route

Read by default:

1. `AGENTS.md`
2. `.ai/START_HERE.md`
3. `.ai/ACTIVE_CONTEXT.md`
4. The active task it names, when one has been recreated and activated.

Read only when relevant:

- `.ai/ROLE_CONFIG.md` for role bindings.
- `.ai/PROJECT_RULES.md` and `.ai/WORKFLOW.md` for authority, seams and checks.
- `.ai/PRODUCT.md` for demo milestones and claim boundaries.
- `.ai/ARCHITECTURE.md` for dependency, runtime and evidence boundaries.
- `.ai/FEATURE_MAP.md` for demonstrable outcomes and unowned requirements.
- `.ai/PLANNING_GUIDANCE.md` and the scoped handoff for task creation.
- Selected `.ai/CODE_STATE.md` entries, decisions and completed tasks for
  built-state detail, durable reasoning and regression risk.

## Working Model

Planned lane: Architect -> Planner -> Implementer -> independent Reviewer ->
User review where required. The Planner turns the reviewed feature map into
task files. Completed tasks move to `tasks/completed/`.

Fast lane: Implementer -> Reviewer for low-risk changes within established
contracts. New behavior, domain semantics, meaningful UI, data contracts,
simulator/ingestion boundaries and analytics use the planned lane.

Every task produces or directly unlocks a named UI-verifiable result.
Protect truth isolation, provenance and honest claims; carry cheap refinements
under `D-2026-09-22-milestone-speed-over-purity`. Do not load all project
history by default.
