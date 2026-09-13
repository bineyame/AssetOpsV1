# T005 - Site Repository Port And Canonical Site Read Path

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T005-site-repository-port-and-canonical-read-path`

## Feature

Site Foundation And Configuration-Only Site.

## UI-Verifiable Screen Behavior

Sites List stops saying "No sites configured" and shows the canonical shipped
Site as a row with stable identity: display name, `site_id`, site type,
lifecycle status, and source mode labelled as provenance. Opening that row
renders a Site Details page addressed by `site_id`, showing the same identity
plus explicit No evidence / Unavailable states for everything the product cannot
yet know.

Site Configuration keeps its existing unavailable placeholder; Foundation
content presentation is the next slice. Both new screens resolve their data
through a `SiteRepository` port, so nothing in the API layer, the read model, or
the UI knows the store is YAML files on disk.

## Why This Is Next

This is Causal Sequencing step 3a. Every later capability is keyed on
`site_id` and interpreted through Foundation content: scenarios target a Site,
runs and envelopes carry a Site, evidence records are keyed to a Site, and
analytics resolve a Site plus a time window. None of that can be truthful until
one Site exists with stable identity and strictly validated Foundation data.

The port ships in this slice rather than later because retrofitting it after
Sites, SLD view models, devices, and evidence resolution all reach storage
directly is a rewrite of every caller, which is the outcome the user asked to
avoid. It does not ship earlier and alone because a port with no consumer is
speculative architecture, which `.ai/PROJECT_RULES.md` guards against. Shipping
it against two real screens is what proves the shape.

This slice is the read half of 3a. It is split from the read-only Site
Configuration slice because the port, the canonical fixture, strict validation,
two CI guards, and the Sites index are already a full review packet, and because
Foundation presentation carries product language that deserves its own review
surface.

## Acceptance Criteria

- A canonical shipped Site document exists under the shipped, git-tracked
  configuration root and declares the narrowed M1 Site fields: `site_id`,
  `display_name`, `site_type`, `lifecycle_status`, location, mandatory IANA
  `timezone`, `source.mode` and `source.provenance`, optional presentation
  metadata, created/updated timestamps, and a versioned `foundation` holding a
  validity interval, components, topology, devices, signal mappings, ratings,
  and control assumptions.
- Strict validation rejects, with a message naming the offending field: unknown
  keys, a missing or non-IANA `timezone`, an unsupported `site_type` or
  `lifecycle_status`, duplicate component/device/signal identifiers, topology or
  signal-mapping references to identifiers that do not exist, a missing or
  malformed Foundation validity interval, and ratings with a missing or
  unsupported unit.
- `SiteRepository` is defined in the product domain as a `typing.Protocol` with
  `list_sites()` and `get_site(site_id)` only. It has no `create_site`,
  `update_site`, `delete_site`, query or filter DSL, pagination, transaction, or
  caching method.
- The port error vocabulary lives in the port module, not in adapters.
  `SiteNotFound`, `SiteConfigurationInvalid`, and `SiteStoreUnavailable` are
  raised and exercised by tests in this slice.
- No `Path`, file handle, YAML text, raw loader `dict`, or store-specific
  exception appears in a port signature or crosses the port. Port arguments,
  return values, and errors are domain records and domain errors. An adapter
  translates `OSError`, `yaml.YAMLError`, and `UnicodeDecodeError` into port
  errors; a `yaml.YAMLError` reaching the service layer is a failure.
- Exactly one composition module imports `sites/adapters/**`. Every other
  backend module, including the API router and the service layer, receives a
  port by injection.
- `tools/check-architecture.ps1` gains two checks, written in the existing
  allowlist and line-regex shape used for the simulator URL chokepoint, and
  using the existing `(^|/)(tests|__tests__)/` exemption:
  - adapter isolation: an import of `sites.adapters` or `from .adapters`
    anywhere under `backend/` fails unless the file is the single allowlisted
    composition module;
  - no storage technology above the adapter layer: `import yaml`, `from yaml`,
    `import pathlib`, `from pathlib`, `import sqlite3`, and `open(` are banned
    inside the sites package outside `adapters/`.
- A fake in-memory `SiteRepository` satisfies the service layer in tests without
  importing anything from `adapters/`. If that test cannot be written, the port
  is wrong.
- `GET /api/sites` and `GET /api/sites/{site_id}` serve the Site read model. An
  unknown `site_id` returns a not-found response rather than a fabricated or
  empty Site. No `POST`, `PUT`, `PATCH`, or `DELETE` route exists for a Site.
- Sites List renders the shipped Site from the port, not from a hard-coded
  fixture in the frontend, and shows `display_name`, `site_id`, `site_type`,
  `lifecycle_status`, and `source.mode`.
- Site Details is addressed by `site_id` and replaces the parameterless
  `/site-details` placeholder route. An unknown `site_id` renders an explicit
  not-found state and no fabricated Site.
- Site identity in the read model, API paths, and UI routing derives only from
  `site_id`. `display_name` is never used for lookup, routing, an object key, or
  a filename.
- Lifecycle status, source mode, and integration readiness render as separate,
  independently labelled facts. A Site with `lifecycle_status = ACTIVE` and
  `source.mode = SIMULATED` shows both, and neither is presented as the other,
  as evidence state, or as source health.
- Site Details for a Site with no accepted evidence shows explicit No evidence
  or Unavailable states and renders no zero-value chart, fabricated telemetry,
  source-health value including OFFLINE, analytics, Replay control, or Finding.
- Sites List, Site Details, and `/api/sites*` are served identically with
  `simulator_lab.enabled` true and false. No Site route or Site API path is
  registered through the simulator gate, and the gate's existing chokepoint
  checks are neither weakened nor extended to cover Site routes.
- The simulator receives no repository handle. No module under the simulator
  root imports the sites package, the port, or an adapter.
- The carried-forward "no digits inside `<main>`" assertions in
  `operatorRouteFrames.test.tsx` and `simulatorLabGate.test.tsx` are replaced
  with Site-specific assertions wherever truthful Site values now render.
  Replace, never loosen: where a screen still renders no truthful value, the
  existing assertion stays.

## Required Product And Domain Semantics

- `site_id` is the universal Site identity. `run_id`, scenario labels, and run
  names are provenance only and never participate in Site identity.
- YAML is the authoritative representation of Site identity and Foundation
  content and is strictly validated on load, through one parser with no lenient
  path.
- A Site conceptually has stable Site identity plus a versioned Site Foundation;
  one M1 YAML document may hold both.
- `source.mode` and `source.provenance` are provenance, not lifecycle status,
  gateway health, evidence quality, or asset condition.
- A configuration-only Site is a valid Site with no accepted evidence. It is not
  an error state, not an offline state, and not a zero-valued Site.
- Configuration is reached only through a domain-defined port. Storage
  technology lives in an adapter chosen in one composition root, so replacing
  file storage later is a new adapter module plus one composition-root line and
  no change to callers.
- Presentation metadata such as a Site image is optional and must never affect
  identity, lookup, simulation, ingestion, analytics, or evidence
  interpretation.

## Protected Seams

- Configuration persistence port: CI guard.
  Configuration is reached only through the port; storage technology lives in
  adapters selected in one composition root. Guarded by the two new
  `tools/check-architecture.ps1` checks plus the fake in-memory adapter test.
- Site identity: contract test.
  Identity, routing, API paths, and object keys derive only from `site_id`;
  `display_name` is never identity.
- YAML configuration authority: unit/contract test.
  Strict validation on load with no lenient path, covering identity, Foundation
  version, components, topology, devices, mappings, ratings, control
  assumptions, and unsupported values.
- Configuration-only Site states: CI guard.
  A valid Site with no accepted evidence shows No evidence or Unavailable, never
  fabricated telemetry, zero-value charts, source health, analytics, or
  Findings.
- Read-only configuration UI: review-time + contract test.
  No update or delete route exists for a Site, and no screen in this slice
  offers an edit, Save, Publish, rename, delete, or history affordance.
- Simulator feature gate: CI guard.
  Site routes and Site APIs are product capabilities and must not be gated on
  `simulator_lab.enabled`. The gate's existing chokepoint discipline stays
  intact and is not extended to Sites.
- Simulator/product boundary: CI guard.
  The simulator is handed a Foundation; it never resolves one. It receives no
  repository handle and imports nothing from the sites package.
- Stack and module direction: CI guard.
  The new backend package preserves the modular roots and the one-way
  dependency direction.

## Focused Tests And Checks

- Parser tests over the canonical document and over invalid variants for each
  rejection listed in the acceptance criteria.
- Port contract test proving a fake in-memory `SiteRepository` satisfies the
  service layer with no import from `adapters/`.
- Adapter test proving store-level exceptions are translated into port errors
  and that no store-specific exception escapes the port.
- API tests for `GET /api/sites`, `GET /api/sites/{site_id}`, unknown
  `site_id`, and the absence of `POST`, `PUT`, `PATCH`, and `DELETE` on a Site.
- UI tests for the Sites List row content, `site_id`-addressed Site Details, the
  unknown-`site_id` state, and the configuration-only No evidence states.
- UI test asserting lifecycle status, source mode, and integration readiness are
  distinct labelled facts and that simulated provenance does not replace any of
  them.
- Route test asserting Sites List, Site Details, and `/api/sites*` behave
  identically with `simulator_lab.enabled` true and false.
- Run `tools/check-architecture.ps1`, including the two new checks: adapter
  import allowlisted to the single composition module, and no `yaml`,
  `pathlib`, `sqlite3`, or `open(` inside the sites package outside `adapters/`.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Do not add any write path. The port has no mutator in this slice, there is no
  writable store, no `.gitignore` change, and no `POST` route for a Site.
- Do not add templates, a template catalog, a template route, a Create action,
  or template provenance.
- Do not add in-place configuration editing, Save, Publish, rename, `site_id`
  change, delete, duplicate, Foundation version bump, configuration diff,
  history, rollback, or approvals.
- Do not build the read-only Site Configuration content surface; it is the next
  slice, and `/site-configuration` keeps its existing unavailable placeholder.
- Do not render a single-line diagram, an auto-layout, a Devices & Sensors
  screen, or a topology view model. Those belong to Causal Sequencing step 4.
- Do not add scenarios, run setup, simulator execution, gateway staging,
  ingestion, source envelopes, evidence records, source health, charts,
  analytics, Replay, or Findings.
- Do not introduce a database, ORM, migration tool, or cache. File-backed is
  sufficient, and the port exists so this stays a later, cheap decision.
- Do not add port methods speculatively. Add a method when a slice needs it.
- Do not give the simulator a repository handle, and do not gate any Site route
  or Site API on `simulator_lab.enabled`.
- Do not weaken the T003/T004 route and API boundary tests, and do not loosen
  the carried-forward fabricated-value assertions. Replace them with
  Site-specific assertions where truthful values now render; never relax them.
