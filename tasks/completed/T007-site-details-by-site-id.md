# T007 - Site Details Addressed By Site Id

Status: complete
USER_REVIEW_REQUIRED: false

Intended branch: `task/T007-site-details-by-site-id`

## Feature

Site Foundation And Configuration-Only Site.

## UI-Verifiable Screen Behavior

A row in the operator Sites index opens that Site. Site Details is addressed by
`site_id` and shows what the product actually knows about the Site the user
created: identity, display name, site type, location, IANA timezone, lifecycle
status, source mode as provenance, integration readiness, configuration origin
with template provenance, and created and updated timestamps.

Everything that would need evidence is explicitly unavailable and says why.
There are no telemetry values, no charts, no gateway or source health, no
`Last Data`, no analytics, no Replay, and no Findings, and none of them is
rendered as a zero, a flat line, or an `OFFLINE` state.

An unknown `site_id` produces an explicit not-found surface, not an empty Site.

The parameterless `Site details` operator navigation item and its route frame
are gone. A Site Details link that names no Site is not a destination; Site
Details is reached from a Sites row.

Site Details is served identically with `simulator_lab.enabled` true and false.

## Why This Is Next

This completes the user-visible arc that T006 started. T006 proved a Site can be
created, persisted, and listed; this slice makes the Site openable, which is
what turns the index row into a destination and what every later Site surface
attaches to.

It is separated from T006 rather than bundled with it because T006 is already
the largest review packet in the feature: a new port, a composite store, a write
path with atomicity and untrusted-input handling, a gated create flow, the
first-run empty state, and the introduction of the shared substrate. Splitting
the detail surface off keeps both packets reviewable without changing the causal
order or the checkpoint, which stays on creation.

It is also the slice that makes the T002 parameterless `Site details` route
false, so it is the slice that removes it.

## Acceptance Criteria

- A Site read endpoint serves the Site read model by `site_id`. An unknown
  `site_id` returns not-found. Lookup is case-insensitive, consistent with the
  port's case-insensitive uniqueness rule, and both the response and the UI
  always render the stored canonical `site_id`, so one Site can never present as
  two.
- An operator route addressed by `site_id` renders Site Details. It is never
  gated and is served identically in both flag states.
- Rows in the Sites index become links to that route. No other new destination
  is added.
- The parameterless `/site-details` route, its frame, and its `Site details`
  operator navigation item are removed. Operator navigation loses one item and
  gains none. A test asserts that no operator navigation item names a Site
  without identifying one. The parameterless `Site configuration` item stays
  until T008, which is the slice that makes its identified replacement real.
- Site Details presentation lives in `frontend/src/sites/**`: the detail read
  model, the view model that derives display values, and the presentation
  components. Nothing under `frontend/src/shell/**` or the Lab feature root
  declares any of the three. The substrate single-definition and leaf-direction
  guards from T006 pass with the new modules present and still find no second
  definition.
- The substrate takes no `variant`, `mode`, `shell`, or `isLab` prop, imports no
  shell code, no simulator code, and no feature flag. The operator shell
  composes it and adds nothing to the shared region in this slice.
- Render equivalence remains deliberately unwritten and is named again: it ships
  with the Lab's Site view at causal step 6, when a second consumer first
  exists.
- The six provenance and status concepts from the Provenance And Status Concepts
  table render as independent facts. The `Simulated` badge is the rendering of
  `source.mode = SIMULATED` and appears next to, never inside, lifecycle status.
  Configuration origin and source mode are neither derived from nor defaulted
  from one another.
- Panels that would require evidence either state No evidence or Unavailable
  with the reason, or are not rendered. No zero value, empty chart, flat series,
  `OFFLINE` state, or fabricated timestamp appears. Configured devices, where
  named, are labelled configured or awaiting evidence, never healthy, online, or
  offline.
- No action control renders in this slice, in any state. `Edit`,
  `Edit Configuration`, `Version History`, `Duplicate Site`, `Delete Site`,
  `Save`, `Publish`, `Rename`, and the site image `Change` control are absent
  from the DOM entirely, not disabled and not `aria-disabled`. A test asserts
  DOM absence rather than disabled state.
