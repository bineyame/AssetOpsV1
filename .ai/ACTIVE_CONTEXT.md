# Active Context

Keep this file compact and current. It is the agent handoff for what matters
now; durable reasoning stays in `.ai/FEATURE_MAP.md`, `.ai/DECISIONS.md`,
`.ai/ARCHITECTURE.md`, and the task files.

## Current Milestone

M1 - A user can configure one mini-grid site, simulate it, and inspect the
resulting operational evidence in the UI.

## Active Task

Active task: none.

Next task to activate:

- `tasks/T005-shipped-site-template-catalog.md`
- Intended branch: `task/T005-shipped-site-template-catalog`
- Lane: Planned lane, then independent review.
- User review: not required for T005.

## Current Site Foundation Sequence

Reworked Site Foundation tasks are T005-T013 in `tasks/`.

- T005: shipped Site Template catalog in Simulator Lab, gated.
- T006: create a Site from a template; first user-review checkpoint.
- T007: Site Details by `site_id`.
- T008: read-only Site Configuration; second user-review checkpoint.
- T009-T013: staged visual fidelity after real content exists.

Capability planning stops at the second checkpoint. Causal Sequencing step 4,
topology, devices, and the configured single-line diagram, is not planned. No
step 3 slice may render the diagram, an empty frame for it, or its signal
selector.

## Read For T005

Minimum required context:

- `tasks/T005-shipped-site-template-catalog.md`
- `.ai/FEATURE_MAP.md` sections:
  - Feature Map Index
  - Product Spine
  - Enforceable Protected Seams
  - Early Feature: Site Foundation And Configuration-Only Site
- `.ai/DECISIONS.md` decision-index entries:
  - `D-2026-09-13-site-foundation-persistence`
  - `D-2026-09-13-site-foundation-resequence`
  - `D-2026-09-13-template-and-create-surfaces-gated`
  - `D-2026-09-13-shared-site-substrate`
  - `D-2026-09-13-provenance-status-vocabulary`
- `.ai/ARCHITECTURE.md` only if dependency direction, contracts, simulator
  boundaries, or protected seams are in play.

## Settled Direction

- M1 ships zero canonical Sites. First run has a genuinely empty Sites index.
- A template is not a Site and never has `site_id`, lifecycle status, location,
  or a place-bound timezone.
- Template browsing and Site creation are Simulator Lab surfaces behind
  `simulator_lab.enabled`.
- Sites index, Site Details, and Site Configuration are operator surfaces and
  are never gated.
- A Site created from the Lab is a normal product Site with
  `source.mode = SIMULATED`; there is no Lab-owned Site store and no publish or
  promote step.
- Operator navigation does not grow for Site Foundation slices.
- Operator Site page and Lab Site page share one presentation substrate at
  `frontend/src/sites/`.
- Source mode, Site lifecycle, configuration origin, evidence readiness, and
  source health are separate concepts.

## Carried-Forward Risk

Open Architect action from T003 review follow-up 1, not absorbed by T004: the
disabled bundle still contains `SimulatorLabFrame.tsx`, because the gate removes
route reachability rather than code. This must become an explicit seam with a
concrete check in `.ai/FEATURE_MAP.md` before simulator truth overlays land.

## Standard Checks

- `tools/check-architecture.ps1`
- `tools/check-agent-workflow.ps1`
- Existing backend and frontend tests relevant to the active slice.

## Task Spec Hygiene

For new or revised task specs, follow `.ai/WORKFLOW.md` Task Spec Size guidance.
Large early M1 specs are acceptable only when they protect dangerous firsts; do
not let that become the default task shape.

Before handing off a new task, scan for repeated negative lists, exact wording
requirements, and implementation mechanics. Keep only what protects a named
seam or slice-specific risk.

## Inherited M1 Step 3 Exclusions

Tasks T005-T013 inherit these exclusions unless a later reviewed task explicitly
changes them:

- No in-place Site/Foundation editing, Save/Publish over an existing Site,
  rename, duplicate, delete, configuration history, rollback, approval flow, or
  disabled placeholder for those capabilities.
- No user-facing removal flow.
- No Single Line Diagram, empty diagram frame, signal selector, SLD view model,
  topology auto-layout, Devices & Sensors screen, or device-management surface.
- No scenarios, run setup, simulator execution, gateway staging, ingestion,
  source envelopes, evidence records, source health, charts, analytics, Replay,
  or Findings.
- No speculative database, ORM, migration tool, cache, query DSL, pagination,
  or port methods beyond the active slice.
- No operator navigation item, second simulator chokepoint, or weakening of
  previous route, API, navigation, architecture, or fabricated-value guards.
- No mockup value, timestamp, status, label, control, or destination unless the
  active slice supplies truthful backing content.
