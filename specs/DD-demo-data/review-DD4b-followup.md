# Review: DD4b follow-up (D-DD.158 EV window sums, D-DD.161 EV `session`), head 5f8a63510

Reviewer: fresh Claude (not the author). Logs: `/opt/assetecon/evidence/DD4b/followup/review/`.

## Round 1 summary
- Verdict: ACCEPT. No High or Medium findings; two Low.
- Recompute: independent script over the day files of a fresh EV-EMB run (14-16 Oct, branch code): site-meter/import summed by
  exact Fractions over local minutes gives 0000_0500 = 1368.133 and 2200_2400 = 2273.800 kWh; `measured.json` states
  1368.133 / 2200_2400 2273.800, and the day sum 7715.933 equals `import_kwh`. Match (a 3-day partial month, not the
  full October; the full 26-minute run was not repeated).
- scope_seasons: the 3 failures are not this branch's. On a temporary merge of main into head, `test_scope_seasons_parity` is 6 passed
  (`scope-merged.log`); the four new/edited DD4b test files are 31 passed on the merged tree (`new-merged.log`). Merge
  conflicted only in docs (`.ai/state/*`, `spec.md`), not code. Copy removed, worktree pruned.
- Code read: writer window sums, `read_measured` key set, `meter_billed` leaves, frame `session`, checker clause all match
  the rulings. Not rerun by me: the plants, parity, guards, backend 44 (builder's results, same code revision).

## Findings
- **Low** `tools/dd_check.py` (`check_meter_books`) and `specs/DD-demo-data/cards/DD5b.md:49-50`: deviation 1 is sound (no
  `measured.json` input before DD5b, D-DD.160), but the DD5b card names only the mini-grid clause as taking `measured.json`.
  The EV window clause is live in `judge_meter_books(measured=)` and nothing wires it in the live run. Fix: Architect adds one line to
  the DD5b card that the same fetched documents feed the EV window clause and the EV pending line goes then.
- **Low** `tools/dd_check.py` `_windows_metered`: a reading row whose span crosses local midnight is credited by the start
  minute's day only (the 22:00-24:00 window clips at 1440, and the spill after midnight is not credited to 00:00-05:00).
  The depot meter rows are 5-minute means aligned to 5 minutes, so none cross midnight and the writer has no such row today. Fix: none
  needed now; a comment or an assert that `end <= 1440` would keep it from going silently wrong.

## Deviations judged
1. Checker gets no `measured.json` until DD5b: accepted. The packet states it; the judge clause is tested (c7 plant d),
   the pending line stays in the live run (reworded), and DD5b owns the fetch. Only the card line above is missing.
2. `session` on all in-session rows (state, means, energy), DD5a copying from energy rows only: accepted. D-DD.161 says "a
   connector measurement row inside a session", the in-session test is CLOCK-1's, and j6 pins idle/FAULTED rows carry none. DD5a's
   copy-from-energy is a subset, so no conflict; DD5a's sealer must not fail on the extra key on non-energy rows (it ignores it).
   Cost: 4.9M extra `session` objects in the EV readings files (size only).

## Could not verify
Full-span parity and the 5 plants were not rerun (26-minute plant); the builder's logs are cited. Backend and guards not rerun.
