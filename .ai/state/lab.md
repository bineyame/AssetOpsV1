> Moved verbatim from the former `.ai/CODE_STATE.md` on 2026-11-18 (declutter step 2), part 4 of 11; sections keep their original relative order; the original order of all sections is the numbering in `index-*.md`. Index: `INDEX.md` in this folder.

## T010 - Lab template and create surfaces to mockup quality

What this slice settled in code.

The Site Templates catalog is a canonical page: a search field, a site-type
filter, and a table whose five columns are the template document's own fields.
The filter's options are derived from the types the shipped catalog actually
contains, never from the site-type enum, and the whole toolbar is absent when
nothing ships. Offering a value nothing matches teaches a catalog the build
does not have, and a test fails if one appears.

The create flow is stepped: `Choose a template`, `Site identity`,
`Review and create`. Three steps because there are three stages of real input.
The review shows what the user supplied and which template it copies and stops
there, because source mode, configuration origin and lifecycle status are
assigned by the backend at creation; rendering them would predict a record that
does not exist, which a test forbids.

Refusals are placed against the field they concern by the backend's own refusal
code, in `REFUSAL_STEPS`. `TEMPLATE_NOT_FOUND` and `SITE_ID_IN_USE` each send
the flow back to the step that owns the field and mark the input with
`aria-invalid` and a described-by message; every other refusal renders where
the user is. Placement is never decided by reading the message text, which
would be a second copy of the identity rules in the UI. `CreateSiteResult`'s
refused branch carries `code` for this, and the code is never rendered.

`+ Add site` is the Lab's entry into the create flow, built by
`simulatorLabRoutes.tsx` beside the operator index's entry point. Two entry
points, one flow, one chokepoint, and no frame spells a simulator path.

The shared vocabulary gained toolbar, form control, step indicator and action
patterns. They live in `frontend/src/ui/` rather than in a Lab frame because
T011's Sites index needs the same search and filter row.

The step number is drawn by a CSS counter, not rendered as text, so the rule
that every digit inside `main` traces to a document or to user input stays
intact. Same trade as T009's brand mark. Keep it that way.

The template inspection view needed no change: T009 had already dressed it, and
its "a template is not a site" statement and absence of actions still pass
untouched.

What this slice leaves open.

1. Still not rendered in a browser. Third slice running, and this one is mostly
   visual: the toolbar, the table layout and the step indicator have not been
   looked at.
2. No client-side validation, deliberately. A user can reach the review step
   with empty fields and be refused by the backend at the end.
3. A refusal that names no field lands on the review step, where the offending
   input is not visible. Placing it better would mean guessing the field from
   the message.
4. Search covers name and template ID, not summary.
5. Filter state does not survive navigation away and back.
6. `SiteTemplatesFrame.tsx` and `CreateSiteFrame.tsx` were destroyed by a
   `git checkout --` used as an undo on uncommitted work during this slice, and
   rebuilt. Behaviour is asserted by the suite, but they are a reconstruction.

## T017 - Scenario catalog and Fuel Loss Event detail

What this slice settled in code.

`backend/assetops_backend/scenarios/` is the first new domain package since
Sites. It is built to the same shape and holds the same line:
`ScenarioDefinitionRepository` in `ports.py` speaks domain records and its own
error family - not found, identity conflict, configuration invalid, store
unavailable - and `adapters/` owns every path, file handle and YAML call. The
error family is parallel to the Site one and deliberately not a reuse of it: a
missing scenario and a missing Site are different facts about different
identity spaces.

There is no write path anywhere in the package. T017 ships no scenario creation
flow, so neither store has a create method and the port has none to implement.
That is structural, not a convention, and `tools/checks/configuration-persistence.ps1`
holds it: writes are allowed only in the one Site user-store adapter, so a
write appearing in any scenario module fails the build.

Two stores, one `scenario_id` space, no overlay and no precedence. Duplicates
within a store are caught by the document reader, which is the only layer that
can see two files; duplicates across stores are caught by the composite. Both
fail on list and on read - a read that quietly picked a store would be
precedence arrived at by accident.

`config/scenarios/fuel-loss-event.yaml` is tracked and read-only at runtime,
and unlike `config/sites/` the shipped scenario store deliberately does NOT
ship empty: with no create flow, an empty store would leave a fresh checkout
with nothing to inspect. The guard asserts both asymmetric expectations rather
than tolerating either.

The parser/service split is the load-bearing seam and it was an Architect
finding before it was code. `scenarios/parsing.py` validates the SHAPE of the
target-site declaration - including the policy-shape rule, where each field is
individually well formed and only the combination is wrong - and never reaches
into Site storage. `ScenarioDetailService` resolves the declared `site_id`
through `SiteRepository` and returns one of four target-resolution states.
Removing a Site therefore makes a scenario's target unresolved; it does not
make the scenario unreadable, and a test asserts the timeline still renders in
that state.

Public authoring data and private test-oracle expectations are separate parsed
fields on `ScenarioDefinition` and separate payload builders in
`simulator_lab_api.py`. The public builders never name the private field, so
they cannot leak one by omission. Proved with a sentinel that is present in the
private payload and absent from the public one, so the assertion cannot pass
because the sentinel was never there.

The breaker/control vocabulary protection grew and the banned list moved to
`backend/tests/control_vocabulary.py`, read by both scans. It now covers the
scenario domain model, the parser's key vocabularies, the shipped definition
and `backend/tests/scenario_fixtures.py`. It compares TOKENS, not substrings,
and scans schema positions only: every mapping key, plus every string value
spelled in upper snake case, which is exactly how this project spells an
enumerated value. Prose is not schema, so a description may use the word
"closed" in English while a category may not. The ban is unconditional: the
taxonomy is typed, because the parser refuses an unsupported value.

Four deliberate violations proved it: a banned category in the model, a
`breaker_position: CLOSED` parameter key in the shipped document, the same key
in the fixture, and `BREAKER` as a Foundation `DEVICE_TYPE`. Each failed
naming the offending term.

`tools/checks/configuration-persistence.ps1` is now stated once and applied per
configuration domain rather than written out twice. Four deliberate violations
proved the scenario half: a scenario adapter imported outside its composition
module, `import yaml` above the scenario adapter layer, a `.mkdir(` in the
shipped scenario store, and the shipped definition removed.

`frontend/src/ui/ReviewProposal.tsx` is a new primitive whose TYPE requires a
question, a proposal, what is already settled, and what accepting and
redirecting mean. T016's checkpoint put candidates on screen with no proposal
and settled nothing; a region that cannot be rendered without a proposal is the
structural answer to that.

The family, at eight, and the eighth is the one worth carrying forward.

**A proof can pass for the wrong reason, and then it has proved nothing.** The
vocabulary scan read mapping keys and upper-snake enum values. A scenario
parameter key is neither: it is the lowercase identifier in the `parameter_id`
FIELD. So `parameter_id: breaker-position` passed the guard and the parser, and
so did `event_id: auto-mode-change` and a `scenario_id` built the same way.

Four deliberate violations did not find it. The reason is the lesson: the
parameter proof added `breaker_position` as a mapping KEY, and the strict
parser already refuses unknown mapping keys, so the document was refused before
the vocabulary rule was ever consulted. It failed, it failed loudly, and it
measured a different guard. **A deliberate violation has to be one the rest of
the system would otherwise accept.** An independent reviewer found this, not the
proofs.

The fix moved the banned list into product code at
`assetops_backend/control_vocabulary.py`, so `scenarios/parsing.py` and
`scenarios/identity.py` refuse a banned identifier at parse time rather than
the rule living only in a scan that might not reach the position it protects.
The scan gained an `identifier` position kind, and
`TestTheIdentifierAuditIsComplete` makes the audit permanent: every `*_id`
field in the scenario schema must be classified as scenario vocabulary or as a
reference into another identity space, and a new one fails until somebody
decides which. Fixing only the position the review named would have left the
next one.

The ninth, found by a proof in the same pass.

The invented-digit assertion took three attempts.
`digitsInRecord()` compared digit RUNS against the record's runs, so an
invented `7` matched a real sequence number - a deliberate "all 7 categories"
passed. Carving out the containers that hold record values failed for the
complementary reason a reviewer named: those containers hold authored text too,
so a static digit in a table heading was removed wholesale. What holds is at
leaf level: every text node is either exactly a string the record supplies, or
carries no digit at all, asserted in both directions so the expectation cannot
be padded.

Then the proof of THAT found a third thing: a digit inserted into the
`No earlier version` fallback still passed, because the loaded fixture takes
the other branch and the fallback never rendered. **Authored text that no test
renders is authored text no assertion covers, whatever the assertion says.** A
second record that takes every fallback branch, and carries no digit of its
own, closed it.

So three habits, in the order they were learned the hard way: break the thing a
guard protects in the cheapest way a careless author would; check that the
break reaches the guard you meant rather than some earlier one; and check that
the branch you broke is a branch the test renders at all.

What the checkpoint proposes, and what it does not settle.

Three `ReviewProposal` regions on `/simulator-lab/scenarios/fuel-loss-event`:
`scenario-versioning` in the identity panel, `scenario-event-taxonomy` under
the timeline and its legend, and `scenario-public-private-boundary` in the
private expectations panel. Each states a proposal, not a menu.

Until the user answers, the values in `EVENT_CATEGORIES`,
`TIMELINE_ENTRY_KINDS` and `SCENARIO_VERSION_FIELDS` are provisional in
meaning but strict in enforcement: the parser refuses anything outside them.
T018 and T019 stay non-implementable until the Review Outcome is recorded.

## T018 - The executable scenario contract

What this slice settled in code.

Scenario content now has two orthogonal axes. `entry_kind` and `category` say
what sort of authored item something is; `execution_role` says what an
executor may do with it. Collapsing them would make a row's meaning depend on
who is reading it, which is exactly the ambiguity T017 left open.

Four roles: `CAUSAL_INPUT` initializes or changes private world state and is
the only one that may; `FORCING_INPUT` is an exogenous condition on the world
or on the reporting path; `REPORTED_OBSERVATION` arrives through a named
source; `NON_EXECUTABLE_CONDITION` is description nothing consumes.

The guarantee "an observation never prescribes private world state" is
structural, not a rule to remember. `ROLES_BY_ENTRY_KIND` refuses an evidence
condition that tries to be a cause. A reported value may carry no `ownership`
block and no `state_effect`, so there is no field it could arrive in as an
initial value or a transition. `initialization_inputs` and
`state_transition_inputs` are built only from causal inputs. Three layers, and
a deliberate violation had to be applied at the third to measure the contract
test at all - relaxing the parser rule tripped a different guard first, twice.

`scenarios/execution.py` is a new module and it holds what the roles commit
the product to, because those semantics are the same for every scenario and
are versioned simulator rules rather than authoring: canonical units, dispatch
rules, bound cases. It converts through exact ratios rather than floats, so
14 L/h over 240 min is 56.0 and not 56.00000000000001 - a screen showing the
second would state a precision the scenario does not have.

`reconcile_reported_observations` lives there and is contract arithmetic, not
a kernel. No clock, no timestep, no state record, no output for any instant
the scenario did not author a reading at, and it declines to answer when a
causal window is still open rather than apportioning half an effect. The
module docstring says so, and a reviewer should keep checking it: the scope
limit that forbids a kernel is the reason the line matters.

Bound behaviour has three policies and the absent fourth is the point: there
is no `SILENT_CLAMP` and no `DISCARD`. `invalid-rate` is the one of four cases
decidable without executing anything, so the parser enforces it end to end - a
negative or non-finite quantity in a non-negative dimension is refused when
the definition is read.

Cadence is declared and never derived. A device source says `NOT_DECLARED`, an
operator record says `NOT_APPLICABLE`, and the vocabulary has no value meaning
"the scenario declares it". The prohibition is enforced where a cadence would
actually be written: a duration parameter on a reading, refused by name. That
Foundation declares no cadence is checked rather than asserted - a test pins
`DeviceSignal` to exactly `signal_id`, `display_name`, `unit`.

`ScenarioDetailService.resolve_observation_sources` follows the target-site
split exactly: the parser validates that a device-signal source names a
well-formed device and signal, and the service resolves them against the Site
store into a screen state. A missing device is an unresolved source, not an
unreadable scenario.

The identifier audit widened from `*_id` to `*_key`. A world state key is an
identifier this domain coins and renders as the name of a thing, and
`state_key: breaker-position` would have read as perfectly natural to an
author - the same hole the T017 review found in `parameter_id`, one field
along. Proved by putting `breaker-position-availability` in the shipped
document and watching both the parser and the scan name `BREAKER`.

The shipped Fuel Loss Event's numbers are unchanged and they do not agree.
430 L initial, less 56 L over the dispatch window, less 120 L removed, is
254 L at both reading offsets, against 155 L reported and 150 L
hand-recorded. Both readings are now classified as reported observations from
a named source, so neither prescribes tank state and the contract is coherent.
What it also does is say the difference out loud, with quantity and sign, and
leave the resolution to review. Editing a number into agreement would have
settled a product question by arithmetic. Two authored values did change
shape: `overcast-day` gained a 360-minute window, which is the distance
between two offsets the document already declared, and the free-text
`observed-signal` parameter was removed because `observation_sources` now
carries that identity machine-readably.

The tenth member of the family, and it is a layout one.

`minmax(8rem, auto)` on the `.fact-list` term column gives that track a
max-content growth limit, and grid hands a non-flexible track all the free
space it can absorb before a `1fr` track sees any. A long term therefore took
the whole row, the value column resolved to zero, and its text pushed the
DOCUMENT sideways: seventeen pixels of horizontal scroll at 640px, with the
rail going with it. The first cap made it worse by moving the overflow one
level down into the value column. **A cap has to leave the other column room
for its longest word.** Twelve rem measured clean. jsdom has no layout, so
neither suite could have seen any of it - only `tools/layout-evidence.mjs`
could, and only because the slice ran it.

What T018 deliberately does not do: no model profile, so nothing computes a
Draft status; no run, no trace, no kernel. Every executable input names the
state it needs and whether it is required, which is what makes that decision
possible for T019.

### What review round one changed, and the three lessons in it

Independent review accepted the slice with five findings, all fixed on the
branch. Three are worth carrying forward because each is a failure shape, not
a typo.

**A screen may not assert a guarantee the code does not hold.** The role
legend said only a causal input could reach private world state, and the
proposal asked the user to accept that, while a forcing input could declare
`initializes: true` and came back as the initializer of a world state. On a
`USER_REVIEW_REQUIRED` screen that is worse than a plain bug: accepting it
would have locked in a guarantee nothing enforced. The fix made the sentence
true rather than weakening it, because the stricter rule is also truer - an
exogenous state's value at every instant comes from its forcing profile,
including the first. `STATE_CHANGING_ROLES` had no consumer anywhere and its
only test asserted its own literal value; it now has two consumers that do
not depend on each other, and a test that measures both.

**A rule written for one position is a rule with positions left over.** The
cadence prohibition was enforced on a duration parameter hung on a reported
observation. Three neighbours were wide open: a top-level duration, a duration
on the entry forcing the reporting path, and a reading timed as a window. The
fix was not to add two more position rules. `min` and `h` stopped being
authoring units, so a duration has no unit to be written in anywhere, and the
closed unit vocabulary the parser already enforced does the work; separately a
reading must be a POINT. The packet had claimed "there is no field a rate
could occupy" while three fields could - so the claim is now true rather than
softened, and what the rule does not reach is stated: prose, which is English.

**A contract may not report a number the same contract refuses.** The
reconciliation summed every completed transition without consulting a bound
and, with the delivery moved before the readings, reported a declared 554 L
against a declared 500 L capacity under a column headed "declared causes
reach". Capacity and volume were two state keys with nothing connecting them,
so a `bounds` declaration now says which state a world value limits - declared
rather than guessed from a shared prefix. Reaching a bound makes the reading
`NOT_RECONCILABLE`, because applying the clamp is the kernel's. The
transitions are walked in completion order rather than summed, since a bound
is reached at a moment and a total that came back inside would hide it. Every
answer now carries a reason: a `NOT_RECONCILABLE` with none was three
different facts wearing one name.

The habit underneath all three: a guard, a sentence and a number each have to
be checked against the thing they describe, not against themselves.

### What round two left open

Re-review accepted the slice. It reproduced every before/after rather than
reading the packet, judged both departures from its own suggested fixes to be
better than what it offered, and confirmed the T017 vocabularies byte-identical
after a round that narrowed the unit vocabulary. Four findings, all Low, all
preferences or test-strength points, none an acceptance gap. They were not
fixed before merge and are the first cleanup available to a later slice:

- **Intra-instant ordering is load-bearing and undeclared.** SETTLED by T019.
  Transitions completing at the same offset are walked in authored `sequence`
  order, which is deterministic, but `DISPATCH_RULES` did not say so - and
  with the bound walk that order decides whether the contract answers or
  abstains. Two causes at one instant, authored either way round, give
  `NOT_RECONCILABLE` or `declared 454.0`. Never a wrong number, and the
  shipped document has no simultaneous transitions on one state. T019 made it
  observable from outside the contract, because the answer became a blocking
  reason persisted on a Draft, so it is now the `intra-instant-order` dispatch
  rule. The rule does NOT say authored order decides: the T019 checkpoint
  reversed that, and simultaneous causes are a group with a net effect whose
  order-dependence is decided exactly. The T019 entry has the reasoning.
- **The second initialization layer is real but unmeasured.** The role guard
  in `initialization_inputs` holds if the parser refusal is ever loosened -
  verified by constructing the record directly - but the branch is unreachable
  through `parse_scenario_document`, so no test exercises it. The same shape as
  the round-one lesson, one size smaller.
- **The contract-version test is honest but weak.** SETTLED by T019, as a
  side effect of the entry above. The fixture value and
  `EXECUTION_CONTRACT_VERSION` were both `1`, so a hard-coded `1` in the
  component would still have passed, and the backend asserted `>= 1`. The
  constant moved to `2` because the rule set gained a rule; the backend now
  asserts equality with it and the frontend fixture stays at `1`, so the two
  cannot be one literal by accident.
- **Two forward constraints live only in code comments.** A `POINT`-only
  reading has no shape for a metered `kWh` aggregate, which a later evidence
  slice will meet; and no duration has an authoring home outside
  `timing.duration_minutes` until a slice reopens that vocabulary on the
  record.

## T019 - Draft run setup

What this slice settled in code.

`backend/assetops_backend/runs/` is the third domain package, built to the
same shape as `sites/` and `scenarios/` and holding the same line: a port
speaking domain records with its own error family, one composition module, one
adapter layer. It is deliberately not a reuse of either - a missing run, a
missing Site and a missing scenario are three facts about three identity
spaces - and it is the second package in the product with a write path.

**Run setup decides one kind of thing, and Amendment 1 is what made that
true.** Every blocking reason is a statement about the SELECTED PROFILE:
a state it does not model, a role it does not support, a cadence or a
publication identity it does not resolve. A sixth kind was removed to make it
so. `OBSERVATION_NOT_ACCOUNTED_FOR` blocked a run when the causes a scenario
declared did not reach a reading the same scenario declared, and proposal (e)
took it out: run setup has no kernel, so whether declared causes reach a
reading is a statement about what a run would produce and not one it can
make. The shipped Fuel Loss Draft blocks on three reasons rather than five;
`BLOCKED` is unchanged as an outcome and is reached for a sounder reason. A
kind added later that is not about the profile's ability to execute an input
is that mistake returning, and the vocabulary is pinned as an exact set for
exactly that reason.

`reconcile_reported_observations` still exists, still answers that question
for the scenario detail surface, and is labelled in the test suite as a
specification reference implementation
(`D-2026-09-21-specification-reference-implementation`). **Its expiry is a
condition, not a slice number**: it stops being an authority when a kernel
exists and the two are compared, which is T021's comparison, and it leaves
the repository when its last product-path caller goes - the
`observation_reconciliation` payload and the panel that renders it. That was
Open Question 5 and undecided; it is now
`D-2026-09-22-reconciliation-panel-retirement`, which puts the panel, the
payload, the reference implementation, `declared_bounds` and
`IMPLICIT_LOWER_BOUND_DIMENSIONS` in **T022**, with (f). No slice before T022
treats the removal as in scope.

**The refusal line is the slice, and the T019 user review sharpened it into
a question about who failed to answer.** The scenario's declared owner has no
answer, so nothing can be frozen and no profile helps: refuse. The selected
profile cannot answer, so a different profile would: persist a `BLOCKED`
Draft. T019 was aligned to T020A rather than the reverse.

The observation that decides the hard cases: **a Foundation's answer is only
locatable THROUGH the selected profile's binding**, so failing to locate it is
a joint fact about the pair, and the profile is the half a person can change
on the setup form. Four failures therefore block - the profile declares no
binding, the binding matches nothing, it matches more than one thing, or its
unit is not the scenario's - and one refuses: the Foundation's value
disagreeing with the value the scenario states it declares, where both
declared owners answered and contradict each other. A profile pointing at
some other component that happened to match would be resolving a
contradiction by shopping for a value.

`INITIAL_VALUE_NOT_RESOLVED` carries all four, and the name is chosen for
that: it names the state the value is left in rather than the cause, so one
name covers four causes here and T020A's uncarried `MODEL_RULE` case without
rewording.

**The frozen identity has one absent case, and it is load-bearing.**
`FrozenInitializationInput.value` and its canonical restatement are nullable
and absent together; the unit is not, because the scenario declares it
whether or not anything answers. This was a protected-seam change, so nothing
else about the identity's shape moved.

Three invariants guard it and **all three live on the record**, because the
service cannot produce a violation and a hand-edited document can:

- a run is `READY` exactly when it carries no blocking reason;
- every absent value has a blocking reason naming **the same state**. The
  first version of this asked only whether the run carried any reason at all,
  and the final gate satisfied it with an absent value beside a reason about
  an unrelated profile identity. **An invariant that is weaker than its own
  docstring is the docstring making a promise the code does not keep** - the
  same family as a screen asserting a guarantee the parser did not hold;
- the two number fields are absent together. That was enforced only where
  documents are read, while the record's own docstring stated it as a
  property of the record.

The reason the contradiction case refuses while the four location failures
block is **structural, not a judgement about fixability**: the four leave the
value with no answer, which the record can represent as absent, and the
contradiction leaves it with two, which the record cannot represent at all.
A blocked Draft would have to freeze one of the two numbers. The earlier
reason - that a profile finding another matching component would be shopping
for a value - falls to a site that declares a second matching component whose
rating equals the scenario's, and is kept only as the intuition.

**That argument is now in the vocabulary.** The contradiction is
`INITIAL_VALUE_ANSWERS_DISAGREE` rather than sharing
`INITIALIZATION_INPUT_MISSING` with a value nobody supplied: an absence and a
contradiction are not the same shape, and the old name described the wrong
one while sitting one word from the blocking `INITIAL_VALUE_NOT_RESOLVED`
with nothing in either name saying which side of the line it was on. The new
name is the mirror of the blocking side - a run can carry "no answer" and
cannot carry "answers disagree" - so a reader knows from the name alone that
it cannot appear on a persisted Draft and must be a refusal.

