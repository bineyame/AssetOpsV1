# T022 - Lab Execution And Device Observation

Status: planned
USER_REVIEW_REQUIRED: true

Intended branch: `task/T022-lab-execution-and-device-observation`

## Feature

Draft SimulationRun And Causal Runtime.

## UI-Verifiable Screen Behavior

A user opens a compatible `READY` Fuel Loss Draft, starts it, pauses/resumes or
steps it, and inspects causally computed private fuel/generator state alongside
the fuel-level device's *generated* observations. The event timeline shows
scheduled causes and evidence conditions at simulation time. The scenario
detail screen states, in words, that the document declares causes and does not
declare what the tank holds or what a device reads. Unsupported values and
gateway staging remain explicitly unavailable.

## Why This Is Next

T021 supplies the authoritative causal state producer. This slice connects it
to the Simulator Lab clock, controls, configured SLD/device bindings, and the
observation transform that makes truth and what a device reports two different
objects. Only after this path works can T023 stage canonical publications
honestly.

It is also where the shipped document stops authoring readings. The authored
155 L at offset 1590 was a hand-simulation of exactly the sample this slice's
transform generates, and the pre-kernel arithmetic puts the real sample near
254 L; T021 computes what it actually is. Removing the authored number is what
makes the document consistent with acceptance criteria this slice already
carries, whatever the computed value turns out to be.

## Dependencies

- T020 run detail shell over persisted Drafts.
- T021's accepted minimal Fuel Loss kernel, and the trajectory it reported,
  because the document's corrected numbers come out of that loop.
- T021A, so the document edited here is already under whatever contract
  version T021A produced and `execution_requirement` is already gone from its
  reported observations. This slice edits one document's content and adds a
  component; it moves the number no further.
- The reporting-path authority decision, if it moved the reporting-path forcing
  to the publication profile, because it changes which profile the transform
  asks.

## Decisions Due Before Implementation

- **When the `observation_reconciliation` panel leaves the scenario detail
  screen.** This is Open Question 5 and it is not decided. The panel and its
  API payload are merged T018 work and the last remaining product-path caller
  of `reconcile_reported_observations`; that function cannot leave the
  repository while the panel exists. The Architect's read is that it goes with
  the removal of the authored readings below, because that is when the panel
  has nothing left to reconcile — a recommendation, not a decision. Until then the
  panel is honest, and a thing still honest goes when someone decides to remove
  it rather than because it has become false. This slice does not settle it by
  scope line. If the user says yes before implementation starts, the removal
  and its test-suite consequence are added here as acceptance criteria. If the
  user says no or says nothing, this slice leaves the panel alone and the
  reference implementation stays.
- Whether the operator's hand reading carries a declared reading error, from
  T021's document correction.

## Acceptance Criteria

- Only a compatible `READY` Draft can start. `BLOCKED`, already running, failed,
  or otherwise ineligible states show stable reasons and cannot execute.
- Starting initializes through T021 and transitions execution status truthfully.
  Pause/resume and single-step operate on simulation time; reset restores the
  same frozen initial state without allocating a new `run_id`.
- Clock, current simulation time, timestep, progress, and execution status come
  from runtime state. Wall elapsed and unsupported controls are omitted unless
  backed by implemented behavior.
- The runtime stops at the half-open interval end and reaches `COMPLETED`; a
  typed execution failure reaches `FAILED` with an inspectable reason rather
  than displaying partial output as complete.
- Execution status, causal runtime events, supported state history, and
  run-local observations needed to reopen this Draft and feed T023 persist
  under `run_id` behind runtime/domain ports. Storage details do not enter the
  runtime contract or UI payloads.
- Supported fuel quantity, generator state/consumption, load forcing, and
  irradiance forcing bind to the Lab using canonical component/signal IDs.
  Unsupported electrical, battery, environmental consequence, and SLD values
  remain labelled unavailable rather than inferred.
- The observation transform samples private state rather than copying it. It
  runs on the cadence the frozen publication profile declares, not on the
  kernel's timestep; it resolves the configured device and signal mapping from
  the frozen Foundation; a reporting-path forcing changes what is reported
  without changing what is true; and its output objects are distinct records
  from private state, not copies. Truth exists at every step and a reading
  exists only at a sample. No cadence is inferred from Foundation or from
  configuration text.
- The shipped Fuel Loss document no longer authors what a device reads. The
  authored 155 L at 1590 and 150 L at 1800 are removed. The entry at 1590
  survives as an evidence condition asserting that a reading arrives there and
  is materially below what dispatch accounts for, backed by a `DETECTION`
  expectation and carrying no value. The operator's inspection at 1800 keeps
  the act and loses the number.
- The operator's inspection becomes a run-local manual operational observation
  with its explicit non-device source identity and occurrence time, and its
  value is generated from private state at that offset through the
  `operator-hand-record` source, perturbed only by a declared reading error if
  the document declares one. It is not copied from a scenario timeline row into
  an envelope; T023 may publish only this persisted observation.
