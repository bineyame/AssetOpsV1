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

### ~~`supported_states` has no falsifier until T021~~ - RESOLVED in T021, 2026-09-27

`MINIMAL_FUEL_TANK_MODEL` declares that `fuel-tank-volume` supports
`CAUSAL_INPUT` and `REPORTED_OBSERVATION`. Nothing in this build could cause or
report anything, so the declaration was a promise about a kernel that did not
exist, and `READY` was computed from it.

**Closed.** `ModelSpec.advertised_supported_states` in the simulator DERIVES the
advertised set by grouping a table of executable handlers - there is no field in
which to write a role no handler implements - and
`host/tests/test_kernel_conformance.py` compares that set against this profile's
declaration in both directions AND asserts every advertised `(state, role)` pair
was reached by executing a Draft created through `RunSetupService` from the shipped
document. Two probes keep it from being two agreeing tables: one removes a handler
and watches the derived set narrow, one adds a handler nothing calls and watches
the execution ledger report it missing.

Kept rather than deleted because the carry note's own warning was the right one
and is worth reading beside what closed it. It said the conformance test "is not a
quality measure", and the thing that made it a falsifier rather than a second
declaration is precisely the leg that could have been left out: DERIVING the set
from handlers, and requiring each one to have RUN. A conformance test comparing
two hand-written tables would have satisfied the sentence and established nothing.

`REPORTED_OBSERVATION` is verified at the model's grain - the world can answer what
a stock is at an instant, after that instant's events - and no further. Nothing
publishes that answer, which is the other entry below.

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

*Narrowed, not closed, by T021.* The model profile's half of the disclosure is
retired because a kernel now derives its supported set; the publication profile's
half stays, so a `READY` cell with no disclosure beside it still hides one
unverified declaration rather than two.

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

## Inline `float(value)` overflow, five open sites

Transferred from the T020A third-pass review, 2026-09-25, which named the
inventory rather than expanding the Implementer's assignment. Seven sites are
known, two were closed in T020A, five remain. This is a minimum established
count from reproduced cases, **not a certified audit** of every numeric
operation - do not read it as one, and do not infer that any unlisted numeric
path is safe.

Each is the inspectable-error half: an unrepresentable integer raises a raw
`OverflowError` where that surface already has a designed refusal. None
persists an invalid value, which is why the review carried them rather than
blocking the merge under `D-2026-09-22-milestone-speed-over-purity`.

| Site | Surface | Current failure | Closure evidence required |
| --- | --- | --- | --- |
| `runs/parsing.py:517` `_quantity` **first priority** | T019, an HTTP run-setup request body | 500 instead of the designed `REQUEST_INVALID`/422 | HTTP test asserting the refusal, no persisted run, and a finite large-number control |
| `runs/parsing.py:740` `_real` | T019, a stored run document read back | escapes run-document refusal | actual run-document read with the domain error and a valid-number control |
| `runs/parsing.py:966` `_parse_parameter` | T019, a stored resolved parameter; does **not** route through `_real` | throws during record construction | full stored-document read refusing this exact field, plus its finite control |
| `sites/parsing.py:269` | T005, a template component `rating` | escapes template refusal | template parser domain error with component position and a valid control |
| `sites/site_parsing.py:549` | T008, a Site component `rating` | escapes Site refusal | Site parser domain error with component position and a valid control |

`_quantity` is first because it is the only one reachable without authoring a
document, so it is a live product defect on an existing request path.

These are error-boundary corrections. They are explicitly **not** a request
for a generic numerical-validation framework, and the reviewer said so.

The generalisation worth keeping: this codebase validates numbers with
`float(value)` written inline, and every place it does carries this hole. A
check moved in front of such a conversion carries the hole with it rather than
closing it - that is how T020A relocated one before closing it.

## Carried out of T020A1

Carried under `D-2026-09-22-milestone-speed-over-purity` on 2026-09-26, after
the backup Reviewer recommended merge with all fourteen criteria met. None
meets the stopping rule: none is expensive to reverse, none misleads an
Implementer about what the code does, none needs a user decision.

