# TEL-05b re-review (fresh Claude reviewer, 2026-10-28)

This re-review covers branch `task/TEL-05b-finding-money-withheld` at `29050394`. It checks the fix for the previous review's H1 (`.agent/TEL-05b-review.md`), judged against the ruling TEL-05b-Q4 (`.agent/TEL-05b-questions.md`, build spec section L).

## Verdict: ACCEPT

H1 is closed. My independent fresh-DB run of the Postgres gate passed: `SKIPPED_LATE 0`, and steps 1-6 were green. The fix matches the ruling, the oracle is unchanged, and the TEL-04 end-to-end file still passes. There are no High or Medium findings. The Lows below can be fixed on the branch or carried, at the coordinator's discretion.

## Ruling conformance

- **`ModbusTcpClient.open()` (`field/assetops_field/modbus_tcp.py:61-72`).**
  - If a socket is already set, it returns True.
  - Otherwise it calls `create_connection` with `timeout_s` and sets `TCP_NODELAY`, as `_connect` does.
  - On an `OSError` it returns False and leaves `_socket` None.
  - It sends no bytes, writes no capture line and changes no counter.
  - It matches the ruling, except for L2.
- **`main()` (`field/assetops_field/modbus_poller.py:547-551`).**
  - It builds the client and calls `open()` before `clock.sleep_until(session_start)`.
  - On failure it prints one stderr line and continues.
  - The same client object is passed to `Poller`.
  - The START line is unchanged.
  - The first read still connects lazily through `_connect` when the warm-up fails, so the outcome and fault paths are unchanged.
- **The oracle is not weakened (`host/tests/test_field_modbus_tcp_acceptance_postgres.py:507-513`).**
  - `assert arrived == expected` and `run.exit_line[1]["counters"] == counters` are still exact.
  - `_expected_run_2` still expects zero `SKIPPED_LATE`.
  - `_print_capture_for_mismatch` (`:354-363`) only prints, and runs only on a mismatch. Its keys (`at`, `wall_at`, `scheduled_at`, `row_id`, `outcome`) exist in the capture lines (`modbus_poller.py:241-246`). Skip lines carry `outcome` `SKIPPED_LATE` (`:231`), so the `"SKIP"` filter catches them.
- **Unit tests.**
  - `test_open_warms_the_connection_before_the_first_read` (`field/tests/test_field_modbus_tcp.py:261`) pins that `open()` is idempotent, sends no bytes, and that the next read reuses the same socket with one frame.
  - `test_open_against_a_closed_port_returns_false_and_the_read_reconnects_lazily` (`:272`) pins the False return, that `_socket` stays None, and the lazy `NO_ANSWER`.
  - Accepting `TIMEOUT` as well as `REFUSED` follows the existing closed-port test (`:192`); Windows can time out a refused loopback connect.
- **TEL-04 behaviour.** The only change on the TEL-04 path is that the connect now happens before the first read instead of inside it. `test_field_modbus_tcp_proof.py` passes 11/11.

## Findings

### High
None.

### Medium
None.

### Low

**L1. The warm-up failure line leaves out the error.** At `field/assetops_field/modbus_poller.py:549-550`, the ruling asks for `FIELD-POLLER warm connect failed: <error>`. The code prints `could not connect to host:port`, because `open()` swallows the `OSError` (`modbus_tcp.py:68-69`). That costs diagnostic value on the board (TEL-08), where refused, unreachable and timeout matter. Fix: have `open()` keep or return the last error, for example a `last_open_error` attribute, and print `str(error)`.

**L2. `setsockopt` is outside the `try` (`field/assetops_field/modbus_tcp.py:70`).** An `OSError` from `setsockopt` would leak the connection and escape `main()`, where this code is outside the configuration `try`. The ruling says "on any OSError ... returns False". In practice this does not happen on TCP, and `_connect` has the same shape. Fix: move `setsockopt` inside the `try`, and close `connection` on failure.

**L3. Nothing at unit level pins that the poller calls `open()` before `sleep_until`.** The unit tests cover `open()` itself. The ordering in `main()` is evidenced only by the end-to-end run below, where the delta at 03:00:00Z was 0 ms. That is acceptable. A small `main()`-level test, with a fake client that records `open()` before the clock sleep, would guard it against a refactor.

**L4. The packet still has the ruling item 4 margin evidence as "pending" (`.agent/TEL-05b-review-packet.md:104-105`).** The builder's own Postgres run was held. My run's numbers are below; the packet should record them, or the builder's, and close the residual-risk line.

**Carried from the previous review:** L1 (the PRICED check over the whole Site, `test_field_modbus_tcp_acceptance_postgres.py`, step 2 area) and L2 (claim wording, for TEL-07). Neither was changed in this round, and neither blocks.

## Checks run (revision `29050394`, Lane T PYTHONPATH on `AssetOpsV1-tel5b`, plan2 venv)

The process list showed no other Python, pytest, node or chrome processes before the runs. Keep-awake was running, and the jobs ran one at a time.

1. `pytest field/tests`: **152 passed** in 13.0 s.
2. `pytest host/tests/test_field_modbus_tcp_proof.py` (TEL-04): **11 passed** in 227.2 s (wall 228 s).
3. The TEL-05b Postgres gate, `-k profile_2`, alone:
   - **Database.** `assetops_tel5brr_test` was freshly created in `assetopsv1-postgres-1` at 127.0.0.1:55432 and dropped afterwards with `WITH (FORCE)`.
   - **Result.** **1 passed in 548.21 s** (wall 550 s). JUnit: tests=1, failures=0, errors=0, skipped=0.
   - **Poller counters.** `VALUE 3170, SKIPPED_LATE 0`, and all other counters 0. All 3170 capture lines are `WORDS`.
   - **Margin (ruling item 4).** The SoC send `wall_at` minus the generator-status send `wall_at` was **0 ms at 03:00:00Z**: both reads were at replay 03:00:01Z, and the capture resolves to 1 ms. The maximum over 97 boundaries was **3 ms**, at 08:15:00Z. The budget is 33 ms.
   - **Step 1.** One Finding, `9afa379d...` (window 2026-10-13 CURRENT), on 802 accepted evidence rows covering all six dispatch roles.
   - **Step 2.** Provenance assertions passed.
   - **Step 3.** The price publication was recorded.
   - **Step 4.** Recompute succeeded, and a PRICED consequence revision `eced9a4e...` was appended.
   - **Step 5.** The Finding index returned 409 `PERFORMANCE_CUTOVER_CLOSED`. The Finding and consequence reads show `presented_as_current: false`.
   - **Step 6.** Currentness shows `money_eligibility ELIGIBLE` and `current_amount_shown false`, with the source gate `permits_current_money false`. The test asserts the exact reason list.
   - **Logs.** Kept in the reviewer scratchpad.
4. Both guards were run directly, without `-ExecutionPolicy Bypass`, and with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv. `check-architecture.ps1`: **passed**. `check-agent-workflow.ps1`: **passed**.

Not run: the full backend suite, frontend checks (there is no frontend change), and the TEL-05 Postgres gate (the ruling excludes it).

## Residual risk

- One green run shows the cold-connect cause is removed: the 03:00:00Z delta was 0 ms. It does not bound the rare late-wake exposure the ruling names for TEL-04/05 (about 33 ms at rate 60).
- TEL-08 (BeagleBone, rate 12): the margin after warm-up there is the board's own latency, including SD-card capture appends. The exact-oracle rule and the stop rule carry over, as the ruling says.
