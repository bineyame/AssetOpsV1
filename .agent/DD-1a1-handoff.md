# DD-1a1 handoff (current: fix round 1 after the REVISE review; older text below is history)

**Current state: fix round 1 on top of R16 (see the packet).** The "builder 14" header below is history.


## Landed earlier
- R8 (builder 11), R9 (builder 12): see `.agent/review-packet-DD-1a1.md`. Helpers in `C:\Users\assef\dd1a1w\`
  (env.sh, d12.sh `<with|without>`, deg.sh, mkdb.py).

## Landed (builder 14)
- `6340405fa` R6 fix (tool only): the gateway's background uploader delivers on start, which drained the withheld half
  through later complements. Post-outage complements now start their gateway with no `upload` block
  (`tools/demo_combined_kobo.py` `publish_first_half(outage_continues, withheld_run)`; `_OUTAGE` is epoch -> story run).
  Check script: grade per story window, stray rows on any later day, no analytic-run count compare.
- `ac9655668` + `33dfe724b` R9 review Lows 1-2 in `actions/verification.py` (`meets` fails closed on an unreadable
  start; `_baseline_target` equality required for `reselected`), two tests, each proven to fail without its fix;
  fixture class fixed to `CANDIDATE_AVOIDABLE`. R9 unit + S6 verification files: 125 passed.
- R6 check (`deg_compare.log`): 1-6 PASS, 7: 0 AMBIGUOUS and findings PASS, **grade FAILS** (details and cause in the
  packet's R6 section: the delivered half follows random source-id order; the with day also holds the night
  interval). Stopped per R6. Architect question is in the packet.
- R5-R9 re-check: one `with` build (981 s) + r9/r8/r7 checks all PASS.
- All DBs dropped; no processes left.

## Landed (builder 15)
- R10: `85c8263a7` guard (`DEGRADED_DAY_HELD`, tests proven to fail); degraded check restated, all PASS; packet R6 section
  updated. Helper `dd1a1w/deg_with_only.sh`. DBs dropped. R3 L2 checks done (`tools/dd1a1_r3_check.py`, all PASS; packet). Builder 15 stopped here
  (context): mill day, Cold failure day, Q8 ruling, guards V/A/W/N/M re-run are NOT done.
- Tooling notes: `dd1a1_fullday_compare.py` already shows EQUAL for findings, actions, ACT-K1 verification, money
  tables (covers R3 checks 2-ACT-K1 and 4). Still needs a new query script on with/without DBs (`d12.sh with|without`
  leaves the DB) for: night shape (starts, fuel, unserved), MG-2 avoidable minutes, mill verdict / spare solar,
  COMPLETE grades, 06:00 jump.

## Resume here (builder 17: R12 done; Cold failure day blocked)
- R12 landed (`9e8f93ae9`): measured dusk start states, `kobo-mill-dusk`, probes S-dusk/M-dusk, `tools/dd1a1_r12_check.py`.
  Mill day and R12 checks recorded in the packet; 0 dusk starts; findings/threads/money/MG-2 equal.
- 17 guards passed before R12. The Cold failure day with full days fails (packet): Architect ruling needed. Also for the
  Architect: `steady-dusk` is unused on the B-22 calendar, steady-afternoon has a 12:05Z start per steady day.
- MILL-3 belongs to DD-1a2/1b2. Fallback if the rehearsal is over 3 h: B-16 (owner file).

## Builder 18 (R13): STOPPED, two Architect questions (packet "R13")
- Cold failure day: no Finding exists with full days; cause is the S4-05 gate (MIXED / MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS over a
  day-wide window of many runs), not (a) or (b). Needs a ruling.
- Standing checks landed (`dd1a1_r12_check.py`, `dd1a1_r3_check.py` take days.json). Seam check fails: 15:00Z +0.95 pp (equal state);
  17:00Z/03:00Z are measured-state resets. Needs a ruling. Guards A/W not run. DBs dropped. Helper `dd1a1w/r13.sh`.

## Builder 19 (R14): Part 1 done and committed; parts 2-3 NOT done
- Part 1: Cold full days removed (see packet "DD1a1-R14"); cold == cold-without proven (3 Findings, tables equal, 0 AMBIGUOUS). Helpers: `dd1a1w/r14_cold.out`.
- Part 2 WIP: `.agent/DD-1a1-r14-wip/*.wip` (copy over `tools/derive_steady_scenarios.py`, `tools/probe_kobo_nights.py`, v2 JSON; then probe, derive, `--check`).
  Design: chains N/R30/R25, files `kobo-chain-<c>-afternoon|late|early` (+R30 early split), kinds `afternoon-<c>`, `late-<c>`, `night-early-after-<c>`,
  day entries S+0 `after: N`, S+1 `after: R30`. `probe_kobo_nights.py` `chains()` ran on the template Site in 11 s.
- Blocker: probe must run on the registered Site (`--registered` mode, shifted drafter) with the 25 % reserve revision for R25. Template says the N story
  ends RUNNING (30 %, 217.65 L) and setup refuses a RUNNING start: Architect to rule if the registered probe agrees. Still to do after that: `dd1a1_r12_check.py`
  bound incl. fuel <= 0.5 L at 11/15/17/21Z with 03Z exempt and reported, Kobo with/without builds, R5-R9 re-check, guards V/A/W.

## Builder 20 (R15): STOPPED at the probe (packet "DD1a1-R15")
- Main merged (`93cd29430`). Registered-Site probe: N story RUNNING at 14:00; N/R30/R25 rest-of-day RUNNING at 24:00; mill passes.
- Nothing derived/built. WIP: `.agent/DD-1a1-r15-wip/` (derive `REST`/`rest_document`, probe test to copy into host/tests, results).
  Probe DB dropped; no processes left. Next: Architect / owner decision on D.

## Builder 21 (R16): built (packet "DD1a1-R16")
- Hybrid landed: only the mill day is full (`kobo-rest-mill`, joins STOPPED recorded in the handover `full_days`); N/R30/R25 story-only;
  guard `FULL_DAY_JOIN_NOT_STOPPED` in `tools/demo_story_days.py`. Checks adapted to full days. All DBs dropped; helpers `dd1a1w/r16_*.out`.
- DD-1a2: B-22 steady days must be probed per day and added to `full_days` (probe tool) before they may carry a complement.
