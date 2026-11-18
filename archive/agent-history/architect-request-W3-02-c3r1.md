# Architect request: W3-02 commit-3 review (r1)

Read `.agent/W3-02-build-spec.md` (c3–c3c) and `.agent/W3-02-commit3-review.md`.

Code: `edcd8fce` on `task/W3-02-estate-evidence-money-basis`.

Rule with exact artifacts:
- M1. Pending cold consequence work does not mark product-exposure coverage unknown (`financials.py:208-213`), so a Site still being computed reads as complete NO_LINES, while EV gets UNKNOWN_COVERAGE in the same case per c3-q2(2). Confirm the fix `covered=False` when `read["withheld"]`, or give the exact rule, with its test.
- M2. The second-chain repository uses `CompositeScenarioRepository` instead of the c3b construction, which raises AttributeError. Confirm this deviation, or give the exact construction, and correct the RESOLVED marking.
- The 6 Lows: fix or carry each.

Append the result as "Commit-3 review r1 rulings" to `.agent/W3-02-build-spec.md`. Write nothing else. Do not commit.
