# ENV-1 reviewer guide

Architect (Claude), 2026-11-21, rev 1. Discovery review (W5): a protected seam (upload parsing). Read `spec.md`,
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
4. **Per host.** S2 really uses two processes; a killed holder frees its slot. `ParseEnvelope.read` holds the host
   slot around `_run` only and waits without a timeout (D-3A6.23 unchanged). Lock descriptors are `O_CLOEXEC`.
5. **Logged as codes and numbers.** A2's sentinel check covers message, args and every record attribute; `bytes` is
   an `int`; no file name. Nothing under `commercial/`, `reading_upload/` or `field/` logs.
6. **Measured margins.** H6 passes F1 and F2 under production limits; the packet's pre-flight figures are within 1.5x
   of the Architect's (rulings D-ENV1.2), or a mid-build question was raised.
7. **3A6 unchanged.** `git diff main -- backend/tests/test_3a6_parse_envelope.py` is empty and E0 to E9 pass; the
   package-scan files pass.
8. **Test isolation.** Both conftests set the slot directory per process; no test writes the production default.
9. **No text.** No i18n key, no new sentence; the docstring line of §2.3 is a docstring.

## Plants (each on a scratch copy; each must fail the named test)

| # | Plant | Fails |
|---|---|---|
| V1 | `_entry` calls `main` before the `setrlimit` calls | FL2 (F2 no longer exit 7) |
| V2 | `run_field` drops `--limit-cpu-seconds` | H1, FL1 path in H2 (configuration exit) |
| V3 | `run_field` no longer catches `TimeoutExpired` | H3 (wall) |
| V4 | `HostSlots.hold` opens one shared descriptor per instance | S1 |
| V5 | `hold` uses `LOCK_EX` without `LOCK_NB` and ignores `timeout` | H5, S2 |
| V6 | `ParseEnvelope.read` skips `self._host.hold` | S4 |
| V7 | the API's `except ParseLimitBreach` is removed | A1 |
| V8 | the log's `extra` gains `"file_name": file_name` | A2 |
| V9 | `_value`'s `except ValueError` is removed | FL4 |
| V10 | `_source_system` keeps `json.loads(data)` | L11, L12 |
| V11 | `_bytes` reads without the `+ 1` bound check | L10 |
| V12 | `CHECK_LIMITS.cpu_seconds` set to 6 | H0, H6 |
