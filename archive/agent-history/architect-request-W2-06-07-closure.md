# Architect request: W2-06 and W2-07 full pre-build closure

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: the sections "Mockup drives the design; implementers never decide", the Architect readiness gate, and "Token Efficiency";
- `tasks/W2-06-ev-assessment.md` and `tasks/W2-07-ev-site-evidence-money.md`;
- `.agent/W2-06-build-spec.md` and `.agent/W2-07-build-spec.md`;
- `.agent/W2-technical-design-ev.md`;
- the W2-05a and W2-05b build specs, including all Run 8, r2 and q1 rulings;
- the W2-03 and W2-04 build specs, which are the cold equivalents W2-06 and W2-07 mirror, including their Run 8 and Run 9 rulings on layout, copy, chip tones and the null-link copy.

The v69 EV mock screens (`frontend/mockups/v69/`) are authoritative: every panel, row, column, chip and label.

Lesson: W2-04 and W2-05b builders each stopped on 10–14 unruled questions that the earlier dry-read missed. Examples:
- the JSON shapes and key names;
- the total ordering of same-time events;
- the state-transition tables, including unreached states;
- the hash input row form;
- the exact UI component choice, labels, and the 403/404/503 copy;
- panel heights above 1.3x the mock, and the column widths and wrapping;
- the null and missing copy;
- the chip tones;
- the migration index, constraint and downgrade details;
- the test counts or constraint-count updates in existing tests.

For EACH of W2-06 and W2-07, do a full implementer dry-read of every spec commit. Answer in advance every question a mid-level implementer would ask, at the level of detail above, including:
- per-panel height budgets against the measured mock heights, with column widths;
- a copy dry-read listing every user-visible string and its source field;
- the exact migration details for `0025` and `0026`.

Where the cold rulings already settle a pattern (for example chip tones and the null-link copy), state that the EV equivalent applies, with the EV-specific values.

Append the results to each build spec as "Pre-build closure (2026-10-19)", amending `D-2026-10-18-w2-06-07-buildspec`. Write nothing else. Do not commit.
