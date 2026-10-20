# W4-02 — Mini-grid depth

Status: planned; Architect spec-review closure recorded 2026-10-20; independent re-review and owner wave-start gate still required. Lane A, step 2; size L, divided into seven reviewable units. Branch `task/W4-02-mini-grid-depth` after reviewed and merged W4-01/W3-01 shared DTO; reserved `0028` is unused. USER_REVIEW_REQUIRED: true at the W4 wave checkpoint after independent review. Architect contract: [W4-02 build spec](../.agent/W4-02-build-spec.md), especially its Review closure.

## Scope and dependency

Own precisely v69 `renewable`, `service`, `fuel`, `backup` for the mini-grid Site. `D-2026-10-20-post-w2-sequence` assigns `A-mini-breadth-rules`, `A-mini-breadth-projections`, `I-mini-breadth-store`, `D-mini-breadth-windows` and migration `0029`. Consume accepted S1 bindings/S2 evidence, selected S3 dispatch and the reviewed W3-01 shared provenance DTO. W4-03 owns scenarios, opportunity Finding and work decisions. W4-01 owns case identity. Never seed the mock's 42 kW, three-day opportunity, 200 L tank or backup success as facts.

## Observable exit

- Four Site Performance pages load from tenant/Site/window/knowledge-cutoff scoped, persisted selections. Each has an accepted-input replay supporting the claims available in its domain and a missing or contradictory replay with exact accepted evidence lineage and coverage. Fuel residual, witnessed-test history and general backup readiness stay explicitly unknown. Reload preserves the selected revision and status.
- Renewable distinguishes measured generation from accepted reported capability, pinned uncertainty and retained margin; recurrence counts only completely assessed eligible days. Productive-use and tariff examples remain unavailable until W4-03 supplies a reviewed scenario basis.
- Service shows observed delivered load per addressed load and refuses unserved energy or service success without a requested-service denominator. Fuel separates modelled consumption from measured generator power from the incomplete inventory bridge; absent delivery records do not mean zero. Backup requires an observed outage-to-critical-service chain; generator runtime is only operating evidence.
- All CTA destinations and unavailable states, 403/404/503 refusals, 1440/390 visual budgets, one migration head/downgrade, positive/missing fixture and named tests follow the build spec. Independent spec review and the owner wave-start scope/core-panel gate precede builder activation; this packet does not assert either gate passed.

## 2026-10-20 scope correction

W4-02 now owns `minigrid-roles-4`, the three typed mini-grid Foundation properties, registered KOBO publication v5/conversion, four dedicated recompute domains and worker, and per-hour immutable selections with one-to-five-day renewable composition. The mini pages use Site-local windows; the W1 overview and Dispatch keep their existing UTC-day contracts. Build in the seven units named in the build-spec closure, with reviewed registry panel paths before activation.

W4-01 OperationalRecords remain SUBMITTED authored statements, not accepted telemetry. W4-02 cannot establish complete deliveries, fuel residual, accepted witnessed-test history or general backup readiness. Keep their mock positions with explicit gap copy and null values. A positive replay proves bounded expected generator use and an accepted observed outage chain where present; it does not claim those unavailable outcomes. Existing roles-3 Sites remain readable with missing-role limits. Any future use of W4-01 records as accepted inputs needs an Architect versioned amendment to W4-01 before implementation.

## Review

Review each commit against the build spec; run its focused Postgres and frontend tests, then one same-revision full backend suite and architecture/workflow/rule-8/navigation/registry guards for the slice. Capture desktop and 390 px app-vs-mock positive and missing states. Owner sees the reviewed result at W4 checkpoint. No private Lab truth or mock-only number enters a public claim.
