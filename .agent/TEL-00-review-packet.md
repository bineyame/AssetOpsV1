# TEL-00 review packet: pre-flight and card corrections

Status: in_review

PowerShell:
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-tel\backend;C:\Users\assef\Bineyame\AssetOpsV1-tel\contracts;C:\Users\assef\Bineyame\AssetOpsV1-tel\simulator;C:\Users\assef\Bineyame\AssetOpsV1-tel\gateway;C:\Users\assef\Bineyame\AssetOpsV1-tel\host;C:\Users\assef\Bineyame\AssetOpsV1-tel\field;C:\Users\assef\Bineyame\AssetOpsV1-tel"
```
Python: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` (3.12.10).

Task file: `.agent/build-spec-telemetry-2026-10-27.md` (rev 2) with `.agent/build-sequence-2026-10-27.md` and `.agent/telemetry-rulings-2026-10-27.md` (amendments 1-3). Branch `task/TEL-01-field-core` from `main` f3c9db4d.

## Environment evidence

- `python -c "import assetops_gateway,assetops_contracts"` with the line above prints
  `C:\Users\assef\Bineyame\AssetOpsV1-tel\gateway\assetops_gateway\__init__.py` and
  `C:\Users\assef\Bineyame\AssetOpsV1-tel\contracts\assetops_contracts\__init__.py`: the worktree, not the main checkout.
- pytest 9.1.1 present. **pymodbus is not installed** in the shared venv (`ModuleNotFoundError: No module named 'pymodbus'`). Spec 0.1 / Q-T7 makes its download and install a coordinator step before TEL-03; the builder did not install it.

## Port table (spec 0.4, fixed here)

| Port | Use |
|---|---|
| 5020 | GX-shaped emulator, Modbus TCP, 127.0.0.1 (runbook and TEL-08). Tests bind port 0 (ephemeral). |
| 8443 | `serve_tls` for the runbook and TEL-08 only. |
| ephemeral | `FakeCentral`: `ThreadingHTTPServer(("127.0.0.1", 0), ...)` at `gateway/tests/fake_central.py:74`. |
| none (pipe) | Gateway IPC: `\\.\pipe\assetops-gateway-hosttest-<uuid>` at `host/tests/gateway_process.py:22`; no TCP port. |
| 7000 | RTU over TCP: unused in October. |

Confirmed: neither `host/tests/gateway_process.py` nor `gateway/tests/fake_central.py` binds a fixed TCP port, so neither can collide with the commercial dev servers on 5173 and 8000.

## Card corrections carried (the HTML is not edited)

All corrections are as written in the spec body and rulings "Card corrections TEL-00 must apply before TEL-01"; this packet adopts them for TEL-01..03:
- TEL-01: D10 done-when (missing poll -> `UNAVAILABLE`/`NO_MEASUREMENT` with span; session's first interval -> `NO_COMPLETED_INTERVAL` with span; fully failed -> nothing); mid-period poll instants (amendment 3 item 1); `output_resolution` with `quantize_half_even` reuse; check changes per D4 and amendment 2 item 2; op set per D4 item 5 (`seal` + `release_run` added); no `conftest.py` in `field/tests`.
- TEL-02: a timeout is retried once by the poller inside the attempt window, then `NO_ANSWER`; the client never retries (spec 0.7, Q-T21).
- TEL-03: observations from the pinned JSONL (D4); rows 808, 809, 810, 843 only (D5); exact stated phase split (whole value on 808); representability amended to register-resolution quantization, stop only on range overflow or `RESOLUTION_FINER_THAN_QUANTUM`; stdlib emulator with pymodbus as client cross-check (amendment 3 item 6).

## Gate

No open questions: the 70 pre-flight questions are answered in the spec (Q-T1..Q-T70). One environment precondition is open and is the coordinator's per Q-T7: pymodbus 3.16.1 is not yet in the venv.
