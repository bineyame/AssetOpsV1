# Start Here

AssetOps helps operators use a simulator lab and site operations screens to
inspect mini-grid evidence, understand current operating state, and investigate
evidence-backed operational findings.

## Current Focus

Current milestone:

M1 - A user can configure one mini-grid site, simulate it, and inspect the
resulting operational evidence in the UI.

Planning status:

Architect feature map, causal sequencing, protected seams, and first-pass
feature-to-task guidance exist at `.ai/FEATURE_MAP.md`.

The Stack, Shell, And Gate feature is complete, reviewed, and accepted:

- `tasks/completed/T001-stack-shell-skeleton.md`
- `tasks/completed/T002-operator-shell-route-frames.md`
- `tasks/completed/T003-simulator-lab-feature-gate.md`
- `tasks/completed/T004-simulator-lab-developer-entry-point.md`

Both user-review checkpoints are closed. T003 accepted the gate but redirected
its entry point; T004 applied that redirection and was accepted on 2026-09-13.
Simulator Lab is reached from workspace-level chrome outside operator
navigation, operator navigation is structurally identical in both flag states,
and the Lab renders outside the operator route layout.

Active task:

- None. T004 was the last planned slice.

Planning may now proceed to Site Foundation slices. The Architect or Planner
owns the next task definition; see `.ai/FEATURE_MAP.md`.

Open Architect action carried from T003 review follow-up 1, not absorbed by
T004: the disabled bundle still contains `SimulatorLabFrame.tsx`, because the
gate removes route reachability rather than code. This must become an explicit
seam with a concrete check in `.ai/FEATURE_MAP.md` before simulator truth
overlays land.

## Default Reading Path

Read by default:

1. `AGENTS.md`
2. `.ai/START_HERE.md`
3. `.ai/PLANNING_GUIDANCE.md` until the Architect creates the first task

Read only when relevant:

- `.ai/ROLE_CONFIG.md` when invoking Planner, Architect, Implementer, or
  Reviewer roles.
- `.ai/PRODUCT.md` when product semantics, user-visible claims, or acceptance
  meaning matter.
- `.ai/ARCHITECTURE.md` when dependency direction, contracts, simulator
  boundaries, or protected seams matter.
- `.ai/DECISIONS.md` when a current choice depends on previous decisions.

Do not load every project document by default.

## Working Model

Planned lane: Architect or Planner -> Implementer -> Reviewer -> User review.

Use it for new product behavior, domain semantics, meaningful UI/UX, data/API
contracts, architecture boundaries, simulator or ingestion semantics, external
integrations, and user-visible analytics.

Fast lane: Implementer -> Reviewer.

Use it only for low-risk work inside existing product and technical contracts:
documentation cleanup, test clarification, small bug fixes with established
behavior, internal refactors, tooling cleanup, implementation cleanup, or minor
styling corrections.

## Task Shape

The primary planning unit is a reviewable vertical slice. Every planned task
should answer: what can the user observe, inspect, or validate in the UI when
this is done?

Implementer work should lead directly to a UI-verifiable outcome or materially
contribute to a clearly named upcoming UI-verifiable slice. Backend-only work is
allowed only when the active task explains which screen behavior it unlocks and
how it will be verified.

Task files live in `tasks/` after the Architect creates them. Completed task
files move to `tasks/completed/`.

Current product truth lives in `.ai/PRODUCT.md`. Durable architecture rules live
in `.ai/ARCHITECTURE.md`. Lightweight durable governance lives in
`.ai/PROJECT_RULES.md`.

Normally ignore local-only `.agent/` files, completed task history, and unrelated
future-slice questions.
