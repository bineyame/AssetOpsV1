# Architect request: W4-02 q11-5 and q12 (capture findings before final review)

Read:
- `.agent/W4-02-build-spec.md`, all rulings;
- `.agent/W4-02-pending-rulings.md`: q11-5 and q12-1 to q12-8;
- `.agent/W4-02-review-packet.md`;
- `.agent/W4-02-mock-measurements.md`;
- the v69 `renewable`, `service`, `fuel`, `backup` and Site overview mocks.

Code and captures: branch `task/W4-02-mini-grid-depth` at `cd5a6350`, with `.agent/W4-02-evidence/` on that branch.

The captures fail 45 of 296 checks. Rule each item with exact, user-faithful fixes:
- q12-7. 39 panels are over their height budgets on all four pages. The worst is backup readiness, which lists every evidence ID: 598 px against 316 at 1440, and 2441 px against 471 at 390. For each over-budget panel, give the exact bounding: row limits, disclosure, collapsed ID lists, or table scroll within the panel, so it matches the mock's density without dropping information.
- q12-6. The Overview mini cards never mount for `MG-W402-001`, which shows the "Awaiting evidence migration" Overview. Give the exact fixture or seed change, or the Overview rule, so the captures show the five cards with mini values.
- q12-8. The seeded sources classify as UNKNOWN, so the positive Watch/Supported states appear only in unit tests. Name the exact seed or replay change that makes at least one positive state visible in a capture honestly, or rule the limitation.
- q12-1 to q12-5, and q11-5: confirm or replace each.

Append the result as "Run 12 rulings (q12)" to `.agent/W4-02-build-spec.md`. Write nothing else. Do not commit.
