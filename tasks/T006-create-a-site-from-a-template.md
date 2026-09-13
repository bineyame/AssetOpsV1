# T006 - Create A Site From A Template, And The Sites Index

Status: planned
USER_REVIEW_REQUIRED: true

Intended branch: `task/T006-create-a-site-from-a-template`

## Feature

Site Foundation And Configuration-Only Site.

## UI-Verifiable Screen Behavior

On first run the operator Sites index is genuinely empty and says so. Nothing
has been configured, and the screen does not pretend otherwise.

With `simulator_lab.enabled` true, the empty state offers exactly one action: a
gated way into the Simulator Lab create flow. In the Lab the user picks a
shipped template, supplies a `site_id` and the required identity-level fields,
and creates a Site. The operator Sites index then shows one row for the Site the
user just created, keyed by `site_id`, carrying configuration origin `USER`,
the originating `template_id` and `template_version` as provenance, source mode
`SIMULATED` as provenance, and lifecycle status as a separate fact. The row is
still there after the backend restarts.

A `site_id` that is already in use, including a case variant of one, and a
malformed `site_id`, are refused with specific readable reasons and nothing is
written.

With `simulator_lab.enabled` false, the Sites index shows the same Sites with
the same data, and offers no way to add one. The empty state then says only that
no Sites are configured. That is the correct state for a gate-off build, not a
defect.

Rows are not yet links, and no per-Site route is registered. Site Details
addressed by `site_id` arrives in T007, and a destination does not appear before
the route behind it renders a truthful surface.

## Why This Is Next

This is Causal Sequencing step 3b and the first untrusted-input write boundary
in the product. It arrives second deliberately: it inherits an already-validated
strict parser, an already-proven port layer, and an already-separate template
namespace from T005, instead of inventing all three under write pressure.

It is also the first moment the Sites index has a truthful reason to contain a
row. A Sites index is a view over Sites somebody configured, so the capability
that fills it comes before the view, and the milestone's own first clause, "a
user can configure one mini-grid site", is satisfied here rather than at the end
of the feature.

Creating a Site is safe to ship now because it writes a brand-new `site_id` that
nothing depends on yet. No scenario targets it, no run references it, no
envelope carries it, no evidence record is keyed to it, and no mapping version
has been consumed. Its blast radius is the validation of one new document.
Editing an existing Foundation is a different capability with a different risk
and stays deferred for the whole milestone.

Site presentation is introduced here rather than later because this is the first
slice that presents a Site at all, and the substrate rule is cheap before a
second consumer exists and expensive after two shells each grow a Site page.

## Acceptance Criteria

### The port and the write path

- `SiteRepository` is a `typing.Protocol` owned by the product domain, with
  `list_sites()`, `get_site(site_id)`, and `create_site(record)` only. It has no
  `update_site`, no `delete_site`, no query or filter DSL, no pagination, no
  transaction, and no caching method. `SiteRepository` and
  `SiteTemplateCatalog` remain separate protocols.
- The port error vocabulary gains site not found and site identity conflict,
  alongside the configuration-invalid and store-unavailable errors T005
  defined. Port signatures and errors still speak domain records only.
- A writable user store root exists outside the shipped configuration roots and
  is configured from one owned location; `.gitignore` covers it.
- The shipped Site store ships empty. A test asserts that on a clean checkout it
  contains no Site and the Sites index therefore renders its first-run empty
  state. No fixture Site is added to the product.
- A composite adapter merges the shipped and user Site namespaces into one
  globally unique `site_id` space with no overlay and no precedence. The same
  `site_id` present in both stores fails loudly at load rather than resolving to
  either document. This is proven with a test fixture store, never by shipping a
  product-visible Site.
- `site_id` uniqueness is compared case-insensitively, enforced at the port so
  behavior does not depend on the host filesystem. `MG-002` and `mg-002` are the
  same identity.
