# ENV-1 reviewer guide

Architect (Claude), 2026-11-21, rev 2 (handshake round 1, D-ENV1.8 to D-ENV1.17). Discovery review (W5): a protected seam (upload parsing). Read `spec.md`,
`rulings.md`, then the diff. Done means every question of spec §6 answers yes with evidence and every plant below
fails its named test.

## What to check, and how

1. **Exclusive.** Grep the diff and `main` for every route to a parse of upload bytes (spec §2, D-ENV1.1's sweep):
   commercial (`envelope.py` only, E7 unchanged), reading (`run_field` only, and only with the limit flags), the
   loader (`_bytes` and `default_envelope().read`; no `json.loads`, no other `read_bytes` in `_run`).
2. **Limits before the first read.** In `csv_upload._entry`, the four `setrlimit` calls come before `main`, and
   `main` reads the profile and the file only after. `main` itself sets nothing (its in-process tests must stay safe).
   A path that runs the field module without the flags must refuse (FL1).
3. **Bounded answers.** Each cause maps to the code and words of spec §2.3, never a 500. Read `run` in
   `reading_upload_api.py`: `ParseLimitBreach` is caught before `GatewayUnavailable` and `RuntimeError`. After a
   breach the next upload reads (H7).
4. **Per network namespace.** S2 and S2b really use separate processes, S2b through `host_slots()` and the
   environment variable; a killed holder frees its slot. `ParseEnvelope.read` resolves the slots at each read
   (D-ENV1.14) and holds one around `_run` only, waiting without a timeout (D-3A6.23 unchanged). `parse_slots.py`
   makes no file system call (no `open`, `mkdir`, `tempfile`, `fcntl`); its sockets are non-inheritable (S1).
5. **Logged as codes and numbers.** A2's sentinel check covers message, args and every record attribute; `bytes` is
   an `int`; no file name; level by cause (WARNING for load and the gateway, ERROR otherwise); all three 503
   branches log once. Nothing under `commercial/`, `reading_upload/` or `field/` logs.
6. **Measured margins.** Recompute each constant of H0 from the packet's runs by D-ENV1.10's method (memory: next
   128 MiB at or above 2x the floor; CPU: next 10 s at or above 3x the largest; wall 2x CPU). A constant that does not
   follow, a single run where the method asks for eight, or a send measured without a real gateway is High. H6 and
   H6s ran (they are `slow`) and passed under production memory and CPU.
7. **3A6 unchanged.** `git diff main -- backend/tests/test_3a6_parse_envelope.py` is empty and E0 to E9 pass; the
   package-scan files pass.
8. **Test isolation.** Both conftests set the slot namespace as the first statement of `pytest_configure`, before
   any `return`; S6 passes; the packet lists hand-built server environments and each copies the variable.
9. **No text.** No i18n key, no new sentence; the docstring line of §2.3 is a docstring.

## Plants (each on a scratch copy; each must fail the named test)

| # | Plant | Fails |
|---|---|---|
| V1 | `_entry` calls `main` before the `setrlimit` calls | FL2 (F2 no longer exit 7) |
| V2 | `run_field` drops `--limit-cpu-seconds` | H1, FL1 path in H2 (configuration exit) |
| V3 | `run_field` no longer catches `TimeoutExpired` | H3 (wall) |
| V4 | `HostSlots.hold` binds one shared socket per instance and counts holders in memory | S2, S2b |
| V5 | `hold` ignores `timeout` and waits without end | H5, S2 |
| V6 | `ParseEnvelope.read` skips the host slot's `hold` | S4 |
| V7 | the API's `except ParseLimitBreach` is removed | A1 |
| V8 | the log's `extra` gains `"file_name": file_name` | A2 |
| V9 | `_value`'s `except ValueError` is removed | FL4 |
| V10 | `_source_system` keeps `json.loads(data)` | L11, L12 |
| V11 | `_bytes` reads without the `+ 1` bound check | L10 |
| V12 | `CHECK_LIMITS.cpu_seconds` set to 6 | H0, H6 |
| V13 | `run_field` maps a negative return code other than XCPU/KILL to today's `RuntimeError` | H4 (`crashed`) |
| V14 | `__init__` resolves `host_slots("commercial")` once and keeps it | S6 |
| V15 | the conftest sets the namespace after the early `return` (worker branch) | S6 under xdist (`-n 2`) |
| V16 | the API's `RuntimeError` branch does not log | A2 |
| V17 | `slot_namespace` ignores the environment variable | S2b |
| V18 | `SEND_LIMITS.memory_bytes` set 32 MiB below pre-flight (c)'s measured floor | H6s, H0 |
| V19 | the loader keeps `contents = {path: _bytes(path) ...}` | L10b (AST) |
