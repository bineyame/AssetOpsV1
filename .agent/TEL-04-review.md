# TEL-04 review: poller and focused end-to-end through a real gateway process

- Reviewer: fresh Claude reviewer (did not author the slice).
- Branch `task/TEL-04-poller` at `164be83c`, diffed against base `3bbce526` (T1 head).
- Authority: build spec TEL-04 (0.6-0.8, gates 1-12, Q-T19..Q-T36, J TEL-T1-Q6/Q7, K TEL-04-Q1..Q5, Dev1..3) and `.agent/telemetry-rulings-2026-10-27.md`.

## Verdict: ACCEPT

There are no High or Medium findings. The Low items below are hardening or test-coverage notes. None is an acceptance gap against the TEL-04 gates or the K rulings, and none blocks the merge.

## Checks run by the reviewer (worktree `AssetOpsV1-tel4`, Lane T PYTHONPATH, interpreter and `ASSETOPS_GUARD_PYTHON` = `AssetOpsV1-plan2\.venv\Scripts\python.exe`)

| Command | Result |
|---|---|
| `pytest host/tests/test_field_modbus_tcp_proof.py -q -p no:cacheprovider --durations=0` | **11 passed in 229.4 s** (clean 71.0 s, faults 66.6 s, restart 66.2 s, unit W 20.9 s). A first attempt errored at setup only because my `--basetemp` parent did not exist. That was my mistake, not a slice defect. |
| `pytest field/tests -q -p no:cacheprovider` | 146 passed in 9.0 s |
| `tools/check-architecture.ps1` (direct, no Bypass) | Architecture check passed, exit 0 |
| `tools/check-agent-workflow.ps1` (direct, no Bypass) | Agent workflow check passed, exit 0 |
| Mutation 1: `publisher.release_previous(previous_ref)` changed to `pass`, `-k test_restart` | 1 failed: `assert (2, 0) == (0, 0)` at proof:693 (two stranded STAGED batches). Reverted, and the tree is clean. |
| Mutation 2: in `poll_state`, NO_ANSWER attempts rewritten to NO_VALUE before `sample`, `-k test_faults` | 1 failed: an extra `state-of-charge 07:15:00Z UNAVAILABLE/NO_MEASUREMENT` was published. Reverted, and the tree is clean. |

I did not run any full suite or Postgres. Everything bound to 127.0.0.1, and I killed no processes.

## Verified points

- **Gates 7 and 12, with mutation proofs.** Both mutations reproduce the failures the packet claims. Gate 7 follows the Q5 ruling:
  - the first diagnostics read waits for `last_publish_instant == 07:15Z`;
  - the second read comes ≥ 3.5 s later;
  - a guard checks that the status still showed 07:15Z, so both reads are inside the pause.

  Gate 12 first asserts that the crash left unbatched rows (`> 0`). That precondition stops the "no stranded batch" assertion from passing vacuously.
- **`release_previous` seals before any new admit.** `GatewayPublisher.release_previous` is `seal` then `release_run(previous_ref)` (publish.py). `main` calls it (modbus_poller.py:534) before `session.json`, START and the `Poller` exist, so no `admit` can come first. Mutation 1 shows the gate depends on it.
- **An unanswered read publishes nothing; a device that answers with no value gives UNAVAILABLE with a span.**
  - `StateSampler.sample` returns `None` unless the last in-window attempt is VALUE or NO_VALUE.
  - `IntervalAggregator.close` returns `None` when no poll was answered. When a NO_VALUE poll is present it returns `UNAVAILABLE/NO_MEASUREMENT` with `interval_start`.
  - `test_faults` checks both through `got == expected`, and that expectation carries the interval start. Mutation 2 shows the "nothing" half is enforced.
- **J Q7 exact comparison.** `expected_value` uses only the existing helpers, `quantize_half_even(presented_value(emulated_row, Fraction(obs)), row.output_resolution)`. Arrived values are parsed as `Fraction` and compared by dict equality, with no float and no tolerance. The independent `|arrived - obs| <= q/2` bound runs on every GOOD report, and the count is asserted to be > 0 and equal to the number of expected GOOD reports.
- **Gateway ops.**
  - The poller reaches the gateway only through `GatewayPublisher._call`, which is limited to `OPS_USED = identity, admit, seal, release_run, diagnostics`.
  - `modbus_poller.py` builds a `GatewayLink` and never calls it directly.
  - The harness uses `activate`, `deliver` and `diagnostics`, plus an in-process `admit` for gates 4 and 5, as the spec allows.
  - `git diff --stat 3bbce526..HEAD -- gateway backend contracts simulator tools field/assetops_field/publish.py` is empty.
