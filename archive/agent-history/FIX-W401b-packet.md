# FIX-W401b packet: clocked-test request times

Branch `task/FIX-W401b-clock`, from main ab248b4c3.

Cause: the `clocked` fixture freezes the store clock at POSITIVE_NOW (2026-11-01T01:00Z), but the `at()` helper in
`backend/tests/test_w401_work_service_postgres.py` took request `occurred_at` from the real clock. Once the real
clock passed about 01:05Z, `check_occurrence` (work/model.py:236-238) refused them with WORK_OCCURRED_AT_FUTURE.

Fix (test-only): `at()` offsets from a module-level `_BASE` (None means real clock). The `clocked` fixture sets it to
POSITIVE_NOW and resets it in a `finally`. No product code or assertion changed. Non-clocked tests and
`test_w401_work_api.py` (which imports `at`, never sets `_BASE`) keep the real clock. No other file uses the
`clocked` fixture with real-clock times (`test_w401_site_indexes_postgres.py` and `test_w401_work_read_postgres.py`
build their own times from POSITIVE_NOW).

Results:
- `tools\run-host-tests.ps1 -- backend/tests/test_w401_work_service_postgres.py -q`: 8 passed (64 s).
- `tools\check-all.ps1`: see report.
