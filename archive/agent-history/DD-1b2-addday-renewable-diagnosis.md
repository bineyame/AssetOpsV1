# DD-1b2b owed item: why add-day days get no spare-solar assessments (read-only diagnosis)

Clone `assetops_demo3_dd1b2r_test`, read-only sessions (`default_transaction_read_only=on`), no writes, no ticks. `dd1b2p`/`dd1b2q` untouched. Clock at measurement: 2026-11-07 09:17Z.

## Verdict

The Architect's candidate (the cutoff at `mini_depth/worker.py:118-121`) is **REFUTED**. The real cause is a **backlog, not a gate**: the spare-solar jobs for S-3 and S-1 **were enqueued** (6 each) but are still `PENDING`, `attempts = 0`. The serve tick runs at most 10 mini jobs per Site, and each add enqueues 34 or more.

## 1. Cause (MEASURED unless marked)

- **MEASURED, jobs exist.** `recompute_job`, domain `mini_renewable`, status `PENDING`, attempts 0, window_start local 08:00 to 13:00 on 2026-11-02 (6 rows) and on 2026-11-04 (6 rows). That equals the 6 local hours with a positive `pv_available_power` reading on each day (72 positive readings of 97, 12 per hour). `available_at` is 09:05:55Z (S-3) and 09:08:54Z (S-1). The enqueue test (`migrations/versions/0048_daylight_enqueue.py`, function `mini_renewable_hour`, trigger `enqueue_mini_depth` on `accepted_evidence` insert) passed. The enqueue is not cutoff-gated.
- **MEASURED, the other domains for the same adds.** S-3 add enqueued backup 10, fuel 9, service 9, renewable 6 (34 jobs, one transaction, identical `created_at`). S-1 add enqueued backup 10, fuel 9, service 9, renewable 6 (also 34). Revisions written after 09:00Z: 11-02 backup 6, fuel 9, service 5 (20 jobs in all) and **0 revisions for 11-04**. So tick 1 and tick 2 together processed 20 jobs, both on S-3's batch. S-3 is left with backup 4, service 4, renewable 6 pending; S-1 is left with all 34 pending. Total mini jobs PENDING now: 48 (renewable 12, service 13, backup 14, fuel 9).
- **The mechanism.**
  - The tick's mini stage runs `run_pending(limit)` with `mini_jobs_per_site = 10` (`scheduling/tick.py:66`, called at `:452`; stage at `scheduling/stages.py:139-151`; loop at `mini_depth/worker.py:101`). The bound is deliberate: the stage must stay under the 300 s lease (`stages.py:136`, `tick.py:95`).
  - Leasing is FIFO on `ORDER BY available_at, created_at` (`analytics/adapters/postgres_assessment_store.py:415`). All 34 jobs of one add share the same timestamps, so the order within a batch is the physical order. In the data, renewable comes last in S-3's batch: fuel, then backup and service were done first, and renewable has 0 of 6 done after 20 jobs. (READ for why: the trigger loops the domains in a fixed order. The row order is not guaranteed.)
  - So a batch needs ceil(34 / 10) = 4 ticks to finish, and renewable is the last to be reached. The S-1 add's tick spent its 10 jobs on S-3's leftovers.
- **Why the candidate does not apply.** `worker.py:118-121` is inside `reconcile()` (`:108`), the explicit backfill CLI. The tick path is `run_once()` (`:62`), which has no daylight filter: it processes whatever job is leased, at the lease clock. Nothing there depends on `received_at` against a cutoff. (READ, and consistent with the rows: the enqueue-time test saw the readings.)
- **Why the earlier days have theirs.** 10-31 (12 renewable revisions), 11-05 (7) and 11-06 (7) were assessed by the prepare's `drain_mini`, which loops `run-pending --limit 500` until a pass returns fewer than the limit (`tools/demo_combined.py:526-536`). It has no per-tick cap. 11-01 and 11-03 have no PV readings at all in this build, so they never had renewable jobs. That is a data property, not a gap.
- **Side finding (packet P7/L1).** The packet records "dirty 0 after M3's ticks"; the DB holds 48 pending mini jobs. Whatever "dirty" counted, it did not count the mini queue. Tick until the tick reports `deferred = 0` (the mini stage returns it, `stages.py:151-156`).