**~~F5 - one diagnosis is inverted, and two functions order the same two facts
oppositely~~ - RESOLVED in T020B, 2026-09-26.** An unqualified reference to a
state the profile models site-wide got the no-binding refusal, because the
address obligation ran first and `binding` is `None` whenever the scopes
disagree. The statement told the author to add an address or a binding; the
actual repair is to write `site:` before the key, which it never said.
`_resolve_foundation_value`'s own docstring forbade that ordering - "Scope before
binding, because a scope disagreement explains a missing binding rather than the
other way round" - so one function contradicted the other's stated rule.
Related: because the two passes ran independently, an executable REQUIRED
declaration failing both yielded two blocking reasons with the same subject.

**Fixed in three parts, and the third is why it should not recur.** The scope
check runs first in `resolve_state_addresses` too. `scope_repair` computes the
one string an author types and `scope_disagreement_statement` is the single
wording all three sites share - the message had been duplicated three times with
its own hedges in each, which is how two of them drifted. And all three now ask
one `state_authority` record instead of each doing its own profile lookup, so an
ordering mistake is one mistake rather than a disagreement between functions that
never read each other. `_decide` skips the support question for an address the
resolution pass refused, closing the two-rows-one-subject half.

Kept rather than deleted because the diagnosis is the record: **the defect was
not a missing check, it was two checks that could not see each other**, each
individually correct about the facts it held. Deduplicating the wording without
deduplicating the lookup would have hidden the next instance rather than
preventing it. `.agent/T020B-guard-probes.py` re-runs both halves as violations
and asserts the tests fail.

**F6 - the packet's stated reason for re-measuring the layout is false.** It
says the ambiguity statement's wording changed again so nothing was inherited.
It did not change: `afbd1da..ba35778` only reflows that message across
different line breaks, and the reported 430 chars / 425x137 / 153x371 are
identical to round three's. The Drafts were genuinely regenerated and
re-measured and both run ids exist with the claimed shape, so the substance is
sound and only the justification is wrong. That section also layers round four
onto round three with a duplicated sentence and a trailing "They were measured
after round two." Correct the section, do not re-measure.

**Three residuals for the T021 handoff, raised by the same pass:**

- `refuse_incompatible_execution` is an equality test on an integer, and
  version 4 has carried **three different intra-version semantics** on the
  T020A1 branch. Twenty of the local Drafts are at version 4 and the guard
  cannot tell them apart. Correct under
  `D-2026-09-22-contract-version-scope`, since 4 was unpublished outside that
  branch, and harmless while nothing executes. **T021 should regenerate rather
  than execute any Draft frozen before its own build.**
- A READY run's `initialization_inputs` can hold a row for a state this build
  does not model at that scope, with nothing on the row saying so - the
  disqualification lives in `unsupported_optional_inputs`. A documented
  carve-out rather than a hole, but **a kernel reading initialization inputs
  without cross-referencing will initialize from it.**
- The shipped Fuel Loss scenario's only upper bound is **inert**.
  `declared_bounds(fuel-loss-event)` returns `{'fuel-tank-volume@fuel-tank':
  (0.0, None)}` because `scenarios/execution.py` skips any parameter whose
  value is not a float, and a Foundation-owned parameter states no value by
  design under `D-2026-09-22-foundation-value-declaration`. Inherited, present
  at `b004f58`. The declaration survives addressed to the right tank; its value
  now lives on the frozen run. **T021 is the first consumer of bounds** and
  must take the capacity from the frozen initialization input, or teach
  `declared_bounds` to read frozen answers. Where a bound's number comes from
  is the kernel's design decision, which is why it was not settled here.

One thing this slice cost that is worth not repeating: five implementation
rounds and three review passes, two of which returned low-severity claim and
docstring corrections that this decision says to carry rather than fix. The
reviewers cited the decision; the coordinator forwarded every finding as work.
See `.ai/ROLE_CONFIG.md`, "Sort Findings Before Forwarding Them".

## Carried out of T020B's review rounds

Added 2026-09-27 at closeout, after two Codex passes, three Claude passes and
the owner's screen review. None meets `D-2026-09-22-milestone-speed-over-purity`'s
stopping rule.

