# Planner Handoff — T019 Narrowing Through T022

**Revised 2026-09-22**, after the Planner's first pass and two user decisions.
T021A is accepted as its own slice. T020A carries its own user-review
checkpoint. The coefficient's unit deadline is earlier than this file first
said, and the `READY` disclosure now has an owner for its retirement. Those
four changes are marked below.

Scope: feature-level guidance for the slices affected by the proposals the user
accepted on 2026-09-21. This is a scoped, disposable handoff, not a canonical
artifact. `.ai/PLANNING_GUIDANCE.md` stays general; this file carries the
per-slice content and should be deleted once T022 closes out.

Written by the Architect. **The Planner writes the task files.** Nothing here
is a task file and nothing here should be copied into one verbatim; task specs
are implementation guardrails and this is the reasoning they are cut from.

## Where the authority is

| Need | Read |
| --- | --- |
| What was decided and why it binds | `.ai/DECISIONS.md`, the five 2026-09-21 entries listed below |
| The durable rules | `.ai/ARCHITECTURE.md`, Causal Runtime Authority and Physical Property Ownership |
| Sequencing, dependency structure, and the surfaced seams | `.ai/FEATURE_MAP.md`, `Early Feature: Draft SimulationRun And Causal Runtime` |
| The full argument, worked example, and mock screens | `Docs/simulator-scenario-authoring-and-runtime.md` |

The five decisions: `D-2026-09-21-scenario-execution-contract-amendment-1`,
`D-2026-09-21-run-setup-outcome-vocabulary`,
`D-2026-09-21-projection-versus-composition`,
`D-2026-09-21-specification-reference-implementation`,
`D-2026-09-21-physical-property-ownership`.

## Three things that gate task files or implementations, not slices

**Revised 2026-09-22: the forcing-state decision has two deadlines, not one.**
This file originally put the whole of it before T021's task file. One part of
it is due earlier, and the earlier part is easy to miss because it looks like
a kernel question.

**The `dispatched-output` half is due before T020A is implemented.** Whether
generator output is promoted to a `FORCING_INPUT` on `generator-output-power`
decides the canonical unit of the Foundation consumption property: a
runtime-based model rule wants `L/h`, an energy-based one wants `L/kWh` and a
generator-output forcing to multiply it by. T020A is what writes that property
into the shipped template and into MG-001, so deciding it in T020A and
changing it later is a unit migration on a Foundation document and on an
instance created by copy. The carriers are the same either way, so only the
shipped value waits — but it waits on a user decision, not on the
Implementer's judgement, and a T020A that picks a unit to get unblocked has
made the decision.

**The rest is due before T021's task file is written.** What happens to
`site-load-demand`, `plane-of-array-irradiance` and
`fuel-level-reporting-availability`, and whether reporting-path authority
moves from the model profile to the publication profile. These decide what the
first kernel must model, so a T021 task file written before them would scope
the kernel by accident. The user owns it. Do not write T021's task file first
and patch it after.

**The four unpinned kernel semantics are due at the same time as that second
half.** Window
apportionment, observe-before-or-after within a step, a forcing outside its
declared window, and what happens after a bounded change. Each would let two
conforming kernels disagree, so each is `EXECUTION_CONTRACT_VERSION` business
and each must be *declared* rather than decided inside an implementation. If
they are still open when T021's task file is written, the task file must say
they are contract decisions returning to review, not choices the Implementer
may make.

## T019 — Draft run setup, narrowed before merge

Already built and in independent review on `task/T019-draft-run-setup`. This is
a narrowing of work in flight, not a new slice.

**Must deliver.** The removal of the cause-to-observation verdict from run
setup: the observation blocking reasons and their call site in the run-setup
service, the `OBSERVATION_NOT_ACCOUNTED_FOR` member of the blocking
vocabulary, and the test assertions that name it. The shipped Fuel Loss Draft
blocks on three `STATE_NOT_SUPPORTED` reasons rather than five. And
`reconcile_reported_observations` is relabelled in place as a reference
implementation for the execution contract, with its expiry stated as T021.

