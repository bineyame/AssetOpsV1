# T008 - Read-Only Site Configuration Presentation

Status: in_review
USER_REVIEW_REQUIRED: true

Intended branch: `task/T008-read-only-site-configuration-presentation`

## Feature

Site Foundation And Configuration-Only Site.

## UI-Verifiable Screen Behavior

From Site Details the user opens Site Configuration for that `site_id` and reads
back, in the product, the configuration they supplied at creation: Foundation
version and validity interval, timezone, lifecycle status, source mode as
provenance, integration readiness, configuration origin with template
provenance, components, devices, signal mappings, ratings with canonical units,
and control assumptions.

The screen states plainly that configuration is fixed at creation in M1. There
is no edit affordance of any kind, enabled or disabled: no Edit, no Edit
Configuration, no Version History, no Save, no Publish, no Rename, no Duplicate,
no Delete, no approve, no diff, no history, and no rollback.

There are no operational values. Devices are shown as configured and awaiting
evidence, never as healthy, online, or offline.

There is no Single Line Diagram, no empty frame where one would go, and no
signal selector. Those belong to later causal steps and the screen makes no
reference to them.

The parameterless `Site configuration` operator navigation item and its route
frame are gone. Site Configuration is reached from a Site.

Site Configuration is served identically with `simulator_lab.enabled` true and
false, and is read-only for every Site regardless of configuration origin.

## Why This Is Next

This is Causal Sequencing step 3c, and it depends on 3b because there is no Site
to present before one is created.

It deserves its own review surface rather than riding along with the write path,
because configuration presentation carries the product language that fixes what
a Site, a Foundation, and a configuration-only Site mean, and what the product
promises about a Site it will not let you edit. That language is what the second
user-review checkpoint exists to settle.

It is also the slice that makes the T002 parameterless `Site configuration`
route false, so it is the slice that removes it. After this slice, operator
navigation contains no parameterless Site destination, and it has not grown at
any point in step 3.

## Acceptance Criteria

- A Site Configuration route addressed by `site_id` renders the Foundation of
  that Site. It is never gated and is served identically in both flag states.
  It is reached from Site Details by a plain link; the canonical tab bar is
  T012 chrome and is not introduced here.
- The parameterless `/site-configuration` route, its frame, and its
  `Site configuration` operator navigation item are removed. A test asserts that
  operator navigation now contains no parameterless Site destination, and that
  operator navigation has not gained an item at any point since T004.
- The screen renders from the persisted document rather than hard-coded values:
  Foundation version, validity interval with its half-open semantics stated
  truthfully, IANA timezone, components, devices, signal mappings, ratings with
  canonical units, and control assumptions.
- Ratings and control mode render as content in this slice. The canonical
  Key Parameters panel and the Summary, Components, Control Logic, and Settings
  tab arrangement are chrome and arrive in T013; a value the Foundation does not
  declare is not rendered and is not shown as a placeholder.
- The six provenance and status concepts from the Provenance And Status Concepts
  table render as independent facts, including configuration origin and template
  provenance. Neither origin nor source mode is derived from, defaulted from, or
  rendered as a proxy for the other.
- The screen states that configuration is fixed at creation in M1 and that
  AssetOps does not edit a Site's Foundation in this milestone. The copy does
  not imply a future editing workflow, does not name one, and does not describe
  the current state as temporary in a way that reads as a promise.
- Absent from the DOM entirely, not disabled and not `aria-disabled`: `Edit`,
  `Edit Configuration`, `Version History`, `Duplicate Site`, `Delete Site`,
  `Save`, `Publish`, `Rename`, approve, diff, history, rollback, and the site
  image `Change` control. A test asserts absence from the DOM rather than
  disabled state, because disabled reads as soon and none of these is coming.
- No update or delete route for a Site exists in the served route inventory, in
  either flag state. `site_id` is immutable and no route or control changes it.
- The screen is read-only for every Site regardless of origin. A `SHIPPED`-origin
  fixture Site renders the same read-only surface as a `USER`-origin one; only
  configuration origin and template provenance differ between them.
- No operational values render: no telemetry, charts, source health, gateway
  status, evidence, analytics, Replay, or Findings, and no zero values or
  `OFFLINE` states. Devices are labelled configured or awaiting evidence.
- Source-health and assessment vocabularies do not appear anywhere on this
  screen, because neither concept has a source here.
- **No Single Line Diagram panel, no empty frame or placeholder for one, and no
  signal selector renders.** The layout closes over that space rather than
  leaving a hole labelled for a future diagram. A test asserts that no diagram
  container, no diagram heading text, and no signal-selector control exists in
  the DOM. The configured diagram is causal step 4 and the signal selector is
  inert until step 6.
- Site Configuration presentation lives in `frontend/src/sites/**`: read model,
  view model, and components. Nothing under `frontend/src/shell/**` or the Lab
  feature root declares any of the three, and the substrate single-definition
  and leaf-direction guards from T006 pass with the new modules present.
- Render equivalence remains deliberately unwritten and is named again: it ships
  with the Lab's Site view at causal step 6.
- No value, timestamp, status, or label appears because a mockup shows it. Every
  rendered value traces to the record under test.
- The carried-forward "no digits inside `<main>`" assertions are replaced with
  configuration-specific assertions wherever truthful Foundation values now
  render. Replace, never loosen.

## Required Product And Domain Semantics

- YAML remains the authoritative M1 configuration representation in both stores
  and is strictly validated on load. The UI renders and explains it and never
  becomes a second source of truth.
