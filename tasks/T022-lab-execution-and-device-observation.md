# T022 - Lab Execution And Device Observation

Status: planned
USER_REVIEW_REQUIRED: true

Intended branch: `task/T022-lab-execution-and-device-observation`

## Feature

Draft SimulationRun And Causal Runtime. Block B of `.ai/FEATURE_MAP.md`, and
the slice that completes it.

## UI-Verifiable Screen Behavior

A user opens a compatible `READY` Fuel Loss Draft, starts it, pauses, resumes
or steps it, and watches the tank level fall because the generator burned fuel
and fall further because fuel was removed - with the **true** tank level and
the **device-reported** level side by side, disagreeing across a declared
reporting gap. The event timeline shows scheduled causes and evidence
conditions at simulation time, explaining the situation being tested rather
than what AssetOps knows. The scenario detail screen states, in words, that the
document declares causes and does not declare what the tank holds or what a
device reads. Unsupported values and gateway staging remain explicitly
unavailable.

This is the first block end that is a demo. Remove the removal cause and the
discontinuity disappears; move it and it moves.

## Why This Is Next

T021 supplies the authoritative causal state producer. This slice connects it
to the Simulator Lab clock, controls, configured SLD and device bindings, and
the observation transform that makes truth and what a device reports two
different objects. Only after this path works can T023 stage canonical
publications honestly.

It is also where the shipped document stops authoring readings. The authored
155 L at offset 1590 was a hand-simulation of exactly the sample this slice's
transform generates. Removing the authored number is what makes the document
consistent with acceptance criteria this slice already carries, whatever the
computed value turns out to be.

## Dependencies

- T020's run-detail shell over persisted Drafts.
- T021's accepted minimal Fuel Loss kernel in
  `simulator/assetops_simulator/kernel/`, the dependency-neutral contract
  module it introduced, and the trajectory it reported - the document's
  corrected numbers come out of that loop.
- T021A, so the document edited here is already under whatever contract version
  T021A produced and `execution_requirement` is already gone from its reported
  observations. This slice edits one document's content and adds a component;
  it moves the version no further.
- T020B's move of reporting-path authority to the publication profile, which
  decides which profile the transform asks.

## Decisions Already Taken

**The `observation_reconciliation` panel leaves the scenario detail screen in
this slice.** `D-2026-09-22-reconciliation-panel-retirement` settled it on
2026-09-22 and it is not reopened here. The panel is honest while the document
still carries two authored readings; (f) below removes them, and a panel with
nothing left to reconcile is a claim that has become false. It goes in the
slice that falsifies it.

## Acceptance Criteria

### Execution and the composition leaf

- Only a compatible `READY` Draft can start. `BLOCKED`, already running, failed
  or otherwise ineligible states show stable reasons and cannot execute.
- Starting initializes through T021's kernel and transitions execution status
  truthfully. Pause, resume and single-step operate on simulation time; reset
  restores the same frozen initial state without allocating a new `run_id`.
- Clock, current simulation time, timestep, progress and execution status come
  from runtime state. Wall elapsed and unsupported controls are omitted unless
  backed by implemented behaviour.
- The runtime stops at the half-open interval end and reaches `COMPLETED`; a
  typed execution failure from T021's vocabulary reaches `FAILED` with an
  inspectable reason rather than displaying partial output as complete.
- **The execution adapter is the composition leaf v4 §3.2 and §3.3 name**, and
  this is the first slice with anything to compose. It may import both the
  backend and the simulator; nothing imports it. Those two are simultaneously
  true in one shape: **the backend declares the execution port and receives an
  implementation, and the leaf is what constructs the simulator-backed one and
  hands it over** - the pattern `backend/assetops_backend/runs/composition.py`
  already uses for the run stores. Its shape is the port the Lab drives -
  start, step, run to end, staged envelopes, commit - with the staging and
  commit members unimplemented here. `tools/checks/dependency-direction.ps1` is
  **extended** to assert that nothing imports the leaf, rather than relaxed to
  let the Lab reach the kernel.
- **The adapter returns a private Lab projection**, and it may carry generated
  device observations. The Lab is gated simulator UI and may render private
  tank level beside reported level; the product receives neither directly
  (v4 §3.3). A Lab projection is never a product record and never crosses
  ingestion.
- Execution status, causal runtime events, supported state history and
  run-local observations needed to reopen this Draft and feed T023 persist
  under `run_id` behind runtime and domain ports. Storage details do not enter
  the runtime contract or UI payloads.

### The observation transform

- **The observation transform is a component, not a step inside execution.** It
  samples private state rather than copying it, resolves the configured device
  and signal mapping from the frozen Foundation, and its output objects are
  distinct records from private state rather than copies. **Truth exists at
  every step; a reading exists only at a declared sample instant.**