- **Three rule statements carry literal `**` markers that render as plain
  asterisks.** `window-overlap`, `window-ramp` (two pairs) and
  `no-interval-signal-at-the-first-boundary`, all introduced during these
  rounds. `Fact` renders prose verbatim. They were on screen during the owner's
  review and were not objected to, which is not the same as being approved.
  One line of text whenever wanted.
- **The phrase blacklist can collide with a true statement.** Two forbidden
  phrases are legitimately true of a *point* rather than a window, so a
  reworded `point-applied-once` could be failed for saying something correct.
  No collision today.
- **The prose is not guarded as a class, and the record now says so.** Nine of
  the property class's ten tests read only its own transcription of the
  predicate and would pass if every published statement were false; one test is
  the phrase blacklist. Guarding the class would mean generating the statements
  from the predicate rather than writing them beside it. F-V1 is the evidence:
  it entered in the same commit that claimed to close the class, matched none of
  the five existing phrases because it was an antecedent rather than a
  consequent, and a human reader found it rather than a test.
- **Layout evidence is unmeasured since the round before last.**
  `ScenarioFrame.tsx:668` renders `dispatch_rules`, so every rule statement
  edited in the last three rounds is on-screen text that no measurement has
  covered. The harness stopped the dev servers for memory pressure and they
  were not restarted.

The pattern worth carrying forward, because it cost four rounds: **every failing
sentence restated a subset of what the predicate does.** F6 fixed the aligned
case, R1 the unaligned case, R1a the short-and-straddling case, R1b the
adjacent case, F-V1 the forcing rule's copy of the same shape. The formula was
correct throughout and ahead of its own description every time.

## Carried out of T020B

Carried under `D-2026-09-22-milestone-speed-over-purity` on 2026-09-26. Neither
is expensive to reverse, neither misleads an Implementer about what the code
does, neither needs a user decision.

### `supported_reporting_states` has no falsifier either

*Still open after T021, and now the only half of the disclosure that is.* The
kernel closed the model profile's half and the disclosure was narrowed to name
only this one, with the observation transform as its stated retirement condition.
The generalisation below - that the two halves retire on different conditions - is
what made narrowing rather than removing the right move, and it is now the record
of a prediction that held.

`LAB_PUBLICATION_PROFILE` declares it can model the fuel level reporting path
being unavailable, and nothing in this build can suppress a reading. It is the
same shape as the `supported_states` entry at the top of this file, one profile
along.

**This entry's original justification was false, and correcting it in place is
the point of keeping it.** It said the readiness disclosure "now covers two
declarations rather than one". It did not: `READY_DISCLOSURE` named only the
model profile and was not touched by T020B at all - `models.py` was not in the
slice's diff. The carry therefore rested on coverage that did not exist, and
T020B's independent review caught it. The disclosure now genuinely names both
profiles and both supported sets and says neither half alone retires it, which is
what makes the rest of this entry true.

*Safe to carry* now that the disclosure says so: a `READY` run states that this
declaration is unverified and names its own retirement condition. The falsifier
is the observation transform, the component that either suppresses a reading
across the declared window or does not.

*What would change the answer:* descoping that transform, or a second
reporting-path state arriving with no consumer.

*The generalisation worth keeping:* this was dangerous rather than untidy because
the two halves retire on **different conditions** - the model profile's with a
kernel, the reporting path's with the transform. A disclosure naming only the
first would have been retired by the kernel slice while the second claim stood.
A coverage claim that names fewer conditions than it covers is not a wording
slip; it is a false statement with a date on it.

### The window ramp is silent on a window that declares two values

Raised by T020B's independent review, and it is about the shipped document rather
than a hypothetical. `window-ramp` in `scenarios/execution.py` settles two cases:
a declared quantity ramps from nothing to all of it, and a single declared level
holds for the window. `baseline-load-profile` is a third. It is `INTERVAL_WIDE`
and declares **two** parameters for one address and one role -
`evening-peak-load` at 72 kW and `overnight-base-load` at 18 kW, both
`site:site-load-demand` as a `FORCING_INPUT`. Nothing says which value sits at
which endpoint, or whether two parameters compose as endpoints at all. Read
literally the rule interpolates 72 kW down to 18 kW across the whole interval,
which is not the "ordinary weekday shape" the entry's own description means.

