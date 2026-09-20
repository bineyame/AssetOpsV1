# Active Context

Keep this file compact and current. Durable reasoning lives in
`.ai/FEATURE_MAP.md`, `.ai/DECISIONS.md`, `.ai/ARCHITECTURE.md`,
`.ai/CODE_STATE.md`, and the task files.

Size rule: this file stays under 200 lines, enforced by
`tools/check-agent-workflow.ps1`.

## Current Milestone

M1 - A user can configure one mini-grid site, simulate it, and inspect the
resulting operational evidence in the UI.

## Active Task

Active planned task: `tasks/T017-scenario-catalog-fuel-loss-detail.md`.

T017 starts M1B, Scenario Catalog And Run Setup. It is planning-only complete
and ready for Implementer pickup after this planning branch is reviewed.

T017 carries `USER_REVIEW_REQUIRED: true`. It is the M1B checkpoint for:

- scenario versioning fields;
- event taxonomy;
- public authoring parameters versus private test-oracle expectations;
- run setup language prerequisites.

T018 and T019 are not task files yet. They depend on the T017 User Review
Outcome and are sequenced in `.ai/FEATURE_MAP.md` under
`Early Feature: Scenario Catalog And Run Setup`.

## Current State

M1A is complete. T001-T016 are in `tasks/completed/` with Review Outcomes.
T016 drew the configured Single Line Diagram inside Foundation and was accepted
by user review on 2026-09-20.

Cold-room symbol treatment was accepted as proposed. Breaker/control vocabulary
was settled by `D-2026-09-20-breaker-vocabulary`: breaker position is evidence,
not Foundation configuration; `OPEN`, `CLOSED`, `TRIPPED`, `AUTO`, `MANUAL`,
and `BREAKER` are not Foundation schema vocabulary. A scenario taxonomy must
not smuggle those terms into schema vocabulary either.

`var/sites/` holds `mg-001`, `mg-002` (cold room), and `mg-003` (two AC buses).
The user asked that these be kept as fixtures. They are gitignored, so add
fixtures when needed and do not clear, replace, or delete that directory.

## Read For T017

- `tasks/T017-scenario-catalog-fuel-loss-detail.md`
- `.ai/FEATURE_MAP.md`
  - Client-Demo Roadmap
  - `### 3. Scenario Authoring And Scenario Catalog`
  - `### 4. SimulationRun Runtime And Simulator Lab Shell`
  - `### Early Feature: Scenario Catalog And Run Setup`
- `.ai/DECISIONS.md` decision-index entries:
  - `D-2026-09-11-simulator-gate`
  - `D-2026-09-13-template-and-create-surfaces-gated`
  - `D-2026-09-20-breaker-vocabulary`
  - `D-2026-09-20-layout-evidence-standing`
- `.ai/CODE_STATE.md`
  - T014
  - T015
  - T016
- `.ai/WORKFLOW.md`
  - Task Spec Size
  - Review Packet
  - Closeout

## Settled Direction For T017

- Scenario catalog is a Simulator Lab surface, not an operator surface, and is
  gated with `simulator_lab.enabled`.
- Only `frontend/src/shell/simulatorLabRoutes.tsx` may name simulator URLs.
- Adding a truthful Scenarios route may add Scenarios to the Lab rail; operator
  navigation and operator Site tabs do not grow.
- ScenarioDefinition answers what happens during the simulated interval. Site
  Foundation answers what the Site is. The two do not duplicate each other.
- Scenario labels, scenario versions, run names, and `run_id` never become
  `site_id`.
- Private expectations are test-oracle metadata only. They never enter source
  envelopes, accepted evidence, operator UI, normal product provenance, exports,
  analytics, or Findings.
- M1B has no ingestion, no accepted evidence, no Draft run yet, and no Findings.
  T017 screens must describe intention, not report outcome.
- No invented digits: a count, timestamp, duration, seed, volume, confidence, or
  parameter value appears only when the record supplies it.
- Dense tables and timeline layouts require browser layout evidence in the
  review packet.

## Standard Checks

- `tools/check-architecture.ps1`
- `tools/check-agent-workflow.ps1`
- Existing backend and frontend tests relevant to the active slice.

## What The Code Already Settles

Per-slice details live in `.ai/CODE_STATE.md`.

- T006-T008 settled Site records, stores, read paths, Foundation basics, and
  frontend/backend Site client shape.
- T009-T013 settled shared visual vocabulary, canonical Site screens,
  Foundation naming, operator tab inventory, and overflow posture.
- T014-T016 settled Foundation topology/devices/mappings, SLD view model, and
  configured SLD/device presentation.
