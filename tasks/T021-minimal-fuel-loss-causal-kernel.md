# T021 - Minimal Fuel Loss Causal Kernel

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T021-minimal-fuel-loss-causal-kernel`

## Feature

Draft SimulationRun And Causal Runtime. Block B of `.ai/FEATURE_MAP.md`.

## UI-Verifiable Screen Behavior

A `READY` Fuel Loss Draft can be checked against a real executable model. Its
run detail reports that the selected model profile is executable and names the
private-state capabilities it supports, and that report is now backed by a
conformance test derived from the kernel rather than by a hand-written tuple.
The `READY` disclosure T020 put on the record and the screen goes with it,
because the test is what makes it false. The run still does not start or
display a state trajectory; T022 owns execution and runtime presentation.

## Why This Is Next

T020 makes persisted Drafts inspectable and T020A gives the kernel physics that
come from the machine rather than from the story. The next causal prerequisite
is the smallest real state producer that can execute the accepted Fuel Loss
contract. Building it before controls or golden traces prevents authored
fixtures from becoming simulator authority.

This backend-heavy slice directly unlocks T022's UI-verifiable execution. Its
small visible readiness result proves the real run-to-kernel compatibility seam
rather than adding a standalone simulator diagnostics product. It is also the
first slice that can answer a question the shipped Fuel Loss document has been
carrying: what its declared causes actually do to the tank.

### Where the kernel lands, decided here

v4 §3.2 states the dependency rule in its strongest form: `simulator/` imports
no `assetops_backend` package at all, `host/` is a composition leaf that may
import both, and nothing imports `host/`. The repository guard already enforces
the first. What it cannot help with is that `host/` does not exist and that the
run, scenario and execution-contract types the kernel initialises from are
backend-owned today.

**The kernel lands in `simulator/assetops_simulator/kernel/` in this slice.**
The alternative - build it backend-side and relocate it at T022 - puts a
structural relocation inside the slice that already carries a user-review
checkpoint on control behaviour and truth visibility. The neutral-contract move
is at its cheapest here, while the kernel has exactly one caller and no UI.

`host/` is **not** created here. Nothing composes execution into the
application until T022 wires the Lab to it, and a composition leaf with nothing
to compose is a directory that teaches a structure rather than serving one.

## Dependencies

- T018's accepted execution roles, initialization, timing and bound behaviour,
  as amended on 2026-09-21.
- T019 freezes all required inputs and persists `READY`/`BLOCKED` Drafts.
- T020 exposes the run-detail shell and truthful pre-execution state.
- T020A supplies the Foundation consumption coefficient and the model-rule
  carrier. Without them the first kernel's physics arrive from the scenario.
- T020B declares the boundary cycle and the other three semantics this kernel
  obeys, refuses a requirement conflict rather than resolving it, and makes the
  shipped Fuel Loss Draft reach `READY`. All three are hard: a kernel that
  chose its own step order, window, out-of-window or post-bound rule would be
  deciding contract semantics inside an implementation, and a `BLOCKED` Draft
  must not execute, so without T020B this slice cannot run against the shipped
  document at all.

## Decisions Already Taken

The execution-contract questions this task file used to hold open were closed by
the user on 2026-09-22 and are not the Implementer's to reopen: the kernel
semantics are declared by T020B (`D-2026-09-22-kernel-step-semantics`); the
three `REQUIRED` forcing states are settled by
`D-2026-09-22-forcing-state-requirements`; and the coefficient's unit and the
`dispatched-output` promotion are settled by
`D-2026-09-22-consumption-coefficient-unit`, which makes the consumption law
energy-based - specific consumption times energy delivered - and gives the
kernel one forced state during the declared window rather than a power-flow
model.

One decision is taken *during* the slice rather than before it: what the
shipped Fuel Loss document should author, answered from the trajectory this
slice produces.

## Acceptance Criteria

### Placement and the neutral contract

- The kernel lives under `simulator/assetops_simulator/kernel/` and imports no
  `assetops_backend` package.
- A **dependency-neutral contract module** carries what both sides need: it
  imports neither `assetops_backend` nor `assetops_simulator`, and the backend
  reaches its existing names through it so no caller outside changes shape.
  Its contents are **only what the kernel actually reads** - the frozen
  initialization inputs, the model-profile and supported-state declaration, the
  canonical units, the declared contract semantics and the bound policies. A
  migration of convenience is the failure mode here: anything the kernel does
  not read stays where it is.
- The module's name and path are the Implementer's. The import rule is not, and
  `tools/checks/dependency-direction.ps1` is **extended** to assert it - the
  neutral module imports neither side - rather than gaining an exception for
  anything this slice wants to wire up.
- The conformance test and the kernel-versus-reference comparison both touch
  the kernel and backend-owned code, so where they live is a real question.
  Moving the contract arithmetic into the neutral module alongside the rest is
  the expected answer; any other shape that leaves both guards intact is the
  Implementer's to choose. Two things are not available: weakening the guard,
  and copying the reference implementation into the simulator, because a
  comparison against a copy proves nothing. **If no shape exists that keeps the
  guards intact, stop and raise `SPEC_AMBIGUITY`** rather than adding an
  exception.

### The kernel

- A runtime-facing contract initializes private state from a frozen run and
  advances it using current state, simulation time, timestep, and events due in
  that step. It imports no UI, gateway, ingestion or product analytics.
- The first model profile resolves the configured generator and fuel tank from
  the frozen Foundation and consumes no display labels as identifiers or data.
  The consumption coefficient resolves from Foundation; no physics is read from
  the scenario.
- Every initialized value is attributable to a frozen Foundation fact,
  executable scenario input, supported run override, or versioned model rule
  carried by the selected profile. The kernel initializes only from a `READY`
  run, so a missing or contradictory value here is a typed kernel
  initialization error and never a hidden default.
- **World arithmetic is exact-rational.** Values are carried as `Fraction`
  while the model stays rational. An authored decimal is normalised **once**,
  at the input boundary. Calling a denominator limiter after an integration
  step is forbidden: doing it per step would repeatedly approximate the world
  and make the policy's own name false. The policy and its version are recorded
  where a later reader can see which arithmetic a run used.
- The kernel represents simulation time, fuel quantity, generator operating
  state and cumulative generator consumption in canonical units. It carries the
  accepted load and irradiance forcings as supported runtime inputs without
  claiming power-flow consequences the model does not calculate.
- Generator consumption, fuel removal and fuel delivery follow the execution
  roles and point/window semantics accepted in T018 and amended on 2026-09-21,
  including the net-effect treatment of simultaneous causes. Reported
  observations and non-executable evidence conditions cannot enter
  initialization or transition inputs.
- Due-event selection follows the accepted half-open boundary convention and
  applies each authored cause exactly once across step boundaries, including
  when an event falls exactly on a boundary.
- Capacity, insufficient-fuel, invalid-rate and other supported bounds use the
  explicit behaviour accepted in T018. The kernel never silently clamps, drops
  or fabricates a transition.
- **The tank's capacity comes from the frozen identity, not from
  `declared_bounds`.** After T020A that function reports no upper value for
  `fuel-tank-volume` and is right to: the document declares *which* state caps
  which, and the frozen run carries *how big* the tank is
  (`D-2026-09-22-capacity-bound-source`). An implementer who meets `(0.0,
  None)` and either invents 500 or concludes the bound was dropped is wrong
  both ways. `BOUND_CASES["fuel-tank-capacity"]` is unchanged and applies
  against the frozen value, which is what gives this slice's document
  correction something to check the delivery against.
- **The non-negativity floor comes from the selected model profile**, never
  from `IMPLICIT_LOWER_BOUND_DIMENSIONS`. *Volume is non-negative* is a model
  rule; the validation layer only ever injected it, and that layer leaves the
  product path in T022. This tank's minimum usable level is a separate
  Foundation property and a follower, not this slice's.
- Identical frozen inputs and seed produce identical ordered states and runtime
  events. No wall-clock time, filesystem ordering or mutable latest-version
  lookup affects execution.
- Kernel output is private simulator state and runtime events only. It contains
  no Source Envelope, evidence status, health conclusion, Finding or private
  expectation.

### Execution failure is a third vocabulary

- Execution failure is distinct from setup refusal and from setup blocking, and
  the naming rule in `.ai/ARCHITECTURE.md` applies unchanged: **from the name
  alone a reader must be able to say which of the three it is.** Both of the
  earlier decisions were taken before a `run_id` existed or before the Draft was
  persisted, and neither vocabulary belongs to the kernel.
- v4 §23 supplies the member names to reuse rather than reinvent:
  `ORDER_DEPENDENT_GROUP`, `BALANCE_IDENTITY_VIOLATION`,
  `PHYSICAL_RESOLUTION_FAILURE`, `UNSUPPORTED_MODEL_STATE`,
  `INTEGRATION_BOUND_FAILURE`, `TOPOLOGY_INCONSISTENT`. Ship the members this
  kernel can actually raise; the rest arrive with the work that can raise them.
- A `FAIL_RUN` condition is never relabelled as completion.

### Oracles, conformance and the loop

- A fifth oracle kind, `TRAJECTORY`, joins `EXPECTATION_KINDS`. It asserts a
  private-state value at an offset, is checked by the kernel in tests, and is
  read by no executable path and published nowhere. Two properties are part of
  the deliverable rather than commentary: it is **sparse and purposeful**, one
  or two points the scenario is about, because a dense set is a hand-authored
  trace occupying the oracle position and fits the kernel to the author's
  arithmetic; and the slice **states that it is a regression guard rather than
  a correctness proof**, because two implementations of the same arithmetic
  agreeing proves only that they agree.
- Every oracle kind in `EXPECTATION_KINDS` is paired with a test proving it
  *can* fail: a deliberate mutation of what the oracle asserts against, which
  the oracle then reports. This is all the kinds and not only `TRAJECTORY`,
  because an oracle nobody has seen fail is indistinguishable from one that
  cannot, and a tolerance wide enough to admit every answer is circularity
  wearing an assertion's clothes. It lands here because this is the first slice
  with a kernel that can make an oracle fail. Accepted by the user on
  2026-09-22 as the T021 half of the `MAGNITUDE` tolerance question; deriving
  that tolerance from declared error sources is Block F's.
- `EXECUTION_CONTRACT_VERSION` does not move in this slice. Adding `TRAJECTORY`
  widens the document space off every executable path, and a widening
  invalidates no frozen run. The count is in `.ai/FEATURE_MAP.md` under *The
  execution-contract version ledger*.
- **The `supported_states` conformance test is derived from the kernel, not
  hand-maintained.** A test that restates the tuple closes nothing. When it
  lands, `READY` means what its name says, and **this slice retires T020's
  `READY` disclosure** from the run payload and the run-detail screen, because
  this is the slice that makes it false. `BLOCKED` is unaffected.
- The labelled reference implementation of the execution contract runs against
  the shipped document beside the kernel and the two are compared. Any
  disagreement is reported and the kernel is the surviving authority from here
  on.
- **The loop.** The slice runs the kernel against the shipped Fuel Loss
  document under its frozen Draft identity and reports the resulting
  private-state trajectory: the value at each authored offset and the outcome
  at the capacity bound. The document's authored **causes** are then corrected
  from what the kernel computed - the removal magnitude, and whether the
  delivery that overfills the tank is reduced or kept deliberately as a second
  puzzle. Expect disagreement and expect the document to be what is wrong.
  Which corrections to make is the user's call taken during the slice;
  producing the trajectory that makes it answerable is this slice's obligation,
  and no authored number changes without it.
- **Causal proof is not schema proof.** Schema validity, internal invariants
  and causal correctness are three separate claims. Causality is demonstrated
  by executable transitions plus independent example, boundary and metamorphic
  tests, not by the document parsing.
- **The refusals here are defence in depth and are unreachable through the
  normal path**, because T019 already froze and validated everything this slice
  initialises from. They are tested directly, because *unreachable* and *not
  yet reached* look identical in a test suite and only one of them is a
  guarantee. The packet says which they are rather than claiming a reachable
  path.
- No state trace is hand-authored or accepted as execution input. T021 may
  compare in-memory deterministic sequences in tests; T022 owns any persisted
  or checked-in golden playback artifact.
- Run detail may show model readiness and supported capabilities, and exposes
  no private state value or apparent execution result before T022.

## Required Product And Domain Semantics

- ScenarioDefinition supplies authored causes, forcings, reported-observation
  inputs and evidence conditions. Only executable causal and forcing roles
  reach this kernel.
- The kernel owns computed private state. It is not evidence and is visible
  only through later Simulator Lab bindings.
- An expectation is legitimate when it occupies a position where being wrong
  causes a failure, and circular when it occupies a position where being wrong
  causes agreement. That rule is why `TRAJECTORY` is an oracle and why the
  conformance test is derived rather than restated.
- The first kernel is intentionally narrow. Unsupported electrical,
  environmental, storage or cold-chain consequences remain unavailable rather
  than being approximated implicitly.
- Runtime and version identity are part of deterministic provenance. A
  different kernel or model-profile version is a different deterministic
  identity.

## Read When You Reach It

- `Docs/simulator_design_v4.md` §8.1-8.2, integration and the three bound
  outcomes, both already implemented.
- v4 §9, the deterministic draw identity - BLAKE2b-256, canonical encoding,
  domain separation, a draw as a pure function of contract version, seed,
  stream name, step index and ordinal. **The first kernel draws nothing**, so
  this is reference now. It becomes binding at the first slice that introduces
  randomness, and the property that matters there is that adding a stream
  cannot perturb an existing one.
- v4 §21, the trace record kinds, when the kernel starts emitting a trace.
- v4 §7, controller intent and the physical resolver. The first kernel has no
  controller. **Preserve the seam without building it**: nothing in T021 should
  make a requested value and an accepted value the same object later.

## Protected Seams

- Dependency direction: `simulator/` imports no `assetops_backend`, the neutral
  contract module imports neither side, and no slice in this range weakens
  `tools/checks/dependency-direction.ps1` to wire execution up.
- Causal runtime authority: executable transitions precede authoritative or
  golden traces, and precede any verdict that depends on composing causes.
- Physical property ownership: the coefficient comes from Foundation.
- Explicit initialization provenance: no fixture or model code hides initial
  state.
- Execution-role boundary: observation and evidence-condition inputs cannot
  mutate truth.
- Foundation identity: component IDs and supported topology resolve from the
  frozen version, not from current or latest configuration.
- Standing for this range, one line rather than repeated per criterion: no
  product conclusion in a scenario fixture; no private oracle value turned into
  evidence; no manufactured default hiding a missing answer; no simulator
  import of the backend.

## Focused Tests And Review Evidence

- Determinism test: identical frozen identity and seed yield identical ordered
  states and runtime events.
- Exactly-once boundary tests cover an event at run start, at a timestep
  boundary, at the final excluded boundary, and a window spanning several steps.
- Metamorphic tests prove: zero removal adds no removal delta; increasing the
  removal by delta changes post-event fuel by that delta; moving it later keeps
  the earlier prefix equal; removing it removes the discontinuity; changing the
  target affects only the resolved target or fails to initialize. The unaffected
  prefix and unrelated state stay fixed in each.
- Example accounting test covers initial fuel, generator consumption, removal
  and delivery under the accepted bound behaviour and canonical-unit
  conversions.
- An arithmetic test at the authored-decimal boundary proving normalisation
  happens once and that no denominator limiting occurs after an integration
  step - which a value-equality assertion alone will not catch.
- Kernel initialization failure tests cover missing component, unsupported
  topology or input, impossible bound and deterministic-identity mismatch. A
  missing or unlocatable Foundation coefficient, a wrong unit and an unresolved
  initial value are not among them: run setup blocks on all three first, so the
  kernel's guard against them is a record-level assertion.
- A test that the execution-failure kinds are disjoint from both setup
  vocabularies, and that a `FAIL_RUN` condition does not reach completion.
- `TRAJECTORY` tests prove the oracle fails when the kernel disagrees with the
  asserted value, and that it reaches no executable path and no published
  output. A mutation test per oracle kind, each showing the oracle reporting a
  failure it was previously never observed capable of; the packet lists the
  kinds and the mutation used for each.
- A test proving the kernel's non-negativity floor comes from the selected
  model profile, which fails if the floor is sourced from the validation
  layer's constant.
- Conformance test proving the shipped profile's supported set is derived from
  the kernel, including a proof that it fails when the profile claims a state
  the kernel does not implement.
- A test proving the `READY` disclosure is gone from the run payload and the
  run-detail screen, the mirror of the test T020 wrote to prove it was there.
- Contract test proves reported observations, public evidence conditions and
  private expectations are absent from kernel inputs and outputs.
- UI/API test shows readiness only for a compatible `READY` Draft and no
  runtime values before execution.
- The computed trajectory for the shipped document, in the review packet, as
  the evidence behind any document correction.
- `tools/check-architecture.ps1` including the extended dependency guard,
  `tools/check-agent-workflow.ps1`, and the relevant backend, simulator and
  frontend suites.

## Scope Limits

- `host/` is not created, and no execution is composed into the application.
- No removal of the reference implementation. It stops being an authority here
  and leaves the repository with its last product-path caller in T022. Two
  events on two clocks: comparing is this slice's, removing is not. The
  `observation_reconciliation` panel and its payload are untouched here.
- No correction of the two authored reported-observation readings. T022 removes
  them outright, so correcting them here is work done twice and a reading the
  document should not carry made briefly more accurate.
- No Lab clock controls, no displayed trajectory, no persisted or checked-in
  golden artifact; those belong to T022.
- No device observation transform, gateway envelope, staging, Commit,
  ingestion, Replay, analytics or Finding.
- No broad power-flow, battery, weather synthesis, cold-chain or controller
  model. Carrying an accepted forcing is not a claim that its consequences are
  modelled.
- No physics read from the scenario, no contract semantic decided inside the
  implementation, no hand-authored trace accepted as execution input, and no
  runtime injection or intervention-history mutation.

## User Review

No new user checkpoint for the kernel itself; it implements semantics already
accepted in T018, in amendment 1, and in the four 2026-09-22 decisions. One
thing inside the slice returns to the user rather than being settled in
implementation: the correction to the shipped Fuel Loss document, presented
with the computed trajectory and decided by the user during the slice.
