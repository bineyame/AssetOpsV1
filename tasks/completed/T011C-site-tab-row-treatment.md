# T011C - Site Tab Row Treatment

Status: complete
USER_REVIEW_REQUIRED: false

Intended branch: `task/T011C-site-tab-row-treatment`

Origin: this task did not come from the Planner. It is a user-review finding on
T011A, raised during the browser pass, with the treatment settled by the user in
the same session. The finding and the choice are recorded in T011A's
`## User Review Outcome`.

## Feature

Site Foundation And Configuration-Only Site, canonical Site tab row.

## Read For This Task

- `tasks/completed/T011A-foundation-naming-and-operator-site-tab-inventory.md`,
  its `## User Review Outcome`.
- `.ai/FEATURE_MAP.md`, `### Not rendered, labelled, or disabled: three states,
  not two`, and `#### Operator Site tabs`.
- `.ai/CODE_STATE.md`, the T011A entry.
- `frontend/src/shell/operatorSiteTabs.tsx` and the `.site-tabs` rules in
  `frontend/src/ui/primitives.css`.

## The Finding

T011A shipped the eight-tab operator Site row with two states: two destinations
rendered as links, six aspects labelled in place. The user opened it and read
the six as disabled.

They are not disabled. They carry no `disabled`, no `aria-disabled`, no `title`,
no route and no control role, which a guard clause and eleven assertions hold.
The defect is entirely in the treatment, and it is worse than the labels being
too quiet:

| Element | Colour |
| --- | --- |
| Current tab | `--accent` `#1d4ed8`, accent underline |
| Destination tab, e.g. Foundation | `--text-secondary` `#55617a` |
| Labelled-in-place tab | `--text-muted` `#6b7690` |

A working destination differs from a dead label by about five percent
lightness. The row does not say "two open, six not built"; it says "one active,
seven greyed out". Every other link in the product uses `--accent`;
`.site-tabs__link` overrode that to grey, which is what erased the distinction.

## UI-Verifiable Screen Behavior

The operator Site tab row distinguishes what can be opened from what cannot, by
two independent signals rather than one.

Destination tabs render in the product's link colour, like every other link.
Labelled-in-place tabs stay muted and unemphasised. A divider separates the two
groups, and a line under the row names the aspects that have no content yet, so
the distinction survives greyscale, a colour-vision difference, and a reader who
does not know the convention.

## Acceptance Criteria

- Destination tabs render in the shared link colour. The current destination
  remains distinguishable from the other destination by more than colour.
- Labelled-in-place tabs remain muted and carry no link, button, route,
  `disabled`, `aria-disabled`, `title`, `tabindex`, or control role. The three
  states stay three: this slice changes how a label looks, never what it is.
- A visible divider separates the destination group from the labelled group.
- A line under the row states how many aspects have no content in this build
  yet. It counts rather than names them: the row one line above already names
  them, and repeating six names under a row that just showed six names is
  heavier than the row it explains. Settled by the user after seeing the first
  version rendered.
- The line makes a claim about the build, not about the site on screen. No
  aspect is missing content because of anything about that site.
- The count is derived from the tab inventory, not written out. An aspect that
  becomes a destination changes the count in the same change that moves it, so
  the line can never contradict the row.
- The line renders nothing when no tab is labelled in place.
- The row still renders exactly the eight v6.9 labels, in order, in both gate
  states, on both Site surfaces.
- No promise vocabulary. Not `coming soon`, not `not yet available`, not
  `unavailable`, not `locked`. The line states what this build contains, never
  what a later one will.
- No change to the tab inventory, its two kinds, the routes behind the
  destinations, or any other surface.

## Protected Seams

- Mockup fidelity versus product honesty: CI guard.
  A labelled-in-place tab must not acquire a disabled affordance. The existing
  guard clause and its five patterns still hold.
- Operator Site tab inventory: CI guard.
  One definition, in the operator shell, carrying no Lab run vocabulary.

