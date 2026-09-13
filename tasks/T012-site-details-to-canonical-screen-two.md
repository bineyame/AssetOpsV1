# T012 - Site Details To Canonical Screen Two

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T012-site-details-to-canonical-screen-two`

## Feature

Site Foundation And Configuration-Only Site, canonical screen fidelity stage 5.

## UI-Verifiable Screen Behavior

Site Details looks like canonical screen 2, under the three-state affordance
rule.

It has breadcrumbs, an identity header carrying `site_id`, display name, and the
`Simulated` badge, and a Site Information panel of Foundation facts. The
mockup's single `Status` row in that panel becomes two labelled facts, Mode and
Lifecycle.

It has a Site tab bar. `Overview` and `Configuration` are real destinations.
`Devices`, `Gateway`, `Ingestion`, `Events`, and `Logs` are labelled in place,
noted as having no content contract yet, and are neither links nor routes nor
disabled buttons.

It has a Quick Actions panel. `Open in Simulator Lab` is not rendered when
`simulator_lab.enabled` is false, and is rendered disabled with its named
prerequisite when the flag is true. `Start Simulation` behaves the same way,
because it is a simulator execution action. `View Live Data` is always rendered
and always disabled, with its own named prerequisite. Every disabled control
says what would make it available.

`Edit`, `Edit Configuration`, `Version History`, `Duplicate Site`,
`Delete Site`, and the site image `Change` control are not rendered at all. The
site image and map panel is not rendered either, because the Foundation carries
no image.

There are still no operational values anywhere on the screen.

## Why This Is Next

Its content became real in T007, Site Configuration became a real destination in
T008, and the shared vocabulary landed in T009, so the tab bar and the Quick
Actions panel can now be honest rather than decorative.

This is the screen where the three-state rule does its real work, and it is
worth its own slice for that reason. It is also the first screen where a
capability the product does not have yet has to be named on the surface, so it
is where the difference between "not rendered" and "disabled with a reason"
becomes visible to a user rather than theoretical.

Because this screen is the shared substrate, the Lab's Site view inherits this
fidelity when it arrives at causal step 6 instead of being dressed a second time
and then kept in agreement forever.

## Acceptance Criteria

### Layout and facts

- Breadcrumbs read from the Sites index to this Site. The identity header
  carries `site_id` as the title, display name beneath it, and the `Simulated`
  badge as the rendering of `source.mode = SIMULATED`.
- The Site Information panel renders Foundation facts from the record: Site ID,
  Name, Type, Location, Timezone, Lifecycle, Created, and Description.
- The mockup's single `Status` row becomes two separately labelled facts, Mode
  and Lifecycle. A test asserts they never share a row, a label, or a badge, and
  that neither is derived from, defaulted from, or rendered as a proxy for the
  other or for configuration origin.
- Configuration origin and template provenance remain visible as their own
  facts.
- The site image and map panel is not rendered. The Foundation carries no image,
  and an empty frame is chrome pretending to content.

### The tab bar

- `Overview` and `Configuration` are real tabs whose routes render truthful
  surfaces.
- `Devices`, `Gateway`, `Ingestion`, `Events`, and `Logs` are labelled in place,
  each carrying a short note that it has no content contract yet. A test asserts
  each is not a link, registers no route, and is not a disabled button, so it
  cannot be mistaken for an action.
- No tab is added beyond the mockup's set, and no tab claims a v6.9 operator tab
  name the product has not adopted.

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
  entirely, not disabled and not `aria-disabled`. A test asserts DOM absence
  using a query that would fail if any of them rendered in a disabled state.

### The substrate and its first extension slot

- The Quick Actions panel is part of the shared substrate, but
  `Open in Simulator Lab` and `Start Simulation` cannot live inside it: the
  substrate is a leaf that may not import shell code, simulator code, or
  `config/featureFlags`, and both controls depend on the gate and on the Lab
  entry point. They are therefore supplied by the operator shell through the
  first named extension slot the substrate declares.
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
  becomes the second consumer. This slice makes it meaningful rather than
  redundant, because the slot is exactly what that test has to prove is the only
  difference between the two compositions.

### Honesty

- No operational values render: no telemetry, charts, source health, gateway
  status, `Last Data`, evidence, analytics, Replay, or Findings, and no zero
  values or `OFFLINE` states.
- No mockup literal renders as content. Every value traces to the record under
  test.
- No Single Line Diagram, empty diagram frame, or signal selector renders.
- Every acceptance criterion of T007, T008, and T009 still holds unchanged in
  meaning. Where a test query must change because markup changed, the assertion
  is preserved or strengthened, never loosened.

## Required Product And Domain Semantics

- Three treatments, never blurred. A gated or decided-against capability is not
  rendered; a canonical tab that names a real aspect of an entity but has no
  content contract is labelled in place; a capability the map can sequence but
  that is not currently eligible is disabled with its reason stated.
- The test for an action control is whether the feature map can name the causal
  step that makes it true. If it can, disable it and name that prerequisite. If
  the answer is a decision to defer, do not render it.
- The distinction between an action control and a tab is what makes the middle
  treatment safe. A tab set describes the aspects of an entity, so naming an
  aspect early is honest chrome. A greyed button describes an action, and greyed
  reads as soon.
- `Edit` and `Edit Configuration` are not soon: M1 decided configuration is
  fixed at creation. `Version History` is worse than a promise, because the
  eventual capability in that territory has a different name and a different
  meaning.
- Where both shells present a Site they present it from one substrate, and every
  shell difference must be expressible as an addition around the core. A
  difference that cannot be expressed that way is not a shell difference and
  belongs in the substrate for both.

## Protected Seams

- Mockup fidelity versus product honesty: CI guard.
  Three treatments never blurred; deferred-by-decision controls absent from the
  DOM; every disabled control exposes an accessible reason; no enabled control
  without a backing capability; no mockup literal as content; Mode and lifecycle
  never share a row.
- Shared Site presentation substrate: CI guard + contract test.
  One read model, one view model, one component set in `frontend/src/sites/**`;
  the first extension slot is declared by the substrate and filled by the shell;
  the substrate never imports what fills it and carries no discriminant. Render
  equivalence, the primary guard, ships at causal step 6.
- Simulator feature gate: CI guard.
  Simulator entry points and execution actions are not rendered with the flag
  off; the crossing reuses the T004 single gated entry-point module; the
  allowlist is unchanged.
- Read-only configuration UI: review-time + contract test.
  `Edit`, `Edit Configuration`, `Version History`, `Duplicate Site`,
  `Delete Site`, `Save`, `Publish`, and `Rename` are absent from the DOM, not
  disabled; no update or delete route exists for a Site.
- Configuration-only Site states: CI guard.
  No fabricated operational values, health states, or charts.
- Vocabulary separation: CI/review check.
  Provenance, lifecycle, source health, and assessment vocabularies stay
  distinct.
- Provenance disclosure: review-time + UI test.
  Decision-relevant provenance is on the primary screen; transport detail is
  not.
- Site identity: contract test.
  The screen is addressed by `site_id`; template provenance and display name are
  not identity.
- Stack and module direction: CI guard.
  One-way dependency direction preserved through the slot.

## Focused Tests And Checks

- UI test asserting the identity header, breadcrumbs, and Site Information panel
  render only record-sourced values.
- UI test asserting Mode and Lifecycle never share a row, label, or badge, with
  fixture Sites whose origin and mode do not coincide.
- UI test asserting each labelled-in-place tab is not a link, registers no
  route, and is not a disabled button, and that `Overview` and `Configuration`
  are real destinations.
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
- Run `tools/check-architecture.ps1`, including the T005 persistence checks, the
  T006 substrate single-definition and leaf-direction checks, and the simulator
  URL chokepoint check with the new gated controls present.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Inherit the M1 Step 3 exclusions from `.ai/ACTIVE_CONTEXT.md`.
- Do not make any Quick Action functional. Every one of them is either absent or
  disabled in this slice.
- Do not build the Lab's Site view, a Lab Sites index, or any step 6 surface.
  The slot is declared and filled by the operator shell only.
- Leave the render-equivalence test for causal step 6, when the second consumer
  exists.
- Do not turn a labelled-in-place tab into a route, a link, or a disabled
  button, and do not add content to one.
- Do not render `Edit`, `Edit Configuration`, `Version History`,
  `Duplicate Site`, `Delete Site`, or the image `Change` control in any state.
- Do not add a site image, an image upload, or a map.
- Do not route a gated control through the substrate.
- Do not give a substrate component a `variant`, `mode`, `shell`, or `isLab`
  prop, and do not let the substrate import shell code, simulator code, or the
  feature flag.

## User Review

User review is deliberately not required for this slice, consistent with the
decision that fidelity slices carry no checkpoint of their own. It adds no
capability: every action it renders is either absent or disabled, and the
product language on the screen was settled at the T006 and T008 checkpoints.

Two judgements in this slice are derivations from settled rules rather than new
product decisions, and are called out here so a reviewer can check them rather
than discover them. First, `Start Simulation` is treated as a simulator
execution action and is therefore not rendered when the gate is off, in addition
to being disabled when it is on; the fidelity table names only the disabled
treatment, and the gate decision is what supplies the other half. Second, the
substrate's first extension slot is declared here rather than at causal step 6,
because the substrate's leaf rule forbids it from importing the feature flag or
the Lab entry point, so a gated control on a shared screen has nowhere else to
come from. If either judgement is wrong, it is cheaper to correct here than
after the Lab's Site view composes the same slot.