- `create_site` is create-if-absent and never upsert. It raises the identity
  conflict error when the `site_id` already exists in either store and never
  overwrites an existing document under any condition.
- `site_id` is charset- and shape-constrained at the port rather than only in
  the adapter. Path separators, `.`, `..`, absolute-looking values, Windows
  reserved device names, empty values, and over-length values are rejected.
- The fully materialized Site document is built, parsed, and validated by the
  same strict parser used for shipped documents, with no lenient path and no
  user mode, before anything touches the store. The thing written is the thing
  that was validated.
- A create that fails validation, identity checks, or the conflict check leaves
  the store byte-identical. A test asserts this by comparing store contents
  before and after a failed create.
- The write is atomic, exclusive, and durable enough that a failed create cannot
  leave a half-written document behind.
- Instantiation deep-copies the template Foundation content into the new Site
  document and records configuration origin `USER`, `template_id`, and
  `template_version`. The created Site does not live-reference the template. A
  test mutates the template document after creation and asserts the created Site
  is unchanged.
- `template_id` is provenance only. It never becomes `site_id`, never appears as
  Site identity, and is never used for lookup, routing, or a filename.
- Document size and collection cardinality are bounded, so an oversized or
  pathological document is refused rather than accepted and cannot make the
  Sites index unopenable.
- Free text, including display name, notes, and any image reference, is stored
  and rendered as text, never as markup, and is never used for lookup, a
  filename, or routing. A display name is not a `site_id`.
- Refusals carry specific product copy, not stack traces or a generic failure.
  A conflicting id, a case-variant conflict, a malformed id, and a missing
  required identity field produce distinct readable reasons that name what is
  wrong and what would be acceptable.
- The created Site survives a backend restart against the same store and is
  present in the Sites index afterwards.
- The create path goes API handler to service to port to adapter, with no
  shortcut to storage. The write adapter lives under the sites `adapters/`
  package and is imported only by the single composition module. The T005
  adapter-isolation and storage-technology guards pass unchanged with the write
  adapter present.
- `tools/check-architecture.ps1` gains checks that the user store root has one
  owned configuration point and that `.gitignore` covers it.
- A fake in-memory `SiteRepository`, including `create_site`, satisfies the
  service layer with no import from `adapters/`.
- The simulator receives no repository handle and imports nothing from the sites
  package.

### Gating and routes

- The create flow and its create API are Simulator Lab surfaces. They are served
  only when `simulator_lab.enabled` is true, are addressed under the Simulator
  Lab path prefix so the existing URL chokepoint covers them, and are absent
  from the served route inventory when the flag is false. The `$gatedModules`
  allowlist is not extended.
- The Sites index and the Sites list API are operator capabilities and are never
  gated. They are served identically in both flag states, and a Site created
  while the Lab was enabled is fully visible when it is disabled.
- No `PUT`, `PATCH`, or `DELETE` on a Site appears anywhere in the served route
  inventory, in either flag state.
- Operator navigation gains no item. The parameterless `Site details` and
  `Site configuration` operator navigation items and route frames from T002 are
  deliberately left in place in this slice and are removed by T007 and T008
  respectively, each by the slice that makes its identified replacement real. No
  slice leaves a parameterless Site destination standing once its identified
  route exists.
- The gated entry point from the Sites index into the Lab create flow routes
  through the existing T004 gated entry-point module. It is not a second
  chokepoint, it is not routed through the shared substrate, and it is not
  rendered at all when the flag is false.

### The shared presentation substrate

- Site presentation is introduced in `frontend/src/sites/`: the Site read-model
  types, the view model that turns a record into display, and the presentation
  components for the Sites index. No Site presentation component, Site
  view-model derivation, or Site read-model type is declared under
  `frontend/src/shell/**` or the Simulator Lab feature root.
- `frontend/src/sites/**` imports nothing from `shell/**`, the Lab feature root,
  or `config/featureFlags`, and no component there takes a `variant`, `mode`,
  `shell`, `isLab`, or equivalent discriminant prop.
