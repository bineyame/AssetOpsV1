# DD-1b2b rehearsal handoff (step 6 done, self-check failed; steps 7-9 NOT done)

Prepare ran once at HEAD `1dd70bc78`: DB `assetops_demo3_dd1b2_test`, work `var/demo3_dd1b2` (both kept). Started 11:17:41Z, ended 12:17:27Z, exit 1 (SELF-CHECK FAILED). No process is running; keep-awake PID 23468 (started by this builder, watches a dead PID, exits by itself) and the Docker Postgres are all that remain. Nothing in the repo changed after the prepare started. Logs (scratchpad `...\f4febd4c-9675-4106-956a-a7689855586a\scratchpad\`): `rehearsal-prepare.log`, `rehearsal-mem.log`, `rehearsal-mem2.log` (30 s RAM samples; the first monitor was replaced at 11:30Z because it looked at the top-level logs folder only, which is quiet during Kobo runs; the second covers 11:30Z to the end), `rehearsal-start.txt`, `rehearsal-end.txt`.

## MEASURED
- Wall 3584.9 s of 10800 (manifest `wall_seconds`). Kobo 1479.8, Cold 21.7, EV 27.0, tree 10.0, after_children 951.5. Steps: mini-depth 524.8, backfill-a 33.8, mill 18.7, backfill-bcd 2.2, drain-1 278.4 (3 ticks, N=4, over_n false), finish-ticks 202.5, drain-2 58.3 (1 tick, N=2), finish-rows (self-check) 735.7.
- Lowest free RAM 3.07 GB (12:09Z, during drain-2/self-check); never under 2 GB. Postgres container up to ~0.97 GB.
- Mill step: `ACT-000004 VERIFIED study LIMITED 5 eligible`. MILL-3 passes: 42.00 -> 110.00, outcome count 1, origin_opportunity_id set. Mill thread events: OPEN, ACTION_IN_HAND, CHANGE_APPLIED, RESOLVED_MONITORING, **RECURRED** (it recurs; the source study and effective day are not yet read).
- Prebuild: 0 non-200 both times (23 requests). F-DRAIN, F-COH3, MILL-3, MONEY-B, WK-2a, CO-1/1b/2/3, SP-3/5/6, CO-6b/7/8/9/10/11/12, WK-3 pass (20 pass).

## The 12 self-check failures (first look; not yet traced; no fix attempted)
| Row | Error | First classification |
|---|---|---|
| F-COH | 4x COH-10: thread `kobo-headroom` shows 2 occurrences on findings_opp and portfolio, week and month | A COH finding other than the named COH-17/COH-2: R6 section 7 stop to the Architect. Likely the recurred thread appears twice (product), not a tool fault |
| CO-5/SP-1, CO-5/SP-2, CO-6, WK-4 | MG-2 / CC-1 / CC-6 `UNKNOWN, OBJECTIVE_NOT_JUDGED`; CC-5 NO_OBJECTIVE_DECLARED; MG-1 NOT_JUDGED "sales not recorded", Kobo S days 0 complete / 3 partial / 2 no_data | Objectives were declared (6 lines, `objectives.json`) yet the boards do not judge them. Possible backend/data cause (days partial, not complete); not a wire-shape bug. Needs Architect |
| SP-4 | finding-index gaps are 2026-10-06..14, 11-01, 11-03 (all UNASSESSED) but not S-10 (2026-10-26, kind `missing`) which the row asserts | Unclear: row expectation vs product; Architect |
| WK-1 (`{}`), WK-2b (None), WK-2c ("Productive-use headroom Opportunity"), WK-6 (`[]`, 2026-11-06) | assertion text only; same partial-day/not-judged data | Probably the same root cause as the objectives group; unverified |
| F-CAL | `AttributeError: 'NoneType' object has no attribute 'replace'` | Probable tool fault: days.json's `missing` day (2026-10-26) has no `start`; `f_cal` calls `at(d["start"])` for every Kobo day before filtering. Fixable at step 7 (commit tool fix, copy into `tree/tools/`, rerun `check` in the tree form) |
| F-THREADS | `AssertionError: None` | Needs a traceback; run in the tree form |

## Where to resume
Owner approval covers one run; **the DB is kept and no second prepare may start.** Next: report to the coordinator/Architect with the table above (the COH-10 and OBJECTIVE_NOT_JUDGED items are stops under R6 section 7 / R8 C3 "backend faults are a stop"). If ruled to go on: fix F-CAL in `tools/demo_combined_finish.py` (Write/Edit only), copy into `var/demo3_dd1b2/tree/tools/`, rerun `check` in the tree form (handoff `DD-1b2b-handoff.md` step 7), then the owed items (O8 recurrence reads, `tools/demo_combined_after.py` not yet written, EX-1 S+2 renewable-selection check, `perf_budget --story`, clone `assetops_demo3_dd1b2c_test` / `var/demo3_dd1b2c` and EX-1 at or after 11:05Z on S+2 = 2026-11-07, which has already passed for today), packet `.agent/review-packet-DD-1b2b.md`. S = 2026-11-05T00:00:00Z.
