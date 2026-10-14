# S4-02d phase 1 handoff (bounded orchestration and storage)

Branch `task/S4-02d-analytic-finding-worker-schedule`; phase 1 commits `7851b4da` (build), `68109a9d` (tests),
then the closeout commit (probes, questions, this handoff, CODE_STATE). No timer installed; no owner-facing copy.

## What landed (file anchors)

- `backend/migrations/versions/0013_schedule_state.py`: `schedule_tick_head` (PK environment), `schedule_site_head`
  (PK tenant/Site, FK `site(tenant_id, id)`), `schedule_cursor`, `schedule_enrolment` (FK to site). One row per
  environment/Site; claim shape CHECKs; no trigger. Downgrade drops the four tables.
- `backend/assetops_backend/scheduling/adapters/postgres_schedule_store.py`: the eighth writer. Expiring claims
  (`claim_tick`, `claim_site`: taken when token NULL or `lease_until < clock_timestamp()`; every later write names
  the token), `finish_tick` (heartbeat), `fail_tick` (back-off, no heartbeat), `release_tick`, `set_cursor`,
  `set_stage`, `record_s3/s4/consequence`, `release_site` (completion or first failure + back-off), `enrol`,
  reads `site_inventory` (imported Sites, lifecycle, `has_evidence` = any `accepted_evidence` row, enrolment),
  `tick_head`, `site_head(s)`, `cursor`, `db_now`. Own engine carries `statement_timeout`/`lock_timeout`.
- `scheduling/ports.py` (ScheduleStore port), `scheduling/composition.py` (only adapter importer; registered as
  domain `scheduling` in adapter isolation).
- `scheduling/stages.py`: stage child `python -m assetops_backend.scheduling.stages discover|s3|s4|consequence
  '<json>'`; typed codes OK/MATCHED/SKIPPED_UNCHANGED_FENCE/FENCE_MOVED/MATCH_EVIDENCE_NOT_ACCEPTED/TIMEOUT
  (SQLSTATE 57014/55P03)/UNAVAILABLE/FAILED/CONSEQUENCE_CLAIMED. S4 skips when head version == `MATCHER_VERSION`
  and the current `_fence` equals the stored one; completed fence = applied fence + own revisions.
- `scheduling/tick.py`: `TickLimits` (S3 bound < 300 s lease; statement timeout < every stage bound),
  `StageRunner` (child per stage, `PGOPTIONS` timeouts (N2), killed at bound -> TIMEOUT; `overrides` for fault
  injection), `select_sites` (active predicate + EXCLUDED_WITH_WORK), `fair_order` (cursor), `ScheduleTick.tick()`.
- `scheduling/run.py`: `tick | enrol | heads` operator CLI (UUID tenants, no demo restriction).
- S3: `postgres_assessment_store.lease_job(..., tenant_id=, site_id=)` scopes both UPDATEs; new reads
  `live_jobs(analytic, domain, tenant?, site?)`, `job(tenant, site, job_id, analytic)` (with `live`).
  `assessment_worker.run_once(tenant?, site?)`, `run_site(tenant, site, limit)`.
- S4: `finding_service.MatchOutcome.fence` (the fence the pass applied under).
- Consequence: `postgres_consequence_store.pending_work_sites()` read.
- `assess_dispatch requeue --tenant-id --site-id --job-id` (N5): only a live FAILED dispatch job of that Site;
  re-enqueues its exact window via `enqueue`; exit 2 otherwise.
- Guard: `tools/checks/configuration-persistence.ps1` rule 8 comment "S4-02d adds the eighth writer, the schedule
  store ..." with `$scheduleWriter`, `$scheduleTables`, `$scheduleUpdates` (named columns per table), line rules
  for the writer (no DELETE/TRUNCATE/DDL/`DO UPDATE`; INSERT only into the four tables; each UPDATE one line with
  literal SET list, every column named), reverse ownership for all modules, non-vacuity entries.

## Proofs

`backend/tests/test_s4_schedule_tick_postgres.py` (7 tests, DB `assetops_s402d_test`): two tenants + PLANNED
KOBO-001 + gateway-only exclusion (N4) + newly enrolled Site + DECOMMISSIONED-with-work reported + cross-tenant
enrolment refused + Site-scoped leasing; 6 Sites/4 jobs with `max_sites=2, s3_jobs=1` over the cursor; idle ticks
zero rows, new selection exactly one pass, FAILED day-B window unchanged and not CURRENT while day A advances,
requeue by job ID and supersession; FENCE_MOVED vs MATCH_EVIDENCE_NOT_ACCEPTED with streak; concurrent ticks and
a held Site claim; crash with expired claims and an expired S3 lease, replay appends nothing; real children: hung
S3 killed (job LEASED ~5 min, exposed), recovery, server-side lock timeout in S4 and in discovery (tick FAILED,
no heartbeat, RETRY_DUE, recovery). Mutation probes: `.agent/S4-02d-phase-1-probes.py guard|tests`.

## Next (phase 2)

Health/report (`RUNNING|BACKLOG|RETRY_DUE|FAILED|STOPPED|idle`, alarms on `claim_skips`, `fence_moved_streak`,
`consecutive_failures`, stale claims, consequence attempt growth, `STALE_NO_WORK`), the S5 seam, timer install
behind F1 and `backend/README-db.md` runbook retiring the per-Site consequence timer, DB-clock skew proof (I3).
Questions with conservative choices: `.agent/S4-02d-questions-1.md` (heartbeat vs Site failures is the one the
seam depends on).

## Open risks

- Stage children cost ~1-2 s start-up each on Windows; a tick of N Sites spends ~3N child starts. Bound with
  `max_sites`; measure on the demo host before choosing cadence.
- `reconcile_all()` stays global and unbounded; its time is recorded per tick (`last_reconcile_ms`).
- One-off CLIs (`process-jobs`, `match-findings`, consequence `run`) bypass the schedule Site claim (Q5).
- S3 lease/cutoff and matcher `now` remain app clock (Q4).
