# T020B - Execution Contract Alignment And The First Ready Shipped Run

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T020B-execution-contract-alignment`

## Feature

Draft SimulationRun And Causal Runtime.

## UI-Verifiable Screen Behavior

The shipped Fuel Loss Event reaches `READY` for the first time through the
product path. A Draft set up against MG-001 and the shipped profiles opens in
the Runs inventory and the run detail as a `READY` run rather than a blocked
one, with its Run action disabled and naming the causal runtime that does not
exist yet, and with its frozen-inputs table naming the publication profile as
the answerer for the reporting path.

It still says what the selected model profile does not model. Demand and
irradiance leave the blocking reasons and appear on the run detail as recorded
unsupported optional inputs, so lowering them changes which list they are in
rather than whether the run discloses them at all.

The scenario detail screen's execution-contract section states four things it
could not state before: how a quantity declared over a window moves across it,
where within a step a reading is taken, what a forcing is outside its declared
window, and what a run does after a bounded change. The contract version it
reports has moved.

## Why This Is Next

The version ledger already reserved a step of its own between T020A and T021.
Four decisions accepted on 2026-09-22 gave it contents, and none of that work
belongs to either neighbour: it is contract and profile, not Foundation
carriers and not kernel. Bundling a contract declaration into T020A would make
that slice's internal ordering load-bearing, which is the argument that gave
T021A a slice of its own.

**It is what stands between the sequence and its own first executable run.**
T021 owes *run the kernel against the shipped Fuel Loss document and report the
trajectory*. `BLOCKED` means everything was frozen and the run must not
execute, so executing a blocked Draft would contradict the status this sequence
spent three decisions making honest. Three states the first kernel has no
business modelling were what held the shipped scenario there.

**The lowering and the conflict refusal travel together and cannot be split.**
`site-load-demand` is declared in three positions and
`plane-of-array-irradiance` in two. While `_executable_inputs` resolves a
disagreement by taking `REQUIRED`, lowering one position of three changes
nothing observable, so a slice that lowered without retiring the collapse would
ship an edit with no effect and a slice that retired the collapse without
lowering would refuse the shipped document.

## Dependencies

- T020A supplies the Foundation coefficient, the `dispatched-output` promotion
  and `generator-output-power` in the shipped model profile's supported states.
  Without them the shipped Draft still blocks and this slice's outcome never
  appears on a screen.
- T020 supplies the Runs inventory and run-detail shell this outcome is read
  on. It also corrects the three frozen rows that say the model profile
  answered when the publication profile did, so this slice carries the
  authority move rather than the relabel.
- `D-2026-09-22-kernel-step-semantics`, `D-2026-09-22-forcing-state-
  requirements`, `D-2026-09-22-consumption-coefficient-unit` and
  `D-2026-09-22-expiry-follows-the-condition`, all accepted on 2026-09-22.
  Nothing here is an open question; the slice implements answers.

## Acceptance Criteria

- The four semantics the execution contract left unpinned are declared
  alongside the dispatch rules it already publishes, each as a statement a
  conforming kernel obeys:
  - a quantity declared over a window ramps linearly across the steps it
    spans, rather than landing at the completion boundary;
  - the observation transform samples after the step's due events are applied,
    so a boundary sample can never see pre-event state;
  - a forcing outside its declared window is unavailable - not zero, which is
    a fabricated value, and not held, which is an invented persistence rule;
  - a bounded change lets the run continue and later causes apply to the
    bounded value, because recording a refused quantity only means something
    if the run goes on.
- Each of the four reaches the scenario-detail contract section the existing
  dispatch rules reach. A semantic declared only in a comment is one an
  implementer can miss, and the point of declaring it is that two conforming
  kernels cannot split on it.
- `EXECUTION_CONTRACT_VERSION` moves by one from whatever this slice finds.
  Two narrowings land here - the four semantics and the requirement-conflict
  refusal - and they spend one number between them, because nothing ever
  conforms to a version between two narrowings in the same unmerged window.
  The literal is not written here: the count for the sequence is stated once,
  in `.ai/FEATURE_MAP.md` under *The execution-contract version ledger*.
- The moved version reaches the frozen identity of runs set up after it. A
  Draft already frozen under the previous version keeps what it was frozen
  under; nothing rewrites a persisted identity.
- A `(state_key, role)` pair must agree about its execution requirement across
  every position that declares it. A document where two positions disagree is
  refused as `ScenarioConfigurationInvalid`, with a reason naming the state,
  the role and the disagreement, at the layer that sees every position rather
  than at the consumer that happens to read them last.
- `_executable_inputs`' `REQUIRED`-wins resolution is retired. It still
  collapses agreeing positions, because a state declared in one role by four
  rows is one question asked once, and it resolves nothing, because after the
  refusal above there is nothing left to resolve.
- `site-load-demand` drops to `OPTIONAL` at all three of its positions and
  `plane-of-array-irradiance` at both of its. Each is lowered everywhere or
  nowhere, and a partial lowering is now a refused document rather than a
  silently stricter one - which is the criterion above doing its work on this
  slice's own edit.
- Authority over `fuel-level-reporting-availability` moves to the publication
  profile, which gains a concept of the reporting states it supports. The
  model profile stops claiming the state, and its statement stops naming the
  availability of the reporting path among the things it does not model,
  because that is no longer its question to answer.
- `FROZEN_INPUT_ANSWERERS` carries `PUBLICATION_PROFILE` after this slice and
  the reporting-path rows name it. T020 introduces the member for the three
  rows it corrects, so what is new here is the authority and not the
  vocabulary; the vocabulary docstring that says "the four" is correct either
  way only once one slice has fixed it.
- The shipped Fuel Loss Draft set up through the product path is `READY`, with
  no blocking reasons, and its record carries the two lowered states as
  unsupported optional inputs.
- Run detail shows the unsupported optional inputs the record carries, as a
  disclosure distinct from blocking reasons. This is the first `READY` run
  that has any, and a `READY` run that dropped them would make the lowering
  hide what blocking used to say out loud.
- This slice retires T020's fixture-only `READY` criterion, because it
  falsifies its premise: that no `READY` run is reachable through the product
  path in this build. The replacement is a `READY` proof on the shipped
  scenario through the path a person uses. A claim that has become false goes
  in the slice that falsifies it
  (`D-2026-09-22-expiry-follows-the-condition`), and this is the third
  artifact in this sequence to acquire an expiry that way, after T020's `READY`
  disclosure and the labelled reference implementation - the rule applying,
  not a coincidence.
- T020's `READY` **disclosure** is not retired here and stays true. It names
  its own condition - that nothing verifies the profile's supported set
  against a kernel - and that condition is met by T021's conformance test. The
  same rule sends the two claims to different slices because they name
  different conditions, and retiring the disclosure here would put a false
  absence on the screen in place of a true sentence.

## Required Product And Domain Semantics

- An unpinned semantic is a place where two conforming implementations can
  both be correct and disagree, which is the one thing a versioned contract
  may not contain. Declaring is not implementing: nothing in this slice
  executes anything.
- `REQUIRED` means an executor must model this state to run this scenario.
  Demand and irradiance were marked `REQUIRED` by an author being careful. The
  scenario declares its dispatch directly, so nothing computes it from load and
  PV, and a kernel that modelled them would be computing dispatch.
- Two positions disagreeing about whether one state is required is two answers
  to one question. Resolving that silently by taking the stricter value is how
  an author's mistake becomes a behaviour.
- That refusal carries no kind vocabulary, deliberately, and nobody should add
  one. `.ai/ARCHITECTURE.md`'s naming rule is scoped to a layer where a request
  can be refused *or* persisted as `BLOCKED`, and a parse failure has no
  blocking twin: a document parses or it does not, and one that does not never
  reaches run setup. `ScenarioConfigurationInvalid` carries no kinds today, so
  naming one would create a vocabulary of a single member.
- `OPTIONAL` and unsupported is *recorded*, not ignored. There is no third
  answer, because "supported if convenient" is how an input gets dropped.
- The model profile models physics; the publication profile owns cadence and
  reporting identity. Reporting availability is a state of the reporting path
  and not of the world, which is why it was the one of the three that was
  never a physics question.

## Protected Seams

- Contract-version identity: the number moves with the space of conforming
  behaviours and reaches frozen provenance, so playback still refuses a
  mismatch.
- Authoring-contract closure: a disagreement is refused where every position is
  visible, rather than reconciled by whichever consumer reads it.
- Profile authority separation: physics to the model profile, the reporting
  path to the publication profile, and neither answering for the other.
- Presentation honesty: a `READY` run discloses what its selected profile does
  not model, and a frozen row names the profile that answered it.
- Simulator/product boundary: no kernel, no execution, no runtime value, and no
  product evidence.

## Focused Tests And Review Evidence

- One test per declared semantic, each pinning the declaration against the
  reading it rules out, so the pin is checkable before a kernel exists.
- Refusal test for a `(state_key, role)` pair declared `REQUIRED` in one
  position and `OPTIONAL` in another, whose deliberate violation is one the
  rest of the system would otherwise have accepted by resolving it.
- A test proving a document that agrees across positions still collapses to one
  question per pair, so retiring the resolution did not retire the collapse.
- A `READY` test on the shipped scenario through the product path, replacing
  T020's fixture-record proof, and asserting no blocking reasons rather than a
  count of them.
- A test proving the two lowered states appear as unsupported optional inputs
  on the record and on the run detail, and that no blocking reason names them.
- A test that the reporting-path row's answerer is the publication profile and
  that no frozen row's answerer disagrees with the detail beside it.
- A contract-version test against the declared rule set rather than a literal,
  and a frozen-identity test: a new Draft freezes the moved version while an
  existing persisted Draft is unchanged.
- Scenario-detail UI test for the four new contract statements and the reported
  version.
- Run architecture/workflow checks, relevant backend and frontend suites,
  typecheck, and build.
- **Review evidence, not an acceptance criterion.** T020's review asked whether
  a Runs inventory, a run detail, a frozen-identity panel and a disabled Run
  action together read as *almost working*. A `READY` shipped run is the
  strongest form of that risk so far, and this slice adds no execution
  capability at all. The packet says what the screen now implies and whether
  the disabled action's stated reason still carries it.

## Scope Limits

- No kernel, no step loop, no execution. Declaring a semantic and obeying one
  are different slices and obeying is T021's.
- No widening of the shipped model profile beyond `generator-output-power`,
  which T020A adds.
- No correction of the shipped document's authored numbers. That needs a
  computed trajectory and it is T021's loop.
- No relabel of the three frozen rows T020 corrects, and no second change to
  the answerer vocabulary.
- No removal of the reference implementation, the `observation_reconciliation`
  panel or its payload; all three go with T022.
- No retirement of T020's `READY` disclosure; its condition is not met here.
- No new blocking-reason kind. Everything this slice changes either removes a
  reason or moves which profile answers a row.

## User Review

No new checkpoint. Every semantic in this slice was accepted by the user on
2026-09-22 in the four decisions named under Dependencies, and the slice
implements them rather than proposing anything. The one thing that returns to
the user is evidence rather than a decision: the cumulative reading of a
`READY` shipped run that still has no way to run.
