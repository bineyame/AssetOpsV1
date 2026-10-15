# S4-07 — evidence decision time at the scheduled cutoff

Status: implementation-ready
Size: S; one build and one fresh independent review
Branch when activated: `task/S4-07-evidence-decided-at`, from merged main
USER_REVIEW_REQUIRED: false (non-UI; no owner-facing copy or visual change)
Owner: evidence/ingestion; S4-02d I3 carry, not a schedule-writer expansion

## Outcome and authority

A late accepted decision is either visible to the scheduled S3 DB-time knowledge cutoff or leaves durable work for a later tick. Close `.ai/MILESTONE_REVIEW_BACKLOG.md` “S4-02d carries” I3 and `.agent/S4-02d-phase-2-review.md` F-A's evidence-owner residual. Preserve the `S3_STALE_NO_JOB` alarm and operator requeue until this is independently proved. Independent of unmerged LR-01/S5-01/S6-01/S4-05.

## Code reality and boundary

- `backend/assetops_backend/evidence/ledger_service.py:174-184` passes `self.clock()` to each chunk before the ledger transaction. `backend/assetops_backend/evidence/adapters/postgres_evidence_ledger.py:249-306` owns the transaction, writes accepted rows/dispositions and coalesces a recompute job; this is the writer to change.
- `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py:50-54` selects ACCEPTED dispositions only when `d.decided_at <= :k`. Scheduled stages use DB time; the cutover read and F-A reproduction are in `backend/tests/test_s4_schedule_health_postgres.py:386` onward. `backend/README-db.md:128-135,204` documents the residual/alarm/requeue.
- Rule 8 keeps the evidence ledger writer on its tables and the assessment writer on S3 jobs (`tools/checks/configuration-persistence.ps1:680-757`). Keep those paths and table ownership; do not add schedule-table writes to evidence code. No migration expected; re-chain any added migration from then-merged head (main 0013; unmerged LR-01 0014/0015; S6-01a/S4-05a may add more).

## Build and acceptance

1. Choose an evidence-owned transactional fix: stamp each newly decided chunk at DB time inside its write transaction and ensure coalescing cannot lose a decision whose commit occurs after a worker's cutoff/read, or durably enqueue an additional job for that case. Use a committed decision's DB-visible order as the invariant; simply changing the Python clock source before the transaction is insufficient. Preserve receipt times, duplicate/rejected semantics, exact accepted identity, Site isolation and idempotent chunk retry.
2. Real-Postgres race proof holds a pending/leased S3 job and a scheduled worker at its DB cutoff, then commits an overlapping late evidence chunk with a deliberately fast and slow app clock. The next tick must either include that accepted ID in the run at a cutoff at or after its decision, or find durable live work that makes the window non-CURRENT until a later run includes it. Assert the disposition time, job state, run cutoff, selection sequence and read status; no `STALE_NO_JOB` terminal gap.
3. Crash/restart after the evidence transaction and before the next tick; replay the same batch and run ticks. Assert one accepted record, no lost job, eventual current assessment citing the ID, and no falsely CURRENT intermediate read. Check a chunk spanning two default windows, a duplicate-only chunk, and a different Site. Keep the documented alarm as defense in depth and update `backend/README-db.md` to state the remaining recovery condition accurately.

Focused checks: `backend/tests/test_s2_evidence_ledger_postgres.py`, `test_s3_dispatch_assessment_postgres.py`, `test_s4_schedule_health_postgres.py`, plus the new race/restart case and `tools/check-all.ps1`. On final revision run one real-Postgres full backend suite per `backend/TESTING.md` with JUnit zero skipped/failed, keep-awake and 20-minute cap. Give the reviewer same-revision evidence. No UI checkpoint.

## Architect questions

If a transactionally safe DB-time stamp still permits a worker snapshot to miss a later commit whose timestamp precedes its cutoff, recommend evidence-owned durable re-enqueue through the existing recompute-job contract, with any assessment-writer API change explicit in review. The invariant above is mandatory whichever mechanism is chosen; no new schedule-table writer is authorized.
