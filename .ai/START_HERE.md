# Start Here

AssetOps helps operators use a simulator lab and site operations screens to
inspect mini-grid evidence, understand current operating state, and investigate
evidence-backed operational findings.

This file is a routing document. Keep volatile task state in
`.ai/ACTIVE_CONTEXT.md`; keep durable product and architecture reasoning in the
canonical files it points to.

## Current Focus

Current milestone:

M1 - A user can configure one mini-grid site, simulate it, and inspect the
resulting operational evidence in the UI.

Planning status:

M1A, T017, T018 and T019 are complete. T019's user-review checkpoint on run
setup language and the READY/BLOCKED treatment was settled on 2026-09-22, and
it moved the refusal line. T020, Runs inventory and Draft shell, is next.
`.ai/ACTIVE_CONTEXT.md` names the task, relevant decision IDs, and feature-map
sections to read.

## Current Route

Read by default:

1. `AGENTS.md`
2. `.ai/START_HERE.md`
3. `.ai/ACTIVE_CONTEXT.md`
4. The active task file named in `.ai/ACTIVE_CONTEXT.md`, when one exists.

Read only when relevant:

- `.ai/PROJECT_RULES.md` for authority order, seams, ambiguity, and git rules.
- `.ai/ROLE_CONFIG.md` when invoking Planner, Architect, Implementer, or
  Reviewer roles.
- `.ai/PRODUCT.md` when product semantics, user-visible claims, or acceptance
  meaning matter.
- `.ai/ARCHITECTURE.md` when dependency direction, contracts, simulator
  boundaries, or protected seams matter.
- `.ai/CODE_STATE.md` only for the slice entries named by the active context:
  what earlier slices settled in code, and what they left open.
- `.ai/DECISIONS.md` only for the decision IDs named by the active context or
  active task.
- `.ai/FEATURE_MAP.md` only for the feature-map sections named by the active
  context or active task.
- Completed task files only when reviewing regression risk or historical
  acceptance.

Do not load every project document by default.

## Working Model

Planned lane:

Architect or Planner -> Implementer -> Reviewer -> User review

Use for new product behavior, domain semantics, meaningful UI/UX, data/API
contracts, architecture boundaries, simulator or ingestion semantics, external
integrations, and user-visible analytics.

Fast lane:

Implementer -> Reviewer

Use only for low-risk work inside existing product and technical contracts:
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

Normally ignore local-only `.agent/` files, completed task history, and
unrelated future-slice questions.
