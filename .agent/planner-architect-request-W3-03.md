# Planner + Architect request: W3-03 task packet and build spec

You are the AssetOps Planner and Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide", the Architect readiness gate, "Mock measurements before the spec", and "Token Efficiency";
- `.agent/post-W2-sequence.md`, which defines W3-03's scope (`portfolio` and finishing the W3-01/02 global roots), migration `0031`, ownership and seams;
- `tasks/W3-01-estate-claim-action-roots.md`, `.agent/W3-01-build-spec.md` (all rulings and amendments), `tasks/W3-02-estate-evidence-money-basis.md` and `.agent/W3-02-build-spec.md` (all closures), and `.agent/W4-01-build-spec.md` for seams. W3-03 consumes W3-01/02, not W4 output;
- `.agent/W3-01-build-spec.md` rulings q1–q4, for the shared provenance DTO;
- the v69 mock screens, the screen manifest and `frontend/docs/architecture/v69-rendered-panels.json`;
- `.agent/W3-03-mock-measurements.md`. Use these measured heights and widths for every 1440/390 budget, with max = mock + max(24px,10%). Do NOT attempt your own browser measurement.

Lessons from `.agent/W4-01-W3-01-spec-review.md` (66 questions) , `.agent/W3-02-spec-review.md` (48 questions) and `.agent/W4-02-spec-review.md` (33 questions):
- Verify every seam against merged code: file, function, column, and whether the column is nullable or ever written.
- Align error codes with the frozen W3-01 and W4-01 tables.
- Give literal label and state tables for every input combination, with total precedence.
- Give literal copy for every mock CTA and cell, with its empty state.
- Size commits to one builder run.
- Never assume a read has `known_at` or multi-day selection without checking.
- Where W1 already ships one of these screens, map the delta exactly.

Write:
1. `tasks/W3-03-<slug>.md` in the W3-01 style, with status "planned; build spec pending".
2. `.agent/W3-03-build-spec.md`, a full Architect contract. Map every mock panel, row, column, chip, label and destination to an exact read or field, or to an honest gap. Include JSON, state tables, ordering, migration `0031` DDL with its index, constraint and downgrade (or record `0031` as unused if the slice is schema-free), the copy ledger, 403/404/503 handling, fixtures, and named tests per commit.
3. A README queue row.

Record decision `D-2026-10-20-w3-03-buildspec`. Write nothing else. Do not commit.
