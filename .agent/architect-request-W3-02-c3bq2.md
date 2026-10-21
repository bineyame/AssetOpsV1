# Architect request: W3-02 c3b-q2 (COMPARABLE test token assertion)

Read `.agent/W3-02-build-spec.md` (c3 and c3b, plus the commit-1 r1 ruling on M1, where tokens include the read cutoff k), and `.agent/W3-02-pending-rulings.md` c3b-q2.

Code: `f1e49236` on `task/W3-02-estate-evidence-money-basis`, `estate/index.py:85`.

The COMPARABLE two-Site test asserts that page one's selection token equals a separate full live read's token. Each live read has its own k, so the tokens legitimately differ. Rule the exact assertion. For example: use an explicit shared `known_at` for both reads, or compare page two to page one under the cursor's frozen k, following the commit-1 M1 precedent. Give the literal test change.

Append the result as "Commit-3 rulings (c3c)" to `.agent/W3-02-build-spec.md`. Write nothing else. Do not commit.
