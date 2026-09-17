# T010 - Simulator Lab Template And Create Surfaces To Mockup Quality

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T010-lab-template-and-create-surfaces-to-mockup-quality`

## Feature

Site Foundation And Configuration-Only Site, canonical screen fidelity stages 2
and 3.

## UI-Verifiable Screen Behavior

With `simulator_lab.enabled` true, the Simulator Lab's two Site-authoring
surfaces look like the canonical mockups.

The Site Templates catalog renders as a canonical page: page title and
subtitle, a search field, a type filter, and a table whose columns come from the
template documents. Opening a template shows its Foundation content in the
canonical panel and table patterns, still stating plainly that a template is not
a Site.

The create flow renders as a canonical stepped flow reached from an
`+ Add site` entry point in the Lab. The user selects a template, supplies Site
identity, and reviews before creating. Refusal copy appears inline against the
field it concerns rather than as a page-level error.

The operator Sites index entry point from T006 continues to route through the
same gated entry-point module into the same flow. Two entry points, one flow,
one chokepoint.

With `simulator_lab.enabled` false none of this is served, exactly as before.

## Why This Is Next

These are the first two surfaces whose content became real, so under content
before chrome they are the first that can carry the shared vocabulary honestly.
They are also the surfaces the user will spend the most time in while
configuring a Site, and they are currently the plainest.

Stages 2 and 3 are combined into one slice because both are Simulator Lab
surfaces, both are dressed with the same vocabulary T009 introduced, both are
small, and they are reviewed as one flow: a user browses templates and then
creates from one. Splitting them would produce two review packets that each
change half of one user journey.

## Acceptance Criteria

- Both surfaces adopt the T009 vocabulary. No bespoke table, badge, panel, or
  header pattern is introduced, and no second visual system appears.
- Catalog: search and a type filter operate over the template records actually
  present. No filter offers a value no template has, and no filter promises a
  dimension the template document does not carry.
- Catalog columns are sourced from the template document. No column exists
  because the mockup shows it, and no column renders a value the document does
  not supply.
- The template inspection view keeps the "a template is not a Site" statement
  verbatim in meaning and gains no action. No Create, Instantiate, Use, Copy,
  edit, Save, Publish, upload, import, delete, or rename control appears,
  enabled or disabled.
- Create flow: `+ Add site` is the Lab entry point. The T006 operator Sites index
  entry point still routes through the existing T004 gated entry-point module to
  the same flow. No second chokepoint is created, and the flow is not routed
  through the shared substrate.
- The flow has only as many steps as there are real inputs. No step exists to
  match a mockup's step count, and no step is a review of nothing.
- Where the flow previews the Site being created, it composes the Site substrate
  from `frontend/src/sites/**` rather than defining Site presentation of its
  own. The substrate single-definition and leaf-direction guards pass with the
  Lab as a consumer, and the substrate still takes no `variant`, `mode`,
  `shell`, or `isLab` prop. The Lab imports the substrate; the substrate imports
  nothing from the Lab.
- Refusal copy from T006 is placed inline against the field it concerns. Its
  wording is unchanged in meaning from what the user accepted at the T006
  checkpoint; any wording change is a checkpoint-1 change and is out of scope
  here.
- No capability is added. No template authoring, upload, edit, delete, or clone;
  no bulk create; no create-without-a-template; no draft or save-for-later; no
  edit of an existing Site.
- Gate behaviour is unchanged: both surfaces and their APIs are absent with the
  flag off, the route and API inventory tests pass in both states, Lab paths
  stay under the Simulator Lab prefix, and the `$gatedModules` allowlist is not
  extended.
- No value, timestamp, status, or label appears because a mockup shows it. Every
  rendered value traces to the template document or to the input the user just
  supplied.
- No Single Line Diagram, empty diagram frame, or signal selector renders on
  either surface, including in the create review step.
- Operator navigation is unchanged, and the Lab rail gains no destination.
- Every acceptance criterion of T005, T006, and T009 still holds unchanged in
  meaning. Where a test query must change because markup changed, the assertion
  is preserved or strengthened, never loosened.

## Required Product And Domain Semantics

- Mockscreen fidelity is an explicit delivery goal for these slices. The task
  should move the real screen as close to the canonical mockscreen's visual and
  information architecture as current backed content honestly allows.
  Differences from the mockscreen must be deliberate corrections for product
  truth, missing evidence, deferred capabilities, or protected seams, not timid
  styling omissions.
- A template is not a Site, and dressing the catalog must not make one look like
  the other. Identity, badges, and column headers keep `template_id` and
  `template_version` visibly in their own space.
- Authoring a simulated Site is a Simulator Lab capability behind the gate. The
  Site it produces is a normal Site in the product store, never published or
  promoted.
- The gate covers surfaces and execution, never objects or stores. Making these
  surfaces canonical does not move that line.
- Refusal copy is product copy settled at a user-review checkpoint, not
  implementation detail. Restyling where it appears is in scope; changing what
  it says is not.

## Protected Seams

- Mockup fidelity versus product honesty: CI guard.
  Canonical layout only for content the product can source; no mockup literal as
  content; no enabled control without a backing capability; no step, column, or
  filter that exists only because the mockup shows it.
- Shipped versus user-authored configuration: CI guard.
  Templates stay visibly not Sites; the shipped catalog stays read-only; no
  authoring or upload path appears.
- Shared Site presentation substrate: CI guard + contract test.
  The Lab composes the substrate for any Site preview and defines no Site
  presentation of its own; the substrate stays a leaf with no shell, simulator,
  or feature-flag import and no variant discriminant. Render equivalence still
  ships at causal step 6, when the Lab's full Site view exists.
- Simulator feature gate: CI guard.
  Both surfaces remain gated; one chokepoint; the allowlist is unchanged; both
  flag states behave exactly as T005 and T006 established.
- User-authored configuration input: unit/contract test.
  Inline refusal placement does not weaken validation. The same strict parser,
  the same whole-document validation before write, and the same atomicity apply.
- Read-only configuration UI: review-time + contract test.
  No edit, Save, Publish, rename, duplicate, delete, or history affordance
  appears on either surface, and no update or delete route for a Site exists.
- Site identity: contract test.
  `template_id` never renders as, or resolves as, Site identity.
- Stack and module direction: CI guard.
  One-way dependency direction preserved.

## Focused Tests And Checks

- UI tests for the catalog page: search and filter behaviour over the records
  present, column sourcing, and the absence of any filter value no template has.
- UI test asserting the template inspection view still states that a template is
  not a Site and still offers no action.
- UI tests for the create flow: template selection, identity input, review, and
  successful creation, all in the enabled state.
- Focused frontend-client/backend-response integration test covering the real
  Site Foundation frontend API clients against representative backend responses
  for Site list, Site detail, create success, validation failure, empty state,
  and not-found/error envelopes. This test binds the shared fetch seam before
  more fidelity work accumulates on it. If it proves too large for this slice,
  split it into `T010A - Site Foundation Fetch Seam Integration Test` before
  T010 and do not defer it past T011.
- UI tests for the refusal cases from T006, asserting each message is unchanged
  in meaning and now renders against the field it concerns.
- UI test asserting the flow's step count equals the number of real input
  stages, with no empty or decorative step.
- UI test asserting both entry points, the Lab `+ Add site` and the operator
  Sites index action, reach the same flow through the same gated module.
- Route and API inventory tests in both flag states, unchanged in strength.
- UI test asserting no diagram container, no diagram heading, and no signal
  selector renders on either surface.
- Substrate guard runs proving the Lab consumes and does not fork Site
  presentation.
- Accessibility checks on the stepped flow: step state, field labels, and error
  association.
- Run `tools/check-architecture.ps1`, including the T005 persistence checks and
  the T006 substrate checks.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Inherit the M1 Step 3 exclusions from `.ai/ACTIVE_CONTEXT.md`.
- Do not add template authoring, upload, editing, deletion, cloning, or import
  of an arbitrary YAML document.
- Do not add bulk creation, creation without a template, cloning an existing
  Site, or a draft or save-for-later state.
- Do not add editing, Save, Publish, rename, duplicate, delete, approvals,
  configuration diff, history, or rollback anywhere, and do not add disabled
  placeholders for them.
- Do not change refusal wording, empty-state wording, or any other copy that the
  T006 checkpoint settled.
- Do not un-gate either surface or its API.
- Do not define Site presentation outside `frontend/src/sites/**`, and do not
  give a substrate component a shell, mode, or variant discriminant.
- Do not dress the operator Sites index, Site Details, or Site Configuration
  here. Those are T011, T012, and T013.

## User Review

User review is deliberately not required for this slice. It adds no capability
and no product language: the template-versus-Site language, the creation
semantics, and the refusal copy were all settled at the T006 checkpoint, and
this slice only changes where and how they are presented. The three-state
affordance rule that governs the presentation is already enforced by the
mockup-fidelity seam.
