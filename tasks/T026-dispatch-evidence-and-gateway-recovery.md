# T026 - Dispatch-capable evidence and gateway recovery

Status: planned
USER_REVIEW_REQUIRED: true

Map: B extension beyond initial fuel staging.
Depends on: T023 and completed A in T025.
Next: T027.
Branch: task/T026-dispatch-evidence-and-gateway-recovery
Sizing: publication/gateway boundary extension.

## Outcome

Inspect staged PV, BMS, generator, meter and time-valid policy evidence for the
healthy and prolonged-runtime worlds. Introduce a gateway outage and inspect
buffered recovery, preserved source times and later publication times.

This closes B's evidence contract before ingestion and supplies the evidence
C needs to assess capability and operating constraints.

## Read for detail

- v4 sections 3, 6, 11-12, 17 and 25.
- Roadmap sections 3.2-3.3 and 7/B-C.
- FEATURE_MAP B's dispatch evidence extension.
- Shared checks and exclusions: tasks/README.md.

## Deliver and acceptance

1. Extend the neutral envelope schema, publication profiles and frozen mappings
   for PV output/available capability, BMS SOC/power/discharge capability,
   generator status/power, load/service meter signals and policy records.
2. Distinguish observed output from available capability. Where a profile cannot
   report capability, leave it unavailable; C must not infer it from private
   PV potential or AcceptedFlowSet.
3. Policy evidence identifies version, effective interval and source.
   Component and Site Controls resolve to the operating time they govern.
4. Operator-commanded override records, when present, use the operational
   record family. Their absence does not establish that no override occurred.
5. Measurements retain StateRef/device/signal mapping and appropriate interval
   semantics. Strict unit, type and schema validation covers each new family.
6. Demonstrate cadence, a reporting gap and at least one biased/noisy numeric
   signal separately from gateway faults.
7. Gateway outage buffers eligible reports without changing physics or original
   source times; recovery releases according to the declared profile.
8. Retry and duplicate publication preserve message/content identity.
   Delayed and out-of-order release preserve individual source times.
9. Buffer exhaustion or configured loss is explicit and yields a gap; recovery
   cannot synthesize observations that were never sampled or retained.
10. Gateway/publication timestamps reflect release behavior and remain distinct
    from source time. No ingestion received_at exists in stage content.
11. A discrete generator status supports timing/dropout/stale/duplicate behavior
    without numeric noise being applied to its enum.
12. Exact canonical payloads and mapping/profile versions survive persistence.
    Retry, conflicting identity and corrupt artifact rules from T023 remain.
13. The inspector distinguishes sensor gap, gateway delay and publication
    quality so C's later evidence gaps can be traced to accepted inputs.
14. Healthy, prolonged-runtime and degraded-evidence runs stage reconstructible
    dispatch datasets. Private recipe labels/oracles stay outside payloads.
15. Expanding the allowlist preserves strict refusal of arbitrary world/trace
    content and leaves Site accepted history unchanged.

## Proof

Run one healthy and one prolonged-runtime Draft through the full publication
profile. Record which C-required signals are present, their units and coverage.
Repeat with a discharge-capability gap and missing override record.

| Fault | Expected stage |
| --- | --- |
| Sensor dropout | No fresh reading |
| Gateway outage/recovery | Original source time, later publication time |
| Retry/duplicate | Same message/content identity |
| Delayed/out-of-order release | Source ordering reconstructible |
| Buffer loss | Explicit missing interval, no backfilled measurement |
| Missing capability | No private-state replacement |
| Policy effective at boundary | Correct version/effective time preserved |

Prove that each fault changes reporting/publication only, with identical world
trajectory and controller decisions under the same physical inputs.
Run simulator/host, strict envelope and inspector tests, shared checks and
layout evidence where the new evidence inspector changes layout.

## Scope limits

Commit and ingestion receipt time remain T027.
Fuel delivery/dip records are T030.
Full Replay and broad source-health UI remain deferred as recorded in README.
This is still stage inspection, not an operator dispatch conclusion.

## Review

The owner follows a sample through outage/recovery and identifies the two
timestamps. The Reviewer checks that C's required evidence has real owners.
Review outcome: pending.
