# Planner + Architect request: W4-03 task packet and build spec

You are the AssetOps Planner and Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide", the Architect readiness gate, "Mock measurements before the spec", and "Token Efficiency";
- `.agent/post-W2-sequence.md`, which defines W4-03's scope (`scenarios`, `alternatives`, `opportunity-finding`; deepen `sitework-incidents`, `sitework-maintenance`), migration `0030`, ownership and seams;
- `tasks/W4-01-work-case-core.md` and `.agent/W4-01-build-spec.md` (all rulings; its case contract is frozen), and `tasks/W4-02-mini-grid-depth.md` and `.agent/W4-02-build-spec.md` (closures 1–3), whose headroom and operating windows W4-03 consumes;
- `.agent/W3-01-build-spec.md` rulings q1–q4, for the shared provenance DTO;
- the v69 mock screens, the screen manifest and `frontend/docs/architecture/v69-rendered-panels.json`;
- `.agent/W4-03-mock-measurements.md`. Use these measured heights and widths for every 1440/390 budget, with max = mock + max(24px,10%). Do NOT attempt your own browser measurement.

Lessons from `.agent/W4-01-W3-01-spec-review.md` (66 questions) , `.agent/W3-02-spec-review.md` (48), `.agent/W4-02-spec-review.md` (33) and `.agent/W3-03-spec-review.md` (35):
- Verify every seam against merged code: file, function, column, and whether the column is nullable or ever written.
- Align error codes with the frozen W3-01 and W4-01 tables.
- Give literal label and state tables for every input combination, with total precedence.
- Give literal copy for every mock CTA and cell, with its empty state.
- Size commits to one builder run.
- Scenario assumptions stay separate from observed claims and money; mark superseded text with a supersession index.
- Never assume a read has `known_at` or multi-day selection without checking.
- Where W1 already ships one of these screens, map the delta exactly.

Write:
1. `tasks/W4-03-<slug>.md` in the W4-01 style, with status "planned; build spec pending".
2. `.agent/W4-03-build-spec.md`, a full Architect contract. Map every mock panel, row, column, chip, label and destination to an exact read or field, or to an honest gap. Include JSON, state tables, ordering, migration `0030` DDL with its index, constraint and downgrade, the copy ledger, 403/404/503 handling, fixtures, and named tests per commit.
3. A README queue row.

Record decision `D-2026-10-20-w4-03-buildspec`. Write nothing else. Do not commit.
