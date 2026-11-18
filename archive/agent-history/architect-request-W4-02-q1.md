# Architect request: W4-02 q1

Read:
- `.agent/W4-02-build-spec.md`, closures 1–5;
- `.agent/W4-02-pending-rulings.md`, R1;
- `.agent/W4-02-phase-handoff.md`, which lists the 29 failing existing tests and the builder's proposed fix.

Code: branch `task/W4-02-mini-grid-depth` at `a81dda88`, commit `00a5703a`: migration 0029, roles-4, the store and the guard.

Rule with exact artifacts:
1. R1, which blocks unit 3: B2's binding-validation rule would refuse every existing v3 channel on a roles-4 Site. Give the exact validation predicate that keeps v3 channels valid and still enforces roles-4, plus the test.
2. The 29 failing existing tests: downgrade tests through 0029 now refuse because mini-grid fixtures leave `mini_*` jobs. The builder proposes deleting those jobs before downgrading, as is already done for EV jobs. Confirm the exact mechanism, or replace it, consistent with earlier rulings that forbid bypassing append-only triggers in downgrade probes. Name the precedent file and line. Also confirm the job-count and raw-insert assertion updates in the s2 and w200 tests, as S4 anticipated.

Append the result as "Run 1 rulings (q1)" to `.agent/W4-02-build-spec.md`. Write nothing else. Do not commit.
