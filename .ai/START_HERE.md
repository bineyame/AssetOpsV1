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

T001-T023 are complete. Sites, Foundation, scenario inspection and frozen Draft
setup/readback exist; the shipped Fuel Loss Event reaches READY, executes in the
Lab where somebody can step and watch it, and stages canonical source envelopes
inspected on the Draft's own screen. There is still no Commit, ingestion or
Finding.

The Planner recreated the task queue, the Architect reviewed it, and the user's
queue review resequenced it on 2026-09-24 under
`D-2026-09-24-queue-resequenced-for-demo`. On 2026-09-29 the owner approved
`D-2026-09-29-run-store-libyaml`: the run store moves to libyaml in its own
slice T022B, now complete as a partial improvement. **T024 is complete**
(daytime PV, storage and three addressed loads, contract 9); T025a and
T025b are complete and the owner accepted A. On 2026-09-30 the owner accepted
the Lab cockpit cadence: **T025c (L1a) is complete** (owner accepted 2026-09-30);
**T025d (L1b) is complete** (owner accepted 2026-09-30); **T025e (cockpit
organisation and live playback) is complete** (owner accepted 2026-10-01); **T025f
(template versioning) is complete** (fast lane, Claude review ACCEPT WITH CARRIES);
**T025g** (`tasks/completed/T025g-run-binds-scenario-to-site.md`, scenario-site contract under
`D-2026-10-01-run-binds-scenario-to-site`) is complete (owner accepted 2026-10-02); **T026**
(`tasks/completed/T026-dispatch-capable-evidence.md`) is complete (owner accepted 2026-10-02);
**T027** (`tasks/completed/T027-commit-ingestion-and-site-overview.md`, Commit,
ingestion, Site > Evidence and the mini-grid Overview) is complete (owner accepted
2026-10-03); next is **T028** (dispatch Finding) and the order in `tasks/README.md`, replanned under `D-2026-10-02-demo-led-recommendation`.
**T025h is parked** (not before T029; gates nothing).

Read `.ai/ACTIVE_CONTEXT.md`, then the task file, `.ai/FEATURE_MAP.md` and
`.ai/PLANNING_HANDOFF_LAB_COCKPIT.md` and
`.ai/PLANNING_HANDOFF_T020A_T023.md`.

This replaces the former "recreate the queue first" routing.
`D-2026-09-24-v4-roadmap-replan` records the new source basis and sequence.
The mechanism/demo direction sources are `Docs/simulator_design_v4.md` and
`Docs/mini-grid-demo-architecture-and-roadmap.md`; the owner also authorized
`Docs/lab-cockpit-proposal.md` as scoped Lab inspection input on 2026-09-30.
Earlier planning reviews and the former second roadmap are not additional
authorities.

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