- `tools/check-architecture.ps1` gains two frontend checks, with the existing
  test-directory exemption:
  - Single definition: Site presentation components, Site view-model derivation,
    and Site read-model types resolve in `frontend/src/sites/**` only.
  - Leaf direction: `frontend/src/sites/**` contains no import from `shell/**`,
    the Lab feature root, or `config/featureFlags`, and no shell, mode, or
    variant discriminant prop.
- Render equivalence, the substrate's primary guard, is deliberately not written
  in this slice. It requires a second consumer of the substrate and ships with
  the Lab's Site view at causal step 6. It is named here so it is not quietly
  dropped: the two structural checks above are backstops, not a substitute.
- The operator shell composes the substrate and adds nothing to the shared
  region. No extension slot is declared yet, because nothing fills one in this
  slice.

### What the Sites index shows

- The first-run empty state states that no Sites are configured, without
  fabricating a row, a count, or a placeholder. With the flag on it offers the
  single gated entry point into the Lab create flow. With the flag off it offers
  no action and does not name the Simulator Lab, because naming a surface this
  build does not serve teaches a capability that is not there.
- Each row is keyed by `site_id` and shows display name, site type, location,
  lifecycle status, source mode, and configuration origin with template
  provenance.
- Configuration origin, source mode, lifecycle status, integration readiness,
  and evidence availability render as independent facts. Source mode is
  `source.mode`; the `Simulated` badge is its rendering and is provenance, never
  status or health. No `created_in_lab`, `is_simulator_site`, or equivalent
  field exists in the model, the API, or the read model.
- Mode and lifecycle never share a column, a badge, or a label, and neither is
  derived from, defaulted from, or rendered as a proxy for the other or for
  configuration origin. A test renders two fixture Sites, one with origin `USER`
  and `source.mode = LIVE` and one with origin `SHIPPED` and
  `source.mode = SIMULATED`, and asserts both facts render correctly for each,
  so the M1 coincidence of `USER` with `SIMULATED` cannot have been implemented
  as a derivation.
- The index shows no fabricated operational content: no `Last Data` or other
  evidence-derived column, no zero values, no charts, no source health, no
  analytics, no Replay, and no Findings. An evidence-derived column arrives with
  the evidence that fills it.
- No value, timestamp, status, or label appears because a mockup shows it. Every
  rendered value traces to the record under test.
- No edit, Save, Publish, rename, delete, duplicate, approve, diff, history, or
  rollback control appears anywhere, enabled or disabled.
- The carried-forward "no digits inside `<main>`" assertions in
  `operatorRouteFrames.test.tsx` and `simulatorLabGate.test.tsx` are replaced
  with Site-specific and create-flow-specific assertions wherever truthful
  values now render. Replace, never loosen.

## Required Product And Domain Semantics

- Creation and editing are different capabilities. M1 ships creation. In-place
  Foundation editing, Save and Publish over an existing Foundation, rename,
  `site_id` change, delete, duplicate-into-existing-id, Foundation version bump
  in place, configuration diff, history, rollback, and approvals stay
  unavailable for the rest of M1. `site_id` is immutable after creation.
- M1 offers no user-facing way to remove a user-created Site. The port exposes
  no delete, no archive, and no tombstone, and no UI affordance or route removes
  a Site. Removal is a developer action on the store for the whole milestone.
- A Site the Lab produces is a normal Site: same identity space, same model,
  same repository, same store, same index, carrying simulated source mode as
  provenance. It is not Lab-owned, lives in no Lab-owned store, and is never
  published or promoted, because it was a product object from the instant it was
  created. The gate covers surfaces and execution, never objects or stores.
- Shipped Sites and user-created Sites share one globally unique `site_id`
  space. There is no overlay and no precedence, because an identity that
  resolves to different content depending on store state would silently fork
  Site history for every later run, envelope, evidence record, and analytic.
