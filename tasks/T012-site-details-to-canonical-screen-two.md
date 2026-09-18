# T012 - Site Details To Canonical Screen Two

Status: in_review
USER_REVIEW_REQUIRED: false

Intended branch: `task/T012-site-details-to-canonical-screen-two`

## Feature

Site Foundation And Configuration-Only Site, canonical screen fidelity stage 5.

## UI-Verifiable Screen Behavior

Site Details looks like canonical screen 2, corrected to the settled operator
Site architecture.

It has breadcrumbs, an identity header carrying `site_id`, display name, and the
`Simulated` badge, and a Site Information panel of record-sourced Site and
Foundation facts. The mockup's single `Status` row becomes two labelled facts:
Mode and Lifecycle.

It uses the operator Site tab row introduced by T011A. Overview and Foundation
are real destination tabs. Health, Performance, Findings, Work, Financials, and
Evidence are labelled in place only, with no link, button, route, or disabled
fake destination.
The row keeps all eight labels under the viewport policy and may scroll inside
its own region rather than collapsing or hiding labels.

It has a Quick Actions panel. `Open in Simulator Lab` is absent when
`simulator_lab.enabled` is false and disabled with its named prerequisite when
the flag is true. `Start Simulation` follows the same gate and sequencing rule.
`View Live Data` is rendered in both flag states and disabled with its accepted
evidence prerequisite. Every disabled control says what would make it available.

`Edit`, `Edit Configuration`, `Version History`, `Duplicate Site`,
`Delete Site`, and the site image `Change` control are not rendered at all. The
site image and map panel is not rendered either, because the Foundation carries
no image.

There are still no operational values anywhere on the screen.

## Why This Is Next

T011A settled the Foundation name, route, compatibility redirect, and operator
Site tab inventory. This slice can now focus on dressing Site Details itself:
identity, backed facts, the settled tab row, and Quick Actions under the
three-state affordance rule.

This is the screen where the three-state rule does its real work. It is also
the first screen where unavailable future actions are named visibly, so the
difference between "labelled in place" tabs and "disabled with a reason" action
controls must be tested.

Because this screen uses the shared Site substrate, the Lab's later Site view
inherits the dressed Site fact presentation instead of building a second one.

## Acceptance Criteria

### Layout and facts

- Breadcrumbs read from the Sites index to this Site. The identity header
  carries `site_id` as the title, display name beneath it, and the `Simulated`
  badge as the rendering of `source.mode = SIMULATED`.
- The Site Information panel renders only record-sourced Site and Foundation
  facts, including Site ID, Name, Type, Location, Timezone, Lifecycle,
  Foundation version or valid-from where available, and Description/Summary
  where the record supplies it.
- The mockup's single `Status` row becomes two separately labelled facts, Mode
  and Lifecycle. A test asserts they never share a row, a label, or a badge, and
  that neither is derived from, defaulted from, or rendered as a proxy for the
  other or for configuration origin.
- Configuration origin and template provenance remain visible as their own
  facts.
- The site image and map panel is not rendered. The Foundation carries no image,
  and an empty frame is chrome pretending to content.

### The operator Site tab row

- The tab row is the T011A operator Site tab inventory: Overview, Foundation,
  Health, Performance, Findings, Work, Financials, and Evidence.
- The tab row preserves all eight labels at every width where the screen
  renders. It may scroll within its own region, but it does not collapse, hide
  the labelled-in-place tabs, or move them into an overflow menu.
- Overview and Foundation are real destination tabs whose routes render truthful
  identified Site surfaces.
- Health, Performance, Findings, Work, Financials, and Evidence are labelled in
  place only. A test asserts each is not a link, registers no route, is not a
  button, and is not a disabled control.
- `Configuration`, `Devices`, `Gateway`, `Ingestion`, `Events`, and `Logs` are
  not operator Site tabs and do not render in this row.

### Quick Actions, under the three-state rule