A test asserts the refusal and blocking vocabularies share no string. The
near-collision one step away is older and was left: `COMPONENT_OR_SIGNAL_
UNRESOLVED` refuses while `INITIAL_VALUE_NOT_RESOLVED` blocks, so "unresolved"
is already on both sides. **This vocabulary has no naming rule that would
have prevented either collision**, and inventing one at the end of a review
round is not an implementer's call.

 A refusal means the request could not be
frozen: something it names does not exist, does not resolve, is not well
formed, or would have to be invented. No `run_id` is allocated and nothing is
written, so there is nothing afterwards to inspect. `BLOCKED` means everything
was frozen and the run still must not execute: the Draft exists, is persisted,
and carries reasons. `runs/refusals.py` states it once, and the code has the
shape: everything in `_freeze` raises, everything in `_blocking_reasons`
returns. Every refusal test asserts the store is empty afterwards, because an
error raised after a write looks identical without that assertion.

Ten refusal kinds and six blocking-reason kinds, each a different fact with
its own code on the wire. The three `BLOCKED` reasons for the shipped Fuel
Loss Event against the shipped profile are three unmodelled forcing states,
so **the shipped scenario cannot reach `READY` in this build by
construction**. `READY` is proved against a fixture scenario instead.

Both counts moved during this slice and an earlier draft of this paragraph
kept the old ones. It said nine refusals, before the contradiction split out
of `INITIALIZATION_INPUT_MISSING` as `INITIAL_VALUE_ANSWERS_DISAGREE` and
`INITIAL_VALUE_NOT_RESOLVED` joined the blocking side; and it said five
blocking reasons on the shipped Draft, which was true before (e) removed the
two unreached readings and is contradicted three paragraphs above by this
same entry. A later slice that resolves the
residual or widens the model profile changes that, and the test naming the
three unsupported states will fail when it does, which is the point.

**Nothing is defaulted, in either direction.** A parameter the scenario
declares `RUN_OVERRIDE` must be supplied by the run and a parameter the
scenario owns may not be overridden; a Foundation-owned initial value is
resolved through a binding the model profile declares, never by matching a
state key against a component by spelling, and a Foundation that disagrees
with the scenario's stated requirement refuses rather than silently winning.
Two components that both fit the binding also refuse: two answers to one
initial value is not something a run may choose between.

**Cadence, simulator source identity and gateway identity are structural.**
They are resolved in `runs/profiles.py`, which imports nothing from the Site
domain, and the two records that carry them may be constructed only there and
in the store's own document parser. `tools/checks/run-setup.ps1` holds both,
plus the identity chokepoint: the `run-` prefix is spelled in
`runs/identity.py` alone and one caller allocates.

**That guard scanned one directory for its first two rounds, and the
independent review disproved it.** A function in `simulator_lab_api.py`
deriving a cadence from a device display name passed 789 tests and passed the
architecture check, because the scan never looked outside
`backend/assetops_backend/runs`. It scans the whole backend package now, with
a vacuity assertion that fails if it ever reaches no module outside the run
domain. The lesson generalises past this guard: **a guard's scope is part of
its claim, and a module that describes itself as protecting the product while
scanning one folder is a false statement about a real check.** The ban is on the IMPORT
rather than on words like `display_name` or `lifecycle_status`, which collide
with the run's own fields - a ban with exceptions is a ban somebody widens.

A run identity is allocated from nothing: no Site, no scenario, no text, no
clock, no counter. The request has no field for one and a request that sends
one is refused by name, which is how "a scenario label never becomes a
`site_id`" holds one space further along.

Real IANA membership is checked against `zoneinfo.available_timezones()`, in
both directions: `Africa/Atlantis` is refused though it is shaped like a zone
and `UTC` is accepted though it is not. `tzdata` is a declared dependency
because Windows ships no database and a membership test against an empty set
refuses every real zone. "Not a zone" and "no database" are two different
failures and stay two.

`frozen_inputs` turns the identity into one row per value with its answerer,
and a test walks `dataclasses.fields(DeterministicIdentity)`: a field added
with no answerer fails the build rather than reaching a screen in a column
with nothing under it. `ANSWERER_BY_INITIALIZATION_OWNER` maps T018's
`INITIALIZATION_OWNERS` one to one, asserted, so a fifth initialization owner
with no answerer fails. **The second half of that assertion is a subset, not
an equality**: `FROZEN_INPUT_ANSWERERS` may hold a member no initialization
owner maps to, which is what lets T020 add `PUBLICATION_PROFILE` without
touching the correspondence. The docstring and the test name saying "the four"
are prose and are T020's to correct.

The persistence guard now registers a third domain. A run is not
configuration, but the seam is the same one, and the guard proved it by
failing with seven findings the moment the store appeared.

The eleventh member of the family, and it is the tenth one again.

T018 capped the fact list's TERM column because an unbreakable term pushed the
document sideways at 640px. T019 put an unbreakable VALUE in the same
component - a run identity is thirty-six characters with no break opportunity
- and the value column resolved to 103px against 230px of content: seventy-
nine pixels of horizontal document scroll, rail included. **A fix applied to
one column of a two-column component is a fix with one column left over.**
`.fact-list__value` now breaks anywhere, which is the right treatment for a
machine identity. Only `tools/layout-evidence.mjs` could see it, and only
because the tool was taught to fill the form and submit it first - the summary
does not exist until somebody does.

Three deliberate violations proved the new guard, each accepted by all 785
backend tests and caught only by the scan: the observation binding built
inline in the service with identical behaviour, an unused Site-record import
in the resolver, and the run identity assembled in the service. The third
found a hole in the guard: its vacuity check counted `def allocate_run_id(` as
a call, so "nothing allocates" would have passed on a tree where nothing did.

What T019 settled from T018's open list, and what the checkpoint reversed.

`intra-instant-order` is now a `DISPATCH_RULES` entry. Freezing run inputs is
what made the question decidable from outside the contract: whether the
reconciliation answers or abstains becomes a blocking reason **persisted** on
a Draft and read back, so the rule decides what a stored run says about
itself and belongs in the contract rather than in the stability of a sort.

**The first rule this slice declared was wrong and the T019 checkpoint
reversed it.** It said two transitions completing at one offset apply in
authored `sequence` order. Three things were wrong with that, and they are
the reason the replacement looks as it does:

- serialising two causes the author declared to happen together produces a
  level the state is never in, and the contract then abstained *on a number
  that does not exist* - the same family as the round-one finding where a
  contract reported a number the same contract refuses;
- `sequence` is an authoring and display field, and reading it as physics is
  the shape of the bound that used to be guessed from a shared prefix;
- it would have obliged T021's kernel to serialise sub-steps within one
  instant in document order and evaluate bounds between them, forbidding a
  net-change-per-step implementation, making bound behaviour depend on
  document position, and removing the metamorphic invariant
  `D-2026-09-21-causal-runtime-before-golden-traces` asks for - under that
  rule, reordering two simultaneous entries changes the trajectory. It also
  sat badly beside `quantity-across-a-window`, which already declares
  intra-step path independence for a single entry.

What replaced it: everything completing on one state at one offset is one
step with a net effect, and a bound is evaluated on that net. Order-dependence
is decided exactly rather than assumed, by testing the two extremes that
bracket every ordering - every increase first against the upper bound, every
decrease first against the lower. If the net itself ends outside a bound every
ordering does, so that is the bound case it already was. If neither extreme
reaches one, no ordering does and the net stands. Only when one extreme
reaches a bound and the other does not is the group genuinely ambiguous, and
then the contract abstains with `ORDER_DEPENDENT_GROUP`, a fourth
`NOT_RECONCILABLE` reason saying to separate the offsets. **Order is expressed
as time, not as position in a document**, and `accounted_by` is sorted within
each instant so the whole record is order-independent - asserted by comparing
two documents that differ only in the listing order of one pair.

The statement covers the case where BOTH extremes reach a bound, which the
code always abstained on and the first draft left unspecified - T019's review
found it, and under this contract's own bump policy an unspecified case is
one where two conforming kernels may legitimately disagree.

One thing about that rule is worth knowing before reading its history: **the
argument that first motivated declaring it no longer holds**. It was declared
because freezing run inputs made the answer a blocking reason on a persisted
Draft. Proposal (e) then removed that blocking reason, so the rule reaches no
run at all. It still belongs in the contract - it decides what the scenario
detail surface reports and what a kernel must do at a shared instant - but a
later reader should not take "a persisted run says it" as current.

`EXECUTION_CONTRACT_VERSION` is 2 and **the bump policy is now written beside
it**: a version moves when the space of behaviours a conforming
implementation may exhibit changes, including when it narrows, and never for
wording. That is stricter than "the rule set is what is versioned", which the
first draft said, and the difference has a cost:
`D-2026-09-21-causal-runtime-before-golden-traces` makes a provenance
mismatch REFUSE playback rather than fall back, so a version that moved on a
prose edit would force regeneration of golden traces that were never invalid.
Under that test the reversal moves nothing further - version 1 left the
instant unspecified, both drafts narrow the same space, and nothing ever
conformed to the first draft.

The version move also closed the weak contract-version test for free: it now
compares against the constant, and the frontend fixture stays at 1 so the two
cannot be one literal by accident. The other two round-two findings are
untouched and unaffected: the unmeasured second initialization layer, and the
two forward constraints that live only in code comments.

What T019 leaves open, for the slice that meets it.

- **A `MODEL_RULE`-owned initial value has no carrier.** Review finding L9,
  narrowed by the user review: it no longer refuses, it blocks with
  `INITIAL_VALUE_NOT_RESOLVED`, so the person gets a Draft to inspect. What
  remains is that no profile in this build can carry such a rule. **T020A
  adds the carrier.** No shipped scenario declares the owner.
- **Narrowing a stored vocabulary makes older Drafts unreadable, and the
  store fails closed.** Removing a blocking kind stopped every Draft written
  before it from parsing, and because `create_run` lists the store to refuse
  a duplicate identity, that stopped run creation entirely until the stale
  documents were deleted. Free on unmerged data; not free after merge. There
  is no migration path and no per-document quarantine, and one unreadable run
  blocks the creation of every other. Checking identity by file name would
  avoid it and is refused on purpose: identity is never read back out of a
  file name. T020 reads this store and meets the same posture.
- **Four small things the re-review logged and left**, in the packet's
  residual risk with the reasoning: the frozen-table layout claim asserting a
  floor its wording outruns; the reason-set audit deriving membership from a
  name-suffix scan with a hand-written count, where the durable fix is
  exporting a vocabulary `frozenset` the way `BLOCKING_REASON_KINDS` is; a
  dead duplicate docstring in the execution contract tests; and the
  stale-vocabulary lockout's 503 saying the store could not be READ when it
  is readable apart from one document - the same collapse this project
  polices elsewhere, in copy this slice introduced.

Two lessons from the last two rounds, because both are about tests rather
than about runs.

**A reason's `subject` is what makes two rows two facts.** A state the
profile does not model was reported once per execution role, differing only
in which role the prose named, so a reader counting rows counted one problem
twice. Reasons are deduplicated on `(kind, subject)`, and a reason that
really is one per role carries the role in its subject.

**A guard's scope is part of its claim.** `tools/checks/run-setup.ps1`
described itself as protecting the product while scanning one folder, and a
reviewer disproved it with a function that passed 789 tests.

**An assertion that holds against a value the product cannot make proves
nothing about the product.** This slice met that three times: a fixture whose
loading sentence the screen never says, a fixture whose 503 message the
endpoint never sends, and a whole client tested only through a stub of its
own interface - so a duplicated sentence in the copy survived a full review
round. Stubbing an interface tests the caller; it never tests the thing that
implements it.

What T019 deliberately does not do: no execution, no step, no trace, no
staging, no Commit, no ingestion, no Replay, no analytics, no Findings. No run
inventory and no run detail surface either - the setup summary is returned
once and is not addressable, which is T020's to fix. A template-derived
scenario cannot have a run set up for it at all: a run is bound to a concrete
Site, and matching the Site's template provenance would be Site provenance
driving a run input.

## T020 - Runs inventory and Draft shell

What this slice settled in code.

**The Drafts T019 writes are now addressable.** `RunInventoryService` in
`backend/assetops_backend/runs/service.py` reads the SimulationRun port and
nothing else, and sorts newest-first on `(created_at, run_id)` so the order is
total rather than merely usually right. Two Lab routes serve it,
`GET /api/simulator-lab/runs` and `GET /api/simulator-lab/runs/{run_id}`, and
`frontend/src/shell/RunsFrame.tsx` and `RunFrame.tsx` render them. A
not-found run and an unreadable store are different screens, because they are
different facts about different things.

**`READY` states what it does not assert, on the record.**
`READY_DISCLOSURE` and `readiness_disclosure()` live in `runs/models.py` and
derive from the execution status, so the payload a caller reads and the panel a
person reads carry one sentence from one place - a screen composing its own
would be a second place for the claim to drift. It names the condition that
retires it, a conformance test deriving the supported states from a kernel,
never a slice number (`D-2026-09-22-expiry-follows-the-condition`). `BLOCKED`
gains nothing equivalent: there is no claim to qualify.

**`PUBLICATION_PROFILE` is the fifth answerer.** The cadence and both
publication-identity rows said `MODEL_PROFILE` answered them and the
publication profile did. The correspondence assertion could not have caught it
- its second half is a subset, so a new member passes silently - so the durable
guard is
`test_no_row_names_an_answerer_its_own_detail_contradicts`, which checks the
property rather than the three rows that carried the mislabel, plus a two
device-signal-source case where a count of three would have been wrong.

**`cadence_resolution` was deleted rather than renamed.** It was a total
function of `source_kind` and `cadence_minutes`, and storing it bought a
fourteen-line parser biconditional that checked a record against a restatement
of itself. `provenance.py` branches on the two fields instead. The run document
parser tolerates unknown keys, so every Draft written before this stayed
readable with the dead key ignored - which is also a strictness gap the
scenario and site parsers do not have, recorded in the packet's residual risk.
`EXECUTION_CONTRACT_VERSION` did not move: this is a run-record shape, not a
scenario-document one (`D-2026-09-22-contract-version-scope`).

**A form default is a thing the screen says it chose.** `RunSetupFrame` now
defaults the interval, the timestep, the seed and any profile selection with
exactly one option, and renders `.field-default` inside the field - "Default,
chosen by this form: X" - tied to the control by `aria-describedby`. The mark
stays after an edit, because "the form chose 15 and you typed 30" is more
useful than a mark that vanishes when it stops being true. The interval's
length is derived from the scenario's own last moment plus one timestep,
rounded to whole steps, because the interval is half-open. The clock is
injected (`App -> simulatorLabRoutes -> RunSetupFrame`) so a test can pin the
day. A value the scenario declares the run owns is never defaulted: that is an
initial world value, and a form supplying one is the fabricated default run
setup refuses over. M4's regression is restated as a property - no control may
hold a value the screen does not disclose - rather than as a list of fields.

**A ban on words became a ban on capability.** The gate suite forbade run
vocabulary on any control. After T020 a destination called "Runs", a row naming
a run identity and a disabled "Run this draft" all match that pattern
truthfully, so the rule is now: an anchor may match, a disabled button carrying
a reason may match, nothing else may, and on the two run surfaces no
non-anchor control may be enabled at all.

**A gate claim that measured an empty screen.** The gate suite rendered the app
with no run client, so both run surfaces showed "the run store could not be
read" - no controls at all - and every claim about what they may offer was a
claim about an empty set. Found by deliberate violation: an enabled Run button
passed the whole suite. The store is injected now. The lesson generalises: a
gate test that asserts an absence must first prove the screen rendered.

What T020 leaves open, for the slice that meets it.

- **No `READY` run is reachable through the product path.** The shipped model
  profile cannot execute the shipped Fuel Loss Event. Every `READY` claim is
  proved against a fixture run record written through the port
  (`run-b54689cf5dd14b5eb49e2e7a00f7275c` in `var/runs/` on this machine) or
  against an injected fixture in the UI suite. **T020B** makes the shipped
  scenario reach `READY` and should re-run the layout evidence then.
- **The inventory cannot disclose what `READY` does not assert.** The word
  stands alone in a table cell; the panel that qualifies it exists only on the
  detail. That is the thinnest point of the slice's presentation honesty and it
  is named in the packet's assessment.
- **The run store accepts unknown keys.** It is what kept older Drafts readable
  here, and it is a strictness gap. Closing it would turn a field deletion into
  a migration, so it was left.
- **`tools/layout-evidence.mjs` creates one Draft per run**, T019 behaviour,
  and nothing clears them. The inventory on a developer machine is dozens of
  near-identical blocked Drafts.

## T020A - Typed component properties and frozen Foundation answers

What this slice settled in code.

**A Foundation declares typed properties beside its ratings.** A `Rating` is
the one nameplate magnitude a component was sold with; a `ComponentProperty`
is a named, unit-carrying physical or control fact about the same component,
and a component may declare several. The vocabulary is closed in
`sites/models.py` - `COMPONENT_PROPERTY_DEFINITIONS` maps a key to its unit,
its kind and its display name, and `PROPERTY_UNITS` is derived from it so a
unit cannot outlive the property that used it. Four members today:
`tank-capacity`, `specific-fuel-consumption`, `reserve-state-of-charge` and
`minimum-runtime`. **The unit belongs to the key, not to the document**, so
`specific-fuel-consumption` in `L/h` is refused rather than stored as a number
that is true at one operating point.

`kind` is not authored. It is read from the vocabulary, so there is no
position a document could disagree from. `source` and `source_version` are,
following the `ControlAssumption.basis` precedent: a property copied from a
template keeps `TEMPLATE` and the template's version, so a later template edit
reads as drift rather than as something that reached back into a Site.

`foundation_parsing.parse_component_properties` is one validator for both
document families, called by the template parser and the Site parser, which is
the T014 rule applied to the new section rather than a new rule.

**The compatibility path is the absent key.** A Site document written before
this slice carries no `properties`, which parses to `None` - the document being
silent, never an empty list - and round-trips to an equal record. Nothing is
invented for it and nothing migrates it. `var/sites/mg-001.yaml` is untouched
and is the live proof: the shipped template moved to version 2 and MG-001 still
says version 1.

**A scenario parameter the Foundation owns has no value position.**
`D-2026-09-22-foundation-value-declaration`, closed at the structure: the rule
is keyed on the owner, because the owner is the only thing the document carries
that identifies these parameters - the binding that addresses a property lives
in the model profile and the scenario parser sees no profile. It reaches
`tank-capacity` as much as the coefficient. `ScenarioParameter.value` and
`InitializationInput.value` are now nullable and the unit is still required:
what kind of quantity the state is remains the scenario's to declare, and it is
what run setup checks the Foundation's property against.

**The bound declaration survived the value's removal.** Which state caps which
is a relationship between two world states and stays in the document; how large
the cap is is the site's. `declared_bounds` reports `(0.0, None)` for
`fuel-tank-volume` and that is the correct answer
(`D-2026-09-22-capacity-bound-source`). The bound test was re-proved where the
distinction still exists - the relationship in the parsed document, the value in
the frozen run - because after the change its control and its case both returned
`(0.0, None)` and it would have passed while proving nothing.

**`FoundationBinding` names the property.** It was a component type and a
rating unit, which can address exactly one fact per component; a generator
needing both its specific fuel consumption and its minimum runtime had nothing
to say which was meant. It is now `(component_type, property_key, unit)`.
Resolution takes the components of the declared type as the candidate set and
looks for the property on the single candidate. **It does not narrow candidates
to components that happen to declare the property**: that would let a second
tank answer for the one the binding could not address, which is the fallback
criterion 7 forbids, and a deliberate violation proved three tests catch it.

**Every Foundation-value failure blocks; none refuses.** Five cases, all
`INITIAL_VALUE_NOT_RESOLVED`: no binding, no component of that type, more than
one, the component declares no such property
(`D-2026-09-22-foundation-property-absent-blocks`), and the property's unit is
not the scenario's. `INITIAL_VALUE_ANSWERS_DISAGREE` was retired with its only
producer, because no document can state the number it compared against.
`.ai/ARCHITECTURE.md`'s naming rule is re-illustrated from the pair that
remains.

**The dispatch window forces an output and causes nothing.** Under `L/kWh` the
coefficient is not a rate over time, so the entry stops naming one: it declares
that the generator runs and at what output, `dispatched-output` is promoted from
`NON_EXECUTABLE_CONDITION` to a `FORCING_INPUT` on `generator-output-power`, and
the model rule owns the transition
(`D-2026-09-22-consumption-coefficient-unit`). The shipped profile gains
`generator-specific-fuel-consumption` and `generator-output-power`.

**`EXECUTION_CONTRACT_VERSION` is 3.** The narrowing reaches a document that was
already valid, so it moved. Version two has been published - frozen Drafts carry
it - and a stored run keeps the version it froze.

**A resolved parameter with no value is left out of `resolved_parameters`.**
`answered_by` there has two cases, `SCENARIO` and `RUN_INPUT`, and neither is
true of a Foundation-owned value. Its real answer is a
`FrozenInitializationInput`, which is the record with a shape for an absent
value and a reason beside it.

**On the screen**, Foundation renders the physical properties with the
components and the control properties beside the control assumptions, each with
its unit and the document and version that declared it, plus a note where a
reader meets the numbers saying nothing writes one to a machine or reads one to
decide anything. A declared physical property joins Key parameters beside the
ratings. A scenario parameter with no number says who answers and in what unit.

Two proof lessons, both found by deliberate violation rather than by review.
The absent-property test asserted `"example-store" in statement` and the state
key `example-stored-volume` contains it as a substring, so it passed against the
wrong message. And the layout run caught what no unit test could: the scenario
detail page rendered with no tables at all, because the client's guard required
a number for every initialization input and two now carry none. A fixture is not
a payload.

**What an independent review returned, and what it changed.** Three reproduced
correctness defects, all closed in the same slice.

A `SITE_FOUNDATION` parameter with `initializes: false` parsed and then
qualified for neither frozen collection - no answer, no row, no blocking
reason, and the run reported `READY`. The parser refuses the combination now,
because a Foundation-owned parameter states no number and the only record for
its answer is a `FrozenInitializationInput`, which is built from parameters
whose ownership initializes. **The concept the refusal turns away is
legitimate and has no carrier: a Foundation-answered coefficient that is not an
initial value. The slice that needs one adds the carrier and lifts the refusal
together.** The service exclusion that assumed representation now keys on the
frozen collection itself rather than on `value is not None`, and the
completeness property is asserted directly, because a paired-absence invariant
cannot catch a row that vanished.

The property validator admitted `nan` and `inf` - both are floats and neither
is less than zero - and the review wrote positive infinity into a real Site
store, then watched serving it raise. Finiteness is checked at the shared
boundary and a percentage is bounded by what its unit implies. The bound is
keyed on the unit rather than on the property: a per-property range table is a
general mechanism a four-member vocabulary has not earned, and the cost is
recorded - a later property that is a percentage above one hundred cannot be
added under `%` without deciding this.

