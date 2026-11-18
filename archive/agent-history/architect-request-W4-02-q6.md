# Architect request: W4-02 q6 (stored result shape)

Read:
- `.agent/W4-02-build-spec.md`, rulings q1–q5;
- `.agent/W4-02-pending-rulings.md`, q6 (6 questions);
- the v69 `renewable`, `service`, `fuel` and `backup` mocks.

Code: branch `task/W4-02-mini-grid-depth` at `55bf97cc`; `mini_depth/projection.py` is in `e0f7c9de`.

Answer all six with the literal stored JSON shape and a test assertion each:
1. Per renewable hour status and cards.
2. `coverage` on fuel and backup rows.
3. Instant backup roles counted with 0 sources.
4. The fuel-consumption ID when several apply.
5. How source freshness is judged.
6. Whether to keep `start_success_count`.

Every mock panel's value must have its stored source, or an honest null with its gap copy.

Append the result as "Run 6 rulings (q6)" to `.agent/W4-02-build-spec.md`. Write nothing else. Do not commit.
