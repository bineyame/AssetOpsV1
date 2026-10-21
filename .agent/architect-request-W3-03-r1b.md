# Architect request: W3-03 Q-1b-1..3 (r1b)

Read:
- `.agent/W3-03-build-spec.md`, through r1a2;
- `.agent/W3-03-pending-rulings.md`, Q-1b-1, Q-1b-2 and Q-1b-3;
- the 1b readings in `git show 6efa8461:.agent/W3-03-phase-handoff.md`;
- the v69 `portfolio` mock.

Code: `06acf1cf` (Lane A) and `f3f04ef6` (Lane B) on `task/W3-03-portfolio-composition`.

Rule each with literal artifacts and a test:
- **Q-1b-1.** r1a2 item 4 requires a signed cursor, but no Lane A signing seam exists and no key setting or refusal code is ruled. Give the exact mechanism (function, key source, refusal code and body, owning lane and run), or replace it with a non-signing rule that closes the tamper risk, such as validating against the selection token.
- **Q-1b-2.** An APPLIED Action with a non-VERIFIED outcome: is the `workflow_label` "Applied" or "No action yet"? Give the full label table over every Action and outcome state.
- **Q-1b-3.** A pending guard with no selected money line cannot be seen without a Lane A addition to `financials.py`. Give the exact field, owner and run, or the honest display rule.

Confirm or replace the five 1b readings.

Re-dry-read the rest of 1b against this code for open copy, IDs, fields or links:
- cards;
- matrix;
- progress;
- the B4 `[11-01,11-03)` proof.

Also re-dry-read run 2 (the page). Give literals for anything open.

Append the result as "Run-1b rulings (r1b)" to `.agent/W3-03-build-spec.md`. Write nothing else. Do not commit.
