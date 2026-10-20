# Architect request: W4-01 q7 and final dry-read of the remaining W4-01 commits

You are the AssetOps Architect. Read:
- `.agent/W4-01-build-spec.md`, all rulings q1–q6;
- `.agent/W4-01-pending-rulings.md`, "q7": five points, each with the builder's reading;
- `.agent/W4-01-phase-handoff.md`, the run-8 file:line plan;
- the v69 mock screens `sitework-incidents` and `sitework-maintenance`.

Code: branch `task/W4-01-work-case-core` at `a23bf8b4`.

Answer q7-1 to q7-5 with literal artifacts. For q7-1, the `asset` table has no `name` column (`0001_foundation_identity.py:95`). Choose the exact display from the existing columns, and keep the mock slot.

This is the seventh question round on W4-01. Finish with a FULL implementer dry-read of commit 4 (lists) and of every remaining W4-01 commit, including the UI and captures, against the code now on the branch. Check every column, every nullable or never-written field, every window, token, enum, copy string, empty state, layout budget and test name. Answer every remaining question now, so the next two builder runs stop for nothing.

Append the result as "Run 7 rulings (q7) and final dry-read" to `.agent/W4-01-build-spec.md`. Write nothing else. Do not commit.