- Reported-observation inputs and non-executable evidence conditions affect
  only their defined observation and timeline presentation. They do not
  initialize or mutate private state, which is what the `REPORTED_OBSERVATION`
  role exists for and what survives this slice's document edit unchanged.
- The UI presents private truth and reported values with unmistakable labels,
  simulation timestamps, source identity where applicable, and missing-sample
  states, including the samples the reporting gap suppresses. It does not label
  either as accepted evidence.
- The scenario detail screen states in product language that the document
  declares causes and does not declare what the tank holds or what a device
  reads. The wording is reviewed as copy, not only as layout.
- The configured SLD reuses the established view model and fills only supported
  runtime slots. The operator Foundation remains configuration-only and does
  not receive these values.
- Scheduled scenario entries and runtime-applied events retain stable identity;
  no run-scoped injection control is introduced.
- Generated golden traces, if used for regression or deterministic playback,
  are produced through this normal T021-backed execution path and bound to the
  exact frozen identity and kernel version. A generation command and
  reproduction check own the artifact; the normal execution path remains the
  causal kernel and mismatched traces are refused.
- Gateway staging renders as unavailable with a named T023 prerequisite. There
  are no Source Envelopes, `received_at`, Commit, accepted evidence, product
  health, analytics, or Findings.

## Required Product And Domain Semantics

- Runtime private truth, reported observation, staged publication, and accepted
  evidence are four distinct states. T022 implements only the first two.
- A device observation is generated under configured mapping and cadence and
  may differ from or omit private truth. It is not evidence until a later
  envelope crosses ingestion and is accepted.
- Reporting availability, sensor bias, dropout and gateway outage are one
  family and they attach to the observation transform, not to the kernel.
- Reset replays the same deterministic identity; Rerun, which allocates a new
  Draft identity, remains a later capability.

## Protected Seams

- Truth/observation separation: typed contracts and UI labels prevent a
  reported input from becoming private state or accepted evidence, and prevent
  a generated reading from being presented as truth.
- Shared configured-Site substrate: runtime values attach through Lab-owned
  extension slots; shared/operator Site components import no simulator module.
- Deterministic runtime authority: the clock drives T021 transitions; golden
  traces are derived artifacts only.
- Feature gate and URL chokepoint: all run execution remains Lab-only.
- No-fabricated-value and overflow posture: unsupported fields remain explicit,
  and dense timeline/device content owns scrolling.

## Focused Tests And Review Evidence

- State-machine tests for start, pause, resume, step, reset, completion,
  ineligible action, and typed failure transitions.
- Persistence/reopen test proves a completed run retains the same ordered
  runtime and observation history without re-executing or selecting a trace.
- Clock tests for timestep advancement, half-open end behavior, and no duplicate
  event application across pause/resume or reset.
- Observation tests for device/signal resolution, cadence taken from the frozen
  publication profile, suppressed samples across the reporting gap, ordered
  timestamps, the generated operator-record value and its explicit source, and
  separation of private truth from reported values.
- A test proving the generated sample at the offset the document used to author
  is computed from private state and matches the kernel's trajectory, rather
  than reproducing any authored number.
- Document test proving no reported observation carries an authored value and
  that the evidence condition at 1590 asserts a relationship rather than a
  quantity.
- UI tests compare supported runtime slots against runtime records, assert
  unsupported values and gateway staging remain unavailable, and prove the
  operator Foundation still has no runtime values.
- Golden-trace reproduction/mismatch proof if a generated artifact is included.
- Gate/route and architecture checks proving simulator imports stay out of the
  shared substrate and operator shell.
- Layout evidence for clock/control header, SLD/runtime slots, device comparison,
  and event timeline at required viewports.
- Run workflow checks, relevant suites, typecheck, and production build.

## Scope Limits

- No sensor bias in the Fuel Loss Event. The mockups already carry a separate
  `Sensor Bias` scenario, and keeping Fuel Loss free of bias keeps its one
  lesson clean: a real loss, hidden by a reporting gap.
- No arbitrary fast-forward/jump-to, Rerun, Replay, or event injection unless
  separately replanned.
- No Source Envelope, gateway staging, Commit, ingestion, accepted evidence,
  source health, analytics, Finding, or operator runtime overlay.
- No full electrical dispatch/power-flow, battery, weather synthesis, or broad
  device-fault model.

## User Review

User review is required for control behavior, private-truth visibility,
truth-versus-reported labels, unavailable-value treatment, and the resulting
Simulator Lab narrative.

One review item is not a control. The scenario detail screen now says in words
that the document declares causes and does not declare what the tank holds or
what a device reads. That sentence is the product-facing statement of this
whole sequence and is worth reviewing as copy. If the reconciliation panel is
removed in this slice, its removal is reviewed here too.

Do not assume T023 presentation remains correct if the user redirects those
semantics.