`FoundationBinding.unit` was read by nothing at all. Three units must agree
now, and the binding-versus-scenario half is decided before the Site is
consulted, because no Foundation can reconcile a profile and a scenario that
disagree about the quantity.

**The substring weakness is a pattern, not two incidents.** It was caught once
during the build and survived two files away, where the review proved it by
mutation: `fuel-tank-capacity` contains both `fuel-tank` and `tank-capacity`,
so replacing every explanation with the bare state key still passed. Assertions
across this slice's tests now pin phrases a state key cannot satisfy.

**And the layout abort had a different cause than the packet guessed.** It was
attributed to the run store's create cost; the actual cause was the submit
script clicking a button the form disables until the configured site has been
read. Clicking a disabled button does nothing, so nothing was posted - which is
why the local run store did not grow across an aborted run. Both layout runs
complete now, 204 claims each. The run store's O(n) create is still real, is
the product's own persistence path rather than a developer-machine cost, and
wants an owner before T027.

**And what a second independent pass corrected.** R1 and R3 were confirmed
closed and the AC6 coverage kept; three bounded items remained, and two of them
are patterns rather than incidents.

`math.isfinite` converts its argument before testing it, so it **throws** on an
integer no float can hold rather than returning False. A 401-digit integer is
valid YAML inside the document size limit, so it reached that line through both
document families and surfaced as a raw `OverflowError` with no property
position. The conversion is now asked first, and refused by position. The
round-one function had the same hole one line further down, at the `float()`
that builds the record - **this slice relocated it rather than introducing
it**, which is worth remembering the next time a check is moved rather than
added. The identical hole existed one domain along in `scenarios/parsing.py`, where
`_reject_unusable_quantity(float(value), ...)` put the conversion one character
outside every numeric rule it was about to apply. It was flagged rather than
quietly fixed - the round was bounded - and then closed in a round of its own
once the user approved. **That makes this a pattern with two confirmed
instances rather than two mistakes: a check moved in front of a conversion,
without the conversion itself being covered, carries the hole with it.** The
function there now takes the authored number and returns the converted one, so
the conversion happens inside the thing that owns the numeric rules.

**And the pattern is wider than the two that were fixed.** Looking for a third
instance while closing the second found four more, all reproduced: the run
setup request parser (`runs/parsing.py` `_quantity`, reachable from a request
body, so a 500 where a `REQUEST_INVALID` refusal already exists), the run
document reader (`_real`), and the rating parser in both Site document
families. None is T020A's surface and none persists a bad value; each is the
inspectable-error half, and each is one `try`/`except` plus a test. They are
flagged in the packet's residual risk rather than swept, because the round was
scoped to one call site - but the honest generalisation is that **this codebase
validates numbers with `float(value)` written inline, and every place it does
carries the same hole.**

A comment claimed the run record would refuse a valueless resolved parameter
loudly. It does not: `FrozenParameter` is annotated and not validated, and
`SimulationRun.__post_init__` checks initialization rows rather than resolved
parameters. The boundary that holds is `YamlRunStore.create_run` re-reading its
staged document. **The comment is corrected and `test_run_store.py` now pins
both halves**, including the dataclass limitation, so a later slice that makes
`FrozenParameter` validate has to delete a test that says it does not. A guard
promised in a comment and absent in code is worse than no guard, because the
next author builds on it.

**The assertion-satisfied-by-adjacent-text pattern reached three instances in
one slice.** After the backend sweep, a frontend test still claimed to prove a
bound survives rendering while matching text from the state column - and
`ScenarioFrame` renders `parameter.bounds` nowhere. It is renamed to what it
tests, and a second test asserts the bound is genuinely absent from the
declaring row, scoped to that row because the state name appears elsewhere in
the same table. Three instances is not three mistakes; it is a habit of
asserting on identifiers that appear near the thing being claimed, and the
fix that generalises is to assert phrases and to scope absence claims to the
element that would carry the thing.

The percent range is recorded as this vocabulary's policy rather than as a
property of the unit: a loading factor of 120 % is an ordinary number, and what
is true is only that the single `%` key here is a fraction of what a component
holds.

What T020A leaves open, for the slice that meets it.

- **Same-type component addressing is T020A1.** An unqualified binding resolves
  exactly one candidate or it blocks. Two tanks block today, with the ambiguity
  named.
- **The shipped Fuel Loss Event still cannot reach `READY`**, on any site. The
  three forcing states the profile does not model remain, and lowering them is
  **T020B** under `D-2026-09-22-forcing-state-requirements`.
- **Option C is still a follower.** No profile carries a model-supplied initial
  value; a `MODEL_RULE`-owned value blocks. Its trigger is the first model rule
  needing a Foundation value without a scenario asking for it.
- **`var/runs` holds 72 local Drafts and `create_run` is O(n) in that count.**
  It re-reads and re-parses every stored run twice to refuse a duplicate
  identity; one create measures 3 to 7 seconds here depending on load. That is
  T020's recorded behaviour biting - the layout script writes one Draft per
  visit and nothing clears them - and it is the PRODUCT's persistence path, so
  calling it a developer-machine cost understates it. It needs a bounded fix
  with an owner before T027's internal demo, preserving the duplicate and
  atomic-write guarantees.
- **A Foundation-answered value that is not an initial world value has no
  carrier**, and the scenario parser refuses the declaration rather than
  letting it vanish. The first law that needs one adds the carrier and lifts
  that refusal together; it is the same trigger as option C. The refusal
  message tells an author how to fit today's schema and does not name that
  third route - a reviewer's suggested wording improvement, carried.
- **`reconcile_reported_observations` reports a wider gap**, 310 L against the
  readings where it reported 254 L, because the document no longer carries the
  generator's consumption. That is the honest projection of a document that has
  stopped carrying a machine's physics, and closing it is T021's kernel.

## T020A1 - Addressed bindings from scenario to frozen initialization

A world state is now named by an ADDRESS rather than by a semantic key alone.
`StateRef` in `backend/assetops_backend/state_refs.py` carries three things: the
semantic key, the scope it is claimed at (`SITE` or `COMPONENT`), and, for a
component-scoped claim, which component. It sits at the package root beside
`document_bounds.py` and for the same reason - the rule is about addressing,
not about scenarios, profiles or runs, and `runs/profiles.py` may not import
the Site record family at all.

**The authored spelling is one string with three forms.** `fuel-tank-volume` is
component-scoped and unqualified, `fuel-tank-volume@north-tank` names the
component, and `site:site-load-demand` is a fact about the installation.
`component:` is accepted as the bare form said out loud and renders back as the
bare form. A bare key means COMPONENT and never SITE. **What makes that direction safe is
enforcement in `runs/service.py`, not the spelling**, and the property has
edges that have to be stated with it or the statement goes false again - it did
three times. A COMPONENT-scoped reference must identify one component of the
bound Site before that run is READY, whoever answers for its number, whether or
not it has one, and at either requirement level. A `site:` reference poses no
component question and is never asked one, though the profile must still model
the state at that scope. And whether this build can MODEL a state is a separate
obligation that stays requirement-sensitive: unsupported and REQUIRED blocks,
unsupported and OPTIONAL is recorded and proceeds. The other direction of the
default would have turned a statement about one machine into a statement about
the installation with nothing that could notice.

One parser serves both document families, which is what makes a frozen record
reconstruct to the address it was written from. `addressed_key` is the
canonical spelling and the identity everything keys on: duplicate detection,
blocking-reason subjects, dedup, the frozen row on the screen, and the run
document's `state_key` field. A run frozen before this slice carries a bare key
there and reads back as what it was - an unqualified component reference - so
the old Drafts stay inspectable.

**The address is stated in the document, the scope is stated twice on purpose.**
`SupportedState` gains a `scope` and still no component id: a profile says what
KIND of claim a state is, the scenario says which instance, and selecting the
same profile for a second Site addresses that Site's components. When the two
disagree the run blocks rather than guessing, and the disagreement is checked in
two places because they reach different declarations - the Foundation resolver
sees only the initial values a Foundation owns, and a scenario-owned forcing
input never goes near it. A `SITE`-scoped supported state may not carry a
`FoundationBinding` at all, refused in `__post_init__`, because such a binding
names a component type and could never resolve.

**Resolution has nine blocking cases and no refusal** - this said eight and
listed nine, and a backup review counted them; the nine are split across the
two functions as the later correction sections describe. Scope disagreement;
no binding; the binding's unit against the scenario's; a named component the
Foundation does not declare; a named component of the wrong type; no candidate
of the bound type; more than one candidate and no selector; the property
absent; the property's unit against the binding's. The candidate set is the components
OF THE DECLARED TYPE and never the components that happen to declare the
property - narrowing it would let a second tank answer for the one the address
could not reach, which is the fallback addressing exists to prevent. Every
reason's subject is the ADDRESS, so two tanks are two rows rather than one
deduplicated row with a hole behind it.

**A resolved input freezes the component that answered, even when the author
named none.** An unqualified `fuel-tank-capacity` against a one-tank site
freezes as `fuel-tank-capacity@fuel-tank`, so a later reader does not have to
re-run the resolution against a Foundation that may have been reordered since.
An unresolved input keeps the address exactly as authored, because nothing chose
a component and naming one would put an asset's identity beside a value it did
not supply - and that is also what lines it up with its blocking reason.

**The parser gained one rule that addressing made necessary.** A document may
not declare both `x` and `x@north-tank` as initial values: an unqualified
reference may resolve to the very component already named, so the two would be
one initial value with two owners, which the duplicate rule can no longer see
and run setup can no longer tell apart. Mixing the forms for one state key is
refused with the repair named.

**What moved to the addressed grain, all of it:** duplicate initialization
detection, the entry-versus-parameter state agreement, the state-effect
agreement, `declared_bounds`, `reconcile_reported_observations`,
`initialization_inputs` ordering, executable-input gathering, and
`SimulationRun.__post_init__`'s never-absent invariant. That last one is the
T020A defect at this slice's grain: keyed on the semantic key, the north tank's
blocking reason would explain the south tank's absent value - one reason, two
holes, and the second hole invisible.

`requirement_conflicts` reports an address and role a document states two
requirements for. Detection, not refusal: `_executable_inputs` keeps taking
`REQUIRED`, which can only block a run that would otherwise have run, and
T020B owns what the product finally does. Two components at different
requirements are NOT a conflict - they are two independent requirements, which
is the whole slice.

`EXECUTION_CONTRACT_VERSION` moved three to four. The same unedited Fuel Loss
Event against the same single-tank Foundation freezes
`fuel-tank-capacity@fuel-tank` where version three froze
`fuel-tank-capacity`, so the resolved identity of a run of an unchanged
document is different - the test `D-2026-09-22-contract-version-scope` sets.
`refuse_incompatible_execution` is the run half: a Draft frozen under another
contract stays readable and is refused execution rather than reinterpreted.
Nothing executes yet, so its one caller today is `runs/provenance.py`, which
puts the refusal on the run's own Execution contract row - a guard with no
caller would be the declaration-nothing-checks defect T020A's review found in
`FoundationBinding.unit`.

Run detail names the address on each frozen row and carries the reason an
unresolved value is missing IN the row it is missing from, matched on the
address. The blocked table still lists every reason; pairing two of them to two
rows that differ by a component id was the work this removes.

`config/site-templates/twin-tank-mini-grid-150kw.yaml` is a second shipped
archetype: two fuel tanks at 500 L and 800 L, two generators at 0.311 and
0.285 L/kWh, `load-res` and `load-mill`, and two fuel level sensors reporting a
signal spelled identically on both tanks - which only the declared mappings tell
apart. The differing values are load-bearing: two equal capacities would let a
resolver pick either component and still look right.

The shipped Fuel Loss Event is migrated. Every executable declaration names
what it is about - the tank, the generator, or the site - and it is STILL
BLOCKED on the three states the first profile does not model. Addressing is not
readiness and T020B owns the difference.

### T020A1 correction round: the address obligation belongs to the reference

An independent Codex review returned the slice with four defects and two
overclaiming tests. All six are closed; a fifth finding is carried by the
reviewer's own judgement. What follows is what changed and, where it matters,
what the first attempt got wrong - because three of the four are one mistake
wearing different clothes.

**The mistake.** Address resolution was written inside the Foundation value
lookup, so a reference was only ever resolved when the Site's Foundation was
the thing answering for its number. Everything else - a `SCENARIO_INPUT` or
`RUN_OVERRIDE` initial value, every forcing input, every reported observation
- carried its authored reference straight into the frozen run. So
`example-stored-level` with no selector, and `example-stored-level@ghost-tank`
naming a component the Foundation does not declare, both froze and reported
READY. The rows were present, so this was not T020A's disappearance defect: it
is the obligation beside it. **Who supplies the number and which asset the
number is about are two different questions, and only the first was asked.**

`resolve_state_addresses` is now one pass over every reference the document
declares - timeline entries, parameters on them, public parameters and the
state a bound names - run before anything is frozen, with the Foundation
lookup consuming its answer instead of doing the choosing. The obligation
cannot be attached to one owner again because it is not reached through one.

**`STATE_ADDRESS_NOT_RESOLVED` is a seventh blocking kind**, not the sixth
reused, because an initial value is not the only thing an address is needed
for. The two do not partition cleanly and a later reader must not act as
though they did: a missing binding and a scope disagreement both report
`INITIAL_VALUE_NOT_RESOLVED` before any asset has been looked for, so all that
kind means is a failure to obtain the initial value. Both carry an addressed
subject, which is what holds a reader's diagnosis together across them. A forcing input has no initial value to be
unresolved and still has to say which machine it forces, so naming this after
initial values would have been a kind unable to describe half the references it
reports on. The cases that moved to it: a named component the Foundation does
not declare, no candidate of the bound type, more than one candidate. What
stayed: no binding, the binding's unit against the scenario's, a named
component of the wrong type, the property absent, the property's unit.

An unqualified reference resolves only through the component type the selected
profile's `FoundationBinding` names for that state, and blocks when the profile
declares no binding to name one. Nothing reads a component type out of the
spelling of a state key.

**Unsupported-input diagnostics carry the address too.** Missing-state and
unsupported-role subjects and the optional record used the bare semantic key,
so two required declarations about two tanks deduplicated into ONE row and two
optional ones were identical in every field. The line now drawn, and both
halves are load-bearing: the profile is ASKED about the semantic key, because
it models a kind of state and knows nothing about how many a site has; what it
REPORTS is addressed, because the thing reported on is a declaration and there
were two. One address in two roles is still one missing-state row.

**`requirement_conflicts` resolves before it groups**, and so takes the Site
and the profile. On a one-tank site, `x` REQUIRED and `x@north-tank` OPTIONAL
are two authored spellings of one asset; grouped by spelling the function
returned nothing while advertising detection at the resolved grain. The
parser's qualified/unqualified refusal does not reach it either - that rule
inspects parameters that initialize, and one of the two does not.

**The state-reference grammar is matched with `fullmatch`.** It was anchored
with `^` and `$` and matched with `.match`, and Python's `$` also matches just
before a final newline - so a selector spelled `north-tank` followed by a line
feed satisfied it and kept that character inside the canonical identity. An
identity that looks like `north-tank`, is not equal to it, and which a YAML
block scalar supplies without an author noticing. Refused rather than
stripped, at both entry paths: trimming would turn one authored identity into
a different one silently.

**The shared scenario fixture is addressed.** It named bare `example-stored-volume`
and `example-demand` and passed only because the obligation was missing; it now
names `@example-store` and `site:example-demand`. A candidate-selection test
readdresses the whole document rather than one parameter, because two spellings
of one state produce two reasons and make a test about two things.

**Two proof overclaims, both found by the reviewer's mutations.**
`test_a_property_in_another_unit_than_the_binding_blocks` swapped the property
key, so the resolver reported a missing property and returned before comparing
the property's unit with the binding's - both unit tests passed with that guard
deleted. And `frozen_by_address` keyed rows into a dict before the whole-set
assertions ran, so a conflicting extra row disappeared into the mapping and
left two tests green. The helper now asserts multiplicity on the tuple before
keying, so every caller gets the check, and the two named tests count rows and
match parameter identities as well as addresses.

**Carried, not fixed: a hand-authored frozen document may hold two rows for one
address.** `runs/parsing.py` reconstructs the initialization tuple without a
uniqueness check and `SimulationRun.__post_init__` checks absence and status
but not uniqueness. The reviewer judged it inherited rather than introduced and
carried it under `D-2026-09-22-milestone-speed-over-purity`; the supported
setup path cannot produce one. **T021 must not reconstruct with
last-write-wins**, and the guard, when built, must keep reading valid older
documents.

`EXECUTION_CONTRACT_VERSION` did not move again. Version 4 has not been
published outside this branch, and the reviewer confirmed corrections inside
an unpublished version do not require another increment.

Also carried out of the review, named rather than swept: the second shipped
archetype's Foundation and SLD have not been measured at any viewport, and the
run-detail browser evidence is not evidence about the diagram it draws.

### T020A1 second correction round: visiting is not resolving

A second independent review closed five of six returned items and found three
more, all of them one sentence: **do not equate visiting a reference with
having resolved it.** The common pass was exhaustive as an ENUMERATION - every
reference was collected and looked at - and the round-two entry above read as
though that settled the matter. It did not.

**A reference now leaves `resolve_state_addresses` in one of three states**,
and naming the third is the fix. Two branches used to record a reference as
settled while checking nothing, on the assumption that `_support_for` would
report it; `_support_for` is asked about EXECUTABLE declarations, so a
reference written only as a bound target reached neither check and
`unmodelled-volume@ghost-tank` came back READY with no reasons and persisted.
The states are RESOLVED (it names one component, checked here), REFUSED (it
carries a reason), and DEFERRED - and `deferred_to_support` is set only when
the address really does appear among the executable inputs `_support_for` is
driven from, read from `_declared_requirements` rather than assumed.
`ResolvedAddress.is_resolved` was "no reason", which reported precisely the
unchecked cases as resolved; it now means what its name means.

**Existence is checked before the profile is consulted at all.** Whether this
Foundation declares a component with that identity needs no state vocabulary,
so asking it first means an explicitly addressed reference is checked even
when it names a state this profile does not model. That is what closes the
bound-only route without inventing a bounds mechanism.

**The binding's component type moved into the pass** with the rest of
selection. It had stayed in the Foundation's number lookup, so naming a
generator for a tank state blocked under `SITE_FOUNDATION` and froze 100 L
against that generator under `SCENARIO_INPUT` - the same ownership-dependent
obligation the previous round removed, one position further in. It is not
duplicated: by the time `_resolve_foundation_value` runs, the component is of
the bound type or there is none.

**A regression the previous round introduced, and the rule that prevents the
class.** Every owner's row moved onto the resolved address while the
MODEL_RULE branch still emitted its reason against the authored one. On a
one-tank Site a bare model-owned reference resolves to `@north-tank`, its
number is absent because no profile carries a model rule for it, and the
mismatch made `SimulationRun.__post_init__` raise - so a Draft that should
have been BLOCKED and inspectable was no Draft at all. **The missing value,
the reference frozen beside it and the explanation for it are kept at one
grain**, here and in `_resolve_foundation_value`.

**An unresolvable row is frozen ABSENT for every owner**, which reverses a
round-two decision. That round kept the scenario's number on such a row,
arguing the document really does state it. Two things were wrong: a frozen
initial value is the initial value OF a world state and an unresolvable
address names none, so the screen showed a quantity beside an asset that
cannot carry it; and it made the record behave one way for a scenario-owned
or run-owned value and another for a Foundation-owned one, which is the
ownership-dependent treatment these rounds exist to remove. My own new test
caught it.

**What the tests learned, which is the part worth carrying.** The round-two
test asserted that the pass VISITED every reference - the assertion that was
already passing while the defect was live.
`test_nothing_is_deferred_to_a_check_that_never_sees_it` asserts the property
that was missing instead: for every reference the pass declines to answer
itself, its address must appear among the executable inputs `_support_for` is
driven from. It counts the deferrals it saw and fails if there were none, so
it cannot pass because the branch was never taken. An enumeration assertion
survives the mutation that makes a deferral blind; this one does not.

Two prose claims were corrected at the places they were made rather than only
in a later section: the blanket safe-default guarantee about a bare key, in
`state_refs.py` and in the authored-spelling paragraph above, which is a
property of the enforcement in `runs/service.py` and not of the spelling; and
the claim that the two blocking kinds partition cleanly, in `models.py` and
above, which they do not - a missing binding and a scope disagreement both
report `INITIAL_VALUE_NOT_RESOLVED` before any asset has been looked for, so
that kind means only a failure to obtain the initial value.

`EXECUTION_CONTRACT_VERSION` did not move. Version 4 remains unpublished
outside this branch.

### T020A1 third correction round: two obligations, asked of every spelling

The Codex Reviewer was out of quota and `.ai/ROLE_CONFIG.md`'s backup rule put
a Claude reviewer on the slice. It found two things three Codex passes had not,
both the same mistake as the previous two rounds, one spelling and one
requirement level further in.

**The SITE branch returned before the profile was consulted.** So the check
round three added to close bound-only references never ran for a `site:`
spelling: `site:unmodelled-volume` as a bound target came back READY with zero
reasons and persisted, and so did `site:example-stored-volume`, a site-wide
claim on a state the profile carries per component.

**The deferral handed the whole reference to `_support_for`, which blocks only
on REQUIRED.** So an unqualified `unmodelled-level` marked OPTIONAL froze 200 L
against no asset and reported READY. Neither party enforced the address
obligation: the resolver had delegated it, and the delegate answers a different
question.

**The structure that came out of it is the durable part.** Two independent
obligations, asked of every reference:

- **does it name one component of this Site?** Component-scoped only, never
  deferred, never requirement-sensitive - because `_support_for` does not
  answer address questions at any requirement level. A `site:` reference poses
  no component question and is never asked one.
- **can this build model the state, at that scope?** Every scope. Deferred to
  `_support_for` when it is really asked, reported here when it is not, and
  requirement-sensitive as it always was: unsupported and REQUIRED blocks,
  unsupported and OPTIONAL is recorded and proceeds.

Conflating them produced both findings. Keeping them apart is what makes the
universal claim about component references finally true, because the things
that used to falsify it are now visibly the other obligation's business.

**The F2 decision was mine and I enforced rather than exempted.** An exemption
by requirement level would have reintroduced what the absent-row rule removed a
round earlier - a record that behaves one way here and another there - and the
requirement level was never the cause: it only decides whether a SUPPORT
failure blocks. The cost is one narrow case, an unqualified reference to an
unmodelled state marked OPTIONAL, which now blocks with the repair named.
`test_optional_still_means_the_run_may_proceed_without_support` pins the half
that stays requirement-sensitive, so OPTIONAL was not quietly promoted.

**The test had a hole the same shape as the code's, and that is the lesson.**
The enforcement assertion whitelisted `address.authored.scope == "SITE"` and
the parametrized bound test had five component-spelled targets and no `site:`
one. **A test written to prove enforcement must not exempt what the code
exempts**: it cannot fail where the code is wrong. Both holes are closed, and
the proof is an experiment rather than an assertion - the corrected assertion
fails against the old code, and with the escape restored it goes blind again
while only the new parametrized cases fire.

