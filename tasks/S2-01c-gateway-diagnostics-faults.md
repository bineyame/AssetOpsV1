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

Consume the publication-delay carry in `D-2026-10-08-s2-simulated-device-resolution-and-delay-boundary`: S2-01b refuses registered delay-window runs and stages no affected report early. Add a repeatable registered delay-window fixture and deferred local admission at the declared release, preserving the original reading and `source_time`, recording `published_at` at release/sealing, and retaining the same message identity and sealed bytes on retry/restart. Inspect queued versus released counts and lag locally; S2-02 owns server receipt and Site Evidence display of source/published/received times. Keep delay cause/private scenario data out of V3/Batch V2.

The S2-01b delay test injects a frozen window through a host override; it proves only that the refusal fails closed. This slice must make a delay-capable publication profile selectable for a registered Draft and prove an actual run's delayed report is absent before release, admitted after release, and stable after restart. Do not count the injected S2-01b regression as this acceptance proof.

Consume `D-2026-10-09-s2-gateway-sealing-state-and-partial-progress`: local queue/diagnostic views distinguish sealed pending batches, admitted but unbatched envelopes, report holds (including `UNBATCHABLE`) and active `SEALING_REFUSED` groups after restart. A sealed batch in another source group remains durable even when one group is stuck; neither that partial progress nor a cleared active refusal implies a central receipt or a healthy source.
