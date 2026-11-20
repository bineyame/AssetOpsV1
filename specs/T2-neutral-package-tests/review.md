# T2 review, round 1 (fresh Claude reviewer, head b983931c5)

Verdict: ACCEPT with Lows. 0 High, 0 Medium, 3 Low.
- R2 proof rerun: break in world/history.py, main first on PYTHONPATH: exit 1, 58 failed / 403 passed, incl. test_t8_extreme_exponent_refuses_fast (child, test_history.py:362); reverted: exit 0, 461 passed.
- Guard and child both load this tree's assetops_simulator and assetops_contracts.
- Missing contracts/tests: `FAIL neutral tests: missing contracts/tests`, exit 1.
- --self-test 0.6 s, four cases hold. Counts 455 + 6, floors 400 / 1.
- Fast check-all: `All 41 guards passed (blocking; 0 advisory, 0 warned).` 87.9 s.

## Findings
- L1 (efficiency) tools/checks/test_select_tests_neutral.py:13-16: five subprocess calls, each rebuilds the import graph
  (37.5 s total, always on). Neutral depends only on the changed paths. Fix: load select-tests.py with importlib
  (hyphenated name), call `select([path], graph=(set(), {}))` in process for four cases (instant), keep ONE real
  subprocess for the CLI/JSON shape (the world_history case, ~7 s). One assertion per case kept. Spec §2.5 line 64 says
  "subprocess", so this is a spec-text change: do it as a follow-up or fold in now; not a merge blocker.
- L2 (acceptance gap, minor) tools/checks/neutral_tests.py:117-129: self-test covers failing/empty/below-floor and the
  message string only. The missing-dir, missing-module and the actual import-root check in main() are plain code paths,
  proven by my manual run (missing dir) but not guarded. Cheap fix: move the dir and root checks into a function taking
  (root, dirs) and call it on a temp tree in --self-test. Not a blocker: done criterion 3 names "self-test proves", but
  the shipped paths are short and I exercised them.
- L3 (gap) NEUTRAL manifest and tools triggers (select-tests.py:61-64) have no case; spec lists five. A one-line
  parametrized in-process case per trigger is free once L1 is done. Do it with L1.
- No contracts/tests planted failure: not needed. The runner is path-generic and the per-folder counter plus floor covers
  contracts (6 >= 1); the simulator proof exercises the same code.

## Which gaps must close before merge
None. L1 to L3 can be one small follow-up (tools only), preferably together.

## Notes
- check-all.ps1 diff is three guard lines and a comment, as scoped; scope otherwise matches the guide.
- DB var removed, no slot used. PYTHONPATH set before pytest.main (D-T2.2 satisfied).
- Not verified: red check-all run quoted in the packet (rerun only the R2 equivalent). My first check-all run showed
  2 failures (Missing-claim scans) caused by my scratch worktree lacking frontend/node_modules; with it linked, 41/41 pass.
- Residual: a pytest `-p` plugin conflict or pytest-xdist config in a package pyproject would silently change counting;
  the floors would catch undercounting.
