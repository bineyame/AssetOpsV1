# Architect request: W3-02 closure round 2

You are the AssetOps Architect. Read:
- `.agent/W3-02-build-spec.md`, including "Review closure (2026-10-20)";
- `.agent/W3-02-closure-check.md`, which has 5 OPEN items (Q4, Q6, Q7, Q19, Q27) and 5 new questions (N1–N5);
- `.agent/W3-02-mock-measurements.md`;
- `.agent/W3-01-build-spec.md`, rulings q1–q3.

Close all 10 items with exact artifacts:
- the literal label tables, with every value and its source constant;
- state mapping tables covering every input combination;
- a total precedence order;
- the literal copy for every mock CTA and `Unlocks` cell, with its empty state.

For N1, split commit 0 into one-builder-run commits if needed. For N2, rule the W3-01 contract amendment explicitly and record it in `.agent/W3-01-build-spec.md` too, as a versioned amendment. For N3, give an explicit stop rule. For N4, give the exact helper call.

Append the result as "Review closure 2 (2026-10-20)" to `.agent/W3-02-build-spec.md`, and add the amendment to `.agent/W3-01-build-spec.md` if one is made. Write nothing else. Do not commit.
