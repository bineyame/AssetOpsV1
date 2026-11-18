# Architect request: W3-01 commit-2 review (r1)

Read:
- `.agent/W3-01-build-spec.md`, all rulings q1–q10;
- `.agent/W3-01-commit2-review.md`, which has M1, q11 analysis, the clock-drift analysis and Lows L1–L4;
- `.agent/W3-01-pending-rulings.md`, q11.

Code: branch `task/W3-01-estate-claim-action-roots` at `1492532c`.

Rule with exact artifacts, so a Sonnet fixer decides nothing:
- M1 and q11 together. The reviewer recommends option (b): record page one's live or historical mode in the cursor, which also fixes M1, the mini-grid page-two 409. Give the cursor field, the predicate, and tests for both the mini-grid pending and stale cases and the explicit-earlier-cutoff case. Keep it consistent with q10 ruling 3 and q8 ruling 6.
- The clock drift: either one test run with the read clock forced 30 days later (name the mechanism), or a dated residual risk in the packet. Cover the mini_grid branch's unguarded read-time pin.
- L1–L4: fix or accept each, with the test name where one is needed.
- The open readings: q10 readings 2 and 4; Lane A q11-2 (the guard tests are not in the suite, and a W3-02 file path is already on the reader allowlist); L3, the restored dropped readings.

Append the result as "Commit-2 review r1 rulings" to `.agent/W3-01-build-spec.md`. Write nothing else. Do not commit.
