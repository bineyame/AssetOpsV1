# Planner Handoff — T019 Narrowing Through T022

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

## Two things that gate task files, not slices

**The `REQUIRED` forcing-state decision is due before T021's task file is
written.** It decides what the first kernel must model, so a T021 task file
written before it would scope the kernel by accident. It is one decision with
three parts: what happens to `site-load-demand`,
`plane-of-array-irradiance` and `fuel-level-reporting-availability`; whether
reporting-path authority moves from the model profile to the publication
profile; and whether `dispatched-output` is promoted to a `FORCING_INPUT` on
`generator-output-power`. The user owns it. Do not write T021's task file
first and patch it after.

**The four unpinned kernel semantics are due at the same time.** Window
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

**May not.** Rename `READY`. The word becomes correct when T021's conformance
test lands two slices away, and renaming ripples through the payload, the
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
spec than a normal UI slice and a user-review checkpoint on the property
vocabulary.

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
coefficient from Foundation and blocks when it is absent.

**And MG-001 is re-created from the updated template.** Templates instantiate
by copy and a template change never reaches an existing instance, so adding the
property to `config/site-templates/hybrid-mini-grid-100kw.yaml` will not give
it to `var/sites/mg-001.yaml`. A slice that adds the field without doing this
produces a site that still blocks. `var/sites/` also holds `mg-002` and
`mg-003` as fixtures the user asked to keep; do not clear the directory.

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
   tuple closes nothing. When it lands, `READY` means what its name says and
   T020's disclosure can be retired by a later slice that says it is doing
   that.

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

**Depends on.** T020A's Foundation coefficient and model-rule carrier. The
`REQUIRED` forcing-state decision and the four unpinned semantics, both before
the task file is written. T020's run-detail shell for the small visible
readiness result.

**Proposals landing here.** (i), the second half of (l), and the expiry of (j)
— when the kernel lands, the reference implementation and the kernel are
compared and the kernel is what survives.

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
2. **(g), closed at the parser.** `execution_requirement` is forbidden on a
   `REPORTED_OBSERVATION` — no position the field can occupy, the way duration
   units were closed at the unit vocabulary. `EXECUTION_CONTRACT_VERSION` moves
   2 to 3. This may be a small slice before T022 instead; it is free now and
   will not be once a golden trace exists.
3. **The reconciliation panel leaves the scenario detail screen.** (f) is when
   the authored readings disappear and the panel has nothing to reconcile.
   Until then it is honest, because it describes a real property of a document
   that does contain two authored readings. This is a visible product change on
   merged work and the slice must say it is making it.

**May not.** Let any authored reading reach a transition or an initialization —
that is what the `REPORTED_OBSERVATION` role is for and it survives (f)
unchanged. Infer a cadence from anything but the frozen publication profile.
Stage a Source Envelope, which is T023. Introduce an injection control.
Introduce sensor bias into the Fuel Loss Event: the mockups already carry a
separate `Sensor Bias` scenario, and keeping Fuel Loss free of bias keeps its
one lesson clean — a real loss, hidden by a reporting gap.

**Depends on.** T021's kernel, and T021's reported trajectory, because the
document's corrected numbers come out of that loop. The reporting-path
authority question, if it moved the reporting-path forcing to the publication
profile, changes which profile the transform asks.

**Proposals landing here.** (f) and (g).

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
- Whether T020A needs its own user-review checkpoint. It changes Foundation's
  schema and the Key Parameters panel, which argues yes; the Planner should
  propose one and the user can decline it.
- Whether (g) rides inside T022 or lands as a small slice before it.
- Every open question listed under `Open Questions Before Task Breakdown` in
  `.ai/FEATURE_MAP.md`. None of them is closed by this handoff, and a task file
  that closes one by implementation rather than by decision is the failure this
  whole sequence exists to stop.
