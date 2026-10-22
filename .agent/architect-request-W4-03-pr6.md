# Architect request: W4-03 PR-6 (opportunity revision result fields)

Read:
- `.agent/W4-03-build-spec.md`, closures 4–5 and u1–u3;
- `.agent/W4-03-pending-rulings.md`, PR-6 (four questions);
- the v69 `opportunity-finding` and `renewable` mocks;
- the W4-02 renewable q6/q9 rulings in `.agent/W4-02-build-spec.md`, for the day-level shapes this consumes.

Code: `24e460d3` on `task/W4-03-mini-decisions-work`.

The spec never defines the stored `result` of an opportunity revision. Give the literal stored JSON shape, with the predicate and a test for each field. Specifically:
1. How `headroom_kw` combines the eligible days, using interval arithmetic such as min/max of bounds.
2. Which `limitations` codes are stored, as an exact list.
3. Whether a stale or pending W4-02 day lowers the stored status, and the precedence.
4. Where each day's `constraints` come from: which W4-02 field.

Every opportunity-page mock value must map to a stored field, or to an honest null with its gap copy.

Append the result as "Unit-4 rulings (u4)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
