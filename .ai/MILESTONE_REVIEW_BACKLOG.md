# Milestone Review Backlog

Things deliberately carried rather than fixed, under
`D-2026-09-22-milestone-speed-over-purity`. The complete review happens once
the simulator milestone is complete and the thing has been tested properly,
and this list is what that review reads first.

With the 2026-09-24 milestone renaming, the former M1 configure/simulate/inspect
evidence finish line maps to the internal architecture demo (feature-map B).
The review backstop stays there after proper testing; it is not postponed to
the full client portfolio milestone.

**This list is what makes the deferral honest.** A thing carried without being
written here is dropped. Anyone - Architect, Planner, Implementer, Reviewer -
adds an entry rather than stopping a slice, and the entry says *what it is*,
*why it was safe to carry*, and *what would change the answer*.

**Do not put here:** a defect expensive to reverse later, a claim that would
mislead an Implementer, or a decision only the user can take. Those three are
still stopped for.

Expiry: delete when the milestone review has closed it out.

## Carried

### `supported_states` has no falsifier until T021

`MINIMAL_FUEL_TANK_MODEL` declares that `fuel-tank-volume` supports
`CAUSAL_INPUT` and `REPORTED_OBSERVATION`. Nothing in this build can cause or
report anything, so the declaration is a promise about a kernel that does not
exist, and `READY` is computed from it.

*Safe to carry* because it discloses exactly that: T020's `READY` disclosure
names the condition, and T021's conformance test deriving `supported_states`
from the kernel is the falsifier that makes the declaration legitimate.

*What would change the answer:* descoping that conformance test. It is not a
quality measure. Without it `supported_states` goes back to being a promise
and `READY` goes back to overreaching.

### The refusal/blocking naming rule's scope

`.ai/ARCHITECTURE.md`'s Refusal And Blocking Vocabularies rule is scoped to
the two vocabularies in `backend/assetops_backend/runs/refusals.py`. Its
review question - *from the name alone, which side is it on; if answering
needs the docstring, the name is wrong* - has now failed on two vocabularies
it does not govern: the requirement-conflict refusal at the scenario-parse
layer, and `CADENCE_RESOLUTIONS`.

*Safe to carry* because the second is being deleted in T020 and the first is
correctly shaped as an ordinary `ScenarioConfigurationInvalid`. Neither is
false today.

*What would change the answer:* a third vocabulary where the test fails and
the name is load-bearing on a screen or a wire.

### T018's two open Low findings

The unmeasured second initialization layer, and two forward constraints that
live only in code comments. Both recorded in place in `.ai/CODE_STATE.md`;
the other two of the four were closed by T019.

*Safe to carry* because neither is a false statement; both are things a later
slice would want to have measured or lifted out of comments.

### T019's re-review residual risk

N3-N6 in `.agent/T019-review-packet.md`, and the four small things
`.ai/CODE_STATE.md` logs as "logged and left": the frozen-table layout claim
whose wording outruns its floor, the reason-set audit deriving membership from
a name-suffix scan with a hand-written count where the durable fix is
exporting a vocabulary `frozenset`, a dead duplicate docstring in the
execution contract tests, and the remaining item in the packet.

The floor now has numbers, measured by T020's review.
`tools/layout-evidence.mjs:1029` asserts `frozen.rowCount >= 20` under a claim
worded *the frozen input table renders a row for every frozen value*, and the
two pages it runs against have **29** and **46** rows - so the floor could
lose a third of one page and nine tenths of the other and still pass a claim
that says "every". `:1046` is the same shape: `blocked.rowCount > 0` under
*the blocked table names every reason the draft carries*, where the true
number is three.

*Safe to carry* because they were reviewed, judged Low, and none makes a false
claim - a floor that is too low reports a true thing weakly rather than a
false thing. T020 reads the same store and reused the same `>= 20` floor, so
the fix is one place with two callers.

*What would change the answer:* a page losing rows silently. The claim would
still pass, and its wording says it would not.

### The answerer vocabulary's inherited shape

`FROZEN_INPUT_ANSWERERS` was inherited from T018's `INITIALIZATION_OWNERS` and
widened to a broader question - who answers for the interval, the seed, the
cadence - without gaining a member, which is how `MODEL_PROFILE` became
cadence's label. T020 adds `PUBLICATION_PROFILE` and corrects the rows, but
the two vocabularies stay coupled by a mapping and a subset assertion rather
than being two vocabularies that happen to overlap.

*Safe to carry* because after T020 every row names the profile that answered
it, which is the part that reaches a screen.

### The gate suite's vacuity shape survives in two more places

T020 fixed one instance: the gate suite rendered the run surfaces with no run
client, so a claim about what they may offer iterated an empty control list.
The same shape is still there twice. `renderAt` injects
`EMPTY_SITE_DIRECTORY`, so the Sites screen a gate claim walks has no rows and
few controls, and the injected `RUN_SETUP` answers `listProfiles` with
`unavailable`, so the run SETUP screen a gate claim walks renders a degraded
panel rather than a form.