**May not.** Change the `BLOCKED` outcome itself, which the user accepted and
which is unchanged. Widen the shipped model profile. Resolve the residual.
Delete the arithmetic rather than relocating it. Touch the scenario-detail
reconciliation panel or the `observation_reconciliation` API payload.

**A conflict the Planner has to resolve, and it is the user's call.** (j) says
the arithmetic leaves the product path. It has two product-path uses, not one.
T019's blocking reason is the first and it goes now. The second is
`observation_reconciliation`, built in `simulator_lab_api.py` and rendered as a
panel at `frontend/src/shell/ScenarioFrame.tsx`, which is T018 work already
merged to `main`. The function cannot actually leave the product path while
that caller exists, so T019 can only get the blocking use and the label. When
the panel goes is Open Question 5 and it is **not decided**. The Architect's
read is that it goes with (f) in T022, because that is when the authored
readings disappear and the panel has nothing to reconcile, and that until then
it is honest. If the user wants it gone sooner it is its own small slice, not
a widening of T019. Do not let a task file settle this by writing a scope line
either way.

**Depends on.** Nothing new. The Reviewer re-reads the narrowed diff.

**Proposals landing here.** (e) and (j). (c) and (d) are already implemented on
the branch; the decision record for them is now written and the code needs no
further change.

## T020 — Runs inventory and Draft shell

The planned task file stands. Two additions and one review instruction.

**Must deliver, in addition to the existing criteria.** The `READY` disclosure.
Both the run record and the run-detail screen state what `READY` does not
assert: every required input resolved and the selected model profile declares
it can consume them, and nothing has verified that the model can execute them
because no causal runtime exists yet. This is disclosure on a record, so it
belongs in the payload as well as on the screen — a screen-only note is a
presentation choice and this is a property of the status.

**Revised 2026-09-22: the disclosure names a condition, and T021 owns
retiring it.** The Planner's T020 said the slice landing the conformance test
would retire it and the Planner's T021 said retirement belonged to a slice
that says it is doing that, which between them left nobody holding it and
would have left false copy on screen after T021. T021 retires it, because
T021's conformance test is what makes it false, and a claim that has become
false goes in the slice that falsifies it rather than waiting for a slice that
says so. That precedent — the cold-room marker, the provisional markings —
covers removing something still honest, which is the opposite case. Recorded
in `D-2026-09-22-expiry-follows-the-condition`. T020's job is unchanged: write
the disclosure so it names the condition rather than a slice number, so the
retiring slice can recognise it.

**May not.** Rename `READY`. The word becomes correct when T021's conformance
test lands, and renaming ripples through the payload, the
frontend, the tests and the screens this slice is building. Add a second run
store, create runs, or show runtime state. Widen into the conformance test,
which needs a kernel.

**Depends on.** T019's persisted Drafts, merged and narrowed.

**Proposals landing here.** (l), first half.

**Review instruction, not an acceptance criterion.** When T020's screens are
reviewed, look at the cumulative effect rather than each control. A Runs
inventory, a run detail, a frozen-identity panel and a disabled Run button
together can read as *almost working* when no execution capability exists at
all. `.ai/ARCHITECTURE.md` gives three treatments and the test for an action
control is whether the feature map can name the causal step that makes it true.
It can — T021 and T022 — so disabled-with-reason is defensible and this is not
a vocabulary change. The risk is cumulative and local honesty does not measure
it. Make this an explicit item in the review packet.

## T020A — Foundation physical properties and model-rule carriers

New slice. After T020, before T021. Boundary-changing, so expect a longer task
spec than a normal UI slice. **Revised 2026-09-22: the user took the
checkpoint. `USER_REVIEW_REQUIRED: true`**, on the property vocabulary and its
units — it changes Foundation's schema and the Key Parameters panel, which is
the kind of change this project reviews.

