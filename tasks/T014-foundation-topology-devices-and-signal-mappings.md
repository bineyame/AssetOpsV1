# T014 - Foundation Topology, Devices, And Signal Mappings

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T014-foundation-topology-devices-and-signal-mappings`

## Feature

Topology, Devices, And SLD.

## UI-Verifiable Screen Behavior

Foundation stops describing topology, devices, signal mappings, and control
assumptions as `Not declared` because the Foundation can now carry them. The
screen renders the configured topology and device/signal relationships as
read-only configuration facts, using the same Site read path as Site Details and
Foundation.

No Single Line Diagram renders in this slice. No diagram frame, signal selector,
runtime value, evidence value, source health, product health, telemetry, chart,
Replay, or Finding appears. The screen remains read-only for every Site in both
flag states, and it still renders no edit, save, publish, history, duplicate, or
delete affordance.

If a Site's YAML is invalid, has broken component references, duplicate
identities, unsupported units, unsupported topology values, or invalid
device-to-signal mappings, it is refused at load rather than normalized or
silently ignored.

## Why This Is Next

This is Causal Sequencing step 4's first dependency. The configured SLD and
the configured SLD and device/signal presentation cannot be truthful until
component, connection, rating, device, and signal-mapping truth exists in the
canonical Foundation.

T008 deliberately left devices, signal mappings, and control assumptions as
stated absences because the M1 `SiteFoundation` carried only `version`,
`valid_from`, `summary`, and `components`. This slice changes that constraint
explicitly before any diagram or device table reads it.

It also expands the shared Site Foundation frontend/backend contract, so it is
the right place to close the 2026-09-17 fetch-seam decision with a focused
integration test before more UI is built on top of the expanded shape.

## Acceptance Criteria

- The canonical Foundation schema expands from `version`, `valid_from`,
  `summary`, and `components` to include topology, devices, signal mappings,
  and control assumptions. The task states the exact backend schema, write path,
  and wire shape changes on both the shipped read-only template store and the
  user-authored writable Site store.
- YAML remains the authoritative representation in both stores and is strictly
  validated on load through the same parser. There is no lenient shipped path,
  no lenient user-authored path, and no frontend-only interpretation of invalid
  configuration.
- Created Sites copy the expanded Foundation seed from the selected template.
  The user store write path persists the expanded document atomically, and a
  failed validation or write leaves the store unchanged.
- The API response for `GET /api/sites/{site_id}` includes the expanded
  Foundation shape only after the backend validates it. API tests pin the exact
  Foundation keys so later slices cannot add diagram runtime fields or evidence
  fields before a screen renders them truthfully.
- Validation rejects duplicate component, topology node, connection, device,
  signal, or mapping identities; invalid component references; invalid device
  references; mappings to undeclared signals; unsupported rating or signal
  units; unknown topology roles; unknown component roles; unknown control
  assumption values; and unknown keys.
- Device-to-signal mappings are canonical configuration facts. They are not
  inferred from display names, topology positions, protocol labels, simulator
  fixture names, or mockup text.
- Foundation renders configured topology and device/signal relationship facts
  from the persisted document, enriching the already-rendered Topology and
  Controls subtabs from T013. The previous `Not declared` absences for devices,
  signal mappings, and control assumptions disappear only when the record
  actually supplies valid values.
- No Single Line Diagram panel, diagram placeholder, empty frame, diagram
  heading, or signal selector renders. A UI test asserts DOM absence, not merely
  disabled state.
- No runtime or evidence values render: no telemetry, latest reading, source
  health, gateway status, product health, chart, Replay, Finding, `OFFLINE`,
  zero defaults, or stale/fresh badges. Devices are configured assets awaiting
  runtime or evidence, not operationally healthy or unhealthy.
- Foundation remains an operator capability and renders identically with
  `simulator_lab.enabled` true and false.
- The expanded Site presentation stays in `frontend/src/sites/**`. The shared
  substrate remains a leaf with no shell, simulator, feature-flag import, or
  shell/mode/variant discriminant.
- A focused integration test binds the real frontend Site Foundation clients to
  representative backend responses across list/detail read, create success,
  validation refusal, empty state, and not-found or store-error envelopes where
  practical.

## Required Product And Domain Semantics

- Canonical Site Foundation is the source of truth for components, topology,
  connectivity, ratings, devices, signal availability, mappings, and control
  assumptions. UI components, SLD view models, simulator runtime, and evidence
  overlays read from it; none becomes a second topology authority.
- YAML remains authoritative for M1 configuration. The UI renders and explains
  the validated document and never becomes a second source of truth.
- Component truth remains distinct from device-reported evidence:
  component truth -> device/sensor behavior -> reported signal -> gateway ->
  Source Envelope -> AssetOps accepted evidence.
- Configured devices may appear before they report, labelled as configured or
  awaiting runtime/evidence, never as healthy, online, offline, stale, or
  degraded.
- No configuration-change, Changes, history, diff, approval, or rollback model
  is introduced here.
- Breaker/control state vocabulary and whether breakers are devices, component
  state, or both is not decided here. The task must surface that ambiguity for
  the T016 user-review checkpoint and avoid baking a final product vocabulary
  into schema names or UI copy beyond the minimum strict values needed to parse
  the M1 template.
- How cold-room process symbols relate to mini-grid electrical topology is not
  decided here. The schema may carry the facts needed for the current hybrid
  mini-grid template, but the visual/domain treatment is deferred to the T016
  checkpoint.

## Protected Seams

- YAML configuration authority: unit/contract test.
  The expanded Foundation is validated on load in both stores, through one
  strict parser, and invalid topology or mappings fail explicitly.
- Canonical topology authority: unit/contract test.
  Topology, device, signal, and mapping truth lives in the Foundation, not in
  the UI, an SLD template, a simulator fixture, or a mockup.
- Device-to-signal mapping: unit/contract test.
  Device rows and later SLD labels can only describe declared mappings.
- Configuration persistence port: CI guard.
  Store and YAML details stay behind adapters and the composition root.
- Shared Site presentation substrate: CI guard.
  Expanded read model and view model live in `frontend/src/sites/**` and remain
  shell-neutral.
- Configuration-only Site states: CI guard.
  Declared configuration renders without fabricated telemetry, health, charts,
  or conclusions.
- Mockup fidelity versus product honesty: CI guard.
  No mockup value, diagram placeholder, or disabled deferred control appears.

## Focused Tests And Checks

- Backend parser and semantic validation tests for the expanded Foundation:
  topology references, duplicate identities, devices, signals, mappings, units,
  ratings, control assumptions, unknown keys, and unsupported values.
- Adapter tests proving the shipped template store and user-authored store use
  the same strict expanded parser, and that failed user-store writes leave the
  store unchanged.
- API tests pinning the expanded `GET /api/sites/{site_id}` Foundation shape,
  including malformed store data and unknown `site_id`.
- Create-flow tests proving a Site copied from the hybrid mini-grid template
  persists the expanded Foundation seed and does not live-reference the
  template.
- Focused frontend/backend integration test for the shared Site Foundation
  clients over representative backend responses.
- UI test asserting Foundation renders topology and device/signal
  relationship facts from the record and no longer shows `Not declared` for
  values the expanded Foundation supplies.
- UI test asserting no SLD panel, diagram heading, empty frame, signal selector,
  runtime value, evidence value, source-health term, product-health term, zero
  default, or `OFFLINE` state renders.
- Run `tools/check-architecture.ps1`, including persistence and substrate
  guards.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Do not render the Single Line Diagram, an empty frame for it, a placeholder,
  a diagram heading, or the signal selector. T015 creates the view model and
  T016 renders the configured diagram.
- Do not add arbitrary graph auto-layout, drag/drop schematic editing, CAD
  behavior, topology editing, runtime simulation, evidence overlays, product
  health, source health, analytics, Replay, or Findings.
- Do not add in-place Foundation editing, Save, Publish, approval, rename,
  duplicate, delete, configuration history, Changes, diff, rollback, arbitrary
  YAML import, or template authoring.
- Do not create a second endpoint for Foundation unless the existing Site read
  path cannot truthfully carry the expanded Foundation; if that happens, stop
  and return to planning rather than inventing a new resource.
- Do not decide the breaker/control vocabulary or cold-room symbol treatment
  silently.

## User Review

User review is not required for this slice. It changes the configuration
contract and validation surface, but it does not yet fix the visual SLD
archetype, incompatible-topology UI, cold-room/electrical symbol treatment, or
final device/signal wording. Those are held for the T016 checkpoint where the
user can see them together.
