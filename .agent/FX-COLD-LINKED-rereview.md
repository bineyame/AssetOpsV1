# FX-COLD-LINKED re-review (fresh Claude reviewer, 2026-11-10)

Diff: `git diff b95fe8587..HEAD` (66298bd8e) and `main...HEAD`. Spec: D-E5.8.

## Verdict: ACCEPT (no High or Medium findings)

1. H1 closed. `cold.py:137,155,253`: rows after the selection's rows (linked-read only) get `selected=False`, so
   `in_window` is False regardless of NULL start-failure bounds. Every board consumer filters on `in_window`:
   Protect/issues `board.py:689` (signals), `707` (open_findings), `831` thread lines, `1072`; Protect contributors use
   `by_mech` filtered on `in_window` (`cold.py:156-157`). The summary/Portfolio reads board rows, so it inherits this.
   Maintenance/claims: `claims` includes the rows but is only read for Findings already chosen via `by_mech`. COH-4
   is covered in process (below). The linked rows reach only `visits.warning_facts` (open, no window filter: the
   intended repeat notice), CC-3 and link resolution (`board.py:443,942`).
2. "Force off, not anchor time" is sound: the selection read already returns every Finding anchored in [lo,hi) as of
   k, so a Finding only the linked read finds is out-of-window by construction; it also keeps "as known at k".
3. M2/M3 closed. New unit test uses `episode_bounds=None`, asserts no FINDING issue, Protect subline, Cost
   NEEDS_ATTENTION, `in_window False`. Postgres test asserts no FINDING issue on the clean and day boards, Protect not
   the start subline, summary Protect equals later Protect, and COH-4 (`coh4_findings_contain`) empty.
4. No regression: REPEATED count still 1 on summary, day board and clean board.
5. Low (note only): `must_not_harm` (`board.py:989`) iterates `moves_here`, which is not window-filtered. Text
   appears only when a linked out-of-window Finding has an Action with verification; same as EV; not a Protect claim.

## Checks run (fxcold worktree, plan2 venv, assetops_test, one file at a time)
- test_fx_cold_linked 4 passed; test_out_b3_cold_ev 28 passed; test_out_c2_board 13 passed.
- test_fx_cold_linked_postgres 1 passed (61 s); test_out_c3_repeat_visits_postgres 1 passed (70 s).
- Not run: full suite, frontend (no frontend change), demo_combined_finish.
