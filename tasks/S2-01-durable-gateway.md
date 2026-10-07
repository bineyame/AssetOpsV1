# S2-01 - Durable edge gateway and Lab inspection

Status: outline; refine after S1-02 review, before activation
USER_REVIEW_REQUIRED: true
Milestone: S2 Evidence
Depends on: S1-02
Branch: task/S2-01-durable-gateway
Planner: Codex, 2026-10-07; contract audit 2026-10-07

## Visible outcome

Lab gateway-status/Commit detail shows sealed SourceEnvelopes, queue depth, mapping basis and delivery state that survive process restart. This is a local acquisition result; central acceptance becomes visible in S2-02.

## Current code and required transition

`simulator/assetops_simulator/gateway/publish.py` and `mappings.py` are an in-process simulated publisher, not the target separate edge process. Adapt their device-report boundary without allowing private world state into the gateway. Add one captured physical-device adapter fixture and a simulated-device adapter behind the same gateway interface. The old Stage files remain comparison artifacts, not the gateway queue.

## Persisted object and wire contract

The separate gateway process uses SQLite WAL with registered identity/mapping snapshot, one transaction for source-scoped epoch/sequence allocation and canonical outbox write, homogeneous sealed upload batches, retry state, durable receipt slots, dead-letter state and inspectable minimal diagnostics. Reboot keeps the exact message IDs, envelope bytes and batch bytes; an outage never reports delivery. S1-02 supplies a signed versioned snapshot.

Define and fixture SourceEnvelope V3 identity from persisted `(site,gateway,source,epoch,sequence)`, plus IngestionBatch V2 and BatchReceipt V2 bytes/hash/ordinal rules from the technical design. Two readings at the same source timestamp must have different IDs. Keep v1/v2 envelope and v1 batch parsers for historical replay; do not mutate their identities. S2-02 owns authenticated delivery and server-issued decisions, so S2-01 must not invent an accepted receipt.

## Demo acceptance

Stage a simulated run, inspect sealed envelopes, stop after SQLite enqueue, restart, and see exact IDs/bytes and queue state. Change Foundation/binding snapshot while offline and see a new homogeneous batch without rewriting the old one. Parse a captured physical-device report through the same interface. A local retry can show pending/in-flight state; S2-02 will exercise the actual HTTPS receipt.

## Missing/conflicting evidence

Unknown channel, incompatible unit or unavailable report is held/refused or represented explicitly as the contract allows. Outage and disk pressure remain visible; no unacknowledged evidence is silently dropped.

## Evidence lineage

From Lab queue row resolve sequence epoch, snapshot version/hash and canonical SourceEnvelope digest. S2-02 will link this to its accepted ID and durable server disposition.

## Review and refinement

Reviewer opens gateway-status/Commit detail, verifies SQLite reload and the wire fixtures, and checks that gateway code cannot read Lab world/oracle data. Before activation, refine exact adapter fixture, process seam and focused crash tests using S1-02 outcome. Apply shared queue gates.

## Defer

Detailed retention/backpressure policy, additional protocols, broker transport and generic edge analytics.
