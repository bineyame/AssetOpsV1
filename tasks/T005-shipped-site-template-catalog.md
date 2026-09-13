# T005 - Shipped Site Configuration Template Catalog

Status: in_review
USER_REVIEW_REQUIRED: false

Intended branch: `task/T005-shipped-site-template-catalog`

## Agent Brief

Build the first Site Template catalog slice in the Simulator Lab only. With
`simulator_lab.enabled` true, the Lab lists shipped templates and opens a
read-only template inspection view. With the flag false, the template route and
API are absent.

Primary implementation work:

- Add a shipped, read-only template configuration root with one Hybrid Mini-Grid
  archetype.
- Add domain records, strict parser, `SiteTemplateCatalog` port, read-only YAML
  adapter, service/composition boundary, gated API, and Lab UI.
- Extend route/API inventory tests and architecture checks for adapter
  isolation, no storage technology above adapters, and no writable path inside
  the shipped catalog root.

Hard limits:

- Do not create a Site, Site repository, writable user store, create action,
  operator navigation item, SLD, signal selector, simulator execution, evidence,
  analytics, Replay, or Findings.
- Do not let a template be a kind of Site; reject `site_id`,
  `lifecycle_status`, unknown keys, oversized documents, and over-cardinality
  documents.
- Do not weaken the T003/T004 gate, route, API, or navigation boundary tests.

Read with this brief:

- `.ai/ACTIVE_CONTEXT.md`
- `.ai/FEATURE_MAP.md` Feature Map Index, Product Spine, Enforceable Protected
  Seams, and Early Feature: Site Foundation And Configuration-Only Site.
- `.ai/DECISIONS.md` only for the decision IDs named by `.ai/ACTIVE_CONTEXT.md`.

## Feature

Site Foundation And Configuration-Only Site.

## UI-Verifiable Screen Behavior

With `simulator_lab.enabled` true, the Simulator Lab developer workspace gains a
Site Templates surface. It lists the shipped configuration templates by
`template_id` and `template_version`, and opening one shows the Foundation
content that template would produce, read-only.

A template is visibly not a Site. It has no `site_id`, no lifecycle status, no
location, and no timezone bound to a real place. It cannot be opened as a Site,
and it offers no Create, Instantiate, or Use action, because nothing can be
created yet.

The operator shell is unchanged. Operator navigation gains no item, the Sites
index is still the empty frame T002 shipped, and no Site exists anywhere in the
product.

With `simulator_lab.enabled` false, the Site Templates surface, its route, and
its API are not served at all, and the product is exactly what T004 left behind.

## Why This Is Next

This is Causal Sequencing step 3a, and its position is a real dependency rather
than a preference. The template concept has to be structural before anything can
be written. If creation lands first, its only source is an empty form or a copy
of a shipped Site; the second quietly makes "shipped Site" and "template" the
same thing, and identity, precedence, and provenance rules then become retrofits
over data users have already created.

The catalog is also the first real read consumer of the persistence port, and a
better one than a Site fixture would be: it is a complete truthful screen that
requires no Site to exist. So the port layer, the strict parser, the composition
root, and the persistence CI guards all arrive here, proven against a screen,
without a Site nobody configured standing in the Sites index.

Shell placement follows the settled reading of the mockups. v6.9 lists Site
Templates in the Simulator Lab shell's own navigation and nowhere in the
operator's, and authoring a simulated Site is a Lab capability. Where a
Site-authoring surface is ambiguous it ships gated, because un-gating later is
cheap and retrofitting a gate around a shipped ungated surface is the
hidden-but-reachable failure the gate exists to prevent.

## Acceptance Criteria

- At least one shipped template document exists under a git-tracked template
  configuration root that is read-only at runtime and separate from any Site
  store. The Hybrid Mini-Grid archetype named in `SimulatorLab1.png` is the one
  that ships.
- A template declares `template_id`, `template_version`, and Foundation content.
  It declares no `site_id`, no `lifecycle_status`, no location, and no
  place-bound timezone. A template document carrying `site_id` or
  `lifecycle_status` is rejected by the parser with a message naming the
  offending field.
