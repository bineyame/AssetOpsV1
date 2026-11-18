# Architect request: W4-02 q5 (run-6 readings)

Read `.agent/W4-02-build-spec.md` (q1–q4) and `.agent/W4-02-phase-handoff.md`, the "Run 6" section, which lists 5 readings.

Code: commits `aa5c724e` and `120ee51e` on `task/W4-02-mini-grid-depth`.

Confirm or replace each reading with an exact predicate and test:
1. How a bad tank reading is assigned to opening or closing.
2. One bad supply row blocks every chain in the hour.
3. A chain with an unusable input loses its recovery time.
4. Backup's critical checks still accept any asset, so unit 4 must pass only the pinned asset's rows. Should the rule itself enforce the pinned asset instead?
5. Which instant the worker uses as its knowledge cutoff (step 4).

Append the result as "Run 5 rulings (q5)" to `.agent/W4-02-build-spec.md`. Write nothing else. Do not commit.
