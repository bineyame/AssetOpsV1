# Architect request: W3-01 commit-2 prerequisite review (r1)

Read:
- `.agent/W3-01-build-spec.md`: "Run 5 rulings (q5)", plus the earlier cold/EV M3.2 ruling in "Commit-1 review r1 rulings";
- `.agent/W3-01-commit2-prereq-review.md` (M1, L1–L3);
- `.agent/W3-01-phase-handoff.md` (R1–R8).

The code is on branch `task/W3-01-estate-claim-action-roots`, commit `a75b0291`, `postgres_assessment_store.py:723-735`.

Rule with exact artifacts, so a Sonnet fixer decides nothing:
- M1: the day-selector predicate. A DONE job whose selections all postdate the cutoff counts as outstanding at the cutoff. Give the exact predicate, the state that results, and the corrected test assertion that replaces `early`.
- L1: whether open jobs count as pending at a historical cutoff for the mini-grid. Reconcile this with the cold/EV M3.2 ruling and give one consistent rule.
- L2: the widened-job overlap at the cutoff. Either fix it or rule it as an accepted disclosed limitation.
- L3 / R1: confirm or revert the early `$pgReaders` line.

Append the result as "Prerequisite review r1 rulings" to `.agent/W3-01-build-spec.md`. Write nothing else. Do not commit.
