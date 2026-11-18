# Architect request: W4-01 q4 (commit 3 readings and two questions)

Read:
- `.agent/W4-01-build-spec.md`, all rulings including q3;
- `.agent/W4-01-pending-rulings.md`, "Run 5": 8 readings, plus q4-1 and q4-2;
- `.agent/W4-01-phase-handoff.md`.

Code: branch `task/W4-01-work-case-core` at `2df11d89`, commits `3353e858` and `99e5fea3`. `99e5fea3` added `analytics/composition.py:build_cold_ev_selection_pins()` because check-all banned importing the adapter from `work/composition.py`.

Rule with exact artifacts:
1. Confirm or replace each of the 8 readings, including pinning all cold analytics of the window together.
2. Confirm the `99e5fea3` composition placement.
3. q4-1: whether the test harness may inject a read time so the F01 case shows on the detail route. Its fixture is dated from 29 Oct, so today it reads as not yet created. Give the exact mechanism, consistent with q2's test-only command clock, or an alternative.
4. q4-2: whether commit 2 must refuse a Finding or Action pin newer than the command's DB time. Give the predicate, the error code and the test.

Append the result as "Run 4 rulings (q4)" to `.agent/W4-01-build-spec.md`. Write nothing else. Do not commit.
