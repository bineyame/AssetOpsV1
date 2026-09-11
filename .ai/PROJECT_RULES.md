# Project Rules

## Authority Order

1. User instructions.
2. Active task acceptance criteria, when a task exists.
3. `.ai/PROJECT_RULES.md`.
4. `.ai/PRODUCT.md` and `.ai/ARCHITECTURE.md`.
5. Existing code and tests.

When instructions conflict, use the higher authority and record material product
or architecture consequences in `.ai/DECISIONS.md`.

## Protected Seams

- Simulator does not equal product.
- Private simulator truth must not leak into product evidence.
- AssetOps consumes site and device evidence, not simulator internals.
- Scenario labels must not become site identity.
- Domain truth, published evidence, analytics, and presentation remain
  explicitly separated.
- External and data contracts stay strict at boundaries.
- Dependency direction is deliberate and testable.
- Demo shortcuts must not silently redefine product semantics.

## Responsibility Modes

Default model:

Architect or Planner -> Implementer -> Reviewer -> User

Low-risk fast lane:

Implementer -> Reviewer

Planner owns slice intent, acceptance criteria, user-observable outcome,
required semantics, relevant protected seams, scope limits, and user-review
placement.

Architect owns feature mapping, causal sequencing, durable architecture seams,
and the first pass at feature-to-task breakdown when needed.

Implementer owns implementation, tests, local verification, conservative
engineering choices, end-to-end behavior, and the review packet.

Reviewer owns independent review for correctness, acceptance gaps, contract or
architecture violations, missing tests, ambiguity, unnecessary scope, and
residual risk. The Reviewer must not merge work they authored.

Optional Architect or Planner hats are Product, Architecture, UI/UX, and Domain.
They are temporary viewpoints, not extra standing roles.

Default configurable role bindings:

- Architect: Codex agent.
- Planner: Codex agent.
- Implementer: Claude agent.
- Reviewer: configurable; must be independent from the author of the work.

The role is authoritative, not the tool identity. If a role binding changes,
the role responsibilities stay the same unless `.ai/PROJECT_RULES.md` changes.

## Ambiguity Rule

Use `SPEC_AMBIGUITY` only when the choice would change product behavior, domain
semantics, user-visible claims, data/API contracts, architecture boundaries,
protected seams, or milestone acceptance.

For ordinary local engineering choices that fit the active task and existing
patterns, make a conservative choice, document it briefly if useful, and
continue.

When a product decision is not needed for the current vertical slice, defer it.

## Fast-Lane Restrictions

Fast-lane work must introduce no new product behavior, domain semantics,
data/API contract change, architecture boundary change, meaningful UI/UX
behavior change, or external integration behavior change.

## Useful Progress

Useful progress moves the active vertical slice toward verified UI-visible value
without creating unnecessary scope, contract drift, or speculative architecture.

Implementer work should lead to a UI-verifiable outcome or heavily contribute to
one. Backend-only or tooling work must identify the screen behavior it enables
and the check that will prove that behavior.

Features and tasks must not be treated as interchangeable. A feature is a
complete product function and may contain several tasks. A task is a reviewable
implementation slice that delivers or materially advances one UI-verifiable part
of a feature.

## Process-Creep Rule

Do not add a new guide, role, checklist, handoff category, or governance
artifact unless the same need has appeared in at least two tasks or the user
explicitly asks for it.

## Git Rules

- Never work directly on `main`.
- Create one branch per vertical slice or task.
- Keep commits focused.
- Do not discard unrelated user changes.
- Do not merge your own work when acting as Reviewer.
- Leave work in a reviewable state.
