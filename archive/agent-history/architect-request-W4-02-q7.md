# Architect request: W4-02 q7 (tick stage schema) and readings R1–R4

Read:
- `.agent/W4-02-build-spec.md`, rulings q1–q6;
- `.agent/W4-02-pending-rulings.md`, q7 and readings R1–R4;
- `backend/migrations/versions/0013_*.py`, the stage CHECK;
- the `0029` migration on branch `task/W4-02-mini-grid-depth` (`git show 5d8d12f9:<path>`).

Rule with exact artifacts:
- q7. Saving the `mini` tick stage in `schedule_site_head` needs table changes that 0029's fixed change list leaves out: the stage CHECK from 0013 and the counter columns. Give the exact DDL to add to 0029 (CHECK replacement, columns, downgrade), the updated catalog counts, and the tests. Confirm the mini live-job discovery read and the stage limits.
- Confirm or replace R1–R4. R4: a guard bans a quoted `run-` literal outside `runs/identity.py`, so the builder spelled the CLI command `run-pending` indirectly. Is that acceptable, or should the CLI name or the guard allowlist change? Give the exact fix.

Append the result as "Run 7 rulings (q7)" to `.agent/W4-02-build-spec.md`. Write nothing else. Do not commit.
