# OWN-G1 phase 2 handoff (PARTIAL: rehearsal stopped on a non-KIS row, F-THREADS)

Branch `task/OWN-G1-add-dates`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-g1`. Phase 1: `.agent/OWN-G1-phase-1-handoff.md`.
Spec: build sheet OWN-GAPS §4 (Rev 1), R2-G1, R3.7/R3.8 (in `AssetOpsV1-plan2/.agent/`). Coordinator ruling: clone DB
`assetops_demo3_g1audit_test`, work folder `var/demo3_g1audit`.

## Step 1 — merge main (done)

- `3609ed5a2` merges main `b73c65eb6` (G3a, G2, G3b). No conflicts. `tools/demo_combined.py` (G2 `Demo.tick` returns the
  report + `retry_until_visited` in `after_children`; G3a serve env) and `tools/demo_combined_finish.py` (KIS-11)
  auto-merged; G1's `kisiwa_stage` reads the same report shape as G2's `demo_rows.fuel_night_entry`.
- No-DB set (21 files, incl. `test_own_g1_add_dates.py`, `test_k7_kisiwa_story.py`, G2/G3 no-DB files, demo_combined
  files, `host/tests/test_own_g3_entry_env.py`): **466 passed, 5 failed**. All 5 fail on main too (the files involved are
  identical to main or the failure is main's): `test_demo_combined_mill.py` x2 and `test_ch5c_env_parity.py` x1
  (phase 1, same on main); `test_ch5c2_clock_guard.py` (G2's `postgres_fuel_balance_store.py:254 schedule_inputs` SQL
  clock read; backend identical to main); `test_k7_kisiwa_story.py::test_carry_r3k2_l2_no_kis_row_keeps_the_skip_branch`
  (expects 12 `raise KisiwaMissing()`, main's KIS-11 made it 13; main's copy of the test has the same 12).
- Guards: `check-architecture.ps1` passed, `check-agent-workflow.ps1` passed.

## Step 2 — rehearsal (stopped after run 1)

Setup (R2-G1 Q4): no serve was running; `CREATE DATABASE assetops_demo3_g1audit_test TEMPLATE assetops_k9_audit_r3u`
(head `0058`); robocopy `AssetOpsV1-k10\var\demo3_r3u` -> `var/demo3_g1audit` without `tree`; `tree` = `git archive` of
`3609ed5a2` (prepare's parts + `var/sites/kobo-001.yaml`, 1888 files); `evidence_migration run` (KOBO-001) and
`performance_migration run` (KOBO-001, KISIWA-001): all "cutover: permitted". Clone S = 2026-11-06; last Kisiwa night
2026-11-06, so `--to 2026-11-08`.

- At 22:38Z (01:38 local) `--to 2026-11-08` refused `DATE_NOT_PAST ... yesterday (2026-11-07)`: EV-LAB-001 is
  `Etc/UTC` (R2-G1 header), so its yesterday was 11-07. Correct behaviour; the run waited for 00:00Z.
- Step 3 (`--to 2026-11-09`, run early): `DATE_NOT_PAST: Data can be added only up to yesterday (2026-11-08).`; work-folder
  file hashes and 8 table counts identical before/after (nothing written).
- Run 1 at 00:01Z, wall 1926 s (check 03:14-03:33 local = 19 min). Free RAM 3.4-4.2 GB; never under 1 GB. Output:

```
add-dates plan: {"KOBO-001": ["2026-11-08"], "EV-LAB-001": [], "KISIWA-001": ["2026-11-07"]}
added KOBO-001 2026-11-08 normal (not checked yet: the next serve tick assesses it)
{"added": [{"site": "KISIWA-001", "date": "2026-11-07", "kind": "normal", "ticket": null, "records": ["REC-000029", "REC-000030"], "checked": "WITHIN_MARGIN (revision 1)"}, {"site": "KOBO-001", "date": "2026-11-08", "kind": "normal", "records": [], "checked": "tick COMPLETED"}], "skipped": [{"site": "KISIWA-001", "date": "2026-11-08", "reason": "NIGHT_NOT_OVER", "text": "the night is not over yet (it ends 15:00 local)"}], "left_empty": {}, "no_session": [], "finish_check": "FAIL F-THREADS"}
KOBO-001: added 8 Nov (normal); checked by the background refresh.
KISIWA-001: added 7 Nov (normal); the night checked: within margin; 8 Nov the night is not over yet (it ends 15:00 local).
This build no longer passes its checks; prepare a fresh one before a demo.
```

  Counts before -> after: accepted_evidence 93284 -> 98140, evidence_publication 18666 -> 20502, operational_record
  13 -> 15, fuel_balance_window 10 -> 11, finding_revision 19 -> 19, analytic_run 122 -> 125, site_day_snapshot 784 -> 799.
- `check.json` (51 rows): 50 pass, **F-THREADS fail**: `AssertionError: {'KOBO-001 2026-11-08': ['PRODUCER_NOT_SETTLED']}`.
  Every KIS row passes, incl. KIS-4, KIS-6 and KIS-11, so no KIS bound was applied (step 3 of the brief not needed).
  F-COH and CO-2 pass.

## Why it stopped

R2-G1 Q3: a non-KIS failure stops the work and goes to the Architect. F-THREADS (`demo_combined_finish.py:856-891`)
reads every `days.json` board, now including the added Kobo day, and fails on its UNKNOWN / PRODUCER_NOT_SETTLED rows.

Observation, not a ruling: the Kobo day is added with `assess` = late (`_add_core_day`, `tools/demo_combined.py:1018`:
`drain_mini` only for `assess == "build"`); §4.4 then runs exactly one tick (`tick_and_verify`, :1150) and no mini drain.
`prepare`'s finish runs `tick(times=2)` plus drains, and `serve` drains continuously. The board's MG settledness needs the
settled board day and mini-depth (`site_outcomes/mini.py:525-544`). Likely the added Kobo day needs a drain (and/or a
second tick) before `finish check`; §4.4 does not say so. Not tested: the clone was left exactly as run 1 left it.

## State left for the Architect / reviewer

- Clone DB `assetops_demo3_g1audit_test` and `var/demo3_g1audit` kept (check.json, logs 41-56, kisiwa-days.json).
- Not done: rehearsal step 2 (second identical run), `chain_coherence`, review packet, CODE_STATE/ACTIVE_CONTEXT.
- Resume after a ruling: apply it (no-DB case), rebuild `tree` from the new HEAD (scratch script recipe above), then
  run 2 of the same command, `finish check`, `chain_coherence collect --work var/demo3_g1audit --database-url ... `
  + `check` (EX-2 = 0), then the packet `.agent/review-packet-G1.md`.
