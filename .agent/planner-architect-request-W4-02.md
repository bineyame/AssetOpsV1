# Planner + Architect request: W4-02 task packet and build spec

You are the AssetOps Planner and Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide", the Architect readiness gate, "Mock measurements before the spec", and "Token Efficiency";
- `.agent/post-W2-sequence.md`, which defines W4-02's scope (`renewable`, `service`, `fuel`, `backup`), migration `0029`, ownership and seams;
- `tasks/W4-01-work-case-core.md` and `.agent/W4-01-build-spec.md`, including all rulings;
- `.agent/W3-01-build-spec.md` rulings q1–q4, for the shared provenance DTO;
- the v69 mock screens, the screen manifest and `frontend/docs/architecture/v69-rendered-panels.json`;
- `.agent/W4-02-mock-measurements.md`. Use these measured heights and widths for every 1440/390 budget, with max = mock + max(24px,10%). Do NOT attempt your own browser measurement.

Lessons from `.agent/W4-01-W3-01-spec-review.md` (66 questions) and `.agent/W3-02-spec-review.md` (48 questions):
- Verify every seam against merged code: file, function, column, and whether the column is nullable or ever written.
- Align error codes with the frozen W3-01 and W4-01 tables.
- Give literal label and state tables for every input combination, with total precedence.
- Give literal copy for every mock CTA and cell, with its empty state.
- Size commits to one builder run.
- Never assume a read has `known_at` or multi-day selection without checking.
- Where W1 already ships one of these screens, map the delta exactly.

Write:
1. `tasks/W4-02-<slug>.md` in the W4-01 style, with status "planned; build spec pending".
2. `.agent/W4-02-build-spec.md`, a full Architect contract. Map every mock panel, row, column, chip, label and destination to an exact read or field, or to an honest gap. Include JSON, state tables, ordering, migration `0029` DDL with its index, constraint and downgrade, the copy ledger, 403/404/503 handling, fixtures, and named tests per commit.
3. A README queue row.

Record decision `D-2026-10-20-w4-02-buildspec`. Write nothing else. Do not commit.
