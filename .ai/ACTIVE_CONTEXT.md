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

`tasks/T017-scenario-catalog-fuel-loss-detail.md` is built and at
`Status: in_review` on branch `task/T017-scenario-catalog-fuel-loss-detail`.
Not merged. Packet: `.agent/T017-review-packet.md`.

Next step is Reviewer, then **user review**, which T017 carries as the M1B
checkpoint. The screen at `/simulator-lab/scenarios/fuel-loss-event` puts a
provisional proposal in front of the user for three decisions:

- scenario versioning fields, in the identity and version panel;
- event taxonomy, under the timeline and its legend;
- public authoring parameters versus private test-oracle expectations, in the
  private expectations panel, with the public parameters panel above it.

Each region states a proposal, what is already settled, and what accepting or
redirecting means, so accepting the screen is a decision. Run setup language
is answered by the third: the screen names the missing run setup / Draft
SimulationRun prerequisite on the disabled `Create Draft Run` control.

T018 and T019 are not task files yet and are not implementable until the T017
User Review Outcome is recorded. They are sequenced in `.ai/FEATURE_MAP.md`
under `Early Feature: Scenario Catalog And Run Setup`.

## Current State

M1A is complete. T001-T016 are in `tasks/completed/` with Review Outcomes.
M1B has opened: T017 is built and in review.

Breaker/control vocabulary is settled by `D-2026-09-20-breaker-vocabulary`:
position is evidence, not configuration. T017 grew that protection to the
scenario domain and moved the banned list to
`backend/tests/control_vocabulary.py`, read by both scans. It is unconditional
and covers the scenario model, the parser key vocabularies, the shipped
definition and the parser fixtures.

`config/scenarios/fuel-loss-event.yaml` is tracked, read-only, and the one
shipped scenario. Unlike `config/sites/`, that store deliberately does not ship
empty: there is no scenario create flow, so an empty store would leave a fresh
checkout nothing to inspect.

`var/sites/` holds `mg-001`, `mg-002` (cold room), and `mg-003` (two AC buses).
The user asked that these be kept as fixtures. They are gitignored, so add
fixtures when needed and do not clear, replace, or delete that directory.
`var/scenarios/` is the writable scenario store; it is gitignored, empty, and
nothing in the product can write to it yet.

## Read For The T017 Review

- `tasks/T017-scenario-catalog-fuel-loss-detail.md`
- `.ai/FEATURE_MAP.md`
  - Client-Demo Roadmap
  - `### 3. Scenario Authoring And Scenario Catalog`
  - `### 4. SimulationRun Runtime And Simulator Lab Shell`
  - `### Early Feature: Scenario Catalog And Run Setup`
- `.ai/DECISIONS.md` decision-index entries:
  - `D-2026-09-11-simulator-gate`
  - `D-2026-09-13-template-and-create-surfaces-gated`
  - `D-2026-09-13-site-foundation-persistence`
  - `D-2026-09-13-canonical-fidelity`
  - `D-2026-09-20-breaker-vocabulary`
  - `D-2026-09-20-scenario-definition-model`
  - `D-2026-09-20-scenario-definition-storage`
  - `D-2026-09-20-run-scoped-event-injection`
  - `D-2026-09-20-scenario-detail-affordances`
  - `D-2026-09-20-layout-evidence-standing`
- `.ai/CODE_STATE.md`
  - T014
  - T015
  - T016
  - T017
- `.ai/WORKFLOW.md`
  - Task Spec Size
  - Review Packet
  - Closeout

## Settled Direction For M1B

- Scenario catalog is a Simulator Lab surface, not an operator surface, and is
  gated with `simulator_lab.enabled`.
- Only `frontend/src/shell/simulatorLabRoutes.tsx` may name simulator URLs.
- Adding a truthful Scenarios route may add Scenarios to the Lab rail; operator
  navigation and operator Site tabs do not grow.
- ScenarioDefinition answers what happens during the simulated interval. Site
  Foundation answers what the Site is. The two do not duplicate each other.
- The shipped Fuel Loss Event is a directly selectable ScenarioDefinition at
  `config/scenarios/fuel-loss-event.yaml`, read through composed shipped and
  writable stores behind a scenario-domain port. Writable user definitions live
  under gitignored `var/scenarios/`.
- Scenario events are authored sub-artifacts inside a scenario version, not
  top-level stored entities. Future runtime injections are run-scoped
  SimulationRun intervention-history records and are not written back into the
  scenario version.
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
- T017 settled the ScenarioDefinition domain, its port and composed stores, the
  parser/service split over target-site resolution, the parsed-field
  public/private boundary, and the Lab's scenario surfaces. The three
  checkpoint semantics are proposed on screen and not yet answered.