Two prose corrections. `_resolve_foundation_value` said "Five cases" over a
list of six, one of which its own later comment says moved out; the count and
the list are now stated together with the five `return blocked(...)` calls they
describe, and the four that moved are named as the address pass's.
`blocking_statement` was documented as appearing "only on a row whose value is
missing" while the execution-contract row, which has a value, carries one; the
docstring now says what the field means - why THIS row stops the run - and
names both kinds of row.

`EXECUTION_CONTRACT_VERSION` did not move. Version 4 remains unpublished
outside this branch.

What this leaves open.

- **T020B still owns readiness.** The three unmodelled forcing states are
  unchanged, and so is `D-2026-09-22-forcing-state-requirements`. It also owns
  what a requirement conflict finally does; `requirement_conflicts` reports them
  and nothing acts on one.
- **Nothing executes, so `refuse_incompatible_execution` has one caller.**
  T021's kernel is the second and calls it before it initializes anything.
- **The scope a state is claimed at is declared twice**, once per scenario
  reference and once per profile state. That is deliberate and the
  disagreement blocks, but it is two places a future slice must keep true.
- **The shipped Fuel Loss scenario's upper bound is INERT, and T021 is the
  first thing that will meet it.** `declared_bounds(fuel-loss-event)` returns
  `{'fuel-tank-volume@fuel-tank': (0.0, None)}`: the upper value is missing
  because `scenarios/execution.py` skips any parameter whose value is not a
  float, and a Foundation-owned parameter states no value by design under
  `D-2026-09-22-foundation-value-declaration`. So the tank capacity that
  bounds the stored volume never reaches the bounds map, and the only
  authored upper bound in the shipped document is absent from the projection
  of it.
  The identical guard is at `b004f58`, so this is inherited rather than
  T020A1's, and AC12's evidence remains true about the authored DOCUMENT -
  the declaration survives, addressed to the right tank. What does not
  survive is its VALUE, which now lives on the frozen run instead.
  **T021 is the first consumer of bounds** and must read the capacity from
  the frozen initialization input rather than from `declared_bounds`, or
  teach `declared_bounds` to take the frozen answers. A backup review found
  this; it is recorded rather than fixed because fixing it is the kernel's
  design decision about where a bound's number comes from.
- **A hand-authored frozen document may hold two rows for one address**, and
  T021 must not reconstruct with last-write-wins. Carried by the review, with
  the acceptance suite no longer claiming otherwise.
- **The twin-tank archetype's Foundation and SLD are unmeasured** at any
  viewport. The browser evidence is about MG-005's run detail and says nothing
  about the diagram that archetype draws.
- **`var/runs` now holds 102 local Drafts and `create_run` is still O(n)** in
  that count, unchanged from T020A and still wanting a bounded owner before
  T027. This slice added twenty-one Drafts to it, most of them written by four
  layout evidence runs.
- **The five inline `float(value)` overflow sites in
  `.ai/MILESTONE_REVIEW_BACKLOG.md` are untouched and no sixth was added.**
  `state_refs.py` converts no numbers.

## T020B - Reachable Fuel Loss readiness and boundary contract

What this slice settled in code.

**The shipped Fuel Loss Event reaches `READY` through the form and API path.**
Three states blocked every run of it, and they turned out to be three different
problems rather than one missing capability
(`D-2026-09-22-forcing-state-requirements`).

`site:site-load-demand` and `site:plane-of-array-irradiance` are now `OPTIONAL`
at all five positions in `config/scenarios/fuel-loss-event.yaml`. `REQUIRED`
means an executor must MODEL this to run this scenario, and producing the fuel
trajectory needs neither: the document declares the generator's dispatch
directly, so nothing computes it from load and PV, and a kernel that modelled
them would be computing dispatch. Both stay declared and reach the run as
`UnsupportedOptionalInput` rows, named on the run's own screen. What consumes
them electrically is T024.

`fuel-level-reporting-availability@fuel-tank` was never the model profile's to
answer, and that is the structural half of the slice. `runs/profiles.py` gains
`REPORTING_PATH_STATES`, a closed vocabulary of states that are facts about the
reporting PATH rather than about the world, and `SupportedReportingState`, which
a `PublicationProfile` declares them with. A `ModelProfile` that declares one is
refused at construction and a `SupportedReportingState` naming a world state is
refused the same way, so exactly one profile answers for each state.

**The authority is read from the state, never from whichever profile replied.**
`state_authority(state_key, model, publication)` returns a `StateAuthority` -
who answers, its detail text, and what it said - and the routing is by
vocabulary membership rather than by asking the model profile first and falling
back. That distinction is the whole value: "ask one and then the other" makes a
world state the model profile has not got round to look like a reporting-path
state, and sends the reader to the wrong profile. So a run whose publication
profile declares no reporting capability blocks with a reason naming THAT
profile and saying a model profile cannot answer for it.

**F5 is settled, and it was two functions ordering two facts oppositely.** An
unqualified reference to a state the profile models site-wide reached the
no-binding refusal, because a binding is only read when the scopes agree and a
site-wide state has no binding by construction. The statement told the author to
add an address or find a profile that declares the binding; the repair is to
write `site:` in front of the key. `_resolve_foundation_value` ordered scope
before binding and said so in its docstring, so one function contradicted the
other's stated rule.

Three things fix it and the third is the durable one. The scope check runs first
in `resolve_state_addresses` too. `scope_repair` computes the one string an
author types, from the two scopes, and `scope_disagreement_statement` is the
single wording all three sites use - the message was duplicated three times with
its own hedges in each. And all three ask `state_authority`, so an ordering
mistake is now one mistake rather than a disagreement between functions that
never read each other.

**One blocking row per address.** `_decide` takes the address resolutions and
skips the support question for an address the resolution pass already refused.
The obligations stay independent and a declaration can fail both, but a
reference that names no asset has nothing for a profile to be asked about, and
the second row added no repair the first did not state. Nothing is traded: the
address obligation is not requirement-sensitive, so such a run is `BLOCKED`
either way.

**A requirement conflict refuses, at the earliest layer that can decide it.**
The `REQUIRED`-wins collapse T019 invented is gone rather than kept as a
fallback, because the fallback is what made this lowering unobservable - demand
is declared at three positions, so raising one kept the state required. Two
levels on one AUTHORED address need only the document, so
`_validate_execution_requirements` in the scenario parser refuses it. Two
spellings that resolve to one address need a Foundation, so
`_refuse_requirement_conflicts` does, as `EXECUTION_REQUIREMENT_CONFLICT` with
no `run_id` allocated. `_declared_requirements` raises
`UnresolvedRequirementConflict` if one reaches it, so there is nothing silent
left to restore the old behaviour.

**The execution contract publishes what a kernel actually has to do.**
`scenarios/execution.py` gains `BOUNDARY_CYCLE`, the nine phases of v4 section
6.1 with declared ordinals - it replaces "observe after the step", which said
which side of a step a sample falls on and nothing about where a controller, a
resolver or an invariant check sits. `OBSERVATION_RULES` with `READING_CLASSES`
states what a reading timestamped `T` describes, per class: a stock is sampled
at `T` after that instant's events, a rate summarises `[T-dt, T)`, an interval
reading is UNAVAILABLE at the run's first boundary absent a declared historical
window, and a controller's view is not the published observation and no
reporting cadence becomes a control cadence. Two new `DISPATCH_RULES` declare
the linear window ramp between a window's own two endpoints and that a forcing
outside its window is UNAVAILABLE rather than zero or held.
`BOUND_POLICY_STATEMENTS` says what each policy commits a kernel to, which is
where `BOUNDED_AND_RECORDED` finally says the run CONTINUES and later causes
apply to the bounded value.

`quantity-across-a-window` was amended in the same pass, because it said the end
state is the same "whether a kernel applies it in one step or spreads it across
the window" and the ramp rule forbids that for every instant inside. Two rules
of one contract saying opposite things is what the amendment prevents.

**All of it is on a screen.** The contract payload carries `boundary_cycle`,
`observation_rules` and a `policy_statement` per bound case, and
`ScenarioFrame.tsx` renders two new tables and a note per policy. A contract
that reaches a kernel author only through a design document is not published.

**`EXECUTION_CONTRACT_VERSION` moved 4 to 5.** Version 4 is on `main` and local
Drafts carry it, so the unreleased-version doctrine that let three amendments
share version two does not apply. Three of this slice's changes reach a document
version 4 accepted: the conflict refusal refuses one that was valid, the
authority move changes the outcome of the shipped document against the same pair
of profiles, and the four declared semantics narrow what a conforming kernel may
do. The `OPTIONAL` lowering is authored content in one document and moves
nothing by itself.

**The fixture-only `READY` proof is retired as the demonstration.**
`backend/tests/test_execution_contract_alignment.py` reaches `READY` with the
shipped document against a Site instantiated from the shipped template through
`SiteCreationService`, and asserts the frozen answers, the two recorded optional
inputs, the disclosure and the contract version on that run. `MG-006` in
`var/sites/` is the same case through the real HTTP path, with
`var/scenarios/fuel-loss-event-mg006.yaml` naming it, and
`run-9f74603b06384126a627a5339fc78fbe` is the `READY` Draft the owner reviews.
T020's fixture run record was left in `var/runs` as user data.

What T020B leaves open, for the slice that meets it.

- **`supported_reporting_states` has no falsifier either.**
  `LAB_PUBLICATION_PROFILE` declares it can model the reporting path being
  unavailable, and nothing in this build can suppress a reading. It is the same
  shape as the `supported_states` entry already in
  `.ai/MILESTONE_REVIEW_BACKLOG.md`, and the observation transform is its
  falsifier: it is what makes the declaration true or false. The readiness
  disclosure covers both, which is why it stays - **but it did not when this
  entry was first written, and the entry said it did.** T020B's independent
  review caught it: `READY_DISCLOSURE` named only the model profile's supported
  states, `models.py` was not in the slice's diff at all, and three documents
  asserted a coverage that did not exist. The correction round widened the
  disclosure to name both profiles, both supported sets and both retirement
  conditions. It was dangerous rather than untidy because those two conditions
  fall on different slices - a kernel for one, the transform for the other - so a
  disclosure naming only the first would have been retired by the kernel slice
  while the second claim stood unfalsified.
- **Two blocking rows can still share a subject across two kinds.** An
  addressed reference whose scope disagrees with the profile produces
  `INITIAL_VALUE_NOT_RESOLVED` from the Foundation lookup and
  `STATE_NOT_SUPPORTED` from the support question, both about one address. The
  F5 item this slice owned was the address-versus-support pair and that one is
  closed; this pair predates T020A1 and has the same fix on both rows. Recorded
  in the backlog rather than fixed.
- **The reporting-path vocabulary has one member**, which is the honest size of
  it, and the routing is unreachable if it ever has none - asserted, so it
  fails rather than passing over an empty set. A second reporting-path state
  arrives with T022's observation transform.
- **`var/runs` now holds 127 local Drafts and `create_run` is still O(n)** in
  that count, unchanged from T020A1 and still wanting a bounded owner before
  T027. This slice added twenty-five: one is the `READY` MG-006 Draft the owner
  reviews, and twenty-four are `BLOCKED` Drafts of the shipped document that
  the layout evidence tool creates, one per run-setup visit across five runs of
  it. The tool has created a Draft per run since T019 and nothing clears them.
- **An `UnsupportedOptionalInput`'s statement is PERSISTED on the frozen run**,
  not computed when the run is read. That is correct - a frozen run records what
  it said at setup - and it has a consequence worth knowing: the review round
  that corrected this copy could not be seen by reloading an existing Draft, so
  the demo Draft was regenerated as
  `run-9f74603b06384126a627a5339fc78fbe`. It is the same shape as the
  instruction that T021 regenerates rather than executes a Draft frozen before
  its own build, one layer down: any slice that changes a persisted statement
  changes it for new runs only.
- **The five inline `float(value)` overflow sites are untouched and no sixth was
  added.** Nothing in this slice converts a number.

## T021 - The independent causal Fuel Loss kernel

What this slice settled in code. **A frozen READY Draft of the shipped Fuel Loss
Event now executes**, in a simulator that cannot see the product, and produces a
private trajectory whose tank movement follows dispatch, consumption and events.

### Where things live, and the rules that keep it that way

Three Python trees are importable and a fourth is not.
`contracts/assetops_contracts` holds what both sides of the truth barrier must
agree about: the versioned execution semantics (moved unchanged from
`scenarios/execution.py`), the frozen-input schema a kernel consumes, the private
trajectory, the execution-failure vocabulary and the BLAKE2b-256 identity domain.
`simulator/assetops_simulator` holds the kernel and the fuel pack.
`host/execution_adapter.py` is the composition leaf, and nothing imports it.

The backend re-exports every moved name, so a product caller still reads one
module and the scenario detail screen renders the contract's own objects rather
than copies: `is` holds, asserted. What stayed in `scenarios/execution.py` is
everything that reads a `ScenarioDefinition`.

`tools/checks/dependency-direction.ps1` gains two rules: nothing imports `host/`,
and the neutral contracts import neither side. Both patterns are anchored at the
start of a line, because these modules discuss both sides at length in prose and
a sentence naming a package is not an import of it - proven narrow by a probe that
inserts an INDENTED import and watches it caught.

**One thing was deliberately not moved.** `StateRef` stayed in the backend and the
neutral boundary carries canonical address TEXT - `fuel-tank-volume@fuel-tank`,
`site:site-load-demand` - which is what a frozen run document persists and what
every comparison in the product already keys on. Moving the record would have
relocated a validator with twenty callers and bought this slice no behaviour.

### The contract is conformed to, not resembled

Three mechanisms, each because the alternative is a claim nobody checks.

**The phase order is read from `BOUNDARY_CYCLE`.** `_PHASES` maps each declared
`phase_id` to the function that runs it and the loop visits them in the contract's
`sequence`. A phase added to the contract stops this kernel until it is
implemented rather than being skipped, which is what `BoundaryPhase.sequence`
being "the contract, not the tuple order" looks like when something consumes it.

**The two dispatch formulas are executable, in the module that publishes the
sentences describing them.** `step_concerns_window` is `window-overlap`'s
predicate and `window_share_of_step` is `window-ramp`'s share. The kernel calls
them rather than deriving overlap itself. Four T020B review rounds were spent on
sentences that each restated a subset of what the formula does; a kernel with its
own copy of the arithmetic would have been the next instance.

**The advertised supported set is derived from a table of executable handlers.**
`ModelSpec.advertised_supported_states` groups the handler table, and there is no
field in which to write a role no handler implements. That closes the backlog's
first entry: `supported_states` had no falsifier, so `READY` was computed from a
promise about a kernel that did not exist.

### The conformance test has three legs, and the third is the one that bites

Deriving a set and comparing it against another declaration would be two tables
somebody keeps in step by hand - the same defect one layer deeper. So: the set is
derived by grouping handlers; every advertised `(state, role)` pair must be
REACHED by executing a Draft created through `RunSetupService` from the shipped
document, recorded by an execution ledger; and the derived set and
`MINIMAL_FUEL_TANK_MODEL`'s declaration must be equal in both directions. A probe
removes a handler and watches the derived set narrow; another adds a handler
nothing calls and watches the ledger report it missing.

**`REPORTED_OBSERVATION` is verified at the model's grain and no further, and the
record has to say so.** The handler answers what a stock is at an instant, after
that instant's events, and refuses to answer in any other phase. Nothing here
publishes that answer: no device, no cadence, no sampling error, no dropout, no
envelope. That is why only half the readiness disclosure retired.

### The trajectory, and the numbers derived before the code ran

Against the shipped template's Foundation - a 500 L tank and a 0.311 L/kWh
generator - the stored volume is 430 L to offset 1080; loses 2799/800 L in each of
the sixteen dispatch steps, reaching 18701/50 = 374.02 L at 1320; holds that to
1500; loses 40 L in each of the three removal steps, reaching 12701/50 = 254.02 L
at 1545; and at 2400 the 300 L delivery fills the tank to 500 L with 2701/50 =
54.02 L recorded refused, after which the run continues and ends at 500 L.

Every number is a `Fraction`. `test_no_kernel_module_limits_a_denominator` scans
the package for `limit_denominator` and for `float(`, so `EXACT_RATIONAL` is
measured rather than intended; the one authored-float normalization is the
contract's own input boundary.

A bound is applied where the transition happens - phase 1 for a due event, phase 7
for the evolution - and phase 8 verifies. That pair reads two ways until one is
ruled out: a bound applied only at phase 8 would let phase 3 sample a volume above
the tank's capacity, which `fuel-tank-capacity` forbids at every step.

### Where a bound's number comes from, which was this slice's to decide

`D-2026-09-22-capacity-bound-source` settles the principle - the declaration is
the document's and the value is the site's - and left the mechanism to the kernel.
The mechanism is the host adapter: it reads the `bounds` block for WHICH state
caps which and the frozen initialization input for HOW LARGE, and
`BOUND_CASE_BY_DECLARED_BOUND` names which contract bound case a declared bound
falls under explicitly. An unmapped bound is refused rather than defaulted,
because deriving the case from a state key's spelling is a rule a later author
moves by renaming something. `declared_bounds` was NOT taught to read frozen
answers: it stays a projection of the document, and it is on its way to the test
suite with the reconciliation panel.

The floor comes from the model, never from `IMPLICIT_LOWER_BOUND_DIMENSIONS` -
`D-2026-09-22-reconciliation-panel-retirement`'s instruction to this slice. The
stock handler declares it with the bound case that says what happens when it is
reached, and the simulator cannot reach that constant anyway.

### The three backlog items addressed to this slice

**Regenerate rather than execute.** Every Draft in both new suites is created in
process by the real setup service. No local Draft is read, and the version-guard
test lowers the version on a rendered document so what is refused is a run whose
provenance is known.

**Cross-reference before initializing.** The adapter carries the run's
`unsupported_optional_inputs` addresses into the neutral inputs, and an initial
value for a state with no handler that is NOT recorded there stops the run as
`UNSUPPORTED_MODEL_STATE`. Recorded, it is skipped with a note saying nothing
about this run models it. The difference between the two is the cross-reference
and nothing else, and both halves are tested.

**The inert upper bound.** Answered above. The capacity reaching the kernel is the
frozen Foundation answer, proved on two Sites: 500 L on the shipped template and
800 L on the twin-tank archetype's south run, whose delivery refuses 65.8 L.
Neither number appears anywhere in the kernel.

### What the kernel refuses, and why each refusal is not the others

Ten execution failure kinds, disjoint from run setup's refusals and a Draft's
blocking reasons - asserted in `host/tests`, the only place that comparison can be
made. `contracts/assetops_contracts/failures.py` records every kind constructed in
a process and the simulator suite fails the session if any member was never
produced, so the vocabulary is reachable rather than decorative. Two are reached
by breaking a handler on purpose: `BALANCE_IDENTITY_VIOLATION` is a contradiction
inside a kernel and cannot be provoked from outside one.

`FORCING_VALUE_AMBIGUOUS` is how this slice **meets** the T020B carry about a
window declaring two values. `baseline-load-profile` declares two parameters for
one address and one role, and nothing says whether they are the ends of a ramp or
two named levels. The kernel refuses to compose them rather than inventing one of
two legitimate readings. It does not reach that refusal on the shipped document
only because nothing models site demand - so the semantic decision still belongs
to whoever models it, and the kernel will not have quietly chosen for them.

A reporting-path forcing never reaches the kernel as a forcing at all. It is the
publication profile's, it moves no stock, and it travels on
`reporting_path_addresses` so the kernel can say it was withheld deliberately
rather than report a declared entry it silently dropped. It is excluded from the
trajectory identity for the same reason: this is the identity of the WORLD, and
two runs differing only in whether a sensor reports produce the same world.

### The shipped document's numbers, corrected from the computed world

Two authored readings were 155 L and 150 L where the trajectory this document's
own declarations produce holds 254.02 L. They predate the consumption coefficient
moving from the document to the machine, and they are corrected to 254.02 with no
reporting error, because nothing in this build models one.

What the reconciliation panel shows afterwards is the honest residual: the
declared causes still reach 310 L, and the 55.98 L difference at BOTH readings is
exactly the fuel the model law burns and the document deliberately does not carry.
It was 155 L of unexplained difference and it is now one identified quantity.

`refuelling-is-not-a-loss` was the one private expectation the trajectory made
inconsistent. It assumed a clean 300 L rise; the tank fills at its capacity, so
54.02 L never arrive and an analysis reconciling the delivery record against the
level would find them. It now names both halves. The computed trajectory is
recorded as a private `TRAJECTORY` expectation - `EXPECTATION_KINDS`' fifth
member - so the corrections can be checked rather than taken. Five expectation
rows now render on the scenario detail, measured at 640px.

**`EXECUTION_CONTRACT_VERSION` did not move, and stays 5.** The `TRAJECTORY`
widening sits off every executable path, which
`D-2026-09-22-contract-version-scope` settles directly. The contract's relocation
moves identical objects. The two new formula functions are the arithmetic the
existing statements already published, tested against those statements' own worked
examples. The disclosure narrowing is about a run status, not about how a document
is read. And the kernel's refusal to compose two forcing values is this kernel's
behaviour rather than a contract statement, so it narrows no declared space.

The scenario document's own `scenario_version` did NOT move either, and that is a
carried deviation rather than a clean answer - see the backlog.

### What T021 leaves open, for the slice that meets it

- **A definition edited in place, at an unchanged scenario version, that MOVES an
  existing entry's offset or window length, is not detected.** A Draft freezes
  resolved values and profile answers rather than a copy of the timeline, so the
  adapter compares what it can - the scenario version, and the exact set of
  parameters the document declares against the set the run froze, which catches an
  entry added or removed. A moved offset changes structure without changing either.
  Recorded in the backlog rather than described as covered.
- **`reporting_path_addresses` carries addresses and not windows.** T022's
  observation transform needs the window to suppress a reading across it, and will
  widen that field rather than discover it missing.
- **The fuel model relates one generator to one fuel tank** and fails as
  `TOPOLOGY_INCONSISTENT` on a second of either. Addressing is not the missing
  piece - T020A1 built that - the missing piece is the declared relationship, and
  it arrives with the electrical world.
- **The law requires its dispatch forcing to be declared somewhere.** A fuel run
  with no generator dispatch at all fails as `FORCING_NOT_AVAILABLE` rather than
  running a tank that sits still. Honest for a world whose only law is driven by
  dispatch, and worth revisiting when a second law arrives.
- **`var/runs` holds 149 local Drafts.** The layout evidence tool added six across
  two runs, one per run-setup visit, which is what it has done since T019.
  `create_run` is still O(n) in that count and still wants a bounded owner before
  T027. The backend suite took 44 minutes in this slice, against 19 seconds in a
  quiet tree; the difference is contention with parallel work rather than a new
  cost, and the O(n) create is what makes it sensitive to it.
- **The three-suite setup needs three editable installs**, recorded in
  `README.md`. The backend imports the neutral contracts, so `assetops-contracts`
  is a real runtime dependency of the product and not only of the tests.

