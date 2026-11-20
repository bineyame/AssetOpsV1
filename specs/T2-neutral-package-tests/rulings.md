# T2 rulings

Architect (Claude), 2026-11-20. Index line: `.ai/decisions/index-rulings-7.md`.

## D-T2.1 The neutral packages' tests are a check-all guard, not a new runner tier

- **Ruling.** `simulator/tests` and `contracts/tests` run as one blocking check-all guard. `select-tests` names them
  for a change that can affect them. The Docker merge runner does not change.
- **Why.**
  - Check-all runs where the gap is: on every branch before review, and on `main` after every merge (RULES §7).
  - The tests need no database and take about 10 s.
  - A new tier in the Docker runner would add an image, a JUnit file and a zero-skip rule for 461 fast tests.
  - It also closes the class for both packages at once, which D-2A.10 (moving `2a`'s tests into `backend/tests`)
    could not do for the simulator.
