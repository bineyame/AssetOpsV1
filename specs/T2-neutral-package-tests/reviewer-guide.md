# T2 reviewer guide

Standard review. Check:
- **Scope.** The diff holds only `tools/checks/neutral_tests.py`, `tools/check-all.ps1` (one guard line and its
  comment), `tools/select-tests.py`, `backend/TESTING.md`, the packet and the bookkeeping.
- **The planted failures in the packet are real.** Plant one yourself in `simulator/tests/world/test_core.py` and run
  check-all fast: it must fail, naming "Neutral package tests (T2)". Revert it.
- **This tree, not main.** Run the script from a worktree with `PYTHONPATH` set to main's `simulator` first. The run
  still imports the worktree, or it fails with the probe message. It never silently tests main.
- **No database.** `ASSETOPS_TEST_DATABASE_URL` is removed before pytest starts, so no slot is needed and no conftest
  asks for one.
- **select-tests.** Run the two `--files` cases of spec §3; `neutral` is true for a simulator change and false for a
  backend-only one. The backend selection for a simulator change is the same as before.
- **No empty pass.** An exit code of 5 (no tests collected) fails the guard.
