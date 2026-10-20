# Architect request: W3-01 q10 (mixed golden, missing states, and a page-two 409 risk)

Read `.agent/W3-01-build-spec.md` (all rulings through q9) and `.agent/W3-01-pending-rulings.md` q10.

Code: branch `task/W3-01-estate-claim-action-roots` at `da3f6f3c`.

Rule each item with exact artifacts:
1. The golden `mixed` branch has no cases, because each replay fixture builds its own DB. Name the fixture path that puts mini-grid, cold and EV in one DB, or rule an honest limitation, with the test assertion either way.
2. No replay produces STALE, LEASED or FAILED states. Name an exact test-only path for each state, or rule which are proven by unit tests only.
3. Risk raised by the builder: a live first page with open cold/EV jobs gets a 409 on page two, under q8 rulings 2 and 6 as written. Confirm that this is intended (a fence after a selection change), or correct the predicate. Give a test.
4. The EV q7 proof bypasses the append-only `ingestion_disposition` trigger with `session_replication_role = replica` on the test DB. Accept it, or name the alternative.

Append the result as "Run 10 rulings (q10)" to `.agent/W3-01-build-spec.md`. Write nothing else. Do not commit.
