# Architect request: W3-02 `0b` review (r1)

Read `.agent/W3-02-build-spec.md` (closures 4–5, the W1 day section) and `.agent/W3-02-0b-review.md`.

Code: commit `d208faef` on `task/W3-02-estate-evidence-money-basis`.

Rule with exact artifacts:
- M3. At an old explicit cutoff, the day still carries a current ceiling. That contradicts "Historical selection keeps IDs but no current claim" (spec line 26). Give the exact HISTORICAL day shape: which fields are null, and the copy.
- The Architect-flagged readings:
  - a role-tagged conflict is CONTRADICTORY even when the day is HISTORICAL. Give the precedence.
  - `GENERATOR_UNOBSERVED` per role can produce up to 5 identical gap groups. Should they be deduplicated? Give the exact grouping key.
- Confirm the mechanical fixes M1 and M2:
  - M1: patch `_connect_engine` and `_run` in the single-transaction trap.
  - M2: drop the single-interval `revision_id` mode, or check membership. Choose one.

Append the result as "0b review r1 rulings" to `.agent/W3-02-build-spec.md`. Write nothing else. Do not commit.
