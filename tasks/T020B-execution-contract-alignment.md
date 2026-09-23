# T020B - Execution Contract Alignment And The First Ready Shipped Run

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T020B-execution-contract-alignment`

## Feature

Draft SimulationRun And Causal Runtime. Block A of `.ai/FEATURE_MAP.md`.

## UI-Verifiable Screen Behavior

The shipped Fuel Loss Event reaches `READY` for the first time through the
product path. A Draft set up against MG-001 and the shipped profiles opens in
the Runs inventory and the run detail as a `READY` run rather than a blocked
one, with its Run action disabled and naming the causal runtime that does not
exist yet, and with its frozen-inputs table naming the publication profile as
the answerer for the reporting path. It still says what the model profile does
not model: demand and irradiance leave the blocking reasons and appear as
recorded unsupported optional inputs, so lowering them changes which list they
are in rather than whether the run discloses them at all.

The scenario detail screen's execution-contract section states what it could
not state before: the order of work at a step boundary, what a timestamped
reading means, how a quantity declared over a window moves across it, what a
forcing is outside its declared window, and what a run does after a bounded
change. The contract version it reports has moved.

## Why This Is Next

The version ledger already reserved a step between T020A and T021, and four
decisions accepted on 2026-09-22 gave it contents. None of that work belongs to
either neighbour: it is contract and profile, not Foundation carriers and not
kernel.

**It is what stands between the sequence and its own first executable run.**
T021 owes *run the kernel against the shipped Fuel Loss document and report the
trajectory*, and `BLOCKED` means everything was frozen and the run must not
execute. Three states the first kernel has no business modelling were what held
the shipped scenario there.

**The lowering and the conflict refusal travel together and cannot be split.**
While `_executable_inputs` resolves a disagreement by taking `REQUIRED`,
lowering one position of three changes nothing observable; a slice that lowered
without retiring the collapse would ship an edit with no effect, and one that
retired the collapse without lowering would refuse the shipped document.

## Dependencies

- T020A supplies the Foundation coefficient, the `dispatched-output` promotion
  and `generator-output-power` in the shipped model profile's supported states.
  Without them the shipped Draft still blocks and this slice's outcome never
  appears on a screen.
- T020 supplies the Runs inventory and run-detail shell this outcome is read
  on. It also corrects the three frozen rows that say the model profile
  answered when the publication profile did, so this slice carries the
  authority move rather than the relabel.
- `D-2026-09-22-kernel-step-semantics`, `-forcing-state-requirements`,
  `-consumption-coefficient-unit` and `-expiry-follows-the-condition`, all
  accepted on 2026-09-22. Nothing here is an open question; the slice
  implements answers.

## Acceptance Criteria

### The boundary cycle, declared

- **The contract declares v4 §6.1's boundary cycle in full, not a shorthand.**
  *Observe after the step* is ambiguous and has already been read two wrong
  ways - as permitting a pre-event sample, and as permitting a forward-looking
  interval value. What this slice declares, at instant `T`:

  ```text
  A. apply events and configuration changes due exactly at T
  B. the post-event state at T now exists
  C. if a sample or publication is due at T:
       sample stocks and discrete state at T,
       attach interval measurements for [T-dt, T),
       apply the reporting transform,
       hand the result to staging
  D. build the controller view at T
  E. emit control intent for [T, T+dt)
  F. resolve accepted flows
  G. integrate the world over [T, T+dt)
  H. check conservation, bounds and invariants
  I. carry the resulting state to T+dt
  ```

  Steps D through G have no implementation in this range and are declared
  anyway, because a cycle with holes in it is a cycle an implementer will
  reorder.
- **A stock reading and an interval reading at the same timestamp mean
  different things.** A stock or discrete reading at `T` is post-event; a rate
  or energy reading at `T` summarises the interval that just ended. This is
  asymmetric only if the two are assumed to mean the same thing, real
  instrumentation has exactly this distinction, and the contract text must say
  it or a later reader reconciles it wrongly.
- **At the first boundary there is no preceding interval**, so interval signals
  are unavailable there unless a profile explicitly declares an initial
  historical window. This is a contract statement rather than a kernel
  behaviour, which is why it lands here and not in T021.
- **No second clock, and no reinterpretation of already-frozen runs.** The
  cycle is the only time model the contract has, and a run frozen under an
  earlier contract version keeps what it was frozen under.

### The other three semantics

- A quantity declared over a window ramps linearly across the steps it spans,
  rather than landing at the completion boundary.
- A forcing outside its declared window is **unavailable** - not zero, which is
  a fabricated value, and not held, which is an invented persistence rule.
- A bounded change lets the run continue and later causes apply to the bounded
  value, because recording a refused quantity only means something if the run
  goes on. `D-2026-09-22-kernel-step-semantics`.
- Each declared semantic reaches the scenario-detail contract section the
  existing dispatch rules reach. A semantic declared only in a comment is one
  an implementer can miss, and the point of declaring it is that two conforming
  kernels cannot split on it.

### Requirement conflict, lowering and authority

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
  silently stricter one - the criterion above doing its work on this slice's
  own edit.
- Authority over `fuel-level-reporting-availability` moves to the publication
  profile, which gains a concept of the reporting states it supports. The model
  profile stops claiming the state, and its statement stops naming the
  availability of the reporting path among the things it does not model,
  because that is no longer its question to answer.
- `FROZEN_INPUT_ANSWERERS` carries `PUBLICATION_PROFILE` after this slice and
  the reporting-path rows name it. T020 introduces the member for the three
  rows it corrects, so what is new here is the authority and not the
  vocabulary.

### Version and outcome

- `EXECUTION_CONTRACT_VERSION` moves by one from whatever this slice finds. Two
  narrowings land here - the semantics and the requirement-conflict refusal -
  and they spend one number between them, because nothing ever conforms to a
  version between two narrowings in the same unmerged window. The count for the
  sequence is stated once, in `.ai/FEATURE_MAP.md` under *The
  execution-contract version ledger*; no task file writes the literal.
- The moved version reaches the frozen identity of runs set up after it, and
  nothing rewrites a persisted identity.
- The shipped Fuel Loss Draft set up through the product path is `READY`, with
  no blocking reasons, and its record carries the two lowered states as
  unsupported optional inputs.
- Run detail shows those unsupported optional inputs as a disclosure distinct
  from blocking reasons. This is the first `READY` run that has any, and a
  `READY` run that dropped them would make the lowering hide what blocking used
  to say out loud.
- **This slice retires T020's fixture-only `READY` criterion, and that is not
  optional.** T020 proves every `READY` claim against a fixture record because
  no `READY` run existed through the product path; this slice makes the premise
  false, so the replacement is a `READY` proof on the shipped scenario through
  the path a person uses (`D-2026-09-22-expiry-follows-the-condition`).
- T020's `READY` **disclosure** is not retired here and stays true. It names
  its own condition - that nothing verifies the profile's supported set against
  a kernel - and that condition is met by T021's conformance test. Retiring it
  here would put a false absence on the screen in place of a true sentence.

## Required Product And Domain Semantics

- An unpinned semantic is a place where two conforming implementations can both
  be correct and disagree, which is the one thing a versioned contract may not
  contain. Declaring is not implementing: nothing in this slice executes.
- `REQUIRED` means an executor must model this state to run this scenario.
  Demand and irradiance were marked `REQUIRED` by an author being careful. The
  scenario declares its dispatch directly, so nothing computes it from load and
  PV, and a kernel that modelled them would be computing dispatch.
- Two positions disagreeing about whether one state is required is two answers
  to one question. Resolving that silently by taking the stricter value is how
  an author's mistake becomes a behaviour.
- That refusal carries no kind vocabulary, deliberately. The naming rule in
  `.ai/ARCHITECTURE.md` is scoped to a layer where a request can be refused
  *or* persisted as `BLOCKED`, and a parse failure has no blocking twin, so
  naming a kind would create a vocabulary of a single member.
- `OPTIONAL` and unsupported is *recorded*, not ignored. There is no third
  answer, because "supported if convenient" is how an input gets dropped.
- The model profile models physics; the publication profile owns cadence and
  reporting identity. Reporting availability is a state of the reporting path
  and not of the world, which is why it was never a physics question.

## Read When You Reach It

- `Docs/simulator_design_v4.md` §6.1-6.3, for the cycle in its original form,
  the worked 13:00 example, and the separation between what a controller may
  see and what a gateway publishes. §6.1 is the source of the block above and a
  disagreement between the two is a defect here.
- v4 §8.2, for the three bound policies, already implemented.

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
- Standing for this range, one line rather than repeated per criterion: no
  product conclusion in a scenario fixture; no private oracle value turned into
  evidence; no manufactured default hiding a missing answer; no simulator
  import of the backend.

## Focused Tests And Review Evidence

- One test per declared semantic, each pinning the declaration against the
  reading it rules out, so the pin is checkable before a kernel exists. For the
  boundary cycle that includes a stock sample at `T` reflecting an event due at
  `T`, an interval signal at the first boundary reported unavailable rather
  than zero, and the declared step order asserted so that a later edit
  reordering it fails rather than silently redefining the contract.
- Refusal test for a `(state_key, role)` pair declared `REQUIRED` in one
  position and `OPTIONAL` in another, whose deliberate violation is one the
  rest of the system would otherwise have accepted by resolving it.
- A test proving a document that agrees across positions still collapses to one
  question per pair, so retiring the resolution did not retire the collapse.
- A `READY` test on the shipped scenario through the product path, replacing
  T020's fixture-record proof, asserting no blocking reasons rather than a
  count of them, and asserting the two lowered states appear as unsupported
  optional inputs on the record and on the run detail.
- A test that the reporting-path row's answerer is the publication profile and
  that no frozen row's answerer disagrees with the detail beside it.
- A contract-version test against the declared rule set rather than a literal,
  and a frozen-identity test: a new Draft freezes the moved version while an
  existing persisted Draft is unchanged. Scenario-detail UI test for the new
  contract statements and the reported version.
- `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1`, the backend
  and frontend suites this slice touches, typecheck, and build.
- **Review evidence, not an acceptance criterion.** T020's review asked whether
  a Runs inventory, a run detail, a frozen-identity panel and a disabled Run
  action together read as *almost working*. A `READY` shipped run is the
  strongest form of that risk so far. The packet says what the screen now
  implies and whether the disabled action's stated reason still carries it.

## Scope Limits

- No kernel, no step loop, no execution. Declaring a semantic and obeying one
  are different slices and obeying is T021's. Steps D through G of the cycle
  are declared and not built.
- No widening of the shipped model profile beyond `generator-output-power`,
  which T020A adds. No correction of the shipped document's authored numbers;
  that needs a computed trajectory and is T021's loop.
- No relabel of the three frozen rows T020 corrects, and no second change to
  the answerer vocabulary. No retirement of T020's `READY` disclosure; its
  condition is not met here.
- No removal of the reference implementation, the `observation_reconciliation`
  panel or its payload; all three go with T022.
- No new blocking-reason kind. Everything this slice changes either removes a
  reason or moves which profile answers a row.

## User Review

No new checkpoint. Every semantic here was accepted by the user on 2026-09-22
in the decisions named under Dependencies, and the slice implements them rather
than proposing anything. The one thing that returns to the user is evidence
rather than a decision: the cumulative reading of a `READY` shipped run that
still has no way to run.