### T021 correction round: the run did not determine the experiment

The independent Codex review returned five defects, four High and one Medium, and
the user asked for all five. It confirmed the shipped arithmetic, all eight
mutation relationships, all fourteen guard probes and the four-tree dependency
direction, and closed the packet's own R0 by widening the product profile in
memory and watching the equality assertion fail. What it found is that the first
executor reinterpreted frozen runs, refused a case the contract had been
corrected to permit, and could report completion after omitting a physical law.

**R1 is the one worth carrying forward, and it was a design change rather than a
repair.** A Draft froze the resolved VALUES a scenario declared and left their
TIMING in a mutable document. So: execute the ordinary shipped Draft, move
`unaccounted-fuel-removal` from offset 1500 to 1515 on the live document at the
same scenario version, execute the SAME persisted run again, and the tank at 1515
goes from 334.02 L to 374.02 L. Both complete. Nothing in the run changed.

The fix is that run setup now freezes the whole causal projection -
`FrozenCause`, `FrozenForcing`, `FrozenDeclaredBound`,
`FrozenReportingPathCondition`, each with its resolved address, direction,
canonical magnitude, shape, offset and span - and `frozen_world_inputs` takes one
argument. **There is no parameter through which a different experiment can
arrive**, which is a stronger statement than any comparison the leaf could have
made. The packet had carried this as "a definition edited in place can still move
an entry's offset undetected", and the reviewer was right that the rationale was
insufficient: T021 owes this boundary and now produces the trajectory later slices
rely on, so "structure only" was not a reason to leave it.

A digest was the cheaper option and was rejected on the reviewer's own argument: a
digest detects drift and then refuses, and criterion 2 asks for RECONSTRUCTION.
Detection is not reconstruction.

**`EXECUTION_CONTRACT_VERSION` moved 5 to 6**, which is the first move this slice
made. A run of an unchanged document freezes differently than it did, which is
exactly `D-2026-09-22-contract-version-scope`'s test. Version 5 is published, so
this is a move rather than an amendment. Earlier runs keep their version, still
read - the four collections default to empty on parse - and are refused execution,
which is what makes an empty projection safe: it can never be mistaken for a run
that declared no causes. The frozen-inputs table grew from 44 rows to 52 and every
one of the four collections reaches a row, because what a reader needs from a
frozen run is what it is going to do.

**R2 was the sharpest irony in the slice.** The kernel rejected any two forcings
concerning one step without asking whether their exposures overlap - the case
`window-active-span` was corrected over four T020B rounds to settle, which R1b and
F-V1 exist to state. It read the phase order from `BOUNDARY_CYCLE.sequence` and
called the contract's own overlap predicate, and then contradicted the sentence
beside them. Each disjoint exposure is now accounted for over its own portion and
their energies add; a `ForcingExposure` per portion replaces one value per address,
so the trajectory can say what happened. Splitting the shipped dispatch at 1085,
inside a step, produces the identical trajectory to the undivided window. A
genuine overlap is still `FORCING_VALUE_AMBIGUOUS`.

**R3: a missing law operand was silence or a `KeyError`.** Remove only the
consumption coefficient and the run reported COMPLETED with zero law events and
430 L at 1320 - missing consumption treated as zero. Remove the starting level and
the stock-moving entries and it raised a raw `KeyError` with no trajectory at all.
`_bind_laws` now resolves every operand and output from `ModelLaw.reads`/`writes`
through the model's own declared component relations, before the first boundary,
and each absence is a classified failure.

**R4: a declared cause disappeared at the adapter.** A parameter that initializes
a state is frozen in `initialization_inputs` and the projection read only
`resolved_parameters`, so a `continue` dropped the cause and the removal stopped
happening. The projection reads both carriers and raises
`UnresolvedCausalProjection` rather than dropping: a declared effect is frozen or
refused, never converted into silence.

**R5: an excluded input manufactured a machine.** `_resolve_topology` collected
addresses before consulting `unmodelled_addresses`, and handler lookup ignored
scope, so an OPTIONAL `site:generator-specific-fuel-consumption` the run had
explicitly recorded as unsupported produced `TOPOLOGY_INCONSISTENT` about
"generator, site". `_excluded` is consulted before topology, initialization and
operand resolution, and `ModelSpec.handler` takes a scope.

**C1 is closed rather than carried.** A stored run carrying two initialization
rows for one address made the last row silently authoritative - the reviewer's
probe got a run starting at 400 L instead of 430. Refused now, in the leaf, where
both rows are still visible.

**C2 shrank.** `COMPONENT_RELATIONS` in the fuel pack declares which state keys
belong to one machine, and `kernel/execute.py` imports no fuel state key at all.
What remains of C2 is that `ModelSpec` is still not a general law executor, which
is the next physical-law slice's to know.

### What this round cost, and the lesson that is not about the kernel

**A fixture pinned a contract version it did not own.**
`simulator/tests/conftest.py` wrote `execution_contract_version=5` as a literal.
The contract moved to 6, the whole simulator suite went red, and nothing said so
until a guard probe reported CAUGHT against an already-failing suite - which is
that probe measuring nothing. Two probes were affected.

So the probe harness now **establishes a green baseline and refuses to probe if
any suite it reads a verdict from is red**. A probe asserts that a test FAILS
after a violation; unless that test passes before one, CAUGHT is a coincidence.
That is the durable half of this round: the fourteen probes were the right idea
and the harness was missing the precondition that makes them mean anything.

Two probes also needed retargeting for honest reasons rather than convenient ones.
The conformance probe added a component-scoped handler that `ModelSpec` now
refuses at construction, so it failed before the test it was about could run; it
uses a site-scoped one. And scope-awareness in `handler()` turned out to be the
layer UNDER the exclusion - the product path never reaches it while the exclusion
holds - so its guard is a kernel-boundary test reached by construction, with a
control, and the probe says why.

**One pre-existing flake was found and fixed rather than swept.**
`test_the_order_is_newest_first_and_total` said its fixture clock was fixed and
asserted the list was sorted by `run_id` descending. `client()` injects no clock,
so that held only while three runs landed in the same second; freezing the
projection made `create_run` do enough more work to straddle a boundary. It now
asserts what `list_runs` guarantees - a total order, stable between reads, sorted
by `(created_at, run_id)` descending.

### What the correction round leaves open

- **`ModelSpec` is not a general law executor**, and the next slice adding a
  physical law must not mistake it for one. A law's operands resolve through
  declared component relations and one write target; two writes, or a law needing
  a relationship between machines rather than within one, need more.
- **`reporting_path_conditions` carries windows now and nothing reads them.** That
  closes the carry that said T022 would have to widen the field, and it leaves a
  frozen collection with one consumer for its address and none for its span.
- **C3 from the review is carried**: several proof descriptions are stronger than
  their assertions. The TRAJECTORY oracle test checks that number strings occur in
  a free-text statement rather than parsing and attributing each to its boundary,
  and the identity field-list guard compares a maintained list against dataclass
  fields rather than mutating each field to prove the digest reads it. Both were
  read and are correct today.
- **`var/runs` holds 159 local Drafts.** Ten more than before this round: the
  layout tool creates one per run-setup visit and was run three times, plus one
  manual POST against the live backend to confirm it served the new projection.

### T021 second correction round: the boundary a run is frozen at

Codex's second pass confirmed the first round's five closed - ten CAUGHT lines,
plus it verified the new red-baseline control by feeding the harness a deliberately
red suite and watching it refuse to probe, and confirmed the adjacent-window fix
works with two DIFFERENT levels (first step energy 75/4, not just the identical
case the tests used). It then found four more and hit its usage limit before
writing a report, so `.agent/T021-codex-second-pass-probes.py` is the review.

Where the first four defects were a kernel reinterpreting or omitting things, these
four are about the **boundary a run is frozen at**.

**1. A rate was normalized twice, and a valid removal became zero.** The worst of
the four, because it was a silent wrong number in the one property this kernel
exists to provide. The projection called a conversion that normalizes and returns a
float, then normalized THAT float again before multiplying by the window's length.
A millionth of a litre an hour is 1/60000000 of a litre a minute; the float is
1.67e-08; normalizing it again gives ZERO, and the run reported COMPLETED having
moved nothing. 1.000001 L/h froze as 999960/999959.

`frozen_canonical_value` in the contract does the whole conversion in exact
arithmetic **with the integration inside it**, converts to float once, and asserts
the round trip. Where the exact value cannot survive the float a frozen record
carries it refuses: `limit_denominator` recovers any denominator within its limit
and none outside it, and a run carrying a number the document did not declare is
what `EXACT_RATIONAL` exists to rule out. Every number a run freezes crosses it,
including initial values - the reported site was the projection and the same
unchecked conversion was one function away, which is how a class comes back.

**2. A version-6 record could omit the fields version 6 exists to carry.** Deleting
`causes` parsed, was READY, executed, and reported COMPLETED with the removal never
happening. Deleting `declared_bounds` overfilled the tank past its capacity. The
version guard cannot help when the version is the current one - and **this was my
own argument for the version move applied to a layer I had not applied it to.** A
run AT this build's version now carries the projection; an empty list is still a
real answer and a missing or null key is not; a run below it may carry none of it,
which is what preserves earlier readback. Both directions are probed, because a
guard that required the fields at every version would pass the first probe and lose
every earlier run.

**3. An unanswered magnitude raised where the product blocks.** A `MODEL_RULE`
magnitude no profile supplies a rule for has no number, and the product has always
BLOCKED such a run because a different profile may answer - the reviewer's own
control proved it by disabling the projection and getting
`INITIAL_VALUE_NOT_RESOLVED`. Raising turned that into HTTP 500 with nothing
written. `FrozenCause.canonical_value` and `FrozenForcing`'s have an absent case
now, and `SimulationRun` enforces for them the invariant it already enforced for an
absent initial value: the thing that made it absent is on the run beside it, naming
the same address. `UnresolvedCausalProjection` survives only for what the scenario
parser already guarantees cannot happen, and its docstring says so.

**4. The exclusion was one notch too wide.** A model may model a state without
modelling every role of it: this one moves a tank's stored volume and cannot have
one FORCED, so a scenario forcing `fuel-tank-volume@fuel-tank` is correctly
recorded unsupported at that role. Excluding the ADDRESS then suppressed the
`CAUSAL_INPUT` role it does support, and execution failed `INITIAL_STATE_UNANSWERED`
for a stock the run genuinely carried. The neutral boundary carries `(address,
role)` pairs - `UnsupportedOptionalInput` has carried both since T020A1 - and
topology asks the different question it should have been asking: an address
excluded in EVERY role it appears in contributes no machine, which is what keeps
R5 fixed.

Also, the same class as 3: a zero-length window reached the kernel and escaped as
an unclassified `ValueError`. It is refused where a document is read.

### The contract version did not move again, and why

**It stays 6, and the four fixes ride on it.** Version 6 has never left this
branch - `main` is at 5 - so the unreleased-version doctrine that let version 2
carry three amendments and version 5 carry four applies, and this paragraph is what
stops the amendment being invisible afterwards.

Judged per change even so, because two of them would otherwise look like moves.
Fix 1 changes what a run freezes for an unchanged document, which is the policy's
test - but the contract already said one-time normalization at the input boundary,
so a conforming implementation always produced 1/1000000 and this is conformance
rather than a rule change. Fix 2 narrows what a version-6 RECORD may be, which is a
rule, and it lands on 6 before 6 is published. Fixes 3 and 4 change what a
non-conforming implementation did.

**One thing to know about `var/runs`.** It holds 165 Drafts and contains version-6
ones frozen by the pre-fix code, created by the layout tool against the live
backend. They are
indistinguishable from post-fix ones by version - the same trap the backlog named
for version 5 - so any Draft there could carry a wrongly normalized rate. Nothing
executes a local Draft and every test regenerates, so it is a note rather than a
defect, and it is the third time this integer-equality guard has been the thing
that cannot tell two builds apart.

### What this round cost, and what the probes caught that I did not

Three probe results were mine rather than the code's, and each is worth keeping.

**A test was satisfied by an adjacent mechanism.**
`test_an_address_excluded_in_every_role_contributes_no_machine` used a `site:`
address, which the scope filter removes before the exclusion is consulted - so it
passed with the exclusion deleted from topology and proved nothing. The probe
written for it found that. It now names a second COMPONENT-scoped tank on the
twin-tank Site, mentioned only in a role the run records as unsupported.

**Two probe anchors went stale** when the exclusion gained a role, and the harness
reported SKIPPED rather than passing. That is the harness working: a probe whose
anchor has moved says so. Both anchors follow the new signature.

**A patch script wrote newline escapes into Python source through a script where
they were already newlines**, and broke every multi-line anchor in the block it
inserted. `.agent/` is gitignored, so there was no committed copy to restore from;
the block was rebuilt with a `lines()` helper so no probe body contains an escape
sequence at all. The instance was cheap and the class is not: a repair that removes
the possibility is worth more than one that removes the symptom.

## T021A - Narrow reported-observation declarations

What this slice settled in code. **A reading declares no execution requirement**,
and an authored document that says one is refused at the strict boundary with the
position named. Nothing else moved: the kernel, the packs, the trace, the
reconciliation payload and every authored value are untouched.

### The rule is a list, and both sides read it

`REQUIREMENT_BEARING_ROLES = {"CAUSAL_INPUT", "FORCING_INPUT"}` in
`scenarios/models.py`, beside `EXECUTABLE_ROLES` and deliberately different from
it. `_parse_execution_placement` refuses `execution_requirement` outside that set;
`_declared_requirements` and `requirement_conflicts` in `runs/service.py` gather
within it. One list rather than a rule written twice, which is the shape this
project keeps paying for when a rule reaches three of four positions.

The two sets differ on purpose and a future reader has to know which one their
rule belongs in. A reading IS executable - the reporting path consumes it and the
kernel's `SAMPLE_HANDLER` samples `fuel-tank-volume` in the
`REPORTED_OBSERVATION` role - but it is not an input a run can proceed-or-block
over, because a requirement level answers "may setup proceed without support for
this" and nothing was ever asking that about a reading.

### What a reading keeps, and it is the half worth remembering

Its ADDRESS. `declared_state_refs` reads all four positions a reference can be
written at and has never been requirement-sensitive, so a reading naming a
component this Site does not declare still blocks with
`STATE_ADDRESS_NOT_RESOLVED`. The narrowing removed a support question, not a
reference obligation. `TestTheAddressObligationIgnoresTheRequirementLevel` is the
class that holds this, and its `declared()` helper now skips the reading entry
when it re-levels a document, because writing a level there is refused.

### The version move, and why it is a move at all

6 to 7. Nothing executes differently - that is the whole argument for removing
the field - and under `D-2026-09-22-contract-version-scope` that is not the test.
The test is DIRECTION against documents that already exist: this narrows, so the
shipped document valid at 6 is refused at 7 and a run frozen against it can no
longer be re-derived from a document that parses. Six was published (T021 merged
at `ed0635c`, `var/runs` carries Drafts at 6), so the unreleased-version doctrine
did not apply and the ledger's own "the next narrowing is a seven" stood.

Worth keeping for the next vocabulary change: this is the first entry in the
ledger where the number moves although no conforming kernel could behave
differently. The paragraph in `execution_contract.py` says so explicitly, so
nobody re-derives it as "document shape changed" - which would bump on
everything.

### What an earlier frozen run does now, measured rather than assumed

