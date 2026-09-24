# T025 - Generator policy and a credible full mini-grid run

Status: planned
USER_REVIEW_REQUIRED: true

Map: A completion.
Depends on: T024.
Next: T026 dispatch-capable gateway, then T027 internal architecture demo.
Branch: task/T025-generator-policy-and-healthy-reference
Sizing: electrical runtime extension and A acceptance checkpoint.

## Outcome

Run one complete Kobo-like site through healthy operation and a cause-authored
prolonged-generator interval. Change a policy and see generator runtime,
battery/service behavior and fuel use respond in Lab.

PV, three addressed loads, battery, generator and named flows now form one
credible electrical world. The prolonged-runtime recipe supplies C's future
evidence; it does not assign a Finding.

## Read for detail

- v4 sections 4.3, 5-10, 17, 23 and 25.
- Roadmap sections 3.1-3.3 and 7/A.
- Shared checks and exclusions: tasks/README.md.

## Deliver and acceptance

1. Model generator physical states STOPPED, STARTING, RUNNING and FAILED with
   an explicit discrete-state specification: scope, allowed values,
   initialization owner, transition rules and observable signals.
2. Each discrete transition records the addressed state, previous/next values,
   causal event/controller reference and simulation instant.
3. Implement start/stop thresholds, minimum runtime and declared output limits.
   Fuel use follows accepted delivered energy using the Foundation coefficient.
4. Keep controller request distinct from actual generator physical state and
   power; requested start is not proof of running output.
5. Generator-to-load and generator-to-battery flows join PV/storage flows under
   the deterministic resolver and exact conservation checks.
6. Healthy baseline serves the intended demand with inspectable reserve and
   service behavior. Declare all dynamic initial conditions.
7. A prolonged-runtime recipe authors policy/recovery/load causes only.
   PV and battery capability recover while the generator remains requested
   under the declared stop policy.
8. A changed policy in a separately frozen scenario produces an explainable
   runtime/flow change. This is an A demonstration, not an all-else-equal
   PairedExperiment or verified intervention claim.
9. A reserve-violation case and a constrained-service case remain visible.
   Lower generator runtime alone is not presented as an operational improvement.
10. Lab exposes simulation time, component state, per-load service, SOC/power,
    named flows, requested controls and accepted values.
11. A discrete reading at T observes a transition due at T.
    Numeric noise/quantization is not applied to discrete enums.
12. Public generator status/power observations come from the observation path.
    Missing or delayed status reporting leaves physics unchanged.
13. Same frozen identity reproduces healthy and prolonged-runtime trajectories.
    Run-start state and time-valid policy remain reconstructible.
14. Control vocabulary retains v4 section 5.1's lexical and semantic limits;
    physical generator state is not renamed switching position/controller mode.
15. A's acceptance packet includes independent balances, boundary timing,
    request-versus-output and changed-forcing/policy demonstrations.

## Proof

| Case | Expected observation |
| --- | --- |
| Healthy sunny-to-low-PV interval | Coherent source transitions and service |
| Start request during start delay | Request visible, no invented generation |
| Minimum-runtime constraint | Stop request/policy and actual state explained |
| Changed stop policy | Runtime changes through physics |
| Low reserve/high load | Constraint and service consequence visible |
| Sample coincides with state transition | Post-event discrete reading |
| Missing generator report | World state unaffected |

Run simulator/host, setup and frontend tests, shared checks and layout evidence
on the complete Lab site. Include hand-checked energy/fuel quantities for a
generator interval and compare healthy versus prolonged-runtime traces.

## Scope limits

T035 owns the cause-authored start-failure/service recipe and product assessment.
This task supplies the discrete-state contract it will use.
B is not complete: Lab physics still has no accepted operator history.
No Finding, economics, intervention UI or paired-comparison claim.

## Review

The owner reviews A: a healthy full mini-grid and a forcing/policy change that
alters physical behavior coherently. Calibrated fidelity to a real plant is
not asserted by these synthetic proofs.
Review outcome: pending.