**Revised 2026-09-22: a user decision is due before this slice is
implemented.** The coefficient's canonical unit follows the
`dispatched-output` promotion; see the deadline section above. Do not let the
slice choose a unit to get itself unblocked.

**Revised 2026-09-22 again: the second decision is taken and it widens this
slice.** Three carriers are listed below and none of them answers what tells
run setup the run needs the coefficient once `generator-fuel-rate` leaves the
scenario. `D-2026-09-22-foundation-value-declaration` settles it: **a scenario
parameter whose declared owner is Site Foundation has no value position at
all.** It declares the need and states no number.

Three things follow that the task file has to carry.

- **`tank-capacity` changes too.** The rule is keyed on the owner, because
  that is the only thing the document carries that distinguishes these
  parameters - the binding lives in the model profile and the scenario parser
  sees no profile. The shipped document has one other `owner: SITE_FOUNDATION`
  parameter and its 500 L goes. This is scope, not tidying: exempting it needs
  a field invented for the exemption.
- **`EXECUTION_CONTRACT_VERSION` moves here.** The shipped document as it
  stands is refused by the new parser, so this narrowing reaches a document
  that already exists. See the ledger in `.ai/FEATURE_MAP.md`.
- **`INITIAL_VALUE_ANSWERS_DISAGREE` is retired in this slice**, because
  `rating.value != declared` is its only producer and no document can state a
  `declared` any more. A refusal kind nothing can produce is the `RUNNING`
  case one layer down.
- **The `fuel-tank-volume` upper bound stops being something the document can
  state, and the `bounds` declaration stays anyway.** `declared_bounds` skips
  any parameter with no float value, so after this slice it reports
  `(0.0, None)` - which is the right answer, settled by
  `D-2026-09-22-capacity-bound-source`. The number is already frozen from
  Foundation as `fuel-tank-capacity`. **The constraint: the parser must keep
  accepting a `bounds` block on a parameter that states no value.** A bound's
  `state_key` and `bound_kind` say which world state caps which, which is a
  relationship between two states rather than a property of a machine; taking
  it out with the number would leave the kernel nothing saying what caps what,
  and it would also remove it from the scenario-detail payload, which
  publishes the relationship and never the number.

The full three-option argument is in
`Docs/simulator-scenario-authoring-and-runtime.md`, *What declares the need,
once the scenario stops declaring it*. Option C, the model profile declaring
the need, is a named follower and not this slice's.

**Must deliver.** Three carriers that move together, because any one alone
still leaves an owner that can be declared and not answered.

1. `SiteComponent` and `TemplateComponent` gain named physical properties
   beyond the single `rating` scalar, with a per-component-type vocabulary the
   strict parser enforces. Untrusted user configuration crosses the same parser
   with no lenient path.
2. `FoundationBinding` gains the ability to address a named property, not only
   `rating` by unit.
3. `SupportedState` gains a carrier for model-rule values, closing the T019
   review's L9 finding: a scenario may declare `owner: MODEL_RULE`, run setup
   correctly names `MODEL_PROFILE` as the answerer, and today there is nowhere
   for the answer to come from.

Then the shipped template declares the generator's specific fuel consumption,
`generator-fuel-rate` leaves the scenario, and run setup freezes the
coefficient from Foundation. A selected profile whose binding cannot
locate it - no binding declared, no match, more than one match, or the wrong
unit - persists a Draft that blocks on `INITIAL_VALUE_NOT_RESOLVED`. **A
Foundation that declares no such property at all is a fifth case of the same
thing and also blocks**, settled by
`D-2026-09-22-foundation-property-absent-blocks`: after T020A the binding
names the property as well as the component type, so a different profile
naming a different property may find something the Foundation does declare.
With the contradiction refusal retired, every failure of a Foundation-owned
value blocks and none refuses.

