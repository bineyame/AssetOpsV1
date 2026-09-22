# Milestone Review Backlog

Things deliberately carried rather than fixed, under
`D-2026-09-22-milestone-speed-over-purity`. The complete review happens once
the simulator milestone is complete and the thing has been tested properly,
and this list is what that review reads first.

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

*Safe to carry* because they were reviewed, judged Low, and none makes a false
claim. T020 reads the same store and should read N3-N6 before it does.

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

## Tracked elsewhere, listed so the review finds them

- **Four open M1C questions** - `.ai/FEATURE_MAP.md`, *Open Questions Before
  Task Breakdown*, and `Docs/simulator-scenario-authoring-and-runtime.md`
  under Open Questions. None blocks a planned slice.
- **Option C**, the model profile declaring that it needs a Foundation value.
  Accepted and scheduled by trigger rather than by position; see
  `D-2026-09-22-foundation-value-declaration`.
- **The observation transform as a component rather than a step** - the one
  seam of the three that is still open, in `.ai/FEATURE_MAP.md` under *Seams
  this sequence surfaced*. Lands in T022.