- `Open in Simulator Lab`, `Start Simulation`, and `View Live Data` are also not
  rendered in this slice. They belong to the Quick Actions panel, which is
  canonical screen 2 chrome and arrives with the three-state treatment in T012.
  Nothing here invents a container in order to hold a disabled control.
- The site image and map panel from the mockup is not rendered. The Foundation
  carries no image, and an empty frame is chrome pretending to content.
- No Site tab bar renders in this slice. Tabs are canonical chrome and arrive in
  T012, where the tabs with no content contract are labelled in place.
- No Single Line Diagram, empty diagram frame, or signal selector renders. Those
  are causal steps 4 and 6.
- No value, timestamp, status, or label appears because a mockup shows it. Every
  rendered value traces to the record under test.
- No update or delete route for a Site exists in the served route inventory, in
  either flag state.
- The carried-forward "no digits inside `<main>`" assertions are replaced with
  Site-specific assertions wherever truthful Site values now render. Replace,
  never loosen.

## Required Product And Domain Semantics

- A configuration-only Site is a valid Site. It may expose declared identity,
  lifecycle, location, timezone, site type, Foundation content, and intended
  source and integration configuration, and must never fabricate operational
  evidence, health, analytics, charts, or conclusions because it exists.
- Source mode, lifecycle status, integration readiness, evidence availability,
  source health, and configuration origin are six separate concepts, per the
  Provenance And Status Concepts table in `.ai/FEATURE_MAP.md` Feature Area 1.
  A Site may be `lifecycle_status = ACTIVE` with `source.mode = SIMULATED`,
  origin `USER`, and no evidence at all.
- Gateway and source health become applicable only once a source is expected to
  report. A configured but not-yet-connected source is not `OFFLINE`.
- A navigation destination appears only when the route behind it renders a
  truthful surface. A parameterless Site destination is not a destination.
- Where both shells present a Site they present it from one substrate. This
  slice builds the operator consumer; the Lab consumer arrives at step 6 and
  will compose the same components rather than fork them.

## Protected Seams

- Shared Site presentation substrate: CI guard + contract test.
  The Site detail read model, view model, and components resolve in
  `frontend/src/sites/**` only, and the substrate stays a leaf with no shell,
  simulator, or feature-flag import and no variant discriminant. Render
  equivalence, the primary guard, ships at step 6 with the second consumer.
- Configuration-only Site states: CI guard.
  A Site with no accepted evidence shows No evidence or Unavailable rather than
  fabricated telemetry, charts, source health, analytics, Findings, or Replay.
- Read-only configuration UI: review-time + contract test.
  Deferred-by-decision controls are absent from the DOM, not disabled, and no
  update or delete route exists for a Site.
- Site identity: contract test.
  The Site is addressed by `site_id` only; template provenance and display name
  never address it, and case-variant lookup resolves to one canonical identity.
- Vocabulary separation: CI/review check.
  Provenance vocabulary is not used as status, health, or assessment
  vocabulary, and source-health vocabulary does not appear where no source
  health exists.
- Provenance disclosure: review-time + UI test.
  Decision-relevant provenance, source mode and configuration origin, is
  visible on the primary screen; no transport detail is dumped onto it.
- Simulator feature gate: CI guard.
  Site Details is an operator capability and is never gated; it renders
  identically in both flag states.
- Mockup fidelity versus product honesty: CI guard.
  No mockup literal renders as content; no enabled control lacks a backing
  capability; no navigation destination is added.
- Stack and module direction: CI guard.
  One-way dependency direction preserved.

## Focused Tests And Checks

- API tests for the Site read endpoint: a created Site resolves, an unknown
  `site_id` returns not-found, a case-variant id resolves to the stored
  canonical identity, and no update or delete route exists.
- UI test opening a Site from a Sites index row and asserting the rendered
  identity, provenance, and Foundation-derived facts come from the record.
