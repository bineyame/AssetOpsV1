# Architect request: W4-03 unit-4 builder choices and unit-5 dry-read

Read:
- `.agent/W4-03-build-spec.md` (closures 4–5, u1–u4);
- the unit-4 section of `.agent/W4-03-phase-handoff.md`, from branch head `6a405a25`; it lists four choices taken without a ruling.

Code: the commits `c4180e15`, `de4301f2`, `791e36c2` and `d5ff988c` on `task/W4-03-mini-decisions-work`. In particular, the shared Site lease grows from 480 to 600 s, and the `run-pending` name is built from the method name.

For each of the four choices, and for the lease change, confirm it or give the exact replacement and a test. Confirm the read-side tests that moved to unit 5.

Then dry-read unit 5 against the code as built, and answer anything still open with literal artifacts. If nothing is open, say so in one line.

Append the result as "Unit-4 builder rulings (u4b)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