- Origin is not encoded into identity. User `site_id` values are not prefixed;
  origin is a field.
- Templates are instantiated by copy. A later template change never alters an
  already-created Site, because silent retroactive Foundation change is what the
  evidence-immutability posture exists to prevent.
- User-authored configuration is untrusted input and crosses the same strict
  parser as shipped configuration.
- The six provenance and status concepts are the ones in the Provenance And
  Status Concepts table in `.ai/FEATURE_MAP.md` Feature Area 1. There are two
  provenance concepts, not three. In M1 every `USER`-origin Site also has
  `source.mode = SIMULATED` because the Lab is the only creation path; they
  coincide by circumstance, not by definition, and must never be collapsed,
  mapped onto each other, or defaulted from each other.

## Protected Seams

- User-authored configuration input: unit/contract test.
  The fully materialized document is validated before any write; unknown keys
  and oversized documents are rejected; `site_id` is charset-constrained, cannot
  traverse, and cannot collide case-insensitively; free text is never identity
  or a path; writes are atomic and a failed write leaves the store
  byte-identical.
- Shipped versus user-authored configuration: CI guard.
  Shipped configuration stays read-only and outside the writable store;
  `site_id` is globally unique across both stores with no overlay; the shipped
  Site store ships empty and disjointness is proven with a fixture store;
  `template_id` is provenance and never Site identity; changing a template does
  not alter an already-created Site.
- Configuration persistence port: CI guard.
  The write adapter is imported only by the composition module; the port and
  service layers name no file, path, or serialization format; the create path
  never reaches storage directly; a fake in-memory repository satisfies the
  service layer.
- Shared Site presentation substrate: CI guard + contract test.
  One read model, one view model, one component set, in `frontend/src/sites/`.
  Guarded here by the single-definition and leaf-direction CI checks. Render
  equivalence is the primary guard and ships at causal step 6 with the Lab's
  Site view, because it needs a second consumer to compare against.
- Site identity: contract test.
  `site_id` is the only Site identity; `template_id` and display name are not,
  and neither is the shell that created the Site.
- Simulator feature gate: CI guard.
  The create flow and its API are Lab surfaces and are not served with the flag
  off; the Sites index and Sites API are operator capabilities and are never
  gated; the single URL chokepoint and its allowlist are unchanged.
- Read-only configuration UI: review-time + contract test.
  Authoring exists only as create-from-template; no update or delete route
  exists for a Site; no edit, Save, Publish, rename, duplicate, delete, or
  history affordance renders anywhere.
- Configuration-only Site states: CI guard.
  A newly created Site with no evidence shows no fabricated operational content
  and no evidence-derived column.
- YAML configuration authority: unit/contract test.
  One strict parser for both stores, with no lenient path for user documents.
- Vocabulary separation: CI/review check.
  Mode and lifecycle never share a column; provenance vocabulary is never used
  as status, health, or assessment vocabulary.
- Mockup fidelity versus product honesty: CI guard.
  No mockup literal renders as content; no enabled control lacks a backing
  capability; no navigation destination is added.
- Simulator/product boundary: CI guard.
  The simulator gets no repository handle and does not resolve configuration.
- Stack and module direction: CI guard.
  One-way dependency direction preserved across the new backend and frontend
  modules.

## Focused Tests And Checks

- Port contract tests: create refuses an existing `site_id` in the shipped
  store, in the user store, and as a case variant of either.
- Load test with a fixture store: the same `site_id` present in both stores
  fails loudly at startup rather than resolving to one of them.
- Clean-checkout test: the shipped Site store is empty and the Sites index
  renders its first-run empty state.
- Identity validation tests covering path separators, `.`, `..`,
  absolute-looking values, Windows reserved device names, empty and over-length
  values, and the accepted charset.
- Parser tests over a user-authored document fixture covering unknown keys and
  an oversized or over-cardinality document.
