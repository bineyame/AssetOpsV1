# S4-07 independent slice review - evidence decided_at on DB time

Reviewer: fresh Claude reviewer (did not author the slice). Worktree `AssetOpsV1-review4`, branch
`review/S4-07-slice` at S4-07 head `a7278bb2`. Diff reviewed `3ec3d765..a7278bb2`.
Inputs: `tasks/S4-07-evidence-decided-at.md` (incl. plan fix round 1, coordinator L-a/L-b),
`.agent/S4-07-review-packet.md`, `.agent/S4-07-handoff.md`, plan reviews, S4-02d F-A context.

## Verdict

**ACCEPT.** No High or Medium findings. Known Deviation 1 (the `available_at` lift) is correct, necessary and
sufficient for the scheduled path, and does not need an Architect ruling. Known Deviation 2 (F-A re-driven with a
SQL restoration) is an acceptable, honestly labelled override-path defense-in-depth test. Two Low notes below;
neither blocks merge.

## Focus 1 - Deviation 1: widened PENDING job `available_at = GREATEST(available_at, decision)`

**Correctness / sufficiency.** The worker's knowledge cutoff is the `now` it passes to `lease_job`
(`assessment_worker.py:127`, `lease.knowledge_cutoff`), and the lease admits a PENDING job only at
`available_at <= :now` (`postgres_assessment_store.py:213-215`). With the lift, every decision a PENDING job
carries satisfies `decided_at <= available_at`, so any lease of that job has cutoff >= every carried decision. The
job row is locked `FOR UPDATE` by the widening transaction until commit and the lease uses `SKIP LOCKED`, so a lease
of a widened job always follows the commit, and the run's evidence read (a later READ COMMITTED snapshot) sees it.
Decisions whose chunk meets a LEASED job (directly, or after waiting on its row lock - L-b) insert a new PENDING job
at the decision instant, which is live work. I walked the remaining interleavings (ingestion waiting on the Site
advisory lock while the worker leases; retry back-off jobs - `GREATEST` keeps the back-off; expired-lease re-leases -
not widened, so a new job is inserted) and found no path where a committed accepted decision is excluded by a
finished run with no live work. Without the lift the invariant fails: I re-ran the implementer's M2 mutation
(lift removed) and `test_a_cutoff_sampled_before_a_committed_widening_cannot_lease_the_widened_job` failed in both
skews with `a lease at a cutoff before the decision consumed the widened job` (reverted; tree clean). So "existing
coalescing should suffice" was false, and the packet's own fallback ("evidence-owned transactional re-enqueue
through `recompute_job`") authorises this narrowest form of it. `created_at` is kept; the only other reader of
`available_at` is the `_LIVE_JOBS` FAILED-supersession rule (`postgres_assessment_store.py:88-91`), which a PENDING
widening cannot reach (`fail_job` rewrites `available_at` on failure). In production the decision instant is always
<= DB now at commit, so the lift never future-dates a job.

**Starvation under a continuous stream - quantified.** The lift adds a miss only when a chunk's decision lands
*after* the worker's cutoff sample and commits *before* its lease statement. That gap `g` is one `db_clock()` call
(it builds and disposes a schedule-store engine, `stages.py:59-71`) plus the lease's own connect - tens of ms,
perhaps ~100 ms under load. Pre-existing, `SKIP LOCKED` already misses the job for the remaining hold time `h` of any
in-flight chunk transaction. A miss only defers the job to the next tick (it stays live; the window reads non-CURRENT,
health shows BACKLOG). With chunks landing every `c` seconds on an overlapping window, the added per-tick miss
probability is about `g/c` (e.g. 0.1 s / 60 s ~ 0.2 %), and `n` consecutive misses about `((g+h)/c)^n`. Sustained
starvation needs back-to-back commits with period comparable to `g+h`, i.e. a saturating stream into one Site's
window - which already starves the job through `SKIP LOCKED` before S4-07. The tick interval does not enter the bound
beyond setting how long each deferral lasts. Second-order effect: the lifted job sorts later in
`ORDER BY available_at, created_at`, delaying it behind older due jobs only up to the per-Site `s3_jobs_per_site`
backlog, which is bounded. **A cap relative to `created_at` should not be added**: any cap that lets a job be leased
at a cutoff below a carried decision reintroduces exactly the terminal gap this fixes. No Architect ruling needed.

## Focus 2 - Deviation 2: F-A alarm test via SQL restoration

Still meaningful. The test now (a) forces a decision ahead of DB time through `test_decision_clock_override`,
(b) asserts the lift (`available_at == ahead`), that a tick leaves J PENDING and raises no `S3_STALE_NO_JOB` - new
coverage of the fix from the override side - and then (c) restores the pre-S4-07 widening by SQL and keeps every
original stale/no-job alarm and `requeue --day` assertion. The detector and recovery are what F-A defends; they
are exercised against the exact state that would arise if the invariant were ever broken (manual CLI, a future
writer, a regression). Labelled override-path in the docstring and backlog. Skew 120 s with the existing
`db_now < ahead` guard is reasonable. See Low L1 on the test name.

## Focus 3 - DB-time stamping

