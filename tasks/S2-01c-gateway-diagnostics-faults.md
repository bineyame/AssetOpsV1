# S2-01c — Gateway diagnostics and fault scenarios

Status: outline; refine after S2-01b review, before activation
USER_REVIEW_REQUIRED: false
Milestone: S2 Evidence
Depends on: S2-01b
Branch: task/S2-01c-gateway-diagnostics-faults
Architect cut: `D-2026-10-07-s2-edge-split-and-demo-source`

## Visible result

Lab gateway-status shows locally persisted diagnostics pending upload, queue age/depth, last device contact, clock offset and disk pressure. A repeatable disconnect/reconnect and disk-pressure run leaves undelivered envelopes queued and visible after restart. Site Health cannot yet use these facts until S2-02 stores centrally received diagnostics.

## Contract and acceptance

Use `GatewayDiagnosticsV1` and the local diagnostic sequence from the technical design. Reports remain operational diagnostics, never AcceptedEvidence or a healthy-device assertion. Produce `I-edge-fault-scenarios` from the agreed scenario manifest; demonstrate that the same sealed batch bytes remain retryable after reconnection and that disk pressure visibly stops acquisition. S2-02 proves actual authenticated upload, receipts and exact-byte network retry. Per-batch signatures and key rotation are deferred by `A-edge-batch-signature`.

Reviewer inspects local state before and after restart and verifies no private Lab cause/oracle enters the diagnostic or envelope. This closes `I-edge-diagnostics-publish`, `I-edge-fault-scenarios` and `I-S2-01c` together. S2-02 owns authenticated central receipt, Postgres diagnostics, batch dispositions and the owner evidence checkpoint.

Refine after S2-01b review: use its actual persistent queue states and selected registered basis, then pin diagnostic cadence/limits, fault fixture and restart inspection. Local reports remain pending until S2-02 authenticates central upload. `queue_baseline_nodes` ownership remains `I-edge-diagnostics-publish`, `I-edge-fault-scenarios`, `I-S2-01c`; no baseline move from S1.

S2-01b makes registered Stage and Batch V2 bytes durable but does not deliver them. At activation, base the outage/reconnect fixture and local diagnostic queue counters on its actual SQLite states; keep any `IN_FLIGHT` restart retry byte-identical and do not show a central receipt before S2-02.
