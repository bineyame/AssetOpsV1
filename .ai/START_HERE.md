# Start Here

AssetOps helps operators use a simulator lab and site operations screens to
inspect mini-grid evidence, understand current operating state, and investigate
evidence-backed operational findings.

## Current Focus

Current milestone:

M1 - A user can configure one mini-grid site, simulate it, and inspect the
resulting operational evidence in the UI.

Planning status:

Architect feature map, causal sequencing, protected seams, and feature-to-task
guidance exist at `.ai/FEATURE_MAP.md`.

Site Foundation planning was reopened by the Architect on 2026-09-13 after user
direction, and the Planner reworked the task set the same day. The earlier
T005-T008 slice sequence is superseded, those four task files were deleted
before any of them was implemented, and the reworked set is T005-T013 in
`tasks/`. Read the twelve 2026-09-13 entries in `.ai/DECISIONS.md`, the revised
Causal Sequencing step 3, the Canonical Screen Fidelity section, the Provenance
And Status Concepts table, the shared-substrate seam row, and the Site
Foundation feature-to-task guidance in `.ai/FEATURE_MAP.md` before working any
of them.

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

Site Foundation persistence direction was set on 2026-09-13: persisted Sites,
shipped configuration templates, user-created Sites, and a swappable persistence
adapter. Those three decisions stand in full. The port, the two-store identity
rules, copy-on-instantiate, untrusted-input handling, create-without-edit, and
no removal are unchanged.

Later the same day the user corrected the causal order and put UI fidelity in
scope. Seven further 2026-09-13 entries in `.ai/DECISIONS.md` record the result.
The material changes:

- Causal Sequencing step 3 is resequenced to 3a shipped template catalog, 3b
  create a Site from a template, 3c read-only Site Configuration presentation.
  M1 ships zero canonical Sites; first run has a genuinely empty Sites index and
  every Site in the product is one a user created.
- `ScreenMockups.png` renders the Simulator Lab developer shell, not the
  operator product. Read correctly it agrees with T004, and the T003/T004
  navigation position is unchanged.
- Template browsing and Site creation are Simulator Lab surfaces behind
  `simulator_lab.enabled`. The Sites index, Site Details, and Site Configuration
  are operator surfaces and are never gated. Operator navigation does not grow.
- Canonical mockup fidelity is in scope, staged per surface after that surface's
  content is real, under a three-state rule for affordances.
- Simulator Lab exists to unblock product development before a real site exists.
  A Site it produces is a normal Site with simulated source mode as provenance,
  in the product store, never published or promoted. The gate covers surfaces
  and execution, never objects or stores.
- The operator Site page and the Lab Site page share one presentation
  substrate at `frontend/src/sites/`: one read model, one view model, one set of
  components. Shells compose and add through declared slots; neither forks, and
  no shell/mode/variant discriminant lives in the shared core.
- Two provenance concepts, not three. The simulator tag is
  `source.mode = SIMULATED`, not a separate field. See the Provenance And Status
  Concepts table in `.ai/FEATURE_MAP.md` Feature Area 1 and cite it rather than
  restating it.

The durable direction for the Planner and Implementer is tracked in the
2026-09-13 entries in `.ai/DECISIONS.md`, the Shells And Navigation,
Presentation Honesty, and Configuration Persistence sections of
`.ai/ARCHITECTURE.md`, and Causal Sequencing step 3, Canonical Screen Fidelity,
the seam table, and the Site Foundation feature-to-task guidance in
`.ai/FEATURE_MAP.md`. Those are sufficient on their own.

The reworked Site Foundation task set, in implementation order:

- `tasks/T005-shipped-site-template-catalog.md` - Simulator Lab, gated. Ports,
  strict parser, composition root, and the three persistence CI guards, proven
  against a read-only template catalog. No Site exists yet.
- `tasks/T006-create-a-site-from-a-template.md` - create flow in the Lab behind
  the gate; ungated operator Sites index from a genuine first-run empty state to
  the created Site. Introduces the shared Site substrate at
  `frontend/src/sites/` and its two structural guards. **User-review checkpoint.**
- `tasks/T007-site-details-by-site-id.md` - ungated operator Site Details
  addressed by `site_id`; removes the parameterless `Site details` route and nav
  item.
- `tasks/T008-read-only-site-configuration-presentation.md` - ungated operator
  read-only Site Configuration; removes the parameterless `Site configuration`
  route and nav item. **User-review checkpoint.**
- `tasks/T009-shared-visual-vocabulary.md` - fidelity stage 1, chrome only,
  applied to surfaces that already have real content.
- `tasks/T010-lab-template-and-create-surfaces-to-mockup-quality.md` - fidelity
  stages 2 and 3, Simulator Lab, gated.
- `tasks/T011-sites-index-to-canonical-screen-one.md` - fidelity stage 4.
- `tasks/T012-site-details-to-canonical-screen-two.md` - fidelity stage 5; the
  three-state affordance rule in full, and the substrate's first extension slot.
- `tasks/T013-site-configuration-to-canonical-screen-three.md` - fidelity stage
  6, canonical screen 3 minus the diagram.

Two user-review checkpoints remain, and both moved. The first sits on T006,
because creation fixes Site, template, instance, identity, origin, and refusal
language at once. The second sits on T008, because configuration-only language
and the "configuration is fixed at creation in M1" statement fix what the
product promises about a Site it will not let you edit. The fidelity slices
T009-T013 carry no checkpoint of their own.

Capability planning stops at the second checkpoint. Causal Sequencing step 4,
topology, devices, and the configured single-line diagram, is not planned, and
no step 3 slice may render the diagram, an empty frame for it, or its signal
selector.

Active task: none. `tasks/T005-shipped-site-template-catalog.md` is the next
task to activate.

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
