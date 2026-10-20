# Architect request: W3-01 q12 (page-two Site state label) and W3-01 commit-3 readiness

Read:
- `.agent/W3-01-build-spec.md`, all rulings, especially "Commit-2 review r1 rulings";
- the "Re-review r1" section of `.agent/W3-01-commit2-review.md`.

Code: branch `task/W3-01-estate-claim-action-roots` at `72554dc2`.

1. Reading 1. On a live page two, the Site `state` label is HISTORICAL, while page one showed PENDING_RECOMPUTE or STALE_SOURCE. The ruling's two sentences conflict on this one user-visible field. Rule the exact label for every page-one mode and Site state combination, as a literal table, plus the test assertion.
2. The L2 test has a vacuous `or seen == old` disjunct. Give the exact replacement assertion.
3. Re-confirm that the "final dry-read" in q6 still covers commits 3 (the five estate UI roots) and 4 (captures and closeout) after q7–q11 and the c2 r1 rulings. List any change those rulings force on commits 3 and 4: wire keys (`estate-finding-index-2`), cursor `page_one_mode`, copy and states.

Append the result as "Run 12 rulings (q12)" to `.agent/W3-01-build-spec.md`. Write nothing else. Do not commit.
