# T017 - Scenario Catalog Fuel Loss Detail

Status: planned
USER_REVIEW_REQUIRED: true

Intended branch: `task/T017-scenario-catalog-fuel-loss-detail`

## Feature

Scenario Catalog And Run Setup.

## UI-Verifiable Screen Behavior

The gated Simulator Lab gains a Scenarios catalog route and a Fuel Loss Event
detail route. A user can open the Lab, choose Scenarios, inspect the Fuel Loss
Event's identity, version, purpose, target-site requirement, public event
timeline, public authoring parameters, and visibly private expectation metadata
before any run exists.

The detail screen says what the simulated world is intended to do. It does not
claim AssetOps has observed anything, does not create a Draft SimulationRun,
and does not state any Finding, assessment, source-health result, confidence,
severity, incident, action, verification outcome, or product conclusion.

This slice carries the M1B user-review checkpoint. The screen must put a
provisional proposal in front of the user, not a menu, for scenario versioning,
event taxonomy, and the public/private scenario parameter boundary.

## Why This Is Next

M1A made configured Sites, topology, devices, mappings, and the configured SLD
visible. The next causal step is simulation authoring: a scenario can describe
what happens during a simulated interval against a declared Site before the
runtime, gateway, ingestion, or evidence path exists.

Run setup cannot be implementation-ready until the project accepts or redirects
the scenario semantics this screen proposes. T018 and T019 are therefore held
as sequence entries in `.ai/FEATURE_MAP.md` until the T017 User Review Outcome
is recorded.

## Acceptance Criteria

- Simulator Lab is the owning surface for Scenarios. Scenario catalog and
  detail routes are served only when `simulator_lab.enabled=true`, and direct
  scenario URLs fall through to the existing unavailable route behavior when
  the gate is closed.
- Only `frontend/src/shell/simulatorLabRoutes.tsx` names the new simulator
  URLs. The Lab rail may add Scenarios because the route renders real scenario
  records; operator navigation and the operator Site tab row do not grow.
- The catalog renders at least the Fuel Loss Event record from a strict scenario
  source. It distinguishes scenario identity from Site identity: scenario label,
  display name, version, and run label never become `site_id`.
- The Fuel Loss Event detail route renders version identity from the record.
  The versioning proposal is marked provisional in a visible review region and
  proposes the required fields this project should carry before run setup.
- The detail screen renders the public event/intervention timeline from the
  scenario record. Timeline rows preserve their backed ordering, timestamps or
  offsets, category, public description, and public parameters.
- The event taxonomy proposal is marked provisional in a visible review region.
  The proposal uses categories for authored causes and evidence conditions,
  including load, weather, equipment, data quality, loss/fraud, intervention,
  and maintenance, without turning breaker position or control mode into
  scenario schema vocabulary.
- Equipment and intervention events may name authored causes or actions such as
  equipment fault, generator availability, feeder/load change, maintenance, or
  operator intervention. They may not define event types, enum values, parameter
  keys, badges, columns, or filters named for breaker position or mode.
- If a scenario model or fixture introduces typed taxonomy values, the T014
  breaker/control vocabulary protection grows to cover scenario model and
  fixture vocabulary. The new protection asserts `OPEN`, `CLOSED`, `TRIPPED`,
  `AUTO`, `MANUAL`, and `BREAKER` cannot enter scenario schema vocabulary, and
  it ships with a proof that a deliberate violation fails for the intended
  reason.
- The public/private parameter proposal is marked provisional in a visible
  review region. The screen identifies which Fuel Loss Event data is public
  authoring data and which data is private test-oracle expectation metadata.
- Private expectations, if rendered at all, are visibly badged as private test
  assertions and not pipeline input. They never appear in operator routes,
  product evidence, source envelopes, exports, Site Details, Foundation, or
  normal AssetOps provenance.
- The detail screen states that ScenarioDefinition answers what happens during
  the simulated interval and Site Foundation answers what the Site is. The two
  do not duplicate one another.
- `Open target Site`, if rendered, opens the declared Site in the operator
  shell and never creates, renames, clones, or promotes a Site. If the target
  Site is unavailable in the current store, the control is absent or disabled
  with an accessible reason.
- `Run`, `Create Draft Run`, `Commit`, `Open in AssetOps`, runtime controls,
  gateway output, ingestion, Replay, Findings, and product analytics are absent
  unless a control is explicitly disabled with a stated future prerequisite.
  There is no enabled placeholder that looks live.
- No count, duration, offset, timestamp, seed, volume, rating, confidence,
  percentage, or other digit appears on screen unless the scenario or Site
  record supplies it.
