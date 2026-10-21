# Architect request: W4-03 PR-2 (scenario narrative column) and the 2a/2b readings

Read `.agent/W4-03-build-spec.md` (closures 4–5, u1), `.agent/W4-03-pending-rulings.md` PR-2, and `.agent/W4-03-phase-handoff.md` (2a readings 7–10, the 2b anchors).

Code: `011961ec` on `task/W4-03-mini-decisions-work`; `0030` is unmerged.

Rule with exact artifacts:
- PR-2. The scenario command requires `narrative`, but no `0030` column holds it. Give the exact DDL amendment to 0030 (column, type, length CHECK, nullability), the catalog count, the downgrade, and the tests. Make it consistent with u1 if u1 also amends 0030, so the builder applies both in one migration edit.
- Confirm or replace the three 2b readings: the pin refusal codes, the scenario provenance scope, and `scenario_state`.
- Confirm or replace the 2a readings 7–10.

Append the result as "Unit-2 rulings (u2)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