- `Open in Simulator Lab` has two treatments by two different rules, and both
  are tested. With `simulator_lab.enabled` false it is not rendered at all,
  which is the gate rule. With the flag true it is rendered disabled with its
  prerequisite named as the Lab's Site and run view at causal step 6, which is
  the sequencing rule.
- `Start Simulation` is a simulator execution action and follows the same two
  rules: not rendered when the flag is false, disabled with a named prerequisite
  when it is true.
- `View Live Data` is not a simulator surface. It is rendered in both flag
  states, always disabled, with its prerequisite named as accepted evidence at
  causal step 9.
- While disabled, none of these controls navigates, submits, or reaches an API.
  A test asserts a click on each is inert.
- Every disabled control exposes an accessible reason naming its prerequisite,
  and no enabled control lacks a backing capability.
- `Edit`, `Edit Configuration`, `Version History`, `Duplicate Site`,
  `Delete Site`, and the site image `Change` control are absent from the DOM
  entirely, not disabled and not `aria-disabled`.

### The substrate and its first extension slot

- The Quick Actions panel is part of the shared Site composition, but
  `Open in Simulator Lab` and `Start Simulation` cannot live inside the
  substrate because they depend on the gate and Lab entry point. They are
  supplied by the operator shell through a named extension slot.
- That slot is declared by the substrate and filled by the shell. The substrate
  never imports what fills it, declares no `variant`, `mode`, `shell`, or
  `isLab` prop, and contains no branch on shell identity. A test asserts the
  substrate renders correctly with the slot empty.
- The gated controls route through the existing T004 gated entry-point module.
  No second chokepoint is created, no simulator URL literal appears outside the
  gated modules, and the `$gatedModules` allowlist is not extended.
- All Site Details presentation still resolves in `frontend/src/sites/**`, and
  the substrate single-definition and leaf-direction guards pass with the slot
  present.
- Render equivalence still ships at causal step 6, when the Lab's Site view
  becomes the second consumer.

### Honesty

- No operational values render: no telemetry, charts, source health, gateway
  status, `Last Data`, evidence, analytics, Replay, or Findings, and no zero
  values or `OFFLINE` states.
- No mockup literal renders as content. Every value traces to the record under
  test.
- No Single Line Diagram, empty diagram frame, or signal selector renders.
- Every acceptance criterion of T007, T008, T009, T011, and T011A still holds
  unchanged in meaning. Where a test query must change because markup changed,
  the assertion is preserved or strengthened, never loosened.

## Required Product And Domain Semantics

- Mockscreen fidelity is an explicit delivery goal for these slices. The task
  should move the real screen as close to the canonical mockscreen's visual and
  information architecture as current backed content honestly allows.
- Three treatments, never blurred. A gated or decided-against capability is not
  rendered; a canonical tab that names a real aspect of an entity but has no
  content contract is labelled in place; a capability the map can sequence but
  that is not currently eligible is disabled with its reason stated.
- The operator Site tab vocabulary is v6.9's Overview, Foundation, Health,
  Performance, Findings, Work, Financials, and Evidence from lines 464 and 615.
  The mockup's Configuration, Devices, Gateway, Ingestion, Events, and Logs are
  not operator Site tab vocabulary for M1.
- The M1 viewport policy keeps operator Site tab vocabulary stable at all
  widths where the screen renders. Narrow widths may change available space, not
  which Site aspects the product names.
- The distinction between an action control and a tab is what makes the middle
  treatment safe. A tab set describes aspects of an entity; a greyed button
  describes an action.
- `Edit` and `Edit Configuration` are not soon: M1 decided configuration is
  fixed at creation. `Version History` is not rendered because no
  configuration-change model exists.
- Where both shells present a Site they present it from one substrate, and every
  shell difference must be expressible as an addition around the core.

## Protected Seams

- Mockup fidelity versus product honesty: CI guard.
  Three treatments never blur; deferred-by-decision controls are absent from
  the DOM; every disabled control exposes an accessible reason; destination
  tabs have real routes; labelled-in-place tabs are not controls or links.
- Shared Site presentation substrate: CI guard + contract test.
  One read model, one view model, one component set in `frontend/src/sites/**`;
  the extension slot is declared by the substrate and filled by the shell; the
  substrate never imports what fills it and carries no discriminant.