- `_decision_instant` runs after `SELECT ... FROM ingestion_batch ... FOR UPDATE` and inside the chunk transaction,
  using `clock_timestamp()` (`postgres_evidence_ledger.py:281,325-328`). One instant per chunk stamps every new
  disposition and `_coalesce_job`'s insert/lift. The 0012 consequence trigger fires inside the same transaction.
- Retry of a committed chunk: `COMPLETED` returns early; otherwise only ordinals from `processed_count` are decided,
  so stored dispositions keep their instants (asserted in the restart test, `dispositions[:size] == partial`).
- `received_at` (`open`) and `completed_at` (`decide_chunk(completed_at=self.clock())`) stay app clock; every
  production-path test asserts both equal the app clock and does not assert their order against `decided_at` (L-a).
- Override is test-only: the only non-test references are the ledger itself; `evidence/composition.py:26`
  constructs `PostgresEvidenceLedger(database_url)` with no override. The protocol has no other `decide_chunk`
  implementation to update.

## Focus 4 - production-path proofs

`production()` asserts `ledger.test_decision_clock_override is None` on every ingestion. All four race tests are
parametrised over fast (+2 h) and slow (-2 h) app clocks; each brackets the decision between DB reads and asserts
`!= app_at`. Restart tests use fast (Site A) and slow (Site B); the fast restart case would also fail on an app-clock
decision through `knowledge_cutoff >= last`. The worker-first test proves the lock wait via `pg_stat_activity`
(L-b) and that ingestion inserts a new job with `available_at == created_at == decided_at`. The uncommitted-new-job
case and two-window/duplicate-only/other-Site restart cases are present. `settle` rejects any CURRENT read missing
the IDs; `no_stale_gap` checks the invariant after each race.

## Focus 5 - ownership

The only new SQL is the ledger's existing `UPDATE recompute_job` widening, extended with `available_at`; the ledger
already owns `recompute_job` in rule 8 (`configuration-persistence.ps1:622-625`). No schedule-table writes, no
assessment-writer change, no migration. `check-architecture.ps1` (which includes rule 8) passed.

## Focus 6 - residuals

Honestly stated in packet, README-db and CODE_STATE: manual `process-jobs` takes an app-clock cutoff
(`assess_dispatch.py` builds the worker on the store default clock), so I3 is not claimed closed for manual CLIs and
the stop-the-tick rule is kept; `clock_timestamp()` vs `now()` reasoned, not mutation-proved (no batch-lock
contention test) - I agree the reasoning is sound (`now()` is transaction start, before the `FOR UPDATE` wait);
configuration `recorded_at` out of scope. Observation: with the lift, a manual run whose app clock is *behind* DB
time also cannot lease a job carrying a later decision, so the manual residual is narrower than "can mix clocks"
suggests; keeping it open is conservative and fine.

## Findings

- **L1 (Low, preference/clarity)** `backend/tests/test_s4_schedule_health_postgres.py:387` - the test name still
  says a decision after the DB cutoff widening a pending job *raises* `S3_STALE_NO_JOB`; after S4-07 it does not
  (the alarm arises only after the SQL restoration). The docstring explains it, but the name now overclaims in test
  reports. Fix: rename to something like `..._override_path_restored_stale_widening_raises_s3_stale_no_job...`.
  Not an acceptance gap.
- **L2 (Low, residual, pre-existing)** No health signal ages a live PENDING job that keeps being missed (by
  `SKIP LOCKED`, or now by the lift); it shows BACKLOG indefinitely. Starvation is improbable (above) and the read is
  honest (non-CURRENT), but if it ever happened it would be silent. Candidate for the existing "health scan cost"
  backlog item rather than this slice.

Housekeeping (not a finding): the backlog I3 line says "pending independent review"; update at merge closeout.

## Checks run (this review, worktree `AssetOpsV1-review4`)

- `assetops_backend.__file__` = `C:\Users\assef\Bineyame\AssetOpsV1-review4\backend\assetops_backend\__init__.py`.
- Private base DB `assetops_s407rev_test`; dropped after (no `assetops_s407rev%` databases remain).
- `pytest backend/tests/test_s4_evidence_decided_at_postgres.py test_s4_schedule_health_postgres.py::TestStaleWithoutJob`:
  **11 passed** (220.9 s).
- Mutation (lift removed): cutoff-sampled test **2 failed** (fast, slow) with the expected message; reverted.
- `pytest test_s2_evidence_ledger_postgres.py test_s2_site_evidence_postgres.py test_s3_dispatch_assessment_postgres.py
  test_s4_evidence_consequence_work_postgres.py test_s4_schedule_health_postgres.py test_s4_schedule_tick_postgres.py
  -n 2 --dist loadfile`: **79 passed** (283 s).
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- Not rerun: `test_s4_finding_store_postgres.py` / `test_s4_finding_evidence_history_postgres.py` (long; CPU-loaded
  machine) and the full suite. Cited implementer full suite at code revision `f1e67a52`: JUnit 2147 tests, 0
  failures/errors/skipped, 708 s; `git diff --stat f1e67a52..a7278bb2` touches only `.agent/`, `.ai/`, `tasks/` docs,
  so that evidence applies to the reviewed revision. No frontend change; no UI or layout evidence required.
