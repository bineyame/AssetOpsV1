# T007 - Shipped Site Template Catalog

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T007-shipped-site-template-catalog`

## Feature

Site Foundation And Configuration-Only Site.

## UI-Verifiable Screen Behavior

A configuration templates surface, reachable from a product route separate from
Sites, lists the shipped configuration templates by `template_id` and
`template_version`. Opening one shows the Foundation content that template would
produce, read-only.

A template is visibly not a Site. It has no `site_id`, no lifecycle status, no
location, and no timezone binding to a real place. It never appears in Sites
List, cannot be opened as Site Details or Site Configuration, and offers no
Create, Instantiate, or Use action. Sites List still contains only Sites.

## Why This Is Next

This is Causal Sequencing step 3b, and its position is a real dependency, not
sequencing preference. If creation lands first, the only thing a user can create
from is an empty form or a copy of a shipped Site. The first is free-form
authoring, which is the largest validation surface and the least milestone
value. The second quietly makes "shipped Site" and "template" the same thing,
and then identity, precedence, and provenance rules all become retrofits over
data users have already created. Retrofitting identity rules after user data
exists is the late failure this project's seam discipline exists to prevent.

So the template/instance distinction has to be structural before anything can be
written. This slice makes it structural and visible while nothing is writable
yet.

## Acceptance Criteria

- At least one shipped template document exists under a template configuration
  root that is separate from the shipped Sites root, git-tracked, and read-only
  at runtime.
- The template document is a separate file from the canonical Site fixture, even
  where content overlaps. The two are not deduplicated into one source.
- A template declares `template_id`, `template_version`, and Foundation content.
  It declares no `site_id`, no `lifecycle_status`, no location, and no
  place-bound timezone. A template document carrying `site_id` or
  `lifecycle_status` is rejected by the parser with a message naming the
  offending field.
- `SiteTemplateCatalog` is a separate `typing.Protocol` from `SiteRepository`,
  with `list_templates()` and `get_template(template_id)` only. It is not a
  subclass, mode, flag, or parameterization of `SiteRepository`, and no type in
  the model makes "a template is a kind of Site" true.
- Template documents cross the same strict parser posture as Site documents:
  unknown keys rejected, no lenient path, no template-only relaxation.
- The template adapter lives under `sites/adapters/` and is imported only by the
  single composition module. The T005 adapter isolation and storage-technology
  guards pass unchanged with the new module present.
- `GET /api/site-templates` and `GET /api/site-templates/{template_id}` serve the
  template read model. An unknown `template_id` returns a not-found response. No
  `POST`, `PUT`, `PATCH`, or `DELETE` route exists for a template.
- `tools/check-architecture.ps1` gains a check that no write-capable path
  constant resolves inside the shipped configuration root, so neither the
  shipped Sites catalog nor the template catalog can be written at runtime.
- The templates route is distinct from `/sites`, is labelled as configuration
  templates rather than Sites, and is not nested under a Site.
- A test asserts that with the template catalog present, Sites List contains
  only Sites: no `template_id` appears as a Site row, and no Site Details or
  Site Configuration route resolves a `template_id`. Requesting
  `GET /api/sites/{template_id}` returns not-found.
- The template inspection view renders the Foundation content the template would
  produce, from the document rather than hard-coded, and states plainly that a
  template is not a Site and has no Site identity.
- The template inspection view offers no Create, Instantiate, Use, Copy, edit,
  Save, Publish, upload, import, delete, or rename action.
- The template surface shows no operational values: no telemetry, charts, source
  health, analytics, Replay, or Findings, and no simulated provenance.
- Template routes and `/api/site-templates*` are served identically with
  `simulator_lab.enabled` true and false, and are not registered through the
  simulator gate.
- The simulator receives no template catalog handle and imports nothing from the
  sites package.
- The carried-forward "no digits inside `<main>`" assertions are replaced with
  template-specific assertions wherever truthful template values now render.
  Replace, never loosen.

## Required Product And Domain Semantics

- A template is not a Site. It has `template_id` and `template_version` in its
  own identity space, no `site_id`, no lifecycle status, no location, and no
  timezone binding to a real place. It cannot be listed as a Site, targeted by a
  scenario, simulated, or receive evidence.
- Template identity must never become Site identity. This is the direct analogue
  of the existing rule that scenario labels must not become Site identity.
- Shipped canonical configuration is read-only at runtime.
- `template_version` exists so that later drift between a template and the Sites
  derived from it stays inspectable. It is not a Site Foundation version.
- Template Foundation content is component truth, not evidence. Showing a
  template's devices is not a claim that any device exists or has reported.

## Protected Seams

- Shipped versus user-authored configuration: CI guard.
  Templates are not Sites and hold no `site_id`; shipped configuration is
  read-only at runtime and lives outside any writable store. Guarded by the
  parser rejection of `site_id` in a template, the Sites-List exclusion test,
  and the new shipped-catalog write check.
- Site identity: contract test.
  `template_id` is a separate identity space and never resolves as a `site_id`.
- Configuration persistence port: CI guard.
  `SiteTemplateCatalog` is a domain-defined port; its adapter is imported only
  by the composition module, and no storage technology appears above the adapter
  layer.
- YAML configuration authority: unit/contract test.
  Templates cross the same strict parser with no lenient path.
- Read-only configuration UI: review-time + contract test.
  Templates are read-only; no authoring, upload, edit, or write route exists.
- Configuration-only Site states: CI guard.
  The template surface shows no fabricated operational content.
- Simulator feature gate: CI guard.
  Template routes are product capabilities and are not gated on
  `simulator_lab.enabled`.
- Stack and module direction: CI guard.
  The template port and adapter preserve the one-way dependency direction.

## Focused Tests And Checks

- Parser tests over the shipped template document and over invalid variants,
  including a template that declares `site_id` and a template with unknown keys.
- Contract test proving `SiteTemplateCatalog` is satisfied by a fake in-memory
  catalog with no import from `adapters/`.
- Type-level or structural test proving `SiteTemplateCatalog` and
  `SiteRepository` are independent protocols and that a template record is not
  accepted where a Site record is required.
- API tests for `GET /api/site-templates`, `GET /api/site-templates/{id}`, an
  unknown `template_id`, and the absence of any write route for a template.
- Test asserting `GET /api/sites/{template_id}` returns not-found and that no
  `template_id` appears in the Sites List response or UI.
- UI tests for the templates list, the template inspection view, the
  not-a-Site statement, and the absence of any Create, Instantiate, upload,
  import, edit, Save, Publish, delete, or rename action.
- Route test asserting template routes behave identically with
  `simulator_lab.enabled` true and false.
- Run `tools/check-architecture.ps1`, including the T005 adapter isolation and
  storage-technology checks and the new shipped-catalog write check.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Do not add instantiation, a Create action, `create_site`, any port mutator,
  the writable user store, user Sites, or a `.gitignore` change. Those are T008.
- Do not add template authoring, template upload, template editing, template
  deletion, or import of an arbitrary YAML document. Those are outside M1.
- Do not add in-place Site editing, Save, Publish, rename, delete, approvals,
  configuration diff, history, or rollback.
- Do not reuse the canonical Site fixture as the template, and do not
  deduplicate the two documents into one source. The separation is the point.
- Do not render a single-line diagram, auto-layout, a Devices & Sensors screen,
  or a topology view model.
- Do not add scenarios, run setup, simulator execution, gateway staging,
  ingestion, source envelopes, evidence records, source health, charts,
  analytics, Replay, or Findings.
- Do not introduce a database, ORM, migration tool, or cache.
- Do not add port methods speculatively.
- Do not give the simulator a repository or catalog handle, and do not gate any
  template route on `simulator_lab.enabled`.
- Do not weaken the T003/T004 route and API boundary tests or the T005/T006
  guards, and do not loosen the carried-forward fabricated-value assertions.
  Replace them where truthful values now render; never relax them.

This slice deliberately carries no user-review checkpoint of its own. The
template-versus-Site language it introduces is reviewed together with the
creation semantics in T008, because the two settle one question: what a
user-authored Site is and what the product does not promise about it. The
placement and label of the templates route is part of what T008 puts to the
user.
