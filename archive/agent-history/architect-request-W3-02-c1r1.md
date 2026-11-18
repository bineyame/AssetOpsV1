# Architect request: W3-02 commit-1 review (r1)

Read `.agent/W3-02-build-spec.md` (closures 1–5, 0b/0c r1, c1) and `.agent/W3-02-commit1-review.md`.

Code: branch `task/W3-02-estate-evidence-money-basis` at `1e50a8a4`.

Rule with exact artifacts:
- M1. `_window_state` (`evidence_money.py:221-228`) turns cold/EV rows UNKNOWN on a live page two when the Site gets a new disposition between requests, while the status and token stay CURRENT and no 409 fires. Give the exact fence: a 409, or a frozen-basis selection, consistent with c1-q1/q7 and W3-01 q8/q10.
- M2. Any W1 refusal becomes a lasting estate-wide 409 (`postgres_evidence_money_read.py:55-59`). Give the exact mapping, so the day is one UNKNOWN row with its reason, per the 0b reading 3.
- R1. One text, "Generator state not observed", for every role. Is that acceptable, or should it be per-role copy?
- R2. METER_GAP sits on the energy row. Is that the right row?
- L1–L5: fix or carry each, with test names where fixed.

Append the result as "Commit-1 review r1 rulings" to `.agent/W3-02-build-spec.md`. Write nothing else. Do not commit.
