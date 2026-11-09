# OWN-G1 phase 3 handoff (STOPPED on R5 stop condition: non-PASS rows CO-2 and WK-6)

Branch `task/OWN-G1-add-dates`. Commits on top of d9540c26c: 776f4fc03 (R5.2 settle in tools/demo_combined.py),
1fb1bb959 (9 no-DB tests), then the K7 12 -> 13 commit (R5.6). No-DB: G1 file 36 pass; adjacent 16 files + host g3 env
432 pass, 4 fail (mill x2, ch5c_env_parity, ch5c2_clock_guard = the expected pre-existing ones). Must-fail proof: removing
`drain_mini` from `settle()` fails 3 tests; reverted.

## Rehearsal step 1 (reused clone assetops_demo3_g1audit_test / var/demo3_g1audit)

1. `tree` rebuilt from HEAD 8cd2e29b2 (old tree removed; 1888 files). Same command
   `add-dates --site KOBO-001,KISIWA-001,EV-LAB-001 --to 2026-11-08`:
   plan nothing new; printed "settling work left from an earlier run"; mini-depth 94 jobs; `settle-close` tick 1/N=2 total 0,
   drained in 1 tick (119.2 s); verdict done (saved `settle-close-attempt1.json`). The settle fix and resume path work: the
   Kobo 11-08 and Kisiwa 11-07 queues (24 and 70 mini jobs) are gone and the Kobo F-THREADS row on 2026-11-08 no longer fails.
   Finish check FAILED 9 rows (saved `check-resume-attempt1.json`): CO-2 returned 409 AWAITING_EVIDENCE_MIGRATION, and
   the cascade (PRODUCER_NOT_SETTLED, KIS-7/CH5D1-O1 priced Sites empty, F-THREADS on many old Kobo days). Cause: deleting
   `tree` also deleted the file-backed legacy comparison report (bound to the tree's store). Fix: re-run the setup
   migrations (scratchpad g1/migrate.py: evidence_migration KOBO-001, performance_migration KOBO-001 + KISIWA-001; all
   "cutover: permitted"). NOTE for any rebuild of `tree` on a clone: re-run the migrations afterwards.
2. Re-run of the same command after migrations: plan nothing (Kisiwa 11-08 not over), counts all 0 so no settle, finish check
   51 rows, **49 pass, 2 FAIL** (`check.json`):
   - **CO-2**: `STALE_PROJECTION / SCHEDULE_STOPPED, SITE_VISIT_STALE`; heartbeat age 1405 s against threshold 300 s
     (last tick was the settle-close tick, about 23 min before the check). Finish check assumes a tick in the last 5 min;
     a run with nothing to add and nothing pending ticks never, so a later "run B" will fail CO-2 by wall time alone.
   - **WK-6**: `('2026-11-08', '2026-11-07')`: the Kobo productive-use opportunity list now has a newer opportunity ending
     11-08 (the added Kobo day), but the row expects `last_day == S+1` (2026-11-07). Same class as the KIS story-calendar
     bound but for a non-KIS row; R2-G1 Q3's pre-authorised bound covers KIS rows only.

## Stopped per R5 ("any non-PASS row" back to the Architect). Questions for the Architect

- WK-6: bound the row to the story calendar (as done for KIS rows) or read the latest opportunity within the story window?
- CO-2 / run B: should add-dates always run one tick (heartbeat refresh) before `finish check` even when nothing is added, or
  should the check tolerate a stale heartbeat for a build with no serve running? (Run B in R5.5 step 4 says "no tick".)

## Not done

Rehearsal fresh clone (steps 2-4), step 6 read-only checks, chain_coherence, review packet `.agent/review-packet-G1.md`,
CODE_STATE, ACTIVE_CONTEXT, re-run of check-architecture / check-agent-workflow after the R5 commits, Task Status
(`in_review`). Both clone DB and folder kept (also `var/demo3_g1audit/check-*.json`).
