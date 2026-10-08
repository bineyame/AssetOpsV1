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

### S2-01a current-row metadata and asset-code identity (expires before S2-02 evidence ingestion)

Snapshot v1 pins Foundation, binding and acquisition references, but not the Site row's name/type/timezone or the asset UUID-to-code relation. S2-01a freezes valid current Site metadata on each Draft and refuses a Site type inconsistent with the selected role set; its binding-derived component links still resolve asset codes from current rows. This is safe for the S2-01a simulated, uncommittable run because the product has no Site/asset identity-edit path and no accepted evidence is produced. It does not prove historical Site metadata at `knowledge_at`.

Before S2-02 accepts evidence, enforce stable `asset.asset_code` identity at the database boundary and reconcile any already changed rows, then validate original registered references without substituting current gateway/source names. If historical Site name/timezone reconstruction becomes a product claim, version those facts or change the snapshot contract; do not infer them from current rows. See the S2-01a phase-1 amendment to `D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary` and the S2-02 packet.

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

## T022 cannot start from an existing Draft

Found by the T021A review, 2026-09-27, as a consequence nobody had drawn. It is
not a defect; it is a fact T022's dispatch needs.

The reviewer read **all 165 run documents** in `var/runs` under build 7:
`165 readable, 0 failed; frozen versions {2:49, 3:33, 4:20, 5:47, 6:16};
refused execution 165, executable 0`.

Every stored Draft is now refused execution, **including the sixteen at version
6 that were executable before T021A narrowed the contract to 7**. Readback is
intact across all five versions, which is criterion 5 holding across the whole
store rather than a sample - but nothing on this machine can be executed as it
stands.

T022's outcome is to create a READY Draft in the gated Lab, start it, step it
and run it to completion. It must **create a fresh Draft** rather than reach for
one of these, and its dispatch brief should say so. An implementer that picks a
version-6 Draft out of `var/runs` to save a setup step will meet
`ExecutionContractIncompatible` and may read it as a defect in its own work.

This is the fourth time the integer-equality version guard has decided
something consequential, and the first time the consequence is entirely correct:
a Draft frozen under a contract that has since narrowed genuinely cannot be
re-derived, so refusing it is right. Recorded beside the other three because the
pattern is the same mechanism.

## One invalid scenario document takes the whole catalog down

Recorded 2026-09-27 at T021A's closeout, on the owner's decision. Found because
T021A's narrowing made four user-authored documents invalid, not because anyone
was looking for it.

`read_scenario_records` in
`backend/assetops_backend/scenarios/adapters/yaml_scenario_documents.py:48`
strictly validates every document under its root and **raises
`ScenarioConfigurationInvalid` on the first invalid one**. There is no
skip-and-continue. `CompositeScenarioRepository.list_scenarios` calls it for
both stores, so a single unparseable document in `var/scenarios/` takes the
entire catalog down - **the shipped scenarios with it**. The screen reports an
error instead of a list.

Its docstring already distinguishes the case it does tolerate: a missing root is
an empty store rather than a failure, "and that is not a reason to refuse to
render the catalog". One bad document is treated as a reason, and the same
argument applies to it.

**Why this is a product defect rather than a strictness decision.** Strict
validation on read is right - a document that cannot be parsed must not be
silently half-loaded. What is wrong is the blast radius. Any future narrowing of
the authored-document contract invalidates whatever a user already wrote, and
the consequence is not "that document is unavailable" but "the catalog is
unavailable". T021A is the second contract narrowing in three slices, so this
recurs by construction rather than by accident.

**What would close it:** list the documents that parse, and surface each
invalid one as an inspectable entry naming its file and its validation error,
rather than replacing the list with an exception. The refusal stays loud; it
stops being fatal. That is a change to the store's read path and its screen, and
it wants a slice rather than a patch inside one.

**What the owner decided here:** the four edited documents stay edited. The
edits were mechanically identical to the shipped change - only the string
`execution_requirement: REQUIRED` removed, at the two positions a
`REPORTED_OBSERVATION` carries it, four lines in each Fuel Loss variant and two
in each twin-tank one, with no value, address, source, timing or identity
touched. Pre-edit copies were taken but live only in a session scratchpad, and
`var/` is gitignored, so there is no durable copy; the edit is four hand-edits
to reverse if that is ever wanted.

**The lesson, corrected by the T021A review.** The coordinator's first account
of this said the dispatch brief had named `var/sites/` and `var/runs/` without
naming `var/scenarios/`, and that an incomplete instruction was the lesson. That
was wrong. `tasks/README.md:134`, under "Shared scope and protected seams",
says **"Keep the existing mg-001/mg-002/mg-003 and var/ data intact"** - all of
`var/`, not two named subdirectories - and the task file cites that README by
name for its shared checks and exclusions. It is the only statement on the
subject in the standing records.

So a standing scope limit covered this and was **overridden** by necessity and
then ratified by the owner, rather than being absent. The lesson for a future
dispatch is not "name the subdirectories"; it is that a standing exclusion can
become impossible to honour when a contract narrowing invalidates data the
exclusion protects, and that the honest move then is what the Implementer did -
edit minimally, back the originals up, and hand both judgements to somebody who
can take them.

**One consequence of T021's R1 fix worth recording, because it is the first
place it paid off:** a frozen run carries its whole causal projection and never
re-reads the document, so editing these files cannot change any existing
Draft's trajectory or identity. The 165 runs in `var/runs` were unaffected.

## T030 owes the refused delivery quantity a home

Recorded 2026-09-27 from the owner's operational reading at T021's closeout,
which is domain judgement no test supplies.

T021's shipped run ends with a `BoundedTransition`: 300 L delivered into a tank
holding 254.02 L with a 500 L capacity, 245.98 L accepted and **54.02 L
refused**. `contracts/assetops_contracts/trajectory.py:110` already carries
`requested`, `accepted`, `refused` and `event_ids` as exact first-class values,
so the quantity is attributable rather than merely clamped. **The kernel is
correct and must not change**: nothing physically failed and the world evolved
as declared. Treating a bounded transition as an execution failure would be
wrong.

**What operational reality adds.** A diesel tank cannot be overfilled; it
overflows. So a 300 L delivery into 245.98 L of headroom never happens as
declared. What happens instead is a partial delivery with the balance still on
the truck, the residual drummed or jerrycanned on site, a second tank taking
it, or a spill. **The quantity is conserved in every case and is somewhere
nobody recorded.** Site buffer drums are common where deliveries are
infrequent, and that residual is typically untracked - which is one of the main
reasons fuel reconciliation is hard in practice.

The scenario's own reporting gap supplies the reason such a delivery was
ordered at all: nobody knew the true level when it was scheduled.

**So a bounded transition at a fuel tank is a reconciliation exception - neither
a clean completion nor a failure.** Fuel was paid for, did not enter the tank,
and is unaccounted for.

**T030 owes this a home.** Its subject is fuel balance with separate delivery
and dip records, and a tank rising less than the delivery note claims is
exactly that. It must treat `BoundedTransition.refused` as a **first-class
unexplained delivery residual** rather than recomputing it or passing over it.
Do not infer the residual's destination: the product's honest claim is that the
quantity left the invoice and did not reach the tank.

**One question for the domain expert at the T028 checkpoint**, because it
changes how much this is worth: do operators in practice notice and record a
drummed residual, or does it leave the books entirely? If it leaves the books,
this is a **stronger wedge than the 120 L removal story** - it recurs every
delivery cycle rather than being exceptional, and recurring unexplained
quantity is a better product argument than an occasional theft.

## Carried out of T021

Added 2026-09-27 after two Codex passes and a backup Claude review that
accepted the slice at 17 of 17 criteria and 8 of 8 mutation rows. Neither item
meets `D-2026-09-22-milestone-speed-over-purity`'s stopping rule: neither is
expensive to reverse, neither misleads T022 about the trajectory it consumes,
and the reviewer measured that no record in `var/runs` carries a value of
either shape.

