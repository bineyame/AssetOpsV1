# Architect request: W4-01 q6 (cold/EV pins in the lists under q5 r1)

Read `.agent/W4-01-build-spec.md` (all rulings, especially "Run 5 rulings (q5)" r1 and "Run 3 rulings (q3)" ruling 6), and the "Commit 4 resume anchors" section of `git show 091d6e50:.agent/W4-01-phase-handoff.md` (branch `task/W4-01-work-case-core`).

The builder flags two points, verified against the code:
1. q5 r1 builds list selection tokens from the W1 Finding and Action index tokens (`sfi1-`/`sai1-`). Cold/EV Finding pins have no W1 index, so under r1 they may come out null/UNKNOWN in every list row.
2. It is unchecked whether rows from `select_dispatch_days_on` reproduce the W1 Finding token exactly.

Check both against the code. Rule the exact list-row selection and token for cold/EV pins, using the shared `_snapshot(..., selection_cutoff, selection_seqs)` from q3 ruling 6 instead of a W1 index. Give literal key and token formats and a named test, and the rule for (2).

Append the result as "Run 6 rulings (q6)" to `.agent/W4-01-build-spec.md`. Write nothing else. Do not commit.
