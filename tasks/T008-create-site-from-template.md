# T008 - Create A Site From A Template

Status: planned
USER_REVIEW_REQUIRED: true

Intended branch: `task/T008-create-site-from-template`

## Feature

Site Foundation And Configuration-Only Site.

## UI-Verifiable Screen Behavior

From the template catalog the user chooses a template, supplies a `site_id` and
the required identity-level fields, and creates a Site. The created Site appears
in Sites List beside the shipped Site, with configuration origin `USER` and the
originating `template_id` and `template_version` shown as provenance. It opens
as a normal configuration-only Site Details and a read-only Site Configuration,
and it is still there after the backend restarts.

A `site_id` that is already in use, including a case variant of an existing one,
or a malformed `site_id`, is refused with a specific readable reason and nothing
is written. There is still no way to edit, rename, or delete a Site once it
exists, and Site Configuration stays read-only for every Site regardless of
origin.

## Why This Is Next

This is Causal Sequencing step 3c and the first untrusted-input write boundary
in the product. It arrives third deliberately: it inherits an already-validated
read model from T005 and T006 and an already-separate template namespace from
T007, instead of inventing both under write pressure.

Creating a Site is safe to ship now because it writes a brand-new `site_id` that
nothing depends on yet. No scenario targets it, no run references it, no
envelope carries it, no evidence record is keyed to it, and no mapping version
has been consumed. Its blast radius is the validation of one new document.
Editing an existing Foundation is a different capability with a different risk
and stays deferred.

## Acceptance Criteria

- `create_site` is added to `SiteRepository`. The port still has no
  `update_site`, `delete_site`, query or filter DSL, pagination, transaction, or
  caching method.
- A writable user store root exists outside the shipped configuration root, its
  location is declared in exactly one module, and `.gitignore` covers it.
- A composite adapter merges the shipped and user Site namespaces into one
  globally unique `site_id` space with no overlay and no precedence. The same
  `site_id` present in both stores fails loudly at load rather than resolving to
  either document.
- `site_id` uniqueness is compared case-insensitively. `MG-002` and `mg-002` are
  the same identity, and the comparison is enforced at the port so behavior does
  not depend on the host filesystem.
- `create_site` is create-if-absent and never upsert. It raises
  `SiteIdentityConflict` when the `site_id` already exists in either store, and
  never overwrites an existing document under any condition.
- `site_id` is charset- and shape-constrained, enforced at the port rather than
  only in the adapter. Path separators, `.`, `..`, absolute-looking values, and
  Windows reserved device names are rejected.
- The fully materialized Site document is built, parsed, and validated by the
  same strict parser used for shipped documents, with no lenient path and no
  user mode, before anything touches the store.
- A create that fails validation, identity checks, or the conflict check leaves
  the store byte-identical. A test asserts this by comparing the store contents
  before and after a failed create.
- The write is atomic and exclusive: exclusive create plus write-temp-then-
  atomic-replace within the same directory, with flush and fsync before replace.
  A half-written document can never be left behind.
- Instantiation deep-copies the template Foundation content into the new Site
  document and records `origin = USER`, `origin.template_id`, and
  `origin.template_version`. The created Site does not live-reference the
  template. A test mutates the template file after creation and asserts the
  created Site is unchanged.
- `template_id` is provenance only. It never becomes `site_id`, never appears as
  Site identity, and is never used for lookup, routing, or a filename.
- Document size and collection cardinality are bounded, so an oversized or
  pathological document is refused rather than accepted, and cannot make the
  Sites index unopenable.
- Free text, including `display_name`, notes, and image references, is stored
  and rendered as text, never as markup, and is never used for lookup, a
  filename, or routing. `display_name` is not `site_id`.
- `POST /api/sites` exists. `PUT`, `PATCH`, and `DELETE` on a Site are still not
  served anywhere in the served route inventory.
- Refusals carry specific product copy, not stack traces or generic failures.
  A conflicting id and a malformed id produce different, readable reasons that
  name what is wrong and what would be acceptable.
- The created Site survives a backend restart and is present in Sites List, Site
  Details, and Site Configuration afterwards.
- The created Site renders identically to a shipped Site everywhere except its
  configuration origin and template provenance. It is a normal
  configuration-only Site: explicit No evidence or Unavailable states, no
  fabricated telemetry, zero-value charts, source health, analytics, Replay, or
  Findings.
