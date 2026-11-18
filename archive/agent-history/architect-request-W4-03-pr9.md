# Architect request: W4-03 PR-9 and the unit-7 and u6b readings (u7)

Read:
- `.agent/W4-03-build-spec.md`, through u6b;
- `.agent/W4-03-pending-rulings.md`, PR-9;
- the unit-7 and u6b readings in `git show dc4c33ae:.agent/W4-03-phase-handoff.md`: 12 for unit 7 and 3 for u6b;
- the v69 mocks for the opportunity and renewable pages.

Code: `8bd3b5c4` (unit 7), plus `b28b4ed3` and `53e3abf0` (the u6b fixes), on `task/W4-03-mini-decisions-work`.

1. **PR-9.** The Opportunity breadcrumb in u5 conflicts with B5, closure 3 and the mock. Give the one literal breadcrumb. Rule the two smaller items too.
2. **Shared-file edits made to pass.** Confirm or replace each:
   - `frontend/src/test/panelStructure.ts`, the shared panel-structure helper, now accepts the moved Analysis helper line;
   - the W1 Finding stubs in the Finding History and Action tests now follow u6b item 6.
3. **Readings.** Confirm or replace each of the 15.
4. **Unit 8.** It is being built in parallel. Say explicitly if any ruling changes something unit 8 depends on.

Append the result as "Unit-7 rulings (u7)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
