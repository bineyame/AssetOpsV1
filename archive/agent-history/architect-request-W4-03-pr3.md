# Architect request: W4-03 PR-3 (CHECK count mismatch)

Read `.agent/W4-03-build-spec.md` (the S4 catalog, u1, u2) and `.agent/W4-03-pending-rulings.md` PR-3.

Code: `c351eed1` on `task/W4-03-mini-decisions-work`; the unmerged `0030` and `backend/tests/test_w403_migration_postgres.py`.

The database has 45 named CHECKs on the ten new tables, matching the test's exact name list, while u2 rules 48 (47 before the narrative check). Recount from the ruled catalog, check by check. Give the exact named CHECK list and the correct total, and say whether any ruled CHECK is missing from 0030 (if so, give its DDL) or whether the 48 was an arithmetic error. Give the literal test assertion.

Append the result as "Unit-2 rulings (u2b)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
