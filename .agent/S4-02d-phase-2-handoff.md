# S4-02d phase 2 handoff (health, install and currentness handoff)

Branch `task/S4-02d-analytic-finding-worker-schedule`; phase 2 commits `8cf2d147` (F1 guard) .. HEAD. No timer
installed on any host; no owner-facing copy, panel or visual state (USER_REVIEW_REQUIRED stays false). No
`.agent/S4-02d-questions-2.md` was needed.

## Phase-1 review fixes

- **F1** `tools/checks/configuration-persistence.ps1` schedule-writer block (~line 776): every keyword rule is now
  `(?i)`; DELETE FROM/TRUNCATE/DO UPDATE/CREATE|ALTER|DROP TABLE refused case-insensitively; INSERT only into the
  four tables; any `update <x> ... set` line must parse as `UPDATE <table> SET <list> WHERE` on one line, the SET list
  fails on `{}`, `"`, `%`, a backtick, a leading `(` (tuple target) or unbalanced parentheses (nested WHERE), and
  each top-level item must be `identifier = expression` with the identifier in the table's named list
  (case-sensitive, so `CREATED_AT` fails). `.agent/S4-02d-phase-1-probes.py guard`: **20/20 caught**, including the
  reviewer's seven bypass lines and the uppercase control (`F1 ...` rows).
- **F2** `test_f2_a_site_inside_its_backoff_runs_no_stage_and_the_cursor_still_advances`; the `tick.py` back-off
  mutation (`if False:`) is now caught.
- **F3** `tick.py` `_site.stage()`: `set_stage` returning False stops the Site, result `CLAIM_LOST`, no further stage;
  `test_f3_...`. `assess_dispatch requeue` without all three IDs is an argparse usage error (exit 2).

## What landed (file anchors)

- `scheduling/health.py`: `HealthThresholds` (stop 300 s, Site visit 900 s, alarms at 3 skips / 3 fence moves /
  3 failures / 5 consequence attempts), `environment_health`, `site_observation` (shared with the seam),
  `ScheduleHealth.report(environment)`; states `STOPPED > FAILED > RETRY_DUE > BACKLOG > RUNNING > IDLE`; typed
  alarms listed in `backend/README-db.md` "Health, alarms and recovery". S4 backlog = Site `fence.selection_seq` >
  last pass `matched_through_selection_seq` for every Site including ones outside the active set
  (`S4_BACKLOG_OUTSIDE_ACTIVE_SET`, review carry 5). `STALE_NO_WORK` via the consequence read per latest revision.
- `scheduling/upstream.py`: `UpstreamCurrentness.window(tenant, site, start, end, environment)`; the contract
  (inputs, outputs, eligibility, commit-safe before/after `match_state` comparison) is the module docstring. Port
  `ports.UpstreamCurrentnessRead`; builders `composition.build_schedule_health` / `build_upstream_currentness`.
  CLI `scheduling.run health|upstream`.
- DB time (I3): `stages.db_clock(url)` (schedule store `clock_timestamp()`, engine disposed per call) is the clock
  of the discover `reconcile_all()`, the S3 worker (lease expiry, knowledge cutoff, job instants) and the matcher's
  `now`; the drain already got DB `now`. One-off `recompute_consequences run` defaults to
  `PostgresConsequenceStore.db_now()` (new read) or `--now` override; summary `now_source`.
- Store: `record_s4("SKIPPED_UNCHANGED_FENCE")` clears `fence_moved_streak` (else the alarm never clears).
- Install: `backend/deploy/schedule/assetops-schedule-tick@.service|.timer` (templates headed DO NOT INSTALL);
  `tools/schedule-install-gate.py --host-class private|walkthrough|demo|pilot` reads the registry (demo CLOSED today:
  F1 node `open`); runbook `backend/README-db.md` "Analytic and Finding worker schedule (S4-02d)" retires the
  per-Site consequence timer, names `CONSEQUENCE_CLAIMED` (Q3), stop-the-tick before manual Leg B (Q5),
  `last_started_at` semantics, bounds, identities, stop/restart.

