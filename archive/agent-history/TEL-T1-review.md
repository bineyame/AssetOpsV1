# TEL-T1 review: TEL-00..TEL-03 (`task/TEL-01-field-core` at 3bbce526, base `main` f3c9db4d)

Reviewer: fresh Claude reviewer, independent of the builder. Authority: `.agent/build-spec-telemetry-2026-10-27.md` rev 2 (Q-T1..Q-T70, section J TEL-T1-Q1..Q7) and `.agent/telemetry-rulings-2026-10-27.md` (D4, D10, amendments 1-3).

## Verdict: ACCEPT

There are no High or Medium findings. The three Low findings below are hardening notes. None of them blocks the merge, and they can be fixed in TEL-04 or left as they are.

## Checks I ran myself

The interpreter was `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`. I set the Lane T PYTHONPATH (build-sequence §1) and `ASSETOPS_GUARD_PYTHON` to the same interpreter, and ran from the worktree root. `assetops_gateway` and `assetops_field` both resolve to `-tel`, and pymodbus is 3.16.1.

| Command | Result |
|---|---|
| `pytest field/tests -q -p no:cacheprovider --basetemp ...` | 146 passed, 9.1 s |
| `pytest host/tests/test_field_observation_fixtures.py` (its own file) | 1 passed |
| `pytest gateway/tests/test_wire_contracts.py` | 32 passed |
| `tools/check-architecture.ps1` | "Architecture check passed.", exit 0 |
| `tools/check-agent-workflow.ps1` | "Agent workflow check passed.", exit 0 |

My first combined run reported 4 setup errors. The cause was that the `--basetemp` parent directory did not exist (`FileNotFoundError` on the basetemp path), which is my environment, not the code. Once I created the directory, every file passed.

What I did not run: no full suites and no Postgres, as instructed. I did not rerun the builder's 19 in-tree guard probes, because that would have meant editing the tree. Instead I checked the new regexes directly against 20 sample import lines (results below). The architecture check passing on the real tree shows that the anti-vacuity counter does see `publish.py`.

## Verification against the spec

- **The `field/` import boundaries** (`tools/checks/dependency-direction.ps1:246-334`):
  - Non-test field modules are refused `assetops_backend`, `assetops_simulator`, bare `backend`/`simulator`/`host`, `pymodbus`, and any `assetops_gateway` module group other than `ipc`.
  - `import_module("assetops_gateway.ledger")` is caught.
  - `field/tests` follows the same rules except that pymodbus is allowed.
  - Anti-vacuity: at least one non-test module must be scanned, and the `ipc` import must be counted. Only non-test modules increment that counter.
  - The reverse rule covers backend (tests included, per amendment 2 item 2), gateway, simulator and contracts with their tests, and non-test host modules only.
  - `field` is added to `$mayNotImportHost`.
  - The `module-roots.ps1` additions match D4 and amendment 2 item 1.
- **No existing guard rule was loosened.** Both `.ps1` diffs are pure additions: one array entry and one new section. The existing host-gateway counts are untouched, and so is the `host/tests/*` exclusion. Nothing changed under the paths the spec forbids (0.2): backend, gateway, contracts, simulator, frontend, the host product modules, `.ai` and `tasks`. `.gitattributes` gets exactly one additive line, as Q-T44 allows.
- **Exact power-of-ten scaling** (`decode.py:86`) is `Fraction(sum(raws)) * Fraction(10) ** exponent`. The checks run in the spec's order: the sentinel check on the unsigned combined value, then two's complement, then the exact phase sum. `encode_value` refuses `NOT_A_MULTIPLE` when the denominator is not 1, and `OUT_OF_RANGE` when the value exceeds the first register's type or equals a sentinel.
- **Quantization.** `IntervalAggregator.close` quantizes the exact mean once with `quantize_half_even` (`aggregate.py:130-131`). There is no second rounding helper. The package contains no `float(` call, and a test asserts that.
- **The client is read-only.** `ModbusTcpClient.read` raises `WriteForbidden` before it takes a transaction ID, opens a socket or sends a byte (`modbus_tcp.py:67-68`). The tests cover function codes 05/06/15/16/23 and confirm the server records 0 bytes.
- **The exception map** (`modbus_tcp.py:169-183`):
  - 01 and 03 give `CONFIG_FAULT`; 02 gives `NO_VALUE`; 04 and 06 give `FAILED`; 0A and 0B give `NO_ANSWER`.
  - Codes the 0.7 table does not name give `FAILED` (TEL-T1-Q4).
  - Precedence is `CONFIG_FAULT > NO_ANSWER > FAILED > NO_VALUE > VALUE`.
  - A malformed frame or a byte-count mismatch gives `NO_ANSWER RESET` and drops the connection (Q3). A well-framed answer with the wrong word count gives `CONFIG_FAULT`.
  - TID and unit mismatches give `NO_ANSWER`, followed by a reconnect.
