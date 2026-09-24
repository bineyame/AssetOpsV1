# T022 - Execute a Draft and inspect generated device observations

Status: planned
USER_REVIEW_REQUIRED: true

Map: A starter.
Depends on: T021 and T021A.
Next: T023.
Branch: task/T022-lab-execution-and-device-observation
Sizing: first visible simulator truth/observation boundary.

## Outcome

In gated Lab, create a READY Fuel Loss Draft, start it, step it and run it to
completion. Inspect simulation time, private tank state and generated sensor
readings, including a declared reporting gap.
Operator Site history remains unchanged.

The kernel now exists; this task makes its physical/reporting distinction
directly inspectable before the gateway gets an envelope contract.

## Read for detail

- v4 sections 3, 6, 9, 11.1, 21 and 25.
- Starter handoff: Observation, Placement and Proof.
- DECISIONS: D-2026-09-22-reconciliation-panel-retirement.
- CODE_STATE T020 for Runs controls and gate regressions.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Wire the execution port through the neutral host leaf.
The backend consumes the neutral port/projection contract, not simulator types.
Use a separate observation transform keyed by
(StateRef, device_id, signal_id) and the frozen publication profile.

LabProjection may contain generated observations and private state for gated
inspection. Raw DeviceObservation and world/trace objects are not product input.
Keep the UI clear about private truth, reported value and missing report.

## Acceptance criteria

1. Start accepts an eligible frozen Draft; BLOCKED, unknown, incompatible or
   already-terminal input yields a typed, inspectable outcome.
2. Step advances declared simulation time; run-to-end produces the same final
   trajectory as the equivalent sequence of steps.
   Execution speed does not change simulation timestamps.
3. Repeated action/retry cannot accidentally advance a single requested step
   twice. Concurrent controls cannot corrupt a run's progression.
4. Start/step/run-to-end failures are visible separately from setup eligibility.
   Completed and failed runs retain their frozen identity and trace provenance.
5. The Lab shows true tank volume, generated reported value, device/signal,
   source sample time and quality for the selected boundary.
6. Observation timing follows v4 section 6: post-event state at T and preceding
   interval measurement ending at T. Initial interval values remain unavailable.
7. Sampling occurs only when due. A reporting gap yields no fresh sample;
   any retained last reading displays its own time and stale status.
8. Changing cadence, bias or dropout changes observations while the private
   physical trajectory and controller-local inputs remain unchanged.
9. Generated readings replace authored readings as the runtime presentation.
   Private expectations remain test oracles, never substitutes for missing data.
10. Bindings distinguish two signals/devices and repeated component addresses;
    a change to one reporting path leaves the others intact.
11. For the first stochastic reporting mechanism, implement v4's BLAKE2b-256
    draw contract and prove that adding an unrelated stream changes no existing
    stream. Freeze seed and reporting parameters needed for reproduction.
12. Persist sufficient private execution/observation artifacts for reloadable
    completed-run inspection. Show an explicit interrupted/unavailable state
    if a live execution handle cannot resume after host restart.
13. Generated artifacts bind to frozen inputs and kernel/profile/numeric versions.
    A new execution of identical frozen content reproduces canonical output.
14. Retire observation_reconciliation, its panel and reference helper when
    their last product caller is removed; remove declared_bounds and
    IMPLICIT_LOWER_BOUND_DIMENSIONS under the retirement decision.
15. Gates cover APIs, routes, controls and private artifacts. With Lab disabled,
    execution and private inspection are inaccessible; existing Site pages remain.
16. Snapshot accepted Site history before and after execution and prove no write.
    There is no Commit action or envelope release in this slice.

## Proof

Demonstrate through the normal UI:
create READY Draft -> start -> step across a fuel event -> inspect state/reading
-> step through a reporting gap -> run to end -> reload completed detail.

Pair that path with these focused assertions:

| Case | Required result |
| --- | --- |
| Event and sample at T | Reading uses post-event stock |
| First interval measurement | Missing without historical input |
| Different step batching | Same trajectory and observation content |
| Changed bias/cadence/dropout | Same world, changed report series |
| Reporting gap | No fabricated fresh reading |
| Unrelated RNG stream | Existing reported values unchanged |
| Gate disabled | No private API/UI reachability |
| Draft executes to completion | Accepted Site history unchanged |
| Process restart | Persisted inspection or honest interruption |

Run simulator/host suites established in T021, relevant backend and frontend
tests, shared checks and layout evidence on populated Run detail.
A gate test must first establish that the enabled screen contains controls.

## Scope limits

Gateway envelope conversion/staging is T023.
Electrical operation is T024-T025.
Interactive event injection/reset is deferred to T032's immutable intervention
control; current events come only from frozen authored input.
No operator reconciliation or Findings are delivered here.

## Review

The owner steps a real run and distinguishes truth, reporting gap and measured
value. The Reviewer checks the observation boundary and gate from API to UI.
Review outcome: pending.