**F1 - a correct refusal reaches the HTTP route as a 500.**
`CanonicalValueNotRepresentable` is raised at
`contracts/assetops_contracts/execution_contract.py:1139` and called from
`backend/assetops_backend/runs/service.py:1077`, `:1527` and `:1564`, all
inside run setup, with nothing catching it. Measured with a `1e-06 L/h` rate
over a 30-minute window: the helper refuses correctly, run setup raises out of
`create_draft_run`, and `POST /api/simulator-lab/runs` returns **500 with zero
records written**. This is the shape of the second pass's gap 3 - a refusal
that is right about the world, raised where this product has always blocked -
and gap 3's fix gave `UnresolvedCausalProjection` a blocking reason and a
persisted BLOCKED run. The refusal introduced in the same round did not get
that treatment. Reachability is narrow: `L/h` is the only canonical unit with
a non-unit factor. Fix by giving it gap 3's treatment, or by refusing at the
scenario parser where the unit and the window length are both in hand.

**F2 - a magnitude below the normalization resolution freezes as zero and the
run COMPLETES.** `_exact` is `Fraction(value).limit_denominator(1_000_000)` at
`execution_contract.py:387`, and it runs at the input boundary **before**
`frozen_canonical_value`, so that helper's round-trip guard compares against an
already-normalized value and structurally cannot see a magnitude lost there.
Measured, and not rate-specific: authored `1e-07 L` on the removal freezes as
exactly 0 and the run COMPLETES with three applied events moving nothing;
authored `1e-09 L/h` over 60 minutes does the same with four. `_exact` is on
`main` and is the declared one-time normalization, so this is not a regression
- but T021 is what made it causally consequential. Fix by refusing or blocking
when a non-zero authored magnitude normalizes to exactly zero, which is one
condition at the same boundary F1 sits on, so price them together.

**One question is open for Codex**, which wrote the gap-3 fix and is the right
reader for what it was meant to cover: did that fix intend to close the class
or the instance, and does either of these belong in T021 or here? A different
answer moves F1 from carry to fix. Not a gate - recorded so the question is not
lost rather than because the slice waits on it.

**A claim corrected rather than carried.** The packet's second correction round
said "A rate whose integral needs a denominator above a million cannot be
frozen at all. The refusal is loud." That is true only *above* the
normalization resolution; below it the same class of value is silently zero.
The sentence would tell a later reader that no magnitude can be lost silently,
and one can.

**Third occurrence of the version guard's blind spot.** `var/runs` holds
version-6 Drafts frozen by pre-fix code, indistinguishable from post-fix ones
because `refuse_incompatible_execution` compares an integer. Nothing executes a
local Draft and every test regenerates, so this instance is harmless. The
pattern is what carries: an equality test on a version number cannot separate
two builds that shared it.

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

## Carried out of T021's second correction round

Added 2026-09-27 after a second Codex pass found four gaps at the boundary a run is
frozen at. All four are fixed, and so is the same defect one site further on. These
are what remains, and none meets
`D-2026-09-22-milestone-speed-over-purity`'s stopping rule.

### A frozen record carries a `float`, and the guard is a refusal

Every number a run freezes crosses `frozen_canonical_value`, which converts once in
exact arithmetic and then checks that the `float` a frozen record holds reads back
as the same rational. Where it does not, the run is refused. That is honest and it
is not the same as being able to freeze the number: a rate whose integral needs a
denominator above a million cannot be frozen at all.

*Safe to carry* because the refusal is loud, the reachable units are narrow - only
`L/h` among the canonical units has a non-unit factor - and no shipped or local
document approaches it. The alternative is an exact representation on every frozen
record, which changes the run document's shape and therefore the contract version.

*What would change the answer:* a unit with a large factor, a scenario authored in
very small rates, or any slice that wants a frozen run to carry an exact rational
rather than a float. That last one is the real fix and it is a deliberate change,
not a repair.

### Version-6 Drafts in `var/runs` were frozen by pre-fix code

The layout tool creates a Draft per run-setup visit against the live backend, and
it ran while version 6 was being amended. Those Drafts are version 6 and are
indistinguishable from post-fix ones, so one could carry a wrongly normalized rate
or, before the parser guard, a record the parser now refuses.

*Safe to carry* because nothing executes a local Draft, every test regenerates in
process, and the shipped document declares no rate at all. It is the third time the
integer-equality version guard has been the thing that cannot tell two builds
apart, which is the part worth carrying forward rather than this instance.

*What would change the answer:* anything that executes a Draft read out of `var/`.
The standing instruction is to regenerate, and it has held for three rounds.

### `.agent/` is gitignored, so a broken tool there cannot be restored

A patch script wrote newline escapes into `.agent/T021-guard-probes.py` through a
script where they were already newlines and broke the block it inserted. There was
no committed copy to restore from. It was rebuilt with a helper that removes the
possibility rather than the symptom.

*Safe to carry* because the probe script is evidence rather than product code, it is
rebuilt from the tests it points at, and the packet records what it measured.

*What would change the answer:* a guard probe script becoming something a later
slice has to re-run rather than re-derive. If it does, it stops being local-only.

## Carried from T022

Six, and none of them is a defect in what T022 built: five are facts about
the tree it ran against and one is a guard that is too eager.

### The shipped scenario cannot reach READY against the user's own MG-001

`var/sites/mg-001.yaml` was created from a template that predates the two
Foundation properties `MINIMAL_FUEL_TANK_MODEL` binds to, so every Draft of the
shipped Fuel Loss Event against it comes back `BLOCKED` on
`INITIAL_VALUE_NOT_RESOLVED` for `fuel-tank-capacity@fuel-tank` and
`generator-specific-fuel-consumption@generator`. That is the truthful answer, and
`backend/tests/test_runs_api.py::TestTheShippedFuelLossEventAgainstAPropertylessFoundation`
has asserted it since T020A.

It became visible in T022 because the browser measurement now needs a Draft this
build can EXECUTE, and one created through the product path from the shipped
scenario is blocked. The layout tool therefore creates its READY Draft from the
user's own `fuel-loss-event-mg006` document, whose target site declares both
properties.

*Safe to carry* because nothing is wrong: a Site created from an older template
legitimately lacks a property a later template added, and
`.ai/ACTIVE_CONTEXT.md` says not to mutate existing fixtures. Both suites and the
browser evidence reach a READY execution through the product path.

*What would change the answer:* a demo that has to run the SHIPPED document end
to end in front of somebody, which would need an MG-001 created from the current
template - a new Site, not an edit to the existing one.

### The layout tool now writes four Drafts per run, not three

Three `BLOCKED` MG-001 Drafts from the run-setup measurement at three widths, plus
one `READY` MG-006 Draft the execution measurements need. `var/runs` grows by four
per invocation and nothing clears it.

*Safe to carry* because it has been true since T019 at three, the run store is
gitignored user data, and the create path is measured rather than mocked - which
is the reason the tool writes at all. The run store's O(n) create is carried
under T022A, in "Reading the run store still costs the whole store, twice",
and this makes it grow faster. That cross-reference pointed at nothing until
T022A's review found it and the entry was written.

*What would change the answer:* the bounded fix that entry asks for, which should
now size itself against four per run rather than three.

### The dependency-direction guard's three oldest patterns match prose

`tools/checks/dependency-direction.ps1` scans for an import statement with
`(?:^|\s)(?:from|import)\s+[^\s]*assetops_simulator`, which also matches the words
in an ordinary sentence. A docstring in `backend/assetops_backend/runs/`
`execution_ports.py` explaining that the backend cannot import the simulator
failed the check. The neutral-contracts half of the same file is anchored to the
start of a line and does not have the problem; the three older patterns are not.

*Safe to carry* because it is a false positive rather than a hole - a guard that is
too eager refuses honest prose and never admits a real import - and because the
sentence was reworded instead. Loosening a dependency check inside the slice that
tripped over it is the one edit that file's own header forbids, so it was not done
here.

*What would change the answer:* nothing about safety. It is a five-character fix
(anchor the three patterns with `^\s*`, as the contracts patterns already are) and
it belongs in a slice that is not the one being unblocked by it.

### `var/executions` is a writable root with no configuration domain

