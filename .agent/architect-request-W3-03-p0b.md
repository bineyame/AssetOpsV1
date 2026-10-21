# Architect request: W3-03 P-0b-1, and the run numbering for L3

Read:
- `.agent/W3-03-build-spec.md`, closures 4–5 and r0a;
- `.agent/W3-03-pending-rulings.md` P-0b-1, with the builder's actual reads and probe;
- the run-0b readings in `git show 45592a22:.agent/W3-03-phase-handoff.md`.

Code: `45592a22` on `task/W3-03-portfolio-composition`, in `backend/tests/test_w303_portfolio_fixture_postgres.py`.

1. **P-0b-1.** The named cold producer `normal` selects no cold Finding or line on 2026-10-06. Its product-exposure group comes back UNKNOWN_COVERAGE while the financials root says COMPLETE.
   - Adopt the builder's probe path (cold `excursion` plus the W2-04 cold consequence drain via `cold_case`/`cold_drain`), or give the exact replacement.
   - Say whether "root COMPLETE while a group is UNKNOWN_COVERAGE" is correct W3-02 behaviour. If it is a defect, name the exact fix, the owning lane and when it lands.
2. **L3 numbering.** r0a assigned L3 (the `estateClient.ts` portfolio union) to "run 2". The builder read run 2 as 0b and treated L3 as out of 0b's scope. Name the exact run (0b, 1a, 1b, ...) that owns L3.

Append the result as "Run-0b rulings (r0b)" to `.agent/W3-03-build-spec.md`. Write nothing else. Do not commit.
