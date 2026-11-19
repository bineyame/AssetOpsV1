> Finished; historical. Archived from .agent/MB-1-rereview.md on 2026-11-18 (declutter step 4).
# MB-1 re-review (fresh Claude reviewer, 2026-11-13)

Fix round 6953f9ca5 on `task/MB-1-modbus`, reviewed as `git diff 46b2e3ece 6953f9ca5` (5 files) against the review's
L1-L4 and two nits.

## Verdict: ACCEPT

All four Lows and both nits are fixed. I found no new High, Medium or Low defects; there are two nits below and the
Postgres step is still pending.

## Findings addressed
- **L1 fixed.** `tools/demo_combined.py:1726`: serve's `finally` calls `live_field.stop(self.work)` after it kills the
  helpers. This runs on any exit, including a failed API. A behavioural test covers it
  (`test_serve_with_the_switch_starts_the_gateway_and_always_stops_the_live_field`: the API stub raises, and stop is still
  called with the work dir).
- **L2 fixed.** `tools/demo_live_field.py:305-315`: the READY wait, the poller spawn, the pids write and the poller wait now
  sit in one `try`, and any `Exception` calls `stop(work)`. The emulator PID is written before the `try`, so `stop` can
  find it.
- **L3 fixed.** `is_ours` checks `/proc/<pid>/cmdline` for `gx_server` or `modbus_poller`. `stop` uses it before it
  signals, and `start` uses it before it refuses with "already running". `stop` deletes `pids.json` either way. A zombie
  child (empty cmdline) is correctly treated as not ours. Without /proc, liveness alone decides, as the docstring says.
  The new test checks this with a real PID that is not ours (the pytest process).
- **L4 fixed.** The source-string match is gone. Two behavioural serve tests cover the switch on, off and `OTHER-001`.
  The flow test now asserts `latest_accepted` covers every profile row, `overlap_refusal` is non-empty at START and empty
  at STOP, and `disabled_sources == []`. It also checks that `OVERLAP_SQL` finds an interval shifted by 150 s, with the
  trigger disabled only inside a transaction that is rolled back. The parameters `t/site/epoch/lo` match the SQL.
- **Nit (shared source) fixed.** `latest_accepted` now maps each source to all of its signals.
- **Nit (switch validation) fixed.** `live_switched_on` requires `KOBO-001`, matching UP-1's switch. `start` still checks
  `switched_sites` for the Site it is asked to start.

## New nits (do not block)
- `tools/demo_live_field.py:313` `except Exception` does not catch `KeyboardInterrupt`. A Ctrl-C during `start`'s waits
  leaves the children running. Both PIDs are already in `pids.json`, so `live-field stop`, or serve's new `finally`,
  recovers them.
- `is_ours` matches a substring (`gx_server` / `modbus_poller`). Matching the full `EMULATOR` path or the module
  `assetops_field.modbus_poller` would be stricter. The chance that a reused PID's cmdline contains either word is
  negligible.

## Checks I ran (worktree HEAD 6953f9ca5, PYTHONPATH = worktree parts)
- `pytest host/tests/test_mb1_live_field.py host/tests/test_up1_demo_upload_gateway.py field/tests/test_field_gx_emulator.py -q`
  -> **58 passed** in 6.3 s. This matches the packet's 58, which is up from 55.
- No `gx_server` or `modbus_poller` processes were left after the run. The worktree was clean.
- **Not run:** `host/tests/test_mb1_live_field_flow_postgres.py`. A heavy DB job is running, and the lane rules allow
  no Postgres. Its new assertions were checked by reading only. The packet reports 1 passed in 134 s on
  `assetops_mb1_test`; this is the coordinator's step to confirm. check-all is also left for the coordinator.

## Residual risk
Unchanged from the first review. The demo-DB bench run is still pending: profile -2 binding, `enable-source`, real
60 s backstop lag, and re-warming after the live beat (D-WARM.4).
