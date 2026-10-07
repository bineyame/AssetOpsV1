# S2-01c — Gateway diagnostics and fault scenarios

Status: outline; refine after S2-01b review, before activation
USER_REVIEW_REQUIRED: false
Milestone: S2 Evidence
Depends on: S2-01b
Branch: task/S2-01c-gateway-diagnostics-faults
Architect cut: `D-2026-10-07-s2-edge-split-and-demo-source`

## Visible result

Lab gateway-status shows locally persisted heartbeat/diagnostic publication, queue age/depth, last device contact, clock offset and disk pressure. A repeatable disconnect/reconnect and disk-pressure run leaves undelivered envelopes queued and visible after restart. Site Health cannot yet use these facts until S2-02 stores centrally received diagnostics.

## Contract and acceptance

Use `GatewayDiagnosticsV1` and the local diagnostic sequence from the technical design. Reports remain operational diagnostics, never AcceptedEvidence or a healthy-device assertion. Produce `I-edge-fault-scenarios` from the agreed scenario manifest; demonstrate retry of the same sealed batch bytes after reconnection and stop acquisition visibly on disk pressure rather than silently discarding evidence. The S2 pilot uses registered TLS credentials and canonical payload SHA-256; per-batch signatures and key rotation are deferred by `A-edge-batch-signature`.

Reviewer inspects local state before and after restart and verifies no private Lab cause/oracle enters the diagnostic or envelope. This closes `I-edge-diagnostics-publish`, `I-edge-fault-scenarios` and `I-S2-01c` together. S2-02 owns authenticated central receipt, Postgres diagnostics, batch dispositions and the owner evidence checkpoint.