## 2. Does the live S+2 add (kind `normal`, one tick right after) hit the same gap?

**Yes, on the evidence, with one measurement left to confirm the order on a clean queue.**
- MEASURED: the S-1 add was kind `normal`, `assess: "tick"` (`.agent/DD-1b2a-m3.json`), and left 34 of 34 jobs pending after its tick. A clean queue would not have changed the count: 34 jobs against a limit of 10.
- Whatever the order, one tick of 10 cannot drain 34, and renewable sits last in the observed batch order. So after one tick the live day has backup/fuel/service partly assessed and no spare-solar: the Grow row has no spare-solar reading and the study is not queued.
- To settle the order on a clean queue: one tick on a fresh clone (not this DB) after a single add, then read which 10 jobs went. This is optional: the conclusion (not drained after 1 tick) holds for any order.
- Escape that already exists: `add_day(..., assess_now=True)` (`demo_combined.py:598-613`) turns the run's assess into `build` and calls the unbounded `drain_mini()` for Kobo. Kind `late` refuses it (`:581`). READ that the demo script would then see renewable heads before its tick queues the study; not run here.

## 3. Would a whole-list build assess S-3 and S-1?

**Yes (READ, with MEASURED analogues).** The prepare runs the day passes, then `after_children` calls `drain_mini()` before the mill (`demo_combined.py:484`), and again before the ticks (`finish`, `:512`). That loop is unbounded, and the enqueue trigger fires on each day's PV readings. The same mechanism produced 12/7/7 renewable revisions for 10-31/11-05/11-06 on this clone. So S-3 and S-1 would get 6 renewable hours each (their PV is the same shape as these clone days) and the studies ending there would be queued by the tick. The rehearsal can therefore see recurrence on a whole-list build, provided the ticks run to `deferred = 0`. One caveat: the clone (a probe list) cannot show this itself, since S-3 and S-1 were add-day deliveries here.

## 4. Smallest fix and what the script must say

It is **intended behaviour of a bounded tick, not a logic defect**; the gap is the add's follow-up. Options, smallest first:

| Option | Where | Size | Blast radius |
|---|---|---|---|
| **A. Script/rehearsal only (recommended)** | The live add uses `--assess-now` (kind `normal`/non-late), or the script ticks until `deferred = 0` (about 4 ticks for a 34-job day; add-day itself takes longer than that). The rehearsal and `dd1b2a_m3.py` loop ticks until `deferred = 0` | +0 code; one script line and one measurement change | None |
| B. Tick bound | `TickLimits.mini_jobs_per_site` 10 to about 40 (`tick.py:66`). 10 jobs took about 6 s, so 40 is about 25 s, under `mini_seconds = 120` and the 300 s lease | About +0.1 | `tests/test_w402_mini_stage.py:97` pins `(10, 120)` and must change. Every Site's tick, but only Kobo has mini work (role set 4). Cold and EV: no mini domains, no effect. Other assessments (S3, domain, opportunity) are separate stages and unaffected, but the tick is longer |
| C. Lease priority | Order the lease by domain (renewable first) at `postgres_assessment_store.py:415` | About +0.1 to 0.2 | Mini domains only (Cold/EV untouched). Does not drain the batch in one tick, only reaches renewable first. Shared SQL with tests that pin the lease order; weaker than A or B |

Recommendation: **A**, because no product change is needed and the demo wants the same state as the whole-list build. If the owner wants a one-tick add, use B.

What the demo script must say: the live add on S+2 is `normal` with assess-now (or "tick until the spare-solar line appears"), and the first board read waits for `deferred = 0`. The rehearsal's M3 rerun must tick to `deferred = 0` and then read the renewable selections for S-3 and S-1 and the studies ending there. That, not the current M3 file, is what decides recurrence.

Evidence queries are not kept as files (read-only, ad hoc); the numbers above are from `recompute_job`, `mini_depth_revision` and `accepted_evidence` on the clone as of 09:17Z.
