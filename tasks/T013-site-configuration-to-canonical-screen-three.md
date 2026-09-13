# T013 - Site Configuration To Canonical Screen Three, Minus The Diagram

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T013-site-configuration-to-canonical-screen-three`

## Feature

Site Foundation And Configuration-Only Site, canonical screen fidelity stage 6.

## UI-Verifiable Screen Behavior

Site Configuration looks like canonical screen 3, minus the diagram.

It has breadcrumbs from the Sites index to the Site to Configuration, a page
header naming the Site, and the configuration tabs Summary, Components, Control
Logic, and Settings, each rendering Foundation content the product actually has.
A Key Parameters panel shows the ratings and control mode the Foundation
declares, with canonical units.

The mockup's `Edit` and `Version History` header actions are not rendered. The
statement that configuration is fixed at creation in M1 is still on the screen.

The `Single Line Diagram (Configured)` panel is not rendered, no empty frame or
placeholder stands where it would go, and the real-power signal selector above
it is not rendered. The layout closes over that space, and the screen makes no
reference to a diagram that does not exist yet.

There are still no operational values, and the screen is still read-only for
every Site regardless of configuration origin.

## Why This Is Next

Its content became real in T008 and the shared vocabulary landed in T009, so the
tabbed arrangement and the Key Parameters panel can be filled from the Foundation
rather than framed and filled later.

It is the last fidelity stage that step 3 can honestly carry. The next stage is
the configured Single Line Diagram, which is causal step 4 and needs topology,
components, ratings, and signal-mapping truth to be validated against an
archetype before anything can be drawn.

This slice is also the easiest place in the whole feature for step 4 to be
smuggled into step 3, which is why the diagram boundary is an explicit,
separately tested acceptance criterion rather than a scope-limit line.

## Acceptance Criteria

- The page adopts the canonical layout using the T009 vocabulary: breadcrumbs,
  a page header naming the Site and the Configuration context, a tab strip, and
  the panel and table patterns.
- The configuration tabs are Summary, Components, Control Logic, and Settings.
  Each renders Foundation content that T008 already ships. No tab is empty, and
  a tab whose content the Foundation cannot supply is not rendered at all rather
  than labelled or framed empty.
- The Key Parameters panel renders only parameters the Foundation declares, with
  canonical units, and each is traceable to a Foundation field. A parameter the
  Foundation does not carry is not rendered and is not shown as a placeholder or
  a dash.
- **No `Single Line Diagram (Configured)` panel, no empty frame or placeholder
  for one, no diagram heading, and no signal selector renders.** A test asserts
  the absence of a diagram container, of any diagram heading text, and of any
  signal-selector control, and the layout is verified to close over that space
  rather than reserve it. The configured diagram is causal step 4; the signal
  selector chooses a runtime signal to overlay and is inert until causal step 6.
- The mockup's `Edit` and `Version History` header actions are absent from the
  DOM entirely, not disabled and not `aria-disabled`, along with
  `Edit Configuration`, `Duplicate Site`, `Delete Site`, `Save`, `Publish`,
  `Rename`, approve, diff, history, rollback, and the site image `Change`
  control. A test asserts DOM absence using a query that would fail if any of
  them rendered disabled.
- The statement that configuration is fixed at creation in M1 remains on the
  screen, unchanged in meaning from what the user accepted at the T008
  checkpoint, and remains visible in the canonical layout rather than being
  demoted to a footnote.
- The screen is read-only for every Site regardless of configuration origin. A
  `SHIPPED`-origin fixture Site and a `USER`-origin Site render the same
  read-only surface and differ only in origin and template provenance.
- The six provenance and status concepts still render as independent facts, and
  neither configuration origin nor source mode is derived from or rendered as a
  proxy for the other.
- No operational values render: no telemetry, charts, source health, gateway
  status, evidence, analytics, Replay, or Findings. Devices are labelled
  configured or awaiting evidence, never healthy, online, or offline, and no
  source-health or assessment vocabulary appears anywhere on the screen.
- No mockup literal renders as content. Every value traces to the record under
  test.
- Site Configuration presentation stays in `frontend/src/sites/**`. The
  substrate single-definition and leaf-direction guards pass, no `variant`,
  `mode`, `shell`, or `isLab` prop is introduced, and no extension slot is
  needed here because nothing on this screen is shell-specific.
- No update or delete route for a Site exists in the served route inventory, in
  either flag state, and the screen renders identically with
  `simulator_lab.enabled` true and false.
- Every acceptance criterion of T008 and T009 still holds unchanged in meaning.
  Where a test query must change because markup changed, the assertion is
  preserved or strengthened, never loosened.

## Required Product And Domain Semantics

- Canonical Site Foundation is the source of truth for components, topology,
  connectivity, ratings, devices, and signal availability. This screen renders
  that truth and creates none of it.
- A diagram is a presentation strategy over canonical topology, and it does not
  exist yet. An empty frame labelled for a future diagram is the layout form of
  a fabricated value: it makes the screen look finished and teaches the user
  that a capability is nearly there.
- The Site Configuration UI stays read-only for every Site for the whole of M1
  and must not imply in-place edit, Save, Publish, approval, rename, duplicate,
  delete, or configuration history.
- `Version History` is not rendered even disabled, because no configuration
  change model exists and the eventual capability in that territory has a
  different name and a different meaning.
- What this project calls Site Configuration is v6.9's `Foundation` tab on a
  Site. The tab names used here are the mockup's configuration tabs, not v6.9's
  operator Site tab set, and adopting them does not commit the operator Site tab
  set to the mockup's.

## Protected Seams

- Mockup fidelity versus product honesty: CI guard.
  Canonical layout only for content the product can source; no mockup literal as
  content; deferred-by-decision controls absent from the DOM rather than
  disabled; the diagram panel and signal selector absent rather than framed
  empty.
- Read-only configuration UI: review-time + contract test.
  Every Site renders read-only regardless of origin; the fixed-at-creation
  statement stays; no update or delete route exists for a Site.
- Configuration-only Site states: CI guard.
  Declared configuration renders; operational evidence does not, and its absence
  is explicit rather than zeroed.
- SLD archetype boundary: unit/contract test.
  No diagram, no archetype, and no layout strategy is introduced here, so
  canonical topology cannot acquire a second model in a fidelity slice.
- Shared Site presentation substrate: CI guard.
  Configuration presentation resolves in `frontend/src/sites/**` only; the
  substrate stays a leaf with no discriminant.
- YAML configuration authority: unit/contract test.
  The screen renders the strictly validated document and introduces no second
  representation.
- Vocabulary separation: CI/review check.
  No source-health or assessment vocabulary appears.
- Simulator feature gate: CI guard.
  Site Configuration is never gated and renders identically in both flag states.

## Focused Tests And Checks

- UI test asserting the tab set, and that each tab renders record-sourced
  Foundation content with no empty tab.
- UI test asserting the Key Parameters panel renders only Foundation-declared
  parameters with canonical units, and renders no placeholder for an undeclared
  one.
- UI test asserting the absence of a diagram container, any diagram heading
  text, and any signal-selector control, plus a layout assertion that no
  reserved empty region stands where the diagram would go.
- UI test asserting DOM absence, not disabled state, of `Edit`,
  `Version History`, `Edit Configuration`, `Duplicate Site`, `Delete Site`,
  `Save`, `Publish`, `Rename`, and the image `Change` control.
- UI test asserting the fixed-at-creation statement is present and unchanged in
  meaning.
- UI test rendering a `SHIPPED`-origin fixture Site and a `USER`-origin Site and
  asserting both are read-only and differ only in origin and template
  provenance.
- UI test asserting no operational value, source-health term, or assessment term
  renders.
- API test asserting no update or delete route for a Site exists in either flag
  state.
- UI test asserting the screen renders identically with `simulator_lab.enabled`
  true and false.
- Accessibility checks on the tab strip, panels, and tables.
- Run `tools/check-architecture.ps1`, including the T005 persistence checks and
  the T006 substrate checks.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Do not render the Single Line Diagram, an empty frame for it, a placeholder or
  skeleton labelled for it, a reserved region sized for it, or its signal
  selector. Do not add an SLD archetype, an SLD view model, topology validation,
  or auto-layout. That is causal step 4.
- Do not add a Devices & Sensors screen or a device management surface. That is
  causal step 4.
- Do not add in-place editing, Save, Publish, rename, duplicate, delete,
  approvals, configuration diff, history, or rollback, and do not add disabled
  placeholders for any of them.
- Do not render `Edit` or `Version History` in any state.
- Do not change the fixed-at-creation statement or any other copy the T008
  checkpoint settled.
- Do not add a tab that the Foundation cannot fill, and do not label a tab in
  place on this screen: the labelled-in-place treatment belongs to the Site tab
  set on Site Details, not to configuration subtabs that either have Foundation
  content or should not exist.
- Do not add a runtime or evidence value slot, even an empty one.
- Do not define Site presentation outside `frontend/src/sites/**`, and do not
  add a shell, mode, or variant discriminant prop.
- Do not gate Site Configuration, its route, or its API.
- Do not add scenarios, run setup, simulator execution, ingestion, evidence,
  source health, charts, analytics, Replay, or Findings.
- Do not weaken any T003 to T012 assertion. Where markup changes force a query
  change, preserve or strengthen the assertion; never relax it.

## User Review

User review is deliberately not required for this slice. It adds no capability
and no product language: the configuration-only language, the fixed-at-creation
statement, and the absent-rather-than-disabled treatment of `Edit` and
`Version History` were all settled at the T008 checkpoint, and this slice only
arranges content the product already renders.

This is the last planned slice of Causal Sequencing step 3. Step 4, topology,
devices, and the configured Single Line Diagram, is not planned and should not
be started until the T008 checkpoint is accepted and the Architect has sequenced
it.
