# Architect request: W3-02 commit 3 (c3-q1, c3-q2)

Read:
- `.agent/W3-02-build-spec.md`: closure 2 N3 and the comparable-proof rule, all money rulings, and c1–c2d;
- `.agent/W3-02-pending-rulings.md`: c3-q1, and c3-q2 with its 7 readings.

Code: `54625bdc` on `task/W3-02-estate-evidence-money-basis`.

Rule with exact artifacts:
- c3-q1. The persisted two-EV-Site comparable fixture cannot be built with the existing producers: they only install EV-LAB-001, and each chain starts a fresh DB. Name the exact fixture path. One option is a second EV Site import plus a replay into the same DB, following the q10 mixed-DB pattern (suppress later `fresh_database()` calls, distinct seeds). Give the file and function names, the assertions for the COMPARABLE group and the different-currency test, and the closure-2 N3 stop rule if it truly cannot be built honestly.
- c3-q2. Confirm or replace each of the 7 readings.

Append the result as "Commit-3 rulings (c3)" to `.agent/W3-02-build-spec.md`. Write nothing else. Do not commit.