- Navigation truthfulness: CI guard.
  Overview and Foundation are the only destination tabs in the Site tab row.
- Simulator feature gate: CI guard.
  Simulator entry points and execution actions are not rendered with the flag
  off; the crossing reuses the T004 single gated entry-point module.
- Read-only Foundation UI: review-time + contract test.
  `Edit`, `Edit Configuration`, `Version History`, `Duplicate Site`,
  `Delete Site`, `Save`, `Publish`, and `Rename` are absent from the DOM, not
  disabled; no update or delete route exists for a Site.
- Configuration-only Site states: CI guard.
  No fabricated operational values, health states, or charts.
- Vocabulary separation: CI/review check.
  Provenance, lifecycle, source health, and assessment vocabularies stay
  distinct.
- Site identity: contract test.
  The screen is addressed by `site_id`; template provenance and display name are
  not identity.

## Focused Tests And Checks

- UI test asserting the identity header, breadcrumbs, and Site Information panel
  render only record-sourced values.
- UI test asserting Mode and Lifecycle never share a row, label, or badge, with
  fixture Sites whose origin and mode do not coincide.
- UI test asserting the T011A tab inventory renders, Overview and Foundation are
  real identified-route destinations, and the remaining tabs are labelled in
  place only.
- UI test asserting the tab row renders all eight labels without an overflow
  menu, hidden subset, collapsed menu, disabled fake destination, or route for a
  labelled-in-place tab.
- UI test asserting `Configuration`, `Devices`, `Gateway`, `Ingestion`,
  `Events`, and `Logs` do not render as operator Site tabs.
- UI tests for Quick Actions in both flag states: `Open in Simulator Lab` and
  `Start Simulation` absent when disabled and disabled-with-reason when enabled;
  `View Live Data` disabled in both.
- UI test asserting a click on each disabled control is inert: no navigation, no
  submission, no API call.
- Accessibility test asserting every disabled control exposes an accessible
  reason naming its prerequisite.
- UI test asserting DOM absence, not disabled state, of `Edit`,
  `Edit Configuration`, `Version History`, `Duplicate Site`, `Delete Site`, the
  image `Change` control, and the site image and map panel.
- Substrate test asserting the shared region renders correctly with the
  extension slot empty, and that no substrate module imports shell code,
  simulator code, or `config/featureFlags`.
- UI test asserting no diagram container, no diagram heading, and no signal
  selector renders.
- UI test asserting no operational value, chart, source-health state, or
  evidence timestamp renders.
- Run `tools/check-architecture.ps1`, including persistence, substrate, tab
  inventory, navigation-truthfulness, and simulator URL chokepoint checks.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Inherit the M1 Step 3 exclusions from `.ai/ACTIVE_CONTEXT.md`.
- Do not make any Quick Action functional. Every one of them is either absent or
  disabled in this slice.
- Do not build the Lab's Site view, a Lab Sites index, or any step 6 surface.
- Leave the render-equivalence test for causal step 6, when the second consumer
  exists.
- Do not turn a labelled-in-place tab into a route, a link, a button, or a
  disabled control, and do not add content to one.
- Do not collapse the tab row, hide any of the eight labels by viewport, or move
  labelled-in-place tabs into an overflow menu.
- Do not render `Edit`, `Edit Configuration`, `Version History`,
  `Duplicate Site`, `Delete Site`, or the image `Change` control in any state.
- Do not add a site image, an image upload, a map, the Foundation subtab row, an
  SLD, or a signal selector.
- Do not route a gated control through the substrate.
- Do not give a substrate component a `variant`, `mode`, `shell`, or `isLab`
  prop, and do not let the substrate import shell code, simulator code, or the
  feature flag.

## User Review

User review is deliberately not required for this slice. It adds no capability
and does not reopen the Foundation naming decision from T011A. Every action it
renders is either absent or disabled, and the product language on the screen was
settled at the T006, T008, and T011A checkpoints.