T022 persists a private execution artifact per run under `var/executions`, written
by `host/lab_execution.py`. It is deliberately NOT registered in
`tools/checks/configuration-persistence.ps1`: a trajectory is private simulator
truth rather than configuration, and the product having a store of private truth
would put a filing cabinet inside the truth barrier - a later slice would find
"the persisted trajectory" in `assetops_backend` and be right to use it.

*Safe to carry* because the leaf owns it, nothing imports the leaf, the directory
is inside the already-gitignored `var/`, and the product reaches it only through a
port that speaks `LabProjection`.

*What would change the answer:* a second writer, or any product module learning
the path. Either would mean the seam has moved and the guard should follow it.

### The run setup screen does not show the reporting paths a profile declares

`LAB_PUBLICATION_PROFILE` now declares which device signals report which state,
at what cadence, with what bias and with what dropout. The run-profiles payload
still carries only the blanket cadence, the source and gateway identities and the
supported reporting states, so somebody choosing a publication profile cannot see
what it will make the sensors do until the run is executing.

*Safe to carry* because the declared paths ARE shown, on the Draft's own execution
panel, with the values the run froze - which is the screen where they decide
something. This is a convenience on the chooser rather than a missing fact.

*What would change the answer:* a second publication profile. With one to choose
from, a chooser that omits the difference between them omits nothing.

### Private state shows stocks and not interval measurements

`LabProjection.private_state` carries the stocks a run holds and not the interval
measurements the kernel accumulated. A stock carries the unit the RUN froze for it;
an interval measurement's unit is the model's - the fuel pack accumulates
kilowatt-hours - and the composition leaf would have to name it on the pack's
behalf.

*Safe to carry* because the interval truth is not lost: it appears in the
observation row beside what was reported, in the unit the publication profile
declared for that signal, and `host/tests/test_lab_execution.py` asserts the
11.25 kWh the kernel measured and the 45 kW the controller published.

*What would change the answer:* a second model, or a kernel measurement nothing
reports on. Either would mean the Lab is hiding a quantity rather than showing it
one layer along, and the model should then declare the unit.

### The reporting-path vocabulary has no "silences nothing" case to refuse

`SupportedReportingState.silences` may be empty, and an empty one means the
profile can model a reporting-path state that suppresses no configured signal. A
run forcing it would complete with every reading intact, which is a capability
with no effect rather than a refusal.

*Safe to carry* because the shipped profile declares exactly one such state and it
silences exactly one signal, the constructor already refuses a name that is not a
declared device signal, and nothing can reach the empty case without somebody
authoring a second reporting-path state.

*What would change the answer:* a second member of `REPORTING_PATH_STATES`. At
that point "declared and silences nothing" becomes reachable by accident and
should be refused at construction rather than executed.

### Accepted evidence history does not exist, so criterion 16's guard cannot cover it

`TestExecutingADraftWritesNoSiteHistory` hashes every file under `var/sites`
before and after a completed execution. That is the whole of the persisted Site
substrate this build has. **Accepted operational evidence history is T027's**, so
the guard proves nothing was written to the store that exists, not that a future
evidence store was left alone.

*Safe to carry* because the host has no evidence writer, no Commit and no
envelope release, and the port has no method that could acquire one.

*What would change the answer:* T027 creating that store. The digest should widen
to it in the same slice, not after something has written to it.

## Carried from T022A

### Reading the run store still costs the whole store, twice

**Routed 2026-09-29:** the parser half goes to T022B under
`D-2026-09-29-run-store-libyaml`; the O(n) scans themselves stay carried with
the triggers that decision names.