- `SiteTemplateCatalog` is a `typing.Protocol` owned by the product domain, with
  `list_templates()` and `get_template(template_id)` only. It is not a subclass,
  mode, flag, or parameterization of a Site repository, and no type in the model
  makes "a template is a kind of Site" true. No `SiteRepository`, no write
  adapter, and no writable store ships in this slice.
- Port signatures and port errors speak domain records only. No `Path`, file
  handle, YAML string, loader `dict`, or store-specific exception crosses the
  port. The port error vocabulary is defined in the ports module and covers what
  this slice needs: template not found, configuration invalid, and store
  unavailable. Adapters translate `OSError`, `yaml.YAMLError`, and
  `UnicodeDecodeError` into it; a `yaml.YAMLError` reaching the service layer is
  a seam failure, not a bug to catch there.
- The parsing module takes an already-loaded `Mapping` and returns domain
  records. It needs no exemption from the storage-technology guard below; if it
  needs one, its signature is wrong.
- The template adapter lives under the sites `adapters/` package and is imported
  only by the single composition module. Everything else receives the port by
  injection.
- `tools/check-architecture.ps1` gains three checks with the same test
  exemptions and failure posture as the existing architecture guards:
  - Adapter isolation: imports resolving into the sites `adapters/` package are
    permitted only from the one allowlisted composition module.
  - No storage technology above the adapter layer: inside the sites package but
    outside `adapters/`, `import yaml`, `from yaml`, `import pathlib`,
    `from pathlib`, `import sqlite3`, and `open(` are banned.
  - The shipped catalog is not writable: no write-capable path constant resolves
    inside the shipped configuration root.
- The strict parser rejects unknown keys, has no lenient path, and bounds
  document size and collection cardinality, so a pathological document is
  refused rather than accepted.
- The Site Templates surface and its API are served only when
  `simulator_lab.enabled` is true. With the flag false the surface is not
  rendered, its route is not registered, and its API path is absent from the
  served route inventory. The T003 route and API inventory tests are extended to
  cover the new paths, never weakened.
- Lab-only routes and API paths are addressed under the Simulator Lab path
  prefix, so the existing simulator-URL chokepoint in
  `tools/check-architecture.ps1` covers them. The `$gatedModules` allowlist is
  not extended and no second chokepoint is introduced.
- Operator navigation, operator routes, and the operator shell are structurally
  identical in both flag states and unchanged from T004. The Sites index still
  renders its empty frame and contains no template.
- No Site exists after this slice. No Site document ships, no `site_id` appears
  anywhere in the product, and no route resolves a Site by identity.
- The template inspection view renders Foundation content from the document
  rather than hard-coded values, and states plainly that a template is not a
  Site and has no Site identity.
- Neither template surface offers a Create, Instantiate, Use, Copy, edit, Save,
  Publish, upload, import, delete, or rename action, enabled or disabled.
- Neither template surface shows operational values: no telemetry, charts,
  source health, evidence, analytics, Replay, or Findings, and no source-mode
  badge, because a template has no source.
- Neither template surface renders a Single Line Diagram, an empty frame for
  one, or a signal selector.
- No value, timestamp, status, or label appears because a mockup shows it. Every
  rendered value traces to the template document under test.
- The simulator receives no catalog handle and imports nothing from the sites
  package.
- The carried-forward "no digits inside `<main>`" assertions in
  `simulatorLabGate.test.tsx` are replaced with template-specific assertions
  wherever truthful template values now render. Replace, never loosen.

## Required Product And Domain Semantics

- A template is not a Site. It has `template_id` and `template_version` in its
  own identity space, no `site_id`, no lifecycle status, no location, and no
  timezone binding to a real place. It cannot be listed as a Site, targeted by a
  scenario, simulated, or receive evidence.
- Template identity must never become Site identity. This is the direct analogue
  of the existing rule that scenario labels must not become Site identity.
- Shipped canonical configuration is read-only at runtime and lives outside any
  writable store.
- `template_version` exists so that later drift between a template and the Sites
  derived from it stays inspectable. It is not a Site Foundation version.
