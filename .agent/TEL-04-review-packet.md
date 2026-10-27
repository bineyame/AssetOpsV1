# TEL-04 review packet: poller and focused end-to-end through a real gateway process

PowerShell PYTHONPATH (build sequence 1, `-tel` replaced by `-tel4`):
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-tel4\backend;C:\Users\assef\Bineyame\AssetOpsV1-tel4\contracts;C:\Users\assef\Bineyame\AssetOpsV1-tel4\simulator;C:\Users\assef\Bineyame\AssetOpsV1-tel4\gateway;C:\Users\assef\Bineyame\AssetOpsV1-tel4\host;C:\Users\assef\Bineyame\AssetOpsV1-tel4\field;C:\Users\assef\Bineyame\AssetOpsV1-tel4"
$env:ASSETOPS_GUARD_PYTHON = "C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe"
```
Interpreter `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` (3.12, pymodbus 3.16.1). `import assetops_gateway, assetops_field` resolve to `AssetOpsV1-tel4`.

- Task: TEL-04 only (build spec TEL-04; Q-T1..Q-T70; section J incl. TEL-T1-Q6 and Q7; rulings 2026-10-27).
- Branch `task/TEL-04-poller` from T1 head 3bbce526. Build commit `346909a0`. No Postgres, no full suite.
- Questions left open (uncovered, not decided in code): `.agent/TEL-04-questions.md` (Q1-Q4; Q5 confirms a gate-7 reading).

## Files changed

- `field/assetops_field/modbus_poller.py` (new): CLI, `new_session_ref`, `session_stamp`, the lazy merged schedule, `Poller`.
- `host/tests/field_bench.py` (new, stdlib): `expect_identity_from_snapshot`, `cohort_members`. TEL-08 subcommands not added.
- `host/tests/test_field_modbus_tcp_proof.py` (new): 4 E2E tests, the `new_session_ref` unit test and one exit-2 subprocess test.
- No change to gateway, backend, contracts, simulator, host product modules, the guards or other field modules.

## What landed

- Loop as spec step 1-5. The order is: load profile, then clock, then `check_identity`, then `release_previous` (`seal`, then `release_run(previous_ref)`) if `session.json` exists, then `session_start` (clamped to `--replay-start`), then `session.json`, then START. The poller seals and releases at every publish instant, and runs one final `seal_and_release` after `--stop-at`.
- Reads per 0.7 and 0.8:
  - The first state attempt goes at `B+⌈skew/2⌉`. A retry is sent only by `B+skew`, and a late first attempt is `SKIPPED_LATE`.
  - Interval polls sit at mid-period and carry the scheduled `Poll.at`. A retry is sent only before `P+period/2`.
  - Only TIMEOUT, 04 and 06 are retried. A `CONFIG_FAULT` faults the whole row: its current result still closes, and later results are dropped.
- Records:
  - one raw-capture line per request attempt, skips included;
  - `status.json` written atomically after every publish instant;
  - HOLD lines;
  - exit codes 0/2/3/4;
  - the crash hook (exit 9 after the n-th admit, before the seal). With a non-SIMULATED expected identity, setting the hook exits 2.
- Ops reached: the poller uses only `GatewayPublisher`, so only `identity`, `admit`, `seal`, `release_run` and `diagnostics`. The harness calls `activate`, `deliver` and `diagnostics`.

## Gate evidence (`host/tests/test_field_modbus_tcp_proof.py`, rate 120, 06:00Z-08:00Z, `--read-timeout-s 0.25`)

| Gate | Evidence |
|---|---|
| 1 ack | `test_clean_window`: after `deliver_all`, gateway SQLite `envelope_outbox` states == {ACKED: n}. Every `upload_batch` is ACKED, there are n `acknowledgement` rows, n == `status.admissions.ADMITTED`, and the posted message IDs == the gateway envelopes. |
| 2 sentinel/02 | `test_faults`: PV 06:30Z, 06:45Z and SoC 06:45Z, 07:00Z envelopes are `UNAVAILABLE/NO_MEASUREMENT`. `holds_by_kind == {}` and there are no HOLD lines. |
| 3 unit W | `test_unit_w`: exit 0. `holds_by_kind == {"UNIT_INCOMPATIBLE": 2}`. There are 2 HOLD lines with the expected report keys, and 0 `envelope_outbox` rows for the PV source (no sequence). |
| 4 repeat | In-process `GatewayPublisher` re-admits the SoC 06:00Z text and gets `ALREADY_ADMITTED`, with `message_id ==` the `report_admission` row. |
| 5 conflict | The same key with value+1 is `HELD CONFLICTING_REPORT`. |
| 6 drop | The first two batch POSTs are DROPped. Each dropped body appears exactly twice. Batch requests == batches + 2. |
| 7 pause -> no report | `test_faults`: there is no SoC envelope at 07:15Z and no PV envelope at 07:30Z. For both sources, the diagnostics `last_contact_at` is unchanged across two reads ≥ 3.5 s of wall time apart inside the pause, and `observed_at - last_contact_at` grew by ≥ 2 s. A guard asserts the second read was still before the 07:30Z publish. Mutation proof below. |
| 8 counters | `status.counters ==` the oracle counts, computed from the fault windows, the schedule and the timeline (NO_VALUE 8, NO_ANSWER ≥ 8, FAILED/CONFIG_FAULT/SKIPPED_LATE 0). Raw capture: TIMEOUT lines ≥ 7, TID_MISMATCH lines 4, EXCEPTION_02 lines 2, and every line carries the profile SHA. |
| 9 writes | `emulator.writes == 0` (clean and faults). |
| 10 activation | `activate` returns `{"snapshot_sha256": sha256(snapshot_text)}`, and `mapping_error_count == 0`, in every test. |
| 11 first GOOD | Clean run: START `session_start == 06:00:00Z`, and PV 06:15Z is GOOD with `interval_start 06:00Z`. |
| 12 restart -> no stranded batch | `test_restart`: the crash run exits 9 with no EXIT line and leaves unbatched outbox rows (> 0, asserted). The restart exits 0. START `previous_ref ==` the killed `session_ref`, and the new ref differs. The first PV interval after restart is `NO_COMPLETED_INTERVAL` with span start `E-900 < session_start`, and the next one is GOOD. After the gateway is killed, SQLite read-only shows (STAGED batches, unbatched STAGED/READY outbox) == (0, 0). Mutation proof below. |
| Q7 values | Every arrived report equals the oracle exactly. GOOD values use `quantize_half_even(presented_value(row, obs), output_resolution)`, compared as Fractions, plus the independent `abs(arrived - obs) <= q/2` bound on every GOOD report (count > 0 asserted). |
| Q6 | `test_session_ref_format_with_an_injected_token`: `field:gx-system-illustrative-1:1:20261027T090807Z:0a1b2c3d`. Bad tokens are refused. |

**Mutation proofs** (on committed `346909a0`, then `git checkout --`; the tree was clean after each):
- `release_previous` call replaced by `pass`: `test_restart` fails with `assert (2, 0) == (0, 0)`. Without the release, the new seal sweeps the killed session's envelopes into batches that `release_run` skips, so they stay stranded STAGED.
- In `poll_state`, NO_ANSWER attempts rewritten as NO_VALUE (publishing on a paused read): `test_faults` fails, because a SoC `07:15:00Z UNAVAILABLE/NO_MEASUREMENT` envelope arrived.

## Commands run

| Command (cwd worktree, basetemp `%TEMP%\assetops-tel4\<name>`) | Result |
|---|---|
| `pytest host/tests/test_field_modbus_tcp_proof.py -q -p no:cacheprovider --durations=0` (final, `346909a0`) | **6 passed in 228 s** (clean 70.9 s, faults 66.5 s, restart 66.3 s, unit W 21.2 s, exit-2 1.0 s, session ref <1 s) |
| `pytest field/tests -q -p no:cacheprovider` | 146 passed in 9.0 s |
| `tools/check-architecture.ps1` | Architecture check passed (exit 0) |
| `tools/check-agent-workflow.ps1` | Agent workflow check passed (exit 0) |
| the 2 mutation runs above | each 1 failed as intended; reverted |

## Known deviations and interpretations

1. **FakeCentral responder (Q-T46).** `deliver` also runs the gateway's diagnostics pass. With the spec's `(200, receipt_text(body))` for every path, the diagnostic POST crashes `receipt_text` (`UNKNOWN_FIELD clock_offset_ms`). The harness therefore sends batch-route posts to the Q-T46 responder, and answers diagnostic posts as `gateway/tests/test_gateway_upload.py:503-506` does (201 with the payload SHA). DROP applies to the first two **batch** posts, and gate 6 counts batch requests only.
2. **Deliver loop.** A DROP sets a 5 s back-off, so "deliver until `attempted == 0`" ends while dropped batches still wait. `deliver_all` repeats that loop after a 1 s sleep until `queue.sealed_pending_batches == 0`, with a 120 s cap.
3. **Gate 7 read timing:** see Q5. The first read is taken after the last pre-pause publish, not strictly before the pause starts.
4. **Schedule edges.**
   - A state boundary equal to `--stop-at` is scheduled, with its attempt at stop+1 s.
   - Interval polls are taken when `>= session_start`.
   - Counters count the final outcome per poll. A late poll counts as `SKIPPED_LATE` only, and is fed to the aggregator as `NO_ANSWER`.
5. **`Poll.at` for state** is `clock.now()` read just before `client.read()`. That read includes a reconnect after a NO_ANSWER, because the TEL-02 client has no pre-`sendall` hook.
6. **Raw capture:** one line per request. A `SKIPPED_LATE` line has `request_hex: null`.
7. **Test placement.** The Q6 unit test and the exit-2 test are in the proof file, because the module map names no new `field/tests` file. `expect_identity.source_mode` is taken from snapshot `gateway.mode`.
8. **Not handled (Q1-Q4):** `GatewayUnavailable` before START or at the final seal (exit 1 with a traceback), retained texts at stop, and no EXIT line on exit 2.

## Residual risk

- State reads depend on wall timing: at rate 120 there are 8.3-16.7 ms of wall time per window. All runs here had `SKIPPED_LATE == 0`. A loaded machine could produce SKIPPED_LATE, which the oracle does not expect, so the test would fail visibly rather than pass wrongly.
- The E2E file takes about 4 minutes and is a heavy job (0.3).

## User-review focus

Q1-Q5 in `.agent/TEL-04-questions.md`; deviations 1-2 (harness responder and deliver loop); gate 7's read point.