*Safe to carry* because nothing consumes the text yet: `site-load-demand` is
`OPTIONAL` and unmodelled, T024 owns its electrical consumption, and no kernel
exists to read the rule either way. Closing it needs a decision about what two
parameters on one window MEAN - endpoints of a ramp, or two named levels a shape
selects between - and inventing that here would be the narrow semantics
`D-2026-09-22-milestone-speed-over-purity` says not to spend a slice on. The
alternative reading is real, so the choice is not obvious enough to make
silently.

*What would change the answer:* **T021 writes its conformance tests from this
text**, so it is the first consumer and should meet this entry rather than
discover the gap. If T024 models demand before the decision is taken it becomes
urgent, because a forcing with two declared values would reach a kernel with no
rule for composing them.

**T021 met it, by refusing.** The kernel raises `FORCING_VALUE_AMBIGUOUS` when two
declared values force one address in one step, and the statement says why: nothing
says whether they are the two ends of a ramp or two named levels a shape selects
between, so it will not pick. That leaves the semantic decision exactly where this
entry put it - with whoever models demand - rather than having a kernel quietly
choose one reading and a later slice inherit it as built behaviour. The refusal is
this kernel's rather than a contract statement, so it narrows no declared space and
moved no contract version.

It is not reachable on the shipped document today, because nothing models site
demand and an unmodelled address never reaches the step where two values would
collide. It is reached in `simulator/tests/test_execution_failures.py` by giving a
MODELLED address the same shape. So this entry stays open as the decision it always
was, and what closed is the risk of a kernel answering it by accident.

### Two blocking rows can still share a subject across two kinds

An addressed reference whose scope disagrees with the answering profile yields
`INITIAL_VALUE_NOT_RESOLVED` from the Foundation lookup and
`STATE_NOT_SUPPORTED` from the support question, both about one address.

*Safe to carry* because the F5 half T020B owned was the address-versus-support
pair and that one is closed, this pair predates T020A1, both rows are true, and
both carry the same repair - so a reader who acts on either is right. It is a
tidiness cost rather than a wrong statement.

*What would change the answer:* the two rows starting to suggest different
repairs, which would make the pair a contradiction rather than a repetition.

## Carried out of T021

Added 2026-09-27 at implementation, under
`D-2026-09-22-milestone-speed-over-purity`. None meets its stopping rule: none is
expensive to reverse, none misleads an implementer about what the code does, none
needs a user decision. Three of the four are named in the code that carries them.

### ~~A definition edited in place, at an unchanged version, can still move an entry~~ - RESOLVED in T021's correction round, 2026-09-27

The host adapter compares two things between a frozen run and the definition it
names: the scenario version, and the exact set of parameters the document declares
against the set the run froze. That catches a version bump and catches an entry
added or removed. It does **not** catch an edit that moves an existing entry's
offset or window length while leaving its parameter in place, because a Draft
freezes resolved VALUES and profile answers rather than a copy of the timeline, so
there is nothing frozen for a structural comparison to be made against.

*Safe to carry* because an edited value cannot reach a trajectory at all - every
number the adapter produces comes from the frozen run, asserted - so the exposure
is structure only, and the two shipped scenario stores are a tracked read-only
document and a writable store a developer edits deliberately. Nothing in the
product can move an offset.

*What would change the answer:* a scenario authoring UI, or any slice that makes a
frozen run's trajectory an artifact somebody relies on across an edit. Closing it
means either freezing the timeline's structural content on the run - which changes
the frozen identity and therefore the contract version - or adding a content
digest of the projected structure to the run. Both are real changes and neither
belonged in the kernel slice.

