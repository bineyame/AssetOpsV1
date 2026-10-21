# Architect request: W3-03 1a review notes (r1a2)

Read:
- `.agent/W3-03-build-spec.md`, through r1a;
- `.agent/W3-03-1a-review.md`, in particular "Builder readings: notes only", the cursor `page_one_mode` note and the Lows.

Rule each item with a literal and a test:
1. **Reading 1, historical settledness.** `settled()` treats `job_state` PENDING/FAILED as U even under HISTORICAL. Mini-grid keeps an outstanding marker under historical, while cold and EV suppress it. Is this correct?
2. **Reading 6, pending vs unknown.** A cold `withheld` result or an EV `ERROR_PENDING` guard sets `_windows_covered=False`, which gives M as U and status UNKNOWN, not PENDING. Confirm, or give the precedence. Name the 1b persisted-variant assertion.
3. **Lane for `estate/composition.py`.** Lane B made an additive edit to this existing file. Confirm the lane, or move the edit.
4. **The unsigned `page_one_mode` in the cursor.** Is it a tamper risk? Give the exact rule: sign it, or validate it against the token, or accept it with a test.

Append the result as "Run-1a review rulings (r1a2)" to `.agent/W3-03-build-spec.md`. Write nothing else. Do not commit.
