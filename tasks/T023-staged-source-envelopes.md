# T023 - Persist and inspect canonical staged source envelopes

Status: planned
USER_REVIEW_REQUIRED: true

Map: B preparation; does not complete A or B.
Depends on: T022.
Next: T024-T025 complete A; T026 extends the dispatch evidence path.
Branch: task/T023-staged-source-envelopes
Sizing: first canonical evidence boundary, staging only.

## Outcome

Run the Fuel Loss Draft and inspect its exact persisted canonical source
envelopes in Lab. Reload the stage without live world objects and see source
mapping, identity, payload, quality and source/publication times.

This establishes the sole future product crossing. Commit and ingestion remain
T027, after the electrical world and dispatch-capable gateway are present.

The inspector stays deliberately utilitarian. Its whole value is that an
engineer can see exactly what is about to cross the boundary. It is not a
source-envelope debugging application, and polish spent on it is polish taken
from the first Finding. `Docs/queue-review-feedback-verbatim.md` says so.

## Read for detail

- v4 sections 3, 6, 11, 21 and 25.
- Starter handoff: Staging and Contract Versions.
- .ai/ARCHITECTURE.md: Evidence Loop Boundaries.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Define a strict, versioned canonical SourceEnvelope in dependency-neutral
contracts. The gateway converts generated observations to this public contract
through explicit allowlisted mappings; it never serializes a private object
graph as an envelope payload.

Persist immutable, reloadable stage content with enough frozen mapping and
profile provenance to reconstruct what was published.
Expose it through the gated Lab stage inspector.

The initial fuel allowlist is intentionally small.
T026 owns PV/BMS/generator/meter/policy extension, faults and recovery.
T030 owns operational fuel delivery/dip completeness.

## Acceptance criteria

1. Every staged envelope carries Site/source/device/signal identity, mapping
   version, schema version, message/sequence identity, value/unit or typed
   unavailable/quality semantics and source/publication timestamps.
2. Source time remains the observation's sample/interval time.
   Gateway/publication time describes publication; received_at is absent.
3. Stock versus interval measurement semantics survive conversion, including
   the interval being summarized where applicable.
4. The strict schema rejects unknown/private payload fields, invalid identity,
   incompatible unit/mapping and malformed timing before they become a stage.
5. Private cause, event/oracle labels, true stock, ControlIntent, AcceptedFlowSet,
   raw observation objects and LabProjection cannot be accepted as envelopes.
6. Mappings resolve from frozen configuration/profile content; changing a
   current mapping cannot reinterpret already-staged envelopes.
7. Message identities are stable across retry of the same publication.
   Same identity/content is idempotent; same identity/different content yields
   an explicit conflict rather than an overwrite.
8. Canonical serialized content round-trips losslessly through stage persistence
   and the strict parser. Integrity failure is visible and blocks release eligibility.
9. A partial write leaves no apparently complete artifact.
   Reloaded content matches what the inspector presents as releasable.
10. A gap in device sampling yields no invented telemetry value.
    Stale/quality information remains explicit where the profile publishes it.
11. The inspector shows exact payload and separately readable metadata,
    including mapping version and source versus publication time.
12. The stage remains accessible after the live execution handle is gone,
    behind the Lab gate. Its immutable records cannot be edited in the inspector.
13. Draft staging makes no accepted Site-history, Evidence or Finding write.
    Normal operator routes cannot treat stage content as accepted evidence.
14. Envelope schema versioning is independent from execution-contract versions.
    Record the new schema and strict compatibility/refusal behavior.
15. Backend and simulator consume the neutral schema without cross-importing.
    The neutral host composes execution and staging without a dependency reversal.

## Proof

| Case | Required result |
| --- | --- |
| Generated fuel sample | Canonical mapped envelope with original source time |
| Reload stage without runtime | Same exact canonical payload |
| Retry publication | Same message/content, no duplicate staged fact |
| Same id with changed payload | Explicit conflict |
| Inject private truth/unknown field | Strict boundary rejection |
| Change current mapping | Existing stage unchanged |
| Missing sample | No fabricated value |
| Truncated/corrupt persisted content | Inspection error, not valid stage |
| Stage a complete Draft | Accepted history unchanged |
| Disable Lab | Stage inspector/API inaccessible |

Use both a schema-level negative corpus and one host-to-Lab demonstration.
A privacy test should attempt to smuggle private data, not just search the
happy-path payload for a known field name.

Run simulator/host, envelope/parser and frontend inspector tests, shared checks
and layout evidence with populated payload content.

## Scope limits

No Commit, received_at, ingestion receipt or operator Site metric yet.
A fuel-only stage is not the architecture-demo milestone.
Do not build a second envelope type owned by the backend or a general message
bus. Keep the persisted source contract suitable for normal ingestion in T027.

## Review

The owner inspects source versus publication time and reloads the exact payload.
The Reviewer verifies strictness, immutability and truth isolation.
Review outcome: pending.
