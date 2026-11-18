# Architect request: W4-02 q9 (read and API choices)

Read:
- `.agent/W4-02-build-spec.md`, q1–q8 and Q28 (the unit 5/6/7 split);
- `.agent/W4-02-pending-rulings.md`, q9 (10 points);
- `.agent/W4-02-mock-measurements.md`;
- the v69 `renewable`, `service`, `fuel` and `backup` mocks.

Code: commit `476773e9` on `task/W4-02-mini-grid-depth`: `mini_depth/read.py`, `provenance.py` and `mini_depth_api.py`.

Rule all 10 points with literal JSON or predicates and test assertions. These include:
- the new top-level `basis`;
- no default window;
- downgrading SUPPORTED on pending, stale or unknown provenance;
- the links;
- point 7, the open question of where the retained-margin value comes from. Give its exact source, or an honest null with gap copy.

Then dry-read units 6 and 7 (the pages) against this API and the mock, and answer every question a builder would still have: panel mapping, copy, empty and refused states, and height budgets.

Append the result as "Run 9 rulings (q9) and pages dry-read" to `.agent/W4-02-build-spec.md`. Write nothing else. Do not commit.