- The Site Configuration UI stays read-only for every Site for the whole of M1
  and must not imply in-place edit, Save, Publish, approval, rename, duplicate,
  delete, or configuration history, none of which exist. Authoring exists only
  as create-from-template, in a separate gated flow.
- `Version History` is not merely deferred: no configuration-change model
  exists, and the eventual shape of that territory in v6.9 is
  `Foundation > Changes`, an auditable intervention record with Retain, Retune,
  and Revert. Rendering the mockup's label, even disabled, would name a real
  future capability by the wrong name.
- Foundation version and validity semantics are canonical model facts, so the UI
  may show them truthfully. They are not a configuration history and must not be
  presented as one.
- Configured devices may be shown before they report, labelled as configured or
  awaiting evidence, never as operationally healthy or unhealthy.
- What this project calls Site Configuration is v6.9's `Foundation` tab on a
  Site. The project's name may stand for M1; the operator Site tab set is
  v6.9's, not the mockup's, when a later slice dresses it.

## Protected Seams

- Read-only configuration UI: review-time + contract test.
  Every Site renders read-only regardless of origin; deferred-by-decision
  controls are absent from the DOM rather than disabled; the copy states that
  configuration is fixed at creation in M1; no update or delete route exists for
  a Site.
- Shared Site presentation substrate: CI guard + contract test.
  Configuration presentation resolves in `frontend/src/sites/**` only; the
  substrate stays a leaf with no shell, simulator, or feature-flag import and no
  variant discriminant. Render equivalence ships at step 6 with the second
  consumer.
- YAML configuration authority: unit/contract test.
  The screen renders the strictly validated document; it introduces no second
  representation and no lenient path.
- Configuration-only Site states: CI guard.
  Declared configuration renders; operational evidence does not, and its absence
  is explicit rather than zeroed.
- Site identity: contract test.
  The screen is addressed by `site_id`; template provenance and Foundation
  version never address it and `site_id` is immutable.
- Vocabulary separation: CI/review check.
  Provenance, lifecycle, source health, and assessment vocabularies stay
  distinct, and the latter two do not appear at all.
- Mockup fidelity versus product honesty: CI guard.
  No mockup literal renders as content; no deferred-by-decision control is
  rendered as disabled; the diagram panel and signal selector are absent rather
  than framed empty.
- Simulator feature gate: CI guard.
  Site Configuration is an operator capability and is never gated.
- Stack and module direction: CI guard.
  One-way dependency direction preserved.

## Focused Tests And Checks

- API test for the Site Configuration read path, including an unknown `site_id`
  and the continued absence of update and delete routes in both flag states.
- UI test asserting every rendered Foundation fact traces to the record:
  Foundation version, validity interval, timezone, components, devices, signal
  mappings, ratings with units, and control assumptions.
- UI test asserting the "configuration is fixed at creation in M1" statement is
  present and that no copy implies an editing workflow.
- UI test asserting DOM absence, not disabled state, of the full deferred-control
  list, using a query that would fail if any of them were rendered disabled or
  `aria-disabled`.
- UI test asserting no diagram container, no diagram heading, and no
  signal-selector control exists.
- UI test rendering a `SHIPPED`-origin fixture Site and a `USER`-origin Site and
  asserting both are read-only and differ only in origin and template
  provenance.
- UI test asserting no operational values, no source-health vocabulary, and no
  assessment vocabulary render.
- UI test asserting operator navigation no longer contains
  `Site configuration`, that the parameterless route is unregistered, and that
  operator navigation has not grown since T004.
- UI test asserting Site Configuration renders identically with
  `simulator_lab.enabled` true and false.
- Run `tools/check-architecture.ps1`, including the T005 persistence checks and
  the T006 substrate single-definition and leaf-direction checks.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Inherit the M1 Step 3 exclusions from `.ai/ACTIVE_CONTEXT.md`.
- Do not add a Site tab bar, a Key Parameters panel, or any other canonical
  screen 3 chrome. That is T013, after the shared visual vocabulary.
- Do not build extension-slot machinery. Nothing fills a slot in this slice.
- Do not gate Site Configuration, its route, or its API on
  `simulator_lab.enabled`.

## User Review

User review is required. This is the second of the two checkpoints for this
feature, and it sits here because configuration-only language and the
"configuration is fixed at creation in M1" statement fix what the product
promises about a Site it will not let you edit.

What the user is being asked to settle:

- The statement that configuration is fixed at creation in M1, its exact
  placement, and that it does not read as a promise of editing later.
- That deferred-by-decision controls are absent from the screen rather than
  greyed out, and specifically that `Version History` is not rendered at all
  because no configuration-change model exists and the eventual capability has a
  different name and a different meaning.
- Foundation version and validity language, and that it is not presented as
  configuration history.
- Device labelling as configured or awaiting evidence rather than any health or
  assessment vocabulary.
- Configuration origin, template provenance, source mode, lifecycle status,
  integration readiness, and evidence availability as six separate facts on this
  screen.
- That the screen is read-only for every Site regardless of origin.

Capability planning for Causal Sequencing step 3 stops at this checkpoint. Step
4, topology, devices, and the configured Single Line Diagram, is not planned and
is not to be started until this checkpoint is accepted or redirected. T009 to
T013 are already planned, but they add no capability and no product language:
they apply canonical screen fidelity to surfaces T005 to T008 have already made
real.