*Safe to carry* because every load-bearing claim in that suite is an absence
when the gate is closed, and an absence asserted over a thin screen is still
an absence. The claim that had to bite - what an enabled run surface may
offer - is the one T020 made non-vacuous.

*What would change the answer:* a gate claim that asserts something is
**present or enabled** on either of those two screens. Against an empty list
or a degraded panel that claim would either fail loudly or pass for the wrong
reason, and the injection has to become real first.

### The inventory's bare `READY` cell

`READY` appears in a table cell on the Runs inventory with no disclosure
beside it and no room for one. The panel that says what the status does not
assert exists only on the run detail. Both the T020 packet's
presentation-honesty assessment and its independent review name this as the
thinnest point of the slice.

*Safe to carry* because the inventory's explanation panel says what ready and
blocked describe before the table, the detail is one click away and states it
in full, and T021's conformance test makes the word correct rather than
qualified.

*What would change the answer:* the inventory gaining a second signal that
reads as readiness - a colour, an icon, a sort that puts `READY` first - or
T021 slipping far enough that the qualified word is read for a long time
without its qualification.

### The answerer-contradiction property covers one cadence branch

`test_no_row_names_an_answerer_its_own_detail_contradicts` is the guard that
makes the `PUBLICATION_PROFILE` relabel a shape rather than a count. It
exercises the branch where a cadence resolves. The not-resolved branch - a
device signal whose profile declares no cadence - is correct by reading, but
no run in that state is passed through the property.

*Safe to carry* because the not-resolved branch blocks the run, and a blocked
run's cadence row is covered by the blocking-reason assertions instead.

*What would change the answer:* any change that lets an unresolved cadence
reach a `READY` run, or a second answerer becoming able to answer a cadence.

### Packet commit counts are stale two slices running

`.agent/T020-review-packet.md` said seven commits when there were eight, and
the T019 packet carried the same kind of error. The count is written before
the last commits land and is never re-read.

*Safe to carry* because it is a number in a document nothing computes from,
and every packet names its branch, which is authoritative.

*What would change the answer:* nothing. Delete this entry at the milestone
review; it is here so the pattern is visible rather than because it needs a
fix.

### The layout tool's action claims cannot see an enabled anchor

`tools/layout-evidence.mjs:245` collects `document.querySelectorAll("main
button")`, so every action claim built on it - `:947` *the inventory offers no
button of any kind*, `:1084` *a blocked draft offers no run action at all*,
`:1089` *the one action on a ready draft is rendered and disabled* - is
satisfied by an enabled `<a className="action">`. That is an established idiom
in this codebase, not a hypothetical: the Lab uses anchors as actions
elsewhere, and T020's F1 finding was exactly that element.

*Safe to carry* because the jsdom suites now close the link set on every run
surface and they run in CI, where this tool does not. The tool measures
layout; the affordance claims on it are a second opinion.

*What would change the answer:* the tool becoming the primary affordance
guard, or a surface whose links the jsdom suites do not close.

### ~~The evidence run's submit race~~ - RESOLVED in T020A, 2026-09-24

`SUBMIT_RUN_SETUP` clicked the submit button without checking whether it is
disabled, and that button is disabled until the configured Site resolves. The
action returned `true` either way, so the run waited for a summary that was
never requested. Recorded during T020's review after three reproductions.

**Fixed.** The action now returns `not-ready` for a disabled submit and the
caller waits for the page rather than clicking through it. T020A hit the same
symptom, mis-attributed it to the run store's create cost, and a second
independent review isolated the real cause on the mounted component: with the
Site promise held pending the old action returned `true` with zero create
calls; resolving the promise enabled the button and produced exactly one.

Kept here rather than deleted because the entry is the record that the
deferral was honest - and because the carry note was right for the wrong
reason. It said this fails honestly and never yields a false PASS, which held;
what it did not anticipate is that an abort with no false PASS can still
produce a false EXPLANATION, which is what T020A's first packet published.

## Tracked elsewhere, listed so the review finds them

2026-09-24 routing correction: the old three-question count, Block F deadline
and feature-area-5 pointer were superseded by the source-based replan.
The carried review findings above are unchanged.

- `.ai/FEATURE_MAP.md`, Decisions At Their Point Of Use, carries unresolved
  Fuel Loss corrections, fuel expectation/uncertainty and injection/reset
  behavior alongside the roadmap's financial, productive-load and lifecycle
  choices. Do not infer implementation blockers from the old question count.
- Option C (the model declaring its Foundation need) remains triggered by its
  first consuming law: `D-2026-09-22-foundation-value-declaration`.
- The separate observation transform is owned by the recreated T022 starter
  work; see `.ai/PLANNING_HANDOFF_T020A_T023.md` and architecture's Execution
  Composition And Truth Barrier.
- The unassigned delivery requirements are in the feature map's Next Work And
  Unowned Requirements table. They are planned capability, not review debt.
