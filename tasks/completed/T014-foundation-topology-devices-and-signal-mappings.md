# T014 - Foundation Topology, Devices, And Signal Mappings

Status: complete
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
Any dense relationship table keeps its configured columns and owns its own
horizontal overflow instead of pushing shell chrome.

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
- Dense topology, device, signal, or mapping tables preserve their configured
  columns at all widths where they render. If they cannot fit, they scroll
  inside their own region and do not create document-level horizontal overflow.
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
- Shell overflow containment: review-time plus focused tests/checks.
  Dense Foundation configuration tables own horizontal overflow and shell
  chrome stays anchored.

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
- UI test asserting any rendered topology/device/signal/mapping table keeps its
  configured columns and has an owning overflow region rather than relying on
  document-level horizontal scrolling.
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
- Do not hide topology, device, signal, or mapping columns by viewport or
  replace their tables with a separate narrow-width card presentation.

## User Review

User review is not required for this slice. It changes the configuration
contract and validation surface, but it does not yet fix the visual SLD
archetype, incompatible-topology UI, cold-room/electrical symbol treatment, or
final device/signal wording. Those are held for the T016 checkpoint where the
user can see them together.

## Review Outcome

Independent review by Codex: **accept with findings fixed on the branch**. Two
Medium, both fixed, and the first opened a third defect neither the packet nor
the finding had named.

This slice was built by a different Implementer agent from T009-T013. Its
numbers were verified independently before review and again after: backend
`441 passed`, frontend `560 passed` across 19 files, `tsc` clean, build clean,
both guards passing, `main` untouched throughout.

### Finding 1: document bounds relaxed on a false premise

`MAX_DOCUMENT_NODES` 2,000 -> 8,000 and `MAX_DOCUMENT_TEXT_LENGTH` 64,000 ->
96,000, on both document families, justified in the packet by the expanded
template no longer fitting the old budget.

The template fits with room to spare: 11,417 characters and about 328 YAML
nodes, five to six times under the old limits. Both restored.

**Restoring them exposed three caps that could never fire.** With the ceiling
back at 2,000 nodes, cardinality tests failed - not because a document was
accepted but because it was refused by the wrong guard, naming node counts
rather than the collection an author had too many of. Measured by bisection:

| Cap | Was | Ceiling refuses at | Now |
| --- | --- | --- | --- |
| `MAX_DEVICES` | 128 | 77 devices | 64 |
| `MAX_SIGNAL_MAPPINGS` | 256 | 208 mappings | 160 |
| `MAX_SIGNALS_PER_DEVICE` | 32 | reachable | 32, unchanged |
| `MAX_TOPOLOGY_NODES` | 64 | reachable | 64, unchanged |
| `MAX_CONNECTIONS` | 128 | reachable | 128, unchanged |
| `MAX_CONTROL_ASSUMPTIONS` | 32 | reachable | 32, unchanged |

Each dead cap moved under the ceiling rather than the ceiling moving over it.
Raising a whole-document guard to make a per-section guard reachable is
backwards, and was how the bounds came to be relaxed in the first place.

Three dead caps in one slice made the instances stop being the point.
`TestEveryCapCanFire` holds the property: for every cap, build a document at
`cap + 1` and require the refusal to name the limit rather than the node count.
A cap added above the ceiling now fails there. Proved by putting
`MAX_SIGNAL_MAPPINGS` back to 256, which fails it on both families.

This is the third appearance of the same family - two guard patterns that could
never match in T011A, a diagram ban that could never match in T013, and now
caps above their own ceiling.

### Finding 2: ignored local Site data discarded

`var/sites/` held two locally created Sites and now holds one. `testsite1.yaml`
was deleted so browser evidence could run over deterministic content, and that
directory is gitignored, so it is gone rather than recoverable.

The Reviewer's judgement is right: nothing in T014 required deleting rather
than adding a Site, or pointing the evidence run at a new Site alongside the
existing data. `.ai/PROJECT_RULES.md` says do not discard unrelated user
changes, and data outside version control is where that matters most. It is
recorded as a deviation rather than residual risk, and the user was told
directly rather than left to find it in a packet.

### What the Reviewer confirmed rather than accepted

- `null` versus `[]` holds in the parser, the frontend response guard and the
  render path. Empty lists are refused by `_require_non_empty_list`, the client
  refuses empty `devices`, `signal_mappings` and `control_assumptions`, and no
  valid document can produce an empty table.
- No additional tracked-code defect in the hotspots the dispatch named: the
  shared-parser identity, the rewritten `Not declared` reasons, the frozenset
  scan that keeps breaker vocabulary out of schema names, and the two
  deviations the Implementer took deliberately.

### Checks

Reviewer: architecture guard, workflow guard, backend suite and `tsc` all
passed. The frontend suite, the production build and the browser evidence could
not run under its sandbox, for the known esbuild reason.

Implementing session, after both fixes: backend `441 passed`, frontend
`560 passed` across 19 files, `tsc --noEmit` clean, build clean at 221.31 kB,
both guards pass, and `tools/layout-evidence.mjs` reports all claims holding at
1280x800, 1000x700 and 640x700 - the last added because at the wider two every
table fits, so the overflow claim was passing on an empty set.

### Not verified

Nobody has judged whether this screen reads well. Six tables on one page is new
and unjudged; `node_id` and `component_id` carry the same string in the shipped
template, so the nodes table shows two identical columns; and whether identity
columns earn their width is a product question no measurement answers.
