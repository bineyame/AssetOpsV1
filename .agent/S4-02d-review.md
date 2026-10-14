# S4-02d fresh Claude review: phase 3 and the whole slice (analytic and Finding worker schedule)

Reviewer: fresh Claude. I did not build or review any earlier phase. Branch
`task/S4-02d-analytic-finding-worker-schedule` at `059158b8`.

- Phase 3 diff: `f2645e48..HEAD` (F-A/F-C/F-D fixes, walkthrough tool and evidence, I4 test change `2288da6a`,
  closeout docs). Whole slice: `dc5afad5..HEAD`.
- Phases 1 and 2: only their carries re-checked (`.agent/S4-02d-phase-1-review.md`, `.agent/S4-02d-phase-2-review.md`).

Judged against `tasks/S4-02d-analytic-finding-worker-schedule.md` (contract items 1-4, the phase 3 row, N2-N6),
`D-2026-10-14-s402d-schedule-storage-and-install-gate`, `D-2026-10-14-s402c-late-sequence-and-s5-money`, the
packet `.agent/S4-02d-review-packet.md`, the phase-3 handoff and the walkthrough evidence (`.md`, `.json`,
`-commands.log`). Under the owner-approved process rules, only High/Medium findings block, Low/Info go to carries,
and I did not rerun the full backend suite.

## Verdict: ACCEPT with carries

No High or Medium finding. F-A is fixed correctly. The alarm fires on the reviewer's case, and my own mutations show
that both the alarm and the two `requeue --day` refusals are non-vacuous. `requeue --day` cannot create a duplicate
or out-of-scope job. I reran the tick-only walkthrough on my own database and ports and got the claimed result:
23/23, 0 hand-run Leg B commands, and the same IDs pattern and money (15.8125).

The I4 test's 31-384 s wall time is host I/O, not product lock contention. I observed no lock waits at any point,
and the slow time sits in fixture DDL/TRUNCATE fsync and in uniformly slower ticks. Since `2288da6a` the test's
assertions are deterministic. Its non-vacuity now rests on round 2, which is sequenced rather than raced (R-1).
The three findings are all Low test-robustness or coverage items for the carries list.

## Checks I ran (as observed)