- UI test asserting explicit No evidence or Unavailable states, and asserting
  the absence of zero values, charts, source health, `OFFLINE`, and any
  evidence-derived timestamp.
- UI test asserting DOM absence, not disabled state, of `Edit`,
  `Edit Configuration`, `Version History`, `Duplicate Site`, `Delete Site`,
  `Save`, `Publish`, `Rename`, and the image `Change` control.
- UI test asserting no diagram container, no diagram heading, no signal
  selector, and no tab bar renders.
- UI test asserting operator navigation no longer contains `Site details`, that
  the parameterless route is unregistered, and that operator navigation gained
  nothing.
- UI test asserting Site Details renders identically with `simulator_lab.enabled`
  true and false.
- Independence test: a fixture Site with origin `USER` and `source.mode = LIVE`
  and one with origin `SHIPPED` and `source.mode = SIMULATED` each render both
  facts correctly and separately.
- Run `tools/check-architecture.ps1`, including the T005 persistence checks and
  the T006 substrate single-definition and leaf-direction checks.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Inherit the M1 Step 3 exclusions from `.ai/ACTIVE_CONTEXT.md`.
- Do not add Site Configuration, its route, or its content. That is T008.
- Do not add a Site tab bar, a Quick Actions panel, a site image panel, or any
  canonical screen 2 chrome. That is T012, after the shared visual vocabulary.
- Do not render `Open in Simulator Lab`, `Start Simulation`, or `View Live Data`
  in any state, and do not add an operator-to-Lab crossing in this slice.
- Do not build extension-slot machinery. Nothing fills a slot in this slice.
- Do not gate Site Details, its route, or its API on `simulator_lab.enabled`.
- Do not apply canonical mockup layout yet. Content before chrome.

## User Review

User review is deliberately not required for this slice. It adds no product
language the T006 checkpoint did not already fix and no capability beyond
opening a Site that already exists. The configuration-only language that this
surface leans on is put to the user at the T008 checkpoint, together with the
statement that configuration is fixed at creation in M1.

## Review Outcome

Reviewer verdict: accept after one medium finding was fixed. No other findings,
no blocking open questions.

Finding: `frontend/src/sites/SiteDetails.tsx` did not clear the loaded Site when
`siteId` changed, so SPA navigation from one Site URL to another left the
previous Site rendered while the new read was in flight. `/sites/MG-404` could
briefly present the previously loaded canonical Site as the site that address
names, against this slice's own rule that a Site is addressed by `site_id` and
by nothing else. Every test in the slice mounted at one identity and never
changed it, which is why nothing caught it.

Fixed on the branch in `b119c32`. The store's answer is now held with the
identity it was asked about and discarded in the render that first sees a new
identity, before any effect runs; resetting inside the effect would still commit
one frame with the previous site under the new address. The in-flight read's
`active` guard is unchanged and still discards a late answer from a previous
identity. The regression test, `drops the site on screen the moment the address
names another`, loads `MG-002`, rerenders at `MG-404` against a lookup left
deliberately pending, and asserts nothing of the previous Site survives the
address change. Reverting the component alone fails it, so it is load-bearing.
The shape is recorded in `.ai/CODE_STATE.md` under T007, because T008's
per-Site configuration surface needs the same treatment.

Reviewer checks: architecture guard passed, agent workflow guard passed, focused
backend 51 passed, focused frontend 52 passed, `git diff --check main...HEAD`
clean.

Checks re-run in the implementing session after the fix: architecture guard
passed, agent workflow guard passed, full frontend suite 251 passed across 10
files, frontend typecheck passed, `git diff --check` clean. The backend is
untouched by the fix and was not re-run. Recorded as a re-run of the fix, not as
a second review.

User review is not required for this slice, as the User Review section above
states. The configuration-only language this surface leans on goes to the user
at the T008 checkpoint.

The full review packet is at `.agent/T007-review-packet.md`, with the finding
and its fix recorded there under Review Findings Addressed, and the branch diff
at `.agent/T007-review.diff`. Both are local-only.
