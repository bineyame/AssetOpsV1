# Architect request: W2-06 q4 (Q4-1, Q4-2, Q4-3)

You are the AssetOps Architect. Read `.agent/W2-06-build-spec.md` (all rulings q1–q3). The code is on `task/W2-06-ev-assessment` at head `362eb97c`. Read these from it with `git show task/W2-06-ev-assessment:<path>`:
- `.agent/W2-06-pending-rulings.md` (section q4);
- the parked vector producer and `backend/assetops_backend/analytics/ev.py`.

Rule three points with concrete artifacts:
- **Q4-1.** `first_cutoff.known_at` comes from the DB clock, so the vector byte comparison can never pass. Rule exactly how the vector handles it: a fixed injected clock, normalization before comparison, or exclusion from the compared bytes. Name the function or parameter and the literal value.
- **Q4-2.** P2 needs the binding-set ID, role, device and signal on each vector row, plus the member rows. Give the final vector JSON schema: the exact keys per row, per case, and for the member rows, with one fully written example row of each kind.
- **Q4-3.** Confirm the whole-file write mechanics (path, ordering, newline, indentation, key ordering) and the two value formats the builder lists.

Check that the answers are consistent with q1–q3 and that the six W2-05b manifests are unchanged. Append the rulings to `.agent/W2-06-build-spec.md` as "Run 4 rulings (q4)". Write nothing else. Do not commit.