**And MG-001 is re-created from the updated template.** Templates instantiate
by copy and a template change never reaches an existing instance, so adding the
property to `config/site-templates/hybrid-mini-grid-100kw.yaml` will not give
it to `var/sites/mg-001.yaml`. A slice that adds the field without doing this
produces a site whose runs **block** on the unresolved coefficient, so the
slice's own UI-verifiable outcome never appears on screen. That is the
warning, and it is weaker than the refusal this paragraph used to assert and
sufficient. The obligation to re-create MG-001 is unchanged.
`var/sites/` also holds `mg-002` and `mg-003` as fixtures the user asked to
keep; do not clear the directory.

**UI-verifiable outcome, which it must have.** Site Configuration's Key
Parameters panel shows the generator's fuel consumption. Run setup's
frozen-inputs panel shows it resolving from *site foundation* rather than from
*scenario*. That one line of a table the user already reads is the seam repair
made visible.

**May not.** Grow Foundation into a wish list. Efficiency curves, minimum load,
ramp rate, tank geometry, sensor placement, battery chemistry, PV tilt,
orientation and derate are all absent and none of them blocks T021, because the
first kernel models none of the things they affect. The fuel tank's minimum
usable level is the honest home for the floor the validation layer currently
invents, and it is a follower, not part of the minimum set. Do not add a
Foundation edit path; Foundation stays read-only for every Site for all of M1.
Do not move the validation-layer volume floor in this slice unless the slice
says it is doing that and carries the test for it.

**Depends on.** T020 for sequencing only. It is independent of the kernel and
nothing in front of it is blocked.

**Proposals landing here.** (k).

**Open question this slice must not settle by accident.** Whether the product's
own expectation later uses the same Foundation coefficient the kernel used, or
a separately declared operating assumption that may differ from it. That is a
T034–T038 question and the worked example shows why it earns its keep. T020A
supplies the Foundation coefficient; it does not decide who else reads it.

## T021 — Minimal Fuel Loss causal kernel

The planned task file stands. Three additions, and the third changes what the
slice is.

**Must deliver, in addition to the existing criteria.**

1. **The `TRAJECTORY` oracle kind.** One vocabulary member in
   `EXPECTATION_KINDS`, its parsed fields, and the kernel test that checks
   them. It asserts a private-state value at an offset, is checked by the
   kernel in tests, and is never published and never read by any executable
   path. Two guards are part of the deliverable, not commentary: it must be
   sparse and purposeful, because a dense set is a trace in the oracle position
   and fits the kernel to the author's arithmetic; and the slice must state
   that it is a regression guard rather than a correctness proof, because two
   implementations of the same arithmetic agreeing proves they agree.

2. **The `supported_states` conformance test.** The shipped model profile's
   supported set equals the set of states the kernel actually implements,
   **derived from the kernel, not hand-maintained**. A test that restates the
   tuple closes nothing. When it lands, `READY` means what its name says.
   **Revised 2026-09-22: this slice also retires T020's disclosure**, because
   this is the slice that makes it false. It is not a later slice's to pick
   up and it is not optional; see
   `D-2026-09-22-expiry-follows-the-condition`.

3. **Run the kernel against the shipped Fuel Loss document and report the
   resulting trajectory.** This is the loop. The document's authored numbers
   are corrected from what the kernel computes, not from what an author
   expects, because the right removal magnitude depends on what the kernel
   computes and on what the product can later recover from published evidence.
   Expect the kernel to disagree with the shipped document, and expect the
   document to be what is wrong: the declared causes reach 254 L at offset
   1590 where the document authors 155 L, and the 300 L delivery at 2400
   overfills a 254 L tank against a 500 L capacity. The correction itself is
   the user's call during the slice; the slice's obligation is to produce the
   trajectory that makes the call answerable.