- **Harness deviations.** These are sound and match the rulings.
  - Dev1: path-routed responder. Diagnostics posts get the `test_gateway_upload.py:503-506` shape, any other path asserts, and DROP counts batch posts only.
  - Dev2: the `deliver_all` outer loop has a 1 s sleep and a 120 s assert.
  - Q5/Dev3: the gate 7 read timing described above.
  - Deviations 4-7 (schedule edges, `Poll.at` including the reconnect, the SKIPPED_LATE raw line, test placement) are consistent with 0.7 and 0.8.
- **Exit codes and lines.**
  - Exit 2 covers profile, identity and argument refusals, replay without `--stop-at`, and the crash hook against a non-SIMULATED identity.
  - Exit 3 covers a `release_previous` refusal, a publish or final refusal, and three consecutive SEAL_REFUSED.
  - Exit 4 covers unavailability before START (Q1, with `session.json` untouched), 10 consecutive unavailable publish instants or more than 4096 retained texts, and unavailability at the final step (Q2/Q3).
  - Exit 9 is `os._exit` straight after the n-th admit, before the seal.
  - START prints after `release_previous` and `session.json`. EXIT prints only after START, from the rewritten status. `finish()` admits the retained texts in order, then seals and releases, and keeps the texts on unavailability. Its three FakeLink tests match the Q3 script exactly.

## Findings

**L1 (Low, robustness).** `field/assetops_field/modbus_poller.py:558-563`.
- What is wrong: only `_Stop` is caught around `poller.run()`. Any other exception after START exits 1 with a traceback and prints no EXIT line, contrary to the "EXIT if and only if START" rule (Q4). Examples are an `OSError` appending the raw capture or writing `status.json`, or a `ValueError` from `IntervalAggregator.add`.
- Pre-START, a `GatewayRequestRefused` from `identity` (`:517`) is not caught either, so it also gives exit 1 rather than the spec's exit 3.
- Why it matters: both paths are unexpected rather than designed ones. The cost is a TEL-07/TEL-08 supervisor that sees exit 1 with no status line.
- Fix: map `GatewayRequestRefused` from `check_identity` to exit 3. Optionally, write the status and print EXIT in a catch-all after START. Preference, not a gate.

**L2 (Low).** `field/assetops_field/modbus_poller.py:531`.
- What is wrong: `previous["session_ref"]` sits outside the configuration `try`. A `session.json` without that key raises `KeyError`, which exits 1 instead of 2.
- Fix: move the lookup inside the guarded block.

**L3 (Low, harness).** `host/tests/test_field_modbus_tcp_proof.py:182`.
- What is wrong: the inner `while deliver(...)["attempted"]: pass` loop does not check the 120 s deadline. A responder that keeps a batch attempted on every pass would hang the test rather than fail it. Today's responders only DROP twice, and the back-off makes `attempted` 0, so it cannot happen now.
- Fix: check the deadline inside the inner loop too.

**L4 (Low, test coverage, not a gate).** The poller paths below are exercised by no test in this slice:
- CONFIG_FAULT whole-row faulting (`:278`, `close` filter);
- the 10-consecutive-unavailable and retained-overflow exits (`:348-360`);
- three consecutive SEAL_REFUSED;
- exit 3 from `release_previous`.

The TEL-04 gates do not require them, and the code reads correctly against 0.7 and Q-T33. A small FakeLink unit test, like the `finish()` tests, would pin them.

**L5 (Info).** The oracle reuses `modbus_tcp.classify` (proof:277) and `aggregate.expected_polls` (proof:301), so it is not fully independent of product code for word classification and poll placement. Both are covered by TEL-01 and TEL-02 unit tests, and the fault-window outcome mapping is independent. A bug there would be caught in `field/tests`, not here.

## Residual risk (beyond the packet)

- The packet already names the wall-timing sensitivity at rate 120. My run also showed `SKIPPED_LATE == 0`, through the exact counter equality. The run took 229 s, against the packet's 232.7 s.
- At a publish instant, a seal failure after a successful admit re-admits those texts at the next instant. Those reports are counted twice in `status.admissions`, once ADMITTED and once ALREADY_ADMITTED. The spec intends the re-admit, but anyone reading the status counts should know about the double count.
