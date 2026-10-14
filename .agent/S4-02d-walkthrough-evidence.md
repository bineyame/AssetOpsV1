# S4-02d phase 3: automatic (tick-only) late-power walkthrough evidence

Tool: `tools/s402d_tick_walkthrough.py run` (then `drop`), code from `dc4b7e4f` (git HEAD, staged into a private
tree), database `assetops_s402d3walk` (dropped afterwards), TLS port 8928, schedule environment `walkthrough`.
It reuses the S4-02c tool (`tools/s402c_late_power_walkthrough.py`: deployment shape, `P02-power-late`
SOURCE_ORDER variant, consequence read) and replaces every S3/S4/consequence step with a full schedule tick
(`python -m assetops_backend.scheduling.run tick --environment walkthrough --max-sites 5 --s3-jobs 10
--consequence-items 100`). No timer installed. Machine record: `.agent/S4-02d-walkthrough-evidence.json`; command
log: `.agent/S4-02d-walkthrough-commands.log` (263 lines, every subprocess the tool started). All values below are
actual output of the run: **23 checks, 0 failed, exit 0**.

## No hand-run Leg B (W4, N6)

The tool greps its full command log for `process-jobs|match-findings|recompute_consequences run|run_pending(|
FindingMatcher|build_finding_matcher|ConsequenceRecomputeWorker|build_consequence_recompute`: **0 hits**, 5 tick
invocations. Non-vacuity: with one `self.drain(...)` (the S4-02c one-off `recompute_consequences run`) inserted
after tick 3, the run exits 1 and exactly this check fails, naming the line
`py -m assetops_backend.recompute_consequences run --tenant demo --site KOBO-001 --limit 100`; reverted.
Stage children are started by the tick process itself, not by the tool.

## 0. Configuration

SYSTEM price v1 `79f9b407-e6aa-4f19-b35f-918aede7c217` (1.25 USD/L), published before both deliveries.

## 1. First delivery, ticks 1-2

- First delivery: 6 batches, 174 accepted readings (24 generator-power means), digest `55c725a7...1e03b`.
  Before any tick: S3 job `563c156d-bd35-478c-8a6a-be6ede6f5fa7` PENDING, no selection, no pass. Seam `PENDING`
  (`S3_PENDING, LIVE_JOB, WORK_OUTSTANDING, SCHEDULE_STOPPED, SITE_NOT_OBSERVED`); health `STOPPED`
  (`TICK_NEVER_COMPLETED`, `SITE_NOT_OBSERVED`), backlog S3 1 / S4 yes / consequence 1.
- **Tick 1** (DB now 17:44:24Z): COMPLETED; s3 OK processed 1 (1405 ms), s4 MATCHED (1664 ms), consequence OK
  selected 2 (1593 ms); reconcile 245 ms. Job DONE; selection seq 1 -> run `4168fb05-b35e-46dc-93bd-77f236f236f8`;
  match pass `95ad1958-be2f-4fe1-b6d8-f51a910f9440` (through seq 1, 1 revision written).
- Finding `97fdae9e-1a18-4fd9-89c4-b9cea4a31ab5`, r1 `7622d2e9-d1a3-4e67-af86-085014c3a9a7` (rev 1, SUPPORTED,
  OPENED, run `4168fb05...`). Work: ASSUMPTION_PUBLISHED `52198ef2-...` (attempt `94629f7f-...`) and r1 FRA
  `09755132-...` (attempt `4d6a2ca4-...`) both SUCCEEDED with consequence 1
  `35cb1fad-c003-4940-b4f1-5c7be5b8e67f` CURRENT `QUANTITY_UNAVAILABLE/POWER_COVERAGE_GAP` (examined 22).
  N5 precondition: `[07:00, 07:05)` lies inside r1's observed Candidate time: passed.
- After tick 1: seam **CURRENT** (watermark seq 1, input `ce483bef...`, config `608aab42...`), health IDLE, heartbeat
  17:44:30.199Z.
- **Tick 2 (idle)**: s3 processed 0, s4 `SKIPPED_UNCHANGED_FENCE`, consequence selected 0; pass rows unchanged (1);
  heartbeat advanced to 17:44:41.858Z.

## 2. Late acceptance (no tick yet)

- Late delivery (same credential, TLS): batch `babc9d87...183a`, source sequence 14, accepted evidence
  **`4b39dd00-2da7-4e74-9e4b-c904fdf119ef`**. New S3 job `27b8d7ac-5a49-4fb0-959f-8d644a4fb701` PENDING.