**May not.** Accept any hand-authored trace as execution input. Persist or
check in a golden artifact — T022 owns that once it wires normal execution
through this kernel. Read physics from the scenario: the consumption
coefficient comes from Foundation via T020A. Decide the four unpinned contract
semantics inside the implementation; if they are still open they return to
review. Display a state trajectory in the Lab, which is T022. Model power flow,
battery, weather synthesis or dispatch logic — carrying a forcing is not a
claim that its consequences are modelled.

Also may not: **remove the reference implementation.** T021 compares it
against the kernel and reports any disagreement, and the kernel is the
surviving authority. Removing it from the repository follows its last
remaining product-path caller, which is the `observation_reconciliation`
panel, and when that goes is undecided. Comparing is this slice's; removing is
not.

**Depends on.** T020A's Foundation coefficient and model-rule carrier. The
second half of the `REQUIRED` forcing-state decision and the four unpinned
semantics, both before the task file is written. T020's run-detail shell for
the small visible readiness result.

**The tank's capacity comes from the frozen identity, not from
`declared_bounds`, and the task file has to say so.** After T020A that
function reports no upper value for `fuel-tank-volume`
(`D-2026-09-22-capacity-bound-source`); the document declares *which* state
caps which and the frozen run carries *how big* the tank is, resolved from
Foundation. An implementer who reaches for `declared_bounds`, finds
`(0.0, None)` and fills the gap will either invent 500 or conclude the bound
was dropped, and both are wrong. `BOUND_CASES["fuel-tank-capacity"]` is
unchanged and is applied against the frozen value - which is what gives this
slice's document correction something to check the 300 L delivery against.

**What T021 refuses, which the task file has to state rather than discover.**
T019 has already frozen and validated everything T021 initializes from, so
T021's "missing or ambiguous inputs" refusals are defence in depth against a
bad caller, not a second validation layer with work to do. They are
unreachable through the normal path and must be tested directly, because
*unreachable* and *not yet reached* look identical in a test suite and only
one of them is a guarantee. This is the open remainder of Open Question 6;
the discriminator half of that question was settled by the 2026-09-22
extension to `D-2026-09-21-run-setup-outcome-vocabulary`.

**The `TRAJECTORY` oracle does not move `EXECUTION_CONTRACT_VERSION`**, under
`D-2026-09-22-contract-version-scope`: it widens the document space off every
executable path, so no document that was already valid changes outcome and no
frozen artifact is affected. (g) moved the number because it narrows, which is
a different direction. Pinning the four unpinned semantics *is* a narrowing
and does move it, so whichever slice declares them spends a version.

**Proposals landing here.** (i), the second half of (l) including the
disclosure's retirement, and (j)'s comparison against the kernel — not (j)'s
removal.

## T021A — Reported observations carry no execution requirement

**New since 2026-09-22.** The user accepted the Planner's split of (g) out of
T022 into its own slice, placed between T021 and T022. The task file exists at
`tasks/T021A-reported-observation-requirement-closure.md`.

**Why it is its own slice, so a later reader does not fold it back in.** The
version-bump window is free only while no golden trace exists, and T022 is the
slice that first produces one. Folding (g) into T022 makes that slice's
internal ordering load-bearing — the parser change would have to land before
trace generation inside one slice — and closes the window entirely if T022 is
ever split. It sits after T021 rather than before because the kernel never
reads `execution_requirement` on a reported observation, so nothing about the
kernel depends on it either way.

**Must deliver.** The parser gives `execution_requirement` no position on a
`REPORTED_OBSERVATION`, closed at the structure rather than as a rule applied
after parsing. The shipped document's reported-observation entries lose the
field. `EXECUTION_CONTRACT_VERSION` moves by one, and the new version reaches
the frozen identity of runs set up after it while a Draft already frozen under
the previous version keeps what it was frozen under. **Write the move, not the
literals.** The task file currently says "2 to 3" and T022's guidance says
"already under version 3", and neither is safe: declaring the four unpinned
kernel semantics is itself a narrowing that spends a number and is due before
T021's task file, and the constant's own docstring carries an
unreleased-version doctrine under which a narrowing that never leaves its
branch spends nothing. See `D-2026-09-22-contract-version-scope` for when the
number moves and `.ai/FEATURE_MAP.md`, *The execution-contract version
ledger*, for what it is after each slice - three narrowings are now in flight
and, as sequenced, none of them collapses into another.

