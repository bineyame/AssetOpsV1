# Architect request: W4-02 q3 (unit-3 readings)

Read:
- `.agent/W4-02-build-spec.md`: closures 1–5, q1 and q2;
- `.agent/W4-02-phase-handoff.md`, which lists 13 unit-3 readings;
- the v69 `fuel` and `backup` mocks.

Code: branch `task/W4-02-mini-grid-depth` at `e35d9239`.

Confirm or replace each of the 13 readings with exact artifacts. Two of them matter most because they change what users see:
- Fuel status is never SUPPORTED, since there is no residual, even when a modelled expected use exists. Is that the honest, intended outcome? Give the exact state table and copy.
- Supply state is an instant reading, so "No outage in the selected hour" can never show. Give the exact predicate that makes it reachable, or rule that it is honestly unreachable, with the copy that then shows in its slot. Keep the mock slot either way.

Also confirm the unit-4 plan to rerun the authored replay through the HTTP `run` path with an issued gateway credential, to record selection seqs.

Append the result as "Run 3 rulings (q3)" to `.agent/W4-02-build-spec.md`. Write nothing else. Do not commit.
