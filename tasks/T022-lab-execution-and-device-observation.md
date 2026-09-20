# T022 - Lab Execution And Device Observation

Status: planned
USER_REVIEW_REQUIRED: true

Intended branch: `task/T022-lab-execution-and-device-observation`

## Feature

Draft SimulationRun And Causal Runtime.

## UI-Verifiable Screen Behavior

A user opens a compatible `READY` Fuel Loss Draft, starts it, pauses/resumes or
steps it, and inspects causally computed private fuel/generator state alongside
the configured fuel-level device's reported observations. The event timeline
shows scheduled causes and observation conditions at simulation time. Unsupported
values and gateway staging remain explicitly unavailable.

## Why This Is Next

T021 supplies the authoritative causal state producer. This slice connects it
to the Simulator Lab clock, controls, configured SLD/device bindings, and the
minimum observation transform needed to demonstrate that truth and what a
device reports are different objects. Only after this path works can T023 stage
canonical publications honestly.

## Dependencies

- T020 run detail shell over persisted Drafts.
- T021 accepted minimal Fuel Loss kernel and runtime-facing contract.

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
- The minimal observation transform resolves the configured fuel-level device
  and signal mapping, applies the cadence frozen from the explicit versioned
  observation profile and the scenario's reporting gap, and emits ordered
  run-local observations distinct from private truth. Foundation supplies no
  cadence in the current schema, so none is inferred from configuration text.
- Reported-observation inputs such as the accepted post-gap level and manual
  inspection affect only their defined observation/event presentation. They do
  not initialize or mutate private fuel state. Non-executable evidence
  conditions remain timeline expectations, not observations, unless T018
  explicitly classified them otherwise.
- The accepted hand inspection becomes a run-local manual operational
  observation with its explicit non-device source identity and occurrence
  time. It is not copied straight from a scenario timeline row into an envelope;
  T023 may publish only this persisted observation through its typed source
  path.
- The UI presents private truth and reported values with unmistakable labels,
  simulation timestamps, source identity where applicable, and missing-sample
  states. It does not label either as accepted evidence.
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
- A device observation is generated under configured mapping/cadence and may
  differ from or omit private truth. It is not evidence until a later envelope
  crosses ingestion and is accepted.
- Reset replays the same deterministic identity; Rerun, which allocates a new
  Draft identity, remains a later capability.

## Protected Seams

- Shared configured-Site substrate: runtime values attach through Lab-owned
  extension slots; shared/operator Site components import no simulator module.
- Truth/observation separation: typed contracts and UI labels prevent a
  reported input from becoming private state or accepted evidence.
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
- Observation tests for configured device/signal resolution, cadence, reporting
  gap, ordered timestamps, explicit manual-observation source, and separation
  of private truth from reported/manual values.
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

- No arbitrary fast-forward/jump-to, Rerun, Replay, or event injection unless
  separately replanned.
- No Source Envelope, gateway staging, Commit, ingestion, accepted evidence,
  source health, analytics, Finding, or operator runtime overlay.
- No full electrical dispatch/power-flow, battery, weather synthesis, or broad
  device-fault model.

## User Review

User review is required for control behavior, private-truth visibility,
truth-versus-reported labels, unavailable-value treatment, and the resulting
Simulator Lab narrative. Do not assume T023 presentation remains correct if the
user redirects those semantics.
