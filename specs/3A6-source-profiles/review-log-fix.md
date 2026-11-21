# Review: D-3A6.29 log fix (branch fix/3a6-commercial-log, head 6be044379)

Verdict: ACCEPT. No High or Medium findings.

- envelope.py: no logging import or call. `EnvelopeBreach(CanonicalRefused)` carries `cause`; uploads.py copies it onto `UploadRefused`; only `commercial_upload_api.py` (outside `commercial/`) logs cause, reader, bytes, tenant code. Grep of `commercial/*.py` for logging/logger/print: none.
- Helpers: `reader_id` returns the given ID or `DEFAULT_READER`; it is logged only after a breach, which needs `reader()` to have accepted the ID (unknown IDs are refused 422 first), so it is always a known profile ID. `tenant_code` returns the stored tenant slug. Neither returns per-upload operator text.
- My own marker through HTTP with log capture (scratch copy, deleted): in a trailing CSV cell, `x-file-name`, two extra headers: E9 passes, marker in no record or `caplog.text`.
- Mutations (scratch copy): API logging stubbed out -> E9 fails; `import logging` added to envelope.py -> `test_no_log_call_in_the_commercial_package` fails.
- Runs: 3A6 envelope/command/profiles, 3A1 service (R13), 3A2 API, 3A4, 4B money leaves, 3A3 single writer: 191 passed. Postgres (3A2, 3A6, 3A4, 4B, 3A1) via heavy-slot --db and run-host-tests.ps1: 67 passed.
- D-3A1.10 amendment: already present in c36658571 as a sub-bullet at specs/3A1-commercial-record-store/rulings.md lines 116-117 (not an unapplied edit). Its wording differs slightly from D-3A6.29's quoted line; same meaning.

Low (no block): D-3A6.29 asks a test that `EnvelopeBreach.cause` is in the closed set for every breach the adversarial tests force; E9 checks one breach (memory) plus the constructor, and E6 checks the log is empty. Optional.
Residual: package-scan tests are still outside check-all (held for owner, per ruling).