**May not.** Remove the authored reading *values* — that is (f) and it is
T022's. Touch the reconciliation panel or its payload. Change anything else in
the execution contract, the kernel, or the observation transform.

**Depends on.** T019's narrowing, merged. Once the observation blocking
reasons are gone, removing the field changes no run-setup outcome, which is
what makes this slice small.

**Proposals landing here.** (g), alone.

## T022 — Lab execution and device observation

The planned task file stands and already contains most of what (f) needs; its
criteria say the transform "emits ordered run-local observations distinct from
private truth" and that authored reported-observation inputs "affect only their
defined observation/event presentation." (f) is what makes the shipped document
consistent with criteria the user has already accepted.

**Must deliver, in addition to the existing criteria.**

1. **(f), in the document and in the code.** The authored 155 L at 1590 and
   150 L at 1800 are removed. The entry at 1590 survives as an evidence
   condition asserting that a reading arrives there and is materially below
   what dispatch accounts for, backed by a `DETECTION` expectation. The
   operator's inspection at 1800 keeps the act and loses the number: it becomes
   a run-local manual operational observation whose value is generated from
   truth at that offset through the `operator-hand-record` source, optionally
   perturbed by a declared reading error if the user chose to model one.
2. **A recommendation, not a requirement: the reconciliation panel leaves the
   scenario detail screen here.** (f) is when the authored readings disappear
   and the panel has nothing left to reconcile, and it is also what unblocks
   removing the reference implementation, whose last product-path caller the
   panel is. But **the user has not decided this** — it is Open Question 5.
   Until they do, the panel is honest, because it describes a real property of
   a document that does still contain two authored readings. If the user says
   yes, it is a visible product change on merged work and this slice must say
   it is making it. If they say no or say nothing, T022 leaves it alone and
   the reference implementation stays.

*(g) is no longer here.* Revised 2026-09-22: it is T021A.

**May not.** Let any authored reading reach a transition or an initialization —
that is what the `REPORTED_OBSERVATION` role is for and it survives (f)
unchanged. Infer a cadence from anything but the frozen publication profile.
Stage a Source Envelope, which is T023. Introduce an injection control.
Introduce sensor bias into the Fuel Loss Event: the mockups already carry a
separate `Sensor Bias` scenario, and keeping Fuel Loss free of bias keeps its
one lesson clean — a real loss, hidden by a reporting gap.

**Depends on.** T021's kernel, and T021's reported trajectory, because the
document's corrected numbers come out of that loop. T021A, so the document
being edited here is already under contract version 3 and the field is already
gone. The reporting-path authority question, if it moved the reporting-path
forcing to the publication profile, changes which profile the transform asks.

**Proposals landing here.** (f), alone.

**User review is already required on this slice** for control behaviour,
private-truth visibility, truth-versus-reported labels and unavailable-value
treatment. (f) adds one thing to review that is not a control: the scenario
detail screen now says, in words, that the document declares causes and does
not declare what the tank holds or what a device reads. That sentence is the
product-facing statement of the whole sequence and it is worth reviewing as
copy, not only as layout.

## What this handoff deliberately does not decide

- Task file contents, acceptance criteria wording, scope-limit lists, test
  structure, and user-review placement. All the Planner's.
- **Closed 2026-09-22:** T020A carries its own user-review checkpoint, and (g)
  is its own slice, T021A. Both were left open here and both are now the
  user's answer, not a recommendation.
- Every open question listed under `Open Questions Before Task Breakdown` in
  `.ai/FEATURE_MAP.md`. None of them is closed by this handoff, and a task file
  that closes one by implementation rather than by decision is the failure this
  whole sequence exists to stop.
