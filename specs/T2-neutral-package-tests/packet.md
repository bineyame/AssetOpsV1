# T2 review packet

Branch `task/T2-neutral-package-tests`, worktree `/opt/assetecon/wt-T2`. Standard review. No user review needed
(`USER_REVIEW_REQUIRED`: tools only). Databases, servers, Docker: not touched.

**Deviation to know.** The dispatch said the spec rev 2 sources are on main; main (8a8df5830) held rev 1. They are on
`task/T2-handshake` (d6b7a0026, merge of the answers). I fast-forwarded the task branch to d6b7a0026 first, so
`git diff main...HEAD` also shows the handshake files until that branch merges. Mid-build questions: **0**.
Spec rev 2 has no Status line; I added `Status: in_review`.

## Commits
- f262ab16d T2: guard, self-test, select-tests neutral key, TESTING bullet (the five spec files)
- a closing commit: packet, state entry, index line, spec status.

## Done criteria
| Criterion | Result |
|---|---|
| 1 check-all fails on a simulator/contracts failure, incl. child test | Yes: planted test in test_core.py gave `[FAIL] Neutral package tests (T2)`; R2 break failed the child test |
| 2 guard tests this tree even with main first on PYTHONPATH | Yes (R2 proof) |
| 3 missing folder, empty collection, below-floor fail; self-test proves | Empty, failing and below-floor proven by --self-test; missing-dir and missing-module are plain code paths, not self-tested |
| 4 select-tests names neutral for every trigger, not markdown; guarded | 5 pytest cases in check-all; manifest and the three tools triggers are in NEUTRAL but have no case (spec lists five) |
| 5 nothing else changed | Yes, apart from the state entry, index line, spec status |

## R2 proof
Break: `raise RuntimeError("T2 R2 deliberate break")` inserted at line 430 of the worktree's world/history.py.
`PYTHONPATH=/opt/assetecon/AssetOpsV1/simulator:/opt/assetecon/AssetOpsV1/contracts` set first (a bare
`import assetops_simulator` under it resolves to /opt/assetecon/AssetOpsV1/simulator, i.e. main).
- Red: exit 1, `58 failed, 403 passed`, including `test_t8_extreme_exponent_refuses_fast[...]` (the child test; failing
  at test_history.py:372, child stderr showing `RuntimeError: T2 R2 deliberate break` from the worktree's history.py:430).
- Reverted (`git checkout --`), same PYTHONPATH: exit 0, `461 passed`.
- In the guard's own process after set_paths: /opt/assetecon/wt-T2/simulator/assetops_simulator/__init__.py and
  /opt/assetecon/wt-T2/contracts/assetops_contracts/__init__.py. Child process (sys.executable -c): same two paths.

## Counts (R6)
Combined: simulator/tests 455, contracts/tests 6 (461). Separate runs: 455 passed, 6 passed. Equal. Test module
basenames are unique across the two folders (a `find | uniq -d` listed none). Note: pytest's rootdir moves to the
package's own pyproject, so nodeids are not prefixed `simulator/tests/`; the counter matches on each item's
absolute path (my first version matched nodeid prefixes and counted 0; the floor caught it).

## Timing
- Idle-ish (load average 4.7 on 8 cores, not fully idle): script 6.3 and 6.5 s wall (pytest 5.7 s). In check-all: 6.7 s.
- Under load (8 busy loops on 8 cores): 9.3 s (pytest 8.5 s). Red check-all run: 7.9 s.
- Select-tests test: 38.2 s in check-all (each of 5 subprocess calls builds the import graph, about 7 s). Not the
  longest guard (Heavy-slot pool self-test 31 s, only when a pool file changes) but the longest always-on one in this run;
  a follow-up could batch the five calls; the spec asks for a subprocess per case, so I did not.

## check-all summary lines
- Before (d6b7a0026, fast): `check-all: inside a held heavy slot (/opt/assetecon/AssetOpsV1/.git/check-all-slots/slot-2.lock); not taking another. check-all: 45.3 s wall (0.2 s waiting for a slot), 4 jobs at once. All 37 guards passed (blocking; 0 advisory, 0 warned). `
- After (fast, via tools/heavy-slot.sh): `check-all: inside a held heavy slot (/opt/assetecon/AssetOpsV1/.git/check-all-slots/slot-2.lock); not taking another. check-all: 81.2 s wall (0.2 s waiting for a slot), 4 jobs at once. All 41 guards passed (blocking; 0 advisory, 0 warned). `
- 37 to 41 is +4, not +3: the conditional "Heavy-slot pool and tripwire self-test (T1)" runs now because check-all.ps1
  changed. The T2 guards are three.
- Red (planted assertion in simulator/tests/world/test_core.py, reverted): `check-all: inside a held heavy slot (/opt/assetecon/AssetOpsV1/.git/check-all-slots/slot-1.lock); not taking another. check-all: 83.2 s wall (0.2 s waiting for a slot), 4 jobs at once. Check failed: 1 of 41 blocking guards (0 advisory, 0 warned). `; `[FAIL] Neutral package tests (T2)`
  with `FAILED simulator/tests/world/test_core.py::test_t2_planted_failure`.

## Not done
No contracts/tests planted failure (the red proof is the simulator one; the self-test covers the runner); no
validate-test-selection.py cases (that file asserts nothing for these).
