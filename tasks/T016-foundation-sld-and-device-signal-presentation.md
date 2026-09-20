# T016 - Foundation SLD And Device/Signal Presentation

Status: in_review
USER_REVIEW_REQUIRED: true

Intended branch: `task/T016-foundation-sld-and-device-signal-presentation`

## Feature

Topology, Devices, And SLD.

## UI-Verifiable Screen Behavior

Foundation renders the configured Single Line Diagram using the hybrid mini-grid
SLD view model and renders device/signal configuration from the same canonical
Foundation source. SLD labels, ratings, configured signal availability, and
device rows agree because they are derived from the same validated topology,
device, and mapping facts.
The diagram area and device/signal tables obey the viewport policy: dense
content owns its own overflow and the shell chrome stays anchored.

This content lives inside the renamed Foundation surface and its subtab
architecture. It does not add `Devices & Sensors` as an operator Site tab, and
it does not copy `ScreenMockups.png` screen 2 tab vocabulary into the operator
Site shell.

For an incompatible topology, the SLD area shows an explicit unavailable state
with a reason. It does not hide assets, draw a partial diagram as complete, or
fall back to a generic graph.

Runtime/evidence value slots are visible only as empty configured slots or
`Awaiting runtime/evidence`; they do not contain live values. There are no
runtime simulations, evidence overlays, source-health states, product-health
states, telemetry charts, Replay, Findings, graph editing, drag/drop, or
auto-layout controls.

## Why This Is Next

T014 makes topology, devices, and mappings canonical. T015 creates the SLD
view-model boundary and compatibility result. This slice is the first
user-visible step-4 outcome: the configured physical model and SLD become real
inside Foundation while operational evidence remains unavailable.

It carries the M1A user-review checkpoint because this is where the SLD
archetype, incompatible-topology UI, cold-room/electrical symbol treatment, and
device/signal wording become visible product and domain representation.

It also closes the M1A block. No T017+ task is created here; scenario catalog
and run setup stay behind their own later checkpoint.

## Acceptance Criteria

- Foundation renders a `Single Line Diagram (Configured)` panel for a compatible
  hybrid mini-grid Site using the T015 SLD view model. The diagram renders
  configured topology, component labels, ratings, connections, and declared
  signal availability from the Foundation.
- The device/signal presentation renders from the same validated Foundation
  facts as the SLD: devices, mapped components, signal IDs, display labels,
  units, protocol metadata where declared, and sample cadence where declared.
- Device/signal tables preserve their configured columns at every width where
  they render. If they cannot fit, they scroll inside their own region rather
  than causing document-level horizontal overflow.
- This device/signal content is presented within Foundation's subtab
  architecture. It may enrich Topology and Controls or a clearly scoped
  Foundation panel, but it does not add `Devices & Sensors` as an operator Site
  tab.
- SLD labels and device/signal rows agree on component names, device names,
  ratings, units, and signal availability. A UI test asserts agreement from one
  fixture rather than duplicating expected text in two separate snapshots.
- The SLD archetype owns presentation only. It does not create, remove, rename,
  reorder, or reinterpret canonical components, devices, signals, mappings, or
  connections. A view-model test compares rendered IDs with Foundation IDs.
- The real-power signal selector from the mockup remains absent unless this
  slice can make it a configured-signal selector with no runtime value binding.
  If rendered, it is disabled with an accessible reason naming the missing
  runtime/evidence prerequisite and never selects or overlays a live value.
- Runtime/evidence value slots render only as empty configured slots or
  `Awaiting runtime/evidence`. No numeric reading, timestamp, freshness, quality,
  source health, product health, simulator truth, accepted evidence value, chart,
  Replay, or Finding appears.
- For incompatible topology, the SLD panel renders an explicit unavailable state
  with a stable, accessible reason. It lists or links to the affected configured
  facts where useful, but it does not hide unmatched assets, render a partial
  diagram as complete, or fall back to a generic graph.
- The configured SLD region may provide internal scrolling or fit treatment for
  the diagram itself, but it must not move the operator rail, workspace bar, or
  page-level chrome. Exact visual fit remains browser/review-time evidence.
