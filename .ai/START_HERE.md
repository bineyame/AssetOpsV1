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

Site Foundation slices T005 to T008 are planned and awaiting implementation.

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

Site Foundation planning direction was set on 2026-09-13. The user asked for
persisted Sites, shipped configuration templates, user-created Sites, and a
swappable persistence adapter. Three 2026-09-13 entries in `.ai/DECISIONS.md`
record this and explicitly supersede parts of the 2026-09-11 read-only
configuration decision. Causal Sequencing step 3 in `.ai/FEATURE_MAP.md` now
splits into 3a port and canonical read path, 3b shipped templates, 3c create a
Site from a template. Full architectural direction for the Planner and
Implementer is in `.agent/M1-site-persistence-architecture.md`.

The Site Foundation And Configuration-Only Site feature is planned as four
slices, not yet implemented:

- `tasks/T005-site-repository-port-and-canonical-read-path.md`
- `tasks/T006-read-only-site-configuration.md`
- `tasks/T007-shipped-site-template-catalog.md`
- `tasks/T008-create-site-from-template.md`

T005 and T006 are step 3a, split because the port, the canonical fixture,
strict validation, two new CI guards, and the Sites index are a full review
packet on their own, and because Foundation presentation carries product
language that deserves its own review surface. T007 is step 3b and T008 is step
3c, unsplit.

Two user-review checkpoints. T006 carries the first, deferred from T005: Site
and Foundation semantics and configuration-only UI language, including the
"configuration is fixed at creation in M1" statement that replaces the
superseded file-backed wording. T008 carries the second, deferred from T007:
creation semantics, template-versus-Site language, configuration origin and
template provenance, and refusal copy. T007 and T008 are provisional until the
T006 checkpoint is accepted or redirected.

Planning stops at the T008 checkpoint. Causal Sequencing step 4, topology,
devices, and the configured single-line diagram, is not planned yet.

Active task:

- `tasks/T005-site-repository-port-and-canonical-read-path.md`, status planned.
  It is the next slice for the Implementer.

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
