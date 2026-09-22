# T021 - Minimal Fuel Loss Causal Kernel

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T021-minimal-fuel-loss-causal-kernel`

## Feature

Draft SimulationRun And Causal Runtime.

## UI-Verifiable Screen Behavior

A `READY` Fuel Loss Draft can be checked against a real executable model. Its
run detail reports that the selected model profile is executable and names the
private-state capabilities it supports, and that report is now backed by a
conformance test rather than by a hand-written tuple. The `READY` disclosure
T020 put on the record and the screen goes with it, because the test is what
makes it false. The run still does not start or display a state trajectory;
T022 owns execution and runtime presentation.

## Why This Is Next

T020 makes persisted Drafts inspectable and T020A gives the kernel physics that
come from the machine rather than from the story. The next causal prerequisite
is the smallest real state producer that can execute the accepted Fuel Loss
contract. Building it before controls or golden traces prevents authored
fixtures from becoming simulator authority.

This backend-heavy slice directly unlocks T022's UI-verifiable execution. Its
small visible readiness result proves the real run-to-kernel compatibility seam
rather than adding a standalone simulator diagnostics product.

It is also the first slice that can answer a question the shipped Fuel Loss
document has been carrying: what its declared causes actually do to the tank.

## Dependencies

- T018 has accepted execution roles, initialization, timing, and bound
  behavior, as amended on 2026-09-21.
- T019 freezes all required inputs and persists READY/BLOCKED Drafts.
- T020 exposes the run-detail shell and truthful pre-execution state.
- T020A supplies the Foundation consumption coefficient and the model-rule
  carrier. Without them the first kernel's physics arrive from the scenario.

## Decisions Due Before Implementation

These are execution-contract decisions and they return to review. They are not
choices the Implementer may make inside the kernel, because each would let two
conforming kernels disagree, which is what `EXECUTION_CONTRACT_VERSION` exists
to prevent. If any is still open when work starts, the slice stops and asks.

- The `REQUIRED` forcing states the first kernel does not model:
  `site-load-demand`, `plane-of-array-irradiance`, and
  `fuel-level-reporting-availability`. Each is lowered in the scenario, modelled
  by the profile, or reassigned.
- Whether authority over the reporting path moves from the model profile to the
  publication profile. If it stays, this kernel must model reporting
  availability, which is not physics.
- The four unpinned kernel semantics: window apportionment, whether a sample
  within a step sees pre-event or post-event state, what a forcing is outside
  its declared window, and whether a run continues after a bounded change and
  whether later causes apply to the bounded value.

The `dispatched-output` promotion is the remaining half of that forcing-state
decision and it is due earlier still, before T020A is implemented, because it
fixes the coefficient's canonical unit. It is therefore already answered by the
time this slice runs, and its answer decides whether the consumption law here
is runtime-based or energy-based.

One decision is taken *during* the slice rather than before it: what the
shipped Fuel Loss document should author, answered from the trajectory this
slice produces. See the document-correction criterion.

## Acceptance Criteria

- A runtime-facing contract initializes private state from a frozen run and
  advances it using current state, simulation time, timestep, and events due in
  that step. It does not import UI, gateway, ingestion, or product analytics.
- The first model profile resolves the configured generator and fuel tank from
  the frozen Foundation and consumes no display labels as identifiers or data.
  The consumption coefficient resolves from Foundation; no physics is read from
  the scenario.
- Every initialized value is attributable to a frozen Foundation fact,
  executable scenario input, supported run override, or versioned model rule
  carried by the selected profile. The kernel initializes only from a `READY`
  run, which by record invariant carries no value marked absent, so a missing
  or contradictory value here is a typed kernel initialization error and never
  a hidden default. That error is not run setup's refusal and not its blocking
  reason: both of those were decided before a `run_id` existed or before the
  Draft was persisted, and neither vocabulary belongs to the kernel.
- The kernel represents simulation time, fuel quantity, generator operating
  state and cumulative generator consumption in canonical units. It also
  carries the accepted load and irradiance forcings as supported runtime inputs
  without claiming power-flow consequences the model does not calculate.
- Generator consumption, fuel removal, and fuel delivery follow the execution
  roles and point/window semantics accepted in T018 and amended on 2026-09-21,
  including the net-effect treatment of simultaneous causes. Reported
  observations and non-executable evidence conditions cannot enter
  initialization or transition inputs.
- Due-event selection follows the accepted half-open boundary convention and
  applies each authored cause exactly once across step boundaries, including
  when an event falls exactly on a boundary.
- Capacity, insufficient-fuel, invalid-rate, and other supported bounds use the
  explicit behavior accepted in T018. The kernel never silently clamps, drops,
  or fabricates a transition.
- The tank's capacity comes from the frozen identity, not from
  `declared_bounds`. After T020A the document declares *which* state caps which
  and the frozen run carries *how big* the tank is, resolved from Foundation,
  so that function reports no upper value for `fuel-tank-volume` and is right
  to (`D-2026-09-22-capacity-bound-source`). `BOUND_CASES["fuel-tank-capacity"]`
  is unchanged and applies against the frozen value, which is what gives this
  slice's document correction something to check the 2400 delivery against.
  Meeting `(0.0, None)` and either inventing 500 or concluding the bound was
  dropped are both wrong.
- Identical frozen inputs and seed produce identical ordered states and runtime
  events. No wall-clock time, filesystem ordering, or mutable latest-version
  lookup affects execution.
- Kernel output is private simulator state/runtime events only. It contains no
  Source Envelope, evidence status, health conclusion, Finding, or private
  expectation.
- A fifth oracle kind, `TRAJECTORY`, joins `EXPECTATION_KINDS`. It asserts a
  private-state value at an offset, is checked by the kernel in tests, and is
  read by no executable path and published nowhere. Two properties are part of
  the deliverable: it is sparse and purposeful, one or two points the scenario
  is about, because a dense set is a hand-authored trace occupying the oracle
  position; and the slice states that it is a regression guard rather than a
  correctness proof, because an author and a kernel performing the same
  arithmetic and agreeing proves that two implementations agree.
- `EXECUTION_CONTRACT_VERSION` does not move in this slice. Adding
  `TRAJECTORY` widens the document space off every executable path, and a
  widening invalidates no frozen run, so it spends no number. Pinning the four
  unpinned semantics does move it, and that is the declaration's to spend
  wherever it lands, not this slice's. The count is in `.ai/FEATURE_MAP.md`
  under *The execution-contract version ledger*.
- A conformance test asserts that the shipped model profile's
  `supported_states` equals the set of states the kernel actually implements,
  derived from the kernel rather than restated by hand. A test that repeats the
  tuple closes nothing. When this lands, `READY` means what its name says.
- This slice retires T020's `READY` disclosure, from the run payload and from
  the run-detail screen, because the conformance test is what makes it false.
  A claim that has become false goes in the slice that falsifies it; leaving it
  for a later slice ships a false sentence on a screen. `BLOCKED` is unaffected.
- The labelled reference implementation of the execution contract is run
  against the shipped document beside the kernel and the two are compared. Any
  disagreement is reported and the kernel is the surviving authority from here
  on.
- The slice runs the kernel against the shipped Fuel Loss document under its
  frozen Draft identity and reports the resulting private-state trajectory:
  the value at each authored offset and the outcome at the capacity bound. The
  authored numbers in scope are then corrected from that trajectory, and they
  are the authored **causes** - the removal magnitude, and whether the 2400
  delivery that overfills the tank is reduced or kept deliberately as a second
  puzzle. Which corrections to make is the user's call taken during the slice;
  producing the trajectory that makes it answerable is this slice's
  obligation. No authored number changes without the computed trajectory that
  justifies it.
- No state trace is hand-authored or accepted as execution input. T021 may
  compare in-memory deterministic sequences in tests; T022 owns any persisted
  or checked-in golden playback artifact after it wires normal execution
  through this kernel.
- Run detail may show model readiness and supported capabilities, but exposes no
  private state value or apparent execution result before T022.

## Required Product And Domain Semantics

- ScenarioDefinition supplies authored causes, forcings, reported-observation
  inputs, and evidence conditions. Only executable causal/forcing roles reach
  this kernel.
- The kernel owns computed private state. It is not evidence and is visible
  only through later Simulator Lab bindings.
- An expectation is legitimate when it occupies a position where being wrong
  causes a failure, and circular when it occupies a position where being wrong
  causes agreement. That rule is why `TRAJECTORY` is an oracle and why the
  conformance test is derived rather than restated.
- The first kernel is intentionally narrow. Unsupported electrical,
  environmental, storage, or cold-chain consequences remain unavailable rather
  than being approximated implicitly.
- Runtime/version identity is part of deterministic provenance. A different
  kernel or model-profile version is a different deterministic identity.

## Protected Seams

- Causal runtime authority: executable transitions precede authoritative or
  golden traces, and precede any verdict that depends on composing causes.
- Physical property ownership: the coefficient comes from Foundation.
- Explicit initialization provenance: no fixture or model code hides initial
  state.
- Execution-role boundary: observation/evidence-condition inputs cannot mutate
  truth.
- Foundation identity: component IDs and supported topology resolve from the
  frozen version, not from current/latest configuration.
- Simulator/product boundary: runtime modules cannot import evidence, operator
  presentation, analytics, or Findings.

## Focused Tests And Review Evidence

- Determinism test: identical frozen identity and seed yield identical ordered
  states and runtime events.
- Exactly-once boundary tests cover event at run start, timestep boundary, final
  excluded boundary, and a window spanning multiple steps.
- Metamorphic tests prove: zero removal adds no removal delta; increasing the
  removal by delta changes post-event fuel by that delta; moving it later keeps
  the earlier prefix equal; removing it removes the discontinuity; changing the
  target affects only the resolved target or fails to initialize.
- Example accounting test covers initial fuel, generator consumption, removal,
  and delivery under the accepted bound behavior and canonical-unit conversions.
- Kernel initialization failure tests cover missing component, unsupported
  topology or input, impossible bound, and deterministic-identity mismatch.
  A missing or unlocatable Foundation coefficient, a wrong unit and an
  unresolved initial value are not among them: run setup blocks on all three
  before a run can reach the kernel, so the kernel's guard against them is a
  record-level assertion and the packet says so rather than claiming a
  reachable path.
- `TRAJECTORY` tests prove the oracle fails when the kernel disagrees with the
  asserted value, and that it reaches no executable path and no published
  output.
- Conformance test proving the shipped profile's supported set is derived from
  the kernel, including a proof that it fails when the profile claims a state
  the kernel does not implement.
- A test proving the `READY` disclosure is gone from the run payload and the
  run-detail screen, which is the mirror of the test T020 wrote to prove it
  was there.
- Contract test proves reported observations, public evidence conditions, and
  private expectations are absent from kernel inputs and outputs.
- UI/API test shows readiness only for a compatible READY Draft and no runtime
  values before execution.
- The computed trajectory for the shipped document, in the review packet, as
  the evidence behind any document correction.
- Run architecture/workflow checks and relevant backend/frontend suites.

## Scope Limits

- No removal of the reference implementation. It stops being an authority here
  and leaves the repository when its last remaining product-path caller goes,
  which is the `observation_reconciliation` panel and is undecided. Two events
  on two clocks: comparing is this slice's, removing is not. The panel and its
  payload are untouched here.
- No correction of the two authored reported-observation readings, the 155 L
  at 1590 and the 150 L at 1800. T022 removes them outright, so correcting
  them here is work done twice and a reading the document should not carry at
  all made briefly more accurate.
- No Lab clock controls or displayed trajectory; those belong to T022.
- No device observation transform, gateway envelope, staging, Commit,
  ingestion, Replay, analytics, or Finding.
- No broad power-flow, battery, weather synthesis, cold-chain, or controller
  model. Carrying an accepted forcing is not a claim that all consequences are
  modeled.
- No runtime injection or intervention-history mutation.

## User Review

No new user checkpoint for the kernel itself; it implements semantics already
accepted in T018 and amendment 1. Two things inside the slice do return to the
user rather than being settled in implementation: the contract decisions listed
above, and the correction to the shipped Fuel Loss document, which is presented
with the computed trajectory and decided by the user during the slice.