## Focused Tests And Checks

- UI test asserting destination tabs and labelled tabs are distinguishable by
  something a test can see: the labelled ones are not links, and the
  destinations are.
- UI test asserting the line counts exactly the labelled tabs, derived from the
  inventory rather than from a number someone typed, and that the row above
  still names them.
- UI test asserting the line names no site and says nothing about `this Site`.
- UI test proving the line disappears when the inventory has no labelled tab,
  and reads grammatically when it has one.
- UI test asserting no promise vocabulary anywhere in the row or its line.
- The existing T011A tab assertions stay green unchanged.
- Run `tools/check-architecture.ps1` and `tools/check-agent-workflow.ps1`.
- Existing suites, typecheck and production build stay green.
- Browser verification, together with T011B's, that the six no longer read as
  disabled.

## Scope Limits

- Do not change which tabs exist, their order, or their kind.
- Do not make a labelled tab clickable, focusable, or disabled.
- Do not add a tooltip, popover, icon, or badge to any tab.
- Do not touch the Sites index, Site Details content, Foundation content, or
  the rails.
- Do not introduce breakpoints; T011B's containment work is separate and this
  slice adds no responsive behaviour.

## User Review

Not required. The user settled the treatment before the work started, and this
slice implements that choice. The browser pass that confirms it is the same one
already outstanding for T011A and T011B.

## Review Outcome

Independent review by Codex: **reject until the documentation finding is
corrected**, then corrected and accepted. One Low finding, and no code finding
at all: "I did not find a product/code behavior defect in the tab treatment."

### The finding

Two durable records still described the pre-revision state. `.ai/CODE_STATE.md`
listed "Not seen" as this slice's first open item, and T011A's User Review
Outcome said the line *names* the aspects. Both were true before the user's
browser pass and false after it: the user did see this row, and the settled line
counts rather than names.

Low severity understates why it mattered, and the Reviewer said so: T012 is
explicitly told to read `.ai/CODE_STATE.md`, so the stale record would have told
the next agent that this row's browser result was unknown and that the settled
treatment lists six names. A handoff document lying to the slice it hands off
to.

Fixed in the commit `T011C: correct two records that still described the
pre-revision line`. The error was mine in a repeatable way: I revised the
sentence and updated the prose beside it, then left the open-items list and the
T011A outcome describing what had been replaced. A revision sweeps every record
of what was revised. The open-items list read 1, 2, 4, 5, 6, which was the tell.

### What the Reviewer verified rather than accepted

- The three states are still three: Overview and Foundation remain links, and
  the six remain spans with no route, control or disabled affordance. That was
  the seam this slice could have undone while making a label legible.
- `labelledAspectsSentence` is genuinely derived, with tests exercising
  fabricated inventories of two labelled aspects, one, all destinations, and
  the real one.
- The active tab stays distinguishable by underline and weight while the
  destinations inherit the global link colour.
- The moved baseline is correct: the active underline still lands on the list
  border now that the sentence lives inside the same nav.
- The sentence inside the `Site sections` nav explains the row rather than the
  Site record, so it belongs there. Known Deviation (c) accepted, with the
  screen-reader discoverability risk named as correctly stated.

### User review

The treatment itself was settled by the user before the work started, and
confirmed by them at the browser afterwards: they rendered the first version,
reported the row reads right and the sentence is heavy, and the sentence was
shortened from naming all six to counting them. That exchange is recorded in
T011A's User Review Outcome, which is where the original finding lives.

### Checks

Reviewer: architecture guard, workflow guard, backend `304 passed`,
`npx.cmd tsc --noEmit` clean. The frontend suite and build failed under its
sandbox for the known esbuild reason.

Implementing session: both guards pass, backend `304 passed`, frontend
`464 passed` across 17 files at the time of the merge, `tsc --noEmit` clean,
build clean.
