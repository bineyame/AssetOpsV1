# S4-07 plan re-review after fix round 1

Reviewer: fresh independent Claude reviewer (did not author the packet or the fix). Worktree
`AssetOpsV1-plan2`, branch `plan/small-followons`, HEAD `59345c6e`; path:line checks against main `5a37c8ce`.
Inputs: `.agent/small-followons-plan-review.md` (S4-07 RETURN M1 + Lows), `.agent/planner-S4-07-fix-brief.md`.
Plan review only; no test suites run.

## Verdict: ACCEPT (Lows carried, none blocking)

M1 is resolved. The mechanism is decided and buildable as written.

## Checklist

- **DB-time contract decided.** One `clock_timestamp()` per chunk inside the write transaction, after the batch
  `FOR UPDATE`, used for every new ordinal's `decided_at` and for `available_at`/`created_at` of a job that
  `_coalesce_job` inserts; widened jobs keep their timestamps; host clock, `now()`/`transaction_timestamp()` and
  pre-transaction sampling excluded with reasons. Matches main: `decide_chunk` at
  `postgres_evidence_ledger.py:251-307` threads `decided_at` into the disposition insert, `completed_at` and
  `_coalesce_job(..., decided_at)` (`:376-404` inserts `available_at = created_at = :now`). Buildable.
- **Named test-only override.** `test_decision_clock_override`, absent = DB path, never set at `main.py:265-269`;
  one result per chunk for disposition and inserted-job stamps; explicitly not evidence for race/restart. The
  `EvidenceLedger.decide_chunk` protocol (`ledger.py:403-411`) changes so the service passes app-clock
  `completed_at` only. All listed fixtures exist at the cited lines on main (`test_s3_dispatch_assessment_postgres.py:53-62`,
  `test_s4_finding_store_postgres.py:117-142` and its users at `test_s4_finding_evidence_history_postgres.py:18`,
  `test_s4_evidence_consequence_work_postgres.py:33,79-81`, `test_s4_schedule_tick_postgres.py:94-95`,
  `test_s4_schedule_health_postgres.py:28-30`, `test_s2_evidence_ledger_postgres.py:127-128`,
  `test_s2_site_evidence_postgres.py:267-276`), plus a catch-all for other exact-time fixtures.
- **Race/restart on the production path.** Build step 2 and 3 say "no override"; ingestion-first, worker-first,
  worker-skips-uncommitted, blocked/rechecked, fast/slow app clocks, two-window chunk, duplicate-only, other Site.
- **F-A alarm test re-driven through the override.** Step 3 names `test_s4_schedule_health_postgres.py:385-424`
  (exists; `TestStaleWithoutJob`), sets `decided_at` ahead of DB time via the override, keeps alarm + requeue
  assertions, labelled override-path.
- **Lock/lease reasoning is a proof obligation.** Cites `_coalesce_job` `FOR UPDATE` and the lease
  `FOR UPDATE SKIP LOCKED` (`postgres_assessment_store.py:203-222`) and `d.decided_at <= :k` (`:47-56`); invariant
  stated; fallback is evidence-owned re-enqueue through `recompute_job`, already in rule 8's ledger tables
  (`tools/checks/configuration-persistence.ps1:622-625`, verified); schedule-table writes and writer-ownership
  expansion explicitly excluded. I walked the interleavings and the reading holds: a committed decision always
  has either a widened PENDING job that could not be leased before commit (so its run's DB cutoff is later than
  the commit and therefore than `decided_at`) or a newly inserted PENDING job.
- **Lows.** L1 batch `received_at`/`completed_at` stay on the app clock (stated). L2 configuration `recorded_at`
  out of scope (stated twice). Manual app-clock `process-jobs` residual stated; I3 not claimed closed for manual
  CLIs; stop-the-tick rule retained. README-db citations `:128-135,204,210-212` exist on main.
- **Size.** M, one bounded build + one review (<= two phases). Honest for a ledger contract change, ~10 fixture
  files and one new real-Postgres race/restart file.
- **Registry.** `tasks/README.md:33` row parses; packet header `USER_REVIEW_REQUIRED: false`;
  `tools/check-agent-workflow.ps1` passed on this HEAD.

## Low findings (carry to the implementer; non-blocking)

- **L-a (receipt ordering under skew).** After the change `ingestion_batch.completed_at` (app clock) and
  dispositions' `decided_at` (DB clock) are both surfaced on the receipt (`ledger_reads.py:242,352`). Today they
  are equal for the final chunk; with skew `completed_at` may precede the last `decided_at`. The packet keeps
  the receipt semantics deliberately; the implementer should not assert `completed_at >= decided_at` anywhere and
  should mention the possible inversion in the README-db note.
- **L-b (decision instant precedes the job lock wait).** The instant is sampled after the batch lock but before
  `_coalesce_job`'s advisory lock and job `FOR UPDATE`, so `decided_at` can predate commit by that wait. The
  invariant does not depend on it (job coverage carries it), and the blocked/rechecked case should exercise this
  wait explicitly: under READ COMMITTED a `FOR UPDATE ... LIMIT 1` whose locked row became LEASED returns no row
  and ingestion inserts a new job, which is the safe outcome to assert.
- **L-c (housekeeping).** The fix round added `.agent/planner-S4-07-fix-log.txt` (2,794 lines of Codex log) to the
  branch; consider dropping it before the planning merge. Not a packet issue.
