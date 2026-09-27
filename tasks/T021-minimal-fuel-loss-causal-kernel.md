# T021 - Independent causal Fuel Loss kernel

Status: planned
USER_REVIEW_REQUIRED: true

Map: A starter; directly unlocks T022's visible execution.
Depends on: T020B and its addressed frozen inputs.
Next: T021A, then T022.
Branch: task/T021-minimal-fuel-loss-causal-kernel
Sizing: first simulator truth boundary; narrow fuel world only.

## Outcome

Execute a product-path READY Fuel Loss Draft in an independently testable
simulator. Produce a private trajectory whose tank movement follows dispatch,
consumption and events. Removing or retiming a cause changes the result.
T022 will expose this result through Lab controls.

This is the causal proof before observations or golden traces can be trusted.
T021A follows this task; its parser narrowing is not a kernel prerequisite.

## Read for detail

- v4 sections 3, 4.2-4.3, 6, 8-10, 17, 21, 23-25.
- Starter handoff: Runtime, Placement, Contract Versions and Proof.
- DECISIONS: D-2026-09-21-projection-versus-composition,
  D-2026-09-21-causal-runtime-before-golden-traces,
  D-2026-09-22-capacity-bound-source,
  D-2026-09-22-contract-version-scope.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Place the kernel in simulator/. Move the minimum shared execution/schema types
to dependency-neutral contracts. Establish a neutral host/ composition leaf
and runnable simulator/host test roots.
The backend and simulator cannot import each other's packages; nothing imports
host. Tests composing both live outside the backend's scanned tree.

Execute frozen input content, not mutable current Site/scenario objects.
Use addressed stocks and flows, simulation time, due events and the declared
fuel model profile. Keep domain-specific fuel rules outside shared mechanisms.

The minimum law is fuel use = specific consumption in L/kWh times delivered
generator energy. Power comes from forcing; this is not an electrical dispatch
controller. Resolve tank bounds from the declared bound plus frozen capacity.

Use EXACT_RATIONAL with one-time authored-float normalization.
No step may approximate its result with limit_denominator.
Bind private trajectory identity to frozen inputs, kernel/model versions and
numeric policy using the v4 BLAKE2b-256 identity domain.

## Acceptance criteria

1. A READY Draft from T020B executes; a BLOCKED or incompatible-version Draft
   cannot be coerced into execution.
2. Reconstruct execution from frozen content after current Site/scenario values
   change. The same identity produces the same canonical private trajectory.
3. Dispatch energy and L/kWh consumption produce an independently calculated
   tank trajectory at selected boundaries.
4. Fuel removal changes the stock at its scheduled boundary. Retiming the event
   moves the discontinuity; removing it removes the discontinuity.
5. Scenario expectations, authored reported readings and reconciliation output
   are unavailable to the evolution path and cannot determine its result.
6. Apply events due at T before exposing stock state at T.
   Interval output ending at T still describes the preceding interval.
7. Preserve declared linear ramps, window boundaries and out-of-window
   unavailability. Required missing forcing fails honestly, without hold-last.
8. The first boundary has no preceding interval measurement unless the frozen
   profile declares historical input.
9. Same-time event groups have deterministic contract-defined behavior.
   An order-dependent group fails as ORDER_DEPENDENT_GROUP.
10. Quantity conservation is exact. Exercise REFUSED_AT_PARSE, FAIL_RUN and
    BOUNDED_AND_RECORDED at their respective phases.
    Continuing after a bounded transition uses the recorded bounded value.
11. A capacity bound uses the actual frozen Foundation value, including a
    second Site with a different capacity.
12. Execution failures distinguish balance, resolution, unsupported state,
    topology and integration failures from setup BLOCKED/refusal.
    Partial output is labelled failed and cannot masquerade as a complete run.
13. Kernel conformance derives the advertised fuel supported set from executable
    handlers/laws and verifies each supported role. Unsupported optional
    demand/irradiance remain explicitly outside this profile.
14. Remove the readiness disclosure only when that conformance establishes its
    expiry condition. Keep any still-honest limitation visible.
15. Compute the shipped Fuel Loss trajectory independently, compare its authored
    expectations, and correct inconsistent private expectations from that result.
    Record the mismatch and calculation; never tune the kernel to old numbers.
16. If TRAJECTORY expectations are needed, keep them private validation inputs.
    That pure oracle widening alone does not move EXECUTION_CONTRACT_VERSION.
17. The specification reference reconciliation helper loses authority when
    compared with this kernel. Its product panel/payload retirement remains T022.

## Numerical and causal proof

Use a hand-derived constant-power interval, a ramp interval, a scheduled fuel
movement and a bounded tank case. Assert exact rational states at boundaries,
not only matching screenshots or snapshots generated by the implementation.

| Mutation | Required relationship |
| --- | --- |
| Remove fuel-removal event | Only consequences of that cause disappear |
| Retime event one step | Stock discontinuity shifts to that boundary |
| Change L/kWh coefficient | Consumption changes with dispatched energy |
| Change capacity only | Bound behavior follows frozen capacity |
| Change private expectation | World trajectory unchanged |
| Change current Site after freezing | Frozen trajectory unchanged |
| Add unrelated component declaration | Existing addressed fuel result stable |
| Repeat run in supported runtime | Canonical trajectory identical |

A generated golden trace is permitted after these independent proofs.
It binds to the full frozen identity and versions; it is not an authored oracle.

For deterministic stochastic mechanisms introduced later, v4 section 9 fixes
BLAKE2b-256 draws by seed, stream, step and ordinal.
This task need not add unused stochastic physics; T022 tests the contract when
its first noise/dropout demonstration consumes a stream.

## Integration and checks

Establish executable commands for the simulator and neutral host test roots.
Run them plus existing backend regression tests and both shared repository
checks. Preserve the dependency guard; a composing test is not an exception.

Show one host-level execution using a Draft created through the normal setup
service and a negative attempt using BLOCKED input.
No visible execution claim is made until T022 wires the controls.

## Scope limits

No PV/load/battery controller world, source envelopes, Commit or analytics.
No generated public observations yet.
Do not move the kernel into the backend or weaken the scanned-tree guard.
The reconciliation panel can still inspect declarations until T022 replaces it.

## Review

The owner reviews the independent calculation and causal mutations as evidence
for the forthcoming Lab screen. The Reviewer checks composition and numeric
policy before accepting generated trace fixtures.
Review outcome: pending.
