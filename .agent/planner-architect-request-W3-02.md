# Planner + Architect request: W3-02 task packet and build spec

You are the AssetOps Planner and Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide", the Architect readiness gate, and "Token Efficiency";
- `.agent/post-W2-sequence.md`, which defines W3-02's scope, lane, migration allocation, shared-file ownership and seams;
- `tasks/W3-01-estate-claim-action-roots.md` and `.agent/W3-01-build-spec.md`, including the Run 1 rulings (q1) and the shared provenance DTO;
- `.agent/W4-01-build-spec.md` (Run 1 rulings), for the seams;
- the v69 mock screens that W3-02 owns, in `frontend/mockups/v69/`, plus the screen manifest and `frontend/docs/architecture/v69-rendered-panels.json`;
- `.agent/W4-01-W3-01-spec-review.md`. Its 66 questions are the lesson: answer that class of question up front.

Write:
1. `tasks/W3-02-<slug>.md`, in the W3-01 packet style. Status is "planned; build spec pending".
2. `.agent/W3-02-build-spec.md`, a full Architect build contract. Map every mock panel, row, column, chip, label and destination to an exact read/field or an honest gap, and include:
   - exact JSON shapes and key names;
   - state tables, including unreached states;
   - ordering;
   - migration details, if any are allocated;
   - per-panel height budgets at 1440/390 against the measured mock;
   - the copy ledger, with source fields;
   - 403/404/503 copy;
   - fixture IDs, and named tests per commit;
   - spec commits sized so one builder run covers one commit.
3. A README queue row for W3-02 in `tasks/README.md`.

Record decision `D-2026-10-20-w3-02-buildspec`. Write nothing else. Do not commit.