| Check | Result |
| --- | --- |
| `tools/s402d_tick_walkthrough.py run --db assetops_s402d3rev --tls-port 8930 --http-port 8931 --work <scratch>` | **exit 0, 23 `[ok]`, 0 `[FAIL]`**, 1 min 51 s; then `drop` (database and work folder removed) |
| My own grep of that command log (263 lines) for `process-jobs|match-findings|recompute_consequences|run_pending|FindingMatcher|ConsequenceRecomputeWorker` | 0 hits; 5 `scheduling.run tick`; backend entry points are only setup (import, configuration, provision, price), `scheduling.run tick/health/upstream`, and the read-only consequence/finding read scripts |
| Focused suites on `assetops_s402drev3_test`: schedule health/tick/upstream/install-gate, S3 dispatch assessment/read, S4 consequence recompute, evidence consequence work, finding store | **76 passed** in 9 min 50 s (run twice; first run's summary line was lost to my output filter, no failure markers) |
| I4 race test alone, 6 runs (1 + 5) | 6/6 passed, 26-37 s wall each |
| Instrumented scratch copy of the I4 test (not committed), 4 runs | 4/4 passed; 45 s, 358 s, 229 s, 49 s (one further run cut by my tool timeout, not a test failure) |
| `pg_stat_activity` polling during 7 of those runs (threshold 0.4-2 s, with `pg_blocking_pids`) | **no Lock waits, `pg_blocking_pids` always empty**; the only long statements were migration `ALTER TABLE` and fixture `TRUNCATE ... CASCADE` waiting on `IO:DataFileImmediateSync` (up to 6.8 s each) |
| Targeted mutations on `TestStaleWithoutJob` (baseline passed, 34 s) | M1 alarm condition disabled: **caught** (`'IDLE' == 'FAILED'`). M2 `--day` ignores live jobs: **caught** (`0 == 2`). M3 `--day` ignores read status: **caught** (`0 == 2`). M4 health ignores intersecting live jobs: **survived** (R-3). All reverted; `git status` clean afterwards |
| `tools/schedule-install-gate.py --host-class demo / walkthrough / pilot / private` | CLOSED exit 2 (F1 open) / CLOSED exit 2 / CLOSED exit 2 (F1 listed once: F-D fixed) / OPEN exit 0 |
| `tools/check-all.ps1` | **All 9 guards passed** |
| Full backend suite | Not rerun (process rule; implementer reported 2116 passed) |
| Frontend suite, build, `tsc`, layout evidence | Not applicable: `git diff dc5afad5..HEAD` touches no `frontend/`, `host/` or `gateway/` file. Not run |

Scratch database `assetops_s402drev3_test` and walkthrough database `assetops_s402d3rev` were dropped.

## Focus 1: F-A fix

- **Alarm** (`backend/assetops_backend/scheduling/health.py:167-187`, wired at `:256-257`, state at `:268`). For
  each selected UTC-day head, the check skips any day with an intersecting live job. Otherwise it reads the day
  through the existing `DispatchReadService.window` and raises `S3_STALE_NO_JOB` with Site `FAILED` on
  `STALE_PROJECTION`. Non-UTC-day heads are skipped by design. The test reproduces the reviewer's case: a decision
  stamped DB now + 20 s widens the PENDING job, a tick completes without it, and the seam reads STALE with no job.
  Health showed `FAILED` with the alarm, and after requeue plus a tick it showed `CURRENT` and `IDLE`. Mutation M1
  is caught.
- **`requeue --day`** (`backend/assetops_backend/analytics/assess_dispatch.py:134-156`). It refuses (exit 2) unless
  the day reads `STALE_PROJECTION` and no live job (PENDING, LEASED or unsuperseded FAILED) intersects it (M2 and M3
  caught). It cannot duplicate: `enqueue` takes the per-Site `_JOB_LOCK` and widens any overlapping PENDING job
  (`postgres_assessment_store.py:264-283`), so a racing reconcile coalesces with it. It cannot reach out of scope:
  `recompute_job` has the composite FK `(tenant_id, site_id) -> site(tenant_id, id)` (migration 0005), and both the
  read and `live_jobs` are scoped by tenant and Site. Exactly one of `--job-id` and `--day` is required. The
  requeued job's `available_at` is app-clock now. Run on the ingestion host, that defers it past the decision,
  which is the safe direction. The runbook says to wait for the DB clock regardless.
- **I3 residual** is stated honestly in `backend/README-db.md` (schedule section and alarm table), CODE_STATE, the
  packet and the handoff. The scheduled S3 cutoff is DB time while `decided_at` is still the app clock. The window
  fails closed and is alarmed, and the fix is routed to an evidence-owner packet.
- **Ingestion unchanged**: no file under `backend/assetops_backend/evidence/` changed in the slice diff.

## Focus 2: walkthrough rerun

All of these held on my run, which was a fresh database and private tree built from HEAD:

- Tick-only. No `process-jobs`, `match-findings` or `recompute_consequences run`, by CLI or entry point.
- Tick 1 is S3 OK, then S4 MATCHED, then the drain selects 2. Tick 2 is idle: `SKIPPED_UNCHANGED_FENCE`, no new
  pass, and the heartbeat advanced.
- After the late acceptance there is exactly one EVIDENCE_ACCEPTED row for r1, and the r1 read is
  `STALE ['TECHNICAL_INPUT_CHANGED']` with that work pending. The seam reads `STALE_PROJECTION` (stage S3).
- Tick 3 runs S3, S4 and the drain together. It appends r2 (`SUPPORT_CHANGED`), which cites the late ID.
- r1's EVIDENCE_ACCEPTED attempt is SUCCEEDED with the typed no-op `FINDING_REVISION_SUPERSEDED`.
- r2 is **CURRENT PRICED**, amount high **15.8125**, using price v1.
- The seam is CURRENT only after tick 3, and its run is r2's run.
- Replay tick 4 appends no pass, no work and no consequence revision.
- A stopped worker shows health `STOPPED` (`HEARTBEAT_STALE`), and the seam is not CURRENT, with
  `SCHEDULE_STOPPED`, 0 jobs and 0 work. Recovery tick 5 brings it back to CURRENT.
- There is no duplicate consequence basis.

The same-revision Leg A state is honestly cited to S4-02c, not claimed. The S3 limits recorded are the
source-ordered variant's `INTERVAL_LIMITED/OPEN_BOUND` only, and money eligibility is recorded, not asserted (M5).

## Focus 3: the I4 race test (`2288da6a`) and its wall time

**Classification: host I/O variance plus test design, not product lock contention.**

- **Timing.** On this host the same test took 26 s, then 358 s, and later 229 s. In the 229 s run, the instrumented
  tick, submit and convergence phases add up to about 60 s. The remaining ~170 s is fixture setup: schema drop,
  migrations and `TRUNCATE ... CASCADE`. My poller saw those statements waiting on `IO:DataFileImmediateSync`
  (Docker Desktop fsync). In the 358 s run, every phase was uniformly 3-10x slower: a race tick took 42 s, a
  convergence tick 96 s, and a single `kobo.submit` 19 s. Across 7 polled runs there was never a `Lock` wait and
  never a non-empty `pg_blocking_pids`. The full suite going from 16 to 37 min is consistent with the same I/O
  variance, since every Postgres test rebuilds its schema. I did not rerun the full suite to prove that.
- **Determinism.** Round 2 joins the chunk threads inside the S4 `before` hook. That hook runs between stages on the
  tick thread, which holds the Site claim, a row value and not a DB lock, and has no open transaction. The chunks
  therefore commit inside the claim with nothing to deadlock on. `held` was True in 4/4 instrumented round-2
  runs, with `('STALE_PROJECTION', 1)` live work left behind each time. Both closing assertions (`any(overlapped)`
  and `any(n > 0)`) are now deterministic.
- **Vacuity of rounds 0-1.** In my runs, ingestion submits took 2-19 s while the race tick finished first, so the
  chunks usually committed after the claim was released. Round 0 overlapped in 2/4 runs and round 1 in 0/4.
  See R-1.

## Focus 4: install gate and owner-facing copy

The gate is CLOSED for demo, walkthrough and pilot, and OPEN only for private (observed). Templates
`backend/deploy/schedule/*` are headed DO NOT INSTALL, and F-C's `TimeoutStartSec=900` exceeds the 780 s tick lease.
Nothing was installed: the repository holds only templates, and the walkthrough used explicit ticks. The slice
changes no frontend, host or owner-visible copy. Its text changes are runbook, operator CLI JSON/stderr and agent
docs, so **USER_REVIEW_REQUIRED false holds**.

## Findings

### R-1 (Low, test honesty; carry) - the I4 test's round 1 does not race, and round 2 is sequenced

`backend/tests/test_s4_schedule_health_postgres.py:460-471`. The comment says round 1 chunks "race S3's lease and
processing". On this host they never overlapped the claim (0/4), and round 0 overlapped in 2/4. The non-vacuity
assertions are now satisfied by round 2, where the chunks are deliberately committed before S4 inside the claim.
That is a sound deterministic regression for "evidence committed mid-tick after S3 is never read CURRENT and is
reprocessed". It is not a concurrent race. The packet's I4 claim correctly rests on the phase-2 reviewer's
independent real-child race, so this is not an acceptance gap. Fix (carry): reword the comment and docstring to
say round 2 is sequenced and rounds 0-1 are opportunistic. If a committed race is wanted, gate round 1 on an event
that the S3 stage sets after leasing.

### R-2 (Low, test robustness; carry) - `TestStaleWithoutJob` has a 20 s skew budget that slow ticks can exceed

`backend/tests/test_s4_schedule_health_postgres.py:395-400`. The test needs the whole first tick to finish within
20 s of DB time, otherwise it fails with "the tick outlived the skew; widen it". The baseline took 26-34 s in total
here, but in the slow I/O periods I observed (single in-process ticks of 42-96 s) the assertion would fail. It
fails loudly, not vacuously, so it is not a correctness problem. Fix (carry): derive the skew from a measured
tick, or use about 120 s and keep the wait loop.

### R-3 (Low, missing test; carry) - the alarm's live-job exclusion is untested

`backend/assetops_backend/scheduling/health.py:179`. Mutation M4 (always evaluate, ignoring intersecting live
jobs) survives. It is mostly equivalent, because the read itself reports `PENDING` while PENDING/LEASED jobs exist.
The observable difference is a live FAILED job over a STALE day: health would then also raise `S3_STALE_NO_JOB`
and advise a `--day` recovery that `requeue --day` refuses. Fix (carry): assert that a day with a FAILED live job
raises `S3_JOB_FAILED` and not `S3_STALE_NO_JOB`.

### Info

- `assetops_s402d_test` (phase-1 scratch) still exists on the shared server; housekeeping.
- Packet deviation 2 (a transient `S3_STALE_NO_JOB` in the seconds before reconcile enqueues a model or
  configuration change) is real and fails closed. Health is a CLI today; it should be revisited with carry 3 if
  health ever runs on a timer.

### Not findings (checked)

- Phase-1 carries F1-F3 and phase-2 F-C/F-D: landed (F-C template, F-D observed once, probe usage exit 2).
  F-B is honestly carried.
- Walkthrough check coverage matches the phase-3 row: accepted ID, pre-tick STALE/TECHNICAL_INPUT_CHANGED, r1
  no-op, r2 CURRENT citing the late ID, seam eligible only after work, IDs/watermarks/backlog/heartbeat
  before and after, replay, stopped worker, command-log grep including `recompute_consequences run` with
  mutation evidence, S3 limits, and source-ordered positive path. N6 was met on my run too (tick 3 completed
  S3 and S4).

## Registry closeout notes

- **`I-analytic-finding-worker-schedule` may resolve on merge.** Its acceptance target is met by the explicitly
  configured `walkthrough` environment:
  - S3 then conditional S4 for every active Site, with bounds, restart/retry and observable backlog/failure.
  - No false CURRENT while work is pending.
  - Late evidence reaches a revised Finding and consequence without manual commands.
  - A stopped worker leaves the seam non-CURRENT.

  Evidence: `.agent/S4-02d-walkthrough-evidence.md` and this review. Record I4 as proved at the phase-2
  independent review (packet carry 7).
- **Stays open:**
  - **I3 `decided_at` comparand.** Belongs to a separate evidence-owner packet: DB-time `decided_at`, or a new
    job when a widened job's lease could predate the decision. I3 is closed for every other scheduled-time use.
  - **F-B** statement-level rule-8 guard.
  - **Health scan cost** of `STALE_NO_WORK` and `S3_STALE_NO_JOB`, before health runs on a timer or an API.
  - **Demo-host tick cost** and `--max-sites`.
  - **S5-01 seam carries:** `S3_UNASSESSED` shown as a gap, `source_open`/F1 money, one seam per process.
  - **Install gate:** demo stays CLOSED until `I-late-reading-series-and-money-limit` resolves. Pilot stays
    CLOSED on F1 and `I-stored-demo-provenance` even after this node resolves.
  - **R-1 to R-3** above.

## Residual risk not already named by the packet

- Postgres test wall time on this host is dominated by Docker Desktop fsync during per-test schema rebuilds. Timing
  budgets inside tests (R-2, and any future "within N s" assertion) should be generous or measured.
