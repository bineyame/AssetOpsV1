# Architect request: W4-02 q10-5 and q11 (page copy and choices)

Read:
- `.agent/W4-02-build-spec.md`, all rulings including q10 and the pages dry-read;
- `.agent/W4-02-pending-rulings.md`: q10 item 5, and q11-1 to q11-4;
- the v69 `renewable`, `service`, `fuel` and `backup` mocks.

Code: branch `task/W4-02-mini-grid-depth` at `4ecbfb25`, in `frontend/src/sites/MiniPerformance.tsx`.

Confirm or replace every provisional choice with literal copy or a predicate:
- q10-5 (service): the verification link copy; the "Clinic (critical)" label taken from the critical load name; "What was needed" always Unknown; the default hour, local 12:00–13:00.
- q11-1: "Evidence limited" when a positive renewable read is downgraded.
- q11-2: the fuel copy and labels.
- q11-3: the 8 backup copy choices. Weigh the Start success denominator most carefully: it is counted from chains with a recorded start, because the read has no denominator. Give the exact honest rule.
- q11-4: the readiness-row rule.

Append the result as "Run 11 rulings (q11)" to `.agent/W4-02-build-spec.md`. Write nothing else. Do not commit.