- The device/signal presentation still renders for an incompatible SLD if the
  device/mapping configuration itself is valid, because a diagram incompatibility
  is not evidence that the Site has no devices.
- The visible UI surfaces the two unresolved semantics as decisions for review
  rather than answering them silently: breaker/control state vocabulary and
  whether breakers are devices, component state, or both; and how cold-room
  process symbols relate to mini-grid electrical topology.
- Cold-room/process symbols are rendered only where backed by configured
  components and the candidate treatment is reviewable. They are not used to
  imply process telemetry, product health, temperature evidence, or a complete
  cold-chain model.
- The screen remains read-only. `Edit`, `Edit Configuration`, `Version History`,
  `Duplicate Site`, `Delete Site`, `Save`, `Publish`, `Rename`, approval, diff,
  history, rollback, graph edit, drag/drop, auto-layout, and diagram editing
  controls are absent from the DOM entirely, not disabled.
- Foundation remains ungated and renders identically with `simulator_lab.enabled`
  true and false, except for no simulator-specific runtime controls because none
  are rendered here.
- No operator navigation item is added. The operator Site tab row remains the
  T011A inventory: Overview and Foundation destinations, and Health,
  Performance, Findings, Work, Financials, and Evidence labelled in place.
- `Configuration`, `Devices`, `Devices & Sensors`, `Gateway`, `Ingestion`,
  `Events`, and `Logs` do not render as operator Site tabs.

## Required Product And Domain Semantics

- The SLD is a configured diagram, not an operational diagram. It represents
  declared topology, components, ratings, devices, and signal availability.
- Runtime values are future Simulator Lab runtime bindings; evidence values are
  future AssetOps accepted-evidence bindings. Neither is present in this slice,
  and neither may be fabricated from configuration.
- Unsupported topology is a first-class unavailable state. It is more truthful
  than hiding assets or drawing a plausible but incomplete diagram.
- Devices and sensors are configured assets awaiting runtime/evidence. They are
  not healthy, unhealthy, online, offline, stale, fresh, degraded, or unknown in
  this slice.
- Device/signal presentation is Foundation content. `Devices & Sensors` is not
  an operator Site tab in M1.
- Breaker/control state vocabulary and whether breakers are devices, component
  state, or both must be presented as a review decision. The implementation may
  use temporary internal names only where required for parsing and rendering the
  current fixture, and those names must not be exposed as final product
  vocabulary unless accepted at review.
- Cold-room process symbols must be presented as a review decision. In M1A they
  may appear as configured loads/process components inside the mini-grid
  topology, but they must not claim cold-chain telemetry, refrigeration
  performance, temperature compliance, or product health.

## Protected Seams

- SLD presentation boundary: unit/contract test.
  The rendered diagram is presentation over canonical topology and never a
  second topology model.
- Canonical topology authority: unit/contract test.
  Rendered component and connection IDs match the Foundation.
- Device-to-signal mapping: UI + unit test.
  Device/signal presentation and SLD signal availability come from the same
  declared mappings.
- Foundation subtab and operator Site tab inventory: CI guard.
  Foundation content does not create a `Devices & Sensors` operator Site tab,
  and the T011A operator Site tab inventory remains intact.
- Unsupported-topology unavailable state: UI test.
  Incompatible topology renders an explicit reason and no misleading diagram.
- Configuration-only Site states: CI guard.
  Configured assets render without operational evidence, health, charts, or
  conclusions.
- Mockup fidelity versus product honesty: CI guard.
  The diagram area follows canonical screen 3 only for backed content; controls
  with no capability are absent or disabled with named prerequisites under the
  three-state rule.
- Simulator/product and evidence loop boundaries: CI guard.
  No simulator truth, staged envelope, accepted evidence, source health, or
  product conclusion is read by this configured SLD.
- Shared Site presentation substrate: CI guard.
  Foundation remains in `frontend/src/sites/**` and shell-neutral.
