# T026 - Dispatch-capable evidence

Status: planned
USER_REVIEW_REQUIRED: true

Map: B extension beyond initial fuel staging.
Depends on: T023 and completed A in T025.
Next: T027.
Branch: task/T026-dispatch-capable-evidence
Sizing: publication/gateway boundary extension.

## Outcome

Inspect staged PV, BMS, generator, meter and time-valid policy evidence for the
healthy and prolonged-runtime worlds, including one reporting gap and one
delayed publication.

This closes the evidence C actually needs to assess capability and operating
constraints. It deliberately stops short of gateway-failure realism.

## Thinned on purpose

This slice was `Dispatch-capable evidence and gateway recovery` and carried the
full outage, buffering, recovery, retry, duplicate, out-of-order,
buffer-exhaustion and noise/bias set. `Docs/queue-review-feedback-verbatim.md`
asked for exactly the evidence the first Finding needs and no more, because
gateway recovery proves architecture rather than product value.
T026A owns the deferred behavior; see `D-2026-09-24-queue-resequenced-for-demo`.

Do not re-expand this slice. If the publication path built in T023 already
makes an outage/recovery case nearly free, include it and report that T026A
shrank by that much. Building buffering in order to demonstrate it is the thing
this thinning refuses.

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
4. Introduce the first operational-record source family here, narrowly:
   operator-commanded override/command records carrying identity, occurrence
   and effective time and actor/source provenance, with their own missing and
   delayed cases. They are not telemetry and do not inherit its cadence or
   interval semantics. T028 needs both the present and the absent override
   case, so this family cannot wait for T030, which extends it with delivery
   and hand-dip records.
   An absent override record never establishes that no override occurred.
5. Measurements retain StateRef/device/signal mapping and appropriate interval
   semantics. Strict unit, type and schema validation covers each new family.
6. Carry exactly two evidence imperfections: normal cadence with one reporting
   gap, and one delayed publication. That is enough for C to show a bounded,
   coverage-limited claim. Numeric bias/noise is T026A.
7. Source time and gateway/publication time are separate fields that the
   delayed case makes visibly differ. No ingestion received_at exists in stage
   content; T027 assigns it.
8. A discrete generator status is carried as an enum and is never numerically
   noised. Dropout, stale and duplicate handling for it is T026A.
9. Exact canonical payloads and mapping/profile versions survive persistence.
   T023's retry, conflicting-identity and corrupt-artifact rules still hold and
   are not re-proved here.
10. The inspector distinguishes a sensor gap from a publication delay, so C's
    evidence gaps trace to accepted inputs. Broad publication-quality display
    is T026A.
11. Healthy, prolonged-runtime and degraded-evidence runs stage reconstructible
    dispatch datasets. Private recipe labels/oracles stay outside payloads.
12. Expanding the allowlist preserves strict refusal of arbitrary world/trace
    content and leaves Site accepted history unchanged.

## Proof

Run one healthy and one prolonged-runtime Draft through the full publication
profile. Record which C-required signals are present, their units and coverage.
Repeat with a discharge-capability gap and a missing override record.

| Fault | Expected stage |
| --- | --- |
| Sensor dropout | No fresh reading |
| Delayed publication | Original source time, later publication time |
| Missing capability | No private-state replacement |
| Missing override record | None observed, not absence of override |
| Policy effective at boundary | Correct version/effective time preserved |

Prove that the gap and the delay change reporting/publication only, with an
identical world trajectory and identical controller decisions under the same
physical inputs.
Run simulator/host, strict envelope and inspector tests, shared checks and
layout evidence where the new evidence inspector changes layout.

## Scope limits

Commit and ingestion receipt time remain T027.
Gateway outage, buffering, recovery, retry, duplicate and out-of-order release,
buffer exhaustion and numeric bias/noise are T026A.
The operational family stays at override/command records here; fuel delivery
and hand-dip records and their completeness rules are T030.
Full Replay and broad source-health UI remain deferred as recorded in README.
This is still stage inspection, not an operator dispatch conclusion.

## Review

The owner follows one sample through the delayed case and identifies the two
timestamps. The Reviewer checks that C's required evidence has real owners and
that nothing from T026A was smuggled back in.
Review outcome: pending.