- Exactly one EVIDENCE_ACCEPTED work row **`117df2d6-93c7-4b1e-b316-a03710ddc1aa`** for r1, affected
  `[07:00, 07:05)`, no attempts.
- **Pre-tick read (r1): `STALE ['TECHNICAL_INPUT_CHANGED']`**, head consequence 1, `pending_work` = [`117df2d6...`],
  bridge `STALE_QUEUED`.
- Seam `STALE_PROJECTION` stage S3 (`S3_STALE_PROJECTION, LIVE_JOB, CONSEQUENCE_STALE, WORK_OUTSTANDING`); health
  BACKLOG (S3 1, consequence 1), heartbeat unchanged 17:44:41.858Z.

## 3. Tick 3: the first post-release tick completed S3, S4 and the drain

- **Tick 3** (DB now 17:44:49Z): COMPLETED; s3 OK processed 1 (1386 ms), s4 MATCHED (1757 ms) appending r2,
  consequence OK selected 2 (1223 ms). Job `27b8d7ac...` DONE; selection seq 2 -> run
  `6a77e15d-0a9b-44a6-a105-5e8955a81d56` (175 inputs); pass `bd1af84c-a15f-42b3-98ca-2ca05fa04067` (through seq 2).
- r2 **`1b8eb2ea-b54f-4f14-bfe3-ffe7d67a3f47`** (rev 2, SUPPORTED, SUPPORT_CHANGED); its run cites the late ID.
- **r1's EVIDENCE_ACCEPTED attempt `3e96c34d-566a-411e-87ca-dbd107a05906`: SUCCEEDED, typed no-op
  `FINDING_REVISION_SUPERSEDED`, no consequence revision.** The same-revision Leg A state
  (`POWER_NOT_IN_ASSESSMENT_INPUTS` on r1) did not arise and was not required: it is S4-02c's evidence
  (`.agent/S4-02c-walkthrough-evidence.md` section 2, consequence `87a04e1a-...`).
- r2 FRA work `82655ea6-4983-4020-a765-2b85e1e0a8ac`, attempt `a7a06c24-82fa-4776-a0ac-e641a52fbfef` SUCCEEDED ->
  consequence **`41623c49-ea73-444e-a410-58d87639c9fc`** (r2 #1) CURRENT **PRICED** by price v1: 23 counted means,
  12.65 L, amount high 15.8125 USD; late ID examined and in the run inputs. Same numbers as S4-02c Leg B.
- r1 now `HISTORICAL ['FINDING_REVISION_SUPERSEDED']` with consequence 1 only.
- Seam after tick 3: **CURRENT** (no live job, no work), watermark seq 2, input `f31b2ccb...`, selected run is r2's
  run. It was not CURRENT at any read between the late acceptance and the end of tick 3. Health IDLE.

## S3 status and limits (M5)

Source-ordered variant (the positive path): S3 `CURRENT`, no `SEQUENCE_ORDER_INVERTED` or
`GENERATOR_SERIES_AMBIGUOUS`; the window's only limitation is `INTERVAL_LIMITED ... OPEN_BOUND: no OFF evidence after
the interval in the read range`, before and after the late mean. The run-1 (gateway intake numbering) inversion is
recorded by S4-02c and owned by F1 (`I-late-reading-series-and-money-limit`). The tool asserts only the seam's
upstream state; the consequence read's money predicate (`s5_money_eligible` = true) is recorded, not asserted, and
does not decide S5 money.

## 4. Replay, stopped worker, recovery

- **Tick 4 (replay)**: s4 `SKIPPED_UNCHANGED_FENCE`, consequence selected 0; no new pass, work row or consequence
  revision; no duplicate `(finding_revision_id, consequence_basis_sha256)`.
- Stopped worker (fresh process, thresholds `stop_after_seconds=1`, `site_stop_after_seconds=1`, 2.5 s after the
  last tick, DB time): health `STOPPED` (`HEARTBEAT_STALE`, Site `SITE_VISIT_STALE`); seam `STALE_PROJECTION`
  stage `SCHEDULE` (`SCHEDULE_STOPPED`, `SITE_VISIT_STALE`) with 0 live jobs and 0 work: queue-empty is not CURRENT.
- **Tick 5** recovers: seam CURRENT, health IDLE, heartbeat 17:45:20.576Z.

Tick wall time on this Windows host: 10-13 s each (three stage children of about 1-1.7 s, plus discover and store
calls); reconcile 245-409 ms.