- Dense timeline content owns horizontal overflow if needed and does not create
  page-level horizontal scrolling or move the Lab shell chrome.

## Required Product And Domain Semantics

- ScenarioDefinition is authoring data about simulated world events, evidence
  visibility, operational-record conditions, interventions, interval defaults,
  seed defaults, and private expectations. It is not evidence, not a run, and
  not an AssetOps conclusion.
- Fuel Loss Event is a scenario identity. It must not allocate, rename,
  duplicate, or imply a Site identity.
- Public authoring parameters are allowed to inform future run setup and
  runtime behavior. Private expectations are test-oracle metadata only and must
  stay outside the product evidence path.
- This slice proposes, but does not settle without user review, the required
  scenario versioning fields, event taxonomy, and public/private boundary.
- Scenario catalog is a Simulator Lab surface, not an operator surface, because
  it is simulation authoring. It is gated with the Lab.

## Protected Seams

- Simulator Lab gate and URL chokepoint: route/API/UI tests and architecture
  guard. Scenario URLs exist only behind `simulator_lab.enabled` and only the
  Lab route module names them.
- Operator navigation inventory: guard/test. Adding Scenarios to the Lab rail
  does not add operator rail items or operator Site tabs.
- Scenario label not Site identity: model/API/UI test. Changing the scenario
  label or version cannot change a Site row, Site route, or `site_id`.
- Public scenario authoring versus private test oracle: contract/UI test.
  Private expectation fields do not appear in public scenario API payloads
  consumed by normal product surfaces or in operator UI.
- Breaker/control vocabulary boundary: existing T014 protection extended if
  scenario typed vocabulary is introduced, with a failing proof case.
- Mockup fidelity versus product honesty: UI tests. The screen follows v6.9 and
  mockup structure only for backed scenario data and does not copy example
  digits or product claims.
- Dense timeline layout: layout evidence. The timeline has non-empty measured
  rows and keeps overflow inside its own region.

## Focused Tests And Checks

- Backend/API tests for strict scenario catalog and detail records, including
  malformed version fields, timeline rows, parameters, and private expectation
  separation.
- Frontend tests for gate-on catalog/detail rendering and gate-off absence.
- Route and architecture checks proving scenario URLs are named only in
  `frontend/src/shell/simulatorLabRoutes.tsx`.
- UI tests proving the Lab rail includes Scenarios only when the route exists
  and the operator rail/Site tab inventory is unchanged.
- UI tests proving Fuel Loss Event detail renders only record-backed digits and
  no AssetOps Finding, assessment, severity, health, confidence, incident,
  action, verification, Commit, ingestion, Replay, or product conclusion.
- UI tests covering the three provisional review regions: versioning fields,
  event taxonomy, and public/private parameter boundary.
- Test or guard proof for any new breaker/control vocabulary scan extension,
  including at least one deliberate violation that fails for the intended
  reason.
- Layout evidence with `tools/layout-evidence.mjs` because the event timeline
  is dense table content. The review packet records the command, base URL when
  non-default, and final result line.
- Run `tools/check-architecture.ps1`.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green for the touched surfaces.

## Scope Limits

- Do not implement run setup, create Draft SimulationRuns, simulator execution,
  recorded runtime playback, gateway staging, Commit, ingestion, accepted
  evidence, Replay, source health, analytics, Findings, Actions, Incidents,
  VerificationOutcomes, or exports.
- Do not add in-product scenario editing persistence, arbitrary scenario
  authoring, blank-canvas editing, scenario packs, upload/import, delete,
  duplicate, approval, publish, or history management.
- Do not clear or replace `var/sites/`. If local Site data is needed for review
  fixtures, add to it and leave `mg-001`, `mg-002`, and `mg-003` intact.
- Do not add operator navigation, operator Site tabs, or a second simulator URL
  chokepoint.
- Do not settle breaker position/control mode as scenario schema vocabulary.

## User Review

User review is required. This is the M1B checkpoint for scenario authoring
semantics and run setup language prerequisites.

The screen must ask the user to accept or redirect these provisional proposals:

- Scenario versioning fields, shown in the scenario header or version summary.
- Event taxonomy, shown with the event/intervention timeline and category
  legend.
- Public authoring parameters versus private test-oracle expectations, shown in
  separate public parameters and private expectations regions.

Accepting the screen should settle those proposals enough for the Planner to
make T018 and T019 implementation-ready. If the user redirects any proposal,
the next planning pass updates the sequence before run setup work begins.
