# Architect request: W3-02 `0c` review (r1)

Read:
- `.agent/W3-02-build-spec.md`, closures 4–5 and the 0b r1 rulings;
- `.agent/W3-02-0c-review.md`: H1, M1 and Lows L1–L3;
- `.agent/W3-01-build-spec.md` "Run 7 rulings (q7)".

Code: commit `750ce929` on `task/W3-02-estate-evidence-money-basis`.

Rule with exact artifacts:
- H1. Pinned heads select the head as of the cutoff (`created_at <= :k`, latest by `revision_no`), not a refusal, following the W3-01 cold and W1 `select_consequence_on` precedent. Confirm the exact predicate for cold and for EV, and the test.
- The EV point: the EV basis is derived from current tariffs, so historical EV reads can show `STALE_BASIS` even after the fix. Rule the exact historical EV tariff and basis selection, with the predicate, the test and the copy if it stays honestly stale.
- M1. The cold Postgres money check passes vacuously because no cold consequence worker runs. Name the exact fixture or replay path that creates real cold consequence heads, and the assertion.
- L1–L3: fix or carry each.

Append the result as "0c review r1 rulings" to `.agent/W3-02-build-spec.md`. Write nothing else. Do not commit.