- Atomicity tests: a create that fails validation leaves the store
  byte-identical; a create that fails after the temp file is written leaves no
  partial or stray document.
- Provenance tests: mutating the template document after creation does not
  change the created Site; origin, `template_id`, and `template_version` are
  recorded and rendered as provenance.
- Independence test: fixture Sites with origin `USER` plus `LIVE`, and origin
  `SHIPPED` plus `SIMULATED`, both render origin and mode correctly and
  separately.
- Persistence test: the created Site is present after the backend restarts
  against the same store.
- API tests for create success, conflict, case-variant conflict, malformed id,
  and missing required field, asserting distinct specific reasons; and for the
  continued absence of `PUT`, `PATCH`, and `DELETE` on a Site in the served
  route inventory in both flag states.
- Route and API inventory tests in both flag states: the create flow and create
  API are absent with the flag off; the Sites index and Sites API are identical
  in both states.
- Contract test proving the fake in-memory `SiteRepository` still satisfies the
  service layer with no import from `adapters/`.
- UI tests for the first-run empty state in both flag states, the gated entry
  point placement, the create flow, the created row with its origin, template
  provenance, mode, and lifecycle, and the refusal messages.
- UI test asserting no row is a link and no per-Site route is registered.
- UI test asserting operator navigation gained no item.
- Run `tools/check-architecture.ps1`, including the T005 checks and the four new
  ones: user store root declared once, `.gitignore` coverage, substrate single
  definition, and substrate leaf direction.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Inherit the M1 Step 3 exclusions from `.ai/ACTIVE_CONTEXT.md`.
- Do not add free-form authoring of a Site from scratch, authoring or uploading
  a template in-product, editing a template, importing an arbitrary YAML
  document, bulk creation, or cloning an existing Site.
- Do not overlay stores, add precedence between them, or prefix user `site_id`
  values with an origin marker.
- Do not add a `created_in_lab`, `is_simulator_site`, or equivalent field, and
  do not derive configuration origin from source mode or the reverse.
- Do not add a Site Details or Site Configuration route, a per-Site destination,
  or a row link. Those are T007 and T008.
- Do not build extension-slot machinery in the substrate. Nothing fills a slot
  in this slice.
- Do not let the create path reach storage directly, even for one case. API
  handler to service to port to adapter, always.
- Do not give the simulator a repository handle, and do not gate the Sites index
  or the Sites API on `simulator_lab.enabled`.
- Do not apply canonical mockup layout to the Sites index or the create flow
  yet. Content before chrome: those are T010 and T011.

## User Review

User review is required. This is the first of the two checkpoints for this
feature, and it moved here because creation is where Site, template, instance,
identity, origin, and refusal language are all fixed at once, and because it is
the first slice that produces a Site at all.

What the user is being asked to settle:

- Creation semantics: that a user creates a Site by choosing a shipped template
  and supplying identity, that `site_id` is immutable afterwards, that nothing
  about the Site can be edited once it exists, and that nothing can remove it.
- Template-versus-Site language: how a template is presented so it never reads
  as a Site, where the templates surface and the create flow live, and how the
  copy-not-reference relationship is described.
- That a Site created in the Simulator Lab is a normal Site with simulated
  source mode as provenance, in the product store, never published or promoted,
  and fully visible when the Lab is switched off.
- Configuration origin, template provenance, source mode, and lifecycle as
  separate facts on the Sites index, and the badge and column vocabulary used
  for each.
- The first-run empty state copy in both gate states, including that a gate-off
  build with an empty index and no way to add a Site is the correct state.
- Refusal copy for a duplicate `site_id`, a case-variant duplicate, a malformed
  `site_id`, and a missing required identity field.

Settled before implementation and not open at this checkpoint: removal of a
user-created Site, which the user deferred on 2026-09-13; the shell placement of
the create flow; and the decision that M1 ships zero canonical Sites.