**T022B result (2026-09-29, pending review):** libyaml is in and the refusal
comparison was done (four declared differences plus one found; one more
difference is an open decision, entry below). At 223 records the composed API
went from 4.1 s to 0.73 s (inventory) and 9.4 s to 1.6 s (setup), but the Runs
screen on the dev server still takes ~1.3-1.5 s on a quiet machine: **the 1 s
budget is missed and T022A criterion 2 stays open.** Remaining cost at 223:
~0.65 s React development-build rendering of the rows, ~0.37 s PyYAML building
Python nodes over libyaml, ~0.07 s domain parsing. At the server, 223 records /
1,504,668 B met both budgets; 300 generated records / 2,305,440 B breached both
(warm medians 1.09 s / 2.26 s); the threshold between them is not established.
Setup through populated run detail in the browser at 223: median 1.86 s, 2 of 7
samples over 2 s. Deferred triggers (caching, indexing, create's scans) are now
live; see `.agent/T022B-review-packet.md`.

**This is the entry three documents already claimed existed.** T022A's packet,
`.ai/CODE_STATE.md` and the task file each said the run store's O(n) cost was
"already carried" here. It was not: the only mention in this file was a pointer
from the layout-tool entry to an entry that had never been written, present
since before T022A. That dangling reference is why this is written out in full
rather than as a cross-link - a residual that lives only in a gitignored packet
and a history file is a residual nobody reads first.

Two live costs, both O(n) in the number of stored runs, both outside what T022A
fixed. T022A made a single-run read cost one document; neither of these is a
single-run read.

1.  **The inventory parses and strictly validates every stored record.**
    `YamlRunStore.list_runs` calls `read_run_records`, which is what the Runs
    screen and `GET /api/simulator-lab/runs` cost. It is unchanged and
    deliberately so: a partial inventory is a wrong answer rather than a slow
    one, so it cannot simply read less.
2.  **`create_run` is still O(n).** `_refuse_existing_identity` calls
    `list_runs`, so setting up a Draft pays the inventory's cost before it
    writes anything. The destination-exists check immediately before the
    atomic move is the other half of the same refusal, and reconciling the two
    is a change to the write's atomicity argument rather than a cheap swap.

**What reproduces, and what does not.** Three independent measurements of the
same operation over the same 216 documents returned about 15 ms, 41 ms and 49 ms
per record - a spread of more than three times on machine state alone. **The
absolute is not a project fact and should not be quoted as one.** What
reproduced across all three: the average stored document is about 6.7 KB, the
YAML scanner is about 99% of the cost with the record parser under 1%, and
libyaml's scanner reads the same corpus about eight times faster. At the
measured range the inventory passes one second somewhere between about 20 and
65 stored runs, which is why it was already uncomfortable when T020A measured
it at 70 Drafts and is plainly a problem at the 216 the store now holds.

*Safe to carry* because a single-run read - every Lab control, every run
screen, every execution read - no longer pays it, which is what made the
build unusable; because neither cost is a correctness defect; and because the
one bounded fix worth anything trades a strictness surface rather than being
free.

*What would change the answer:* **this is partly an owner's decision and is
recorded as one.** The lever is the per-record constant, and libyaml is the
only candidate measured to be worth taking. It shares `SafeConstructor` and
`Resolver` with the current loader, and a reviewer confirmed the two produce
equal documents for all 216 stored runs - but that says nothing about what the
two scanners REFUSE, which is the question that actually matters and which a
pass over valid documents cannot answer. Settling it means comparing them on
invalid inputs. Until somebody does that, or the owner accepts the trade, both
costs stand. T027 is the internal architecture demo and the Runs screen is on
the way to every run.

### Deep flow nesting in a run document kills the process under libyaml

Found by T022B. PyYAML's compiled `CParser` composes recursively in C, so a run
document with flow nesting past ~2,500-3,000 levels (Windows) or ~20-30k
(Linux x86-64) overflows the native stack and the interpreter dies with no
Python exception - before the run parser's own depth bound (12) can refuse it,
and well inside the 256 KiB size bound. The pure-Python loader raised
`RecursionError` and the process survived. Pinned as found by
`test_flow_nesting_a_few_thousand_deep_ends_the_process`.

**Owner decision, 2026-09-29: accepted risk, carried until the run store moves
to a database** (recorded by the coordinator). No database is scheduled in the
queue, so this stays open until one is. Reopen sooner if the store starts
accepting run files from anything but its own writer, or the Lab runs on a
shared or unattended server.

*Why it needed a decision:* the store's own writer cannot
produce such a document, so only a hand-placed or hostile file triggers it; but
one such file in `var/runs` takes the Lab server down on every Runs visit and
every create, because both read the whole store.

*What would change the answer:* an Architect/owner call on a pre-load bound
(for example refusing a document whose raw `[`/`{` depth exceeds a few hundred
as `RunConfigurationInvalid`). That is a new refusal rule the libyaml decision
did not approve, which is why T022B did not add it.

### Construction-time `ValueError`s still cross the run store seam untranslated

Recorded by T022B, identical under both loaders and so not a compatibility
difference: an impossible date (`2026-02-30`), an integer past Python's digit
limit, or a bad explicit `!!float`/`!!int` tag anywhere in a run document raise
`ValueError` from PyYAML's constructor, which is not a `yaml.YAMLError`, so
`read_run_record` lets it through. The inventory then fails as a 500 rather
than as `RunConfigurationInvalid`.

*Safe to carry* because the store's writer never emits such a scalar and the
failure is a refusal either way, only an untranslated one.

*What would change the answer:* the next slice that touches the run reader;
translating `ValueError`/`OverflowError` from the load call is a two-line change
with a test already written (`EQUAL_CASES`, whose expectation would flip).

### The shape check and the identity comparison are two barriers, not one

T022A's fast read is guarded twice: `is_allocated_run_id_key` decides whether a
key may name a file at all, and the identity parsed out of the document is
compared to the key before the record is returned. The packet originally called
the first defence in depth. It is not: the reviewer showed it is what stops an
out-of-root file being opened and parsed, because the identity comparison never
runs on a file that fails to parse. Both now have non-vacuous guards and the
code says so.

*Safe to carry* because it is now correct in the code, the tests and the packet;
what is carried is the risk that a later reader removes **either** barrier as
redundant.

*What would change the answer:* nothing pending. It is here so the next person
to touch `_read_filed_under` meets the reason before the temptation.

### Two documents declaring one identity now resolve to the canonical one

Undeclared behaviour change found in review. With two individually valid
documents declaring the same `run_id`, the old read returned whichever path
sorted first and the new one returns the one filed under that identity. The new
answer is the better one.

*Safe to carry* because `create_run` refuses a duplicate identity, so no path in
the product can produce this, and a check of all 216 stored documents found no
duplicates. It is recorded because T022A's criterion 10 asked for the list of
behaviour changes to be complete and this was missing from it.

*What would change the answer:* a store hand-arranged to contain one, which is
also the only way to reach it.

### `RUN_ID_PATTERN` accepts one trailing newline

`re.compile(r"^run-[0-9a-f]{32}$")` with `.match()` matches before a single
trailing newline, so `is_allocated_run_id_key` and `validate_run_id` both accept
a well-formed identity with a newline after it. Inherited, not introduced: the
pattern predates T022A.

*Safe to carry* because a newline cannot form a path escape and the identity
comparison still refuses the record, so the laxity is not reachable as a defect.
The docstring wording that says "and nothing else" is very slightly generous.

*What would change the answer:* `\Z` is the one-character fix, but it also
tightens `validate_run_id` for every stored document, so it belongs to a slice
that intends that rather than to one that notices it.

### Two T022A claims were stated more broadly than they hold

Both about the account rather than the code, corrected in the packet and kept
here so the correction is not the only record.

- Criterion 4, "one invalid document does not break an unrelated read", holds
  for a canonically filed run - which is every run in the real store - and not
  for a sound run reachable only through the fallback scan. The baseline failed
  there too, so it is not a regression.
- Criterion 1's "a store of any size does not change what one read costs" is
  true of a hit and not of a miss. A miss still walks the store.

*Safe to carry* because both are disclosed and neither is a code defect.

*What would change the answer:* making the fallback unnecessary, which would
mean enforcing the filed-name invariant, which would mean refusing documents the
inventory currently accepts.

### The concurrency test does not prove temporal overlap

Raised by both reviewers. `test_a_read_during_a_write_returns_a_whole_record`
asserts that reads happened, which a reader finishing before the writer started
would also satisfy. The mechanism it covers is sound and was verified
deterministically by a reviewer's synchronized probe.

*Safe to carry* because the property - staging files carry no document suffix and
publication is `os.replace` - is structural, and because the write path is
byte-identical to the one that held before.

*What would change the answer:* a barrier or an injected pause that forces the
read to land mid-write. Worth doing in whichever slice next touches the write.

### A browser harness should live beside the packet it measured

`.agent/` holds the T020A and T020B browser probes, so the practice exists; it
was not applied to T022A's criterion-9 harness until review asked. The harness is
now at `.agent/T022A-step-evidence.mjs` with its baseline server at
`.agent/T022A-before-app.py`, but nothing makes this a rule and `.agent/` is
gitignored, so a preserved harness is still one machine away from being lost.

*Safe to carry* because the practice is cheap and known, and because the same
gitignore risk is already carried in T021's entry about `.agent/`.

*What would change the answer:* deciding whether measurement harnesses belong in
`tools/` beside `layout-evidence.mjs` instead. That is an Architect decision
about what evidence means here, which is the same reason `layout-evidence.mjs`
is not wired into the architecture check.

## Carried from T023

### A message id is the publication's, so two Drafts of one Site share ids

`envelope_message_id` covers Site, gateway, source, device, signal and source
time and deliberately not the run. Inside one stage that is what makes a retry
recognisable. Two Drafts against one Site publishing the same device at the same
simulated instant produce the same id with (usually) different content - a real
collision that T027's Commit or ingestion must decide about (refuse, scope by
commit, or treat as a conflicting report). Not decided here because nothing
crosses a stage yet.

### Interval envelopes and typed unavailability are proved on fixtures only

The shipped allowlist is the fuel level sensor, a state signal that always has a
value, so the shipped run exercises neither `INTERVAL_MEAN` nor `UNAVAILABLE`.
Both are proved by `simulator/tests/test_gateway_publication.py`. T026's
allowlist extension is where they first meet a real run.

### A stage is rewritten whole on every step

`JsonSourceStages.admit` re-reads and rewrites the stage, and the host
republishes the whole series every step: quadratic per run. About 110 KB and
150 envelopes at completion today. An append-only format belongs with T026's
larger allowlist if it matters.

### Release eligibility rests on a publication watermark, not a seal

Corrected in the T023 fix round. This entry first said write order made
eligibility honest; the independent review (R1) showed it did not - a failed
final stage write with the process alive, and a publication refusal caught in
`_stage`, both read as ELIGIBLE. The stage now records `published_through`
against `boundaries_total`, advanced only by a successful write, and a short
watermark blocks release (`STAGING_INCOMPLETE`). What remains carried: the
watermark proves publication through the run's end, not that the stage is
sealed against later change. Sealing is Commit's (T027).

### Some corrupted stages answer HTTP 500 rather than STAGE_UNREADABLE (review R2)

`host/source_stages.py` decodes UTF-8 outside the `StageUnreadable` wrapper, and
`source_envelope._exact_value` calls `Fraction(value)` without translating a
zero denominator, which `parse_stage_text` does not catch. A stage replaced by
byte `0xff`, and one whose envelope value is `"1/0"`, both return HTTP 500 from
the stage route instead of `STAGE_UNREADABLE` / `INTEGRITY_FAILURE` (reproduced
again after the fix round). Fails closed - the frontend shows the stage as
unavailable, never as content - but loses the integrity diagnosis. Carried as a
localized exception-translation gap: widen the negative corpus and translate
both when parser robustness is next touched.

### Identifier and unit validation accept a trailing newline (review R3)

`_IDENTIFIER` and `_UNIT` in `source_envelope.py` are anchored with `$` and
applied with `match`, and Python's `$` matches before a final newline. An
otherwise valid envelope with device id `"fuel-level-sensor\n"` and a correctly
recomputed message id is accepted by `parse_source_envelope`. Narrow against
criterion 4; the shipped allowlist does not admit that id and generated
identities are unaffected. Fix with `fullmatch` (or `\Z`) for both patterns and
a trailing-newline negative case.

### The stage's integrity digest is redundant with its canonical-form check

A guard probe removed the digest comparison and every damage case was still
refused, by the final check that re-renders the whole text including a
recomputed digest. Only the REASON changed, which a test now asserts. Harmless
duplication; a later reader simplifying it should keep one of the two and the
reason assertion.

### Stage selection buttons scale with the stage