**Closed, by the first of those two, and the carry rationale above was wrong.**
T021's independent review reproduced the exposure rather than reasoning about it -
the same persisted run, one offset moved from 1500 to 1515, 334.02 L becoming
374.02 L - and said the rationale was insufficient because T021 owes this boundary
and now produces the trajectory later slices rely on. It was right: an offset is a
causally effective number, and calling the exposure "structure only" did not make
it harmless. Run setup freezes the causal projection, the executing component
takes the run alone, and `EXECUTION_CONTRACT_VERSION` moved 5 to 6.

The second option - a content digest - was rejected on the reviewer's own
argument, and it is the sentence worth keeping: **a digest detects drift and then
refuses, and the criterion asks for reconstruction.** Detection is not
reconstruction.

Kept rather than deleted because the entry is the record that a carry can be
honest in form and still wrong in substance. It named the exposure accurately and
priced both closures, and then reached the wrong conclusion about whose slice it
was - which is the failure mode the backlog's own preamble exists to prevent and
did not.

### The shipped scenario's content changed without a `scenario_version` move

T021 corrected two authored reading VALUES in
`config/scenarios/fuel-loss-event.yaml` and left `scenario_version` at 1. T020B
set the precedent by lowering five `execution_requirement` positions in the same
document at the same version, and this is one step further: a value rather than a
requirement level.

*Safe to carry* because no frozen run is reinterpreted - every existing Draft
carries its own frozen copy of the value it resolved, and the adapter refuses a
definition whose version does not match the one a run froze - and because T022
removes both authored readings entirely under
`D-2026-09-22-reconciliation-panel-retirement`. Nothing has ever executed this
document, so no artifact was frozen against a trajectory.

*What would change the answer:* the shipped store gaining a second consumer that
resolves `(scenario_id, scenario_version)` to content rather than reading a
document, or any slice after T022 editing a value in a document whose runs matter.
The honest general rule, not yet written anywhere durable, is that a shipped
document's version should move when a VALUE changes even if a milestone convention
has been tolerating it.

### The kernel requires its one forcing to be declared

`FORCING_NOT_AVAILABLE` fires when a law reads a forcing input the frozen run
declares nowhere, so a fuel run with a removal and a refuelling and no generator
dispatch at all fails rather than running a tank that sits still. For a world
whose only law is driven by dispatch that is the honest answer - the alternative
is a law that silently does not run - and the failure statement says exactly that.

*Safe to carry* because every document that reaches this kernel declares the
dispatch, and because the statement is true about what happens rather than a
guess. It is recorded because a reader might reasonably expect such a run to
execute.

*What would change the answer:* a second law, or a scenario that legitimately
exercises fuel movement with no dispatch. The fix is per-law rather than global: a
law would declare whether its forcing is required for the run or only for the
steps the forcing covers.

### ~~`reporting_path_addresses` carries addresses and not windows~~ - RESOLVED in T021's correction round

A reporting-path forcing reaches the neutral frozen inputs as an address so the
kernel can say it was withheld deliberately, and its WINDOW is dropped, because
this kernel has nothing to do with it.

*Safe to carry* because the kernel genuinely cannot use the window and because the
field's docstring says what it is for. T022's observation transform is the first
consumer that needs it, and widening a field is cheap.

*What would change the answer:* nothing before T022. It is listed so that slice
widens the field rather than discovering it missing.

**Closed as a side effect of R1.** `FrozenReportingPathCondition` carries the
window, because the defect R1 closed is precisely a declared span being read from
a mutable document at execution time, and leaving this one behind would have
reopened it for the observation transform. The neutral `reporting_path_addresses`
still carries addresses only, which is all the kernel consumes; T022 reads the
span off the frozen run.

## Carried out of T021's correction round

Added 2026-09-27 after the Codex review returned R1-R5 and the user asked for all
five. R1-R5 and the reviewer's C1 are fixed and C2 shrank. These are what remains,
and none meets `D-2026-09-22-milestone-speed-over-purity`'s stopping rule.

### Several proof descriptions are stronger than their assertions

The reviewer's C3, carried as it recommended. The `TRAJECTORY` oracle test checks
that number strings occur somewhere in a free-text statement, and a separate test
checks the physics; it does not parse each number and attribute it to the
statement's own boundary, so swapped labels would retain every token. The identity
field-list guard compares a maintained list against the dataclass's fields rather
than mutating each field to prove the digest reads it.

