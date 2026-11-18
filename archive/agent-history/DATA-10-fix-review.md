# DATA-10 fix review (gate item 2) — ACCEPT WITH NOTES

Reviewed: fix/DATA-10-generator-plan, `git diff 8dbf5a317 HEAD` (d2c4d2658 + 78d45563f packet). Code not edited.

## Verified
- Date/timezone: `plan_fact` turns `next_due_at` into the Site-local date via `due.astimezone(tz or utc).date()`;
  `day_month` formats that local date. Kisiwa's 2026-11-20T21:00Z renders "21 Nov" in Africa/Nairobi. The test
  fixtures use exactly this shape (T(30,21) = 30 Oct 21:00Z gives "due 31 Oct"), so the local-day rollover is pinned.
- Overdue comparison: `p.due_at < to` uses the UTC instant against `end` (local 00:00 D+1). That is the same `to`,
  `tz` and suffix that mini passes to `warning_facts` (mini.py:703-704), and the same rule as `plan_due_state`
  (`next_due_at < to`). So the generator line and PLAN_OVERDUE / PLAN_DUE_SOON cannot disagree: on board day 20 Nov
  Kisiwa reads "due 21 Nov", which matches the warning's "Due 21 Nov". The wording matches cold.py `_plan` (l.397-400).
- Range: mini has no ranged compose. `read.compose` calls `mini.compose(day=...)` and ignores lo/hi, so `end` is the
  only window end, and no ranged mini caller exists to pass a different `to`. Cold/EV keep their own `_plan(..., hi)`.
- Wire: `asset_type` is the same plan-wire field cold.py reads (cold.py:66,179). `PlanFact.asset_type` is defaulted
  and last, and `_protect`'s new args are defaulted (its only caller is mini).
- Precedence: plans_failed gives Not loaded; then a RUN_HOURS plan wins; then a CALENDAR GENERATOR plan; then NO_GEN_PLAN. All four are tested.
- Checks run (PYTHONPATH = worktree): test_out_b2_mini + test_out_b1_board + test_out_b3_cold_ev gave 95 passed in 1.34s.
  Not run: check-all (coordinator), Postgres tests, frontend (the packet says no frontend test pins the text).

## Findings
- Low — backend/tests/test_out_b2_mini.py:552-558: no test covers the boundary `due_at == to`. For example, T(20,21)
  on DAY 20 Oct must read "due 21 Oct", not overdue, and this is the exact Kisiwa-on-20-Nov case. Neither the
  depth-refused path (UTC date plus UTC_SUFFIX) nor a plan with `next_due_at` None (filtered out, so it falls to
  NO_GEN_PLAN) is tested. The code is correct by inspection; a boundary test would lock in agreement with PLAN_DUE_SOON.
- Low — mini.py:1208: the CALENDAR branch drops a plan with no due date. cold `_plan` would show it as "{title} due date
  not recorded", but mini shows "No preventive plan recorded". That is defensible (a CALENDAR plan always has a
  due date on the wire) but differs from the cold wording; a note only.

No High/Medium findings.
