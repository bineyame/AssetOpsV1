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

The review-bounded Stack, Shell, And Gate feature is implemented and reviewed:

- `tasks/completed/T001-stack-shell-skeleton.md`
- `tasks/completed/T002-operator-shell-route-frames.md`
- `tasks/completed/T003-simulator-lab-feature-gate.md`

The T003 user-review checkpoint is closed. The gate was accepted; the enabled
Simulator Lab entry point was redirected, because Simulator Lab is a separate
developer workspace rather than an operator navigation item.

Active task:

- `tasks/T004-simulator-lab-developer-entry-point.md`

Planning stops at T004 because it carries the redirection from that checkpoint.
Do not plan Site Foundation or later slices until T004 is accepted.

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
