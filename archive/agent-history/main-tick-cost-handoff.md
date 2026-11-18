# main-tick-cost handoff

Branch `fix/main-tick-cost` from main `439c6127`. Not merged.

## Finding: not a code regression

`TestTickCost::test_measure_a_real_child_tick_over_one_and_four_sites` passes on
unchanged main code when the host is awake:

- Alone, instrumented (debug print, reverted): 1 passed in 49.8 s. Four-Site idle
  tick 17.3 s wall, all 4 visited COMPLETED, each Site s3/s4/consequence child
  1.0-1.4 s, reconcile 447 ms. Baseline in CODE_STATE (S4-02d): 12.6 s for 4 Sites.
  The tick budget is `TickLimits.tick_seconds = 240` (`scheduling/tick.py:231`),
  so a 3-of-4 visit needs ~80 s per Site - 20x the measured cost.
- Focused S4 tick + health files: 18 passed in 311 s (TickCost 22 s).

Cause of the observed failure and the 47-minute suite: the laptop entered
Modern Standby mid-run. System log (Kernel-Power 506/507):

```
22:20:39 506 entering  Reason: Idle Timeout
22:21:40 507 exiting   Reason: Input Keyboard
22:25:17 506 entering  Reason: Idle Timeout
22:31:04 506/507       Reason: Austerity Battery Drain Budget Exceeded
22:49:30 507 exiting   Reason: Input Keyboard
23:01:09 506 entering  Reason: Idle Timeout
```

During standby the processes are throttled while wall/monotonic time advances,
so the tick's 240 s budget runs out after 3 Sites and the remaining Site is
DEFERRED (`visited()` = 3). This session reproduced the stall itself: a focused
run started 23:21 sat at 27 CPU-seconds for 80 minutes (Wi-Fi adapter D3 cycling
every 3 min, shell commands frozen), then the same files completed in 5 min once
the session was active.

`tools/keep-awake-during-tests.ps1` set only `ES_SYSTEM_REQUIRED`, which does not
stop the display idle timeout from entering Modern Standby on this machine.

## Fix (commit 7363a6f9)

- `tools/keep-awake-during-tests.ps1`: also requests `ES_DISPLAY_REQUIRED`, with
  the reason in the header comment.
- `backend/TESTING.md` (Before a long full run): states the display hold and how
  to check System events 506/507 before reading a slow or budget-bound failure as
  a regression.

No product code or test changed. The tick budget is untouched (not a product
decision to make here: the product cost is ~4 s per idle Site, about +35% over the
S4-02d baseline, well inside the bound).

## Slowdown attribution

- Not product cost: idle per-Site tick ~4.3 s (was ~3.2 s).
- Real but small test cost from S4-07: `TestStaleWithoutJob` now takes ~125 s
  (S4-07 widened its override skew from 20 s to 120 s, which the test waits out).
- Rest of 47 min: standby.

## Checks

- Focused: `test_s4_schedule_tick_postgres.py` + `test_s4_schedule_health_postgres.py`:
  18 passed in 311 s (TickCost 22 s).
- Full suite at `7363a6f9`, PowerShell, keep-awake (display hold) running:
  `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=30 --junitxml=.pytest-junit.xml`
  on `assetops_mainfull_test`: 2244 passed in 606 s (wall 10:07). JUnit cases=2244
  skipped=0 failed=0. No 506/507 standby events during the run.

## Open

- Keep-awake still cannot stop lid-close or power-button sleep, nor battery
  austerity standby; long runs should be on AC with the lid open.
- `.pytest-junit.xml` in the worktree root is a run artifact, not committed.