- Site Configuration for a `USER`-origin Site is read-only, carries the same
  "configuration is fixed at creation in M1" statement, and offers no edit,
  Save, Publish, rename, `site_id` change, delete, duplicate, approve, diff,
  history, or rollback control, enabled or disabled.
- Configuration origin, `source.mode`, lifecycle status, integration readiness,
  and source health remain five independently labelled facts. None is rendered
  as a proxy for another, and a `USER`-origin Site may be
  `lifecycle_status = ACTIVE` with `source.mode = SIMULATED` and no evidence.
- `tools/check-architecture.ps1` gains the remaining shipped-versus-user checks:
  the user store root is declared in exactly one module, `.gitignore` covers it,
  and no write-capable path constant resolves inside the shipped configuration
  root. The T005 adapter isolation and storage-technology checks and the T007
  shipped-catalog check still pass with the write adapter present.
- The write adapter lives under `sites/adapters/` and is imported only by the
  single composition module. The create path goes API handler to service to port
  to adapter, with no shortcut to storage.
- Site creation routes and APIs are served identically with
  `simulator_lab.enabled` true and false, and are not registered through the
  simulator gate.
- The simulator receives no repository handle and imports nothing from the sites
  package.
- The carried-forward "no digits inside `<main>`" assertions are replaced with
  creation- and Site-specific assertions wherever truthful values now render.
  Replace, never loosen.

## Required Product And Domain Semantics

- Creation and editing are different capabilities. M1 ships creation. In-place
  Foundation editing, Save and Publish over an existing Foundation, rename,
  `site_id` change, delete, duplicate-into-existing-id, Foundation version bump
  in place, configuration diff, history, rollback, and approvals stay
  unavailable for the rest of M1.
- `site_id` is immutable after creation, and a created Site cannot be deleted in
  M1. Removing a Site is a developer action on the store, not a product
  capability, until the user decides otherwise.
- Shipped Sites and user-created Sites share one globally unique `site_id`
  space. There is no overlay and no precedence, because an identity that
  resolves to different content depending on store state would silently fork
  Site history for every later run, envelope, evidence record, and analytic.
- Origin is not encoded into identity. User `site_id` values are not prefixed;
  origin is a field.
- Templates are instantiated by copy. A later template change never alters an
  already-created Site, because silent retroactive Foundation change is what the
  evidence-immutability posture exists to prevent.
- User-authored configuration is untrusted input. It crosses the same strict
  parser as shipped configuration, and the thing written is the thing that was
  validated.
- Configuration origin is provenance about the configuration document, distinct
  from `source.mode`, lifecycle status, integration readiness, and source
  health.

## Protected Seams

- User-authored configuration input: unit/contract test.
  The fully materialized document is validated before any write; unknown keys
  and oversized documents are rejected; `site_id` is charset-constrained, cannot
  traverse, and cannot collide case-insensitively; free text is never identity
  or a path; writes are atomic and a failed write leaves the store
  byte-identical.
- Shipped versus user-authored configuration: CI guard.
  Shipped configuration stays read-only and outside the writable store;
  `site_id` is globally unique across both stores with no overlay; `template_id`
  is provenance and never Site identity; changing a template does not alter an
  already-created Site.
- Configuration persistence port: CI guard.
  The write adapter is imported only by the composition module; the port and
  service layers name no file, path, or serialization format; the create path
  never reaches storage directly.
- Read-only configuration UI: review-time + contract test.
  Site Configuration is read-only for `USER`-origin Sites too, with no edit,
  Save, Publish, rename, delete, or history affordance, and no update or delete
  route exists for a Site.
- Site identity: contract test.
  `site_id` is the only Site identity; `template_id` and `display_name` are not.
- Configuration-only Site states: CI guard.
  A newly created Site with no evidence shows No evidence or Unavailable, never
  fabricated operational content.
- YAML configuration authority: unit/contract test.
  One strict parser for both stores, with no lenient path for user documents.
- Simulator feature gate: CI guard.
  Site creation is a product capability and is not gated on
  `simulator_lab.enabled`.
- Simulator/product boundary: CI guard.
  The simulator gets no repository handle and does not resolve configuration.

## Focused Tests And Checks

- Port contract tests: create refuses an existing `site_id` in the shipped
  store, in the user store, and as a case variant of either.
- Load test: the same `site_id` present in both stores fails loudly at startup
  rather than resolving to one of them.
