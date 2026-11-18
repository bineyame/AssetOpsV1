# Architect request: W3-02 commit-1 questions (c1-q1 to c1-q3)

Read `.agent/W3-02-build-spec.md` (closures 4–5, the 0b/0c r1 rulings) and `.agent/W3-02-pending-rulings.md`: c1-q1, c1-q2, and c1-q3 with its 7 readings.

Code: branch `task/W3-02-estate-evidence-money-basis` at `1147519a`.

Rule with exact artifacts:
- c1-q1. `0c`'s `historical_label` is set only when the Site snapshot is HISTORICAL, meaning the row-local cutoff is earlier than the Site watermark. An explicit earlier estate cutoff with no later disposition gets no label. Rule which condition labels a row as historical, consistently for Evidence and commit-3 Financials, and say which file changes (a Lane A facade or the Lane B estate layer).
- c1-q2. The EV facade does not expose `unknown_meter`, so the builder reads it through a private `_sessions` call. Give the exact public facade addition (a Lane A file), or rule the alternative.
- c1-q3. Confirm or replace each of the 7 readings.

Append the result as "Commit-1 rulings (c1)" to `.agent/W3-02-build-spec.md`. Write nothing else. Do not commit.
