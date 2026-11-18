# Architect request: W4-03 PR-1 (OPPORTUNITY stage counters)

Read `.agent/W4-03-build-spec.md` (closures 4–5, the unit split), `.agent/W4-03-pending-rulings.md` PR-1, and the W4-02 q7 ruling in `.agent/W4-02-build-spec.md` (the MINI stage added counter columns to `schedule_site_head`).

Code: `c3713564` on `task/W4-03-mini-decisions-work`; migration `0030` is unmerged.

Rule PR-1: does `0030` need OPPORTUNITY counter columns on `schedule_site_head`, following the MINI precedent? Give the exact DDL, the downgrade, the catalog count change and the tests, and say which unit lands them: as a 0030 amendment now, or in unit 4.

Also confirm or replace the readings in the handoff: the length limits copied from W4-01, the CHECK names the builder chose, and the study-window check deferred to unit 4.

Append the result as "Unit-1 rulings (u1)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
