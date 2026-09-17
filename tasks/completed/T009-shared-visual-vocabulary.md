# T009 - Shared Visual Vocabulary

Status: complete
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

## Review Outcome

Reviewer verdict: accept after one medium finding was fixed on the branch. No
other findings, no blocking open questions. The review was independent: Codex
reviewed work Claude authored, per the role separation in
`.ai/PROJECT_RULES.md`.

Finding: the Site substrate's edge states kept bespoke page headers. The loaded
states of Site Details and Site Configuration rendered through `PageHeader`,
but their loading, not-found and unavailable states still rendered a raw `<h1>`
- six across the two files. Two of those states had already adopted `Panel`, so
the same surface was half on the shared vocabulary and half bespoke, in exactly
the module this slice exists to keep from drifting. That is an acceptance gap
against the criterion that says two visual systems do not coexist, not a
preference.

Fixed on the branch in `6edbbf1`. All six render through `PageHeader` with the
same heading text and the same `headingId`, so every `aria-labelledby` on the
surrounding landmark still resolves, and no raw `<h1>` remains in
`frontend/src/sites/` or `frontend/src/shell/`. The reviewer offered the option
of exempting the loading states as "not real content" and recording that as a
deviation; they were not exempted, because a loading state is a user-visible
state of a dressed surface that renders the same page heading, and exempting it
would have left standing the exception the finding is about.

Judgement calls the reviewer examined and did not find fault with: the Lab rail
adds no route, surface, destination or capability and renders none of the eight
mockup-only items; the changed inherited assertions are the expected set and
preserve or strengthen their prior meaning, with no fifth assertion quietly
changed; no rendered field, order, label, absence reason, column or tab
changed; no badge renders around an absence; and `d5919cb` is the right review
base, because `main...HEAD` would include unrelated planning lineage and
misstate the slice.

The reviewer also judged the new guard's shared-vocabulary clause intentionally
coarse - a consumer can import one primitive while hand-rolling another pattern
- and recorded that as a named limitation rather than a finding, which matches
the packet's own Residual Risk 3.

Reviewer checks: architecture guard passed, agent workflow guard passed,
backend 296 passed, frontend typecheck passed, `git diff --check d5919cb...HEAD`
clean. The reviewer could **not** run the frontend suite or the production
build: Vite failed while loading its config in that environment with
`Cannot read directory "../../..": Access is denied`. The 352 frontend tests
and the clean build are therefore the Implementer's numbers and were not
independently confirmed. Recorded rather than glossed.

Checks re-run in the implementing session after the fix: architecture guard
passed, agent workflow guard passed, backend `pytest -q` 296 passed, frontend
`vitest run` 352 passed across 14 files, `tsc --noEmit` clean,
`npm run build` clean.

Frontend flakiness under CPU contention was characterised during closeout and
is broader than the single case T007 and T008 recorded. Runs made while a heavy
background process and two dev servers competed for the machine produced two or
three failures per run, in different files each time, every one of them
`Test timed out in 5000ms` rather than an assertion failure, and each passing
when its file was run alone. With the machine quiet the suite passed five
consecutive times, three before the fix and two after. A single red run on a
loaded machine should be re-run before it is believed.

Not verified, and not claimed: nobody has rendered this in a browser, and it is
a visual slice. Browser tooling was unavailable in the implementing session.

User review is not required for this slice, as the User Review section above
states, and no fidelity slice in this feature carries a checkpoint of its own.

The full review packet is at `.agent/T009-review-packet.md`, the reviewer's
findings at `.agent/T009-review-findings.md`, and the branch diff at
`.agent/T009-review.diff`, taken against `d5919cb`. All three are local-only.
