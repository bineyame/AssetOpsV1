# COV-PARTIAL handoff (implementer)

Branch `task/COV-PARTIAL-estate-coverage`, worktree `AssetOpsV1-covp`.

Landed (commits on top of `0796218fc`):
- U1 `36ab2f54a`: coverage rule and wire.
- U2 `eac8556df`: Portfolio status, X1, X2.
- U3 `b44f86572`: frontend.
- U4 `282cedb90`: Postgres proof, the `:561` edit, and the golden.
- Docs commit: task file, DECISIONS entry, register and built state.

Still to do:
- Golden replay without the write flag, plus the U4 focused Postgres set. Both wait for `assetops-ops03-*` to be idle.
- Captures at 390 and 1440 with producer `tools/s404_finding_index_walkthrough.py --db assetops_s404_owner_covp_test`.
  `var/sites/kobo-001.yaml` was copied from plan2; it is local and ignored.
  - Set `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX` for serve.
  - Pick a window from the estate API: clean checked days plus gaps. The 10-27 day is dirty and 11-05 failed, so
    keep both out of the window.
  - Afterwards: drop the DB, then stop the servers by PID.
- Write the packet `.agent/COV-PARTIAL-packet.md` (force-add) and update this handoff.
- The full vitest run and `-Tier all` happen only on the coordinator's go, after LINK-LINEAGE merges.

Notes:
- `vitest related` fails here because the import graph pulls in a `.py` file. Run the scoped test files directly
  (estate tests plus the shell routes, globalMaintenance, t028Vocabulary and idxGapsFindingIndex).
- Postgres runner: scratchpad `ptpg.ps1`, against DB `assetops_covp_test`, which I created and still need to drop
  at the end.
