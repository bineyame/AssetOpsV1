# Architect request: W3-02 commit 4 (c4-q1 to c4-q3, plus the Aggregation height defect)

Read:
- `.agent/W3-02-build-spec.md`, all rulings;
- `.agent/W3-02-pending-rulings.md`, c4-q1 to c4-q3;
- `.agent/W3-02-phase-handoff.md`, the commit-4 capture defects;
- `.agent/W3-02-mock-measurements.md`, the financials rows;
- the v69 `globalfinancials` mock.

Code and captures: `75d30ca0` on `task/W3-02-estate-evidence-money-basis`, `.agent/W3-02-evidence/`.

Rule with exact artifacts:
1. The Aggregation panel is over its cap in every capture: 211 px against 123 at 1440, and 298 against 187 at 390. Its results list is already clipped at 56/96 px, which hides content. Give the exact layout and content rule that fits the mock's density without hiding information: row limits, disclosure, chip wrapping and font sizes. Give the revised cap only if the mock itself measures larger.
2. c4-q1: confirm or replace the copy readings.
3. c4-q2: confirm the registry prerequisites (area `money`, `I-financial-read`, `D-money-comparison`, `P-money-area`) and the ledger `data_owner` wording.
4. c4-q3: the capture data has no mini-grid money line, so the register shows 2 rows where the mock shows 3. Name a fixture path that yields an honest mini-grid line for the capture, or rule the honest limitation with its copy.

Append the result as "Commit-4 rulings (c4)" to `.agent/W3-02-build-spec.md`. Write nothing else. Do not commit.