- Identity validation tests covering path separators, `.`, `..`,
  absolute-looking values, Windows reserved device names, empty and
  over-length values, and the accepted charset.
- Parser tests over a user-authored document fixture covering unknown keys and
  an oversized or over-cardinality document.
- Atomicity tests: a create that fails validation leaves the store
  byte-identical; a create that fails after the temp file is written leaves no
  partial or stray document.
- Provenance test: mutating the template document after creation does not change
  the created Site; `origin.template_id` and `origin.template_version` are
  recorded and rendered as provenance.
- Persistence test: the created Site is present after the backend is restarted
  against the same store.
- API tests for `POST /api/sites` success, conflict, and malformed-id refusal,
  asserting distinct specific reasons, and for the continued absence of `PUT`,
  `PATCH`, and `DELETE` on a Site in the served route inventory.
- Contract test proving the fake in-memory `SiteRepository`, now including
  `create_site`, still satisfies the service layer with no import from
  `adapters/`.
- UI tests for the create flow, the created Site in Sites List with its
  configuration origin and template provenance, the configuration-only Site
  Details, the read-only Site Configuration for a `USER`-origin Site, and the
  two refusal messages.
- Route test asserting the create flow and its API behave identically with
  `simulator_lab.enabled` true and false.
- Run `tools/check-architecture.ps1`, including the T005 adapter isolation and
  storage-technology checks, the T007 shipped-catalog write check, and the new
  single-declaration and `.gitignore` checks for the user store root.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Do not add in-place Foundation editing, Save or Publish over an existing
  Foundation, rename, `site_id` change, delete, duplicate-into-existing-id,
  Foundation version bump in place, configuration diff, history, rollback, or
  approvals, and do not add disabled placeholders for them.
- Do not add free-form authoring of a Site from scratch, authoring or uploading
  a template in-product, editing a template, or importing an arbitrary YAML
  document. Those are deliberately not scheduled for M1.
- Do not add a user-facing way to remove a user-created Site. Removal is a
  developer action on the store for now, and is an open question for the user
  recorded below.
- Do not add bulk creation, cloning an existing Site, or creating a Site without
  a template.
- Do not add `update_site`, `delete_site`, a query DSL, pagination,
  transactions, or caching to the port.
- Do not overlay stores, add precedence between them, or prefix user `site_id`
  values with an origin marker.
- Do not let the create path reach storage directly, even for one case. API
  handler to service to port to adapter, always.
- Do not introduce a database, ORM, migration tool, or cache.
- Do not render a single-line diagram, auto-layout, a Devices & Sensors screen,
  or a topology view model.
- Do not add scenarios, run setup, simulator execution, gateway staging,
  ingestion, source envelopes, evidence records, source health, charts,
  analytics, Replay, or Findings.
- Do not give the simulator a repository handle, and do not gate any Site,
  template, or creation route on `simulator_lab.enabled`.
- Do not weaken the T003/T004 route and API boundary tests or the T005 to T007
  guards, and do not loosen the carried-forward fabricated-value assertions.
  Replace them where truthful values now render; never relax them.

## User Review

User review is required. This is the second of the two checkpoints the Architect
named for this feature, and it carries the template-versus-Site language
deferred from T007.

What the user is being asked to settle:

- Creation semantics: that a user creates a Site by choosing a shipped template
  and supplying identity, that `site_id` is immutable afterwards, and that
  nothing about the Site can be edited once it exists.
- Template-versus-Site language: how a template is presented so it never reads
  as a Site, where the templates surface lives and what it is called, and how
  the copy-not-reference relationship is described.
- Configuration origin and template provenance language on Sites List, Site
  Details, and Site Configuration, and that origin is not confused with source
  mode, lifecycle status, integration readiness, or source health.
- Refusal copy for a duplicate `site_id`, a case-variant duplicate, and a
  malformed `site_id`.

Settled before implementation, not open at this checkpoint: the Architect asked
whether M1 should offer a user-facing way to remove a user-created Site, and the
user deferred it on 2026-09-13. Removal stays a developer action on the store
for M1, and no delete affordance, route, or port method is in scope here. If the
user revisits it later it becomes its own slice with explicit archive,
tombstone, or hard-delete semantics, never folded into this task.

Planning stops at this checkpoint. Causal Sequencing step 4, topology, devices,
and the configured single-line diagram, is not planned until this is accepted or
redirected.
