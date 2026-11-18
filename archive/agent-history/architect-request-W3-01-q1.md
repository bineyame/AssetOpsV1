# Architect request: W3-01 run-1 pending rulings (q1)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide" and "Token Efficiency";
- `.agent/post-W2-sequence.md`, including shared-file ownership and the seam table;
- `.agent/W3-01-build-spec.md` and `.agent/W4-01-build-spec.md`, with every closure;
- `.agent/W3-01-pending-rulings.md` (7 questions) and `.agent/W3-01-phase-handoff.md` (8 builder readings).

The code is on branch `task/W3-01-estate-claim-action-roots` commit `1c409a3d` (`git show 1c409a3d`). Lane A W4-01 is building in parallel on `task/W4-01-work-case-core`.

Answer each of the 7 questions with exact artifacts (file/function names, literal predicates, JSON, test names). Also confirm or replace each of the 8 readings. Question 1 is a cross-lane ownership problem. Rule it so neither lane edits the other's files, by giving the exact commit and merge order between the lanes, and amend the sequence's ownership table if needed.

Append the result as "Run 1 rulings (q1)" to `.agent/W3-01-build-spec.md`, and to `.agent/post-W2-sequence.md` if ownership changes, amending `D-2026-10-20-w4-01-w3-01-buildspec`. Write nothing else. Do not commit.
