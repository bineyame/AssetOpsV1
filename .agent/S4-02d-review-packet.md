# S4-02d review packet: analytic and Finding worker schedule (all three phases)

Task `tasks/S4-02d-analytic-finding-worker-schedule.md` (registry node `I-analytic-finding-worker-schedule`).
Branch `task/S4-02d-analytic-finding-worker-schedule` from main `0d137768`. Phase reviews: phase 1 ACCEPT with
carries (`.agent/S4-02d-phase-1-review.md`), phase 2 ACCEPT with findings fixed on the branch
(`.agent/S4-02d-phase-2-review.md`). Handoffs `.agent/S4-02d-phase-{1,2,3}-handoff.md`.
USER_REVIEW_REQUIRED: **false** (operations/read-contract only; no owner-facing copy, panel or visual state). A fresh
independent implementation review of phase 3 and the F-A..F-D fixes is still required.

## Outcome delivered

- One environment tick (`python -m assetops_backend.scheduling.run tick`) enumerates persisted active Sites,
  bounds and rotates them with a durable cursor, and per Site under a DB claim runs S3 (Site-scoped leasing) ->
  S4 only on a new matcher version or moved fence -> the consequence drain, each in a killable child with
  server-side statement/lock timeouts; DB time throughout (phase 1, I3 for scheduled work).
- Migration 0013 and the ratified eighth writer with the rule-8 amendment (phase 1, F1 hardening phase 2).
- Read-only health report with typed alarms and the S5 upstream currentness seam (phase 2); phase 3 adds
  `S3_STALE_NO_JOB` and `requeue --day` (F-A).
- Gated install templates and the runbook retiring the per-Site consequence timer (phase 2); nothing installed.
- A late accepted reading reaches a revised FindingRevision and a CURRENT PRICED consequence by ticks alone
  (phase 3 walkthrough, `.agent/S4-02d-walkthrough-evidence.md`).

## Files materially changed (`git diff --stat 0d137768..HEAD`)

`backend/assetops_backend/scheduling/` (new: `tick.py`, `stages.py`, `health.py`, `upstream.py`, `run.py`,
`ports.py`, `composition.py`, `adapters/postgres_schedule_store.py`); `backend/migrations/versions/0013_schedule_state.py`;
S3 `adapters/postgres_assessment_store.py`, `assessment_worker.py`, `assess_dispatch.py` (requeue `--job-id|--day`),
`analytics/composition.py`, `finding_service.py`; consequence store `pending_work_sites`/`db_now`,
`recompute_consequences.py` (DB-time default); `backend/deploy/schedule/*`; `backend/README-db.md`;
`tools/checks/configuration-persistence.ps1` (rule 8); `tools/schedule-install-gate.py`;
`tools/s402d_tick_walkthrough.py`; tests `test_s4_schedule_{tick,health}_postgres.py`,
`test_s4_schedule_upstream_unit.py`, `test_s4_schedule_install_gate.py`.

## Acceptance criteria status

| Packet item | Status | Evidence |
| --- | --- | --- |
| 1. Inventory, cadence, fair bounded tick, Site-scoped lease, reconcile every tick, conditional S4 | Met | Phase-1 review rulings; `test_s4_schedule_tick_postgres.py`; walkthrough ticks 2/4 skip S4 with no pass row |
| 2. Cross-host claims, timeouts, retry/back-off, typed `FENCE_MOVED`, FAILED S3 requeue | Met | Phase-1/2 reviews (F2, F3, N3, N5); DB stall and nonreturning stage injected |
| 3. Migration 0013, sole writer, rule 8, health | Met, with F-B carry | Rule 8 line-based (F-B); health incl. `S3_STALE_NO_JOB` (F-A) |
| 4. S5 seam (status, basis, watermark, jobs, match, consequence, schedule, DB time, eligibility) | Met | `scheduling/upstream.py`; phase-2 tests; walkthrough seam reads |
| Phase 2 install gate and runbook (retire per-Site timer) | Met | Gate CLOSED for demo/pilot; F-C timeout; nothing installed |
| Phase 3 tick-only walkthrough (first delivery and all steps by ticks; accepted ID; pre-tick STALE/TECHNICAL_INPUT_CHANGED; r1 `FINDING_REVISION_SUPERSEDED` no-op; r2 CURRENT; cites late ID; seam eligible only after work; IDs, watermarks, backlog, heartbeat, replay, stopped worker; command-log grep incl. `recompute_consequences run`; S3 limits; source-ordered positive path) | Met | `.agent/S4-02d-walkthrough-evidence.md`: 23/23 checks; grep 0 hits, mutation caught |
| N6: first post-release tick completes S3 and S4 | Met (observed) | Tick 3: s3 processed 1, s4 MATCHED r2, drain selected 2; a non-completing tick would be reported, not asserted |
| I4 two-chunk race | Met at independent review | Phase-2 review: 48 polls, 0 false CURRENT, no unresolved lock |
| I3 DB time | Met except one comparand | S3 cutoff (DB) vs `decided_at` (app clock) stays open (carry 2); visible via `S3_STALE_NO_JOB` |

## Checks run

CHECKS_PLACEHOLDER

## Known deviations

1. `requeue --day` is new operator surface beyond the reviewer's minimum F-A ask; added so the new alarm has a
   recovery through the existing `AssessmentStore.enqueue` path. It refuses unless the day is STALE with no live job.
2. `S3_STALE_NO_JOB` fires for any STALE day without a live job, including a model/configuration change in the
   seconds before the next tick's reconcile enqueues it (transient, fails closed).
3. The walkthrough's positive path uses the SOURCE_ORDER variant as the packet requires; it never shows the
   same-revision Leg A state (cited from S4-02c) and does not exercise run-1 numbering (F1's).
4. Phase-2 conservative choices 1-5 (handoff) stand as accepted by the phase-2 review.

## Carries

1. **F-B (guard owner, or a scoped fix round):** rule 8 is line-based; multi-line/concatenated SQL, comment
   whitespace, `MERGE`, lowercase `copy` and SQLAlchemy Core `insert/update/delete` evade every writer's rules.
   Needs a statement-level guard (`ast` string extraction, joined concatenations, comments stripped).
2. **Evidence-owner packet (I3):** stamp `ingestion_disposition.decided_at` from the database, or have acceptance
   create a new job when a widened PENDING job's lease could predate the decision. I3 stays open for that
   comparand; the same skew delays (self-heals) the configuration `recorded_at` vs DB-clock reconcile.
3. Health `STALE_NO_WORK` and `S3_STALE_NO_JOB` scans grow with Findings and assessed days: bound or cache them
   before health runs on a timer or behind an API.
4. S5-01: present `S3_UNASSESSED` days as a gap (deviation 5 of phase 2), apply the `source_open` gate and the F1
   money rule on top of the seam, hold one seam instance per process.
5. Measure tick cost on the demo host before choosing `--max-sites` (Windows: ~1 s per stage child).
6. Install gate: no owner-visible tick before `I-late-reading-series-and-money-limit` resolves.
7. Registry/CODE_STATE: record I4 as proved at the phase-2 review when the slice closes.

## Residual risk

- One-off S3/S4 CLIs still use the app clock and bypass the Site claim (runbook: stop the tick first).
- S4-02c consequence retries have no terminal cap; alarmed at 5 attempts, not stopped.
- The walkthrough runs on one Windows host with one Site; per-tick limits that fit here may not on the demo host.

## User-review focus

None required (USER_REVIEW_REQUIRED false). Reviewer focus: F-A alarm correctness and `requeue --day` refusal
paths; the walkthrough's command-log grep coverage; that no owner-facing text changed.