The inspector renders one "Show envelope N" button per envelope (154 at the end
of the browser run). Utilitarian by instruction; a later slice with thousands of
envelopes needs paging, not polish now.

## Carried from T024

### The controller decides once per step, at T

The controller's request is made from the view at T and holds as a ceiling
across the step, even when the step is split into segments because a forcing
window starts or ends inside it. A demand rise mid-step can therefore leave
load unserved that a re-deciding controller would have served. Deterministic
and stated in `resolver-is-a-declared-cascade`; the shipped scenarios align
every window to the step grid, so they never meet it.

*What would change the answer:* a scenario with off-grid demand windows that
the owner reads as wrong, or T025's generator start logic needing sub-step
decisions.

### "Battery first" in the source priority means the controller asks for the whole demand

The Implementer's reading of a source priority placing the battery ahead of PV:
the controller requests the whole demand from the battery and PV serves what
the battery cannot; PV surplus during battery discharge is curtailed, because
the battery cannot charge while it discharges. Physically coherent and tested,
and a domain choice nobody else made. The shipped template puts PV first.

*What would change the answer:* the owner's hands-on review, or T025 adding
the generator to the same list.

### One PV array, one inverter, one battery and one PCS

The daytime model relates exactly one of each (`TOPOLOGY_INCONSISTENT`
otherwise), like the fuel model's one tank and one generator. Loads are the
first relation of many. Two batteries resolve and freeze independently at
setup and then refuse to execute.

### The kernel still imports the fuel pack as its default model

The new dependency guard tolerates `packs.fuel` in the kernel and forbids any
other pack. Removing the default is a refactor across every fuel caller.

### Electrical observations are generated, not published

Publication profile 3 declares the electrical reporting paths and the transform
generates their readings; the gateway allowlist is still fuel-only, so a Kobo
Draft stages no envelope. T026 extends the allowlist.

### The screen approximates exact ratios

A state of charge after a 95 % efficient conversion is a ratio such as
`965/19`. The Lab shows it to two decimals marked approximate, with the exact
text in the title. The wire and the artifact stay exact.

### Priority lists cannot change during a run

Only the battery reserve has a scenario override in T024; the two priority
lists are baseline-only and the Lab says so.

### Layout evidence: one CDP hang on the first attempt

The first `tools/layout-evidence.mjs` run of this slice stopped with "the
browser stopped answering" while stepping the fuel Draft (no step request ever
reached the server); the immediate re-run passed every claim. Each run now adds
five Drafts to `var/runs` (four as before plus the Kobo Draft), and the Kobo
Draft adds one execution artifact and one stage.

## Carried from T025a: the contract-9 gate no longer covers real stored Drafts

Owner decision 2026-09-29: the T025a contract-9 gate uses generated stand-ins
(`host/tests/contract9_gate/`, built by its `capture.py` on 96618d9 from the
shipped templates and scenarios), not copies of the owner's Drafts. So the gate
no longer proves that the owner's real stored v9 Drafts and artifacts in
`var/` survive a change. It covers the same case classes (fuel and daytime,
READY, BLOCKED, FAILED, within-step reserve windows, schema-3 stored
artifacts, COMPLETED and RUNNING) and nothing older than what 96618d9 wrote.

Also carried: three of the owner's stored artifacts (two written mid-run, one
under an identity an earlier v9 fix changed) already failed to re-render equal
on `main` before T025a. That was found while the gate still held copies and is
not explained further.

Trigger to look again: before a contract 10, before any change to how v9
Drafts or stored artifacts are parsed, hashed or rendered, or at the milestone
review, whichever comes first. Then run the current reader over `var/runs` and
`var/executions` read-only and diff against a fresh re-execution.

## Carried from T025b: all-missing status attempts skip the enum mapping check

Codex first review, 2026-09-29, finding C1 (`.agent/T025b-codex-review.md`,
probe `.agent/T025b-codex-probe.py`). The gateway skips `DROPPED` and
`SUPPRESSED_BY_GAP` observations before `refuse_an_enum_under_schema_1`
(`simulator/assetops_simulator/gateway/publish.py:115-121`). An allowlist entry
that disguises `generator-controller/status` as numeric therefore publishes
nothing and raises nothing when every status attempt is missing; the same
mapping raises `MAPPING_INCOMPATIBLE` once one report arrives.

Carried under `D-2026-09-22-milestone-speed-over-purity`: the shipped mapping
is fuel-only, no false numeric or UNAVAILABLE status envelope is emitted, and
the fix is a local validation-order change with no identity or persisted-format
migration.

Trigger: when T026 extends the gateway for status staging, validate an
allowlisted observation's enum compatibility before skipping a missing attempt,
with an all-dropped and an all-suppressed case.

## Carried from T025c: four cockpit findings from the first review

Codex first review, 2026-09-30, findings C1-C4 (`.agent/T025c-codex-review.md`).
Carried under `D-2026-09-22-milestone-speed-over-purity`: each is a local
presentation, reporting or parser change with no persisted-identity or
contract migration. R1 from the same review was blocking and is fixed in
T025c itself.

- **C1, stale reading labelled with the selected interval.**
  `frontend/src/shell/HistoryCharts.tsx` `inspectorRows` labels a held STALE
  reading with the selected offset's interval rather than the reading's own
  support (stop-60 run, offset 80: PV row says `[75, 80)` for a reading
  describing `[70, 75)`). Source time and STALE are shown; the plot is right.
  **Closed in T025d phase 1** (3395e5c, test 2bf69d7): `reportedApplies`
  labels the row with the reading's own source time and support.
- **C2, legacy chart fallback unreachable.** A real legacy artifact returns
  `boundaries=[]`, so `HistoryInspector` never mounts `HistoryCharts` and zero
  panels draw; the frontend test keeps the modern boundary list and misses it.
  Tables remain. The T025c packet's fallback claim is wrong for this path.
- **C3, live session hides a history write failure.** `host/lab_execution.py`
  `history()` prefers the retained session and returns `LIVE_SESSION` even
  when the terminal artifact recorded `WRITE_FAILED`; only a restarted host
  shows it. No false durability claim is made.
  **Closed in T025d phase 1** (9a6b980): `LabSession.history_write_failure`;
  the live `history()` answers `WRITE_FAILED`, tested on the same host.
- **C4, strict reader narrower than claimed.** `host/lab_history.py` accepts
  re-signed documents with an empty RECORDED family, a malformed address, an
  unknown unit and an out-of-window timestamp; a short coverage row raises
  `IndexError` instead of `HistoryUnreadable`.

Trigger: T025d touches the same inspector, history reader and live history
capture; close C1 and C3 there if the change is local, and C2/C4 when the
legacy path or reader is next changed.

Claude verification of the R1 fix, 2026-09-30
(`.agent/T025c-claude-verification.md`), carried the same way:

