# T021 - Minimal Fuel Loss Causal Kernel

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T021-minimal-fuel-loss-causal-kernel`

## Feature

Draft SimulationRun And Causal Runtime.

## UI-Verifiable Screen Behavior

A `READY` Fuel Loss Draft can be checked against a real executable model. Its
run detail reports that the selected model profile is executable and names the
private-state capabilities it supports. It still does not start or display a
state trajectory; T022 owns execution and runtime presentation.

## Why This Is Next

T020 makes persisted Drafts inspectable. The next causal prerequisite is the
smallest real state producer that can execute the accepted Fuel Loss contract.
Building it before controls or golden traces prevents authored fixtures from
becoming simulator authority.

This backend-heavy slice directly unlocks T022's UI-verifiable execution. Its
small visible readiness result proves the real run-to-kernel compatibility seam
rather than adding a standalone simulator diagnostics product.

## Dependencies

- T018 has accepted execution roles, initialization, timing, and bound behavior.
- T019 freezes all required inputs and persists READY/BLOCKED Drafts.
- T020 exposes the run-detail shell and truthful pre-execution state.

## Acceptance Criteria

- A runtime-facing contract initializes private state from a frozen run and
  advances it using current state, simulation time, timestep, and events due in
  that step. It does not import UI, gateway, ingestion, or product analytics.
- The first model profile resolves the configured generator and fuel tank from
  the frozen Foundation and consumes no display labels as identifiers or data.
- Every initialized value is attributable to a frozen Foundation fact,
  executable scenario input, supported run override, or versioned model rule.
  Missing or ambiguous inputs produce a typed refusal, never a hidden default.
- The kernel represents simulation time, fuel quantity, generator operating
  state and cumulative generator consumption in canonical units. It also
  carries the accepted load and irradiance forcings as supported runtime inputs
  without claiming power-flow consequences the model does not calculate.
- Generator consumption, fuel removal, and fuel delivery follow the execution
  roles and point/window semantics accepted in T018. Reported observations and
  non-executable evidence conditions cannot enter initialization or transition
  inputs.
- Due-event selection follows the accepted half-open boundary convention and
  applies each authored cause exactly once across step boundaries, including
  when an event falls exactly on a boundary.
- Capacity, insufficient-fuel, invalid-rate, and other supported bounds use the
  explicit behavior accepted in T018. The kernel never silently clamps, drops,
  or fabricates a transition.
- Identical frozen inputs and seed produce identical ordered states and runtime
  events. No wall-clock time, filesystem ordering, or mutable latest-version
  lookup affects execution.
- Kernel output is private simulator state/runtime events only. It contains no
  Source Envelope, evidence status, health conclusion, Finding, or private
  expectation.
- No state trace is hand-authored or accepted as execution input. T021 may
  compare in-memory deterministic sequences in tests, but T022 owns any
  persisted or checked-in golden playback/regression artifact after it wires
  normal execution through this kernel.
- Run detail may show model readiness and supported capabilities, but exposes no
  private state value or apparent execution result before T022.

## Required Product And Domain Semantics

- ScenarioDefinition supplies authored causes, forcings, reported-observation
  inputs, and evidence conditions. Only executable causal/forcing roles reach
  this kernel.
- The kernel owns computed private state. It is not evidence and is visible
  only through later Simulator Lab bindings.
- The first kernel is intentionally narrow. Unsupported electrical,
  environmental, storage, or cold-chain consequences remain unavailable rather
  than being approximated implicitly.
- Runtime/version identity is part of deterministic provenance. A different
  kernel or model-profile version is a different deterministic identity.

## Protected Seams

- Causal runtime authority: executable transitions precede authoritative or
  golden traces.
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
  target affects only the resolved target or is refused.
- Example accounting test covers initial fuel, generator consumption, removal,
  and delivery under the exact accepted T018 bound behavior and canonical-unit
  conversions.
- Refusal tests cover missing component, unsupported topology/input, invalid
  unit, missing initialization, impossible bound, and deterministic-identity
  mismatch.
- Contract test proves reported observations, public evidence conditions, and
  private expectations are absent from kernel inputs and outputs.
- UI/API test shows readiness only for a compatible READY Draft and no runtime
  values before execution.
- Run architecture/workflow checks and relevant backend/frontend suites.

## Scope Limits

- No Lab clock controls or displayed trajectory; those belong to T022.
- No device observation transform, gateway envelope, staging, Commit,
  ingestion, Replay, analytics, or Finding.
- No broad power-flow, battery, weather synthesis, cold-chain, or controller
  model. Carrying an accepted forcing is not a claim that all consequences are
  modeled.
- No runtime injection or intervention-history mutation.

## User Review

No new user checkpoint. T021 implements the executable semantics reviewed in
T018. Any required change to those semantics returns to planning/user review
rather than being decided inside the kernel implementation.