- **The emulator reads back at register resolution.** `gx_server.presented_value` quantizes `value / 10^exponent` to `register_quantum` (half-even) and multiplies the scale back. It skips quantization only for rows whose **row** status is `ILLUSTRATIVE` (TEL-T1-Q5). The read-back test covers every PV and SoC observation in the window, at `T - S/2` for intervals and at `T` for states. The tally adds up to the full observation count. The pymodbus 3.16.1 client cross-check passes.
- **Whole-second UTC Z.**
  - `instant_z` and `_seconds` refuse naive instants, instants with a non-zero offset, and instants with microseconds.
  - `WallClock.now()` truncates to whole seconds.
  - `ReplayClock` keeps integer-microsecond arithmetic and floors to whole seconds.
- **D10 coverage** (`test_field_aggregate.py`): every case below has a test.
  - The expected polls sit at mid-period: 06:02:30, 06:07:30 and 06:12:30.
  - With all three polls answered, values 1, 1 and 2 give 1.333.
  - One missing poll gives `NO_MEASUREMENT` with its span.
  - Any bad poll among answered ones gives `NO_MEASUREMENT`.
  - Sentinel-only answers still give `NO_MEASUREMENT`.
  - A fully failed interval gives `None`.
  - The session's first interval gives `NO_COMPLETED_INTERVAL` with its span, and a session started on the boundary gives `GOOD`.
  - The state window checks are at B+1, B+3 and B+2 (retry).
- **Section J.**
  - Q1: a sentinel must fit the narrowest register of the row (`profile.py:441`).
  - Q2: "first sentinel" is `min(sentinels)` (`decode.py:126`).
  - Q3, Q4 and Q5 are implemented as ruled.
  - Q6 is deferred to TEL-04.
  - Q7 has no TEL-03 code impact.
- **The publisher** uses only the ops in `OPS_USED`, and the `release_run` and `seal` bodies match `ipc.py:62-85`. `seal_and_release` catches only `SEAL_REFUSED` and still releases. `release_previous` seals, then releases, and lets `SEAL_REFUSED` propagate.

## Findings

**L1 (Low): a write during a PAUSE fault is not counted** (`field/tests/field_emulators/gx_server.py:243-247`). `_answer` returns on an active `PAUSE` before the write counter runs. A write sent during a pause window would therefore be missed by the `writes == 0` teardown assertion that every emulator fixture makes. Spec TEL-03 says "any write FC ... increments this". The fix is to increment `writes` before the PAUSE check. This is a gap in test instrumentation only. The client cannot send a write in any case.

**L2 (Low): the client does not check the MBAP protocol identifier** (`field/assetops_field/modbus_tcp.py:84`). `_protocol` is unpacked and then ignored, so an answer with a non-zero protocol ID is accepted. The emulator does check it (`gx_server.py:223`). The fix is to treat `protocol != 0` as `NO_ANSWER RESET`, which matches the Q3 malformed-frame rule. The spec does not require this check; I am suggesting it as hardening.

**L3 (Low, informational): the guard regexes have the same blind spots as the existing rules** (`tools/checks/dependency-direction.ps1:258-261`, and the reused `$hostGatewayImport` at :213):
- `import_module("host")`, `("backend")` and `("simulator")` without a trailing dot are not caught.
- A comma-joined import such as `import assetops_gateway.ipc, assetops_gateway.service` passes, because the module group is read as `ipc`.
- `import os, assetops_backend` and `__import__(...)` are not caught.

The existing host and gateway rules have the same blind spots. The spec directs the builder to reuse `$hostGatewayImport`, and `from assetops_gateway import ipc` is refused, which errs on the strict side. This is not a regression and needs no action in this slice.

## Residual risk not already named in the packet

- `aggregate._seconds` uses `timedelta.total_seconds()` (a float) to test alignment. It is exact for whole-second instants in any realistic range, so I have not raised it as a finding.
- The emulator serves a state row's sentinel from `last + cadence - 1 s`, not from `last + cadence`. That follows from the one-second lead rule and is consistent with Q-T26 and Q-T27.
- I am carrying forward the packet's TEL-04 risks: rate-120 timing on one machine, and rational source values compared at register resolution under TEL-T1-Q7.
