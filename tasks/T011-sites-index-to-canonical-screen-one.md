# T011 - Sites Index To Canonical Screen One

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T011-sites-index-to-canonical-screen-one`

## Feature

Site Foundation And Configuration-Only Site, canonical screen fidelity stage 4.

## UI-Verifiable Screen Behavior

The operator Sites index looks like canonical screen 1, corrected where the
mockup is wrong.

It has a page title and subtitle, a site search, a type filter, and separate
filters for mode and lifecycle. Its table columns are Name with `site_id`, Type,
Location, Mode, Lifecycle, Last analysed, and Actions. Mode and lifecycle are
two columns, never one, because mode is provenance and not status. Last analysed
renders `--` for every Site, because no evidence has been analysed in any
window yet.

The Actions column offers View, which opens Site Details. It offers nothing
else, because nothing else exists.

The `+ New Site` button is the gated entry point T006 already shipped,
restyled. With `simulator_lab.enabled` false it is not rendered and the empty
state offers no action, exactly as before.

Aside from that one gated button, the screen is identical in both flag states.

## Why This Is Next

Its content became real in T006 and the shared vocabulary landed in T009, so
this is the first operator screen that can be made canonical honestly.

It comes before Site Details and Site Configuration because it is the entry
point to both: it is where an operator forms their model of what a Site is and
what facts the product tracks about one. Getting the mode-versus-lifecycle
separation right here is what stops the mockup's collapsed `Status` column from
becoming the product's data model.

## Acceptance Criteria

- The page adopts the canonical layout using the T009 vocabulary: page header
  with title and subtitle, search, filters, and table.
- Columns are Name with `site_id`, Type, Location, Mode, Lifecycle,
  Last analysed, and Actions. A test asserts that no single column header
  renders both a mode value and a lifecycle value, and that `Simulated` never
  appears under a header named `Status`.
- Mode renders `source.mode` as provenance. Lifecycle renders
  `lifecycle_status`, whose permitted values come from the M1 Site schema in
  `.ai/FEATURE_MAP.md` and not from the mockup. Neither is derived from,
  defaulted from, or rendered as a proxy for the other or for configuration
  origin, and a test proves it with fixture Sites whose origin and mode do not
  coincide.
- Configuration origin and template provenance remain visible as their own
  facts, distinct from mode and lifecycle.
- `Last analysed` renders `--` for every Site in the store, and a test asserts
  that no timestamp renders in that column for any Site. The mockup's
  `Last Data` column and its timestamps are not reproduced.
- Search, type filter, mode filter, and lifecycle filter operate over the
  records present. No filter offers a value no Site can have, and no filter
  promises a dimension the Site model does not carry.
- The Actions column contains only View. No overflow menu renders, because it
  would contain no real action. No `Edit`, `Duplicate Site`, `Delete Site`, or
  equivalent control appears, enabled or disabled, and a test asserts DOM
  absence rather than disabled state.
- `+ New Site` is the T006 gated entry point, restyled. It still routes through
  the existing T004 gated entry-point module, is not rendered at all when
  `simulator_lab.enabled` is false, and adds no second chokepoint. No new
  capability is introduced by this slice.
- The first-run empty state keeps its T006 behaviour and copy in both flag
  states, dressed in the canonical layout. It still fabricates no row, no count,
  and no placeholder, and with the flag off it still offers no action and does
  not name the Simulator Lab.
- Aside from the gated `+ New Site` button, the screen renders identically with
  `simulator_lab.enabled` true and false, and a test asserts it.
- No mockup literal renders as content. Specifically, no `site_id`, display
  name, location, timestamp, or badge value appears unless the record under test
  supplies it. Values such as `Planned` may appear when a record carries that
  lifecycle value; the test is record-sourced rather than string-banned.
- No operational content appears: no source health, evidence state, charts,
  assessment, top issue, analytics, Replay, or Findings columns.
- The index presentation stays in `frontend/src/sites/**`. The substrate
  single-definition and leaf-direction guards pass, and no `variant`, `mode`,
  `shell`, or `isLab` discriminant prop is introduced.
- Every acceptance criterion of T006 and T009 still holds unchanged in meaning.
  Where a test query must change because markup changed, the assertion is
  preserved or strengthened, never loosened.

## Required Product And Domain Semantics

- Mode is provenance, not status. `SIMULATED` is neutral provenance and never an
  assessment. Collapsing mode and lifecycle into one status column is a mockup
  error the product corrects rather than copies.
- `lifecycle_status` is this project's extension. v6.9 has no site lifecycle
  enum, so the permitted values come from the M1 Site schema, not from whatever
  the mockup drew.
- `Last analysed` is an evidence-derived fact. Until evidence exists it is `--`,
  which is a truthful rendering of nothing rather than a placeholder for
  something.
- A navigation destination appears only when the route behind it renders a
  truthful surface. `+ New Site` is a button, not a destination, and it is
  rendered only when the capability behind it is served.

## Protected Seams

- Mockup fidelity versus product honesty: CI guard.
  Canonical layout only for content the product can source; no mockup literal as
  content; deferred-by-decision controls absent rather than disabled; Mode and
  lifecycle never share a column; `Last analysed` renders `--`.
- Vocabulary separation: CI/review check.
  Provenance, lifecycle, source health, and assessment vocabularies stay
  distinct; no source-health or assessment term appears on this screen.
- Configuration-only Site states: CI guard.
  No evidence-derived value, chart, or health state is fabricated for a Site
  with no accepted evidence.
- Shared Site presentation substrate: CI guard.
  Index presentation resolves in `frontend/src/sites/**` only and the substrate
  stays a leaf.
- Simulator feature gate: CI guard.
  The Sites index is never gated; the one gated control on it is the existing
  T004 entry point, not rendered when the flag is off.
- Site identity: contract test.
  Rows are keyed by `site_id`; display name and template provenance never
  address a Site.
- Read-only configuration UI: review-time + contract test.
  No edit, duplicate, or delete affordance appears in the Actions column, and no
  update or delete route for a Site exists.

## Focused Tests And Checks

- UI test asserting the column set, and specifically that no header renders both
  a mode value and a lifecycle value and that `Simulated` never appears under a
  header named `Status`.
- Independence test with fixture Sites whose configuration origin and source
  mode do not coincide, proving neither column is derived from the other.
- UI test asserting `Last analysed` renders `--` for every Site and that no
  timestamp renders in that column.
- UI tests for search and each filter over the records present, including that
  no filter offers an unreachable value.
- UI test asserting the Actions column contains only View, and asserting DOM
  absence of `Edit`, `Duplicate Site`, `Delete Site`, and any overflow menu.
- UI tests for `+ New Site` in both flag states: rendered and routing through
  the T004 gated module when enabled, absent when disabled.
- UI test asserting the empty state copy and behaviour are unchanged in meaning
  in both flag states.
- UI test asserting the screen is otherwise identical in both flag states.
- Vocabulary scan asserting no source-health or assessment term appears.
- Accessibility checks on the table, filters, and badges.
- Run `tools/check-architecture.ps1`, including the T005 persistence checks and
  the T006 substrate checks.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Do not add a column, filter, or badge whose value the product cannot source,
  including `Last Data`, assessment, top issue, evidence state, or source
  health.
- Do not add an Actions overflow menu, `Edit`, `Duplicate Site`, `Delete Site`,
  or any other deferred-by-decision control, disabled or otherwise.
- Do not add a new capability. `+ New Site` is the existing T006 entry point
  restyled.
- Do not change the empty-state copy or any other copy the T006 checkpoint
  settled.
- Do not add sorting, pagination, saved views, bulk selection, or bulk actions,
  and do not add a query DSL, pagination, or filtering to the port to support
  them.
- Do not gate the Sites index or its API, and do not add an operator navigation
  item or a second entry-point chokepoint.
- Do not define Site presentation outside `frontend/src/sites/**`, and do not
  add a shell, mode, or variant discriminant prop.
- Do not dress Site Details or Site Configuration here. Those are T012 and T013.
- Do not render a Single Line Diagram, an empty diagram frame, or a signal
  selector.
- Do not add scenarios, run setup, simulator execution, ingestion, evidence,
  source health, charts, analytics, Replay, or Findings.
- Do not weaken any T003 to T010 assertion. Where markup changes force a query
  change, preserve or strengthen the assertion; never relax it.

## User Review

User review is deliberately not required for this slice. It adds no capability
and no product language: the Sites index vocabulary, the provenance facts, and
the empty-state copy were settled at the T006 checkpoint. The two corrections
this slice makes to the mockup, separating Mode from lifecycle and rendering
`Last analysed` as `--`, are already required by the vocabulary-separation and
mockup-fidelity seams rather than being new product decisions.