- **A binding is keyed by a triple - world-state address, `device_id`,
  `signal_id` - and the state address stays a distinct element of that key.**
  Until T020A's deferred addressing layer lands the address is the state key;
  when it lands it becomes a `StateRef`. Keeping the triple unflattened is what
  makes that a replacement of one element rather than a reshaping of every
  binding, and is the same rule T020A applied to Foundation bindings: a
  component identity is never spliced into a state-key string.
- It runs on the cadence the frozen publication profile declares, not on the
  kernel's timestep. No cadence is inferred from Foundation, from a device, or
  from configuration text.
- A reporting-path forcing changes what is reported without changing what is
  true.
- **Do not interpolate through the reporting gap.** During the gap there is no
  fresh sample, and the UI shows a missing sample. Carrying an old reading
  forward is legitimate only if a declared stale-reporting transform does it
  and labels it stale. A convincing-looking trace through the gap is exactly
  the failure this slice exists to make visible.
- **At the first boundary there is no preceding interval**, so an interval
  signal is unavailable there. T020B declared this; this slice is the first
  that can violate it.
- **Reporting faults divide, and this slice gets one half.** Sampling, bias,
  dropout and quantisation belong to the observation transform. Buffering,
  outage, retry, delayed release, duplicate publication and publication timing
  belong to the gateway and are T023's. A cadence-driven sampling gap is
  sufficient here; do not build the gateway's half early.

### The document, and the hand dip

- **(f), in the document and in the code.** The shipped Fuel Loss document no
  longer authors what a device reads: the authored 155 L at 1590 and 150 L at
  1800 are removed. The entry at 1590 survives as an **evidence condition**
  asserting that a reading arrives there and is materially below what dispatch
  accounts for, backed by a `DETECTION` expectation and carrying no value. The
  operator's inspection at 1800 keeps the act and loses the number.
- **The hand dip is a generated operational observation, not a copied number.**
  It becomes a run-local manual operational observation with its own non-device
  source identity, its tank, its occurrence time, and a value generated from
  private state at that offset through the `operator-hand-record` source,
  perturbed only by a declared reading error if the document declares one. A
  physical fuel addition and its human delivery report are different events:
  the addition can happen while the record is delayed, wrong or absent. It is
  not copied from a scenario timeline row into an envelope, and T023 may
  publish only this persisted observation.
- Reported-observation inputs and non-executable evidence conditions affect
  only their defined observation and timeline presentation. They do not
  initialize or mutate private state, which is what the `REPORTED_OBSERVATION`
  role exists for and what survives this slice's document edit unchanged.
- **The `observation_reconciliation` panel and its payload leave the scenario
  detail screen**, and with them `reconcile_reported_observations`,
  `declared_bounds` and `IMPLICIT_LOWER_BOUND_DIMENSIONS` leave the product
  path. This is a visible change to merged work and the slice says so rather
  than performing it as cleanup. The reference implementation's last
  product-path caller goes here, which is what completes the removal
  `D-2026-09-21-specification-reference-implementation` scheduled.

### Presentation

- The UI presents private truth and reported values with unmistakable labels,
  simulation timestamps, source identity where applicable, and missing-sample
  states including the samples the reporting gap suppresses. It labels neither
  as accepted evidence.
- The scenario detail screen states in product language that the document
  declares causes and does not declare what the tank holds or what a device
  reads. The wording is reviewed as copy, not only as layout.
- The configured SLD reuses the established view model and fills only supported
  runtime slots. Unsupported electrical, battery, environmental-consequence and
  SLD values remain labelled unavailable rather than inferred. The operator
  Foundation remains configuration-only and receives none of these values.
- Scheduled scenario entries and runtime-applied events retain stable identity;
  no run-scoped injection control is introduced.
- Generated golden traces, if used for regression or deterministic playback,
  are produced through this normal kernel-backed execution path and bound to
  the exact frozen identity and kernel version. A generation command and
  reproduction check own the artifact; the normal execution path remains the
  causal kernel and mismatched traces are refused.
- Gateway staging renders as unavailable with a named T023 prerequisite. There
  are no Source Envelopes, no `received_at`, no Commit, no accepted evidence,
  no product health, no analytics and no Findings.

## Required Product And Domain Semantics

- Runtime private truth, reported observation, staged publication and accepted
  evidence are four distinct states. This slice implements only the first two.
- A device observation is generated under configured mapping and cadence and
  may differ from or omit private truth. It is not evidence until a later
  envelope crosses ingestion and is accepted.
- A scenario declares no reading. Every device value the product will ever see
  is generated by this component, which is why the document losing its authored
  readings is a correction rather than a subtraction.
- Reset replays the same deterministic identity; Rerun, which allocates a new
  Draft identity, remains a later capability.

## Read When You Reach It

