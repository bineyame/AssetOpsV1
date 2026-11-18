# Architect request: W3-01 q2 (before Lane A's compatibility commit)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide" and "Token Efficiency";
- `.agent/W3-01-build-spec.md`, including Run 1 rulings (q1);
- `.agent/W3-01-pending-rulings.md`, which holds 2 questions and 5 readings;
- `.agent/W3-01-lane-a-adapter-contract.md`.

The code is on branch `task/W3-01-estate-claim-action-roots` at `d811232b` (`git show 990f2113`, `git show 2951b66c`).

Answer both questions with exact artifacts:
- Q1: the literal `source_provenance` value, or the refusal, when there is neither a selected row nor a pending set.
- Q2: the exact cold "full newer accepted set" query, with tables and predicates, and whether EV builds the pending block on every pending read.

Confirm or replace each of the 5 readings. Then dry-read the adapter contract as Lane A, against the Lane A call sites listed in ruling 1, and answer in advance any question still open. If nothing is open, say so in one line.

Append the result as "Run 2 rulings (q2)" to `.agent/W3-01-build-spec.md`. Write nothing else. Do not commit.