*Safe to carry* because both were read and both are correct today: the oracle's
attribution is right, and the identity serialization does read every listed field.
The guard probe for the field list mutates the RECORD and watches the guard notice,
which is the half that matters most.

*What would change the answer:* a second `TRAJECTORY` oracle, or a frozen-input
field the digest reads through something other than the listed name.

### `ModelSpec` is not a general law executor

A law's operands resolve through the model's declared component relations to
exactly one address each, and a law writes one stock. That is enough for one law
about one machine acting on another, and it is not a general mechanism: a law
needing two write targets, or a relationship BETWEEN machines rather than within
one, needs a declared connection this model does not have.

*Safe to carry* because the fuel model is the only model and the constraint is
declared rather than assumed - `_bind_laws` fails as `TOPOLOGY_INCONSISTENT`
rather than pairing whatever it found first. This is the remainder of the
reviewer's C2 after the fuel state keys left the shared kernel.

*What would change the answer:* T024's electrical laws. The next implementation
must not mistake `ModelSpec` for a general law executor, and the reviewer said so
in as many words.

### A frozen collection whose span nothing reads

`FrozenReportingPathCondition` carries a window and only its address is consumed.

*Safe to carry* because it is one field on a record that had to exist anyway, and
leaving it out would have reopened for the next consumer the exposure R1 closed.

*What would change the answer:* nothing. T022's observation transform is the
consumer, and it reads the span off the frozen run rather than off a document.

### A guard harness needs a green baseline, and did not have one

Not a finding of the review: found while fixing it.
`simulator/tests/conftest.py` pinned `execution_contract_version=5` as a literal,
the contract moved to 6, the suite went red, and two guard probes reported CAUGHT
against an already-failing suite - which is those probes measuring nothing. The
fixture reads the constant now and the harness establishes a baseline and refuses
to probe if any suite it reads a verdict from is red.

*Safe to carry* as a RECORD rather than as work: both halves are fixed. It is here
because the generalisation is worth more than the fix. **A probe asserts that a
test fails after a violation, so it says nothing at all unless that test passes
before one** - and fourteen probes had been reported as evidence without that
precondition ever being checked.

*What would change the answer:* nothing. Delete at the milestone review.

## Tracked elsewhere, listed so the review finds them

2026-09-24 routing correction: the old three-question count, Block F deadline
and feature-area-5 pointer were superseded by the source-based replan.
The carried review findings above are unchanged.

- `.ai/FEATURE_MAP.md`, Decisions At Their Point Of Use, carries unresolved
  Fuel Loss corrections, fuel expectation/uncertainty and injection/reset
  behavior alongside the roadmap's financial, productive-load and lifecycle
  choices. Do not infer implementation blockers from the old question count.
- A technical walkthrough document, `Docs/life-of-a-finding.md`, was proposed
  on 2026-09-24 and **parked by the user on 2026-09-25**, not declined. It
  would trace one value from authored cause to a claim on screen - world
  state, observation, envelope, gateway, Commit, ingestion, accepted evidence,
  read model, Finding, financial bridge - naming what owns each step and
  marking each as built, specified in a task file, or planned only. The gap it
  fills: `Docs/simulator_design_v4.md` covers the simulator through to the
  gateway and the roadmap covers the demo path, and nothing joins them in one
  technical register. Commission from the Architect when the queue allows.
  A user-authored `Docs/AssetOps_MiniGrid_Technical_Walkthrough.md` covers part
  of this ground and cites the pre-resequencing T024-T029 order; reconcile
  before or during that work.
- Option C (the model declaring its Foundation need) remains triggered by its
  first consuming law: `D-2026-09-22-foundation-value-declaration`.
- The separate observation transform is owned by the recreated T022 starter
  work; see `.ai/PLANNING_HANDOFF_T020A_T023.md` and architecture's Execution
  Composition And Truth Barrier.
- The unassigned delivery requirements are in the feature map's Next Work And
  Unowned Requirements table. They are planned capability, not review debt.
