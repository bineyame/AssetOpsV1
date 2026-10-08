# S2-01b — Durable simulated gateway

Status: outline; refine after S2-01a review, before activation
USER_REVIEW_REQUIRED: false
Milestone: S2 Evidence
Depends on: S2-01a
Branch: task/S2-01b-durable-simulated-gateway
Architect cut: `D-2026-10-07-s2-edge-split-and-demo-source`

## Visible result

Lab shows a sealed Kobo SourceEnvelope V3 and queued Batch V2 from simulated public reports. Exact sequence, message ID and bytes survive gateway restart; a second reading at the same source timestamp has a different identity. Upload remains pending until S2-02.

## Contract and acceptance

Run the gateway as a separate process with SQLite WAL mapping snapshot, source-scoped sequence/epoch allocation, append-only envelope outbox, homogeneous sealed batch bytes, retry state and receipt slots. Use the simulated report adapter behind the common typed adapter interface. Registered snapshot provenance is carried from S2-01a. The source in effect for this demo is **simulated only**: no physical protocol parser or captured-device equivalence is claimed. The first real pilot decides whether its physical peer is a real capture or a labelled vendor-format wire fixture.

Reviewer stages a run, stops after SQLite enqueue, restarts, and checks byte/ID stability, mapping-version batch split and explicit pending state. Unknown channel and incompatible unit have inspectable refusal/hold behavior. This closes `I-edge-outbox`, `I-edge-simulated-adapter` and `I-S2-01b` together. S2-01c adds diagnostics and fault scenarios; S2-02 owns authenticated delivery and server decisions.

S1 carry to consume at refinement: S1 snapshot download is development-tenant scoped, not gateway authenticated; S2-01b must define how the separate process obtains the immutable selected basis while S2-02 owns registered TLS upload credentials. S2-01a run basis and public report shape are the input, never a new YAML read. Refine exact process API, snapshot transfer/authentication, V3 test vectors, SQLite crash/retry fixtures and Lab queue read before activation. `queue_baseline_nodes` ownership remains `I-edge-outbox`, `I-edge-simulated-adapter`, `I-S2-01b`; no baseline move from S1.
