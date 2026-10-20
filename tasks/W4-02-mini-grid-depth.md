# W4-02 — Mini-grid depth

Status: planned; build spec pending. Lane A, step 2; size L, divided into reviewable one-run commits. Branch `task/W4-02-mini-grid-depth` after reviewed W4-01 and migration `0028` disposition. USER_REVIEW_REQUIRED: true at the W4 wave checkpoint after independent review. Architect contract: [W4-02 build spec](../.agent/W4-02-build-spec.md).

## Scope and dependency

Own precisely v69 `renewable`, `service`, `fuel`, `backup` for the mini-grid Site. `D-2026-10-20-post-w2-sequence` assigns `A-mini-breadth-rules`, `A-mini-breadth-projections`, `I-mini-breadth-store`, `D-mini-breadth-windows` and migration `0029`. Consume accepted S1 bindings/S2 evidence, selected S3 dispatch and the reviewed W3-01 shared provenance DTO. W4-03 owns scenarios, opportunity Finding and work decisions. W4-01 owns case identity. Never seed the mock's 42 kW, three-day opportunity, 200 L tank or backup success as facts.

## Observable exit

- Four Site Performance pages load from tenant/Site/window/knowledge-cutoff scoped, persisted selections. Each has a supported replay and a missing or contradictory replay with exact accepted evidence lineage and coverage. Reload preserves the selected revision and status.
- Renewable distinguishes measured generation from configured capability, protected reserve and unmet service; recurrence counts only completely assessed eligible days. Productive-use and tariff examples remain labelled illustrative until W4-03.
- Service shows observed delivered load per addressed load and refuses unserved energy or service success without a requested-service denominator. Fuel separates modelled dispatch consumption from a complete inventory bridge; absent delivery records do not mean zero. Backup requires a witnessed outage-to-critical-service chain; generator runtime is only operating evidence.
- All CTA destinations and unavailable states, 403/404/503 refusals, 1440/390 visual budgets, one migration head/downgrade, positive/missing fixture and named tests follow the build spec. Independent spec review and the owner wave-start scope/core-panel gate precede builder activation; this packet does not assert either gate passed.

## Review

Review each commit against the build spec; run its focused Postgres and frontend tests, then one same-revision full backend suite and architecture/workflow/rule-8/navigation/registry guards for the slice. Capture desktop and 390 px app-vs-mock positive and missing states. Owner sees the reviewed result at W4 checkpoint. No private Lab truth or mock-only number enters a public claim.
