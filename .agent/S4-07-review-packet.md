# S4-07 review packet - evidence decided_at on DB time

Task: `tasks/S4-07-evidence-decided-at.md` (M; non-UI; USER_REVIEW_REQUIRED false). Branch `task/S4-07-evidence-decided-at` from `3ec3d765` (main `5bfff665` + activation). Build commits `aa56dfc6` (code + proofs), `f1e67a52` (docs, F-A skew); closeout commit follows. Diff: `git diff 3ec3d765..HEAD`.

## Outcome delivered

A late accepted decision is either inside a scheduled run's DB-time cutoff or carried by live S3 work for a later tick. Each chunk takes one DB `clock_timestamp()` after the batch row lock; it stamps `decided_at` and a newly inserted job's `available_at`/`created_at`. Coalescing alone was **not** sufficient: a scheduled worker samples its cutoff (`db_clock`) before the lease statement, so a widening committed between the two was consumed at a cutoff that excluded it. That interleaving failed on the production path before the fix (see Checks). The evidence-owned fix lifts a widened PENDING job's `available_at` to the decision instant.

## Files materially changed

- `backend/assetops_backend/evidence/adapters/postgres_evidence_ledger.py` - `_decision_instant` (DB time, or the test-only override); `decide_chunk(completed_at=)`; `_coalesce_job` widen sets `available_at = GREATEST(available_at, :now)`; module docstring.
- `backend/assetops_backend/evidence/ledger.py` - `decide_chunk` contract: `completed_at` (app-clock receipt), never a decision instant.
- `backend/assetops_backend/evidence/ledger_service.py` - passes `completed_at=self.clock()`.
- `backend/tests/test_s4_evidence_decided_at_postgres.py` (new) - race and restart proofs, production path.
- Fixtures moved to `test_decision_clock_override`: `test_s2_evidence_ledger_postgres.py`, `test_s2_site_evidence_postgres.py`, `test_s3_dispatch_assessment_postgres.py`, `test_s4_finding_store_postgres.py` (CaseRunner; covers finding history, schedule tick/health users), `test_s4_evidence_consequence_work_postgres.py`.
- `backend/tests/test_s4_schedule_health_postgres.py` - F-A test re-driven as override-path; skew 120 s.
- `backend/README-db.md` (I3 section, alarm row, manual Leg B note), `.ai/MILESTONE_REVIEW_BACKLOG.md` (I3 closeout).

## Acceptance criteria

1. DB decision clock + override - **met.** One instant per chunk after `SELECT ... FOR UPDATE` on the batch row, inside the chunk transaction (`clock_timestamp()`, not `now()`). Retry of a committed chunk returns early / processes only new ordinals, so stored dispositions keep their instants (asserted in the restart test). `received_at`/`completed_at` stay app clock (asserted equal to the app clock in every production-path test). Production composition (`evidence/composition.py:26`, `main.py`) constructs `PostgresEvidenceLedger(database_url)` with no override. Named fixtures moved; no other fixture asserted exact `decided_at` (full suite green).
2. Production-path race proof - **met**, fast (+2 h) and slow (-2 h) app clocks each: ingestion-first (tick passes the row-locked job; after commit J widened, `created_at` kept, `available_at` == decision; next tick cutoff >= decision cites the IDs); worker-first with the lease transaction held, ingestion proved waiting on the job row lock (`pg_stat_activity`), then inserting a new PENDING job with `available_at == created_at == decided_at` (L-b); the finished run's cutoff < decision and it excludes the IDs, the new job keeps the window non-CURRENT, next tick cites; cutoff-sampled-before-commit race (lease at the earlier cutoff takes nothing); tick passing an uncommitted new job. Each asserts the DB-bracketed decision instant != app clock, job status/window/timestamps, run cutoff, cited IDs and read state; `settle` refuses any CURRENT read missing the IDs.
3. Restart - **met.** Crash after chunk 1 (which crosses midnight: two day windows), no tick, replay the same bytes: one accepted row per message, chunk-1 dispositions unchanged, two DB instants, live job, both windows non-CURRENT until a tick cites all IDs. Duplicate-only batch: all DUPLICATE, job list unchanged. Site B (KOBO-002) crash/replay: own job, settles; Site A jobs and selection untouched. F-A test re-driven through `test_decision_clock_override`, labelled override-path; see Known Deviation 2.
4. Docs - **met.** README-db states DB-time decisions, the lift, app-clock receipt fields and L-a (no order between `completed_at` and last `decided_at`), the manual `process-jobs` residual (I3 not closed for manual CLIs; stop-the-tick rule kept), `recorded_at` out of scope. No migration.

## Checks run

- Pre-fix (code at DB-time stamping, without the lift): `test_s4_evidence_decided_at_postgres.py` 4 failed / 6 passed; the cutoff-sampled race failed both skews with `a lease at a cutoff before the decision consumed the widened job` (JobOutcome DONE). After the lift: 10 passed + F-A test passed.
- Focused (at `aa56dfc6`): S2 ledger + site evidence 39 passed; S3 dispatch, S4 finding store/history/consequence work/schedule tick/health 49 passed (`-n 2`); new file + F-A 11 passed.
- Mutations (each reverted with `git checkout`, tree clean after): M1 `decided_at = completed_at` (app clock) - cutoff-sampled test fails on the DB bracket; M2 lift removed - cutoff-sampled test fails (`consumed the widened job`); M3 `FOR UPDATE` dropped from the coalesce job select - worker-first test fails (`ingestion never waited on the leased job's row lock`).
- `tools/check-all.ps1`: all 9 guards passed (temporary `.venv` junction, removed).
- Full backend suite, final code revision `f1e67a52`: `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=30 --junitxml=.pytest-junit.xml`, keep-awake on, wall 708 s (cap 20 min); JUnit tests=2147 failures=0 errors=0 skipped=0. Closeout commit changes docs only. Run-owned DBs dropped (only base `assetops_test` remains); temporary `var/sites`, JUnit file removed.

## Known deviations

1. **Widened job `available_at` lifted.** The packet says a widened PENDING job retains its existing timestamps; it also requires an evidence-owned `recompute_job` fallback if an interleaving fails. One did (cutoff sampled, widening commits, lease at the earlier cutoff). The fix keeps `created_at` and lifts only `available_at` to `GREATEST(available_at, decision)` in the same transaction - the narrowest evidence-owned re-enqueue. No schedule-table or assessment-writer change; rule 8 accepts it.
2. **F-A alarm no longer reachable through ingestion.** With the lift, an override decision ahead of DB time leaves J PENDING (asserted: tick leaves it, no `S3_STALE_NO_JOB`). To keep the alarm/requeue assertions as defense in depth, the test then restores the pre-S4-07 widening by SQL (`available_at` back to J's original) and proceeds as before. Skew allowance raised 20 s -> 120 s (carry R-2).

## Residual risk

- Manual app-clock `process-jobs` beside the tick can mix clocks (documented; stop the tick first).
- `clock_timestamp()` vs `now()` is reasoned, not mutation-proved: no test contends the batch row lock.
- Under a continuous stream the widened job's due time follows the latest chunk; a lease only misses it when a chunk lands between its cutoff sample and lease (milliseconds), so starvation is theoretical but not measured.
- Configuration `recorded_at` vs `reconcile` unchanged (out of scope).

## User-review focus

None required (USER_REVIEW_REQUIRED false). Reviewer focus: Known Deviation 1 (accept or route to Architect) and whether the F-A SQL restoration is an acceptable override-path re-drive.
