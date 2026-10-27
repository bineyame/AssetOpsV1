# TEL T1 review packet: TEL-00, TEL-01, TEL-02, TEL-03

Status: in_review

PowerShell:
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-tel\backend;C:\Users\assef\Bineyame\AssetOpsV1-tel\contracts;C:\Users\assef\Bineyame\AssetOpsV1-tel\simulator;C:\Users\assef\Bineyame\AssetOpsV1-tel\gateway;C:\Users\assef\Bineyame\AssetOpsV1-tel\host;C:\Users\assef\Bineyame\AssetOpsV1-tel\field;C:\Users\assef\Bineyame\AssetOpsV1-tel"
```
Python `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` 3.12.10. `assetops_gateway.__file__` resolves to the `-tel` worktree.

Task file: `.agent/build-spec-telemetry-2026-10-27.md` rev 2 (Q-T1..Q-T70 binding), with the build sequence and rulings (amendments 1-3). Branch `task/TEL-01-field-core` from `main` f3c9db4d. Review group T1.

| Task | Commit |
|---|---|
| TEL-00 | 2fb27dde (`.agent/TEL-00-review-packet.md`) |
| TEL-01 | 7896dcc3 |
| TEL-02 | ae9c258a |
| TEL-03 | c29f0897 |

USER_REVIEW_REQUIRED: no UI; Architect review of `.agent/TEL-T1-questions.md` (6 items, none blocking).

## Files changed

- New `field/`: `pyproject.toml`; `assetops_field/{__init__,profile,decode,clock,aggregate,report,publish,modbus_tcp}.py`; `profiles/gx-system-illustrative-1.json`; `tests/{field_fixtures,test_field_profile,test_field_decode,test_field_clock,test_field_aggregate,test_field_report,test_field_publish,test_field_modbus_tcp,test_field_gx_emulator}.py`; `tests/field_emulators/{__init__,gx_server}.py`. No `conftest.py`.
- New `host/tests/field_observation_fixtures.py`, `host/tests/test_field_observation_fixtures.py`.
- New `contract-fixtures/telemetry/kobo-public-observations-v1/{observations.jsonl,manifest.json}` (294 observations, sha256 `3d62a8319af585f5e8ee1a4210b7fc42930d50b4513e796df4e74379edb5be6b`).
- Additive: `tools/checks/module-roots.ps1` (+2 dirs, +2 marker files), `tools/checks/dependency-direction.ps1` (`field` in `$mayNotImportHost`; new section "The field adapters are IPC clients"), `.gitattributes` (+ `contract-fixtures/telemetry/** -text`). No existing rule edited, reordered or loosened; existing host counts untouched.
- `.agent/TEL-00-review-packet.md`, `.agent/TEL-T1-questions.md`, this packet.

## Gate evidence

**TEL-00.** Port table and the `gateway_process.py:22` (named pipe) / `fake_central.py:74` (`127.0.0.1:0`) confirmation are in the TEL-00 packet: neither binds 5173 or 8000. Card corrections carried by reference. 70 questions answered in the spec; no new open question at pre-flight.

**TEL-01** (`test_field_profile` 38, `test_field_decode` 10, `test_field_clock` 9, `test_field_aggregate` 17, `test_field_report` 8, `test_field_publish` 14):
- Decoder vectors: `FF9C` int16 ×0.1 = −10; `7FFF` sentinel; int16 sentinel `[32768]` with `8000` → SENTINEL (and `8001` → −32767); `0001 86A0` uint32 BIG ×0.001 = 100; `86A0 0001` LITTLE = 100; `03E8 0000 FFFF` → SENTINEL; `03E8 0001 0002` → 1.003. Encode→decode round trip over every row of `-1` and the TEL-05b `-2` table (fixture rows), whole value on the first register. `EncodeRefused`: 65.536 kW `OUT_OF_RANGE`, 65.535 kW (the sentinel) `OUT_OF_RANGE`, 0.0005 kW `NOT_A_MULTIPLE`, unknown state `UNKNOWN_STATE`.
- D10: one missing poll → `UNAVAILABLE`/`NO_MEASUREMENT` with span; session's first interval → `NO_COMPLETED_INTERVAL` with span; fully failed → `None`; 1, 1, 2 → `1.333`; `expected_polls` 06:02:30Z, 06:07:30Z, 06:12:30Z.
- State: `B+1` GOOD at `B`; `B+3` with skew 2 → `None`; failed first then good retry at `B+2` → GOOD.
- Every report text round-trips through `parse_device_report_text`; SHA unchanged under key reordering (and through `load_profile`); a source-scan test asserts each of the nine `PROFILE_CODES` has a refusal test.
- `FakeLink` sees only `OPS_USED`; `release_previous` sends `seal` then `release_run(previous_ref)`; `seal_and_release` survives a scripted `SEAL_REFUSED` and still releases; other refusals propagate.
- No `float(` in `field/assetops_field` (test-asserted).
- Guard non-vacuity (each probe appended one line, ran `Invoke-DependencyDirectionCheck` + `Invoke-ModuleRootsCheck` dot-sourced, then `git checkout`; clean tree after): clean 0 failures; non-test field → `assetops_backend`, `assetops_simulator`, `host`, `assetops_gateway.service`, `import_module('assetops_gateway.ledger')`, `pymodbus` each 1 failure (host also trips `$mayNotImportHost`); field test → `pymodbus` 0 (allowed), → gateway.service 1, → backend 1; `assetops_field` imported from host product 1, host/tests 0 (allowed), backend/tests 1, gateway product 1, gateway tests 1, simulator 1, contracts 1; publisher's ipc import commented out → anti-vacuity failure; `field/assetops_field/__init__.py` removed → module-roots failure.

**TEL-02** (`test_field_modbus_tcp` 28): FC 05/06/15/16/23 raise `WriteForbidden` with 0 bytes received; the five request frames of the gate table byte-exact with TID 1 (808 frame `… 64 03 03 28 00 03`); Figure 2b → words `(0x007B, 0xFF9C)`; Figure 2c → `EXCEPTION 02`; exceptions 01/02/03/04/06/0A/0B through `classify` to the 0.7 outcomes; TID and unit mismatch → `NO_ANSWER` and reconnect; silent server → `NO_ANSWER TIMEOUT` after `timeout_s`, exactly one frame (12 bytes) sent; TID wraps 65535 → 0; `classify` precedence across split requests; `requests_for` contiguous/split.

**TEL-03** (`test_field_gx_emulator` 21 passed, 1 skipped; `host/tests/test_field_observation_fixtures.py` 1 passed):
- Window maxima (measured first, Q-T16): PV 50 kW (within 65.534), SoC 100 %. No range overflow.
- Read-back over every PV and SoC observation of 2026-09-30T03:00Z-15:00Z through the TEL-02 client and profile `-1` on a fake wall: 96 REPORTED equal the register-quantized value exactly, 1 SENTINEL (PV `NO_PRECEDING_INTERVAL` at 03:00Z), 1 `EXCEPTION 0B` (SoC `DROPPED`).
- Each `FaultWindow` kind (PAUSE, EXCEPTION 04/06/02/03, SENTINEL, WRONG_UNIT_ID, WRONG_TID) gives its 0.7 outcome through `classify`; windows are half-open; a row fault leaves the other row unchanged. Framing: unknown unit 0B, undeclared address 02, count 0/126 → 03, FC 01 → 01. `writes == 0` asserted in every emulator fixture teardown; the write test sends FC 06 by raw socket → `86 01`, `writes == 1`. CLI prints `READY 127.0.0.1:<port>` and exits 0 at `--stop-at`.
- Freshness: regenerated JSONL and manifest byte-equal to the checked-in files; manifest SHA matches; LF only, one final LF; exactly the seven public fields; each `-1` row's reading class, cadence (and span = cadence for interval), and unit equal the run's declared signal.
- Proofs: emulator presenting value + one quantum → 3 read-back tests fail; one byte of the JSONL changed → freshness fails; both reverted with `git checkout`.

## Commands run (cwd worktree root, PYTHONPATH above)

| Command | Result |
|---|---|
| `python -m pytest field/tests -q -p no:cacheprovider --basetemp $env:TEMP\assetops-tel\field-tests` | 145 passed, 1 skipped (pymodbus), 9.1 s |
| `python -m pytest host/tests/test_field_observation_fixtures.py …` (own file) | 1 passed, 5.0 s |
| `python -m pytest gateway/tests/test_wire_contracts.py …` | 32 passed |
| `tools/check-architecture.ps1` with `ASSETOPS_GUARD_PYTHON` = the venv python, at c29f0897 | "Architecture check passed.", exit 0, 175 s with the next row |
| `tools/check-agent-workflow.ps1`, at c29f0897 | "Agent workflow check passed.", exit 0 |
| `python host/tests/field_observation_fixtures.py daytime` | wrote the fixture (294 observations) |

Guard baseline before any change: `check-architecture.ps1` passed with `ASSETOPS_GUARD_PYTHON` set (without it, Rule 8 cannot find `.venv` in the worktree and reports 9 vacuity failures: an environment precondition, not a code failure). No full suite, no Postgres, no dev server.

## Deviations and findings

1. **pymodbus 3.16.1 not installed** in the shared venv (coordinator step, Q-T7; not installed by the builder). The cross-check `test_pymodbus_client_reads_the_same_words` is written and skips via `importorskip`; it asserts version 3.16.1 when present. Wheel name/SHA not recorded. Rerun the file after install.
2. **The daytime run publishes exact rationals, not 0.000001-resolution values.** `registered.request()` with no overrides uses `simulator-lab-publication:3`; e.g. SoC `48347/760` at 07:45Z. The amended TEL-03 rule (quantize to the register quantum) handles it, so the gate holds; but the amendment's premise (`profiles.py:1826` resolution) does not apply to this window. Risk for TEL-04/05: the poller publishes 1 W / 1 % values, the simulator exact rationals.
3. `.gitattributes` line is `-text` as the spec says; existing pins use `text eol=lf`. Both keep LF bytes here (no CRLF warning on the JSONL).
4. Implementation choices awaiting Architect confirmation: `.agent/TEL-T1-questions.md` items 1-6 (mixed-width sentinel range, "first" sentinel of a set, malformed answers → `NO_ANSWER RESET`, unnamed exception codes → `FAILED`, quantization discriminator `status != ILLUSTRATIVE`, session-ref builder left to TEL-04).
5. Manifest `window` is `{start, end}` and `scenario`/`publication_profile` are `id:version` strings (0.6 names the keys, not their shape).

## Residual risk

- One-machine rate-120 timing is untested here (TEL-04).
- `ReplayClock.now()` floors pre-epoch times (earlier than "truncate toward zero" for negatives); only the pre-start clamp sees it.

## Reviewer focus

The new `dependency-direction.ps1` section (additive, reuses `$hostGatewayImport`), `classify` precedence, `IntervalAggregator.close`, and questions 1-6.