- **K1, no committed agreement test.** Nothing committed asserts that the
  chart's `electrical.steps` PV/battery values match the recorded interval
  flows; it holds (96/96 in the verifier's probe) because one run writes both.
  Trigger: any change to the history writer or the electrical view.
- **K3, fixture label.** The Kobo stop-60 frontend fixture still says history
  schema 1; display-only. Trigger: next regeneration of that fixture.

K2 (stale schema-1 records) was fixed before merge in `ef408a5`.

Found at the owner's hands-on check, 2026-09-30:

- **Run setup's 15-minute default blocks every mini-grid v2 recipe.**
  `frontend/src/shell/RunSetupFrame.tsx` `DEFAULT_TIMESTEP_MINUTES = 15`, while
  the v2 recipes' 5-minute generator start delay needs a 5-minute step, so an
  untouched form yields `LIFECYCLE_TIMING_NOT_ALIGNED`. The refusal is correct
  and explained; the default is the problem. Options: the scenario declares its
  timestep, or the form proposes the largest step dividing the declared
  lifecycle timings. Trigger: T025d or a fast-lane fix, owner's choice.

## Carried from T025d: three cockpit findings from the first review

Codex first review, 2026-09-30, verdict ACCEPT WITH CARRIES
(`.agent/T025d-codex-review.md`). Carried under
`D-2026-09-22-milestone-speed-over-purity`: each is a local frontend repair
with no persisted-format, contract or physical change. The packet's "Met" for
criteria 3, 5 and 6 is qualified by these.

- **C1, timeout recovery re-enables controls before the re-read lands.**
  `frontend/src/shell/runPlayback.ts` `stop()` marks `stopped` before awaiting
  the recovery read, and that read is not tied to its playback generation, so
  a resume can send a stale `from_boundary` guard (probe: `[10, 11, 11]`). The
  host lock and guard refuse it, so no double advancement. Repair: a recovering
  state that keeps mutating controls disabled, generation checks on the read,
  and history/stage sync when a late Step answer lands.
- **C2, whole-run timeline shows unreached declared reporting gaps as
  applied.** `historyTimelineModel.ts` `allEntries()`/`runTimeline()` include
  every declared reporting window regardless of recorded coverage (a run at
  boundary 0 lists its `[60,90)` status gap as a reporting condition). The
  selected-boundary view is correct. Repair: label unreached windows as
  declared context, or restrict to the recorded span.
- **C3, live playback mixes fresh and cached coverage.** `RunFrame.tsx` passes
  each Step's fresh `electrical.steps` to charts whose other series come from
  the history cached at the last stop, so PV and battery power run ahead of
  loads, SOC, fuel and generator; stopping restores agreement. Repair: plot
  the electrical summary captured with the same history, or clip it to that
  history's coverage. Trigger: T025e (Architect item 2 closes it there).

Also noted, unmeasured: the SLD's node slots (PV, inverter, PCS) carry full
sentences in one SVG text element in a 200 px node; the layout tool measures
connection labels only. Checked at the owner's hands-on review.

Found at the owner's hands-on check, 2026-09-30: T025d was accepted as
functionally OK, but the page is poorly organised and flickers during
playback. Routed to T025e (frontend only), guidance
`.agent/T025e-architect-guidance.md`; not a T025d defect.

Trigger: before playback is shown externally at T028/T029, or when T026 next
changes the run screen's refresh path, whichever comes first.

## Carried from T025e: five findings from the first review, two from the R1 re-review

Claude discovery review, 2026-09-30, verdict REJECT on finding 1
(`.agent/T025e-claude-review.md`); findings 1, 2, 4 and 5 were fixed in fix
round R1. These five are carried under
`D-2026-09-22-milestone-speed-over-purity`: each is local, reversible and
cannot mislead an Implementer. Line anchors are as of the review commit.

- **C1 (finding 3), recorded can exceed the clock.** `runFrameState.ts:124-127`
  (`recorded >= clock` leads to `none`) and `:254-270` (`historyLag` states only
  `recorded < clock`). If another tab steps between this tab's answer and its
  delta read, the cursor and drawing show a boundary past the execution clock
  with no statement; a manual Step keeps it until the next control. AC5's
  "cursor <= recorded <= clock" does not hold in that window. Repair: one
  execution read when a delta records more than the answer's clock, or state it.
  Trigger: before playback is shown to a second operator, or when multi-tab use
  is first exercised.
- **C2 (finding 6), server delta cost scales with window length; timing scope.**
  `RunFrame.tsx:90-111` and `tools/layout-evidence.mjs` (T025e budgets). Every
  delta read does a full `capture`, so cost grows with boundary count; 45.9 ms
  is within 8 % of the 50 ms budget at 97 boundaries and a 288-boundary window
  would likely miss it. Repair: memoise capture per session and boundary count.
  Trigger: before any longer demo window (T028/T029 scripts).
- **C3 (finding 7), evidence gaps.** `tools/layout-evidence.mjs`
  `T025E_OBSERVE_PINNED`, `T025E_SAMPLER`. Pinned geometry is not measured
  across the pin and Return-to-live transition (AC7's "nothing moves" is proved
  by jsdom structure only), and the empty-frame check counts series paths
  page-wide, so one blank panel among drawing ones is missed. Repair: sample
  cockpit and cursor boxes across the transitions; count empty panels per
  panel. Trigger: the next change to the cockpit layout or the cursor strip.
- **C4 (finding 8), the Lab gate never iterates the cursor controls.**
  `frontend/src/shell/__tests__/simulatorLabGate.test.tsx`: the fake client
  renders no recorded history, so "offers exactly the named execution controls"
  is vacuous over the timeline buttons, SLD arrows, Return to live and chart
  clicks (the layout evidence exempts them by label). Repair: a recorded-history
  fixture and a named allowance for cursor movers (reads that execute nothing).
  Trigger: the next slice that adds a control to the run surface.
- **C5 (finding 9), performance entries accumulate.** `RunFrame.tsx:90-111`:
  `run-frame-commit` marks and measures are never cleared in production (about
  two per tick; unbounded but negligible at 97 boundaries). Repair: clear the
  mark after measuring, or cap. Trigger: any run longer than a few hundred
  boundaries, or when the instrumentation is next touched.
- **C6 (R1-2), the load-history guard compares counts across runs.**
  `runFrameState.ts:189-199`. The `HISTORY_READ` guard discards a load read that
  records fewer boundaries than the held history but, unlike `laterExecution`
  (`runPlayback.ts:104`), does not check `run_id`. If `runId` changes on one
  `RunFrame` while a commit is in flight (old `TICK_COMMITTED`, `RESET`, new
  load), an old run with more boundaries makes the guard drop the new run's
  history. Reachable only through browser history between two run pages (no
  in-app run-to-run navigation). Repair: compare `run_id` first, as
  `laterExecution` does. Trigger: any in-app run-to-run navigation, or the next
  change to the load path.
- **C7 (R1-3), a timed-out history read is ignored, not cancelled.**
  `RunFrame.tsx:137` (`withinTimeout`). The fetch keeps running after expiry and
  the next tick makes a full read, so repeated hangs can hold open the
  browser's six per-host HTTP/1.1 connections and queue later reads and steps
  in the browser (bounded by the step timeout; play stays honest). Repair: pass
  an `AbortSignal` through `getExecutionHistory` and `getExecutionHistorySince`
  and abort on expiry. Trigger: a host that can hang a read, or any longer
  unattended playback.
- **C8 (R2-1, nit), fixture docstring states the wrong order.**
  `host/tests/make_history_fixtures.py:195` says `load-mill@62` follows
  `load-res@60`; the fixture has it before, which is the case under test.
  Repair: reword the line. Trigger: next edit to that file.
- **C9 (R2-2, nit), fixture regeneration is not byte-stable.** Regenerating
  rewrites five fixture JSONs whose only change is a fresh random `run_id`; no
  test pins it. Repair: pin the `run_id` or say so in the docstring. Trigger:
  next fixture regeneration. Also seen in R2 verification: the frontend
  `src/shell` suite failed 3 and errored 31 while running alongside host
  pytest (153 s), then passed 652 alone (49 s); failure detail not captured,
  load-induced timeouts inferred. Run the suites serially until investigated.

## Carried from T025f: three findings, one decision wording, two residual risks

Claude discovery review, fresh reviewer under the temporary binding, verdict
ACCEPT WITH CARRIES (`.agent/T025f-claude-review.md`, commit `24f53f2`). Every
finding is carried under `D-2026-09-22-milestone-speed-over-purity`: each is
local, reversible and cannot mislead an Implementer. Line anchors are as of the
review commit.

- **F1 (Low), no frontend test for the UNRECOGNISED_VERSION note.**
  `frontend/src/sites/siteTemplateLineage.ts:118`. The branch that words a
  record whose template version the shipped table does not know is never
  exercised by a frontend test. Carried: the note is advisory and the backend
  states the case. Repair: one frontend test with an unrecognised version.
  Trigger: next edit to `siteTemplateLineage.ts`.
- **F2 (Low), the "records unchanged" assertion cannot fail.**
  `backend/tests/test_site_template_lineage.py:130,158-159`. It compares a
  shallow copy against the same objects. The read-only repository that raises
  on `create_site` is the real proof that nothing is written. Carried: the real
  guard exists. Repair: compare deep copies or serialised records, or drop the
  assertion. Trigger: next edit to that test file.
- **F3 (Info), the exported state type is unused and `state` is `string`.**
  `siteTemplateLineage.ts:22-33`. `SiteTemplateLineageState` is exported but
  nothing uses it. Carried: no behavioural effect. Repair: type `state` with it.
  Trigger: next edit to that file.
- **Decision wording, routed to the Architect.** The Versioning clause of
  `D-2026-10-01-run-binds-scenario-to-site` says a bump sets `supersedes` and a
  new valid-from, but shipped templates have neither field. Either narrow the
  clause to scenarios, or plan a template schema change. Carried: T025f
  needed neither. Trigger: T025g, or the next template bump.
  **RESOLVED 2026-10-02** by `D-2026-10-02-template-bump-record` (owner
  signed off): the clause applies to scenarios only.
- **Residual risk, one bad site record blanks every note.** One unparseable
  site record makes the whole lineage read return 503, and every site loses
  its note. Carried: the note is advisory and the sites list still loads.
  Trigger: first hand-edited or migrated site record, or any change to how the
  lineage read walks records.
- **Residual risk, the fingerprint pin table can be edited in place.** It can
  be changed at the same version, and only review of the pin diff catches that.
  T025g's scenario pins share the weakness. Carried: no automatic guard is
  proportionate yet. Trigger: T025g, or any edit to a pin table.

## Carried from T025g: four findings, two residual risks

Claude discovery review, verdict ACCEPT WITH CARRIES
(`.agent/T025g-claude-review.md`, commit `3c37d60`). F1 and F5 were fixed in
fix round R1 and are not carried. The rest are carried under
`D-2026-09-22-milestone-speed-over-purity`. Line anchors are as of the review.

- **F2 (Medium, wording), RESOLVED 2026-10-02 by amending AC6b, owner-approved,
  AC6b names a status-source reason the build does not give.** `host/tests/test_t025g_join.py:125,135`. A missing status source is
  recorded (no `generator-status` mapping frozen) but does not block, by
  design: blocking it would narrow currently-READY requests and argue for a
  contract version move. Carried: the engineering call is right; only the
  acceptance text disagrees. Routed to the owner or Planner to amend AC6b to
  "BLOCKED naming the four missing generator properties; the absent status
  source is recorded, not blocking". Resolved: the owner approved the amendment
  on 2026-10-02 and AC6b now reads that way; blocking would need a later slice
  with its own contract reading.
- **F3 (Low), shipped Kobo `site_contract.description` still states template
  lineage as the requirement.** Six documents, for example
  `config/scenarios/kobo-mini-grid-prolonged.yaml:40`, `kobo-daytime.yaml:35`,
  `kobo-mini-grid-stop-60.yaml:44`: "created from the kobo-mini-grid-60kw
  template". Carried: prose, never evaluated; rewording needs a version bump.
  Trigger: T025i, which bumps these documents anyway. Reword as "a mini-grid
  whose Foundation declares ...".
- **F4 (Low), layout evidence for the run header's lineage fact not run.**
  `frontend/src/shell/RunHeader.tsx:60-65`. `tools/layout-evidence.mjs` aborts
  at its MG-006 user-scenario section. Header wrap at 640 px is unproven.
  Carried: additive fact in an existing header. Trigger: next edit to the run
  header, or running the tool against a stack holding an MG-006-shaped user
  scenario (or making that section skip with a recorded reason).
- **F6 (Nit), leftover "target Site" wording, blank lines, picker copy.**
  `scenarios/parsing.py:93,1730-1748` (one is a user-facing refusal message),
  `scenarios/models.py:230,270,534`, `runs/profiles.py:454`,
  `simulator_lab_api.py:494-498` (five blank lines),
  `RunSetupFrame.tsx:1037` ("Created from template: Not created from a
  template"). Carried: wording only. Trigger: next edit to any of these files.
- **Residual risk, the picker reads each site's Foundation version once.**
  `RunSetupFrame.tsx`. If a site's Foundation moves while the screen is open,
  the request carries the stale version and run setup refuses it. Truthful,
  unchanged behaviour. Trigger: any live-refresh work on run setup.
- **Residual risk, the v2-hard-coded scenario test.**
  `backend/tests/test_scenario_fingerprints.py:143`
  (`test_every_shipped_scenario_is_v2_superseding_v1`). The next bump must edit
  it as well as the pin. Intended friction. Trigger: T025i.

## Carried from T026: two items

Recorded 2026-10-02 by the T026 Implementer after owner ruling on C1.

- **AC15, server delta p95 misses 50 ms before T026 too.** Quiet machine,
  interleaved: pre-T026 p95 about 62 ms, profile 5 about 73 ms (packet "AC15
  re-measure"). To be fixed by a separate performance task taking T025e C2
  memoisation, not by T026.
- **For T028: should stop-60's policy change appear as a policy record (AC3)
  under profile 5?** Since `D-2026-10-02-scenario-states-override-issuer` its
  override publishes no record there; whether it surfaces as a policy record
  (version, effective interval, source) is T028's question.

## Carried from T027 phase 1: three items

Recorded by the T027 phase 1 fix round (review `.agent/T027-phase-1-claude-review.md`).

- **N2: resuming a release needs the live stage, and the refusal misdescribes
  it.** `simulator_lab_api.py` (the commit POST) reads the stage even when the
  sealed artifact is already filed; a missing stage gives `COMMIT_STAGE_CHANGED`
  ("differs from the stage as it is now"). Safe to carry: the stage store is not
  cleaned in the demo, and the refusal is honest about refusing, only wrong about
  why. Would change the answer: any stage cleanup or retention policy (T026A
  recovery volumes), or an owner report of a stuck release. Fix then: refuse
  only when a stage is present and its digest differs, else release the
  artifact; at minimum give an absent stage its own message.
- **N6: the evidence store design.** One JSON document per Site, rewritten whole
  per 64-record chunk with `.partial` and `os.replace`, in-process locks only.
  Measured: the owner's 329-record Site is 571 KB and loads in about 10 ms;
  writes grow quadratically within a batch. Safe to carry: single product
  process, a few Sites, and the task's "simple and correct" limit. Would change
  the answer: two processes over the same `var/evidence` (product app and
  `host/lab_app`) risk lost read-modify-write updates; or multi-Site live
  ingestion, a much larger history, or T026A outage and recovery volumes. Two
  parts to fix then: a single-writer guarantee, and per-record or append storage.
- **N1 store location (owner question).** `var/evidence/registry/` is
  configuration, not derived data: it is the only record of how an earlier
  Foundation version read, because the Site repository keeps no version
  history. The fix round documents this and tests rebuild after an edit, but did
  not move it. Pending the owner: move it to a durable configuration-history
  store, or accept the location. Trigger: T034, before Foundation becomes
  editable. Until then nothing edits a Foundation, so the registry cannot be the
  sole copy of a changed basis.

## Carried from T027 phase 2: three items

Recorded by the T027 phase 2 fix round (review `.agent/T027-phase-2-claude-review.md`).

- **Generator running time is whole-interval.** `evidence/overview.py`
  (`_dispatch`) counts a measured interval as running whenever its mean output is
  above zero, so a start part-way through an interval is counted as the whole
  interval. The basis says so ("measured intervals with generator output above
  zero"). Safe to carry: no Finding reads it before T028. Would change the
  answer: T028's dispatch analytic using runtime. Fix then: derive runtime from
  the status record's transitions, or from the interval mean as a fraction of
  rated output, under the dispatch capability's evidence requirements.
- **Two Lab explanations still say drafts have "no accepted evidence".**
  `shell/RunsFrame.tsx` (76-82) and `shell/RunSetupFrame.tsx` (around 502 and
  1178-1199) explain a draft as never executed, with no output or accepted
  evidence. Two falsifications stack here. "Nothing here has been executed" and
  "no causal runtime exists" have been false since T022. T027 extends it: the
  Runs list shows every run with its execution columns, and a committed run's
  envelopes are accepted evidence, so the "no accepted evidence" clause is
  T027's own (corrected per `.agent/T027-phase-2-claude-rereview.md`). Safe to
  carry under `D-2026-09-22-milestone-speed-over-purity`: Lab-only, gated off by
  default, outside the operator Overview. Fix in a fast-lane wording pass: say
  what a draft is without stating that nothing has run or been accepted.
- **Intermittent T026 layout claim: "the attempts table has five columns, and
  a delayed reading is named".** `tools/layout-evidence.mjs` (around 3742-3751,
  T026 "inspector through the held publication") drives the history cursor and
  reads after a fixed `sleep(600)`. It failed in two of three T027 phase 2 runs,
  with the attempt rows present and only the delayed cell reading 0. That is a
  read racing an asynchronous render, not changed data. Fix: replace the sleep
  with a wait on the delayed cell (or the selected boundary's attempt row) before
  reading. Until then, a single failure of this claim alone is not evidence of a
  regression.

## Carried from T028 Codex review: one item

Recorded by the coordinator from `.agent/T028-codex-review.md` (C1).

- **Unknown Finding types lose the backend display name.**
  `frontend/src/sites/FindingDetail.tsx` and `FindingsIndexes.tsx` call
  `findingTypeLabel` without the declaration's display name, so the AC18 rule-1
  fallback shows the raw id. Safe to carry: the id still renders and the only
  shipped type is mapped. Fix in a fast-lane pass, or with the next analytic
  slice that adds a Finding type: pass the backend display name through.
  The T025b "profile 4 discloses the status as observed and not staged" layout
  claim (failed in T027 phase 2 and T028 runs) also needs a focused Lab check;
  not diagnosed as a flake.

- **Conflicting optional evidence does not lower readiness (re-review F2).**
  Two conflicting minimum-runtime policies or generator overrides make part of
  an assessment Indeterminate, yet readiness stays Full with "no claim-limiting
  gaps identified" (`analytics/declaration.py`, `CapabilityReadiness.tsx`):
  the interim rule has no coverage row for optional inputs. The conflict is
  still named in the assessment's missing evidence. Safe to carry: needs two
  gateways disagreeing on policy, which no shipped recipe produces. Fix with
  T028A's gap impact types (`.agent/T028-fix-round-1-claude-rereview.md`).

## For T029: practitioner-first presentation direction

From `D-2026-10-04-practitioner-first-finding-presentation`
(`.agent/T028-architect-audience.md`): the Planner carries the audience
direction into T029 before it starts. The prospect's journey begins on a
seeded, populated site with the Lab off, not Draft creation, Commit setup or
API inspection; the bounded fuel and maintenance consequence is added to the
readable Finding, compact Overview value and Site Financials, keeping
associated candidate cost distinct from realised savings.

## Carried from T028 presentation review

From `.agent/T028-presentation-claude-review.md` (Claude). Safe to carry under
`D-2026-09-22-milestone-speed-over-purity`: none changes a classification,
number or claim strength.

- **F2:** the Overview Dispatch card is silent on fuel when the lead's fuel is
  unavailable (`SiteOverview.tsx`); the spec asks for an honest unavailable state.
  Fix with T029's card value.
- **F3:** equipment is always "Generator" (`analytics/plain.py`) though the site
  has a display name; use it where available.
- **F4:** a guard exemption can cover a whole prose node and source-reference
  exemptions get no shape check (`frontend/src/test/productVocabulary.ts`); the
  template-shipped foundation summary is exempted as "user-owned"
  (`SiteDetails.tsx`). Tighten with the post-T029 copy inventory.
- **F7 (rest):** decimal hours beside "h min" (`assessmentAnalysis.tsx`); the
  part-missing message misdescribes the default part; "may have been withdrawn"
  shown when the Dispatch read failed (`SiteEvidence.tsx`); a misplaced doc
  comment (`operatorSiteRoutes.ts`); tab-tree indentation in
  `ARCHITECT_DEMO_RECOMMENDATION.md`.
- **Live scan breadth:** the browser vocabulary scan covered one Possibly
  avoidable period; Needed and Cannot determine wording is covered by fixtures
  and the backend check only.

## Planned follow-up after T029: legacy product copy inventory

From `D-2026-10-04-plain-language-analysis-views`: product surfaces outside
the T028 journey (Foundation, Sites, shell) still carry simulation or
implementation wording. Inventory and correct them after T029; no new jargon
meanwhile. Lab surfaces are excluded.

## Planned follow-up: T028A, configurable analytic evidence-gap impact

Assigned by the Codex Architect under `D-2026-10-04-analytic-readiness-scope-and-gap-impact`
(record `.agent/T028-architect-readiness-decisions.md` section 2) at the owner's
request (2026-10-04: defer the gap rule, make it configurable through a "gap
impact type"). Plan after T029's point-2 feedback; unscheduled; gates nothing
on the demo spine. Scope: a versioned backend setting per analytic evidence
requirement (`CLAIM_DEPENDENT`, `COVERAGE_REQUIRED`, `CONTEXT_ONLY`), a small
inspection/editing surface on Site > Evidence, effective type and version shown
with readiness; no generic rules engine. T028 ships `CLAIM_DEPENDENT` as the
disclosed interim rule.

## Parked task: T025h, picker compatibility status (Lab ergonomics)

Recorded 2026-10-02 by the coordinator at the owner's request ("add it to the
backlog to be picked later"), under `D-2026-10-02-demo-led-recommendation`
(D8, owner ruling "Accept"; recommendation 6.3, 6.5).

*What it is:* `tasks/T025h-picker-compatibility.md`, fully planned, no code.
In Simulator Lab run setup, every site-picker row says what Create would give
for that site with the form as it stands: Ready, Blocked (reasons on expand),
or cannot be set up (refusal statement). The task file stays `Status: planned`
because the workflow check has no parked state. The original branch
`task/T025h-picker-compatibility` (`f4274f2`, `8901c4a`) is superseded: do not
merge it; plan from the file on `main`.

*Open owner ruling it carries:* whether the row status depends on the whole
current form (interval, seed, run inputs) or only on the (scenario, profile)
pair its decision names. The Architect leans whole-form: a preview of Create
must depend on everything Create reads.

*Safe to carry* because it gates nothing and is not client-facing. Create
already refuses or blocks with recorded reasons, so a wrong pick is refused
truthfully, not silently accepted. Template drift is avoided by seeding demo
sites from template v3.

*Pick up* not before T029, preferably bundled with the carried T026 AC15
delta-p95 performance task as one Lab-ergonomics slice. *What would change the
answer:* an operator or expert struggling to choose a compatible site during
a demo rehearsal, more templates or profiles making blocked picks common, or
the Lab becoming client-facing beyond the closing proof.

## Superseded scenario versions survive only in git

Recorded 2026-10-01 by the Planner (Claude under
`D-2026-09-30-planner-claude-until-reset`), from
`D-2026-10-01-run-binds-scenario-to-site` and the Architect advisory
`.agent/scenario-site-targeting-architect.md` section 3.

The scenario store holds exactly one document per `scenario_id` (the port has
only `list_scenarios` and `get_scenario(id)`; a duplicate id raises
`ScenarioIdentityConflict`). When T025g moves the seven shipped scenarios to v2,
v1 leaves the store. What survives of v1 is git history and the frozen runs
that used it, which freeze resolved parameters, causes and forcings but not the
`purpose` text. A run setup naming v1 is refused by the existing version check.

*Safe to carry* because run readback never re-reads the scenario document: the
run header renders `scenario <id> v<n>` from the frozen record, and execution
uses only frozen inputs. Nothing on a product path resolves an old version to
content.

*What would change the answer:* a screen or analysis that needs an old run's
purpose text or document beside it (for example a comparison across scenario
versions, or Replay showing the authored intent), or the owner wanting to set
up a new run against a superseded version. The repair is a store that retains
superseded versions keyed by `(scenario_id, scenario_version)`; T025f's and
T025g's fingerprint pins already name every version that has existed.

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
- Option C (the model declaring its Foundation need) was taken by T024 for the
  daytime mini-grid profile (`D-2026-09-29-t024-option-c-and-reserve-override`).
  The Fuel Loss scenario stays on Option B, deliberately.
- The separate observation transform is owned by the recreated T022 starter
  work; see `.ai/PLANNING_HANDOFF_T020A_T023.md` and architecture's Execution
  Composition And Truth Barrier.
- The unassigned delivery requirements are in the feature map's Next Work And
  Unowned Requirements table. They are planned capability, not review debt.