- `Docs/simulator_design_v4.md` §11.1, the full declarable fault list. This
  slice builds cadence and gap and none of the rest.
- v4 §3.3, the execution adapter's shape as the port the Lab drives - useful
  when wiring, not a constraint the slice has to reason about.
- v4 §21, trace record kinds, and the distinction between simulator trace
  playback as a debug mechanism and AssetOps Replay as a historical view over
  recorded Site history.

## Protected Seams

- Truth/observation separation: typed contracts and UI labels prevent a
  reported input from becoming private state or accepted evidence, and prevent
  a generated reading from being presented as truth.
- Dependency direction: the Lab reaches the kernel through the composition
  leaf, nothing imports the leaf, and `simulator/` still imports no
  `assetops_backend`.
- Shared configured-Site substrate: runtime values attach through Lab-owned
  extension slots; shared and operator Site components import no simulator
  module.
- Deterministic runtime authority: the clock drives kernel transitions; golden
  traces are derived artifacts only.
- Feature gate and URL chokepoint: all run execution remains Lab-only.
- No-fabricated-value and overflow posture: unsupported fields remain explicit,
  and dense timeline and device content owns its own scrolling.
- Standing for this range, one line rather than repeated per criterion: no
  product conclusion in a scenario fixture; no private oracle value turned into
  evidence; no manufactured default hiding a missing answer; no simulator
  import of the backend.

## Focused Tests And Review Evidence

- State-machine tests for start, pause, resume, step, reset, completion,
  ineligible action and typed failure transitions.
- Persistence and reopen test proves a completed run retains the same ordered
  runtime and observation history without re-executing or selecting a trace.
- Clock tests for timestep advancement, half-open end behaviour, and no
  duplicate event application across pause, resume or reset.
- Observation tests for device and signal resolution, cadence taken from the
  frozen publication profile, ordered timestamps, the generated operator-record
  value and its explicit source, and separation of private truth from reported
  values.
- **A reporting-gap test proving the gap changes observations and nothing
  else**: the truth trajectory across the gap is unchanged, no reading is
  emitted inside it, and no value is interpolated or carried forward through
  it.
- A test that an interval signal at the first boundary is unavailable rather
  than zero.
- A test proving the generated sample at the offset the document used to author
  is computed from private state and matches the kernel's trajectory, rather
  than reproducing any authored number.
- Document test proving no reported observation carries an authored value and
  that the evidence condition at 1590 asserts a relationship rather than a
  quantity.
- A test proving the reconciliation payload and panel are gone, and that
  `reconcile_reported_observations`, `declared_bounds` and
  `IMPLICIT_LOWER_BOUND_DIMENSIONS` have no remaining product-path caller.
- **A test that no operator history changes during a Draft run**, measured
  before and after a completed run.
- UI tests compare supported runtime slots against runtime records, assert
  unsupported values and gateway staging remain unavailable, and prove the
  operator Foundation still has no runtime values.
- Golden-trace reproduction and mismatch proof if a generated artifact is
  included.
- Gate and route tests plus the extended dependency guard, proving simulator
  imports stay out of the shared substrate and operator shell and that nothing
  imports the composition leaf.
- Layout evidence for the clock and control header, SLD and runtime slots, the
  device comparison, and the event timeline at the required viewports.
- `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1`, the backend,
  simulator and frontend suites, typecheck, and production build.

## Scope Limits

- **No sensor bias in the Fuel Loss Event.** The mockups already carry a
  separate `Sensor Bias` recipe, and keeping Fuel Loss free of bias keeps its
  one lesson clean: a real loss, hidden by a reporting gap.
- No gateway-half fault behaviour: no buffering, outage, retry, delayed
  release, duplicate publication or publication timing. These belong to a later
  slice that owns gateway faults; neither T022 nor T023 builds them.
- No Source Envelope, gateway staging, Commit, ingestion, accepted evidence,
  source health, analytics, Finding or operator runtime overlay.
- No arbitrary fast-forward or jump-to, Rerun, Replay, or event injection
  unless separately replanned.
- No authored reading reaching a transition or an initialisation, and no
  cadence inferred from anything but the frozen publication profile.
- No full electrical dispatch or power-flow, battery, weather synthesis, or
  broad device-fault model. PV, battery and loads stay configured assets.

## User Review

User review is required for control behaviour, private-truth visibility,
truth-versus-reported labels, unavailable-value treatment, and the resulting
Simulator Lab narrative.

One review item is not a control. The scenario detail screen now says in words
that the document declares causes and does not declare what the tank holds or
what a device reads. That sentence is the product-facing statement of this
whole sequence and is worth reviewing as copy rather than only as layout. The
reconciliation panel's removal is shown here too - as a change already
decided, not as a question.

Do not assume T023 presentation remains correct if the user redirects these
semantics.