- Shell overflow containment: review-time plus focused tests/checks.
  The configured SLD and device/signal tables own their overflow instead of
  creating page-level horizontal scrolling.

## Focused Tests And Checks

- UI test rendering a compatible hybrid mini-grid Site and asserting the SLD
  panel contains configured component labels, ratings, connections, and declared
  signal availability from the record.
- UI test asserting SLD labels and device/signal rows agree on names, ratings,
  units, and signal availability from the same fixture.
- UI test asserting device/signal tables keep their configured columns and have
  an owning overflow region, with no viewport-based column hiding or card
  replacement.
- View-model test comparing rendered component, connection, device, signal, and
  mapping IDs with canonical Foundation IDs and asserting no extra or missing
  element.
- UI test rendering an incompatible topology and asserting the explicit
  unavailable state, accessible reason, and absence of a partial or generic
  diagram.
- UI test asserting the device/signal presentation still renders valid device
  and mapping configuration when only the SLD archetype compatibility fails.
- UI test asserting runtime/evidence value slots are empty or labelled awaiting
  runtime/evidence and contain no numeric reading, timestamp, freshness, quality,
  health, simulator truth, accepted evidence value, chart, Replay, or Finding.
- UI test asserting DOM absence of edit/save/history/delete controls and of
  graph editing, drag/drop, auto-layout, CAD, and diagram-edit controls.
- UI test covering the signal selector treatment: either absent, or disabled
  with an accessible reason and no value-binding behavior.
- UI/review fixture showing the proposed breaker/control and cold-room symbol
  treatments so the user can accept or redirect them.
- UI test asserting Foundation renders with `simulator_lab.enabled` true and
  false and no operator navigation item is added.
- Operator Site tab test asserting `Devices & Sensors` is not added as a Site
  tab and the T011A tab inventory remains unchanged.
- Accessibility checks for diagram labels, unavailable state, table headers, and
  value-slot labels.
- Run `tools/check-architecture.ps1`.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Do not create T017 or any scenario catalog/run setup work.
- Do not implement arbitrary graph auto-layout, drag/drop schematic editing,
  topology editing, CAD behavior, or automatic routing beyond the fixed hybrid
  mini-grid archetype.
- Do not bind simulator runtime values, accepted evidence values, latest
  telemetry, source health, product health, evidence overlays, charts, Replay,
  analytics, or Findings.
- Do not build Simulator Lab runtime, the Lab Site view, run setup, scenario
  catalog, gateway output, Commit, ingestion, or evidence views.
- Do not add in-place Foundation editing, Save, Publish, approval, rename,
  duplicate, delete, configuration history, rollback, graph editing, or diagram
  editing controls.
- Do not add or rename operator Site tabs. In particular, do not introduce
  `Devices & Sensors` as an operator Site tab.
- Do not hide device/signal columns by viewport, move them to a separate
  narrow-width card layout, or let the SLD/device presentation create
  document-level horizontal overflow.
- Do not silently settle breaker/control vocabulary or cold-room symbol
  treatment without presenting them in the User Review section.

## User Review

User review is required. This is the M1A checkpoint for the configured SLD,
device/signal presentation, and topology/device/signal representation inside
Foundation.

What the user is being asked to settle:

- The hybrid mini-grid SLD archetype as the M1 presentation strategy, including
  symbol placement, visual roles, labels, and the fact that it is not arbitrary
  auto-layout or CAD editing.
- The incompatible-topology unavailable state: its wording, whether it is
  prominent enough, and whether it makes clear that unsupported topology is not
  the same as "no configured assets."
- The device/signal wording for configured devices, signal availability,
  protocol metadata, sample cadence, and awaiting runtime/evidence slots.
- Breaker/control state vocabulary and whether breakers are devices, component
  state, or both.
- How cold-room process symbols should relate to mini-grid electrical topology,
  and whether the proposed treatment avoids implying cold-chain telemetry,
  product health, or a complete cold-chain model.

Capability planning for M1A stops at this checkpoint. M1B, Scenario Catalog And
Run Setup, is not planned or started until this checkpoint is accepted or
redirected.