A version-6 record carries a causal projection. The readback rule REQUIRES the
projection key at the current version and TOLERATES its absence below - so a
record carrying one below the current version is read, not refused. Confirmed
against real runs already in `var/runs`:
`run-0cc40a866aa0472b97ac33f736f0309f` (version 6, READY, 2 causes, 4 forcings)
and `run-9f74603b06384126a627a5339fc78fbe` (version 5, T020B's Draft) both parse
under build 7 and both are refused execution. The test for it is parametrized
over 4 and 6 and asserts the record came back WHOLE - run id and frozen causes
equal to the original - rather than that parsing returned something.

### A narrowing of the document structure invalidates documents that exist

The cost this slice actually paid, and the thing a future narrowing should expect
to pay again. The version number protects RUNS: an old frozen run keeps its
identity, stays readable and is refused execution. There is no equivalent signal
for authored DOCUMENTS. The four user-authored scenarios in `var/scenarios/` all
declared `execution_requirement` on their readings, and after the narrowing none
of them parsed.

Two consequences, and the second is open.

- Those four documents had the field removed from their reading positions and
  nothing else, by the same mechanical rule applied to the shipped document. No
  value, address, source or identity changed. Pre-edit copies were kept outside
  the repository for the length of the slice.
- **One invalid user document makes the whole catalog unreadable.**
  `composite_scenario_repository.list_scenarios` raises out of the list rather
  than reporting the one document it could not read, so a single unparseable file
  in `var/scenarios/` takes the scenario catalog down. That is how this was
  found: `test_scenario_repository.py` and four `test_scenarios_api.py` tests
  failed on this checkout for a reason that had nothing to do with the shipped
  document. Pre-existing, unowned, and deliberately not fixed here - the slice
  was time-boxed to the parser closure.

### What stayed inside the box

The Execution rule said implement the narrow closure and stop. What was NOT done,
so a reviewer does not have to infer it: no readiness rework, no vocabulary
decision about what an author should write instead, no reconciliation-panel
retirement, no trace, no authored value change, and no fix for the catalog
fragility above. The Implementer wrote no backlog entry, correctly, because
writing one is a planning act the time-box excluded; **the coordinator then
wrote it at the owner's direction after the packet was closed** -
`.ai/MILESTONE_REVIEW_BACKLOG.md`, "One invalid scenario document takes the
whole catalog down". Do not read the sentence above as saying the item is
unrecorded. Two tests changed the role they prove the
role-support rule with - `FORCING_INPUT` in place of the observation role - and
that was forced by the closure rather than chosen: the case they used no longer
exists.

### What this leaves open

- **The intent the field used to carry has no home yet.** An author who meant
  "the world state behind this reading must be modelled" is pointed at the cause
  that moves it, and one who meant "the reporting path must carry readings" at
  the reporting-path forcing. If a real authoring case fits neither, the
  vocabulary needs a decision.
- **`requirement_conflicts` keeps a `requirement is None` guard that the parser
  now makes unreachable.** Left as defence in a reporting function.
- **The catalog fragility above has no owner.**
- Guard probes: `.agent/T021A-guard-probes.py`, 8 probes, all CAUGHT, baseline
  measured green before any mutation.

## T022 - Execute a Draft in the Lab, and inspect generated device observations

The first visible slice since T020. Before it, the kernel existed, executed and
was confirmed by three independent reviewers, and nobody outside a test had seen
it run. After it, the owner starts a Draft in the gated Lab, steps it across the
fuel event, and reads three things that used to be one: what the world holds,
what a device reported, and the fact that nothing reported at all.

### The demonstration, in numbers, because it is what the slice is for

The shipped reporting gap is `[1490, 1580)` and the removal `[1500, 1545)` sits
entirely inside it. At offset 1545 the Lab shows:

- true value **254.02 L** - the tank after the removal;
- reported value **373.52 L** - the fuel sensor's last reading before the gap
  opened, half a litre below the 374.02 L the world held when it was taken;
- a source sample time that is that earlier instant and not this one. WHICH
  earlier instant depends on the draws, so it is not a constant of the slice:
  the host suite's fixture retains offset 1485 (`2026-09-22T00:45:00Z`) and the
  browser, executing `fuel-loss-event-mg006`, retains offset 1470
  (`2026-09-22T00:30:00Z`). The reported value is 373.52 L either way, because
  nothing moves the tank between those instants and the removal;
- quality **STALE**, outcome **SUPPRESSED_BY_GAP**, and the authored entry that
  did it named on the row.

The two columns differ by 119.50 L. The removal is 120 L, and the difference is
that number with the sensor's declared -0.5 L bias taken back out: 373.52 + 0.5 =
374.02 L when it was taken, less 254.02 L now. Saying "the columns differ by 120"
would be reading the reported value as the world's, which is the one confusion
this screen exists to prevent. That is asserted in
`host/tests/test_lab_execution.py` and measured in a real browser by
`tools/layout-evidence.mjs`.

### What it settled in code

- **`EXECUTION_CONTRACT_VERSION` is 8.** `REPORTING_RULES` in the contract
  answers four questions a version-seven implementation was free to answer any
  way it liked: when a sample is due, what a forced gap does to one, what a
  consumer sees when nothing fresh arrived, and whether a publication failure is
  drawn or chosen. Two of them are executable beside their sentences -
  `sample_due_at` and `cadence_is_expressible` - for the reason `window-overlap`
  and `window-ramp` are.
- **The publication profile is version 2**, and the two moves are one move. It
  now declares `device_signals`: which configured signal reports which world
  state, at what cadence, with what bias and with what dropout. A run freezes
  which publication profile answered, so a run of an unchanged document freezes
  a different identity under eight than under seven - which is
  `D-2026-09-22-contract-version-scope`'s own test.
- **A kernel execution is a handle.** `Execution` advances a boundary at a time
  with the boundaries so far readable mid-flight; `execute` is that handle
  advanced to the end and returns the trajectory it always did. Every scrap of
  state was already on one mutable object, so this changes when a caller may
  look rather than what any boundary holds - and five batching patterns are
  asserted to produce one content digest.
- **The observation transform is a separate component**, in
  `simulator/assetops_simulator/observation/`. It is handed the boundaries and a
  `FrozenReportingInputs` with no field a stock could arrive in; the kernel is
  handed a `FrozenWorldInputs` with no field a cadence could. Criterion 8 -
  changing a cadence, a bias or a dropout changes the reports and not the world -
  is therefore a fact about two signatures rather than a rule a caller remembers.
- **A `DeviceObservation` carries no true value**, deliberately. Pairing truth
  with a reading happens once, in `LabProjection`, built by the composition leaf
  and consumed by a gated surface. That is the exception to the truth barrier
  stated as one record rather than left as a habit.
- **The first stochastic mechanism draws under `assetops-sim-rng-v1`**, the
  domain v4 reserved and `identity.py` declined to spell until something consumed
  it. A draw is BLAKE2b-256 over the seed, a stream name derived from the device
  and signal, and the fields that locate it - never over how many draws came
  before. That is what makes "adding an unrelated stream changes no existing
  stream" structural rather than a hope about call order.
- **The execution port is the backend's, and only the leaf can implement one.**
  `runs/execution_ports.py` speaks `SimulationRun` in and `LabProjection` out.
  `host/lab_app.py` is the entry point for a build that executes; run it from
  `host/` with `python -m uvicorn lab_app:app`. `assetops_backend.main:app` still
  serves everything else and answers `PORT_NOT_COMPOSED` on the four execution
  routes, which keeps the served route set a function of the gate alone.
- **Private execution artifacts are the leaf's**, under `var/executions`, one
  file per run. A terminal run reloads from its artifact; a run recorded as
  RUNNING with no live handle reads back as `INTERRUPTED`, because its world
  lived in a process that has ended and re-executing it would be a second
  trajectory under the first one's identity.
- **Every execution artifact states the schema version it was written in**,
  first in the file, and `EXECUTION_ARTIFACT_SCHEMA_VERSION` is 2. One is the
  first build that persisted an execution; two added the reporting condition's
  shape and the run's timestep to every gap row. The number exists because
  adding those fields broke every record already on disk: the reader demanded
  them and four completed runs became an HTTP 500 on the screen that inspects
  them.

  **Three layouts exist on disk and each was written by a build on this branch.**
  The current one says its schema. The two older ones do not, and
  `_identify_layout` tells them apart by whether their reporting-gap rows carry
  `timing_shape` - the exact field the later of those two builds added, and the
  only evidence such a record holds about its own provenance. All rows or none;
  a record whose rows disagree was written by neither and is not interpreted.

  **Where the shape was recorded it is honoured**, and the span follows from it
  by `end_offset_minutes` - the same rule that build resolved with, so what is
  shown is what was computed. **Where it was not**, each row carries
  `recorded_end_offset_minutes`, the span that build resolved, recoverable
  exactly because it resolved every window by one rule over fields the record
  still carries; the shape is `SHAPE_NOT_RECORDED`, which is not a shape and
  never a guess. **A record this build cannot interpret** - a later schema, a
  marker that is not a whole number, disagreeing rows, or a record that states a
  layout and then lacks what it requires - is reported: status
  `ARTIFACT_UNREADABLE` with the reason on the projection, and a typed refusal on
  every control, because an unreadable record treated as no record would let
  Start overwrite the very result nobody could read. Nothing is re-executed,
  rewritten or discarded.

  **A version marker cannot name what predates it, and the first attempt proved
  it.** The marker was added by the build that fixed the shape collapse, so the
  build before it had already written records with the shape on them and no
  marker. Assigning every unmarked record to the oldest known layout discarded
  that shape and printed a note saying it had never been recorded - while it sat
  in the same file - and turned an honest `KeyError` into a confident wrong
  reading. That is in the published rule now, not only here:
  `a-record-older-than-a-rule-is-read-as-what-it-recorded`, with version 8's
  ledger carrying the third amendment. **A later slice adding a persisted field
  inherits the rule, not the mechanism**: the run store and the scenario
  documents have their own versioning conventions and were not touched here, and
  the rule's second half - identify what predates the marker from what it carries
  - is the half that is easy to skip.
- **A window's declared instant and its resolved span are separate everywhere.**
  For a POINT they differ: an entry declared at offset 1490 in a fifteen-minute
  run silences the sample at 1485. The suppression sentence names both, the wire
  carries `declared_offset_minutes` beside `start_offset_minutes` and
  `end_offset_minutes`, and the gaps table has a column for each. One field
  named `offset_minutes` was carrying the resolved start - the right number
  under a name that promised the other one.
- **`draw_fraction` refuses a field of the wrong type**, narrowly and on
  purpose. A signature constrains arity and not types, so the claim that an
  address "cannot be supplied" was false - `draw_fraction(7, "a-stream",
  "<an address>", 1500)` returned a Fraction. The refusal is here rather than
  everywhere because this substitution IS the defect R1 was: a draw keyed on an
  address is deterministic, returns a plausible number, and differs from the
  contract's stream with nothing on any surface to show it.
- **Every exact quantity leaves the backend as text.** `EXACT_RATIONAL` never
  rounds, and a payload carrying a binary float would be the one place the policy
  stopped holding. A test walks the whole payload and fails on a float anywhere.
- **Criterion 14 is done.** `reconcile_reported_observations`,
  `ObservationReconciliation`, `RECONCILIATION_STATES`, its seven reason strings,
  `unaccounted_observations`, `declared_bounds` and
  `IMPLICIT_LOWER_BOUND_DIMENSIONS` are gone with the scenario detail panel that
  was their last product-path caller. Nothing survived the retirement. The
  frozen run's own `declared_bounds` - a tuple of `FrozenDeclaredBound` on the
  deterministic identity - is a different thing with the same name, is
  load-bearing, and is untouched.

### One defect the browser found, which no suite could

`reporting_inputs` asked whether the run had selected this publication profile
BEFORE asking whether it was frozen under this contract version. A run from an
earlier build fails both, and it was reporting the narrower one: "this run does
not determine one experiment" for a run whose real answer is "these rules are not
the rules it was frozen under". Every suite builds its runs in process at the
current version, so none of them had a run that failed both. The coarse, prior
fact is asked first now.

### What this leaves open

- **The shipped scenario cannot reach READY against the MG-001 in `var/sites`**,
  which predates the two Foundation properties the model profile binds to. Both
  suites and the browser evidence reach a READY execution through the product
  path from the user's own `fuel-loss-event-mg006` document instead. Backlog.
- **`var/runs` grows by four per layout-evidence run**, not three: three BLOCKED
  MG-001 Drafts from the run-setup measurement at three widths, plus the READY
  MG-006 Draft the execution measurements need.
- **The run setup screen does not show a publication profile's declared reporting
  paths.** They are on the Draft's own execution panel, which is the screen where
  they decide something, and there is one profile to choose from.
- **`private_state` carries stocks and not interval measurements**, because a
  stock's unit is the run's and an interval measurement's is the model's. The
  interval truth is in the observation row, in the unit the profile declared.
- **The dependency-direction guard's three oldest patterns match prose.** A
  docstring saying the backend cannot import the simulator failed the check. It
  was reworded rather than fixed, because loosening a dependency check inside the
  slice it blocks is the one edit that file forbids. Backlog.
### The fifth variant of one defect, and why it is a rule now

R4 was a change correct going forward and silent going backward. So were three
before it: T021's frozen runs reinterpreted by a live document, a version guard
unable to separate two builds sharing a number, T021A's narrowing invalidating
four authored documents, and then a schema with no reader for its own past.
**And so was R4's own fix**, which is the fifth: a version marker that correctly
identified future writes and could not identify the two historical shapes that
lacked it. The fourth was the fix for the third and the fifth was the fix for the
fourth. That is why the backward path is a published rule rather than something
each slice is expected to remember, and why the rule now names its own second
half - identifying what predates the marker from what it carries - which is the
half that was skipped.

The shape is worth recognising rather than the instance: every one of the five
was found by somebody looking at existing data, and none by a suite, because a
suite writes its fixtures with the build that reads them. A round trip through
one schema cannot fail this way. **The test that catches it supplies a record in
the shape the PREVIOUS build wrote**, and the one for R4 builds that record by
executing a real run and removing exactly what the old build never wrote - with a
precondition test asserting the fixture really is that shape.

A sixth instance of the same habit, smaller and caught by a reviewer rather than
by data: the fix's own tests all build their fixtures by STRIPPING a record the
current build wrote, so none of them states a schema marker the current build
would not write - and a record stating `artifact_schema_version: 1` was read
under the current layout and then told it had said 2. The lesson applies to a
fix as readily as to a defect, and the missing case is always the one the author
did not think to write down.

### What the independent review returned, and what it cost to be wrong about

Three defects, and each was missed by a test that was written from the code
rather than from the contract or from the surface a user meets. That is one
lesson with three instances, and it is the one worth carrying.

- **R1: the draw identity was not v4 section 9.2's.** It hashed the domain, the
  stream, the seed and whatever the caller found convenient - an address and an
  offset in minutes - where the specification names the domain, the seed, the
  stream name, the step index and the ordinal. Deterministic, domain-separated,
  and a different contract. **The test could not catch it because it recomputed
  the payload the implementation had chosen.** It now writes the expected payload
  from the specification's field list, and `draw_fraction` has no variadic
  parameter, so a caller cannot supply an address because there is nowhere to put
  one. The shipped run drops 12 samples where it dropped 13.
- **R2: a READY Draft at a 30-minute timestep answered HTTP 500 on Start.** The
  cadence check ran outside the port's exception translation and the route
  catches only `LabControlRefused`, so the explanation naming the signal and both
  numbers never arrived. **The test proved the lower-level object raises and
  never drove the HTTP composition.** The check moved inside `_reporting_for`,
  `CADENCE_NOT_EXPRESSIBLE` is a ninth control refusal, and `LabControlRefused`
  gained a `detail` because a per-kind statement cannot name two particular
  numbers.
- **R3: a POINT reporting condition became an outage lasting the rest of the
  run.** `reporting_inputs` dropped the frozen `timing_shape` and every absent
  duration read as the interval's end, so POINT and INTERVAL_WIDE collapsed.
  **Every test used the shipped document, which declares a WINDOW**, so the one
  shape that worked was the only shape covered. The shape travels now,
  `ReportingPathWindow` resolves its own span from it, and
  `reporting-path-conditions-occupy-time-by-their-shape` publishes the rule.

`EXECUTION_CONTRACT_VERSION` stays 8. R1 and R3 each narrow what a conforming
implementation may do and would each move a number; they ride on eight because
eight has never been published - `main` is at seven - and the ledger records the
amendment rather than leaving it invisible after the merge. R2 moved nothing: a
translation is not a rule.

Three smaller corrections. The Lab landing page still said no simulator run
exists and that execution was not implemented. The retained-timestamp probe's
mutant was an undefined name, so its CAUGHT measured a `NameError` rather than a
rejected restamping - and the test it named survived the reviewer's semantic
mutant, because it asserted the offset and the value and never the timestamp.
And `NOT_STARTED` said "Its frozen inputs are eligible", which a BLOCKED Draft
renders beside its own blocking reasons.

**The displayed columns differ by 119.50 L and not 120.** The removal is 120 L;
the difference is that with the sensor's -0.5 L bias taken back out. Saying 120
reads the reported value as the world's, which is the confusion the screen exists
to prevent.

- Guard probes: `.agent/T022-guard-probes.py` (11 of 11 CAUGHT) and
  `.agent/T022-return-probes.py` (4 of 4, each putting a returned defect back
  exactly as it was).

## T022A - A run read that does not cost the whole store

The owner found this stepping the first real run T022 delivered: everything was
correct and every interaction took about nine seconds, which reads as a hang.
`YamlRunStore.get_run` called `list_runs`, parsed all 216 stored documents and
then scanned the records for one identity, so a single read paid for the whole
store. It is the cost T020A measured at 70 Drafts and 6.8 seconds.

### What a single read does now

`get_run` looks for the document filed under the requested identity first. The
file name has always been the case-folded `run_id`, and using it as a hint about
WHERE TO LOOK is a different thing from reading identity out of it. Three
properties keep that true, and a reader changing this code needs all three:

- a key may name a file only when `is_allocated_run_id_key` says it is the shape
  allocation produces. **This is a barrier, not defence in depth**: it is the
  only thing that stops an out-of-root file being opened and parsed, because the
  identity comparison below never runs on a file that will not parse. T022A's
  packet called it defence in depth and was wrong; a reviewer found the mutation
  that proves otherwise, and the guard now carries an out-of-root sentinel;
- the document is read by the same strict reader the inventory uses, so the fast
  path refuses exactly what the slow path refused;
- the identity comes from the PARSED DOCUMENT and is compared to the key before
  the record is returned. **This is the load-bearing barrier.** Remove it as
  redundant and one run's frozen record can be answered under another's name.

A name that leads nowhere, or to a document declaring a different run, falls
back to the old scan. That is why a store somebody rearranged by hand still
answers, and why a MISSING run still costs the whole store - unchanged behaviour
on a path that is not the defect.

Measured through `host/lab_app.py` against the real `var/runs` at 216 records:
216 documents parsed becomes 1, and every wall-clock ratio sits around two
orders of magnitude - run detail and execution read both from about nine seconds
to under a tenth, a step from about ten seconds to about a twentieth. In a
browser, clicking Step went from about nine and a half seconds to about an
eighth. **Quote the ratios, not the seconds**: see the measurement warning
below.

Cost is guarded by counting documents parsed, not by timing. A clock measures
the machine; the count measures the property.

### One behaviour deliberately changed, and one bound deliberately dropped

An unrelated invalid document no longer refuses a sound single read - criterion
4 asked for that. And `MAX_DOCUMENTS` is enforced by `document_paths`, so a
store above the bound still refuses to be enumerated and still refuses a new
run, but a run somebody can name is now readable in one. Counting the directory
on every read is the shape of cost the slice exists to remove.

### An absolute measured once here is not a project fact

Recorded because this slice got it wrong first. `read_run_records` over the same
216 documents was measured three times by three readers and returned about
**15 ms, 41 ms and 49 ms per record** - more than a three-fold spread on machine
state alone, on the same corpus and the same operation. The first packet wrote
41.3 ms and a derived threshold into this file as fact, and a reviewer's
measurement disagreed by 2.7x. The same session had already seen `/api/sites`
move from 0.41 s to 0.13 s with nothing touching the site store, which was the
warning.

**So quote a ratio, a share or a shape here; quote an absolute only with the
conditions it was taken under.** What reproduced across all three readings: the
average stored document is about 6.7 KB, the YAML scanner is about 99% of the
inventory with the record parser under 1%, and libyaml reads the same corpus
about eight times faster.

### The inventory was measured and left alone, and it is NOT acceptable

`list_runs` still reads and strictly validates every record - a partial
inventory is a wrong answer rather than a slow one - and it costs a whole-store
parse every time. **99% of that is the pure-Python YAML scanner**; the record
parser is under 1%. Across the measured range the inventory passes one second
somewhere between about 20 and 65 stored runs. **It stopped being acceptable
long before the 216 the store now holds**, which is consistent with T020A
finding it uncomfortable at 70 Drafts.

The one lever measured to be worth anything is the constant: libyaml's scanner
is present here and reads the same corpus about eight times faster, with the
same `SafeConstructor` and `Resolver`, so only the scanner differs. A reviewer
went further and confirmed the two produce EQUAL documents for all 216 stored
runs - which settles the constructor argument and settles nothing about what the
two scanners REFUSE, and refusal is the question. It was reported rather than
taken, because this slice was told strictness is not what is being traded.
**It wants an owner's decision.**

`create_run` is also still O(n): `_refuse_existing_identity` calls `list_runs`,
so setting a Draft up still pays the inventory's cost. Both costs are carried in
`.ai/MILESTONE_REVIEW_BACKLOG.md` under "Reading the run store still costs the
whole store, twice" - an entry T022A had to WRITE, because three documents
including this one cited it before it existed.

### What the records on disk proved before anything changed

All 216 stored documents are filed under their own case-folded identity, with no
duplicates and no non-YAML entries. That was checked FIRST, because a change to
how a record is located is exactly the shape that is right going forward and
silently wrong going backward. Nothing enforces the invariant and nothing needs
to; the fallback covers a store where it does not hold, at the old cost.

### Two things the review round added

**The one filesystem touch outside the strict reader now translates.**
`Path.is_file` answers False for "not there" and lets a permission denial, a
sharing violation and an unacceptable path through. That stat sits outside
`read_run_record`, so an `OSError` on the requested document crossed the port
raw and a 503 became a 500 - breaking the rule `yaml_run_documents` states in
its own docstring. Because every record in the real store is canonically filed,
it was reachable on every read. Fixed with the same translation one line below
it, and guarded.

**Duplicate identities resolve differently now**, to the canonically filed
document rather than to whichever path sorted first. Unreachable through
`create_run` and absent from the store; carried, and recorded because criterion
10 asked for the list of behaviour changes to be complete.

- Packet: `.agent/T022A-review-packet.md`; reviews `.agent/T022A-review.md`
  (Claude backup) and `.agent/T022A-codex-review.md` (incomplete); the
  criterion-9 harness and its pre-change baseline server at
  `.agent/T022A-step-evidence.mjs` and `.agent/T022A-before-app.py`.

## T023 - Staged canonical source envelopes

The first canonical evidence boundary, staging only. Executing a Draft in the Lab
now also publishes, through a simulated gateway, the canonical source envelopes a
later Commit would release, persists them as an immutable stage, and shows them
exactly as persisted on the Draft's own screen. Nothing is committed, received,
ingested or accepted; no Site history changes.

### What it settled in code

- **`contracts/assetops_contracts/source_envelope.py` is the one crossing.**
  Schema `assetops.source-envelope` **v1**, independent of
  `EXECUTION_CONTRACT_VERSION` (still 8) - `D-2026-09-29-source-envelope-schema-v1`
  records the choices. Exact key sets at every level, no free-text field, exact
  decimal text for values, `YYYY-MM-DDTHH:MM:SSZ` instants, `published_at >=
  source_time`, `received_at` refused as an unknown field. `SourceEnvelope`
  validates in `__post_init__`, so an invalid one cannot be constructed, and
  `parse_canonical_envelope_json` refuses text that is not already canonical.
- **The message id is derived and content is not in it**: BLAKE2b-256 over Site,
  gateway, source, device, signal and source time, recomputed by the parser. A
  retry is the same id by construction; same id with different content is a
  `StageConflict`, never an overwrite.
- **Stock versus interval survives**: `STATE_AT_INSTANT` names no interval;
  `INTERVAL_MEAN` carries `interval_start`/`interval_end` with the end equal to
  `source_time`, the span read off the interval's real boundaries.
- **What is not published has no envelope.** `SUPPRESSED_BY_GAP` and `DROPPED`
  publish nothing; `NO_PRECEDING_INTERVAL`/`NO_VALUE_AT_BOUNDARY` become a typed
  `UNAVAILABLE` envelope only where the mapping says the signal publishes
  unavailability. The suppression sentence (which names the scenario's event)
  never crosses.
- **The gateway is `simulator/assetops_simulator/gateway/`**, a component beside
  the transform. It reads `DeviceObservation`s only. The shipped allowlist is
  `simulator-lab-gateway-fuel` v1: the fuel level sensor alone, 3 s declared
  publication latency. The generator's power signal is generated and NOT
  published - T026 extends the allowlist.
- **`contracts/assetops_contracts/source_stage.py` is the stage**: admission
  appends only, the whole mapping is frozen into the stage and read back from
  it, a refused conflict is recorded by id and kind and blocks release, and the
  persisted document is canonical JSON carrying each envelope as its own
  canonical text plus a BLAKE2b-256 integrity digest. Anything that fails to
  verify is `STAGE_UNREADABLE`, and an unreadable stage is never overwritten.
- **`host/source_stages.py` persists under `var/stages/<run_id>.json`**, atomic
  via a `.partial` sibling and `os.replace`. Gitignored user data, safe to
  delete; a missing stage reads `NOT_STAGED`.
- **`host/lab_execution.py` stages on start and on every step, before writing
  the execution artifact**. That order only means a stage write that RAISES
  aborts the step before the artifact is written; a publication refusal caught
  in `_stage` (by design) is followed by the artifact write, so a persisted
  execution CAN be ahead of the stage's watermark (review R5: 106 vs 105).
  **Write order does NOT make eligibility honest** - the first
  packet said it did, and the independent review (R1) disproved it: a failed
  final stage write with the process still alive, and a publication refusal
  caught in `_stage`, both read as ELIGIBLE. What does is the stage's own
  watermark: a stage (schema **2**) records `boundaries_total` and
  `published_through`, the latter moving only when a stage write succeeds, and
  `published_through < boundaries_total` is the `STAGING_INCOMPLETE` blocker -
  after a reload too. Measured by `TestEligibilityRequiresStagingThroughCompletion`
  without `forget`, and by guard probes P13/P14. It is a progress record, not
  T027's seal. Every step
  republishes the whole series, which is the idempotent-retry case by
  construction. The session freezes the gateway mapping at start.
- **The port gained one READ, `staged_envelopes(run) -> SourceStageView`** (v4
  3.3's name), which re-reads and verifies the persisted stage and never reads a
  live session. Route `GET /api/simulator-lab/runs/{run_id}/stage`, gated, no
  write verb. `PORT_NOT_COMPOSED` answers 503 like the execution routes.
- **Only `simulator_lab_api.py` and `runs/execution_ports.py` may import the
  stage contract** in the product; `tools/checks/dependency-direction.ps1`
  enforces it with an anti-vacuity count. The envelope schema is deliberately
  NOT restricted: T027's ingestion must parse it.
- **The inspector** (`RunFrame.tsx`, panels "Staged source envelopes" onward)
  shows status, eligibility and blockers, schema versions, frozen mapping and
  allowlist, integrity digest, one row per envelope with source and publication
  time in separate cells, and the selected envelope's canonical text byte for
  byte in `pre.canonical-text`. It is re-read after every control. It has no
  input and no control but "Show envelope N". `settledScreen` knows its loading
  sentence.

### The demonstration, in numbers

Shipped Fuel Loss Event against MG-001 (host suite): stepped to offset 1545 the
stage holds 91 envelopes, the newest at source time `2026-09-22T00:45:00Z`,
published `00:45:03Z`, value 373.52 L, and none inside the gap; completed, 147,
eligible. In the browser against `fuel-loss-event-mg006` the draws differ: 97
staged at 1545, newest `00:30:00Z`/`00:30:03Z`, 154 when complete, and a fresh
page load at 640px shows the same 154 and the same 643 characters of canonical
text. Quote the relationship, not the count: which samples drop is the draw.

### What this leaves open

- **Two Drafts of one Site produce the same message ids** for the same device
  and source time, because the id is the publication's and not the run's. Within
  a stage that is correct; across runs it is a real collision T027's commit or
  ingestion must decide about.
- **The shipped allowlist has no interval signal**, so `INTERVAL_MEAN` and the
  typed-unavailable path are proved by the gateway suite's fixtures, not by the
  shipped run. T026 is where they meet real data.
- **A stage is rewritten whole on every step** (about 110 KB at completion), so
  staging a run is quadratic in its envelope count. Fine at 150; not at T026's
  scale without an append format.
- **Eligibility rests on the publication watermark, not a seal.** It says
  every boundary was published into the stage; sealing is Commit's (T027).
- **The integrity digest is redundant with the canonical-form check**; a probe
  found the digest comparison removable with every damage case still refused.
  Both stay; the reason is now asserted.
- `var/stages` grows by one stage per layout-evidence run, beside the four Drafts
  `var/runs` gains.
- Guard probes: `.agent/T023-guard-probes.py` (12 of 12 CAUGHT); browser log
  `.agent/T023-layout-evidence.log`.

## T022B - The run store reads with libyaml

Under `D-2026-09-29-run-store-libyaml`. Packet: `.agent/T022B-review-packet.md`;
evidence `.agent/T022B-evidence/`.

### What the code settles

- **One load point, libyaml, required.** `runs/adapters/yaml_run_documents.py`
  loads every run document with `yaml.load(text, Loader=CSafeLoader)`. The
  inventory, canonical and fallback reads, both create identity scans and the
  staged readback all pass through `read_run_record`. `from yaml import
  CSafeLoader` failing raises `LibyamlUnavailable` (an `ImportError`) at import,
  so an installation without the C extension cannot import the run store - or
  `assetops_backend.main` - and is told how to reinstall. No fallback exists.
  Site, scenario, execution-artifact and stage readers are untouched.
- **Guard:** `tools/checks/configuration-persistence.ps1` check 7 - exactly one
  `= yaml.load(..., Loader=CSafeLoader)` in the run adapters, a direct
  `from yaml import CSafeLoader`, and no `safe_load`, other `Loader=`, other
  loader import or `__with_libyaml__` there. Proven non-vacuous four ways.
- **Declared compatibility changes, pinned both ways** in
  `backend/tests/test_run_store_loader.py`: tab after a colon and tab in a flow
  sequence now accepted; literal `\uD800` and `\U00110000` now
  `RunConfigurationInvalid` (the latter was an untranslated `ValueError`); ~600-
  deep flow nesting was an untranslated `RecursionError` and is now the run
  parser's own depth refusal. 34 further probes give equal outcomes. Inherited
  policy unchanged: unknown top-level fields ignored, duplicate keys keep the
  last value.
- **Counts:** canonical hit 1 parse, inventory N, fallback N, create 2N+1 - now
  asserted at the loader, not just at `read_run_record`.
- **Tools:** `tools/run-store-evidence.py` (`runtime` is the installation check
  named in README and in the diagnostic; `compare-corpus` is read-only and
  hashes; `seed`/`measure`/`serve` write only to a directory outside `var/`,
  and refuse one inside it). `tools/run-store-browser-evidence.mjs` times Runs,
  setup and run detail in headless Chrome.

### The numbers, and what they do not say

Owner corpus 223 docs / 1,504,668 B: equal under both readers. Composed
in-process at 223, warm medians: inventory 4.14 s -> **0.73 s**, setup 9.43 s ->
**1.57 s** - both inside the budgets at the server. At 300 generated records
(2,305,440 B) the warm medians are 1.09 s / 2.26 s, **both over budget**: 300 is
an observed breach point, and where between the two corpora the server stops
meeting the budgets is not established. At 500: 1.93 s / 4.06 s; at 2,000:
6.8 s / 34 s (wide ranges). The browser is a separate and worse result.
Browser, dev server, 223-231 records, CPU ~50 %: Runs **1.46-1.48 s** by
navigation, 1.32-1.37 s in-app (API ~0.67 s, the rest React dev-build
rendering); setup through populated run detail, one clock, **median 1.86 s
[1.73-2.37], 2 of 7 samples over 2 s** (the created summary on the setup page
alone: 1.62 s). **T022A criterion 2 stays open: the 1 s inventory budget is
missed on the dev server.** Quote conditions with the numbers: loaded samples
on this workstation ran 2.5-4x slower (setup through detail 4.8 s at 86 % CPU).

### What this leaves open

- **Deep flow nesting kills the process (open Architect/owner decision).**
  libyaml's C composer overflows the native stack at ~2.5-3k levels on Windows,
  ~20-30k on Linux - inside the 256 KiB bound - where the baseline raised
  `RecursionError`. Pinned by
  `test_flow_nesting_a_few_thousand_deep_ends_the_process`. A pre-load nesting
  bound would be a new refusal rule; not added.
- **The inventory budget.** Remaining cost at 223: ~0.65 s client rendering in
  the dev build, ~0.37 s PyYAML building Python nodes and resolving scalars on
  top of libyaml, ~0.07 s domain parsing. O(N) retained. Demonstrated server
  envelope: 223 records / 1,504,668 B passes; 300 / 2,305,440 B breaches; the
  threshold between them is not established. The browser misses inventory
  already at 223.
- **No CI exists**; the backend test `test_the_installed_pyyaml_carries_libyaml`
  and `tools/run-store-evidence.py runtime` are the gates. Verified at runtime
  on Windows x86-64, Linux x86-64 and Linux aarch64 (emulated); macOS only at
  the wheel-contents level.

## T024 - Daytime PV, storage and addressed load service

The first electrical world. A Kobo-like Site runs a daytime interval in the Lab:
PV, a battery and three separately addressed loads, a controller that reads a
local view and requests battery power, a declared-cascade resolver that
accepts what the installation allows, and exact energy balances. The generator
is not modelled (T025).

### What it settled in code

- **`EXECUTION_CONTRACT_VERSION` is 9** (`D-2026-09-29-t024-option-c-and-reserve-override`).
  The ledger paragraph names three moves: model-owned needs and Site Controls
  frozen in the identity, `a-control-override-replaces-its-baseline` in
  `DISPATCH_RULES`, and `COUPLING_RULES` (local view, intent versus acceptance,
  declared cascade, segment split, exact balance). New bound case
  `battery-state-of-charge-limits` (FAIL_RUN). Every Draft below 9 reads and is
  refused execution.
- **Option C.** `ModelProfile` gained `foundation_needs`, `site_control_needs`
  and `initialization_needs`; `SupportedState` gained an optional carrier
  `component_type` for unbound component states. Run setup resolves each need
  at every component of the bound type and freezes a `FrozenModelNeed`
  (declared_by, answered_by, Foundation version and valid_from, property
  source and version) in `DeterministicIdentity.model_needs`; Site Controls
  freeze as `FrozenSiteControl` in `site_controls`. Absent answers BLOCK:
  `INITIAL_VALUE_NOT_RESOLVED` at the address, and new
  `SITE_CONTROL_NOT_RESOLVED` at `site-control:<key>`. A run-start state of
  charge the scenario does not state blocks at `battery-state-of-charge@<battery>`.
  A version-9 run document omitting either collection is refused; below 9 they
  read as empty. Provenance rows render on the Draft's frozen table.
- **Foundation.** Six electrical properties (`pv-rated-power`,
  `inverter-ac-limit`, `battery-energy-capacity`, `pcs-charge-limit`,
  `pcs-discharge-limit`, `pcs-conversion-efficiency`) and an optional typed
  `site_controls` section: `source-priority` and `critical-load-priority`, each
  an ordered list naming every component of its member types exactly once.
  Existing Sites parse unchanged. Rendered on the Foundation Controls section.
  The control-properties note no longer says nothing reads them.
- **Profiles.** New `daytime-mini-grid` v1 beside the unchanged
  `minimal-fuel-tank` v1. Publication profile **3** adds six electrical paths;
  a declared path whose state the selected model does not produce is skipped,
  so a fuel run grows no electrical column.
- **Kernel.** `ModelSpec` gained an optional `Coupling` (prepare, view, decide,
  resolve) and `measured_interval_states`; phases D-F call it, G applies only
  the accepted stock accounts (origin `ACCEPTED_FLOW`), H checks every declared
  balance and the stock account exactly from the named flows. `StateHandler`
  gained a `ceiling`; `ComponentRelation` gained `many`. The kernel imports no
  electrical pack, guarded in `tools/checks/dependency-direction.ps1`.
  Contract records live in `contracts/assetops_contracts/control.py`;
  `BoundaryState.control_step` carries view, intent and acceptance, and is left
  out of the digest when absent, so fuel digests are unchanged in shape.
- **Pack** `simulator/assetops_simulator/packs/minigrid.py`: PV potential =
  rated x irradiance / 1000, capped by the inverter (clipping); battery SOC in
  %, 95 %-style one-way efficiency each direction; the controller requests the
  deficit (or the whole demand when the battery precedes PV) above the reserve
  in effect, or the surplus to charge; the resolver clips by PCS limit, energy
  above the reserve and headroom, serves loads in critical priority, curtails
  the rest; segments split where a forcing window starts or ends in a step.
- **Host.** `model_for(run)` selects the model by the frozen profile identity;
  model needs reach the kernel as initial values answered by the Foundation.
  The Lab projection gains `electrical` and the execution artifact is schema
  **3**; schema-2 records read with no electrical view.
- **Shipped content.** Template `kobo-mini-grid-60kw` and scenarios
  `kobo-daytime`, `kobo-daytime-overcast` (with the 16:00-18:00 reserve
  override to 15 %) and `kobo-daytime-larger-mill`, targeting `KOBO-001`.

### The demonstration, in numbers

Sunny: no load unserved, battery full at 100 % by early afternoon and PV
curtailed after, 7 kW clipped at 12:00, SOC 55 % -> 89.47 %. Overcast: the
battery holds the 30 % reserve, 56.9 kWh of mill and 6.3 kWh of residential
demand unserved, clinic fully served, and the override carries the evening to
15 %. Larger mill: residential demand unserved in the evening (19.865 kWh),
SOC ends at the reserve. 30 kW requested through a 22 kW PCS: accepted 22 kW,
SOC falls 55/19 %, 2 kWh unserved in the step, next PCS reading 22 kW.

### What this leaves open

Carried in `.ai/MILESTONE_REVIEW_BACKLOG.md` under "Carried from T024": the
controller decides once per step; "battery first" semantics; one of each
electrical machine; the kernel's fuel default import; electrical readings not
yet published (T026); ratios approximated on screen; priority lists
baseline-only; one CDP hang in layout evidence. `var/sites` gained `kobo-001`
(created through the product for the browser evidence).

### T024 fix round 1

Codex review R1-R3 closed on the branch (`.agent/T024-review-packet.md`, "Fix round 1"). Setup now: blocks a scenario/run value at a model-owned Foundation address while still resolving the Foundation's need; blocks needs and controls when the Foundation's `valid_from` is after run start (`_instant`); and validates the single-bus topology, freezing `FrozenBusAttachment` rows (`bus_attachments`, optional in the run document, required by the model at execution) under the new blocking kind `ELECTRICAL_TOPOLOGY_NOT_CONNECTED`. Open: connections are undirected; offset instants unreachable through setup.


## T025a - Generator lifecycle and healthy full-site runtime

In review (`.agent/T025a-review-packet.md`). Contract 9 kept, additively
(`D-2026-09-29-t025-generator-policy-package`).

### What it settled in code

- **Kernel discrete state.** `DiscreteStateSpec`, `DiscreteValue`,
  `TransitionRequest` (`kernel/model.py`); `ModelSpec.discrete_states`,
  `StepContext.discrete`, `Coupling.due` (phase A, before the sample) and
  `Coupling.commit` (phase F, before the resolver). The kernel validates every
  edge and records `DiscreteTransition` (address, previous/next, phase, cause,
  controller ref, instant). `BoundaryState.discrete` / `discrete_for_step`,
  `PrivateTrajectory.discrete_transitions` and
  `FrozenWorldInputs.discrete_initial_values` enter digests and identities only
  when non-empty. `KERNEL_VERSION` stays 1.
- **Typed enums.** `DISCRETE_UNIT = "state"` (`contracts/control.py`); view,
  request and acceptance values are text exactly in that unit, checked on
  construction. Scenarios author a discrete initial value as `value: STOPPED,
  unit: state` (CAUSAL_INPUT, scenario-owned, initializes only).
- **Profile `mini-grid` v1** (`runs/profiles.py`, `packs/mini_grid.py`):
  daytime states plus `generator-state`, `fuel-tank-volume` and seven Option C
  needs (rating, SFC, start/stop thresholds, minimum runtime, start delay, tank
  capacity). New Foundation properties `start-soc-threshold`,
  `stop-soc-threshold`, `start-delay`, `generator-rated-power`; `min` is a
  model-need-only unit (`MODEL_NEED_ONLY_UNITS`), still no scenario unit.
  Bus paths may attach directly (`GENERATION`, via `None`); `FUEL_SUPPLY` is
  tank via generator. `DISCRETE_STATE_RULES` state the contract text.
- **Setup blocks**: initial RUNNING/STARTING or a number for a discrete state
  (`INITIAL_VALUE_NOT_RESOLVED`), a timeline entry on a discrete state
  (`STATE_NOT_SUPPORTED`, T035's), and new kind `LIFECYCLE_TIMING_NOT_ALIGNED`.
- **Lab.** `ElectricalView.generator` (`GeneratorView`); service counts
  `generator_to_load`. Artifact schema **4** only when a generator is recorded;
  every other record is still written as 3, byte-identical. API serves
  `electrical.generator`; `GeneratorPanels.tsx` renders it.
- **Shipped content.** Scenario `kobo-mini-grid-evening` (5-min, 12:00-20:00);
  template gains the generator policy (35/90 %, 5 min, 40 kW).
- **Merge gate** `host/tests/contract9_gate`: all 15 v9 Drafts from `var/runs`
  plus a within-step reserve Draft, captured before any shared change.

### What this leaves open

The owner's `var/sites/kobo-001` lacks the four new properties, so a
`mini-grid` Draft against it BLOCKS until its Foundation gains them. Under
Kobo's `[pv-array, battery, generator]` the battery serves ahead of a running
generator, so the state of charge hovers at the reserve while the generator
charges only when the battery is not discharging. Generator status is not
yet reported (T025b) or staged (T026).

## T025b - Generator policy recipes, reported status and A acceptance

Complete; owner accepted A on 2026-09-29 (`.agent/T025b-review-packet.md` is
also A's integrated acceptance packet; Codex ACCEPT WITH CARRY). Contract 9 kept; `D-2026-09-29-t025-generator-policy-package`.

### What it settled in code

- **`mini-grid` v2** (`runs/profiles.py`, `packs/mini_grid.py` `resolve_v2`):
  v1 unchanged. The stop threshold is a second overridable CONTROL
  (`STOP_THRESHOLD_OVERRIDE`, value in (start, 100]); `ModelProfile.step_aligned_forcings`
  makes setup block an off-step stop window as `LIFECYCLE_TIMING_NOT_ALIGNED`;
  overlap is the kernel's runtime `FORCING_VALUE_AMBIGUOUS`. `effective_controls`
  is (reserve, stop threshold) per step - nothing may assume index 0 is the
  only one. v2 measures generator power over the completed interval.
- **Shipped recipes** `kobo-mini-grid-prolonged` / `kobo-mini-grid-stop-60`
  (03:00Z-11:00Z, 5 min), identical but for one 60 % stop override.
- **Publication profile 4** (`LAB_PUBLICATION_PROFILE_V4`), v3 kept: typed
  `generator-controller/status` (unit `state`, 15 min, bias 0, dropout 40/1000)
  and 15-min generator power. An enum is marked by unit `state`; numeric error
  on it is refused (`refuse_numeric_error_on_a_discrete_signal`). A status at T
  reads phase-B `BoundaryState.discrete`.
- **Artifact schema 5** only when a `state` reading is recorded (4 and 3 keep
  their bytes). `GeneratorStepRow.reported_state/reported_quality`;
  `GENERATOR_STATUS_REPORTED_NOT_STAGED` for profile-4 runs.
- **Envelope** schema 1 and the fuel-only mapping unchanged;
  `refuse_an_enum_under_schema_1` refuses an enum mapping or allowlist entry.
- **Frontend.** Client guards type the step's reported status (closed members,
  qualities) and refuse a `state` reading carrying a decimal or bias.
  `GeneratorPanels` shows reported status beside physical state (fact and
  series column, profile-4 only); `ElectricalPanels` names each effective
  control by address; the stage panel names each `state` signal as observed,
  not staged. Real-backend fixture `kobo-mini-grid-stop-60-execution.json`.
- **Layout evidence** pins the T025a run to `mini-grid@1`/profile 3 and adds
  three v2/profile-4 runs; it creates three more Drafts per run in its store.

### What this leaves open

Setup preselects no publication profile when two are offered (owner question).
The owner's `var/sites/kobo-001` lacks the status signal and generator
properties; demo on a Site created from the current template. Content digests
differ across separately created Drafts (run metadata); reproduction is
trajectory/step equality. Generator status staging is T026's; start-failure
causes are T035's. Demo values await the owner's hands-on check.

## T025c - Persisted Lab history, addressed charts and run identity (L1a)

Complete; owner accepted 2026-09-30 (packet `.agent/T025c-review-packet.md`). Contract 9
kept: an artifact-only addition, no execution-contract bump.

### What it settled in code

- **History contract** `contracts/assetops_contracts/lab_history.py`
  (`LAB_HISTORY_SCHEMA_VERSION = 2`; 1 existed only before the R1 fix and now
  reads as an unknown schema): manifest, five families (`state_samples`,
  `intervals`, `observation_attempts`, `timeline`, `drawing`), each
  `RECORDED`/`NOT_APPLICABLE`/`UNAVAILABLE`; sources `LIVE_SESSION`,
  `PERSISTED`, `LEGACY_ARTIFACT`, `NOT_RECORDED`, `WRITE_FAILED`,
  `HISTORY_UNREADABLE`. Sample phases `POST_EVENT`, `FOR_STEP`,
  `PRECEDING_INTERVAL` (interval samples are kWh over the step in "model unit").
  Only the backend's `simulator_lab_api.py` and `execution_ports.py` may import
  it (`dependency-direction.ps1`, with an anti-vacuity count).
- **Artifact layout** (`host/lab_execution.py`, `host/lab_history.py`): the
  projection document is byte-identical; a TERMINAL artifact appends
  `--- # assetops-lab-history` and one line of canonical JSON with a blake2b
  `history_digest` (distinct from the trajectory digest), written by one atomic
  rename. The digest covers a manifest `projection_binding` over the
  projection's `signals`, `reporting_gaps` and `electrical` view, so an edit to
  the projection alone reads back as `HISTORY_UNREADABLE` (R1 fix). `read()` never parses it; `read_history()` is strict and writes
  nothing. RUNNING artifacts carry none. **Any tool that `yaml.safe_load`s a
  terminal artifact whole now fails on the second document** - split at
  `HISTORY_MARKER` first.
- **Port/route**: `HostLabExecution.history(run)` / `LabExecutionPort.history`;
  gated `GET /runs/{run_id}/execution/history` (`history_payload`). A live
  session answers `LIVE_SESSION` (no digest) even after it completed; the
  artifact answers `PERSISTED` only when no session is held, i.e. after a
  restart. The simulator gained read-only `Execution.applied_events` and
  `bounded_transitions`.
- **Frontend**: `runHistory.ts` (types/guard/fetch), `HistoryInspector.tsx`
  (coverage + records at one boundary), `historyChartModel.ts` (pure chart
  model, stale rule mirroring `reading_at`), `HistoryCharts.tsx` (the only other
  module allowed an `<svg>`, inside `.history-chart__scroll`), `RunHeader.tsx`.
  PV potential/accepted/curtailed/clipped and battery signed power are read
  from the execution projection's `electrical.steps` (host sums); loads,
  SOC, reserve/stop threshold, generator output, fuel and generator state from
  the history. `--series-1..4` tokens added. One selection drives the range
  input, every chart cursor, the exact-value table and the boundary select.
- **Guards/evidence**: `shell-overflow.ps1` admits `HistoryCharts.tsx` under its
  own region rule (three new failure modes, proven). `layout-evidence.mjs` adds
  the T025c section and a `--readback <file>` pass for after a host restart
  (`ASSETOPS_EVIDENCE_ENV` hashes the artifact). Fixture generator
  `host/tests/make_history_fixtures.py`.

### What this leaves open

- The single-run history payload is ~1 MB for the 8 h mini-grid window; full
  wire kept (a selection re-render ~55-65 ms). First paint of the whole run
  screen after a host restart was 1.6-3.2 s after the history response,
  dominated by the page's other panels, not measured in isolation.
- Live history is recomputed on every read; T025d's auto-play must not fetch it
  per step. The history read re-parses the projection YAML.
- Charts are keyed by this model family's state keys (`pv-ac-power`,
  `load-served-power@<load>`, `battery-*`, `generator-*`, unit `L`/`%`); an
  unmatched reported signal is listed as not charted rather than dropped.
- SLD overlays, the causal timeline, requested/accepted panel and playback are
  T025d's; `bus_attachments` is recorded for it.

## T025d - Lab SLD, causal inspection and playback (L1b)

Complete; owner accepted 2026-09-30 (packet `.agent/T025d-review-packet.md`).
Contract 9 and history schema 2 kept: wire additions only, no persisted change.

### What it settled in code

- **Wire** `simulator_lab_api.py` `history_payload(history, run)`: per-interval
  `balance_identities` (exact source/sink sums, residual), `reporting_gaps`,
  and `drawing_context` (`VERIFIED | NOT_RECORDED | DISAGREES` against the
  run's frozen bus attachments; attachments with connection ids only when
  VERIFIED). Live `history()` reports `WRITE_FAILED` (backlog C3, closed).
- **Shared SLD slots** `sites/SiteSingleLineDiagram.tsx` `SldSlotContent`:
  node and connection slots (`ALONG|AGAINST|NONE`, text, detail, optional short
  `label`), arrow marker, contents table, headless `ConfiguredSingleLineDrawing`.
  No slots = Foundation screen unchanged. Labels are short and centred; full
  statement in `<title>` and the table (sentences overlapped boxes, measured).
- **Lab composition** (shell): `intervalDrawingModel.ts` (`bindDrawing`,
  `drawingSlots`, `FLOW_ROLES` keyed by mini-grid flow ids, `drawnValue`),
  `IntervalDrawing`, `IntervalInspection` (C4), `historyTimelineModel` +
  `HistoryTimeline` (C3). One selection = the interval that ENDED at T.
  `HistoryCharts` labels a held reading with its own support (backlog C1, closed).
- **Playback** `shell/runPlayback.ts` `PlaybackScheduler`: one one-boundary
  guarded Step in flight, next only after its answer plus a wall delay
  (0.25/1/2/5 s); stops on pause, terminal, refusal, 404, network error,
  timeout (20 s, re-read), hidden tab, unmount; `laterExecution` never moves the
  display backwards. `RunFrame` disables Step/Run to end while it schedules and
  re-reads history/stage only when it stops. Reload starts paused.
- **Proof** `host/tests/test_lab_cockpit_window.py` (window [55,135) derived
  from template and scenario: event phase, gap, PCS- and reserve-limited
  requests, reversal, balance; duplicate step, restart, pacing digests, reload
  with the kernel unreachable). `layout-evidence.mjs` T025d section + readback.

### What this leaves open

- Drawing binding needs the current Site read to be the frozen Foundation
  version; a future Foundation edit path would make old runs "unavailable"
  (no presentation snapshot is persisted). `DISAGREES` is unit-tested only.
- Flow roles are frontend-keyed; a new model family needs its own roles.
- History read ~1.15 MB for the 8 h window; first chart 3.7 s after the
  response on a cold reload (informational); selection re-render 118-143 ms.
- Trajectory digest is run-bound, so pacing equality across Drafts is shown on
  the reading digest and inputs identity; same-run pacing is host-tested.
- Backlog C2, C4, K1, K3 untouched.

## T025e - Lab cockpit organisation and live playback (L1c)

Complete; owner accepted 2026-10-01 (packet `.agent/T025e-review-packet.md`, evidence
`.agent/T025e-layout-evidence.txt`). Contract 9 and history schema 2 kept;
`contract9_gate` unedited. Three phases; handoffs in `.agent/`.

### What it settled in code

- **Wire** `?since_boundary=n` on the gated history read: append families
  (`HISTORY_APPEND_FAMILY_KEYS`, `simulator_lab_api.py`) keyed by the boundary
  that records the row (intervals, exposures and `electrical_steps` on
  `from_offset`); static families empty; `delta` envelope; typed refusals.
  Prefix stability proved per family in `host/tests/test_lab_history_prefix.py`.
- **Option R** `LabHistory.electrical_steps`: the projection's own
  `ElectricalStepRow`s, joined only where intervals are recorded (live
  projection or the binding-verified stored one); never persisted in the
  history document. Charts read `pv_output` and signed `battery_power` from it.
- **Client** `liveHistory.ts` pure merge + slice index; `runFrameState.ts` one
  owner (execution, history, fullReadDue, cursor); `RunFrame.commit` one read
  and one dispatch per answer; `PlaybackScheduler` awaits `show`.
- **Layout** control strip (`data-control-strip`), then `HistoryCockpit`
  (drawing beside inspection in a fixed row, cursor, charts, timeline, all
  reserved before the first boundary); nine closed `Disclosure`s (new `ui/`
  primitive, `data-disclosure`). Drawing, inspection and raw records are
  memoised on slice/row references; chart points cached per row (WeakMap);
  playing status is one sentence, in-flight on `data-playback-in-flight`.
- **Evidence** `tools/layout-evidence.mjs` opens disclosures before measuring
  and has a T025e section (per-frame sampling, pinned MutationObserver, delta
  bytes, server p95 at boundary 96, `run-frame-commit` measures).

### What this leaves open

- Server delta p95 45.9 ms against 50 ms (within 8 %); capture memoisation
  (the named stop) not taken.
- Charts start below an 800 px first viewport; the charts region grows once at
  the first recorded interval (panels derive from recorded rows).
- A second tab stepping the run can make recorded > clock until the next
  answer (not clipped). The screen-test fake history has no intervals.
- Backlog C2, C4, K1, K3 untouched; T026 adds dispatch panels here.

## T025f - Template versioning and site lineage staleness (S0)

Complete (fast lane; packet `.agent/T025f-review-packet.md`; Claude review ACCEPT WITH CARRIES). No
contract move; no Site record rewritten; no run reads a template.

### What it settled in code

- **Template v2.** `kobo-mini-grid-60kw` is `template_version: 2`; the four
  generator properties T025a added (`2f076d3`) carry `source_version: 2`.
  T025b's status signal and mapping (`0dc42c0`) have no per-entity provenance
  field, so only the bump records them.
- **Fingerprint guard** `backend/tests/test_site_template_fingerprints.py`:
  `PINNED_TEMPLATE_FINGERPRINTS[(id, version)]` = SHA-256 of the parsed
  document as sorted canonical JSON (comments and order are not content).
  Changed content at a pinned version fails naming the template and the bump;
  an unpinned version fails asking for its pin. Kobo v1 is deliberately
  unpinned (it named two contents).
- **Lineage read** `sites/lineage.py` `assess_template_lineage`: `CURRENT`,
  `BEHIND`, `NOT_SHIPPED`, `NO_TEMPLATE`, `UNRECOGNISED_VERSION`, computed on
  read. Served only at gated `GET /api/simulator-lab/site-template-lineage`
  (the catalog is gated; `create_app` must not touch it when closed). The
  operator `/api/sites` shapes are unchanged.
- **UI** `sites/siteTemplateLineage.ts` (client, `templateLineageNote`,
  `useSiteTemplateLineage`) and `sites/TemplateProvenanceText.tsx`: a
  `cell-secondary` line under "Created from template" on the Sites index,
  Overview and Foundation ("Created from v1; current template is v2"). The
  client is handed out only by `simulatorLabSiteTemplateLineage(flags)`,
  resolved once in `App`; closed gate, no read and no note.

### What this leaves open

- The note appears only with the Lab gate open (AC4's gated-surface rule).
- A lineage read that fails shows the recorded provenance alone (no note),
  not an "unknown" note.
- Scenario fingerprints are T025g's; the same digest shape is reusable.

## T025g - The run is the only join of scenario and site (S1)

Complete; owner accepted 2026-10-02 (packet `.agent/T025g-review-packet.md`; `USER_REVIEW_REQUIRED: true`).
Rule `D-2026-10-01-run-binds-scenario-to-site`; contract stays 9 (gate unedited).

### What it settled in code

- **Parser.** `target_site` optional legacy (parsed only when present; null or
  malformed refused); `site_contract: {description}` only (`scenarios/parsing.py`).
- **Run setup** binds the site in the request; only the no-topology refusal
  remains (`runs/service.py` `_refuse_site_without_topology`); legacy
  `target_site` ignored.
- **Lineage** `FrozenSiteBinding.template_lineage` (`runs/models.py`), frozen
  from `SiteRecord.template`; `None` = not recorded (pre-T025g runs). Outside
  `FrozenWorldInputs`. Served as `template_lineage {state RECORDED |
  NO_TEMPLATE | NOT_RECORDED, template_id, template_version}` on `run_summary`
  (top level and `deterministic_identity.site`); `RunHeader` and the setup
  summary render it (`templateLineageText`).
- **Scenario domain reads no site.** `ScenarioDetailService(repository)`;
  resolution code, state sets and payloads gone. Detail payload carries
  `scenario.site_needs {addresses[], device_sources[]}` from
  `scenario_site_needs()`. AST guard in `test_run_binds_scenario_to_site.py`
  allows only `validate_site_id` and `SiteConfigurationInvalid` from `sites`.
- **Picker** (`RunSetupFrame` `SitePicker`): list + per-site `getSite` + gated
  lineage client; nothing preselected; Create disabled until picked.
- **Shipped scenarios v2** (no `target_site`, `site_contract.description`).
  `test_scenario_fingerprints.py` pins `(scenario_id, version)` via the shared
  `backend/tests/content_fingerprint.py` (T025f's guard uses it too) and fails
  on site-naming keys.
- **Join proof** `host/tests/test_t025g_join.py` (READY current Kobo, BLOCKED
  pre-T025a content, v1 refused).

### What this leaves open

- A missing status source does not block (publication declaration only); the
  Draft records its absence. Known deviation in the packet.
- Scenario detail and run setup scroll the page at 375 px (shared FactList and
  PageHeader); below the measured widths.
- `tools/layout-evidence.mjs` cannot complete on an isolated `var/` (needs the
  owner's MG-006 scenario).
- Superseded scenario versions are not retained in the store (git only).
- Picker reads one site detail per site; a summary field would be needed at scale.

## T026 - Dispatch-capable evidence (B extension)

Complete; owner accepted 2026-10-02 after hands-on check (Claude review ACCEPT after fix rounds 1-2; Codex retrospective pending).

Branch `task/T026-dispatch-capable-evidence`; packet `.agent/T026-review-packet.md`,
handoffs `.agent/T026-phase-{1,2,3a}-handoff.md`. Contract stays 9
(`host/tests/contract9_gate` green, execution_contract.py untouched); every change
reaches new Drafts only.

### What is settled in code

- **Schemas.** Envelope schema 2 (families MEASUREMENT / STATE enum member /
  POLICY / OPERATIONAL records; schema 1 still readable, stage schema stays 2,
  `envelope_schema` is the frozen mapping's version). Publication profile 5,
  `mini-grid` v3, site template v3, scenario `kobo-mini-grid-degraded-evidence`.
  Profiles 3/4 keep the fuel-only schema-1 mapping.
- **Evidence.** Capability signals (`pv-inverter-controller/available-power`,
  `battery-pcs-controller/discharge-capability`) exist only under v3; policy
  records (Foundation version, valid-from, source), override records from the
  scenario CONTROL overrides, generator status staged as a typed member. Two
  imperfections: one reporting gap and one hold (`PublicationDelayWindow`: a
  publication due inside the window is released at its end; refused if it would
  reorder, `PUBLICATION_DELAY_REFUSED`). A held envelope enters the stage only
  at its release (`publish(reached_offset_minutes)`, `_still_held`).
- **History schema 3** (`lab_history.py`): append families `records`
  (key occurrence) and `publications` (key release, `HeldPublication`); 7
  coverage rows; schema 2 reads and discloses both UNAVAILABLE; prefix proof
  `test_lab_history_prefix.py` covers both.
- **Screen.** Frontend mirrors both append keys (`liveHistory.ts`); records,
  declared gaps clipped to recorded time and `Publication delay` entries in
  the Applied timeline REPORTING lane; inspector "Publication" column
  (sensor gap / delay / none recorded); stage "Arrival" fact; capability tracks
  join PV and battery curves (second reported track = square marks, dashed
  join); "observed, not staged" shown only when the frozen mapping lacks the
  signal, host statement `GENERATOR_STATUS_REPORTED_STAGED` otherwise.
- **Layout evidence** follows the run's mapping (`EXPECT_UNSTAGED` by profile),
  T025e AC12 section now measures a profile-5 degraded Draft, new T026 section.

### Measurements (this machine, 2026-10-02)

- Delta bytes max 20,249 B (limit 32,768); tick commit p95 30.5 ms max 34.6.
- Server delta p95 at boundary 96 **misses 50 ms**: 108-134 ms through the
  preview proxy on profile 5, 131.7 ms on the T025e profile-4 stop-60 run on
  the same day; in-process (`delta_ms` method, packet) pre-T026 tree 68-93 ms,
  head profile 4 84-95, head profile 5 95-97. T025e's 45.9 ms is not
  reproducible on this machine today; T026 adds roughly 0-15 %.
  Memoisation (backlog T025e C2) NOT taken, owner/Architect to rule.
- Stage: 329-333 envelopes, 267 KB final, per-control write ~36-47 ms CPU.

- **Override issuer (fix round 2, C1,
  `D-2026-10-02-scenario-states-override-issuer`).** Optional `issued_by: OPERATOR`
  on scenario EVENT entries (`TimelineEntry`/`FrozenForcing.issued_by`, in the
  frozen identity only when set); refused except on the stop-threshold and
  battery-reserve forcings. Host `record_inputs` and backend delay refusal read
  it; degraded-evidence v1 declares it (re-pinned, no bump); stop-60 unchanged
  and publishes no override record under profile 5.

### What this leaves open

- Carried to the backlog: AC15 delta p95 misses 50 ms before T026 too
  (performance task, T025e C2); T028 to decide whether stop-60's policy change
  is a policy record.
- Stage order in a stepped run is arrival order (pre-existing); a run stopped
  inside a hold shows "No publication delay recorded" for that reading.
- `kobo-degraded-evidence-deltas.json` fixture is 1.38 MB.
- `tools/layout-evidence.mjs` needs `ASSETOPS_LAYOUT_SITE=MG-006`, a store of
  `.demo/T025c` runs with no executions, and backdated Site `valid_from`; with
  that, 3 pre-existing "blocked table" claims fail (run-setup against MG-006 is
  READY, no blocked table) - environment, not T026.
- No shipped world curtails PV (available == output); T026A owns bias/noise.

## S2-01a - Registered Kobo Lab basis (in review)

Branch `task/S2-01a-registered-lab-basis`. Phase 1: commits `ce65b8d`, `fabbfc2`, `f1b78bd`, `ad0b210`. Phase 2: commits `8d0e1d3`, `7c2b271`, `d0042fb`. Packet `.agent/S2-01a-review-packet.md`; phase-1 anchors `.agent/S2-01a-phase-1-handoff.md`. Decision `D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary` with its amendment; Architect answers are in `.agent/architect-S2-01a-answers-2.md`.

### What it settled in code

- Selection: `sites/registered_basis.py::select_registered_basis` picks the Foundation and binding set at the run's source start, as recorded at `knowledge_at`. It refuses with typed `BasisRefused` codes:
  - not registered, inconsistent, or crossing a boundary (`end_time` included);
  - a role-set mismatch, or an invalid Site row;
  - any snapshot error.
- Snapshot verification: `binding_service.acquisition_snapshot(now=)` classifies a snapshot as CURRENT or HISTORICAL. A historical one is verified from its pinned identity, and current-row gaps are reported separately.
- Run adapter: `runs/registered_basis.py::RegisteredLabBasis` supplies the Site record, the binding-derived links and a `RegisteredBasis`.
  - Links are frozen from binding rows only: `mapping_id` is the binding revision ID, and the asset code must be in the selected Foundation.
  - The frozen display name is `site_display_name`.
  - `RegisteredBasis.__post_init__` re-hashes the stored snapshot text, so a tampered stored run is refused on reload.
- Run read: `simulator_lab_api.configuration_basis_payload` reports `LEGACY_FILE`, or `REGISTERED` with:
  - the revisions, the hash and the two selecting instants;
  - `site_metadata.source = CURRENT_SITE_ROW_AT_SETUP`;
  - `accepted_evidence: false`.
- Lab writes: `_refuse_if_imported(record, *, commit=False)` is the one shared boundary.
  - A registered Draft may start, step and run to end.
  - Commit refuses any registered run with `REGISTERED_COMMIT_UNAVAILABLE` (409).
  - A pre-import YAML Draft of an imported code keeps `SITE_AWAITING_MIGRATION`.
- Stage read: `_frozen_basis` reports `configuration_store: REGISTERED` with the basis and `can_release: false`. Legacy Drafts are unchanged.
- Guard: `configuration-persistence.ps1` rule 8 requires the plain boundary call on start, step and run-to-end, and `commit=True` on Commit. It also requires the registered Commit refusal to come first in the boundary. Both parts were proven non-vacuous.
- Host: no code change. `host/tests/test_registered_kobo_execution.py` shows:
  - the ten binding links, including `generator-controller/status`, resolve as frozen;
  - the two legacy-only capability links are absent;
  - registered and legacy daytime runs produce identical observations;
  - public reports carry no cause, oracle, intent or private keys.
- Frontend:
  - Setup labels each picker row with its configuration store.
  - For a registered Site, setup reads the configuration the start selects and sends that version. It blocks Create with the snapshot reason and shows `reasonCode`.
  - The run page has a `ConfigurationBasisPanel`, with name and time zone labelled as setup metadata.
  - The Stage shows the frozen basis.
  - `commitBasisBlock` disables Commit when `can_release` is false or the basis is unreadable.
- Layout evidence: `ASSETOPS_LAYOUT_S2_01A_RUN=<run_id> node tools/layout-evidence.mjs <base>` measures a registered run at 1280 and 640 px.

### Open

- Q4: two KOBO-001 capability signals are unbound, so a profile-5 run reports them as unconfigured.
- Q5: the imported Foundation lacks generator parameters, so mini-grid models are BLOCKED. Generator status is proven at link resolution only.
- Backlog: Site name, type and time zone are current-row metadata (snapshot v1 does not version them). Asset-code identity is mutable before S2-02.
- The full `layout-evidence.mjs` run stopped after the run-setup sections because the browser stopped answering (no FAIL before that point).


## S2-01b - Durable simulated gateway (in review)

Packet `.agent/S2-01b-review-packet.md`; phase handoffs `.agent/S2-01b-phase-{1,2,3a}-handoff.md`.

- Wire: `contracts/assetops_contracts/source_envelope_v3.py` (length-delimited message id, canonical V3 text), `ingestion_batch_v2.py` (sealed, bounded, source-homogeneous Batch V2; digest excludes `payload_sha256`), `gateway_report.py` (`assetops.simulated-device-report` v1, the only text that crosses the process boundary), `gateway_stage.py` (`RegisteredStageView`, `GATEWAY_LEDGER`, upload always `PENDING`). Vectors: `contract-fixtures/source-envelope-v3-vectors.json`.
- Gateway: `gateway/assetops_gateway/` is a separate process (`python -m assetops_gateway serve --config`), importing contracts only. WAL SQLite ledger with single-writer file lock, immutability triggers, per-(gateway,source,epoch) sequence, `report_admission` dedupe, `mapping_hold` holds; authenticated local IPC with a protected credential file.
- Host: `host/gateway_publication.py` publishes a registered run's public reports through `assetops_gateway.ipc` only (guarded); `lab_execution.py::_stage` for registered runs uses the gateway; a delay-window run is refused before activation. `execution_adapter.py::frozen_resolutions` makes the frozen identity the resolution authority.
- Profiles: `registered-kobo-publication` v1 = v3 plus `resolution="0.000001"` on each numeric signal; quantized half-even after bias in `simulator/.../observation/transform.py`; frozen as `DeterministicIdentity.signal_resolutions` (written only when non-empty). Refusals `PUBLICATION_PROFILE_REQUIRES_REGISTERED_SITE`, `PUBLICATION_UNIT_MISMATCH`. Every run's `frozen_inputs` gains a "Device resolution" row.
- API: `GET /runs/{id}/stage` returns `registered_stage_payload` for a registered run (never the file Stage); `signals[].resolution`; profile summary `device_resolutions`, `requires_registered_site`.
- Frontend: `runSetupClient.ts::isGatewayLedgerStage` accepts only pending, receipt-free, non-eligible ledgers and yields `status: "gateway"`; `GatewayLedgerView.tsx` renders it; `commitBasisBlock`/`releaseBasisBlock` block Commit and release for it. F1 closed: `releaseBasisBlock` blocks Resume/Retry for a committed legacy artifact whose Site was imported since. Run view shows a resolution column and half-step note; setup shows the profile's resolution and labels the two refusals.
- Q4: `ObservationView` docstring no longer says reported minus bias recovers a quantized or gap-hidden value exactly.
- Layout: `ASSETOPS_LAYOUT_S2_01B_RUN=<run_id> node tools/layout-evidence.mjs <base>`.

### Open

- ENUM is proved by a direct public generator-status observation, not by the daytime run (S2-02 owns a selectable generator-status run). Delay windows are refused only (S2-01c owns delayed admission).
- No product path writes gateway provisioning; it is an operator config file. No IPC idle timeout; Windows credential protection relies on the profile ACL.
- Whole-series republish per step is O(n); a long run needs a watermark. Hold rows are not byte-fixed (`seen_count`).

## S2-01c - Gateway diagnostics and fault scenarios (in review)

Packet `.agent/S2-01c-review-packet.md`; handoffs `.agent/S2-01c-phase-{1,2,3a}-handoff.md`; open questions `.agent/S2-01c-questions-6.md` (3, 4, 5 answered).

- Gateway ledger: schema 3 keys `seal_refusal` by `(source, epoch, snapshot, outbox_state)` (R1); `diagnostic_config` (frozen), `diagnostic_outbox` (one immutable report per cadence slot, READY only, never received), `health_observation` (contacts, injected faults). Schema 4 `publication_clock(lab_run_ref)` forward-only.
- Wire: `contracts/assetops_contracts/gateway_diagnostics.py` `GatewayDiagnosticsV1` + `DiagnosticConfig` (60 s cadence, 1 GiB/256 MiB WARN/STOP demo triggers); vectors `contract-fixtures/gateway-diagnostics-v1-vectors.json`. `publication_schedule.py` holds the Lab-private `PublicationSchedule`/`DelayedReport`.
- Service: STOP refuses acquisition before any write; `mapping_error_count` counts mapping kinds only; queue age on real-UTC `created_at`; `admit_at_run_clock` stamps V3 `published_at` from the scoped virtual clock. IPC ops `diagnostics`, `emit_diagnostic`, `advance_publication_clock`, `admit_at_run_clock`, `inject_fault` (fixture only; no Lab port method).
- Profiles/scenarios: `registered-kobo-publication` v2 (`publication_clock: RUN_VIRTUAL`, opt-in); `kobo-daytime-delayed-publication` v1 and `kobo-daytime-post-run-publication` v1 (closing window [710,725)); setup allows only a RUN_VIRTUAL reporting-path WINDOW ending at most one timestep after the interval (`runs/service.py` `_post_run_release_window`). Manifests `host/fixtures/gateway-fault-scenarios.v{1,2}.json`.
- Host: `lab_execution.py` `advance_publication` (`release_basis` LIVE_SESSION|STORED_SCHEDULE_ONLY; refusals CLOCK_NOT_SUPPORTED, CLOCK_BACKWARD, AHEAD_OF_WORLD, SCHEDULE_UNREADABLE, SCHEDULE_MISSING, INSTANT_INVALID), `publication_schedule`, `gateway_diagnostics` (AVAILABLE|GATEWAY_UNAVAILABLE).
- API: `GET /runs/{id}/publication`, `POST /runs/{id}/publication/advance` `{instant}`, `GET /gateway/diagnostics`; profile `publication_clock`; seal refusals carry `outbox_state`.
- Frontend: `runSetupClient.ts` `isRunPublicationSchedule` (no private fields, absent schedule never a list), `isGatewayDiagnostics` (unavailable carries no counters, no ACKED), optional client methods `getPublication`/`advancePublication`/`getGatewayDiagnostics`; `GatewayPublicationPanels.tsx` renders schedule, advance and diagnostics with clock labels on a registered run's Stage; setup names the profile's publication clock. F2: `releaseBasisBlock` blocks Resume/Retry while the basis is pending, unreadable or unreported.
- Layout: `ASSETOPS_LAYOUT_S2_01C_RUN=<run_id> node tools/layout-evidence.mjs <base>` (includes a fetch-intercepted Sealing-refused row).
- Fix round 1 (`D-2026-10-09-s2-ordered-publication-and-closing-boundary`): IPC `admit_at_run_clock` requires `at_instant`; the gateway advances the run clock to it in the admission transaction and, once the clock has passed it, answers replays only and refuses a new admission `PUBLICATION_INSTANT_PASSED` (`service.py` `_clock_at`, `_admit_in(replay_only=)`). Host `RegisteredGatewayPublisher.publish_in_boundary_order` + `lab_execution.py` `_release`: each reached boundary after the schedule's `admitted_through` watermark is admitted at its own instant (due delayed reports first), sealed per boundary; post-run leftovers go at the explicit advance instant. Undelayed `published_at == source_time`; run_to_end and single steps give identical envelope and batch bytes. Read `SCHEDULE_MISSING` for an executed run with no schedule and no session; Lab view renders gateway HELD releases as held.
- Fix round 2 (`D-2026-10-09-s2-publication-gap-and-batch-boundary`): `PublicationSchedule` persists `world_boundaries_completed` and `ordinary_stopped_at` and derives `ordinary_publication()` (NOT_STARTED|CONTIGUOUS|COMPLETE|INCOMPLETE|TERMINAL_GAP). `advance_publication` with no live session refuses `PUBLICATION_GAP` (both instants in the detail) before the Lab clock, the gateway or a seal moves. `_release` records `ordinary_stopped_at` when the gateway refuses an ordinary boundary `PUBLICATION_INSTANT_PASSED`. Read and advance refuse `SCHEDULE_MISSING` for an executed run even with a live session, and `_stage_registered_virtual` creates a schedule only before the execution artifact exists. The API schedule read carries `admitted_through`, `ordinary_publication` and `ordinary_stopped_at`. The panel shows an "Ordinary publication" fact (`data-ordinary-publication`), a `data-publication-gap` paragraph and the `PUBLICATION_GAP` refusal.

### Open

- Architect: questions-6 (legacy schedules without a boundary count, live terminal-gap clock movement, first-start schedule failure, refusal shape, which refusal is terminal). questions-5 answered in `.agent/architect-S2-batch-answers-2026-10-09.md`; questions-3/-4 in `.agent/architect-S2-01c-answers-4.md`.
- N1 (exact IPC key-set refusal kind) and N2 (HELD/SCHEDULE_MISSING strings at 640 px) carried to the S2 checkpoint.
- Carries C2 (AC5 diagnostic bytes across a real reconnect not asserted) and C3 (full seeded layout run unverified) for the S2 milestone checkpoint.
- A seal refusal after admission leaves a delayed report PENDING until the next advance. S2-02 owns upload, central receipt and diagnostic freshness.