## Proofs

`backend/tests/test_s4_schedule_health_postgres.py` (10, DB `assetops_s402d2_test`): F2, F3, requeue usage; PENDING
first build -> CURRENT -> same after reload -> idle heartbeat -> STALE_PROJECTION on new evidence -> CURRENT;
stopped timer beyond threshold (seam blocked with empty queues, `SCHEDULE_STOPPED`) and recovery; FENCE_MOVED x3
alarm and recovery; MATCH_PENDING after an S4 TIMEOUT; terminal S3 FAILED (seam FAILED with job ID/error, health
`S3_JOB_FAILED` with requeue) and requeue recovery; Site leaving the active set keeps S4 backlog; repeated claim
skips (STOPPED while the environment stays IDLE, Q1) and stale crashed claim; skewed app clocks (+3 h on the S3
worker, matcher and drain modules): run/revision instants within 120 s of DB time, failed consequence work not
retried early by the tick or the one-off run, override reported, backdated config change reconciled and processed
in the same tick; `STALE_NO_WORK` with Finding/revision/consequence IDs; I4 race (below); tick cost.
`test_s4_schedule_upstream_unit.py` (5, no DB): selection moved during read, eligibility statuses, DB-time
thresholds, one-off `now_source`. `test_s4_schedule_install_gate.py` (3).
Mutation probes `.agent/S4-02d-phase-2-probes.py`: **21/21 caught** (first run 17/20: the three drain/reconcile clock
probes were missed because the skew patched `_utc_now`, which the worker binds at definition; fixed by patching the
module `datetime` and adding the reconcile scenario; reruns caught; the I4 probe was added after).

**I4** `TestOverlappingIngestionRace`: three rounds of two overlapping chunks (same S3 day window, adjacent
hours) committed by concurrent threads while a tick holds the Site claim, timed at S3 start, racing S3's lease,
and during S4/drain. Asserted: both chunks finish (no unresolved lock), they committed while the Site claim was
held, at least one round left live S3 work after the tick, the seam is never CURRENT while live work exists, and
later ticks reach CURRENT with the larger accepted basis. No ingestion defect observed; mutation "seam ignores S3"
is caught. This is the implementer's proof; the packet still asks the independent review to run its own race.

## Tick cost (real stage children, Windows dev host)

1 Site first tick 4.8 s (reconcile 223 ms; s3 1255, s4 1374, consequence 956 ms); 1 Site idle 4.1 s; 4 Sites idle
12.6 s (reconcile 271 ms). Child start dominates (~1 s each, 3 per Site); one-minute cadence fits about 12-15 Sites
on this host. Measure on the target host before choosing `--max-sites`.

## Conservative choices (for review)

1. Schedule-only blockers keep a usable result `STALE_PROJECTION` (no result: `PENDING`); S5 decides presentation.
2. Health STOPPED for a never-visited scheduled Site (`SITE_NOT_OBSERVED`) or no finished visit within 900 s; a
   visited but never-completed Site is reported by its failure/back-off state and still blocks the seam.
3. A consequence read `PENDING` (`NOT_YET_COMPUTED[_NO_WORK_RECORDED]`) blocks CURRENT like STALE.
4. Consequence work with null `affected_from/to` counts as overlapping every window (blocks rather than misses).
5. Multi-day windows with a day that has no evidence stay `PENDING`, not `UNASSESSED`.

## Open risks / not done

- I3: closed for scheduled stages, the tick, health and the seam; remaining app-clock uses are manual one-off
  `process-jobs`/`match-findings`/`assess` (unchanged S3/S4 CLIs, outside the schedule).
- `STALE_NO_WORK` scan derives a consequence per latest Finding revision on every health read (cost grows with
  Findings); per-window in the seam.
- Phase 3 (tick-only walkthrough) not built.

## Checks

- Focused: new files 18 passed; phase-1 probes guard 20/20; phase-2 probes 21/21; `tools/check-all.ps1` all 9
  guards passed. Full backend pytest: see `.ai/CODE_STATE.md` "S4-02d phase 2". Frontend unchanged.
