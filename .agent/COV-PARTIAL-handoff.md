# COV-PARTIAL handoff (implementer)

Branch `task/COV-PARTIAL-estate-coverage`, worktree `AssetOpsV1-covp`. Built and packeted; the slice is ready for review.

Landed on top of `0796218fc`:
- U1 `36ab2f54a`, U2 `eac8556df`, U3 `b44f86572`, U4 `282cedb90`.
- Docs `ea8fcef3e` and `4188e17c7`.
- `28fcf3965`: the cold exact coverage literal gains `days: None`, found by the U4 replay.
- `2a8b96f64`: the packet `.agent/COV-PARTIAL-packet.md` and `.agent/COV-PARTIAL-captures/`.

Done:
- Golden replay without the write flag: passes.
- U4 §5 Postgres set: 168 passed. Of the 2 failures, one was genuine and is fixed; the other is the known
  `INVALID_CURSOR`.
- Captures at 390 and 1440: 12/12 claims pass.
- Non-vacuity proofs and check-all: 11/11 guards pass.
- Both DBs are dropped and the servers are stopped.

Still to do (on the coordinator's go, after LINK-LINEAGE merges):
- One `-Tier all` on an idle machine.
- One full `npx vitest run`.
- Then a slice review.

Notes:
- `.venv` in this worktree is a junction to plan2's venv. It is ignored.
- Five orphaned gateway processes from a stopped test run remain: PIDs 2592, 2052, 22440, 31564 and 7664. Stopping
  them was refused by the permission classifier.
