# Architect request: W4-03 unit-5 builder readings (u5b)

Read:
- `.agent/W4-03-build-spec.md`, through "Unit-5..12 rulings (u5)";
- the unit-5 section of the handoff: `git show ab020170:.agent/W4-03-phase-handoff.md`. It lists nine readings taken without a ruling.

Code: `ab020170` on `task/W4-03-mini-decisions-work`, in `mini_decisions/opportunities.py`, `store.py`, `mini_decisions_api.py` and `main.py`.

For each of the nine readings, confirm it or give the exact replacement (a literal wire or predicate) and a test. The readings include:
- the non-MINIGRID detail envelope;
- when SOURCE_STALE is added;
- literal job-window overlap;
- withholding scenario money unless the opportunity data is current and its source class is known;
- the closed-gate error shape;
- passing gate failures into the router (a guard constraint).

Also confirm the u4b vector change: job status isn't kept over time, so a replay at an earlier cutoff sees a finished job, matching W4-02.

Say whether any reading changes what units 6–12 in u5 assume. If so, give the exact amendment.

Append the result as "Unit-5 builder rulings (u5b)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
