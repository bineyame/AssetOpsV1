# T009 - Shared Visual Vocabulary

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T009-shared-visual-vocabulary`

## Feature

Site Foundation And Configuration-Only Site, canonical screen fidelity stage 1.

## UI-Verifiable Screen Behavior

Every surface that already has real content looks like it belongs to one
product and to the canonical mockscreen family: the operator shell home, the
Sites index, Site Details, Foundation, the Simulator Lab shell, the Site
Templates catalog, and the template inspection view. They share a brand header,
a left rail rendered as a real component, breadcrumbs, one page-header pattern,
one badge and pill vocabulary, one table and panel pattern, and one set of type
and colour tokens strong enough for T010 through T013, including T011A, to
realise the mockscreen visual and information architecture without inventing
content.

Nothing else changes. No screen gains a value, a control, a column, a tab, or a
destination. No screen that lacks content is dressed. Every fact on every screen
still traces to a record, and every screen still says exactly what it does not
have.

Operator navigation is the same set of items T008 left. The Simulator Lab's
navigation still lists only destinations whose routes render truthful surfaces.
The two rails look consistent and remain separate.

## Why This Is Next

This is canonical screen fidelity stage 1, and it is first because it is the
only chrome-only stage. It is safe precisely because it adds nothing a user
could mistake for a capability.

It comes after T005 to T008 rather than before them because of the rule that
does the work in this feature: content before chrome. Building the shells of the
nine canonical screens and filling them later is the failure this project's
evidence posture exists to prevent, moved from data into layout. It produces a
screen that looks finished and is not, and it is exactly how mockup placeholder
values leak into a build that cannot source them.

Doing the vocabulary once, now, also means the four fidelity slices that follow
are each about one screen's information architecture rather than about
reinventing badges and tables three more times.

## Acceptance Criteria

- A shared UI primitives module provides the vocabulary: header, rail,
  breadcrumbs, page header, badge and pill, table, panel, and type and colour
  tokens. It is not the Site substrate. `frontend/src/sites/**` may depend on
  shared UI primitives, because the substrate is a leaf over the domain read
  model and shared UI primitives, but the primitives module declares no Site
  read model, no Site view-model derivation, and no Site presentation component.
  The substrate single-definition guard from T006 still passes.
- The primitives module imports no shell code, no simulator code, and no feature
  flag, so it cannot become a back door around the gate or the substrate rule.
- Both shells and the substrate use the same vocabulary. Two visual systems do
  not coexist, and no surface keeps a bespoke table, badge, or panel.
- Applied only to surfaces that already have real content. No surface is
  created, no surface without content is dressed, and no empty frame is added to
  balance a layout.
- The badge and pill vocabulary is defined once, but a badge renders only where
  a record supplies its value. Defining a badge for a concept does not cause it
  to appear.
- No content, control, column, tab, destination, or navigation item is added or
  removed. A test asserts operator navigation contains exactly the items T008
  left it with, and that the Simulator Lab rail lists only routes that render
  truthful surfaces. `Home`, `Library`, `Documentation`, `Settings`,
  `Scenarios`, `Devices`, `Ingestion`, and `Events` from the mockup rail are not
  added to either shell. The Lab rail vocabulary follows v6.9 lines 657, 845,
  and 2379; those mockup items are not evidence for operator navigation.
- The left rail becomes a real component, but the operator rail and the Lab rail
  stay separate item sets supplied by their own shells. Neither shell imports
  the other's rail contents, and no simulator URL literal appears outside the
  gated modules. The `$gatedModules` allowlist is not extended.
- No mockup literal appears as content anywhere. Dressing a screen does not
  introduce a value, timestamp, status, or label the record does not supply.
- Colour is never the only carrier of meaning, and text contrast meets the
  project's accessibility posture in both rails and every badge.
- Every acceptance criterion of T003 through T008 still holds unchanged in
  meaning. Where a test query must change because markup changed, the assertion
  it makes is preserved or strengthened, never loosened. The T003 and T004 gate,
  placement, and identical-navigation assertions are untouched in meaning.
- Typecheck and the production build stay green, and no new runtime dependency
  is added unless the review packet names it and the build vendors it.

## Required Product And Domain Semantics

- Mockscreen fidelity is an explicit delivery goal for these slices. The task
  should move the real screen as close to the canonical mockscreen's visual and
  information architecture as current backed content honestly allows.
  Differences from the mockscreen must be deliberate corrections for product
  truth, missing evidence, deferred capabilities, or protected seams, not timid
  styling omissions.
- Design references are authoritative about information architecture and never
  about capability inventory, status vocabulary, or navigation. A visual
  vocabulary borrowed from a mockup carries no claim about what the product can
  do.
- Chrome is honest only when it describes something real. A shared badge
  vocabulary is chrome; a badge that renders without a record behind it is a
  claim.
- The Simulator Lab's navigation is a developer workspace menu, not a second
  product information architecture, and nothing in it is evidence that the
  operator product should have a matching destination.

## Protected Seams

- Mockup fidelity versus product honesty: CI guard.
  A screen adopts canonical layout only for content the product can source; no
  mockup literal becomes content; no navigation destination appears without a
  truthful route behind it.
- Shared Site presentation substrate: CI guard.
  The primitives module does not become a second home for Site presentation, and
  the substrate stays a leaf that imports primitives and nothing else.
- Simulator feature gate: CI guard.
  The two rails stay separate, no simulator URL literal moves outside the gated
  modules, and both flag states render as before.
- Vocabulary separation: CI/review check.
  Badge and pill vocabulary keeps provenance, lifecycle, source health, and
  assessment terms visually and semantically distinct rather than collapsing
  them into one status pill.
- Stack and module direction: CI guard.
  Primitives are a leaf; shells and the substrate depend on them and not the
  reverse.

## Focused Tests And Checks

- UI test asserting operator navigation items are exactly those T008 left, in
  both flag states.
- UI test asserting the Simulator Lab rail lists only destinations whose routes
  render truthful surfaces, in the enabled state, and is absent in the disabled
  state.
- UI test asserting no new control, column, tab, or value appears on any dressed
  surface, and that each surface's existing no-evidence and unavailable states
  still render with the same meaning.
- UI test asserting no badge renders without a record value behind it.
- Accessibility checks on rails, badges, and tables: accessible names, contrast,
  and meaning not carried by colour alone.
- The full T003 to T008 suites pass, with any query changes reviewed
  individually to confirm the assertion was preserved or strengthened.
- Run `tools/check-architecture.ps1`, including the T005 persistence checks and
  the T006 substrate checks.
- Run `tools/check-agent-workflow.ps1`.
- Typecheck and production build stay green.

## Scope Limits

- Inherit the M1 Step 3 exclusions from `.ai/ACTIVE_CONTEXT.md`.
- Do not create a new surface, route, destination, or navigation item.
- Do not dress a surface that has no real content, and do not add an empty frame
  or placeholder panel to complete a layout.
- Do not add a column, tab, filter, badge value, or control. The per-screen
  information architecture is T010 through T013, including T011A.
- Do not add the Quick Actions panel, the Foundation naming change, the operator
  Site tab bar, or `+ New Site` styling work; those belong to the slices that
  own them.
- Do not change any product copy that a user-review checkpoint settled.

## User Review

User review is deliberately not required for this slice, and no fidelity slice
in this feature carries a checkpoint of its own. Fidelity adds no capability and
no product language, and the three-state affordance rule that governs it is
already enforced by the mockup-fidelity seam. The product language on these
screens was settled at the T006 and T008 checkpoints and is not reopened here.
