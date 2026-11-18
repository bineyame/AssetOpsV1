# S4-02d phase 3 handoff (automatic late-power walkthrough and slice wrap-up)

Branch `task/S4-02d-analytic-finding-worker-schedule`; phase 3 commits `62581ecd`..HEAD. No timer installed; no
owner-facing copy (USER_REVIEW_REQUIRED stays false). Slice review packet: `.agent/S4-02d-review-packet.md`.

## Phase-2 review fixes

- **F-A** `scheduling/health.py` `ScheduleHealth.stale_without_job`: for each selected UTC day (`run_heads`) with no
  intersecting live S3 job, the S3 read (`DispatchReadService.window`, now a health collaborator from
  `composition.build_schedule_health`) is checked; `STALE_PROJECTION` raises `S3_STALE_NO_JOB` (day, run ID,
  reasons) and the Site state `FAILED`. Recovery `assess_dispatch requeue --tenant-id T --site-id S --day D`
  (`_requeue_stale_day`: refused unless that day is STALE with no live job; enqueues through
  `AssessmentStore.enqueue`). Test `TestStaleWithoutJob` reproduces the reviewer's case: decision stamped DB now +
  20 s widens the PENDING job, tick completes without it, seam STALE with no job, health FAILED with the alarm;
  `--day` refused for an unassessed day and while live; after the DB clock passes the decision, requeue + tick ->
  CURRENT, alarm cleared. Mutation (alarm disabled) caught.
- **I3 residual** stated in `backend/README-db.md` (schedule section + alarm table): DB-clock cutoff vs app-clock
  `decided_at` remains; the fix (DB-time `decided_at` or a new job when a widened job's lease may predate the
  decision) is a separate evidence-owner packet. Ingestion unchanged here.
- **F-C** service `TimeoutStartSec=900` (> 780 s tick lease plus store-call slack), comment corrected.
- **F-D** install gate dedupes `needed`; pilot prints F1 once.
- `.agent/S4-02d-phase-1-probes.py` prints usage (exit 2) without `guard|tests`.

## Phase 3

`tools/s402d_tick_walkthrough.py` (subclass of the S4-02c `LateWalk`; DB `assetops_s402d3walk*`, ports 8928/8929,
environment `walkthrough`): five full ticks, no hand-run Leg B, command-log grep (mutation caught). Evidence
`.agent/S4-02d-walkthrough-evidence.md` (+ `.json`, `-commands.log`): 23 checks, 0 failed; tick 3 completed S3,
S4 (r2) and the drain; r1's EVIDENCE_ACCEPTED attempt is the typed `FINDING_REVISION_SUPERSEDED` no-op; r2
CURRENT PRICED; seam CURRENT only after the tick; stopped worker blocks the seam; recovery tick restores CURRENT.

## Open (carried in the review packet)

F-B statement-level guard; evidence-owner `decided_at` packet (I3 stays open for that comparand); health scans
(`STALE_NO_WORK`, `S3_STALE_NO_JOB`) grow with Findings/assessed days; target-host tick cost; S5-01 seam carries.