- Template Foundation content is component truth, not evidence. Showing a
  template's devices and ratings is not a claim that any device exists or has
  reported.
- The gate covers surfaces and execution, never objects or stores. Nothing in
  this slice creates an object, so the gate here removes only a developer
  workspace surface.

## Protected Seams

- Shipped versus user-authored configuration: CI guard.
  Templates are not Sites and hold no `site_id`; shipped configuration is
  read-only at runtime and lives outside any writable store. Guarded by the
  parser rejection of `site_id` and `lifecycle_status` in a template, by the
  absence of any Site, and by the new shipped-catalog write check.
- Configuration persistence port: CI guard.
  `SiteTemplateCatalog` is a domain-defined port; its adapter is imported only
  by the composition module; no storage technology appears above the adapter
  layer; a fake in-memory catalog satisfies the service layer.
- YAML configuration authority: unit/contract test.
  One strict parser, no lenient path, explicit failure for unknown keys,
  invalid references, duplicate identities, invalid ratings, and unsupported
  values.
- Site identity: contract test.
  `template_id` is a separate identity space and never resolves as a `site_id`.
- Simulator feature gate: CI guard.
  The template surface and its API are Lab surfaces and are not served with the
  flag off; the single URL chokepoint is preserved and its allowlist is not
  extended.
- Read-only configuration UI: review-time + contract test.
  Templates are read-only; no authoring, upload, edit, or write route exists.
- Configuration-only Site states: CI guard.
  The template surfaces show no fabricated operational content.
- Mockup fidelity versus product honesty: CI guard.
  No mockup literal renders as content; no enabled control lacks a backing
  capability; the Lab navigation gains no destination without a truthful route
  behind it.
- Stack and module direction: CI guard.
  The port and adapter preserve the one-way dependency direction.
- Simulator/product boundary: CI guard.
  The simulator gets no catalog handle and does not resolve configuration.

## Focused Tests And Checks

- Parser tests over the shipped template document and over invalid variants:
  a template declaring `site_id`, a template declaring `lifecycle_status`,
  unknown keys, an oversized document, and an over-cardinality document.
- Contract test proving a fake in-memory `SiteTemplateCatalog` satisfies the
  service layer with no import from `adapters/`.
- Structural test proving the catalog port is independent of any Site
  repository type and that a template record is not accepted where a Site record
  is required.
- API tests for the template list and template detail paths, an unknown
  `template_id`, and the absence of any write route for a template.
- Route and API inventory tests in both flag states, extending
  `backend/tests/route_inventory.py` and the T003 frontend gate tests: the
  template paths are served with the flag on and absent with it off.
- UI tests for the template list, the template inspection view, the
  not-a-Site statement, and the absence of any Create, Instantiate, upload,
  import, edit, Save, Publish, delete, or rename control.
- UI test asserting operator navigation and operator routes are unchanged from
  T004 in both flag states, and that the Sites index contains no template.
- UI test asserting no diagram container, no diagram heading, and no signal
  selector renders on either template surface.
- Run `tools/check-architecture.ps1`, including the three new checks: adapter
  isolation, no storage technology above the adapter layer, and the shipped
  catalog not writable.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Inherit the M1 Step 3 exclusions from `.ai/ACTIVE_CONTEXT.md`.
- Do not add instantiation, a Create action, `SiteRepository`, `create_site`,
  any port mutator, the writable user store, user Sites, or a `.gitignore`
  change. Those are T006.
- Do not add template authoring, upload, editing, deletion, or arbitrary YAML
  import. Those are outside M1.
- Do not ship a canonical Site in the shipped Site store. M1 ships zero Sites.
- Do not apply canonical mockup layout to these surfaces yet. Content before
  chrome: fidelity for the template surfaces is T010, after the shared visual
  vocabulary lands in T009.

## User Review

User review is deliberately not required for this slice. The
template-versus-Site language it introduces is reviewed together with creation
semantics at the T006 checkpoint, because the two settle one question: what a
user-authored Site is, and what a template is not. Splitting that question
across two reviews would settle half of it against a surface that cannot yet
produce a Site.
