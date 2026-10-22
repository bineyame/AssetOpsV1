# Architect request: W4-03 PR-7 (unit-5 read contract), plus a batched dry-read of units 6–12

Read:
- `.agent/W4-03-build-spec.md`, all closures and u1–u4b;
- `.agent/W4-03-pending-rulings.md`, PR-7, which records each reading the builder would take;
- the unit-5 survey anchors in `.agent/W4-03-phase-handoff.md` at `9eabb433` (`git show 9eabb433:.agent/W4-03-phase-handoff.md`);
- the v69 mocks for the opportunity and work screens.

u4b said unit 5 had no open decision, but the builder found these wire values open:
- the list status;
- the currentness order;
- the read-time codes;
- the history and row shape;
- the list window;
- the `site_work` path.

For each, give the literal wire, either as JSON examples or as enum lists with their precedence, plus the test name.

To avoid more mid-build stops, dry-read units 6–12 against the code as built, at branch head `9eabb433`. For every wire value, status, copy string, path or fixture a builder would still have to choose, give the literal artifact now.

Append the result as "Unit-5..12 rulings (u5)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
