# T011C - Site Tab Row Treatment

Status: planned
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
- A line under the row names the labelled aspects and states that they have no
  content in this build yet.
- That line is derived from the tab inventory, not written out. An aspect that
  becomes a destination leaves the sentence in the same change that moves it,
  so the sentence can never contradict the row.
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
- UI test asserting the line under the row names exactly the labelled tabs,
  derived from the inventory rather than from a written-out list.
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
