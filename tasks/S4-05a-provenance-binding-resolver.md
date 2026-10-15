# S4-05a — immutable source binding and resolver

Status: implementation-ready. Size M, two phases. USER_REVIEW_REQUIRED: false — no UI; mergeable after fresh independent review. The source-state contract and owner-visible copy proposal are presented at S4-05b's owner checkpoint. Branch `task/S4-05a-provenance-binding-resolver` from reviewed main. Coordinator commits the plan.

Depends on merged S2-02, S4-01, S4-02b and resolved `A-S2-evidence`, `A-actor-identity`. Implements registry `I-S4-05a`; shared contract and authority in [S4-05](S4-05-stored-demo-provenance.md). Independent of unmerged LR-01/S5-01/S6-01; re-check merged head before coding.

## Phase 1 — admission authority and immutable binding

Extend **existing** `backend/assetops_backend/evidence/adapters/postgres_evidence_ledger.py:202-307`; no ninth writer. Add migration from the actual single head (main currently `0013_schedule_state`; LR-01 may require renumber to 0016). Prefer separate insert-only `evidence_publication` and scoped `batch_publication_link` rows; both have UUID and tenant/Site scoped FKs, unique publication identity/exact commitment and database triggers prohibiting UPDATE/DELETE. If instead adding `ingestion_batch.publication_id`, set it only on batch INSERT and use a **column-specific** DB trigger/guard to forbid later addition/change: ledger `decide_chunk` updates the batch at `backend/assetops_backend/evidence/adapters/postgres_evidence_ledger.py:285-296`. A table-wide UPDATE ban would break admission. Migration owns DDL.

Implement the shared pre-admission SYSTEM authority/lock/refusal contract in S4-05. Simulator registration must verify the server-recorded run identity/digest and the exact produced Batch V2, not merely a private manifest; authored registration verifies fixture/spec version and payload. Keep private scenario truth out of product evidence. Add server-side command, no public route. Extend rule 8 at `tools/checks/configuration-persistence.ps1:621-625,678-704,828-840` so **only** ledger INSERT into publication/link rows is allowed; reject ledger/other UPDATE, DELETE, TRUNCATE, upsert and DDL there, reject other-writer INSERT and client-route designation. Preserve all existing writer allowlists, reverse ownership and driver/write non-vacuity, including independently merged Action writer. Test direct-SQL immutability, uniqueness and scoped FKs.

Focused real-Postgres proof: two tenants/same Site code; wrong Site/gateway/source/digest; client/gateway/`SIMULATED`/`LIVE`/manifest-only refusals; authored and run positive proof; identical retry/conflicting reuse; after-partial-admission refusal; registration/upload race on same lock; mismatched publication commitment fails upload; chunk restart; duplicate original accepted ID, rejected/conflict none; DB mutation and guard probes. Measure added `open_batch` advisory-lock latency/cost against unbound baseline under the phase-1 test workload and report sample size, median/p95 and contention observation. Independent phase review.

## Phase 2 — scoped exact-revision resolver

Implement one tenant/Site-scoped resolver for accepted IDs and the S4-05 truth table, returning exact per-ID provenance, all publication/run IDs, problematic IDs and typed reasons. Resolve selected FindingRevision evidence from `backend/assetops_backend/analytics/finding_read.py:350,446` and consequence power IDs from `backend/assetops_backend/financials/consequence_read.py:87,149`; keep the resolver usable without changing these public DTOs until S4-05b. Test two publications same fixture/version, differing version, one run, compatible/incompatible multiple runs, class crossing, bound/unbound mix, empty set, foreign/missing/broken link with UNKNOWN precedence, and consequence-only mixed power. Verify selected historical revision, not current head. Independent phase review; hand exact resolver fixture/field contract to S4-05b.

Run focused checks and rule 8 guard; final full suite is owned by S4-05b after UI integration. Keep unbound current reads cautious at the S4-05b cutover; no retroactive binding.

## Coordinator note after plan re-review (`.agent/S4-05-plan-rereview.md`)

- N-M1 fixed: USER_REVIEW_REQUIRED set false (no UI; S6-01a precedent); copy proposal moves to S4-05b.
- N-L1 (implementer carry): anchor simulator registration on the registered commit/release path (`simulator_lab_api.py` ~3278-3283, `runs/execution_ports.py:178` `release_registered`), checking and registering each sealed batch against the run's committed stage before it moves to READY; one run can produce several batches (gateway `_fit` splits by size).
- N-L2 (implementer carry): until a compatible-run-basis contract exists, several run IDs in one set resolve to `MIXED`.
- N-L3: the S5-01 amendment is due before the merge of whichever of S4-05b/S5-01 merges second (not before coding).
- Residual risk: if the binding lives on `ingestion_batch`, reconcile the existing `ON CONFLICT DO NOTHING` batch insert with rule 8's upsert rejection explicitly.

