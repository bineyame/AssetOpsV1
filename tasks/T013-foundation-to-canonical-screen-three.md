# T013 - Foundation To Canonical Screen Three, Minus The Diagram

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T013-foundation-to-canonical-screen-three`

## Feature

Site Foundation And Configuration-Only Site, canonical screen fidelity stage 6.

## UI-Verifiable Screen Behavior

Foundation looks like canonical screen 3, minus the diagram, and uses the
Foundation name and route settled in T011A.

It has breadcrumbs from the Sites index to the Site to Foundation, a page header
naming the Site and the Foundation context, and the filtered v6.9 Foundation
subtab row from line 2117. Definition, Topology, and Controls render with
current M1 limits. The content panel currently headed `Foundation` is renamed
or reworked as Definition so the page does not carry a redundant
Foundation-under-Foundation heading. Readiness is labelled in place because
there is no accepted evidence/readiness model. Changes is absent in every state
until a reviewed configuration-change capability exists.

The mockup's `Edit` and `Version History` header actions are not rendered. The
statement that configuration is fixed at creation in M1 is still on the screen.

The `Single Line Diagram (Configured)` panel is not rendered, no empty frame or
placeholder stands where it would go, and the real-power signal selector above
it is not rendered. The layout closes over that space, and the screen makes no
reference to a diagram that does not exist yet.

There are still no operational values, and the screen is still read-only for
every Site regardless of configuration origin.

## Why This Is Next

T011A renamed the surface and introduced the canonical operator Site tab row.
T012 dressed Site Details against that row. This slice dresses the Foundation
destination itself, using the settled Foundation subtab architecture rather than
the old mockup tab names.

It is the last fidelity stage that step 3 can honestly carry. The next stage is
the configured Single Line Diagram, which is causal step 4 and needs topology,
components, ratings, and signal-mapping truth to be validated against an
archetype before anything can be drawn.

This slice is also the easiest place for step 4 or change-history semantics to
be smuggled into step 3, so the diagram boundary and the absence of Changes are
separately tested acceptance criteria.

## Acceptance Criteria

- The page adopts the canonical layout using the T009 vocabulary: breadcrumbs,
  a page header naming the Site and Foundation context, the Foundation subtab
  row, and the panel and table patterns.
- The Foundation subtab row renders Definition, Topology, Controls, and
  Readiness in that order. Changes is absent in every state.
- Definition renders record-sourced Site Foundation identity, purpose/summary,
  validity, and provenance fields available in the current read model.
- The existing panel headed `Foundation` is renamed or reworked into the
  Definition content area. The final page must not show a `Foundation` panel
  heading directly under the `Foundation` page title.
- Topology renders with current M1 limits: it may state that topology, devices,
  and signal mappings are not declared where the schema does not yet carry
  them, using the accepted T008 absence semantics.
- Controls renders with current M1 limits: it may state declared or
  not-declared control assumptions without inventing a control model.
- Readiness is labelled in place only until evidence readiness has a source
  contract. It is not a link, button, disabled control, route, empty panel, or
  placeholder content area.
- The old Summary, Components, Control Logic, and Settings subtab set does not
  render.
- The Key Parameters panel renders only parameters the Foundation declares, with
  canonical units, and each is traceable to a Foundation field. A parameter the
  Foundation does not carry is not rendered and is not shown as a placeholder or
  a dash.
- No `Single Line Diagram (Configured)` panel, no empty frame or placeholder for
  one, no diagram heading, and no signal selector renders. A test asserts the
  absence of a diagram container, of any diagram heading text, and of any
  signal-selector control, and the layout is verified to close over that space.
- The mockup's `Edit` and `Version History` header actions are absent from the
  DOM entirely, not disabled and not `aria-disabled`, along with
  `Edit Configuration`, `Duplicate Site`, `Delete Site`, `Save`, `Publish`,
  `Rename`, approve, diff, history, rollback, and the site image `Change`
  control.
- The statement that configuration is fixed at creation in M1 remains on the
  screen, unchanged in meaning from what the user accepted at the T008
  checkpoint, and remains visible in the canonical layout.
- The screen is read-only for every Site regardless of configuration origin. A
  `SHIPPED`-origin fixture Site and a `USER`-origin Site render the same
  read-only surface and differ only in origin and template provenance.
- The six provenance and status concepts still render as independent facts, and
  neither configuration origin nor source mode is derived from or rendered as a
  proxy for the other.
- No operational values render: no telemetry, charts, source health, gateway
  status, evidence, analytics, Replay, or Findings. Devices are labelled
  configured or awaiting evidence only when declared by configuration, never
  healthy, online, or offline.
- No mockup literal renders as content. Every value traces to the record under
  test.
- Foundation presentation stays in `frontend/src/sites/**`. The substrate
  single-definition and leaf-direction guards pass, no `variant`, `mode`,
  `shell`, or `isLab` prop is introduced, and no extension slot is needed here
  because nothing on this screen is shell-specific.
- Any Foundation table or subtab row introduced or restyled here owns its own
  overflow if dense. Shell chrome must not move because Foundation content is
  wider than the viewport.
- No update or delete route for a Site exists in the served route inventory, in
  either flag state, and the screen renders identically with
  `simulator_lab.enabled` true and false.
- Every acceptance criterion of T008, T009, and T011A still holds unchanged in
  meaning. Where a test query must change because markup changed, the assertion
  is preserved or strengthened, never loosened.

## Required Product And Domain Semantics

- Mockscreen fidelity is an explicit delivery goal for these slices. The task
  should move the real screen as close to the canonical mockscreen's visual and
  information architecture as current backed content honestly allows.
- Canonical Site Foundation is the source of truth for components, topology,
  connectivity, ratings, devices, and signal availability. This screen renders
  that truth and creates none of it.
- The Foundation subtab row derives from v6.9 line 2117 and is filtered by the
  accepted T008 decision: Changes is absent until a reviewed change capability
  exists.
- T011A deliberately left the redundant Foundation panel heading for this
  slice. v6.9 names this content Definition, and T013 owns that visible
  correction together with the subtab row.
- A diagram is a presentation strategy over canonical topology, and it does not
  exist yet. An empty frame labelled for a future diagram is the layout form of
  a fabricated value.
- The Foundation UI stays read-only for every Site for the whole of M1 and must
  not imply in-place edit, Save, Publish, approval, rename, duplicate, delete,
  or configuration history.
- `Version History` and Changes are not rendered even disabled, because no
  configuration-change model exists and the eventual capability in that
  territory has a different meaning from mockup history chrome.

## Protected Seams

- Mockup fidelity versus product honesty: CI guard.
  Canonical layout only for content the product can source; no mockup literal as
  content; deferred-by-decision controls absent from the DOM; the diagram panel,
  signal selector, and Changes subtab absent rather than framed empty.
- Read-only Foundation UI: review-time + contract test.
  Every Site renders read-only regardless of origin; the fixed-at-creation
  statement stays; no update or delete route exists for a Site.
- Configuration-only Site states: CI guard.
  Declared configuration renders; operational evidence does not, and its absence
  is explicit rather than zeroed.
- Foundation subtab inventory: CI guard.
  Definition, Topology, Controls, and Readiness render as specified; Changes is
  absent until a reviewed change model exists.
- SLD archetype boundary: unit/contract test.
  No diagram, no archetype, and no layout strategy is introduced here.
- Shared Site presentation substrate: CI guard.
  Foundation presentation resolves in `frontend/src/sites/**` only; the
  substrate stays a leaf with no discriminant.
- YAML configuration authority: unit/contract test.
  The screen renders the strictly validated document and introduces no second
  representation.
- Vocabulary separation: CI/review check.
  No source-health or assessment vocabulary appears.
- Simulator feature gate: CI guard.
  Foundation is never gated and renders identically in both flag states.

## Focused Tests And Checks

- UI test asserting the Foundation subtab set is Definition, Topology, Controls,
  and Readiness, and that Changes is absent in every state.
- UI test asserting Definition, Topology, and Controls render only
  record-sourced Foundation content or the accepted current M1 absence states.
- UI test asserting the redundant Foundation-under-Foundation panel heading no
  longer renders and that Definition names the content area instead.
- UI test asserting Readiness is labelled in place and is not a link, button,
  disabled control, route, or empty placeholder panel.
- UI test asserting Summary, Components, Control Logic, and Settings do not
  render as the Foundation subtab row.
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
- Accessibility checks on the subtab row, panels, and tables.
- Run `tools/check-architecture.ps1`, including persistence, substrate, route,
  and Foundation subtab inventory checks.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Inherit the M1 Step 3 exclusions from `.ai/ACTIVE_CONTEXT.md`.
- Do not render the Single Line Diagram, an empty frame for it, a placeholder or
  skeleton labelled for it, a reserved region sized for it, or its signal
  selector. Do not add an SLD archetype, an SLD view model, topology validation,
  or auto-layout. That is causal step 4.
- Do not render `Edit`, `Version History`, or Changes in any state.
- Do not change the fixed-at-creation statement or any other copy the T008
  checkpoint settled.
- Do not add a subtab that the Foundation cannot truthfully fill or label in
  place under the settled subtab architecture, except Readiness as specified.
- Do not leave the T011A wart where the page title and an immediate content
  panel are both headed `Foundation`.
- Do not add a runtime or evidence value slot, even an empty one.
- Do not define Site presentation outside `frontend/src/sites/**`, and do not
  add a shell, mode, or variant discriminant prop.
- Do not gate Foundation, its route, or its API.

## User Review

User review is deliberately not required for this slice. It adds no capability
and does not reopen the Foundation naming and tab-inventory checkpoint from
T011A. The configuration-only language, fixed-at-creation statement, and
absent-rather-than-disabled treatment of edit/history/change affordances were
settled at the T008 checkpoint, and this slice arranges content the product
already renders.

This is the last planned slice of Causal Sequencing step 3. Step 4, topology,
devices, and the configured Single Line Diagram, is not planned or started
until the T008 and T011A checkpoints are accepted or redirected.
