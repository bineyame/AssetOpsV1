# Architect request: W4-01 q2 (commit 2 blocked)

You are the AssetOps Architect. Read:
- `.agent/W4-01-build-spec.md`, including all closures and the q1 rulings;
- `.agent/W4-01-pending-rulings.md`, q2 items 4–5;
- `.agent/W4-01-phase-handoff.md`, which lists 8 builder readings.

The code is on branch `task/W4-01-work-case-core` at `482d2540`, with the draft in `.agent/W4-01-commit2-partial.patch`.

Rule with exact artifacts:
- q2-4. The F01 fixture's accepted evidence is received on 2026-10-30/31 through the ledger test clock, while the database clock is 2026-10-20, so "received at or before the command's DB time" refuses with 422. Choose the fix: move the fixture dates, freeze or inject the command clock, or change the predicate. Give the exact values and code, and keep the rule honest.
- q2-5. After F01's Action is accepted, F02's recommendation returns no proposal. Give the exact fixture path that yields a second, distinct Action for the wrong-Action-event test.

Confirm or replace all 8 readings, especially:
- reopening an in-progress Incident to Open;
- the refusal order: 403 for no principal, then 422 for shape, then 403 for a USER actor, then 422 for attestation;
- a non-head correction returning 409 `WORK_CORRECTION_CONFLICT`;
- the idempotency hash using the resolved Site ID.

Append the result as "Run 2 rulings (q2)" to `.agent/W4-01-build-spec.md`. Write nothing else. Do not commit.
