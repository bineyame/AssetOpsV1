# T011A - Foundation Naming And Operator Site Tab Inventory

Status: planned
USER_REVIEW_REQUIRED: true

Intended branch: `task/T011A-foundation-naming-and-operator-site-tab-inventory`

## Feature

Site Foundation And Configuration-Only Site, foundational screen architecture
alignment before canonical Site Details and Foundation fidelity.

## UI-Verifiable Screen Behavior

The operator product uses one user-visible name for the read-only Site
Foundation surface: Foundation.

The existing Site Configuration address becomes a compatibility redirect from
`/sites/:siteId/configuration` to `/sites/:siteId/foundation`, preserving the
identified `siteId`. The product links, breadcrumbs, headings, and tab labels
surface only the Foundation destination.

Site Details gains the canonical operator Site tab row from v6.9 lines 464 and
615: Overview, Foundation, Health, Performance, Findings, Work, Financials, and
Evidence. Overview and Foundation are destination tabs with real identified
routes. Health, Performance, Findings, Work, Financials, and Evidence are
labelled in place only: no link, no button, no route, and no disabled fake
destination.

## Why This Is Next

T011 finishes the Sites index. Before T012 can dress Site Details, the shared
name, route, and operator Site tab inventory need to be settled in code and
tests. Otherwise the Site Details fidelity slice would mix page composition with
a cross-surface navigation migration.

This slice is also the smallest honest place to carry the user-visible rename:
the route, heading, breadcrumb, Site Details link, tab label, test names, and
guard messages all change together, while the domain concept of configuration
and the accepted fixed-at-creation copy remain intact.

## Acceptance Criteria

- The canonical Foundation route is `/sites/:siteId/foundation` and renders the
  existing read-only Foundation surface for the identified Site.
- `/sites/:siteId/configuration` is a compatibility redirect to the Foundation
  route, preserving `siteId`. It is not linked, tabbed, counted as a destination,
  or allowed to render a second surface.
- The parameterless `/site-configuration` ban remains enforced.
- User-visible surface vocabulary changes from Site Configuration to Foundation
  wherever the surface is named: route text, page heading, breadcrumb, Site
  Details link text, and operator Site tab label.
- The accepted body copy that says a Site's configuration is fixed at creation
  in M1 remains unchanged in meaning. Configuration remains the domain concept;
  Foundation is the product surface name.
- Test names, user-facing guard messages, and guard-script comments that name
  the surface use Foundation, except tests that deliberately assert the legacy
  redirect or the parameterless `/site-configuration` ban.
- Internal module, component, and symbol names under `frontend/src/sites/**` may
  deliberately lag for this slice when changing them would be mechanical churn
  across the shared substrate. No user-visible string or route constant may lag.
- The operator Site tab inventory is defined once in the operator shell, not in
  the shared Site substrate.
- The tab row renders exactly Overview, Foundation, Health, Performance,
  Findings, Work, Financials, and Evidence.
- Overview and Foundation are destination tabs with real identified routes.
  Tests assert their links preserve `siteId` and render truthful surfaces.
- Health, Performance, Findings, Work, Financials, and Evidence are labelled in
  place only. Tests assert they are not links, are not buttons, register no
  route, and expose no disabled-action affordance.
- `Configuration`, `Devices`, `Gateway`, `Ingestion`, `Events`, and `Logs` are
  not operator Site tabs.
- The shared Site substrate still owns Site facts and presentation components,
  but not the operator Site tab row. The substrate remains a leaf with no shell,
  simulator, feature-flag import, or shell/mode/variant discriminant.
- Operator rail navigation does not grow. This slice changes the Site tab row,
  not the operator rail.

## Required Product And Domain Semantics

- v6.9 lines 464 and 615 settle the operator Site tab vocabulary for M1. The
  `ScreenMockups.png` screen 2 tabs are layout evidence for a Site tab row, not
  operator product vocabulary.
- v6.9 line 2117 names the Foundation content row. The former Site
  Configuration surface is this Foundation destination.
- A tab is a destination only when it is rendered as a link to a route with
  truthful content. A canonical Site aspect without a content contract may be
  labelled in place, but it is not a link, route, disabled button, or inert fake
  destination.
- A compatibility redirect preserves old addresses without creating a second
  product surface.

## Protected Seams

- Mockup fidelity versus product honesty: CI guard.
  The operator Site tabs use v6.9 operator vocabulary, destination tabs have
  real routes, and labelled-in-place tabs do not imply disabled or hidden
  capability.
- Shared Site presentation substrate: CI guard.
  The operator shell owns the Site tab inventory; the shared substrate does not
  import shell tabs or branch on shell identity.
- Navigation truthfulness: CI guard.
  The Foundation route is the one surfaced destination; the legacy
  configuration address redirects and is not counted as a destination.
- Read-only Foundation UI: review-time + contract test.
  The rename does not introduce edit, save, publish, history, duplicate, delete,
  or rename affordances.

## Focused Tests And Checks

- Route test for `/sites/:siteId/foundation` rendering the read-only Foundation
  surface for the identified Site.
- Route test for `/sites/:siteId/configuration` redirecting to
  `/sites/:siteId/foundation` while preserving `siteId`.
- Navigation or guard test proving no product link, tab, or route inventory
  exposes the legacy configuration address as a destination.
- UI tests asserting Foundation appears in the page heading, breadcrumb, Site
  Details link, and operator Site tab label.
- UI test asserting the fixed-at-creation configuration copy remains present
  and unchanged in meaning.
- Operator Site tab inventory test asserting the exact tab labels and the
  destination-versus-labelled-in-place assignment.
- UI tests proving Overview and Foundation tabs are links to identified routes,
  while Health, Performance, Findings, Work, Financials, and Evidence are not
  links, buttons, disabled controls, or routes.
- Architecture guard update for the operator Site tab inventory, with the
  definition owned by the operator shell.
- Architecture guard and test-name update from Site Configuration to Foundation,
  except for assertions that deliberately cover legacy redirect compatibility or
  the parameterless `/site-configuration` ban.
- Run `tools/check-architecture.ps1`, including persistence, substrate, route,
  and navigation-truthfulness checks.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Do not add operator rail items.
- Do not render Health, Performance, Findings, Work, Financials, or Evidence as
  routes, links, buttons, or disabled controls.
- Do not add content for any labelled-in-place tab.
- Do not add the Foundation subtab row; T013 owns that.
- Do not rename internal modules or symbols unless the implementer can keep the
  change behavior-neutral and reviewable inside this slice.
- Do not change the accepted fixed-at-creation copy except to preserve it under
  the Foundation surface name.
- Do not add edit, save, publish, history, duplicate, delete, rename, or update
  routes.

## User Review

User review is required. This slice changes user-visible product vocabulary and
information hierarchy across routes, headings, breadcrumbs, links, tabs, tests,
and guard messages.

What the user is being asked to settle:

- The product name Foundation for the surface formerly labelled Site
  Configuration.
- The `/foundation` route with `/configuration` kept only as a compatibility
  redirect.
- The operator Site tab row and the treatment of Health, Performance, Findings,
  Work, Financials, and Evidence as labelled-in-place tabs until content
  contracts exist.
- The decision to let internal `frontend/src/sites/**` module and symbol names
  lag when renaming them would be mechanical churn rather than user-visible
  behavior.
