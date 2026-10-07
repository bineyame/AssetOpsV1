# S2-01 — Durable gateway and Lab inspection

Status: outline; refine after preceding task review, before activation
USER_REVIEW_REQUIRED: true
Milestone: S2 Evidence
Depends on: S1-02
Branch: task/S2-01-durable-gateway
Planner: Codex, 2026-10-07

## Visible outcome

Lab gateway-status/Commit detail shows sealed envelopes, queue depth and delivery state after restart.

## Persisted object and read contract

Edge SQLite sequence_state, canonical outbox envelope, homogeneous upload batch and durable receipt state; one captured physical-device adapter shape and simulated adapter share the gateway interface.

## Demo acceptance

Stage a simulated run, inspect sealed envelopes, kill/restart after enqueue, reconnect and see exact IDs/bytes and queue state; parse a captured physical-device fixture through the same gateway contract.

## Missing/conflicting evidence

Unknown channel or invalid mapping is held/rejected visibly; outage remains queued, not silently delivered.

## Evidence lineage

From Lab queue row resolve sequence, snapshot version and canonical SourceEnvelope digest; S2-02 will link its accepted ID.

## Review and refinement

Reviewer opens the selected-window surface and read API, verifies storage/reload and the state above, and follows lineage. Apply shared gates in the current task queue. Before implementation, refine exact fixture, wire/API fields, migration seam and focused checks using the reviewed predecessor and accepted architecture/technical design. This outline is not permission to change those contracts.

## Defer

Detailed retention/backpressure, extra protocols and broker transport.
